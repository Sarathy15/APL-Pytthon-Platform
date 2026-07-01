import json
import os
import re
import subprocess
from typing import Any
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class APLRunner:
    @staticmethod
    def _to_apl_literal(value: Any) -> str:
        if value is None:
            return "⍬"
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (list, tuple)):
            if any(isinstance(item, (list, tuple)) for item in value):
                return ";".join(APLRunner._to_apl_literal(item) for item in value)
            return " ".join(APLRunner._to_apl_literal(item) for item in value)
        return str(value)

    @staticmethod
    def _prepare_code(code: str) -> str:
        lines = code.splitlines()
        active_lines = [line for line in lines if line.strip() and not line.strip().startswith("⍝")]
        if not active_lines:
            return code

        if any(line.strip().startswith("⎕←") for line in active_lines):
            return code

        last_index = max(i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith("⍝"))
        lines[last_index] = f"⎕←{lines[last_index]}"
        return "\n".join(lines)

    @staticmethod
    def execute(code: str, inputs: dict[str, Any] | None = None, timeout: int | None = None) -> dict[str, Any]:
        timeout = timeout or settings.TIMEOUT_SECONDS
        inputs = inputs or {}

        try:
            # Build APL script with inputs and code
            lines = ["⍝ Auto-generated APL runner script"]
            for name, value in inputs.items():
                lines.append(f"{name} ← {APLRunner._to_apl_literal(value)}")
            lines.append(APLRunner._prepare_code(code))

            apl_script = "\n".join(lines) + "\n"
            logger.info("Executing Dyalog APL code: %s", apl_script[:100] + ("..." if len(apl_script) > 100 else ""))

            # Use stdin to pass code to Dyalog with Popen (more reliable)
            command = [settings.DYALOG_EXECUTABLE]
            
            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    env={**os.environ},
                )
                
                stdout, stderr = process.communicate(input=apl_script, timeout=timeout)
                
            except subprocess.TimeoutExpired:
                process.kill()
                logger.error("Dyalog execution timed out after %s seconds", timeout)
                return {
                    "success": False,
                    "error": "Dyalog execution timed out",
                    "timeout": timeout,
                }
            
            # Parse output
            stdout = stdout.strip() if stdout else ""
            stderr = stderr.strip() if stderr else ""
            
            # Filter out license banner and noise from stderr
            if stderr:
                stderr_lines = [
                    line for line in stderr.split('\n')
                    if line.strip()
                    and not line.strip().startswith("|")
                    and not line.strip().startswith("+")
                    and not re.match(r"^[A-Z][a-z]{2} [A-Z][a-z]{2} \d{1,2} \d{2}:\d{2}:\d{2} \d{4}$", line.strip())
                    and not any(
                        keyword in line for keyword in [
                            "Dyalog APL",
                            "Serial number",
                            "UNREGISTERED",
                            "non-commercial",
                            "free software",
                            "licence",
                            "https://www.dyalog.com",
                            "Dyalog is free",
                            "Prompt",
                            "Execution",
                        ]
                    )
                ]
                stderr = "\n".join(stderr_lines).strip()
            
            if process.returncode != 0:
                logger.error("Dyalog execution failed with return code %d", process.returncode)
                return {
                    "success": False,
                    "error": "Dyalog execution failed",
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": process.returncode,
                }

            try:
                output = json.loads(stdout)
            except Exception:
                # Try to parse as a number if it's a simple result
                try:
                    output = float(stdout) if stdout and '.' in stdout else (int(stdout) if stdout else stdout)
                except (ValueError, TypeError):
                    output = stdout

            return {
                "success": True,
                "output": output,
                "stdout": stdout,
                "stderr": stderr if stderr else None,
            }
        except FileNotFoundError as exc:
            logger.error("Dyalog executable not found: %s", exc)
            return {
                "success": False,
                "error": "Dyalog runtime not found",
                "detail": str(exc),
            }
        except Exception as exc:
            logger.exception("Unhandled exception in APLRunner")
            return {
                "success": False,
                "error": "Unexpected APL execution error",
                "detail": str(exc),
            }
