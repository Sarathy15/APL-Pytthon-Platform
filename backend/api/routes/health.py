from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    version: str

@router.get("", response_model=HealthResponse)
async def get_health():
    return {"status": "healthy", "version": "1.0.0"}
