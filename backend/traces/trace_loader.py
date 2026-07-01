import json
from pathlib import Path
from typing import Iterable, List

from .trace_schema import TraceRecord


def load_ndjson(file_path: Path) -> List[TraceRecord]:
    traces: List[TraceRecord] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            traces.append(TraceRecord(**payload))
    return traces


def load_traces(directory: Path) -> List[TraceRecord]:
    traces: List[TraceRecord] = []
    for path in sorted(directory.glob("*.ndjson")):
        traces.extend(load_ndjson(path))
    return traces
