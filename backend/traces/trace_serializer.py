import json
from pathlib import Path
from typing import Iterable, List, Optional

from .trace_schema import TraceRecord

TRACE_OUTPUT_DIR = Path("outputs") / "traces"
TRACE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_trace_dir(path: Optional[Path] = None) -> Path:
    target = path or TRACE_OUTPUT_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def serialize_to_ndjson(trace: TraceRecord, file_path: Optional[Path] = None) -> Path:
    target = file_path or ensure_trace_dir() / f"trace_{trace.timestamp.strftime('%Y%m%d%H%M%S%f')}.ndjson"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(trace.json(exclude_none=True) + "\n")
    return target


def serialize_to_parquet(trace: TraceRecord, file_path: Optional[Path] = None) -> Path:
    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Parquet export requires pandas") from exc

    target = file_path or ensure_trace_dir() / f"trace_{trace.timestamp.strftime('%Y%m%d%H%M%S%f')}.parquet"
    df = pd.DataFrame([trace.dict(exclude_none=True)])
    df.to_parquet(target)
    return target


def serialize_batch_to_ndjson(traces: Iterable[TraceRecord], file_path: Optional[Path] = None) -> Path:
    target = file_path or ensure_trace_dir() / f"trace_batch_{traces[0].timestamp.strftime('%Y%m%d%H%M%S%f')}.ndjson"
    with target.open("a", encoding="utf-8") as handle:
        for trace in traces:
            handle.write(trace.json(exclude_none=True) + "\n")
    return target
