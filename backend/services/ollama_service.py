import asyncio
import httpx
from ..config import settings

class OllamaService:
    @staticmethod
    async def generate(prompt: str, system: str = ""):
        url = f"{settings.OLLAMA_URL}/api/generate"
        payload = {
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }

        timeout = httpx.Timeout(settings.TIMEOUT_SECONDS, connect=settings.TIMEOUT_SECONDS)
        last_error = None

        for attempt in range(1, settings.RETRY_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if 500 <= exc.response.status_code < 600 and attempt < settings.RETRY_ATTEMPTS:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {"error": f"Ollama request failed: {exc.response.status_code}", "detail": exc.response.text}
            except Exception as exc:
                last_error = exc
                if attempt < settings.RETRY_ATTEMPTS:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {"error": "Ollama service unreachable", "detail": str(exc)}

        return {"error": "Ollama retry exhausted", "detail": str(last_error)}
