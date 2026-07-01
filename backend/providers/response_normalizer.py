"""Unified response normalization across all AI providers.

Handles:
- Markdown-wrapped JSON (```json ... ```)
- Malformed JSON with embedded structure
- Plain text responses
- Missing confidence scores
- Provider-specific response fields
- Consistent output schema
"""

import json
import re
from typing import Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ResponseNormalizer:
    """Centralized response parser for all AI providers."""

    # Standard response schema
    CONVERSION_SCHEMA = {"python_code", "explanation", "confidence_score"}
    UNDERSTANDING_SCHEMA = {"operator", "meaning", "category", "explanation", "confidence"}

    @staticmethod
    def normalize_conversion_response(
        raw_response: dict[str, Any] | str,
        provider_name: str = "unknown",
        fallback_code: str = "",
    ) -> dict[str, Any]:
        """
        Normalize provider response to conversion schema.

        Args:
            raw_response: Raw dict or string from provider
            provider_name: Name of provider (for logging)
            fallback_code: Default code if parsing fails

        Returns:
            {python_code, explanation, confidence_score}
        """
        # Extract text content from raw response
        text = ResponseNormalizer._extract_text(raw_response)

        # Try to parse as JSON
        parsed = ResponseNormalizer._parse_json_safely(text)

        if not parsed:
            extracted = ResponseNormalizer._extract_fields_from_text(text)
            code_block = (
                ResponseNormalizer._extract_code_block(text, language="python")
                or ResponseNormalizer._extract_code_block(text)
            )
            if code_block and not extracted.get("python_code"):
                extracted["python_code"] = code_block
            if extracted:
                logger.info(
                    "[%s] Extracted fields from plain text response",
                    provider_name,
                )
                python_code = (
                    extracted.get("python_code")
                    or extracted.get("code")
                    or extracted.get("converted_code")
                    or fallback_code
                    or ""
                )
                explanation = (
                    extracted.get("explanation")
                    or extracted.get("description")
                    or extracted.get("summary")
                    or ""
                )
                try:
                    confidence_score = float(
                        extracted.get("confidence_score")
                        or extracted.get("confidence")
                        or extracted.get("score")
                        or 50
                    )
                except (ValueError, TypeError):
                    confidence_score = 50.0

                confidence_score = max(0.0, min(100.0, confidence_score))
                return {
                    "python_code": python_code.strip() if python_code else "",
                    "explanation": explanation.strip() if explanation else "",
                    "confidence_score": confidence_score,
                }

            logger.warning(
                "[%s] Failed to parse response as JSON, treating as plain text",
                provider_name,
            )
            parsed = {"raw_text": text}

        # Normalize field names
        python_code = (
            parsed.get("python_code")
            or parsed.get("code")
            or parsed.get("converted_code")
            or fallback_code
            or ""
        )
        explanation = (
            parsed.get("explanation")
            or parsed.get("description")
            or parsed.get("summary")
            or ""
        )
        try:
            confidence_score = float(
                parsed.get("confidence_score")
                or parsed.get("confidence")
                or parsed.get("score")
                or 50
            )
        except (ValueError, TypeError):
            confidence_score = 50.0

        # Clamp confidence to 0-100
        confidence_score = max(0.0, min(100.0, confidence_score))

        result = {
            "python_code": python_code.strip() if python_code else "",
            "explanation": explanation.strip() if explanation else "",
            "confidence_score": confidence_score,
        }

        logger.debug(
            "[%s] Normalized response: code_len=%d, confidence=%.1f",
            provider_name,
            len(result["python_code"]),
            confidence_score,
        )

        return result

    @staticmethod
    def normalize_understanding_response(
        raw_response: dict[str, Any] | str,
        provider_name: str = "unknown",
    ) -> dict[str, Any]:
        """
        Normalize provider response to understanding schema.

        Args:
            raw_response: Raw dict or string from provider
            provider_name: Name of provider (for logging)

        Returns:
            {operator, meaning, category, explanation, confidence}
        """
        text = ResponseNormalizer._extract_text(raw_response)
        parsed = ResponseNormalizer._parse_json_safely(text)

        if not parsed:
            extracted = ResponseNormalizer._extract_fields_from_text(text)
            if extracted:
                logger.info(
                    "[%s] Extracted plain-text understanding fields",
                    provider_name,
                )
                parsed = extracted
            else:
                logger.warning(
                    "[%s] Failed to parse understanding response as JSON",
                    provider_name,
                )
                parsed = {}

        try:
            confidence = float(
                parsed.get("confidence")
                or parsed.get("confidence_score")
                or parsed.get("score")
                or 0
            )
        except (ValueError, TypeError):
            confidence = 0.0

        confidence = max(0.0, min(100.0, confidence))

        result = {
            "operator": parsed.get("operator") or parsed.get("symbol") or "unknown",
            "meaning": parsed.get("meaning") or parsed.get("definition") or "",
            "category": parsed.get("category") or parsed.get("type") or "",
            "explanation": parsed.get("explanation") or parsed.get("description") or "",
            "confidence": confidence,
        }

        logger.debug(
            "[%s] Normalized understanding: operator=%s, confidence=%.1f",
            provider_name,
            result["operator"],
            confidence,
        )

        return result

    @staticmethod
    def _extract_text(raw_response: dict[str, Any] | str) -> str:
        """
        Extract text content from provider response.

        Handles:
        - str: returned as-is
        - dict: checks 'response', 'text', 'content', 'message' keys
        - other: stringified
        """
        if isinstance(raw_response, str):
            return raw_response

        if isinstance(raw_response, dict):
            # Try common response field names
            for key in ["response", "text", "content", "message", "output"]:
                if key in raw_response and isinstance(raw_response[key], str):
                    return raw_response[key]

            # If dict but no text field, try to reconstruct or stringify
            logger.debug("Response dict has no standard text field, keys: %s", list(raw_response.keys()))
            return json.dumps(raw_response) if raw_response else ""

        return str(raw_response) if raw_response else ""

    @staticmethod
    def _parse_json_safely(text: str) -> dict[str, Any] | None:
        """
        Safely parse JSON from text, handling markdown wrapping.

        Handles:
        - Plain JSON: {..}
        - Markdown: ```json {...} ```
        - Markdown: ```{...}```
        - JSON with embedded text
        """
        if not text:
            return None

        text = text.strip()

        # Remove markdown code blocks
        text = ResponseNormalizer._strip_markdown_blocks(text)

        # Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from embedded text
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            logger.debug("Could not extract valid JSON from response text")
            return None

    @staticmethod
    def _strip_markdown_blocks(text: str) -> str:
        """Remove markdown code block markers (```json ... ```)."""
        # Pattern: ```[optional language] ... ```
        pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            extracted = match.group(1).strip()
            logger.debug("Extracted JSON from markdown block")
            return extracted

        # Alternative: inline markdown ``` ... ```
        if text.startswith("```") and text.endswith("```"):
            return text[3:-3].strip()

        return text

    @staticmethod
    def _extract_code_block(text: str, language: str | None = None) -> str | None:
        """Extract the first fenced code block from text."""
        if language:
            pattern = rf"```(?:{language})?\s*\n(.*?)\n?```"
        else:
            pattern = r"```(?:[A-Za-z0-9_+-]*)?\s*\n(.*?)\n?```"

        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_fields_from_text(text: str) -> dict[str, str]:
        """Extract simple key:value fields from plain-text responses."""
        field_names = [
            "python_code",
            "code",
            "converted_code",
            "explanation",
            "description",
            "summary",
            "confidence_score",
            "confidence",
            "score",
        ]
        fields: dict[str, str] = {}

        def lookup_pattern(name: str) -> re.Pattern[str]:
            return re.compile(
                rf"(?:^|\n)\s*(?:\"{name}\"|{name})\s*:\s*(?P<value>.*?)"
                rf"(?=\n\s*(?:\"[A-Za-z_]\w*\"|[A-Za-z_]\w*)\s*:\s*|\Z)",
                re.IGNORECASE | re.DOTALL,
            )

        def quoted_pattern(name: str, quote: str) -> re.Pattern[str]:
            return re.compile(
                rf"(?:^|\n)\s*(?:\"{name}\"|{name})\s*:\s*{quote}(?P<value>.*?){quote}",
                re.IGNORECASE | re.DOTALL,
            )

        for key in field_names:
            # Triple-quoted content first
            for quote in ['"""', "'''"]:
                pattern = quoted_pattern(key, quote)
                match = pattern.search(text)
                if match:
                    fields[key] = match.group("value").strip()
                    break
            if key in fields:
                continue
            # Double-quoted string content next
            pattern = re.compile(
                rf"(?:^|\n)\s*(?:\"{key}\"|{key})\s*:\s*\"(?P<value>.*?)\"",
                re.IGNORECASE | re.DOTALL,
            )
            match = pattern.search(text)
            if match:
                fields[key] = match.group("value").strip()
                continue
            # Fallback unquoted or raw block
            pattern = lookup_pattern(key)
            match = pattern.search(text)
            if match:
                fields[key] = match.group("value").strip()

        return fields

    @staticmethod
    def validate_conversion_output(response: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate conversion response has required fields.

        Returns:
            (is_valid, message)
        """
        if not response.get("python_code"):
            return False, "Missing python_code"
        if not response.get("explanation"):
            return False, "Missing explanation"
        if not isinstance(response.get("confidence_score"), (int, float)):
            return False, "Invalid confidence_score"
        return True, "Valid"

    @staticmethod
    def validate_understanding_output(response: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate understanding response has required fields.

        Returns:
            (is_valid, message)
        """
        if not response.get("operator"):
            return False, "Missing operator"
        if not isinstance(response.get("confidence"), (int, float)):
            return False, "Invalid confidence"
        return True, "Valid"
