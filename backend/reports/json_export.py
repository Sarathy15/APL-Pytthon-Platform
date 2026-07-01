import json
from pathlib import Path
from ..config import settings
from ..utils.helpers import ensure_output_directories

class JSONExport:
    @staticmethod
    def save(report: dict, filename: str) -> str:
        ensure_output_directories(settings.REPORTS_DIR)
        path = settings.REPORTS_DIR / f"{filename}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)
