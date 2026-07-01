from backend.agents.conversion_agent import ConversionAgent


def test_normalize_python_code_corrects_named_input_and_result_assignment():
    apl_code = (
        "AvgSalary ← (+/Salary) ÷ ⍴Salary\n"
        "MaxSalary ← ⌈/Salary\n"
        "MinSalary ← ⌊/Salary\n"
        "Eligible ← Salary > AvgSalary\n"
        "Result ← AvgSalary MaxSalary MinSalary"
    )
    understanding = {
        "variables": ["AvgSalary", "MaxSalary", "MinSalary", "Eligible", "Result"],
        "dependencies": {
            "AvgSalary": ["Salary"],
            "MaxSalary": ["Salary"],
            "MinSalary": ["Salary"],
            "Eligible": ["Salary", "AvgSalary"],
            "Result": ["AvgSalary", "MaxSalary", "MinSalary"],
        },
    }

    generated = "result = np.array(A)\nAvgSalary = np.mean(result)\n"
    normalized = ConversionAgent._normalize_python_code(generated, apl_code, understanding)

    assert "Salary = np.array(A)" in normalized
    assert "result = Result" in normalized
    assert normalized.startswith("import numpy as np")
