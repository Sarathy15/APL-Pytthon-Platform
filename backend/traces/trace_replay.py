from pathlib import Path
from typing import Any, Dict, List, Optional
import math

from ..config import settings
from ..execution.apl_runner import APLRunner
from ..execution.python_runner import PythonRunner
from ..comparator.engine import ComparatorEngine
from ..utils.logger import get_logger
from .trace_loader import load_traces
from .trace_schema import TraceRecord

logger = get_logger(__name__)


class TraceReplay:
    def __init__(self, trace_dir: Optional[Path] = None, retry_attempts: Optional[int] = None):
        self.trace_dir = trace_dir or Path("outputs") / "traces"
        self.retry_attempts = retry_attempts or settings.RETRY_ATTEMPTS

    @staticmethod
    def _trace_id(trace: TraceRecord) -> str:
        return trace.metadata.get("trace_id") or f"{trace.function_name}_{trace.timestamp.isoformat()}"

    @staticmethod
    def _to_python_literal(value: Any) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            if math.isnan(value):
                return "float('nan')"
            if math.isinf(value):
                return "float('inf')" if value > 0 else "float('-inf')"
            return repr(value)
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, (list, tuple)):
            inner = ", ".join(TraceReplay._to_python_literal(item) for item in value)
            bracket = "[" if isinstance(value, list) else "("
            closing = "]" if isinstance(value, list) else ")"
            return f"{bracket}{inner}{closing}"
        if isinstance(value, dict):
            items = ", ".join(
                f"{repr(key)}: {TraceReplay._to_python_literal(val)}"
                for key, val in value.items()
            )
            return f"{{{items}}}"
        if hasattr(value, "tolist"):
            return TraceReplay._to_python_literal(value.tolist())
        return repr(value)

    @staticmethod
    def _build_python_source(python_code: str, inputs: Optional[Dict[str, Any]] = None) -> str:
        if not inputs:
            return python_code

        bindings = []
        for name, value in inputs.items():
            bindings.append(f"{name} = {TraceReplay._to_python_literal(value)}")
        return "\n".join(bindings) + "\n" + python_code

    def _retry_execute(self, runner, *args, **kwargs) -> Dict[str, Any]:
        last_result: Dict[str, Any] = {"success": False, "error": "no result"}
        for attempt in range(1, max(1, self.retry_attempts) + 1):
            result = runner(*args, **kwargs)
            if result.get("success"):
                return result
            last_result = result
            logger.warning(
                "Execution attempt %s/%s failed for %s: %s",
                attempt,
                self.retry_attempts,
                runner.__name__,
                result.get("error") or result.get("stderr"),
            )
        return last_result

    def replay_trace(
        self,
        trace: TraceRecord,
        python_code: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        timeout = timeout or settings.TIMEOUT_SECONDS
        trace_id = self._trace_id(trace)

        logger.info("Replaying trace %s", trace_id)

        apl_result = self._retry_execute(
            APLRunner.execute,
            trace.source or "",
            trace.inputs or {},
            timeout=timeout,
        )

        python_source = self._build_python_source(python_code, trace.inputs)
        python_result = self._retry_execute(
            PythonRunner.execute,
            python_source,
            timeout=timeout,
        )

        comparison = ComparatorEngine.compare(
            apl_result.get("output"),
            python_result.get("output"),
            rtol=1e-7,
            atol=1e-9,
        )

        apl_success = apl_result.get("success", False)
        python_success = python_result.get("success", False)
        errors = {
            "apl_error": apl_result.get("error") or apl_result.get("stderr"),
            "python_error": python_result.get("error") or python_result.get("stderr"),
        }

        failure_reason = None
        if not apl_success or not python_success:
            lower = "".join(str(v).lower() for v in errors.values() if v)
            if "timeout" in lower or "timed out" in lower:
                failure_reason = "execution_timeout"
            else:
                failure_reason = "execution_failure"

        report: Dict[str, Any] = {
            "trace_id": trace_id,
            "function_name": trace.function_name,
            "metadata": trace.metadata,
            "apl_output": apl_result.get("output"),
            "python_output": python_result.get("output"),
            "apl_success": apl_success,
            "python_success": python_success,
            "match": comparison.get("match", False) and apl_success and python_success,
            "verdict": "pass" if comparison.get("match", False) and apl_success and python_success else "fail",
            "reason": failure_reason,
            "warnings": comparison.get("warnings", []),
            "mismatches": comparison.get("mismatches", []),
            "confidence": 0 if failure_reason else comparison.get("score", 0),
            "error_magnitude": comparison.get("error_magnitude", 0.0),
            "details": {
                **comparison.get("details", {}),
                "apl_success": apl_success,
                "python_success": python_success,
            },
            "errors": errors,
        }

        if failure_reason:
            if failure_reason not in report["mismatches"]:
                report["mismatches"].append(failure_reason)

        logger.info(
            "Replay result for %s: match=%s confidence=%s",
            trace_id,
            report["match"],
            report["confidence"],
        )

        return report

    def replay_all(
        self,
        python_code: str,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        traces = load_traces(self.trace_dir)
        reports: List[Dict[str, Any]] = []
        for trace in traces:
            try:
                reports.append(self.replay_trace(trace, python_code=python_code, timeout=timeout))
            except Exception as exc:
                logger.exception("Failed replaying trace %s", trace.timestamp.isoformat())
                reports.append(
                    {
                        "trace_id": self._trace_id(trace),
                        "function_name": trace.function_name,
                        "match": False,
                        "confidence": 0,
                        "errors": {"trace_replay_error": str(exc)},
                    }
                )
        return reports
