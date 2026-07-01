from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from ...reports.generator import ReportGenerator

router = APIRouter()

class ReportRequest(BaseModel):
    job_id: str
    apl_code: str
    python_code: str
    understanding: dict[str, Any]
    test_results: list[Any] | None = None
    comparison: dict[str, Any] | None = None
    scores: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    failures: list[Any] | None = None
    export_pdf: bool = False

@router.post("")
async def generate_report(req: ReportRequest):
    """Generate a JSON report and optionally save a PDF artifact locally."""
    context = {
        "apl_code": req.apl_code,
        "python_code": req.python_code,
        "understanding": req.understanding,
        "test_results": req.test_results or [],
        "comparison": req.comparison or {},
        "scores": req.scores or {},
        "metrics": req.metrics or {},
        "failures": req.failures or [],
        "status": "COMPLETED",
    }
    report = ReportGenerator.generate_migration_report(req.job_id, context)
    report_path = ReportGenerator.save_json_report(report, req.job_id)

    response = {
        "report": report,
        "report_path": report_path,
    }

    if req.export_pdf:
        pdf_path = ReportGenerator.save_pdf_report(report, req.job_id)
        response["pdf_path"] = pdf_path

    return response
