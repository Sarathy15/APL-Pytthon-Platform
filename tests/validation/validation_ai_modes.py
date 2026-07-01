"""
Validation test for Public + Private AI Mode Implementation.

This script tests:
1. Private mode (Ollama)
2. Public mode (Claude, OpenAI, Gemini)

Test APL: +/A
Input: A=[1,2,3]
Expected Python: import numpy as np\nresult = np.sum(A)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.agents.understanding_agent import UnderstandingAgent
from backend.agents.conversion_agent import ConversionAgent
from backend.providers.provider_factory import ProviderFactory
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationResult:
    def __init__(self, mode: str, provider: str):
        self.mode = mode
        self.provider = provider
        self.tests_passed = []
        self.tests_failed = []
        self.errors = []

    def add_pass(self, test_name: str, details: str = ""):
        self.tests_passed.append({"name": test_name, "details": details})

    def add_fail(self, test_name: str, details: str = ""):
        self.tests_failed.append({"name": test_name, "details": details})

    def add_error(self, error_msg: str):
        self.errors.append(error_msg)

    def summary(self) -> str:
        total = len(self.tests_passed) + len(self.tests_failed)
        status = "✓ PASS" if len(self.tests_failed) == 0 else "✗ FAIL"
        return f"{status} | Mode: {self.mode} | Provider: {self.provider} | {len(self.tests_passed)}/{total} passed"

    def details(self) -> str:
        lines = [
            f"\n{'='*70}",
            f"Mode: {self.mode} | Provider: {self.provider}",
            f"{'='*70}",
        ]

        if self.tests_passed:
            lines.append("\n✓ PASSED TESTS:")
            for test in self.tests_passed:
                lines.append(f"  • {test['name']}")
                if test['details']:
                    lines.append(f"    {test['details']}")

        if self.tests_failed:
            lines.append("\n✗ FAILED TESTS:")
            for test in self.tests_failed:
                lines.append(f"  • {test['name']}")
                if test['details']:
                    lines.append(f"    {test['details']}")

        if self.errors:
            lines.append("\n⚠ ERRORS:")
            for error in self.errors:
                lines.append(f"  • {error}")

        return "\n".join(lines)


async def test_private_mode():
    """Test PRIVATE mode with Ollama."""
    os.environ["AI_MODE"] = "private"
    os.environ["AI_PROVIDER"] = "ollama"

    result = ValidationResult("PRIVATE", "ollama")

    try:
        # Reset factory cache
        ProviderFactory.reset_cache()

        # Test 1: Provider initialization
        logger.info("Testing provider initialization...")
        provider = ProviderFactory.get_provider()
        if provider.__class__.__name__ == "OllamaProvider":
            result.add_pass("Provider Initialization", "OllamaProvider created successfully")
        else:
            result.add_fail("Provider Initialization", f"Expected OllamaProvider, got {provider.__class__.__name__}")

        # Test 2: Understanding analysis
        logger.info("Testing understanding analysis...")
        apl_code = "+/A"
        understanding = await UnderstandingAgent.analyze(apl_code)

        if understanding.get("operator") == "+/":
            result.add_pass("Understanding Analysis", f"Correctly identified operator: {understanding.get('operator')}")
        else:
            result.add_fail("Understanding Analysis", f"Wrong operator: {understanding.get('operator')}")

        # Test 3: Conversion
        logger.info("Testing conversion...")
        conversion = await ConversionAgent.convert(apl_code, understanding)

        if conversion.get("python_code") and "np.sum" in conversion.get("python_code", ""):
            result.add_pass("Conversion", "Generated Python code with np.sum")
        else:
            result.add_fail("Conversion", f"Invalid Python code: {conversion.get('python_code')}")

    except Exception as exc:
        result.add_error(f"PRIVATE mode test failed: {str(exc)}")
        logger.error("PRIVATE mode test error: %s", exc, exc_info=True)

    return result


async def test_public_mode_claude():
    """Test PUBLIC mode with Claude."""
    if not os.environ.get("CLAUDE_API_KEY"):
        logger.warning("CLAUDE_API_KEY not set, skipping Claude tests")
        result = ValidationResult("PUBLIC", "claude")
        result.add_error("CLAUDE_API_KEY not configured")
        return result

    os.environ["AI_MODE"] = "public"
    os.environ["AI_PROVIDER"] = "claude"

    result = ValidationResult("PUBLIC", "claude")

    try:
        # Reset factory cache
        ProviderFactory.reset_cache()

        # Test 1: Provider initialization
        logger.info("Testing Claude provider initialization...")
        provider = ProviderFactory.get_provider()
        if provider.__class__.__name__ == "ClaudeProvider":
            result.add_pass("Provider Initialization", "ClaudeProvider created successfully")
        else:
            result.add_fail("Provider Initialization", f"Expected ClaudeProvider, got {provider.__class__.__name__}")

        # Test 2: Understanding analysis
        logger.info("Testing understanding analysis with Claude...")
        apl_code = "+/A"
        understanding = await UnderstandingAgent.analyze(apl_code)

        if understanding.get("operator") == "+/":
            result.add_pass("Understanding Analysis", f"Correctly identified operator: {understanding.get('operator')}")
        else:
            result.add_fail("Understanding Analysis", f"Wrong operator: {understanding.get('operator')}")

        # Test 3: Conversion
        logger.info("Testing conversion with Claude...")
        conversion = await ConversionAgent.convert(apl_code, understanding)

        if conversion.get("python_code") and "np.sum" in conversion.get("python_code", ""):
            result.add_pass("Conversion", "Generated Python code with np.sum")
        else:
            result.add_fail("Conversion", f"Invalid Python code: {conversion.get('python_code')}")

    except Exception as exc:
        result.add_error(f"Claude test failed: {str(exc)}")
        logger.error("Claude test error: %s", exc, exc_info=True)

    return result


async def test_public_mode_openai():
    """Test PUBLIC mode with OpenAI."""
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set, skipping OpenAI tests")
        result = ValidationResult("PUBLIC", "openai")
        result.add_error("OPENAI_API_KEY not configured")
        return result

    os.environ["AI_MODE"] = "public"
    os.environ["AI_PROVIDER"] = "openai"

    result = ValidationResult("PUBLIC", "openai")

    try:
        # Reset factory cache
        ProviderFactory.reset_cache()

        # Test 1: Provider initialization
        logger.info("Testing OpenAI provider initialization...")
        provider = ProviderFactory.get_provider()
        if provider.__class__.__name__ == "OpenAIProvider":
            result.add_pass("Provider Initialization", "OpenAIProvider created successfully")
        else:
            result.add_fail("Provider Initialization", f"Expected OpenAIProvider, got {provider.__class__.__name__}")

        # Test 2: Understanding analysis
        logger.info("Testing understanding analysis with OpenAI...")
        apl_code = "+/A"
        understanding = await UnderstandingAgent.analyze(apl_code)

        if understanding.get("operator") == "+/":
            result.add_pass("Understanding Analysis", f"Correctly identified operator: {understanding.get('operator')}")
        else:
            result.add_fail("Understanding Analysis", f"Wrong operator: {understanding.get('operator')}")

        # Test 3: Conversion
        logger.info("Testing conversion with OpenAI...")
        conversion = await ConversionAgent.convert(apl_code, understanding)

        if conversion.get("python_code") and "np.sum" in conversion.get("python_code", ""):
            result.add_pass("Conversion", "Generated Python code with np.sum")
        else:
            result.add_fail("Conversion", f"Invalid Python code: {conversion.get('python_code')}")

    except Exception as exc:
        result.add_error(f"OpenAI test failed: {str(exc)}")
        logger.error("OpenAI test error: %s", exc, exc_info=True)

    return result


async def test_public_mode_gemini():
    """Test PUBLIC mode with Gemini."""
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY not set, skipping Gemini tests")
        result = ValidationResult("PUBLIC", "gemini")
        result.add_error("GEMINI_API_KEY not configured")
        return result

    os.environ["AI_MODE"] = "public"
    os.environ["AI_PROVIDER"] = "gemini"

    result = ValidationResult("PUBLIC", "gemini")

    try:
        # Reset factory cache
        ProviderFactory.reset_cache()

        # Test 1: Provider initialization
        logger.info("Testing Gemini provider initialization...")
        provider = ProviderFactory.get_provider()
        if provider.__class__.__name__ == "GeminiProvider":
            result.add_pass("Provider Initialization", "GeminiProvider created successfully")
        else:
            result.add_fail("Provider Initialization", f"Expected GeminiProvider, got {provider.__class__.__name__}")

        # Test 2: Understanding analysis
        logger.info("Testing understanding analysis with Gemini...")
        apl_code = "+/A"
        understanding = await UnderstandingAgent.analyze(apl_code)

        if understanding.get("operator") == "+/":
            result.add_pass("Understanding Analysis", f"Correctly identified operator: {understanding.get('operator')}")
        else:
            result.add_fail("Understanding Analysis", f"Wrong operator: {understanding.get('operator')}")

        # Test 3: Conversion
        logger.info("Testing conversion with Gemini...")
        conversion = await ConversionAgent.convert(apl_code, understanding)

        if conversion.get("python_code") and "np.sum" in conversion.get("python_code", ""):
            result.add_pass("Conversion", "Generated Python code with np.sum")
        else:
            result.add_fail("Conversion", f"Invalid Python code: {conversion.get('python_code')}")

    except Exception as exc:
        result.add_error(f"Gemini test failed: {str(exc)}")
        logger.error("Gemini test error: %s", exc, exc_info=True)

    return result


async def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("APL-to-Python Migration Platform - AI Mode Validation")
    print("="*70)

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    results = []

    # Test Private Mode
    print("\n[1/5] Testing PRIVATE mode (Ollama)...")
    results.append(await test_private_mode())

    # Test Public Modes
    print("\n[2/5] Testing PUBLIC mode (Claude)...")
    results.append(await test_public_mode_claude())

    print("\n[3/5] Testing PUBLIC mode (OpenAI)...")
    results.append(await test_public_mode_openai())

    print("\n[4/5] Testing PUBLIC mode (Gemini)...")
    results.append(await test_public_mode_gemini())

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    for result in results:
        print(f"  {result.summary()}")

    # Detailed results
    for result in results:
        print(result.details())

    # Final status
    all_passed = all(len(r.tests_failed) == 0 and len(r.errors) == 0 for r in results)
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - System is ready for Phase 5")
    else:
        print("✗ SOME TESTS FAILED - Review errors above")
    print("="*70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
