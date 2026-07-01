import datetime
from pathlib import Path
from .json_export import JSONExport
from .pdf_export import PDFExport
from .report_formatter import ReportFormatter
from ..config import settings
from ..utils.helpers import ensure_output_directories

class ReportGenerator:
    @staticmethod
    def generate_migration_report(job_id: str, results: dict) -> dict:
        report = {
            "metadata": {
                "job_id": job_id,
                "timestamp": str(datetime.datetime.now()),
                "status": results.get("status", "COMPLETED"),
                "engine_version": "v2.1.0-enterprise",
            },
            "artifacts": {
                "apl_source": results.get("apl_code", results.get("apl")),
                "python_target": results.get("python_code", results.get("python")),
                "semantic_proof": results.get("understanding", results.get("explanation")),
            },
            "comparison": results.get("comparison", {}),
            "scores": results.get("scores", {}),
            "metrics": results.get("metrics", {}),
            "failures": results.get("failures", []),
        }
        return report

    @staticmethod
    def save_json_report(report: dict, filename: str) -> str:
        ensure_output_directories(settings.REPORTS_DIR)
        return JSONExport.save(report, filename)

    @staticmethod
    def save_pdf_report(report: dict, filename: str) -> str:
        ensure_output_directories(settings.REPORTS_DIR)
        pdf_bytes = PDFExport.create_pdf_bytes(report)
        path = settings.REPORTS_DIR / f"{filename}.pdf"
        path.write_bytes(pdf_bytes)
        return str(path)

    @staticmethod
    def format_report_text(report: dict) -> str:
        return ReportFormatter.format_text(report)
