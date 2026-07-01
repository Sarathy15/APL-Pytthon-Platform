from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from ...execution.apl_runner import APLRunner
from ...execution.python_runner import PythonRunner

router = APIRouter()

class APLValidationRequest(BaseModel):
    apl_code: str
    test_cases: list[Any] | None = None
    inputs: dict[str, Any] | None = None

class PythonValidationRequest(BaseModel):
    python_code: str
    test_cases: list[Any] | None = None
    inputs: dict[str, Any] | None = None

@router.post("/apl")
async def validate_apl(req: APLValidationRequest):
    """Execute APL code safely with optional test cases."""
    inputs = req.inputs or {}
    if req.test_cases is not None and "A" not in inputs:
        inputs["A"] = req.test_cases
    outputs = APLRunner.execute(req.apl_code, inputs=inputs if inputs else None)
    return outputs

@router.post("/python")
async def validate_python(req: PythonValidationRequest):
    """Execute Python migration code safely and capture structured output."""
    outputs = PythonRunner.execute(req.python_code, test_cases=req.test_cases, inputs=req.inputs)
    return outputs
