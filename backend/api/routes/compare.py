from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from ...comparator.engine import ComparatorEngine

router = APIRouter()

class CompareRequest(BaseModel):
    apl_result: Any
    python_result: Any

@router.post("")
async def compare_results(req: CompareRequest):
    """Compare APL and Python outputs across shape, dtype, tolerance, and semantic checks."""
    comparison = ComparatorEngine.compare(req.apl_result, req.python_result)
    return {
        "match": comparison["match"],
        "score": comparison["score"],
        "issues": comparison["issues"],
        "details": comparison["details"],
    }
