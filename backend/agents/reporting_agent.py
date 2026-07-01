from ..providers.provider_factory import ProviderFactory, ScaffoldedProviderError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ReportingAgent:
    @staticmethod
    async def generate_summary(metrics: dict):
        # AI-generated executive summary for the migration report
        prompt = f"Summarize these migration metrics for a CTO:\n{metrics}"
        system_prompt = "You are an enterprise migration reporting assistant. Return a concise executive summary."
        try:
            provider = ProviderFactory.get_provider()
        except ScaffoldedProviderError as exc:
            logger.warning("ReportingAgent provider scaffolded but not configured: %s", str(exc))
            return {"summary": "Reporting provider not configured."}
        except Exception as exc:
            logger.error("ReportingAgent failed to initialize provider: %s", str(exc))
            return {"summary": "Reporting provider unavailable."}

        result = await provider.generate(prompt, system_prompt)
        if isinstance(result, dict) and result.get("error"):
            logger.warning("ReportingAgent provider error: %s", result.get("detail"))
            return {"summary": "Reporting provider returned an error."}

        if isinstance(result, dict) and result.get("response"):
            return {"summary": result.get("response")}

        return {"summary": str(result)}
