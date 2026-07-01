"""
End-to-End AI-Driven APL to Python Migration Test

NO MANUAL PYTHON CODE.

The Python code must be generated automatically by:
- UnderstandingAgent
- ConversionAgent

Test flow:
APL → Understanding Agent → Conversion Agent → Generated Python
↓                                                          ↓
APL Execution ←────────── Trace Replay & Compare ────── Python Execution
"""

import json
import asyncio
from pathlib import Path
from typing import Any

from backend.agents.understanding_agent import UnderstandingAgent
from backend.agents.conversion_agent import ConversionAgent
from backend.execution.apl_runner import APLRunner
from backend.execution.python_runner import PythonRunner
from backend.traces.trace_replay import TraceReplay
from backend.traces.trace_schema import TraceRecord, ExecEnv
from backend.comparator.engine import ComparatorEngine
from backend.utils.logger import get_logger
from datetime import datetime
import platform

logger = get_logger(__name__)

OUTPUT_DIR = Path("outputs") / "e2e_ai_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# TEST CASES - NO MANUAL PYTHON
# ============================================================================

TEST_CASES = [
    {
        "id": "TEST_1",
        "name": "Sum Reduction (+/A)",
        "apl_code": "+/A",
        "inputs": {"A": [1, 2, 3]},
        "expected_output": 6,
        "description": "APL sum of integer vector",
    },
    {
        "id": "TEST_2",
        "name": "Product Reduction (×/A)",
        "apl_code": "×/A",
        "inputs": {"A": [2, 3, 4]},
        "expected_output": 24,
        "description": "APL product reduction - AI must understand × operator",
    },
    {
        "id": "TEST_3",
        "name": "Max Reduction (ceiling/A)",
        "apl_code": "⌈/A",
        "inputs": {"A": [1, 8, 3]},
        "expected_output": 8,
        "description": "APL maximum reduction - AI must understand ceiling operator",
    },
]


