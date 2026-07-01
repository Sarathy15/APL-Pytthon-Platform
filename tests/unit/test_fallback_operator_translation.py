"""
Regression tests for fallback conversion operator translation.

Tests cover fixes for:
- Arithmetic operators (subtraction) being mangled as lists
- Boolean operators using NumPy bitwise operators for arrays
"""

import ast
import sys
import pytest


def test_subtraction_expression():
    """Test that subtraction expressions are not converted to lists."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Result ← A - B"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should NOT contain [A, -, B] or similar list syntax
    assert "[" not in python_code or "Result = [" not in python_code, \
        f"Subtraction should not be a list: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_subtraction_in_list():
    """Test that subtraction in complex expressions works."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Variance ← HighestValue - LowestValue"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain valid subtraction
    assert "HighestValue - LowestValue" in python_code or \
           "HighestValue-LowestValue" in python_code, \
        f"Expected subtraction expression in: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_greater_than_operator():
    """Test > operator translation."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Filter ← Values > Threshold"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain valid comparison
    assert ">" in python_code, f"Expected > operator in: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_less_than_operator():
    """Test < operator translation."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Filter ← Values < Threshold"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain valid comparison
    assert "<" in python_code, f"Expected < operator in: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_greater_equal_operator():
    """Test ≥ operator translation to >=."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Filter ← Values ≥ Threshold"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain >= (not ≥)
    assert ">=" in python_code, f"Expected >= in: {python_code}"
    assert "≥" not in python_code, f"Unicode ≥ should be replaced: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_less_equal_operator():
    """Test ≤ operator translation to <=."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Filter ← Values ≤ Threshold"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain <= (not ≤)
    assert "<=" in python_code, f"Expected <= in: {python_code}"
    assert "≤" not in python_code, f"Unicode ≤ should be replaced: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_and_operator_becomes_bitwise():
    """Test ∧ (AND) operator translation to & for NumPy compatibility."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Filter ← (A > 5) ∧ (B < 10)"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain & (not 'and' keyword)
    assert " & " in python_code, f"Expected & operator in: {python_code}"
    # Make sure it's not the Python 'and' keyword (which wouldn't work for NumPy arrays)
    lines = python_code.split('\n')
    filter_line = [l for l in lines if 'Filter' in l and '=' in l]
    if filter_line:
        assert " and " not in filter_line[0], \
            f"Should use & for arrays, not 'and': {filter_line[0]}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_or_operator_becomes_bitwise():
    """Test ∨ (OR) operator translation to | for NumPy compatibility."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = "Filter ← (A > 5) ∨ (B < 10)"
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Should contain | (not 'or' keyword)
    assert " | " in python_code, f"Expected | operator in: {python_code}"
    # Make sure it's not the Python 'or' keyword (which wouldn't work for NumPy arrays)
    lines = python_code.split('\n')
    filter_line = [l for l in lines if 'Filter' in l and '=' in l]
    if filter_line:
        assert " or " not in filter_line[0], \
            f"Should use | for arrays, not 'or': {filter_line[0]}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


def test_complex_expression_with_operators():
    """Test complex expression with multiple operators."""
    from backend.agents.conversion_agent import ConversionAgent
    
    apl_code = """Result ← High - Low
    Filter ← (Data ≥ 70) ∧ (Data ≤ 90)"""
    understanding = {}
    
    result = ConversionAgent._fallback_conversion(apl_code, understanding)
    python_code = result['python_code']
    
    # Verify subtraction is not a list
    assert "[High, -, Low]" not in python_code, \
        f"Subtraction should not be a list: {python_code}"
    
    # Verify >= and <= are present
    assert ">=" in python_code, f"Expected >= in: {python_code}"
    assert "<=" in python_code, f"Expected <= in: {python_code}"
    
    # Verify & is used instead of 'and'
    assert " & " in python_code, f"Expected & operator in: {python_code}"
    
    # Should be valid Python
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\n{python_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
