from fastapi import APIRouter
from pydantic import BaseModel
from ...agents.testcase_agent import TestcaseAgent

router = APIRouter()

class TestsRequest(BaseModel):
    apl_code: str
    python_code: str

@router.post("")
async def generate_tests(req: TestsRequest):
    """Generate migration test vectors for APL and Python behavior validation."""
    return await TestcaseAgent.generate(req.apl_code, req.python_code)