async def run_e2e_test():
    """
    Run full end-to-end AI migration pipeline for all test cases.
    """
    summary = {
        "pipeline_working": False,
        "successful_conversions": 0,
        "failed_conversions": 0,
        "ready_for_phase5": False,
        "tests": [],
    }

    print("\n" + "=" * 80)
    print("END-TO-END AI CONVERSION TEST - NO MANUAL PYTHON")
    print("=" * 80)

    for test_case in TEST_CASES:
        test_id = test_case["id"]
        apl_code = test_case["apl_code"]
        inputs = test_case["inputs"]
        expected = test_case["expected_output"]

        print(f"\n{test_id}: {test_case['name']}")
        print("-" * 80)
        print(f"Description: {test_case['description']}")
        print(f"APL Input:   {repr(apl_code)}")
        print(f"Inputs:      {inputs}")
        print(f"Expected:    {expected}")

        result = {
            "id": test_id,
            "name": test_case["name"],
            "apl_code": apl_code,
            "inputs": inputs,
            "expected_output": expected,
        }

        try:
            # ================================================================
            # STEP 1: UnderstandingAgent analyzes APL
            # ================================================================
            print(f"\n[1] Understanding Agent analyzing: {apl_code}")
            understanding = await UnderstandingAgent.analyze(apl_code)
            print(f"    Operator:   {understanding.get('operator')}")
            print(f"    Meaning:    {understanding.get('meaning')}")
            print(f"    Category:   {understanding.get('category')}")
            print(f"    Confidence: {understanding.get('confidence', 0):.0f}%")

            result["understanding_agent_output"] = understanding

            # ================================================================
            # STEP 2: ConversionAgent generates Python (NO MANUAL CODE)
            # ================================================================
            print(f"\n[2] Conversion Agent generating Python...")
            conversion = await ConversionAgent.convert(apl_code, understanding)
            
            if not conversion.get("python_code"):
                print(f"    [FAILED] No Python code generated")
                result["generated_python"] = None
                result["conversion_status"] = "failed"
                result["pass_fail"] = "FAIL"
                summary["failed_conversions"] += 1
                summary["tests"].append(result)
                continue

            generated_python = conversion.get("python_code")
            syntax_valid = conversion.get("syntax_valid", False)
            confidence = conversion.get("confidence_score", 0)

            print(f"    Generated:\n{generated_python}")
            print(f"    Syntax Valid: {syntax_valid}")
            print(f"    Confidence:  {confidence:.0f}%")

            result["generated_python"] = generated_python
            result["conversion_confidence"] = confidence
            result["syntax_valid"] = syntax_valid

            if not syntax_valid:
                print(f"    [FAILED] Generated Python has syntax errors")
                result["conversion_status"] = "syntax_error"
                result["pass_fail"] = "FAIL"
                summary["failed_conversions"] += 1
                summary["tests"].append(result)
                continue

            result["conversion_status"] = "success"

            # ================================================================
            # STEP 3: Execute APL code with inputs
            # ================================================================
            print(f"\n[3] Executing APL...")
            apl_result = APLRunner.execute(apl_code, inputs=inputs, timeout=10)
            apl_success = apl_result.get("success", False)
            apl_output = apl_result.get("output")

            print(f"    Success: {apl_success}")
            print(f"    Output:  {apl_output}")

            result["apl_success"] = apl_success
            result["apl_output"] = apl_output

            if not apl_success:
                print(f"    [FAILED] APL execution failed: {apl_result.get('error')}")
                result["pass_fail"] = "FAIL"
                summary["failed_conversions"] += 1
                summary["tests"].append(result)
                continue

            # ================================================================
            # STEP 4: Execute generated Python code
            # ================================================================
            print(f"\n[4] Executing Generated Python...")
            # Build proper Python source with input bindings
            py_source = TraceReplay._build_python_source(generated_python, inputs)
            py_result = PythonRunner.execute(py_source, timeout=10)
            py_success = py_result.get("success", False)
            py_output = py_result.get("output")

            print(f"    Success: {py_success}")
            print(f"    Output:  {py_output}")

            result["python_success"] = py_success
            result["python_output"] = py_output

            if not py_success:
                print(f"    [FAILED] Python execution failed: {py_result.get('error')}")
                result["pass_fail"] = "FAIL"
                summary["failed_conversions"] += 1
                summary["tests"].append(result)
                continue

            # ================================================================
            # STEP 5: Trace Replay & Comparison
            # ================================================================
            print(f"\n[5] Comparing Results...")
            comparison = ComparatorEngine.compare(apl_output, py_output, rtol=1e-7, atol=1e-9)
            match = comparison.get("match", False)
            confidence_score = comparison.get("score", 0)

            print(f"    Match:      {match}")
            print(f"    Confidence: {confidence_score:.0f}%")
            print(f"    Details:    {comparison.get('details', {})}")

            result["replay_match"] = match
            result["comparator_confidence"] = confidence_score
            result["comparator_details"] = comparison.get("details", {})

            # ================================================================
            # STEP 6: Final PASS/FAIL
            # ================================================================
            is_pass = (
                apl_success
                and py_success
                and match
                and apl_output == expected
                and py_output == expected
            )

            result["pass_fail"] = "PASS" if is_pass else "FAIL"

            if is_pass:
                print(f"\n[PASS] {test_id} PASSED")
                summary["successful_conversions"] += 1
            else:
                print(f"\n[FAIL] {test_id} FAILED")
                if apl_output != expected:
                    print(f"   APL output mismatch: {apl_output} != {expected}")
                if py_output != expected:
                    print(f"   Python output mismatch: {py_output} != {expected}")
                if not match:
                    print(f"   Comparator mismatch detected")
                summary["failed_conversions"] += 1

        except Exception as exc:
            print(f"[ERROR] Unexpected error: {exc}")
            logger.exception("Test case exception")
            result["pass_fail"] = "FAIL"
            result["error"] = str(exc)
            summary["failed_conversions"] += 1

        summary["tests"].append(result)

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    summary["pipeline_working"] = summary["failed_conversions"] == 0
    summary["ready_for_phase5"] = (
        summary["pipeline_working"]
        and summary["successful_conversions"] == len(TEST_CASES)
    )

    result_json = {
        "pipeline_working": summary["pipeline_working"],
        "successful_conversions": summary["successful_conversions"],
        "failed_conversions": summary["failed_conversions"],
        "ready_for_phase5": summary["ready_for_phase5"],
        "total_tests": len(TEST_CASES),
        "pass_rate": f"{(summary['successful_conversions'] / len(TEST_CASES) * 100):.0f}%",
        "tests": summary["tests"],
    }

    print(json.dumps(result_json, indent=2, default=str))

    # Save to file
    output_file = OUTPUT_DIR / "e2e_ai_conversion_results.json"
    output_file.write_text(json.dumps(result_json, indent=2, default=str), encoding="utf-8")
    print(f"\n[OK] Results saved to: {output_file}")

    return result_json


if __name__ == "__main__":
    results = asyncio.run(run_e2e_test())
    
    # Exit with success only if all tests passed
    exit(0 if results["ready_for_phase5"] else 1)
