"""
Mini App Integration Test - Employee Salary Analytics

Full AI-driven pipeline:
APL → UnderstandingAgent → ConversionAgent → Generated Python
   ↓                                             ↓
   APL Execution ←────── TraceReplay & Comparator ──── Python Execution

NO MANUAL PYTHON CODE - All Python is automatically generated.
"""

import json
import asyncio
from pathlib import Path

from backend.agents.understanding_agent import UnderstandingAgent
from backend.agents.conversion_agent import ConversionAgent
from backend.execution.apl_runner import APLRunner
from backend.execution.python_runner import PythonRunner
from backend.traces.trace_replay import TraceReplay
from backend.comparator.engine import ComparatorEngine
from backend.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = Path("outputs") / "mini_app_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_mini_app_test():
    """
    Run the employee salary analytics mini app through the full AI migration pipeline.
    """
    
    # ========================================================================
    # MINI APP - Employee Salary Analytics
    # ========================================================================
    
    apl_code = """⍝ Employee Salary Analytics Mini App
AvgSalary ← (+/Salary) ÷ ⍴Salary
MaxSalary ← ⌈/Salary
MinSalary ← ⌊/Salary
Eligible ← Salary > AvgSalary
Result ← AvgSalary MaxSalary MinSalary"""

    inputs = {
        "Salary": [25000, 30000, 45000, 50000, 28000]
    }

    expected_output = [35600, 50000, 25000]  # [AvgSalary, MaxSalary, MinSalary]

    summary = {
        "mini_app_supported": False,
        "business_logic_preserved": False,
        "migration_success": False,
        "test_details": {}
    }

    print("\n" + "=" * 90)
    print("MINI APP INTEGRATION TEST - Employee Salary Analytics")
    print("=" * 90)

    print("\n[APL CODE]")
    print(apl_code)
    print(f"\n[INPUTS]")
    print(f"Salary = {inputs['Salary']}")
    print(f"\n[EXPECTED OUTPUT]")
    print(f"Result = {expected_output}")
    print(f"  - Average Salary: 35600")
    print(f"  - Maximum Salary: 50000")
    print(f"  - Minimum Salary: 25000")

    details = {
        "understanding_agent": {},
        "conversion_agent": {},
        "apl_execution": {},
        "python_execution": {},
        "comparator_result": {},
    }

    try:
        # ====================================================================
        # STEP 1: UnderstandingAgent analyzes APL code
        # ====================================================================
        print("\n" + "-" * 90)
        print("[STEP 1] Understanding Agent - Analyze APL Business Logic")
        print("-" * 90)

        understanding = await UnderstandingAgent.analyze(apl_code)
        details["understanding_agent"] = understanding

        print(f"Operator:     {understanding.get('operator')}")
        print(f"Meaning:      {understanding.get('meaning')}")
        print(f"Category:     {understanding.get('category')}")
        print(f"Explanation:  {understanding.get('explanation')}")
        print(f"Confidence:   {understanding.get('confidence', 0):.0%}")

        if understanding.get('confidence', 0) < 0.5:
            print("\n[WARNING] Low confidence in understanding. Conversion may fail.")

        # ====================================================================
        # STEP 2: ConversionAgent generates Python (NO MANUAL CODE)
        # ====================================================================
        print("\n" + "-" * 90)
        print("[STEP 2] Conversion Agent - Generate Python Automatically")
        print("-" * 90)

        conversion = await ConversionAgent.convert(apl_code, understanding)
        details["conversion_agent"] = conversion

        generated_python = conversion.get("python_code", "")
        syntax_valid = conversion.get("syntax_valid", False)
        conversion_confidence = conversion.get("confidence_score", 0)

        if not generated_python:
            print("[FAILED] ConversionAgent did not generate Python code")
            print(f"Response: {conversion}")
            summary["test_details"] = details
            return summary

        print(f"Generated Python:\n{generated_python}\n")
        print(f"Syntax Valid:     {syntax_valid}")
        print(f"Confidence:       {conversion_confidence:.0%}")

        if not syntax_valid:
            print("\n[FAILED] Generated Python has syntax errors")
            summary["test_details"] = details
            return summary

        # ====================================================================
        # STEP 3: Execute Original APL Code
        # ====================================================================
        print("\n" + "-" * 90)
        print("[STEP 3] Execute Original APL Code")
        print("-" * 90)

        apl_result = APLRunner.execute(apl_code, inputs=inputs, timeout=15)
        details["apl_execution"] = {
            "success": apl_result.get("success"),
            "output": apl_result.get("output"),
            "error": apl_result.get("error"),
        }

        apl_success = apl_result.get("success", False)
        apl_output = apl_result.get("output")

        print(f"Success:   {apl_success}")
        print(f"Output:    {apl_output}")
        print(f"Type:      {type(apl_output).__name__}")

        if not apl_success:
            print(f"Error: {apl_result.get('error')}")
            print(f"Stderr: {apl_result.get('stderr')}")
            summary["test_details"] = details
            return summary

        # ====================================================================
        # STEP 4: Execute Generated Python Code
        # ====================================================================
        print("\n" + "-" * 90)
        print("[STEP 4] Execute Generated Python Code")
        print("-" * 90)

        # Build Python source with input bindings
        py_source = TraceReplay._build_python_source(generated_python, inputs)
        print(f"Python Source:\n{py_source}\n")

        py_result = PythonRunner.execute(py_source, timeout=15)
        details["python_execution"] = {
            "success": py_result.get("success"),
            "output": py_result.get("output"),
            "error": py_result.get("error"),
        }

        py_success = py_result.get("success", False)
        py_output = py_result.get("output")

        print(f"Success:   {py_success}")
        print(f"Output:    {py_output}")
        print(f"Type:      {type(py_output).__name__}")

        if not py_success:
            print(f"Error: {py_result.get('error')}")
            print(f"Stderr: {py_result.get('stderr')}")
            summary["test_details"] = details
            return summary

        # ====================================================================
        # STEP 5: Trace Replay & Comparator Validation
        # ====================================================================
        print("\n" + "-" * 90)
        print("[STEP 5] Trace Replay & Comparator Validation")
        print("-" * 90)

        comparison = ComparatorEngine.compare(apl_output, py_output, rtol=1e-5, atol=1e-8)
        details["comparator_result"] = comparison

        match = comparison.get("match", False)
        confidence_score = comparison.get("score", 0)

        print(f"Match:                {match}")
        print(f"Confidence Score:     {confidence_score:.0%}")
        print(f"Shape OK:             {comparison.get('details', {}).get('shape_ok')}")
        print(f"DType OK:             {comparison.get('details', {}).get('dtype_ok')}")
        print(f"Tolerance OK:         {comparison.get('details', {}).get('tolerance_ok')}")
        print(f"Semantic OK:          {comparison.get('details', {}).get('semantic_ok')}")

        if comparison.get("mismatches"):
            print(f"Mismatches:           {', '.join(comparison.get('mismatches', []))}")

        # ====================================================================
        # STEP 6: Business Logic Validation
        # ====================================================================
        print("\n" + "-" * 90)
        print("[STEP 6] Business Logic Validation")
        print("-" * 90)

        # Extract the Result values
        apl_avg = apl_output[0] if isinstance(apl_output, list) else apl_output
        py_avg = py_output[0] if isinstance(py_output, list) else py_output

        print(f"APL Result:           {apl_output}")
        print(f"Python Result:        {py_output}")
        print(f"Expected:             {expected_output}")

        business_logic_preserved = (
            apl_success
            and py_success
            and match
            and apl_output == py_output
        )

        results_match_expected = (apl_output == expected_output)

        print(f"\nBusiness Logic Preserved: {business_logic_preserved}")
        print(f"Results Match Expected:   {results_match_expected}")

        # ====================================================================
        # FINAL RESULT
        # ====================================================================
        print("\n" + "=" * 90)
        print("FINAL RESULT")
        print("=" * 90)

        summary["mini_app_supported"] = apl_success and py_success and syntax_valid
        summary["business_logic_preserved"] = business_logic_preserved
        summary["migration_success"] = (
            summary["mini_app_supported"]
            and business_logic_preserved
            and match
            and results_match_expected
        )

        status = "✓ PASS" if summary["migration_success"] else "✗ FAIL"
        print(f"\n{status}")
        print(f"\nMini App Supported:        {summary['mini_app_supported']}")
        print(f"Business Logic Preserved:  {summary['business_logic_preserved']}")
        print(f"Migration Success:         {summary['migration_success']}")
        print(f"Comparator Confidence:     {confidence_score:.0%}")

    except Exception as exc:
        print(f"\n[ERROR] Unexpected error: {exc}")
        logger.exception("Mini app test exception")
        summary["test_details"] = details

    # Save results
    output_file = OUTPUT_DIR / "mini_app_results.json"
    output_file.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\n[SAVED] Results to {output_file}")

    return summary


if __name__ == "__main__":
    result = asyncio.run(run_mini_app_test())
    print("\n" + "=" * 90)
    print(json.dumps(result, indent=2, default=str))
    print("=" * 90)
