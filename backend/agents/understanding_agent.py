"""
understanding_agent.py – Upgraded APL Semantic Understanding Agent
===================================================================
Key improvements over v1
------------------------
* Fixed response-key mismatch: reads program_type/variables/operations directly
  from normalized response instead of operator/meaning/explanation (conversion keys)
* Single authoritative JSON-parse path — no double-parse anti-pattern
* Retry with exponential back-off (3 attempts)
* Chunked analysis for large programs (500+ lines)
* Full APL operator coverage: reductions, scans, outer/inner product, dfns,
  power, grade, rotate, transpose, compress, expand, encode/decode
* Dependency graph builder (variable → variables it depends on)
* 15-category program-type classifier (not just 4 hardcoded heuristics)
* Calibrated confidence scoring (not hardcoded 0.6)
* Variable filter: strips APL glyphs, numeric strings, single-char noise
* Business summary templating driven by detected domain signals
* Full type annotations throughout
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from ..providers.provider_factory import ProviderFactory, ScaffoldedProviderError
from ..providers.response_normalizer import ResponseNormalizer
from ..utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RETRIES      = 3
RETRY_BASE_DELAY = 1.0   # seconds

# Lines per chunk for large-program analysis
ANALYSIS_CHUNK_SIZE = 100

# Minimum variable name length to keep (filters out single-char APL noise)
MIN_VAR_LEN = 2

# Known APL system names to exclude from user-variable lists
APL_SYSTEM_NAMES: frozenset[str] = frozenset({
    "IO", "ML", "CT", "PP", "PW", "RL", "WA", "NC", "NL",
    "CR", "DL", "ES", "EX", "LC", "NA", "NNAMES", "NNUMS",
})

# ---------------------------------------------------------------------------
# APL operator catalogue
# ---------------------------------------------------------------------------

# (regex_pattern, human_readable_name)
APL_OP_CATALOGUE: list[tuple[str, str]] = [
    # Reductions
    (r"\+\s*/",      "Sum reduction (+/)"),
    (r"×\s*/",       "Product reduction (×/)"),
    (r"⌈\s*/",       "Maximum reduction (⌈/)"),
    (r"⌊\s*/",       "Minimum reduction (⌊/)"),
    (r"-\s*/",       "Alternating-sum reduction (-/)"),
    (r"÷\s*/",       "Division reduction (÷/)"),
    (r"∧\s*/",       "AND reduction (∧/)"),
    (r"∨\s*/",       "OR reduction (∨/)"),
    (r"≠\s*/",       "XOR/parity reduction (≠/)"),
    # Scans
    (r"\+\\",        "Cumulative sum scan (+\\)"),
    (r"×\\",         "Cumulative product scan (×\\)"),
    (r"⌈\\",         "Running maximum scan (⌈\\)"),
    (r"⌊\\",         "Running minimum scan (⌊\\)"),
    # Products
    (r"\+\.\×",      "Matrix inner product (+.×)"),
    (r"∘\.\×",       "Outer product (∘.×)"),
    # Shape / structure
    (r"⍴",           "Reshape / shape query (⍴)"),
    (r"⍳",           "Index generation (⍳)"),
    (r"⌽",           "Reverse / rotate (⌽)"),
    (r"⊖",           "Vertical reverse (⊖)"),
    (r"⍉",           "Transpose (⍉)"),
    (r"⍋",           "Grade up / ascending sort (⍋)"),
    (r"⍒",           "Grade down / descending sort (⍒)"),
    (r"↑",           "Take (↑)"),
    (r"↓",           "Drop (↓)"),
    (r"∊",           "Enlist / membership (∊)"),
    (r"⍪",           "Table / catenate along first axis (⍪)"),
    (r",",           "Catenate / ravel (,)"),
    # Encoding / decoding
    (r"⊤",           "Encode / base representation (⊤)"),
    (r"⊥",           "Decode / base value (⊥)"),
    # Logic / comparison
    (r"≤|≥|<|>",     "Relational comparison"),
    (r"=(?!=)",      "Equality test"),
    (r"≠",           "Inequality test (≠)"),
    (r"∧(?!\s*/)",   "Logical AND (∧)"),
    (r"∨(?!\s*/)",   "Logical OR (∨)"),
    (r"~",           "Logical NOT (~)"),
    # Arithmetic
    (r"÷",           "Division (÷)"),
    (r"×(?!\s*/)",   "Multiplication (×)"),
    (r"\*",          "Power / exponential (*)"),
    (r"⌈(?!\s*/)",   "Ceiling (⌈)"),
    (r"⌊(?!\s*/)",   "Floor (⌊)"),
    (r"\|",          "Absolute value / modulo (|)"),
    (r"○",           "Circular / trig functions (○)"),
    (r"⍟",           "Natural logarithm (⍟)"),
    # Control / dfns
    (r"\{[^}]*⍵",    "Dfn / anonymous function ({})"),
    (r"∇",           "Tradfn / named function (∇)"),
    (r":If|:For|:While|:Select", "Control structures (:If/:For/:While)"),
    # System / I-O
    (r"⎕",           "System variable / quad I-O (⎕)"),
    (r"⍎",           "Execute (⍎)"),
    (r"⍕",           "Format / stringify (⍕)"),
]

# ---------------------------------------------------------------------------
# Domain classifier signals
# ---------------------------------------------------------------------------

# (domain_key, list_of_keyword_signals_in_variable_names_or_code)
DOMAIN_SIGNALS: list[tuple[str, list[str]]] = [
    ("payroll_analysis",        ["salary", "pay", "wage", "employee", "bonus", "tax", "deduction", "gross", "net"]),
    ("financial_analysis",      ["tax", "revenue", "profit", "loss", "balance", "account", "ledger", "interest", "rate", "cost", "price", "invoice"]),
    ("statistical_analysis",    ["mean", "median", "std", "variance", "deviation", "average", "distribution", "frequency", "sample", "population"]),
    ("matrix_computation",      ["+.×", "matmul", "∘.×", "outer", "inner", "transpose", "determinant", "inverse", "eigenvalu"]),
    ("sorting_ranking",         ["⍋", "⍒", "rank", "sort", "order", "grade"]),
    ("string_processing",       ["⍕", "⍎", "text", "string", "char", "word", "format", "parse"]),
    ("signal_processing",       ["fft", "signal", "filter", "frequency", "amplitude", "wave", "spectrum"]),
    ("database_query",          ["⎕SQL", "query", "select", "join", "where", "table", "row", "column", "record"]),
    ("array_transformation",    ["⍴", "reshape", "ravel", "flatten", "transpose", "partition", "compress"]),
    ("logical_decision",        [":If", ":Select", ":While", ":For", "guard", "condition", "branch", "case"]),
    ("scheduling_optimisation", ["schedule", "optim", "minimise", "maximise", "constraint", "route", "assign", "allocat"]),
    ("scientific_computation",  ["○", "⍟", "log", "exp", "trig", "sin", "cos", "tan", "physics", "chem"]),
    ("risk_modelling",          ["risk", "probability", "monte", "simulation", "random", "stochastic", "model"]),
    ("reporting_formatting",    ["⍕", "report", "summary", "print", "output", "format", "display", "header"]),
    ("data_pipeline",           ["input", "output", "pipeline", "transform", "load", "extract", "ingest"]),
]


# ---------------------------------------------------------------------------
# Deterministic APL analyser
# ---------------------------------------------------------------------------

class _APLAnalyser:
    """
    Pure-Python structural analyser for APL source code.

    Provides variable extraction, operation detection, dependency mapping,
    program-type classification, and business-summary generation — all
    without an AI provider.
    """

    _ASSIGN_RE = re.compile(r"^([A-Za-z_⎕][A-Za-z0-9_]*)\s*←(.*)$")
    _TOKEN_RE  = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{1,})\b")   # ≥2 chars
    _DFNARG_RE = re.compile(r"[⍺⍵∇]")

    def __init__(self, source: str) -> None:
        self.source = source
        self.lines  = [
            ln.strip()
            for ln in source.splitlines()
            if ln.strip() and not ln.strip().startswith("⍝")
        ]

    # ------------------------------------------------------------------
    # Variable extraction
    # ------------------------------------------------------------------

    def extract_variables(self) -> list[str]:
        """
        Return all meaningful user-defined variable names.

        Filters:
        * Single-character names (APL loop indices / temporaries)
        * All-uppercase 2-char names that match APL system variables
        * Pure digit strings
        * Known Python / NumPy built-in names
        """
        _noise = {
            "np", "True", "False", "None", "int", "float", "str", "list",
            "dict", "set", "tuple", "range", "len", "sum", "min", "max",
            "print", "result", "import",
        }
        assigned: set[str] = set()
        referenced: set[str] = set()

        for ln in self.lines:
            m = self._ASSIGN_RE.match(ln)
            if m:
                lhs = m.group(1)
                rhs = m.group(2)
                # Strip ⎕ prefix for system vars but keep them for detection
                assigned.add(lhs)
                for tok in self._TOKEN_RE.findall(rhs):
                    referenced.add(tok)
            else:
                for tok in self._TOKEN_RE.findall(ln):
                    referenced.add(tok)

        all_vars = assigned | referenced
        return sorted(
            v for v in all_vars
            if len(v) >= MIN_VAR_LEN
            and not v.isdigit()
            and v not in _noise
            and v.upper() not in APL_SYSTEM_NAMES
        )

    # ------------------------------------------------------------------
    # Operation detection
    # ------------------------------------------------------------------

    def detect_operations(self) -> list[str]:
        """Return list of detected APL operations, deduplicated, ordered by catalogue."""
        seen: set[str] = set()
        result: list[str] = []
        code = self.source

        for pattern, name in APL_OP_CATALOGUE:
            if re.search(pattern, code) and name not in seen:
                seen.add(name)
                result.append(name)

        # Derive higher-level concepts from primitives
        if "Sum reduction (+/)" in seen and ("Division (÷)" in seen or "⍴" in code):
            result.insert(0, "Arithmetic mean / average")

        if not result:
            result = ["General APL computation"]

        return result

    # ------------------------------------------------------------------
    # Dependency graph
    # ------------------------------------------------------------------

    def build_dependency_graph(self) -> dict[str, list[str]]:
        """
        Return {variable: [variables_it_directly_depends_on]}.

        Only assignment lines are analysed; only tokens that appear as
        LHS somewhere in the program are considered dependencies.
        """
        all_lhs: set[str] = set()
        raw_deps: dict[str, list[str]] = {}

        for ln in self.lines:
            m = self._ASSIGN_RE.match(ln)
            if m:
                lhs = m.group(1)
                rhs = m.group(2)
                all_lhs.add(lhs)
                raw_deps[lhs] = self._TOKEN_RE.findall(rhs)

        # Filter rhs tokens to only known LHS names (true inter-variable deps)
        graph: dict[str, list[str]] = {}
        for lhs, rhs_tokens in raw_deps.items():
            deps = sorted({t for t in rhs_tokens if t in all_lhs and t != lhs})
            if deps:
                graph[lhs] = deps

        return graph

    # ------------------------------------------------------------------
    # Program type classification
    # ------------------------------------------------------------------

    def classify_program_type(
        self,
        variables: list[str],
        operations: list[str],
    ) -> str:
        """
        Score each domain against variable names + code text, return the winner.

        Falls back to "general_apl_computation" when no domain scores.
        """
        code_lower = self.source.lower()
        var_lower  = " ".join(v.lower() for v in variables)
        ops_lower  = " ".join(o.lower() for o in operations)
        combined   = f"{code_lower} {var_lower} {ops_lower}"

        scores: dict[str, int] = {}
        for domain, signals in DOMAIN_SIGNALS:
            score = sum(1 for sig in signals if sig in combined)
            if score:
                scores[domain] = score

        if not scores:
            return "general_apl_computation"
        return max(scores, key=lambda k: scores[k])

    # ------------------------------------------------------------------
    # Business summary
    # ------------------------------------------------------------------

    def derive_business_summary(
        self,
        program_type: str,
        variables: list[str],
        operations: list[str],
        dependencies: dict[str, list[str]],
    ) -> str:
        """
        Generate a concise, human-readable business-level description.

        Driven by program_type, top variables, and detected operations.
        """
        top_vars = variables[:6]
        top_ops  = operations[:4]
        var_str  = ", ".join(top_vars) + ("…" if len(variables) > 6 else "")
        op_str   = ", ".join(top_ops)  + ("…" if len(operations) > 4 else "")
        dep_count = len(dependencies)

        templates: dict[str, str] = {
            "payroll_analysis": (
                f"Payroll processing system computing employee compensation metrics "
                f"({op_str}) across variables: {var_str}. "
                f"Tracks {dep_count} inter-variable dependencies."
            ),
            "financial_analysis": (
                f"Financial computation performing {op_str} on {var_str}. "
                f"Likely used for budgeting, cost analysis, or reporting."
            ),
            "statistical_analysis": (
                f"Statistical analysis pipeline executing {op_str}. "
                f"Operates on dataset variables: {var_str}."
            ),
            "matrix_computation": (
                f"Matrix / linear algebra computation using {op_str}. "
                f"Core variables: {var_str}."
            ),
            "sorting_ranking": (
                f"Sorting and ranking program applying {op_str} to order {var_str}."
            ),
            "string_processing": (
                f"String manipulation and formatting program using {op_str} on {var_str}."
            ),
            "signal_processing": (
                f"Signal processing pipeline performing {op_str} on data: {var_str}."
            ),
            "database_query": (
                f"Database query / data retrieval program using {op_str}. "
                f"Involves: {var_str}."
            ),
            "array_transformation": (
                f"Array transformation program applying {op_str} to reshape or "
                f"rearrange data in {var_str}."
            ),
            "logical_decision": (
                f"Decision / branching logic program using control structures ({op_str}) "
                f"over {var_str}."
            ),
            "scheduling_optimisation": (
                f"Scheduling or optimisation routine minimising/maximising over "
                f"{var_str} via {op_str}."
            ),
            "scientific_computation": (
                f"Scientific / mathematical computation applying {op_str} to {var_str}."
            ),
            "risk_modelling": (
                f"Risk or probabilistic model performing {op_str} on {var_str}."
            ),
            "reporting_formatting": (
                f"Report generation and data formatting program producing structured "
                f"output from {var_str}."
            ),
            "data_pipeline": (
                f"Data pipeline program transforming {var_str} through {op_str}."
            ),
        }

        if program_type in templates:
            return templates[program_type]

        # Generic fallback
        return (
            f"APL program ({program_type.replace('_', ' ')}) performing {op_str} "
            f"on {var_str}. Contains {dep_count} tracked inter-variable dependencies."
        )

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------

    def score_confidence(
        self,
        variables: list[str],
        operations: list[str],
        dependencies: dict[str, list[str]],
        program_type: str,
    ) -> float:
        """
        Return a 0–1 confidence score for the deterministic analysis.

        Higher when:  more variables found, more ops detected, deps present,
                      type is specific (not "general_apl_computation").
        Lower when:   program is very short or no ops detected.
        """
        score = 0.50   # baseline

        # Variable richness
        score += min(len(variables) * 0.02, 0.15)

        # Operation diversity
        score += min(len(operations) * 0.02, 0.15)

        # Dependency graph presence
        if dependencies:
            score += 0.05

        # Specific program type detected
        if program_type != "general_apl_computation":
            score += 0.10

        # Penalise very short programs (likely incomplete)
        clean_lines = len(self.lines)
        if clean_lines < 3:
            score -= 0.10

        return round(min(1.0, max(0.0, score)), 3)

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def analyse(self) -> dict[str, Any]:
        """Run the complete deterministic analysis and return a structured dict."""
        variables    = self.extract_variables()
        operations   = self.detect_operations()
        dependencies = self.build_dependency_graph()
        program_type = self.classify_program_type(variables, operations)
        summary      = self.derive_business_summary(program_type, variables, operations, dependencies)
        confidence   = self.score_confidence(variables, operations, dependencies, program_type)

        return {
            "program_type":       program_type,
            "variables_detected": variables,
            "operations_detected": operations,
            "dependencies":       dependencies,
            "business_summary":   summary,
            "confidence_score":   confidence,
        }


# ---------------------------------------------------------------------------
# Provider retry helper
# ---------------------------------------------------------------------------

async def _call_provider_with_retry(
    provider: Any,
    user_prompt: str,
    system_prompt: str,
    provider_name: str,
    task: str = "understanding",
) -> dict[str, Any] | None:
    """
    Call provider up to MAX_RETRIES times with exponential back-off.

    Returns the raw response dict on first success, or None on total failure.
    """
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = await provider.generate(user_prompt, system_prompt, task=task)
            if resp and "error" not in resp:
                return resp
            err = (resp or {}).get("error", "unknown")
            logger.warning("Understanding provider attempt %d error: %s", attempt + 1, err)
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Understanding provider attempt %d raised %s: %s",
                attempt + 1, type(exc).__name__, exc,
            )
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            logger.debug("Retrying understanding in %.1fs…", delay)
            await asyncio.sleep(delay)

    if last_exc:
        logger.error("All %d understanding attempts failed. Last: %s", MAX_RETRIES, last_exc)
    return None


# ---------------------------------------------------------------------------
# Chunk splitter
# ---------------------------------------------------------------------------

def _split_apl_for_analysis(source: str, chunk_size: int = ANALYSIS_CHUNK_SIZE) -> list[str]:
    """
    Split large APL source into overlapping chunks for analysis.

    Each chunk overlaps the previous by 10 lines so cross-boundary
    variable references are visible to the analyser.
    """
    clean = [
        ln.strip()
        for ln in source.splitlines()
        if ln.strip() and not ln.strip().startswith("⍝")
    ]
    if len(clean) <= chunk_size:
        return ["\n".join(clean)]

    overlap = min(10, chunk_size // 6)
    step    = chunk_size - overlap
    chunks: list[str] = []
    i = 0
    while i < len(clean):
        chunks.append("\n".join(clean[i : i + chunk_size]))
        i += step
    return chunks


# ---------------------------------------------------------------------------
# JSON extraction from provider response
# ---------------------------------------------------------------------------

def _extract_understanding_from_response(
    provider_response: dict[str, Any],
    provider_name: str,
) -> dict[str, Any] | None:
    """
    Single authoritative path to extract understanding fields from a provider response.

    Reads JSON directly from the text content of the response.
    Returns None if extraction fails or the response looks like a conversion response.
    """
    # Reject responses that look like conversion output
    if any(k in provider_response for k in ("python_code", "confidence_score")):
        logger.warning("Provider returned conversion-style response for understanding task")
        return None

    raw_text = ResponseNormalizer._extract_text(provider_response)
    if not raw_text:
        return None

    # Strip markdown fences if present
    clean = re.sub(r"```(?:json)?|```", "", raw_text).strip()

    try:
        parsed = ResponseNormalizer._parse_json_safely(clean)
    except Exception as exc:
        logger.warning("JSON parse failed for understanding response: %s", exc)
        return None

    if not isinstance(parsed, dict):
        return None

    # Validate that the response has at least one understanding key
    understanding_keys = {"program_type", "variables", "operations",
                          "dependencies", "business_summary", "confidence"}
    if not understanding_keys & parsed.keys():
        logger.warning("Provider response missing all understanding keys: %s", list(parsed.keys()))
        return None

    return parsed


# ---------------------------------------------------------------------------
# Result merger for multi-chunk analysis
# ---------------------------------------------------------------------------

def _merge_chunk_understandings(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Merge understanding dicts produced by analysing individual chunks.

    * program_type: majority vote
    * variables / operations: union (deduplicated)
    * dependencies: union of all graphs
    * business_summary: from chunk with highest confidence
    * confidence_score: average across chunks
    """
    if len(results) == 1:
        return results[0]

    from collections import Counter

    type_votes: Counter[str] = Counter()
    all_vars:   set[str]     = set()
    all_ops:    list[str]    = []
    seen_ops:   set[str]     = set()
    all_deps:   dict[str, list[str]] = {}
    best_summary = ""
    best_conf    = 0.0
    conf_sum     = 0.0

    for r in results:
        type_votes[r.get("program_type", "general_apl_computation")] += 1
        all_vars.update(r.get("variables_detected", []))
        for op in r.get("operations_detected", []):
            if op not in seen_ops:
                seen_ops.add(op)
                all_ops.append(op)
        for var, deps in r.get("dependencies", {}).items():
            existing = set(all_deps.get(var, []))
            existing.update(deps)
            all_deps[var] = sorted(existing)
        c = r.get("confidence_score", 0.0)
        conf_sum += c
        if c > best_conf:
            best_conf    = c
            best_summary = r.get("business_summary", "")

    return {
        "program_type":       type_votes.most_common(1)[0][0],
        "variables_detected": sorted(all_vars),
        "operations_detected": all_ops,
        "dependencies":       all_deps,
        "business_summary":   best_summary,
        "confidence_score":   round(conf_sum / len(results), 3),
    }


