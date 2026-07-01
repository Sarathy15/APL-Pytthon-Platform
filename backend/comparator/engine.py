import itertools
import re
from typing import Any

import numpy as np
from .axis_checker import AxisChecker
from .dtype_checker import DtypeChecker
from .index_checker import IndexChecker
from .nan_checker import NanChecker
from .semantic_checker import SemanticChecker
from .shape_checker import ShapeChecker
from .tolerance_checker import ToleranceChecker


class ComparatorEngine:
    @staticmethod
    def _parse_apl_token(token: str) -> Any:
        token = token.strip()
        if token == "":
            return ""
        if token == "⍬":
            return []
        normalized = token.replace("¯", "-").replace("∞", "inf")
        upper = normalized.upper()
        if upper in {"0N", "N", "NAN", "NA"}:
            return float("nan")
        if upper in {"INF", "+INF", "INFINITY", "+INFINITY"}:
            return float("inf")
        if upper in {"-INF", "-INFINITY", "-∞", "¯∞"}:
            return float("-inf")
        if re.fullmatch(r"-?\d+", normalized):
            return int(normalized)
        try:
            return float(normalized)
        except ValueError:
            return token

    @staticmethod
    def _parse_apl_string(value: str) -> Any:
        text = value.strip()
        if text == "":
            return ""
        if text == "⍬":
            return []
        if ";" in text:
            return [ComparatorEngine._parse_apl_string(segment) for segment in text.split(";")]
        parts = text.split()
        if len(parts) > 1:
            return [ComparatorEngine._parse_apl_token(part) for part in parts]
        return ComparatorEngine._parse_apl_token(text)

    @staticmethod
    def _normalize(value: Any) -> np.ndarray:
        if isinstance(value, str):
            parsed = ComparatorEngine._parse_apl_string(value)
            if parsed != value:
                value = parsed
        if hasattr(value, "tolist") and not isinstance(value, str):
            try:
                value = value.tolist()
            except Exception:
                pass
        try:
            return np.asarray(value)
        except Exception:
            return np.asarray(str(value))

    @staticmethod
    def _broadcast_mismatch(a: np.ndarray, b: np.ndarray) -> bool:
        if a.shape == b.shape:
            return False
        try:
            np.broadcast_shapes(a.shape, b.shape)
            return True
        except ValueError:
            return False

    @staticmethod
    def _error_magnitude(a: np.ndarray, b: np.ndarray) -> float:
        try:
            if a.shape != b.shape:
                return 0.0
            if not np.issubdtype(a.dtype, np.number) or not np.issubdtype(b.dtype, np.number):
                return 0.0
            diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
            return float(np.nanmax(diff)) if diff.size else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def compare(
        apl_value: Any,
        python_value: Any,
        rtol: float = 1e-7,
        atol: float = 1e-9,
        apl_origin: int = 1,
        allow_permutation: bool = False,
    ) -> dict:
        a = ComparatorEngine._normalize(apl_value)
        p = ComparatorEngine._normalize(python_value)

        shape_ok = ShapeChecker.verify(a, p)
        dtype_ok = DtypeChecker.verify(a, p)
        nan_ok = NanChecker.verify(a, p)
        tolerance_ok = ToleranceChecker.verify(a, p, rtol=rtol, atol=atol)
        semantic_ok = SemanticChecker.verify(a, p, tol=rtol, allow_permutation=allow_permutation)
        index_ok = IndexChecker.verify(a, p, apl_origin=apl_origin)
        axis_ok = AxisChecker.verify(a, p)
        broadcast_issue = ComparatorEngine._broadcast_mismatch(a, p)

        warnings = []
        mismatches = []

        if not shape_ok:
            mismatches.append("shape_mismatch")
        if not axis_ok:
            mismatches.append("axis_mismatch")
        if broadcast_issue:
            mismatches.append("broadcasting_mismatch")
        if not nan_ok:
            mismatches.append("nan_mismatch")
        if not tolerance_ok:
            mismatches.append("tolerance_violation")
        if not semantic_ok:
            mismatches.append("semantic_mismatch")
        if not index_ok:
            mismatches.append("index_origin_mismatch")

        if not dtype_ok:
            warnings.append("dtype_coercion")

        verdict = "pass" if len(mismatches) == 0 else "fail"
        score = max(0, 100 - len(mismatches) * 15)

        return {
            "verdict": verdict,
            "match": verdict == "pass",
            "shape_match": shape_ok,
            "dtype_match": dtype_ok,
            "semantic_match": semantic_ok,
            "error_magnitude": ComparatorEngine._error_magnitude(a, p),
            "warnings": warnings,
            "mismatches": mismatches,
            "score": score,
            "details": {
                "shape_ok": shape_ok,
                "dtype_ok": dtype_ok,
                "nan_ok": nan_ok,
                "tolerance_ok": tolerance_ok,
                "semantic_ok": semantic_ok,
                "index_ok": index_ok,
                "axis_ok": axis_ok,
                "broadcast_ok": not broadcast_issue,
                "permutation_allowed": allow_permutation,
            },
            "apl_value": apl_value,
            "python_value": python_value,
        }
