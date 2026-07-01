from typing import Any
from ..providers.provider_factory import ProviderFactory, ScaffoldedProviderError
from ..providers.response_normalizer import ResponseNormalizer
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TestcaseAgent:
    """Generate test cases for APL to Python migration."""

    _FALLBACK_CASES = [
        [1, 2, 3],
        [0, 0, 0],
        [-1, 5, 8],
        [],
        [999999],
    ]

    @staticmethod
    async def generate(apl_code: str, python_code: str) -> dict[str, Any]:
        """
        Generate test cases for APL to Python migration.

        Args:
            apl_code: APL source code
            python_code: Generated Python code

        Returns:
            {test_cases: list, metadata: dict}
        """
        system_prompt = (
            "Generate test case arrays for APL to Python migration. "
            "Return JSON with key 'test_cases' containing a list of test input arrays."
        )

        user_prompt = (
            "Create diverse test cases for this migration. "
            "Return JSON with 'test_cases' key containing a list of valid Python literal arrays.\n\n"
            f"APL Code:\n{apl_code}\n\n"
            f"Python Code:\n{python_code}\n\n"
            'Example: {"test_cases": [[1,2,3], [0,0,0], [-1,5,8], [], [999999]]}'
        )

        # Try to get provider
        try:
            provider = ProviderFactory.get_provider()
            provider_name = ProviderFactory.get_active_provider_name()
        except ScaffoldedProviderError as exc:
            logger.warning("Provider not configured: %s, using fallback test cases", exc)
            return {
                "test_cases": TestcaseAgent._FALLBACK_CASES,
                "metadata": {"source": "fallback", "case_count": len(TestcaseAgent._FALLBACK_CASES)},
            }
        except Exception as exc:
            logger.warning("Failed to get provider: %s, using fallback test cases", exc)
            return {
                "test_cases": TestcaseAgent._FALLBACK_CASES,
                "metadata": {"source": "fallback", "case_count": len(TestcaseAgent._FALLBACK_CASES)},
            }

        # Call provider
        try:
            provider_response = await provider.generate(user_prompt, system_prompt)
        except Exception as exc:
            logger.error("Provider call failed: %s", exc)
            provider._log_fallback_triggered(provider_name, f"test_generation_error: {type(exc).__name__}")
            return {
                "test_cases": TestcaseAgent._FALLBACK_CASES,
                "metadata": {"source": "fallback", "case_count": len(TestcaseAgent._FALLBACK_CASES)},
            }

        # Check for error response
        if not provider_response or "error" in provider_response:
            error_msg = provider_response.get("error", "unknown") if provider_response else "no response"
            logger.warning("Provider error: %s", error_msg)
            provider._log_fallback_triggered(provider_name, f"test_generation_error: {error_msg}")
            return {
                "test_cases": TestcaseAgent._FALLBACK_CASES,
                "metadata": {"source": "fallback", "case_count": len(TestcaseAgent._FALLBACK_CASES)},
            }

        # Extract and parse response
        response_text = ResponseNormalizer._extract_text(provider_response)
        parsed = ResponseNormalizer._parse_json_safely(response_text)

        if not parsed or not isinstance(parsed, dict):
            logger.warning("Failed to parse test cases from provider response")
            provider._log_fallback_triggered(provider_name, "test_parse_failed")
            return {
                "test_cases": TestcaseAgent._FALLBACK_CASES,
                "metadata": {"source": "fallback", "case_count": len(TestcaseAgent._FALLBACK_CASES)},
            }

        test_cases = parsed.get("test_cases", [])
        if not isinstance(test_cases, list) or not test_cases:
            logger.warning("Provider returned invalid test_cases format")
            provider._log_fallback_triggered(provider_name, "invalid_test_cases")
            return {
                "test_cases": TestcaseAgent._FALLBACK_CASES,
                "metadata": {"source": "fallback", "case_count": len(TestcaseAgent._FALLBACK_CASES)},
            }

        return {
            "test_cases": test_cases,
            "metadata": {
                "source": "provider",
                "case_count": len(test_cases),
            },
        }
