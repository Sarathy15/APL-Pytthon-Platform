from backend.execution.python_runner import PythonRunner


def test_python_runner_injects_named_inputs():
    code = "result = Salary[0]"
    outputs = PythonRunner.execute(code, inputs={"Salary": [10, 20]})

    assert outputs["success"] is True
    assert outputs["output"] == 10


def test_python_runner_supports_dict_test_cases():
    code = "result = Salary[0] + Bonus"
    test_cases = [
        {"Salary": [10, 20], "Bonus": 5},
        {"Salary": [1, 2], "Bonus": 2},
    ]
    outputs = PythonRunner.execute(code, test_cases=test_cases)

    assert outputs["success"] is True
    assert outputs["output"] == [
        {"success": True, "output": 15},
        {"success": True, "output": 3},
    ]
