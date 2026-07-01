"""
conversion_agent.py – Upgraded APL-to-Python ConversionAgent
=============================================================
Key improvements over v1
------------------------
* Chunked conversion for large APL programs (500+ lines)
* Fixed operator-substitution ordering (compound ops before simple ones)
* APL dfn ({}) and tradfn (:Signature) parsing
* System-variable awareness (⎕IO, ⎕ML, ⎕CT)
* Safe inputs injection (no globals() mutation)
* Retry logic with exponential back-off
* Calibrated confidence scoring
* Correct reshape / concat / reduction regex sequencing
* Post-normalize syntax validation (not pre)
* print() stripping (not fallback trigger)
* Full type-annotation coverage
"""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import re
import textwrap
from typing import Any

from ..providers.provider_factory import ProviderFactory, ScaffoldedProviderError
from ..providers.response_normalizer import ResponseNormalizer
from ..utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Lines per chunk sent to the AI provider.  Keep well under typical 8 k-token
# context windows while still giving the model enough context.
CHUNK_SIZE = 120

# Maximum provider retries before falling back to the rule-based converter.
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds

# APL system variables and their Python / NumPy equivalents
APL_SYSTEM_VARS: dict[str, str] = {
    "⎕IO": "1",       # Index origin – default 1; code below adjusts arange calls
    "⎕ML": "1",       # Migration level
    "⎕CT": "1e-14",   # Comparison tolerance
    "⎕PP": "10",      # Print precision
    "⎕PW": "80",      # Print width
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _APLParser:
    """
    Lightweight structural parser for APL source.

    Responsibilities
    ----------------
    * Split a flat APL listing into logical blocks: dfns, tradfns, and
      statement sequences.
    * Extract ⎕IO / ⎕ML / ⎕CT assignments so the emitter can compensate.
    * Identify every variable that is *assigned* vs. only *referenced* so the
      wrapper can declare a proper parameter list.
    """

    # Matches a traditional function header, e.g. "∇ Z←A FOO B" or "∇ FOO A"
    _TRADFN_OPEN  = re.compile(r"^∇\s*(.+)$")
    _TRADFN_CLOSE = re.compile(r"^∇\s*$")

    # Matches a dfn assignment, e.g. "foo ← { ⍺ + ⍵ }"
    _DFNSIGN_RE   = re.compile(r"^([A-Za-z_]\w*)\s*←\s*\{(.+)\}\s*$", re.DOTALL)

    # Assignment token
    _ASSIGN_RE    = re.compile(r"^([A-Za-z_⎕]\w*)\s*←(.*)$")
    _TOKEN_RE     = re.compile(r"\b([A-Za-z_⎕]\w*)\b")

    def __init__(self, source: str) -> None:
        self.source   = source
        self.lines    = source.splitlines()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_clean_lines(self) -> list[str]:
        """Return non-empty, non-comment lines, stripped."""
        return [
            ln.strip()
            for ln in self.lines
            if ln.strip() and not ln.strip().startswith("⍝")
        ]

    def get_system_var_overrides(self) -> dict[str, str]:
        """Return {var_name: value} for any ⎕XX ← N assignments."""
        overrides: dict[str, str] = {}
        for ln in self.get_clean_lines():
            m = self._ASSIGN_RE.match(ln)
            if m and m.group(1) in APL_SYSTEM_VARS:
                overrides[m.group(1)] = m.group(2).strip()
        return overrides

    def find_unassigned_variables(self) -> set[str]:
        """Variables referenced but never assigned (i.e. free / input variables)."""
        lhs: set[str] = set()
        rhs: set[str] = set()
        for ln in self.get_clean_lines():
            m = self._ASSIGN_RE.match(ln)
            if m:
                lhs.add(m.group(1))
                for tok in self._TOKEN_RE.findall(m.group(2)):
                    rhs.add(tok)
            else:
                for tok in self._TOKEN_RE.findall(ln):
                    rhs.add(tok)
        # Remove Python / NumPy keywords and built-ins that may appear
        noise = {"np", "True", "False", "None", "int", "float", "list",
                 "range", "len", "sum", "min", "max", "print", "result"}
        return (rhs - lhs) - noise

    def split_into_chunks(self, chunk_size: int = CHUNK_SIZE) -> list[str]:
        """
        Split large APL programs into overlapping logical chunks.

        Each chunk starts from a clean assignment boundary where possible so
        the AI model has enough context to resolve inter-line dependencies.
        Chunks overlap by 10 lines so the model can see the tail of the
        previous block.
        """
        clean = self.get_clean_lines()
        if len(clean) <= chunk_size:
            return ["\n".join(clean)]

        chunks: list[str] = []
        overlap = min(10, chunk_size // 6)
        step    = chunk_size - overlap
        i = 0
        while i < len(clean):
            end = min(i + chunk_size, len(clean))
            chunks.append("\n".join(clean[i:end]))
            i += step
        return chunks


# ---------------------------------------------------------------------------
# Rule-based emitter (fallback / offline path)
# ---------------------------------------------------------------------------

class _RuleEmitter:
    """
    Translates individual APL expressions to Python / NumPy using ordered
    regex substitutions.

    Design notes
    ------------
    * Compound operators are replaced BEFORE their constituent symbols so that,
      e.g., '+.×' is handled before '×' is turned into '*'.
    * The reshape / reduction patterns are anchored to avoid greedy over-match.
    * dfn bodies (⍺, ⍵) are mapped to standard Python lambda parameters.
    * ⎕IO awareness: if index origin is 1 (default), arange starts at 1.
    """

    def __init__(self, index_origin: int = 1) -> None:
        self.io = index_origin   # APL ⎕IO value (1 or 0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _arange(self, n: str) -> str:
        """Return np.arange respecting ⎕IO."""
        if self.io == 1:
            return f"np.arange(1, {n} + 1)"
        return f"np.arange({n})"

    # ------------------------------------------------------------------
    # Main translation entry-point
    # ------------------------------------------------------------------

    def translate_expr(self, expr: str) -> str:  # noqa: C901  (complexity OK for a translator)
        """Translate a single APL RHS expression to Python."""
        e = expr.strip()

        # ── Step 0: dfn special names ──────────────────────────────────
        e = e.replace("⍺⍺", "_op")    # operator left operand
        e = e.replace("⍵⍵", "_rop")   # operator right operand
        e = e.replace("⍺",  "_left")
        e = e.replace("⍵",  "_right")
        e = e.replace("∇",  "_self")   # self-reference inside dfn

        # ── Step 1: Unicode minus / not-equal / relational ────────────
        e = e.replace("−", "-")
        e = e.replace("–", "-")
        e = e.replace("≠", "!=")
        e = e.replace("≥", ">=")
        e = e.replace("≤", "<=")

        # ── Step 2: Compound operators FIRST (before single chars) ────
        # Inner product: A +.× B  →  np.matmul(A, B)
        e = re.sub(
            r"([A-Za-z_]\w*)\s*\+\.\×\s*([A-Za-z_]\w*)",
            r"np.matmul(\1, \2)",
            e,
        )
        # Outer product: A ∘.× B  →  np.outer(A, B)
        e = re.sub(
            r"([A-Za-z_]\w*)\s*∘\.\×\s*([A-Za-z_]\w*)",
            r"np.outer(\1, \2)",
            e,
        )

        # ── Step 3: Reductions (before scalar op replacement) ──────────
        e = re.sub(r"\+\s*/\s*([A-Za-z0-9_()\[\]\.]+)", r"np.sum(\1)",              e)
        e = re.sub(r"×\s*/\s*([A-Za-z0-9_()\[\]\.]+)", r"np.prod(\1)",             e)
        e = re.sub(r"⌈\s*/\s*([A-Za-z0-9_()\[\]\.]+)", r"np.max(\1)",              e)
        e = re.sub(r"⌊\s*/\s*([A-Za-z0-9_()\[\]\.]+)", r"np.min(\1)",              e)
        e = re.sub(r"-\s*/\s*([A-Za-z0-9_()\[\]\.]+)",  r"np.subtract.reduce(\1)", e)
        e = re.sub(r"÷\s*/\s*([A-Za-z0-9_()\[\]\.]+)",  r"np.divide.reduce(\1)",   e)

        # Scan (prefix reduction) variants
        e = re.sub(r"\+\\\s*([A-Za-z0-9_()\[\]\.]+)", r"np.cumsum(\1)",  e)
        e = re.sub(r"×\\\s*([A-Za-z0-9_()\[\]\.]+)",  r"np.cumprod(\1)", e)

        # ── Step 4: Reshape  N1 N2 … ⍴ expr ───────────────────────────
        def _reshape(m: re.Match[str]) -> str:
            dims  = m.group(1).strip().split()
            inner = m.group(2).strip()
            shape = ", ".join(dims)
            return f"np.reshape({inner}, ({shape},))"

        e = re.sub(r"([0-9]+(?:\s+[0-9]+)*)\s+⍴\s*(.+)", _reshape, e)

        # ── Step 5: Iota and reverse-iota ─────────────────────────────
        e = re.sub(r"⌽\s*⍳\s*([0-9]+)",  lambda m: f"np.flip({self._arange(m.group(1))})", e)
        e = re.sub(r"⍳\s*([0-9]+)",       lambda m: self._arange(m.group(1)),               e)
        e = re.sub(r"⍳\s*([A-Za-z_]\w*)", lambda m: self._arange(m.group(1)),               e)

        # ── Step 6: Monadic array functions ───────────────────────────
        e = re.sub(r"⌽\s*([A-Za-z_]\w*(?:\([^)]*\))?)", r"np.flip(\1)",    e)
        e = re.sub(r"⍉\s*([A-Za-z_]\w*(?:\([^)]*\))?)", r"np.transpose(\1)", e)
        e = re.sub(r"⍋\s*([A-Za-z_]\w*(?:\([^)]*\))?)", r"np.argsort(\1)", e)
        e = re.sub(r"⍒\s*([A-Za-z_]\w*(?:\([^)]*\))?)", r"np.argsort(\1)[::-1]", e)
        # Monadic shape: ⍴V  →  for APL, ⍴ of a vector returns its length
        # as a scalar (a 1-element shape vector, conventionally treated
        # as a scalar count here so "(+/Salary) ÷ ⍴Salary" works as a
        # scalar division rather than dividing by a shape tuple).
        e = re.sub(r"⍴\s*([A-Za-z_]\w*)",               r"np.asarray(\1).shape[0]", e)

        # Ceiling / floor as monadic
        e = re.sub(r"⌈\s*([A-Za-z_]\w*)", r"np.ceil(\1)",  e)
        e = re.sub(r"⌊\s*([A-Za-z_]\w*)", r"np.floor(\1)", e)

        # Absolute value
        e = re.sub(r"\|\s*([A-Za-z_]\w*)", r"np.abs(\1)", e)

        # ── Step 7: Scalar operators (NOW safe to replace) ─────────────
        e = e.replace("×", "*")
        e = e.replace("÷", "/")
        e = e.replace("∧", " & ")
        e = e.replace("∨", " | ")
        e = e.replace("∗", "**")     # APL power (some dialects)

        # ── Step 8: APL-style bare equality → ==  ─────────────────────
        # Only replace isolated '=' not already preceded/followed by =!<>
        e = re.sub(r"(?<![=!<>])=(?![=])", "==", e)

        # ── Step 9: Catenation  (A,B) or bare comma-separated vars ────
        # Explicit catenate: A,B  →  np.concatenate([np.atleast_1d(A), np.atleast_1d(B)])
        e = re.sub(
            r"([A-Za-z_]\w*)\s*,\s*([A-Za-z_0-9_]\w*)",
            r"np.concatenate([np.atleast_1d(\1), np.atleast_1d(\2)])",
            e,
        )

        # ── Step 10: Space-separated numeric literals → NumPy array ────
        # Only when the whole expression is whitespace-separated numbers.
        # APL vector literals (e.g. "45000 52000 61000") must become
        # np.array([...]) — not a plain Python list — so that downstream
        # elementwise arithmetic and comparisons (×, ÷, >, etc.) work
        # correctly. Single scalar literals are left untouched.
        if re.fullmatch(r"-?[0-9]+\.?[0-9]*(\s+-?[0-9]+\.?[0-9]*)+", e):
            parts = e.split()
            e = "np.array([" + ", ".join(parts) + "])"

        # ── Step 11: Balance parentheses ──────────────────────────────
        diff = e.count("(") - e.count(")")
        if diff > 0:
            e += ")" * diff

        return e

    def translate_assignment(self, lhs: str, rhs: str) -> str:
        """Return a Python assignment string for one APL ← statement."""
        return f"{lhs} = {self.translate_expr(rhs)}"

    def needs_numpy(self, python_expr: str) -> bool:
        """Return True if the expression references np.*."""
        return bool(re.search(r"\bnp\.", python_expr))


# ---------------------------------------------------------------------------
# Main agent
# ---------------------------------------------------------------------------

class ConversionAgent:
    """
    APL-to-Python conversion agent.

    Flow
    ----
    1.  Parse the APL source (structural analysis, chunk splitting).
    2a. For programs ≤ CHUNK_SIZE lines: single AI provider call.
    2b. For larger programs: chunk → AI-convert each chunk → stitch results.
    3.  If provider is unavailable or returns invalid output: rule-based
        fallback (no external dependency).
    4.  Normalize, validate syntax, score confidence, return.
    """

    # ------------------------------------------------------------------
    # Syntax validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_python_syntax(code: str) -> bool:
        """Return True iff `code` is syntactically valid Python."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    # ------------------------------------------------------------------
    # Code normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_prints(code: str) -> str:
        """Replace top-level (column-0) print(expr) with result = expr.

        Indented print() calls inside migrate() are left untouched — turning
        those into `result = expr` would make `result` a local variable,
        not the module-level name _ensure_result relies on.
        """
        return re.sub(r"(?m)^print\((.+)\)\s*$", r"result = \1", code)

    @staticmethod
    def _ensure_result(code: str) -> str:
        """
        Guarantee that a top-level `result` name is set by calling migrate().

        Generated code defines a `migrate(inputs=None)` function whose body
        is indented; any `Result = ...` / `result = ...` assignments inside
        that body are LOCAL to the function and must never be referenced at
        module level (doing so raises NameError).

        Rules
        -----
        * Only column-0 (top-level, unindented) lines are considered when
          checking for an existing `result = ...` assignment or deciding
          what to append — indented lines inside migrate() are ignored.
        * If a top-level `result = migrate(...)` (or any top-level
          `result = ...`) already exists, the code is returned unchanged.
        * Otherwise, append `result = migrate()` (or `migrate(None)` if the
          function signature has no default) so the return value of
          migrate() — not any of its internal local variables — becomes the
          module-level `result`.
        * Generic: makes no assumption about variable names used inside
          migrate() (Result, Z, Output, etc.).
        """
        lines = code.splitlines()

        # Names assigned at top level (column 0), e.g. "Result = migrate()"
        # or plain variable assignments outside any function.
        top_level_assign_re = re.compile(r"^([A-Za-z_]\w*)\s*=\s*(.*)$")
        top_level_names: set[str] = set()
        for ln in lines:
            m = top_level_assign_re.match(ln)
            if m:
                top_level_names.add(m.group(1))

        def_match = re.search(
            r"(?m)^def\s+migrate\s*\(\s*([^)]*)\)\s*:", code
        )
        call_expr = "migrate()"
        if def_match:
            params = def_match.group(1).strip()
            if params and "=" not in params:
                call_expr = "migrate(None)"

        # Check for an existing top-level `result = ...` line
        result_re = re.compile(r"^result\s*=\s*(.*)$")
        for idx, ln in enumerate(lines):
            m = result_re.match(ln)
            if not m:
                continue
            rhs = m.group(1).strip()

            # Already correct: result = migrate(...)
            if re.fullmatch(r"migrate\([^)]*\)", rhs):
                return code

            # Buggy pattern: rhs is a bare name that is NOT itself a
            # top-level assignment target (i.e. it's a local variable
            # leaked from inside migrate()). Replace with migrate() call.
            if re.fullmatch(r"[A-Za-z_]\w*", rhs) and rhs not in top_level_names and rhs != "result":
                if def_match:
                    lines[idx] = f"result = {call_expr}"
                    return "\n".join(lines) + "\n"
                # No migrate() to call — leave as-is, nothing better to do
                return code

            # Otherwise (literal, expression of top-level names, etc.) —
            # treat as already valid.
            return code

        # No top-level `result = ...` line exists at all.
        if def_match:
            return code.rstrip() + f"\nresult = {call_expr}\n"

        # No migrate() function at all (unexpected for our pipeline) —
        # fall back to the last top-level assignment, if any.
        if top_level_names:
            # Preserve insertion order: re-scan for the last assigned name
            last = None
            for ln in lines:
                m = top_level_assign_re.match(ln)
                if m:
                    last = m.group(1)
            return code.rstrip() + f"\nresult = {last}\n"
        return code.rstrip() + "\nresult = None\n"

    @staticmethod
    def _normalize_code(raw: str) -> str:
        """Full normalization pipeline applied to AI-generated code."""
        code = raw.rstrip() + "\n"
        code = ConversionAgent._strip_prints(code)
        code = ConversionAgent._ensure_result(code)
        return code

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _score_confidence(
        python_code: str,
        apl_code: str,
        provider_score: float | None,
        fallback: bool,
    ) -> float:
        """
        Compute a calibrated 0-100 confidence score.

        Heuristics
        ----------
        * Start from provider score (if available) or 60 for rule-based.
        * Penalise for unresolved APL glyphs left in the output.
        * Reward for every recognised NumPy primitive used.
        * Penalise if the output is suspiciously short relative to input.
        """
        if fallback:
            base = 60.0
        else:
            base = float(provider_score) if provider_score is not None else 65.0

        # Penalise residual APL symbols (≠, ←, ⍴, ⌽, etc.) in output
        residual_glyphs = len(re.findall(r"[←⍴⌽⍳⌈⌊÷×∧∨⍉⍋⍒]", python_code))
        base -= residual_glyphs * 4

        # Reward recognised NumPy usage
        np_hits = len(re.findall(
            r"\bnp\.(sum|prod|max|min|reshape|matmul|outer|flip|arange|"
            r"cumsum|cumprod|argsort|transpose|abs|ceil|floor|concatenate|"
            r"atleast_1d|subtract|divide)\b",
            python_code,
        ))
        base += min(np_hits * 2, 15)

        # Penalise extremely short output for non-trivial input
        apl_lines  = len([l for l in apl_code.splitlines() if l.strip()])
        py_lines   = len([l for l in python_code.splitlines() if l.strip()])
        if apl_lines > 5 and py_lines < apl_lines // 2:
            base -= 10

        return round(min(100.0, max(0.0, base)), 1)

    # ------------------------------------------------------------------
    # Rule-based fallback (offline / provider-unavailable path)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_conversion(
        apl_code: str,
        understanding: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Pure rule-based APL → Python conversion.

        Returns a `migrate(inputs)` wrapper that accepts a dict of free
        variables.  Uses lexical scoping instead of `globals()` mutation
        for safe execution in sandboxed environments.
        """
        parser  = _APLParser(apl_code)
        sysovr  = parser.get_system_var_overrides()
        io      = int(sysovr.get("⎕IO", "1"))
        emitter = _RuleEmitter(index_origin=io)

        clean_lines = parser.get_clean_lines()
        free_vars   = parser.find_unassigned_variables()

        body_lines:   list[str] = []
        assigned:     list[str] = []
        needs_numpy             = False
        expr_counter            = 0

        assign_re = re.compile(r"^([A-Za-z_⎕]\w*)\s*←(.*)$")

        for ln in clean_lines:
            m = assign_re.match(ln)
            if m:
                lhs, rhs = m.group(1).strip(), m.group(2).strip()
                # Skip system-variable self-assignments (already handled)
                if lhs in APL_SYSTEM_VARS:
                    continue
                py_line = emitter.translate_assignment(lhs, rhs)
                if emitter.needs_numpy(py_line):
                    needs_numpy = True
                body_lines.append(py_line)
                assigned.append(lhs)
            else:
                # Bare expression line
                py_expr = emitter.translate_expr(ln)
                if emitter.needs_numpy(py_expr):
                    needs_numpy = True
                expr_counter += 1
                name = f"_expr_{expr_counter}"
                body_lines.append(f"{name} = {py_expr}")
                assigned.append(name)

        # Determine the final result variable
        result_var = "None"
        for var in reversed(assigned):
            if var.lower() in ("result", "z", "r", "out", "output"):
                result_var = var
                break
        if result_var == "None" and assigned:
            result_var = assigned[-1]

        # ── Build output code ──────────────────────────────────────────
        lines: list[str] = []

        if needs_numpy:
            lines.append("import numpy as np")
            lines.append("")

        if io != 1:
            lines.append(f"# ⎕IO={io} detected — zero-based indexing applied")
            lines.append("")

        # Docstring listing free parameters
        params = sorted(free_vars) if free_vars else []
        param_doc = "\n    ".join(f"{p}: ..." for p in params) if params else "    (none)"

        lines += [
            "def migrate(inputs: dict | None = None):",
            '    """',
            "    Migrated APL program.",
            "",
            "    Parameters (pass via `inputs` dict)",
            "    ------------------------------------",
        ]
        for p in params:
            lines.append(f"    {p}: APL free variable")
        lines += [
            '    """',
            "    # Unpack caller-supplied inputs into local scope",
            "    _inp = inputs or {}",
        ]
        for p in params:
            lines.append(f"    {p} = _inp.get({p!r})")
        if needs_numpy and params:
            lines.append("")
            lines.append("    # Coerce inputs to NumPy arrays")
            for p in params:
                lines.append(
                    f"    if {p} is not None:"
                )
                lines.append(
                    f"        {p} = np.asarray({p})"
                )

        lines.append("")
        for bl in body_lines:
            lines.append(f"    {bl}")

        lines += [
            "",
            f"    result = {result_var}",
            "    return result",
            "",
            "",
            "# ── Top-level execution ──────────────────────────────────────────",
            "result = migrate()",
        ]

        python_code = "\n".join(lines)

        confidence = ConversionAgent._score_confidence(
            python_code, apl_code, provider_score=None, fallback=True
        )

        return {
            "python_code": python_code,
            "explanation": (
                "Rule-based APL→Python conversion using ordered regex substitutions. "
                "Supports: reductions, scans, reshape, iota, outer/inner product, "
                "catenation, ceiling/floor, sort, transpose, and ⎕IO awareness."
            ),
            "confidence_score": confidence,
            "syntax_valid": ConversionAgent.validate_python_syntax(python_code),
            "fallback": True,
        }

    # ------------------------------------------------------------------
    # AI provider helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompts(
        apl_chunk: str,
        understanding: dict[str, Any],
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> tuple[str, str]:
        """Build system + user prompt for a single chunk."""
        system_prompt = textwrap.dedent("""
            You are an expert Dyalog APL to Python migration engine.
            Rules:
            1. Produce ONLY a JSON object with keys: python_code, explanation, confidence_score.
            2. python_code must be syntactically valid Python 3.10+ using NumPy where appropriate.
            3. Wrap all logic in a function named `migrate(inputs=None)` that accepts a dict of
               free APL variables and returns a `result` value.
            4. Do NOT use globals(). Do NOT include bare print() calls.
            5. Preserve ALL variable names and assignment order from the APL source.
            6. Emit `import numpy as np` inside python_code if NumPy is used.
            7. confidence_score is a float 0-100 reflecting your certainty.
        """).strip()

        chunk_note = ""
        if total_chunks > 1:
            chunk_note = (
                f"\n\n[Chunk {chunk_index + 1} of {total_chunks}. "
                "Assume prior chunks already defined earlier variables.]"
            )

        program_type = understanding.get("program_type", "")
        variables    = understanding.get("variables", [])
        operations   = understanding.get("operations", [])

        user_prompt = (
            f"Convert this Dyalog APL chunk to Python.\n\n"
            f"Program type: {program_type}\n"
            f"Known variables: {variables}\n"
            f"Known operations: {operations}\n"
            f"{chunk_note}\n\n"
            f"APL Code:\n```\n{apl_chunk}\n```\n\n"
            "Respond with valid JSON only (no markdown fences)."
        )

        return system_prompt, user_prompt

    @staticmethod
    async def _call_provider_with_retry(
        provider: Any,
        user_prompt: str,
        system_prompt: str,
        provider_name: str,
    ) -> dict[str, Any] | None:
        """
        Call provider with exponential back-off retry.

        Returns the raw provider response dict, or None on total failure.
        """
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await provider.generate(user_prompt, system_prompt)
                if response and "error" not in response:
                    return response
                err = (response or {}).get("error", "unknown")
                logger.warning("Provider attempt %d returned error: %s", attempt + 1, err)
            except Exception as exc:
                last_exc = exc
                logger.warning("Provider attempt %d raised %s: %s", attempt + 1, type(exc).__name__, exc)

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.debug("Retrying in %.1fs…", delay)
                await asyncio.sleep(delay)

        if last_exc:
            logger.error("All %d provider attempts failed. Last error: %s", MAX_RETRIES, last_exc)
        return None

    # ------------------------------------------------------------------
    # Chunk stitching
    # ------------------------------------------------------------------

    @staticmethod
    def _stitch_chunks(chunk_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Merge multiple per-chunk conversion results into one coherent output.

        Strategy
        --------
        * Collect all imports at the top (deduplicated).
        * Merge migrate() bodies in order, removing duplicate headers.
        * Average confidence scores (weighted by chunk length).
        * Concatenate explanations.
        """
        import_lines: list[str] = []
        body_sections: list[str] = []
        confidence_sum = 0.0
        explanations: list[str] = []

        # Regex to find import lines and def migrate(...) header
        import_re    = re.compile(r"^import\s+.+|^from\s+\S+\s+import\s+.+", re.MULTILINE)
        fn_header_re = re.compile(
            r"(?ms)^def migrate.*?:\s*(?:\"\"\".*?\"\"\")?", re.DOTALL
        )
        body_re      = re.compile(r"(?ms)^def migrate.*?(?=\n\n|\Z)", re.DOTALL)

        for i, res in enumerate(chunk_results):
            code = res.get("python_code", "")
            confidence_sum += res.get("confidence_score", 60.0)
            explanations.append(res.get("explanation", ""))

            # Collect imports
            for imp in import_re.findall(code):
                if imp not in import_lines:
                    import_lines.append(imp)

            # Extract the body of migrate()
            fn_match = body_re.search(code)
            if fn_match:
                fn_text = fn_match.group(0)
                # Strip the 'def migrate...:' header (keep only inner body)
                inner = fn_header_re.sub("", fn_text).strip()
                if inner:
                    body_sections.append(f"    # ── Chunk {i + 1} ──\n" + textwrap.indent(inner, "    "))
            else:
                # No function found; indent raw code as-is
                body_sections.append(f"    # ── Chunk {i + 1} ──\n" + textwrap.indent(code.strip(), "    "))

        avg_confidence = confidence_sum / len(chunk_results) if chunk_results else 0.0

        # Build the unified migrate() function
        header = "\n".join(import_lines) + "\n\n" if import_lines else ""
        body   = "\n\n".join(body_sections)

        merged_fn = (
            "def migrate(inputs: dict | None = None):\n"
            '    """Merged APL migration across all chunks."""\n'
            "    _inp = inputs or {}\n\n"
            + body
            + "\n\n    return result\n"
        )

        python_code = header + merged_fn + "\n\nresult = migrate()\n"

        return {
            "python_code": python_code,
            "explanation": " | ".join(e for e in explanations if e),
            "confidence_score": round(avg_confidence, 1),
            "syntax_valid": ConversionAgent.validate_python_syntax(python_code),
        }

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    @staticmethod
    async def convert(
        apl_code: str,
        understanding: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert APL source to optimised Python.

        Parameters
        ----------
        apl_code:     Full APL source (any size).
        understanding: Dict from the understanding agent with keys
                       program_type, variables, operations, etc.

        Returns
        -------
        {
            python_code:      str,
            explanation:      str,
            confidence_score: float (0-100),
            syntax_valid:     bool,
            fallback:         bool,   # True if rule-based path was used
        }
        """
        # ── 1. Structural parse ────────────────────────────────────────
        parser = _APLParser(apl_code)
        chunks = parser.split_into_chunks(CHUNK_SIZE)
        total  = len(chunks)

        logger.info("APL source: %d logical lines → %d chunk(s)", len(parser.get_clean_lines()), total)

        # ── 2. Acquire provider ────────────────────────────────────────
        try:
            provider      = ProviderFactory.get_provider()
            provider_name = ProviderFactory.get_active_provider_name()
        except ScaffoldedProviderError as exc:
            logger.warning("Provider scaffolded/unconfigured: %s → rule-based fallback", exc)
            return ConversionAgent._fallback_conversion(apl_code, understanding)
        except Exception as exc:
            logger.warning("Provider unavailable: %s → rule-based fallback", exc)
            return ConversionAgent._fallback_conversion(apl_code, understanding)

        # ── 3. Convert each chunk via AI ───────────────────────────────
        chunk_results: list[dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            system_prompt, user_prompt = ConversionAgent._build_prompts(
                chunk, understanding, chunk_index=idx, total_chunks=total
            )

            raw = await ConversionAgent._call_provider_with_retry(
                provider, user_prompt, system_prompt, provider_name
            )

            if raw is None:
                logger.warning("Chunk %d/%d: provider failed → rule-based fallback for chunk", idx + 1, total)
                chunk_results.append(
                    ConversionAgent._fallback_conversion(chunk, understanding)
                )
                continue

            normalized = ResponseNormalizer.normalize_conversion_response(
                raw, provider_name=provider_name
            )

            py_code     = normalized.get("python_code", "")
            explanation = normalized.get("explanation", "")
            prov_score  = normalized.get("confidence_score")

            if not py_code:
                logger.warning("Chunk %d/%d: empty python_code → rule-based fallback", idx + 1, total)
                provider._log_fallback_triggered(provider_name, "empty_python_code")
                chunk_results.append(
                    ConversionAgent._fallback_conversion(chunk, understanding)
                )
                continue

            # Normalize before syntax check
            py_code = ConversionAgent._normalize_code(py_code)

            if not ConversionAgent.validate_python_syntax(py_code):
                logger.warning("Chunk %d/%d: syntax error → rule-based fallback", idx + 1, total)
                provider._log_fallback_triggered(provider_name, "syntax_error")
                chunk_results.append(
                    ConversionAgent._fallback_conversion(chunk, understanding)
                )
                continue

            confidence = ConversionAgent._score_confidence(
                py_code, chunk, provider_score=prov_score, fallback=False
            )

            chunk_results.append({
                "python_code":      py_code,
                "explanation":      explanation,
                "confidence_score": confidence,
                "syntax_valid":     True,
                "fallback":         False,
            })

        # ── 4. Stitch chunks (or return single result directly) ────────
        if total == 1:
            result = chunk_results[0]
        else:
            result = ConversionAgent._stitch_chunks(chunk_results)

        # ── 5. Final syntax gate ───────────────────────────────────────
        if not result.get("syntax_valid"):
            logger.error("Stitched output has syntax errors → rule-based fallback on full source")
            return ConversionAgent._fallback_conversion(apl_code, understanding)

        result.setdefault("fallback", False)
        return result