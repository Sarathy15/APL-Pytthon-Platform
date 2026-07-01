from ..providers.provider_factory import ProviderFactory, ScaffoldedProviderError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ScoringAgent:
    @staticmethod
    async def evaluate(apl: str, python: str):
        prompt = f"Score the parity between this APL and Python:\nAPL: {apl}\nPython: {python}"
        system = "Evaluate parity, syntax, and complexity. Return a score 0-100."
        try:
            provider = ProviderFactory.get_provider()
        except ScaffoldedProviderError as exc:
            logger.warning("ScoringAgent provider scaffolded but not configured: %s", str(exc))
            return {"score": 0, "reason": "Provider not configured."}
        except Exception as exc:
            logger.error("ScoringAgent failed to initialize provider: %s", str(exc))
            return {"score": 0, "reason": "Provider unavailable."}

        result = await provider.generate(prompt, system)
        if isinstance(result, dict) and result.get("error"):
            logger.warning("ScoringAgent provider error: %s", result.get("detail"))
            return {"score": 0, "reason": "Provider error."}

        if isinstance(result, dict) and result.get("response"):
            return {"score_response": result.get("response")}

        return {"score_response": str(result)}
