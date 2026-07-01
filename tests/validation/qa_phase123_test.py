import json
from pathlib import Path

from backend.traces import TraceCapture, TraceReplay
from backend.execution.python_runner import PythonRunner
from backend.execution.apl_runner import APLRunner

OUTPUT_DIR = Path("outputs") / "traces" / "qa_phase123"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

cases = [
    {
        "name": "happy_path",
        "apl_code": "+/A",
        "inputs": {"A": [1, 2, 3]},
        "python_code": "result = sum(A)",
        "expect_match": True,
        "description": "APL sum of integer vector",
    },
    {
        "name": "empty_array",
        "apl_code": "+/A",
        "inputs": {"A": []},
        "python_code": "result = sum(A)",
        "expect_match": True,
        "description": "APL sum of empty array",
    },
    {
        "name": "negative_values",
        "apl_code": "+/A",
        "inputs": {"A": [-1, -2, -3]},
        "python_code": "result = sum(A)",
        "expect_match": True,
        "description": "APL sum of negative values",
    },
    {
        "name": "float_values",
        "apl_code": "+/A",
        "inputs": {"A": [0.1, 0.2, 0.3]},
        "python_code": "result = sum(A)",
        "expect_match": True,
        "description": "APL sum with float values",
    },
    {
        "name": "nan_value",
        "apl_code": "+/A",
        "inputs": {"A": [1, float("nan"), 3]},
        "python_code": "import math\nresult = sum(A) if not any(math.isnan(x) for x in A if isinstance(x, float)) else float('nan')",
        "expect_match": False,
        "description": "APL with NaN should not crash; compare handling",
    },
    {
        "name": "infinity_value",
        "apl_code": "+/A",
        "inputs": {"A": [float("inf"), 1]},
        "python_code": "result = sum(A)",
        "expect_match": True,
        "description": "APL with infinity handling",
    },
    {
        "name": "wrong_python_conversion",
        "apl_code": "+/A",
        "inputs": {"A": [1, 2, 3]},
        "python_code": "result = max(A)",
        "expect_match": False,
        "description": "Wrong Python conversion should fail mismatch",
    },
    {
        "name": "shape_mismatch",
        "apl_code": "+/A",
        "inputs": {"A": [1, 2, 3]},
        "python_code": "result = [1, 2, 3]",
        "expect_match": False,
        "description": "Shape mismatch between scalar and list",
    },
    {
        "name": "timeout",
        "apl_code": "+/A",
        "inputs": {"A": [1, 2, 3]},
        "python_code": "while True:\n    pass",
        "expect_match": False,
        "description": "Python timeout should be handled safely",
        "timeout": 1,
    },
    {
        "name": "dangerous_code",
        "apl_code": "+/A",
        "inputs": {"A": [1, 2, 3]},
        "python_code": "import os\nos.system('echo unsafe')\nresult = sum(A)",
        "expect_match": False,
        "description": "Dangerous code attempt should be blocked or fail safely",
    },
]

summary = {"passed": 0, "failed": 0, "cases": [], "critical_issues": []}

capture = TraceCapture(output_dir=OUTPUT_DIR)
replay = TraceReplay(trace_dir=OUTPUT_DIR)

for case in cases:
    case_name = case["name"]
    timeout = case.get("timeout", None)
    trace = capture.capture(
        function_name=case_name,
        apl_code=case["apl_code"],
        inputs=case["inputs"],
        metadata={"case": case_name},
        seed=None,
        timeout=timeout,
    )
    report = replay.replay_trace(trace, python_code=case["python_code"], timeout=timeout)

    python_output = report.get("python_output")
    apl_output = report.get("apl_output")
    match = report.get("match", False)
    status = "PASS" if match == case["expect_match"] else "FAIL"
    reason = []
    if status == "FAIL":
        reason.append("match expectation not met")
    if case_name == "timeout" and report.get("python_error") is None:
        reason.append("timeout not reported")
    if case_name == "dangerous_code" and report.get("python_error") is None and report.get("python_success"):
        reason.append("dangerous code executed without failure")

    if status == "PASS":
        summary["passed"] += 1
    else:
        summary["failed"] += 1

    summary["cases"].append(
        {
            "name": case_name,
            "description": case["description"],
            "inputs": case["inputs"],
            "apl_output": apl_output,
            "python_output": python_output,
            "replay_result": report,
            "pass": status == "PASS",
            "reason": reason,
        }
    )

    if case_name == "dangerous_code" and report.get("python_success"):
        summary["critical_issues"].append("Dangerous code executed in PythonRunner")
    if case_name == "timeout" and report.get("python_success"):
        summary["critical_issues"].append("Timeout handling failed")

print(json.dumps(summary, indent=2, default=str))
