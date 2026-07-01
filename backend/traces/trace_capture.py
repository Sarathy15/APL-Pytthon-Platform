import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from ..execution.apl_runner import APLRunner
from .trace_schema import ExecEnv, TraceRecord
from .trace_serializer import serialize_to_ndjson, ensure_trace_dir


def _infer_dtype(value: Any) -> Optional[str]:
    try:
        array = np.asarray(value)
        return str(array.dtype)
    except Exception:
        return type(value).__name__


def _infer_shape(value: Any) -> Optional[list[int]]:
    try:
        array = np.asarray(value)
        return list(array.shape)
    except Exception:
        return None


class TraceCapture:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = ensure_trace_dir(output_dir) if output_dir else ensure_trace_dir()

    def capture(
        self,
        function_name: str,
        apl_code: str,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> TraceRecord:
        inputs = inputs or {}
        metadata = metadata or {}

        result = APLRunner.execute(apl_code, inputs=inputs, timeout=timeout)

        trace = TraceRecord(
            function_name=function_name,
            timestamp=datetime.utcnow(),
            inputs=inputs,
            output=result.get("output"),
            dtype=_infer_dtype(result.get("output")),
            shape=_infer_shape(result.get("output")),
            seed=seed,
            exec_env=ExecEnv(
                os=platform.system().lower(),
                apl_runtime="dyalog",
                python_version=platform.python_version(),
            ),
            metadata=metadata,
            success=result.get("success", False),
            error=result.get("stderr") or result.get("error"),
            source=apl_code,
        )

        serialize_to_ndjson(trace, self.output_dir / f"trace_{function_name}_{trace.timestamp.strftime('%Y%m%d%H%M%S%f')}.ndjson")
        return trace
