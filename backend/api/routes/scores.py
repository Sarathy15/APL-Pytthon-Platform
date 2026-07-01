from fastapi import APIRouter
from pydantic import BaseModel
from ...scoring.engine import ScoreEngine

router = APIRouter()

class ScoreRequest(BaseModel):
    python_code: str
    conversion_confidence: float
    semantic_score: float | None = 100.0

@router.post("")
async def calculate_scores(req: ScoreRequest):
    """Compute enterprise migration quality scores from code and comparison feedback."""
    scores = ScoreEngine.calculate(req.python_code, req.conversion_confidence, req.semantic_score or 100.0)
    return scores
