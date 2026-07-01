def calculate_syntax_score(python_code: str) -> float:
    try:
        compile(python_code, '<string>', 'exec')
        return 100.0
    except SyntaxError:
        return 0.0


def calculate_complexity_score(python_code: str) -> float:
    lines = python_code.count('\n') + 1
    return max(0.0, min(100.0, 100.0 / lines * 1.5))
