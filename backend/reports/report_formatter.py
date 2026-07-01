from typing import Any

class ReportFormatter:
    @staticmethod
    def format_text(report: dict[str, Any]) -> str:
        lines = [
            f"Migration Report: {report.get('metadata', {}).get('job_id', 'unknown')}",
            f"Timestamp: {report.get('metadata', {}).get('timestamp', '')}",
            f"Status: {report.get('metadata', {}).get('status', '')}",
            "\n--- APL Source ---",
            report.get('artifacts', {}).get('apl_source', ''),
            "\n--- Generated Python ---",
            report.get('artifacts', {}).get('python_target', ''),
            "\n--- Understanding ---",
            report.get('artifacts', {}).get('semantic_proof', ''),
            "\n--- Metrics ---",
        ]

        metrics = report.get('metrics', {})
        for name, value in metrics.items():
            lines.append(f"{name}: {value}")

        lines.append("\n--- Comparison ---")
        comparison = report.get('comparison', {})
        for name, value in comparison.items():
            lines.append(f"{name}: {value}")

        lines.append("\n--- Scores ---")
        scores = report.get('scores', {})
        for name, value in scores.items():
            lines.append(f"{name}: {value}")

        if failures := report.get('failures'):
            lines.append("\n--- Failures ---")
            lines.append(str(failures))

        return "\n".join(lines)
