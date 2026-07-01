from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecEnv(BaseModel):
    os: str
    apl_runtime: str
    python_version: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class TraceRecord(BaseModel):
    function_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    inputs: Any
    output: Any
    dtype: Optional[str] = None
    shape: Optional[List[int]] = None
    seed: Optional[int] = None
    exec_env: ExecEnv
    metadata: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    source: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda value: value.isoformat(),
        }
