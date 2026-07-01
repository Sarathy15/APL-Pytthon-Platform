import json
from backend.agents.conversion_agent import ConversionAgent
from backend.execution.python_runner import PythonRunner


def run_and_get_output(apl_code: str, inputs: dict):
    conv = ConversionAgent._fallback_conversion(apl_code, {})
    python = conv["python_code"]
    result = PythonRunner.execute(python, inputs=inputs)
    return conv, result


def test_sum_reduction():
    apl = "Total ← +/A"
    inputs = {"A": [1, 2, 3, 4]}
    conv, res = run_and_get_output(apl, inputs)
    assert "np.sum" in conv["python_code"]
    assert res["success"] is True
    assert res["output"] == 10


def test_list_literal_and_reduction():
    apl = "L ← 1 2 3\nS ← +/L"
    inputs = {}
    conv, res = run_and_get_output(apl, inputs)
    assert "L = [1, 2, 3]" in conv["python_code"] or "L = [1,2,3]" in conv["python_code"]
    assert res["success"] is True
    assert res["output"] == 6


def test_preserve_variable_names_and_order():
    apl = "X ← 5\nY ← X × 2\nZ ← Y + 3"
    inputs = {}
    conv, res = run_and_get_output(apl, inputs)
    # ensure variables X, Y, Z exist in generated code in that order
    code = conv["python_code"]
    assert "X =" in code
    assert "Y =" in code
    assert "Z =" in code
    assert res["success"] is True
    assert res["output"] == 13