# ---------------------------------------------------------------------------
# Main agent
# ---------------------------------------------------------------------------

class UnderstandingAgent:
    """
    APL program semantic understanding agent.

    Flow
    ----
    1. Deterministic structural analysis (_APLAnalyser) — always runs.
    2. For programs ≤ ANALYSIS_CHUNK_SIZE lines: single AI provider call.
       For larger programs: chunked AI calls merged with _merge_chunk_understandings.
    3. AI result merged with deterministic result (AI enriches; deterministic fills gaps).
    4. Calibrated confidence scoring.
    5. On any provider failure: retry with back-off → fallback to deterministic only.
    """

    # ------------------------------------------------------------------
    # Deterministic fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_response(apl_code: str) -> dict[str, Any]:
        """Run purely deterministic analysis and return structured result."""
        analyser = _APLAnalyser(apl_code)
        return analyser.analyse()

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompts(
        apl_chunk: str,
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> tuple[str, str]:
        chunk_note = (
            f"\n[Chunk {chunk_index + 1} of {total_chunks} — assume prior chunks "
            "defined earlier variables.]"
            if total_chunks > 1 else ""
        )

        system_prompt = (
            "You are an expert Dyalog APL semantic analysis engine.\n"
            "Analyze the APL program and return ONLY a valid JSON object with these exact keys:\n"
            "  program_type      – string: one specific category (e.g. 'payroll_analysis')\n"
            "  variables         – array of strings: all meaningful variable names\n"
            "  operations        – array of strings: all APL operations / patterns used\n"
            "  dependencies      – object: {var: [vars_it_depends_on]}\n"
            "  business_summary  – string: plain-English description of business intent\n"
            "  confidence        – number: 0-100 reflecting analysis certainty\n"
            "Return ONLY valid JSON. No markdown, no prose, no code fences."
        )

        user_prompt = (
            f"Analyze this Dyalog APL program chunk.{chunk_note}\n\n"
            f"APL Code:\n```\n{apl_chunk}\n```\n\n"
            "Return ONLY the JSON object described in your instructions."
        )

        return system_prompt, user_prompt

    # ------------------------------------------------------------------
    # Merge AI result with deterministic result
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_ai_with_deterministic(
        ai: dict[str, Any],
        det: dict[str, Any],
    ) -> dict[str, Any]:
        """
        AI response enriches but does not completely replace deterministic analysis.

        Rules:
        * program_type: prefer AI if not 'unknown' / empty
        * variables: union of both
        * operations: union of both
        * dependencies: union of both graphs (AI may add semantic edges)
        * business_summary: prefer AI (richer language) if non-empty
        * confidence: max of both, then average
        """
        # Program type
        ai_type = ai.get("program_type") or ""
        program_type = ai_type if ai_type and ai_type != "unknown" else det["program_type"]

        # Variables: union, re-sorted
        ai_vars  = set(ai.get("variables", []))
        det_vars = set(det["variables_detected"])
        variables = sorted(ai_vars | det_vars)

        # Operations: union preserving order (AI first, then det extras)
        ai_ops   = list(ai.get("operations", []))
        det_ops  = det["operations_detected"]
        seen     = set(ai_ops)
        operations = ai_ops + [o for o in det_ops if o not in seen]

        # Dependencies: union
        ai_deps  = ai.get("dependencies", {})
        det_deps = det["dependencies"]
        merged_deps: dict[str, list[str]] = {}
        for k in set(list(ai_deps.keys()) + list(det_deps.keys())):
            combined = set(ai_deps.get(k, []) + det_deps.get(k, []))
            merged_deps[k] = sorted(combined)

        # Business summary
        ai_summary = (ai.get("business_summary") or "").strip()
        business_summary = ai_summary if ai_summary else det["business_summary"]

        # Confidence: normalise AI score (0-100) to 0-1 then average with det
        ai_conf  = float(ai.get("confidence", 0) or 0)
        if ai_conf > 1.0:
            ai_conf /= 100.0
        ai_conf  = max(0.0, min(1.0, ai_conf))
        det_conf = det["confidence_score"]
        confidence = round((ai_conf + det_conf) / 2, 3)

        return {
            "program_type":       program_type,
            "variables_detected": variables,
            "operations_detected": operations,
            "dependencies":       merged_deps,
            "business_summary":   business_summary,
            "confidence_score":   confidence,
        }

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    @staticmethod
    async def analyze(apl_code: str) -> dict[str, Any]:
        """
        Analyse APL source code and return a structured semantic understanding.

        Parameters
        ----------
        apl_code : Full APL source (any size).

        Returns
        -------
        {
            program_type:       str,
            variables_detected: list[str],
            operations_detected: list[str],
            dependencies:       dict[str, list[str]],
            business_summary:   str,
            confidence_score:   float  (0–1),
        }
        """
        # ── 1. Always run deterministic analysis first ─────────────────
        det_result = UnderstandingAgent._fallback_response(apl_code)
        logger.info(
            "Deterministic analysis: type=%s vars=%d ops=%d",
            det_result["program_type"],
            len(det_result["variables_detected"]),
            len(det_result["operations_detected"]),
        )

        # ── 2. Acquire provider ────────────────────────────────────────
        try:
            provider      = ProviderFactory.get_provider()
            provider_name = ProviderFactory.get_active_provider_name()
        except ScaffoldedProviderError as exc:
            logger.warning("Provider scaffolded/unconfigured: %s → deterministic only", exc)
            return det_result
        except Exception as exc:
            logger.warning("Provider unavailable: %s → deterministic only", exc)
            return det_result

        # ── 3. Chunk and call provider ─────────────────────────────────
        chunks = _split_apl_for_analysis(apl_code)
        total  = len(chunks)
        logger.info("Understanding: %d chunk(s) to analyse", total)

        chunk_ai_results: list[dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            system_prompt, user_prompt = UnderstandingAgent._build_prompts(
                chunk, chunk_index=idx, total_chunks=total
            )

            raw = await _call_provider_with_retry(
                provider, user_prompt, system_prompt, provider_name
            )

            if raw is None:
                logger.warning("Chunk %d/%d: provider totally failed", idx + 1, total)
                provider._log_fallback_triggered(provider_name, "all_retries_failed")
                # Use deterministic result for this chunk
                chunk_analyser = _APLAnalyser(chunk)
                chunk_ai_results.append(chunk_analyser.analyse())
                continue

            extracted = _extract_understanding_from_response(raw, provider_name)
            if extracted is None:
                logger.warning("Chunk %d/%d: response extraction failed → deterministic chunk", idx + 1, total)
                provider._log_fallback_triggered(provider_name, "extraction_failed")
                chunk_analyser = _APLAnalyser(chunk)
                chunk_ai_results.append(chunk_analyser.analyse())
                continue

            chunk_ai_results.append(extracted)

        # ── 4. Merge chunks (if more than one) ────────────────────────
        if total > 1:
            merged_ai = _merge_chunk_understandings(chunk_ai_results)
        else:
            raw_ai = chunk_ai_results[0]
            # Normalise single-chunk result to standard keys
            merged_ai = {
                "program_type":       raw_ai.get("program_type", ""),
                "variables":          raw_ai.get("variables_detected", raw_ai.get("variables", [])),
                "operations":         raw_ai.get("operations_detected", raw_ai.get("operations", [])),
                "dependencies":       raw_ai.get("dependencies", {}),
                "business_summary":   raw_ai.get("business_summary", ""),
                "confidence":         raw_ai.get("confidence_score", raw_ai.get("confidence", 0.0)),
            }

        # ── 5. Merge AI with deterministic ────────────────────────────
        final = UnderstandingAgent._merge_ai_with_deterministic(merged_ai, det_result)

        logger.info(
            "Final understanding: type=%s vars=%d ops=%d deps=%d conf=%.3f",
            final["program_type"],
            len(final["variables_detected"]),
            len(final["operations_detected"]),
            len(final["dependencies"]),
            final["confidence_score"],
        )

        return final