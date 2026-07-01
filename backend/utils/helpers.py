import os
import json
from pathlib import Path

class PromptVersions:
    @staticmethod
    def get_latest(agent_type: str):
        # Implementation of enterprise prompt versioning
        return "v1.2.0"

def load_prompt(name: str):
    with open(f"backend/agents/prompts/{name}.txt", 'r', encoding='utf-8') as f:
        return f.read()

def parse_json_response(response: str | dict) -> dict:
    if isinstance(response, dict):
        if "response" in response and isinstance(response["response"], str):
            parsed = parse_json_response(response["response"])
            if isinstance(parsed, dict):
                merged = {k: v for k, v in response.items() if k != "response"}
                merged.update(parsed)
                return merged
        if "raw_response" in response and isinstance(response["raw_response"], str):
            parsed = parse_json_response(response["raw_response"])
            if isinstance(parsed, dict):
                merged = {k: v for k, v in response.items() if k != "raw_response"}
                merged.update(parsed)
                return merged
        return response
    if not isinstance(response, str):
        return {"raw_response": str(response)}
    
    # Strip markdown code blocks (```json ... ```)
    text = response.strip()
    if text.startswith("```"):
        # Extract content between triple backticks
        lines = text.split("\n")
        if len(lines) > 2 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
        elif lines[0].startswith("```"):
            text = "\n".join(lines[1:]).strip()
            if text.endswith("```"):
                text = text[:-3].strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return json.loads(text[start:end])
        except Exception:
            return {"raw_response": response}

def ensure_output_directories(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

