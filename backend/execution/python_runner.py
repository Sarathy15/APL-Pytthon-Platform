import ast
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PythonRunner:
    @staticmethod
    def _is_safe_code(code: str) -> tuple[bool, str | None]:
        dangerous_modules = {
            "os",
            "sys",
            "subprocess",
            "pathlib",
            "shutil",
            "socket",
            "signal",
            "multiprocessing",
            "ctypes",
            "threading",
            "asyncio",
            "importlib",
        }
        dangerous_names = {
            "exec",
            "eval",
            "compile",
            "open",
            "__import__",
            "input",
        }
        dangerous_attrs = {
            "system",
            "popen",
            "Popen",
            "spawn",
            "remove",
            "unlink",
            "rmdir",
            "mkdir",
            "startfile",
            "kill",
            "send",
            "connect",
            "bind",
        }

        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as exc:
            return False, f"Python syntax error: {exc}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in dangerous_modules:
                        return False, f"Unsafe import detected: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in dangerous_modules:
                    return False, f"Unsafe import-from detected: {node.module}"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_names:
                        return False, f"Unsafe function call detected: {node.func.id}"
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in dangerous_attrs:
                        return False, f"Unsafe attribute call detected: {attr_name}"
                    if isinstance(node.func.value, ast.Name) and node.func.value.id in dangerous_modules:
                        return False, f"Unsafe module call detected: {node.func.value.id}.{attr_name}"
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id in dangerous_modules:
                    return False, f"Unsafe module attribute access detected: {node.value.id}.{node.attr}"

        return True, None

    @staticmethod
    def _to_python_literal(value: Any) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return repr(value)
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, (list, tuple)):
            inner = ", ".join(PythonRunner._to_python_literal(item) for item in value)
            return f"[{inner}]"
        if isinstance(value, dict):
            items = ", ".join(
                f"{repr(str(key))}: {PythonRunner._to_python_literal(val)}"
                for key, val in value.items()
            )
            return f"{{{items}}}"
        if hasattr(value, "tolist"):
            return PythonRunner._to_python_literal(value.tolist())
        return repr(value)

    @staticmethod
    def _build_script(
        code: str,
        input_file: Path | None = None,
        use_test_cases: bool = False,
        inputs: dict[str, Any] | None = None,
    ) -> str:
        lines = [
            "import json",
            "import traceback",
            "from pathlib import Path",
            "result = None",
            "",
            "def _to_json_safe(value):",
            "    try:",
            "        import numpy as np",
            "    except Exception:",
            "        np = None",
            "    if value is None or isinstance(value, (str, int, float, bool)):",
            "        return value",
            "    if np is not None and isinstance(value, (np.integer, np.floating, np.bool_)):",
            "        return value.item()",
            "    if np is not None and isinstance(value, np.ndarray):",
            "        return value.tolist()",
            "    if isinstance(value, (list, tuple)):",
            "        return [_to_json_safe(item) for item in value]",
            "    if isinstance(value, dict):",
            "        return {str(key): _to_json_safe(val) for key, val in value.items()}",
            "    return str(value)",
            "",
        ]

        if use_test_cases and input_file:
            lines.extend([
                "outputs = []",
                f"test_cases = json.loads(Path(\"{input_file.name}\").read_text(encoding=\"utf-8\"))",
            ])
            if inputs:
                for name, value in inputs.items():
                    lines.append(f"{name} = {PythonRunner._to_python_literal(value)}")
            lines.extend([
                "for item in test_cases:",
                "    if isinstance(item, dict):",
                "        globals().update(item)",
                "    else:",
                "        A = item",
                "    try:",
            ])
            lines.extend([f"        {line}" for line in code.splitlines()])
            lines.extend([
                "        outputs.append({\"success\": True, \"output\": _to_json_safe(result)})",
                "    except Exception as exc:",
                "        outputs.append({\"success\": False, \"error\": str(exc), \"traceback\": traceback.format_exc()})",
            ])
            lines.append("print(json.dumps(outputs))")
        else:
            if inputs:
                for name, value in inputs.items():
                    lines.append(f"{name} = {PythonRunner._to_python_literal(value)}")
            else:
                lines.append("A = None")
            lines.extend(code.splitlines())
            lines.append("outputs = {\"success\": True, \"output\": _to_json_safe(result)}")
            lines.append("print(json.dumps(outputs))")

        return "\n".join(lines)

    @staticmethod
    def execute(
        code: str,
        test_cases: list[Any] | None = None,
        inputs: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        timeout = timeout or settings.TIMEOUT_SECONDS
        temp_dir = Path(tempfile.mkdtemp(prefix="python_runner_"))
        script_path = temp_dir / "migration_execution.py"
        input_file_path = temp_dir / "input_data.json"

        try:
            if test_cases is not None:
                input_file_path.write_text(json.dumps(test_cases, ensure_ascii=False), encoding="utf-8")
                script_content = PythonRunner._build_script(
                    code,
                    input_file=input_file_path,
                    use_test_cases=True,
                    inputs=inputs,
                )
            else:
                script_content = PythonRunner._build_script(code, inputs=inputs)

            safe, reason = PythonRunner._is_safe_code(code)
            if not safe:
                logger.error("Python execution blocked for safety: %s", reason)
                return {
                    "success": False,
                    "error": "unsafe_python_code",
                    "detail": reason,
                }

            script_path.write_text(script_content, encoding="utf-8")

            command = [settings.PYTHON_EXECUTABLE, str(script_path)]
            logger.info("Executing Python migration code: %s", command)

            env = {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUNBUFFERED": "1",
                "PATH": os.environ.get("PATH", ""),
            }

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=str(temp_dir),
            )

            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            if process.returncode != 0:
                logger.error("Python execution failed: %s", stderr)
                return {
                    "success": False,
                    "error": "Python execution failed",
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": process.returncode,
                }

            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError:
                logger.error("Python execution returned invalid JSON: %s", stdout)
                return {
                    "success": False,
                    "error": "Python execution produced non-JSON output",
                    "stdout": stdout,
                    "stderr": stderr,
                }

            output_value = None
            if isinstance(parsed, dict):
                output_value = parsed.get("output")
            elif isinstance(parsed, list):
                output_value = parsed

            return {
                "success": True,
                "output": output_value,
                "stdout": stdout,
                "stderr": stderr if stderr else None,
                "details": parsed,
            }
        except subprocess.TimeoutExpired as exc:
            logger.error("Python execution timed out after %s seconds", timeout)
            return {
                "success": False,
                "error": "Python execution timed out",
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            }
        except Exception as exc:
            logger.exception("Unexpected Python execution error")
            return {
                "success": False,
                "error": "Unexpected execution error",
                "detail": str(exc),
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
