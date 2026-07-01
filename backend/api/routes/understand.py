from fastapi import APIRouter
from pydantic import BaseModel
from ...agents.understanding_agent import UnderstandingAgent

router = APIRouter()

class UnderstandRequest(BaseModel):
    apl_code: str

@router.post("")
async def understand_code(req: UnderstandRequest):
    """Analyze raw APL code and return structured understanding output."""
    return await UnderstandingAgent.analyze(req.apl_code)
