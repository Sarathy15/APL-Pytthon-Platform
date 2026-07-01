from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from ...agents.conversion_agent import ConversionAgent

router = APIRouter()

class ConvertRequest(BaseModel):
    apl_code: str
    understanding: dict[str, Any]

@router.post("")
async def convert_code(req: ConvertRequest):
    """Convert APL code to Python using understanding context from the analysis agent."""
    return await ConversionAgent.convert(req.apl_code, req.understanding)
