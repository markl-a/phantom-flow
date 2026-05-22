"""Tests for the calculator v2 tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestCalculatorToolV2:
    """Tests for CalculatorToolV2 class."""

    def test_calculate_simple_addition(self):
        """Test simple addition calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="2+3")

        assert result["success"] is True
        assert result["result"] == 5

    def test_calculate_complex_expression(self):
        """Test complex expression calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="2+2*3")

        assert result["success"] is True
        assert result["result"] == 8  # Operator precedence

    def test_calculate_with_parentheses(self):
        """Test expression with parentheses."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="(2+2)*3")

        assert result["success"] is True
        assert result["result"] == 12

    def test_calculate_subtraction(self):
        """Test subtraction calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="10-4")

        assert result["success"] is True
        assert result["result"] == 6

    def test_calculate_division(self):
        """Test division calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="15/3")

        assert result["success"] is True
        assert result["result"] == 5.0

    def test_calculate_power(self):
        """Test power calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="2**3")

        assert result["success"] is True
        assert result["result"] == 8

    def test_calculate_modulo(self):
        """Test modulo calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="10%3")

        assert result["success"] is True
        assert result["result"] == 1

    def test_calculate_negative_number(self):
        """Test calculation with negative number."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="-5+3")

        assert result["success"] is True
        assert result["result"] == -2

    def test_calculate_float_numbers(self):
        """Test calculation with float numbers."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="3.5+2.5")

        assert result["success"] is True
        assert result["result"] == 6.0

    def test_calculate_division_by_zero(self):
        """Test division by zero returns error."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="5/0")

        assert result["success"] is False
        assert "error" in result

    def test_calculate_invalid_expression(self):
        """Test invalid expression returns error."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(operation="calculate", expression="2+")

        assert result["success"] is False

    def test_calculate_blocked_code_injection(self):
        """Test that code injection is blocked."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        # This should fail safely without executing import
        result = calc.execute(operation="calculate", expression="__import__('os')")

        assert result["success"] is False

    def test_percentage_calculation(self):
        """Test percentage calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(
            operation="percentage",
            value=200,
            percentage=15
        )

        assert result["success"] is True
        assert result["result"] == 30.0

    def test_percentage_calculation_zero(self):
        """Test percentage calculation with zero."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(
            operation="percentage",
            value=100,
            percentage=0
        )

        assert result["success"] is True
        assert result["result"] == 0.0

    def test_compound_interest_annual(self):
        """Test annual compound interest calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(
            operation="compound_interest",
            principal=1000,
            rate=5,  # 5%
            time=2,  # 2 years
            n=1  # annual
        )

        assert result["success"] is True
        # A = 1000 * (1 + 0.05/1)^(1*2) = 1000 * 1.1025 = 1102.50
        assert result["final_amount"] == 1102.50
        assert result["interest_earned"] == 102.50

    def test_compound_interest_quarterly(self):
        """Test quarterly compound interest calculation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.execute(
            operation="compound_interest",
            principal=1000,
            rate=10,  # 10%
            time=1,  # 1 year
            n=4  # quarterly
        )

        assert result["success"] is True
        assert result["compound_frequency"] == 4
        # A = 1000 * (1 + 0.1/4)^(4*1) ≈ 1103.81
        assert result["final_amount"] == 1103.81

    def test_validate_inputs_missing_expression(self):
        """Test validation with missing expression."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(operation="calculate")

        assert "Missing required parameter: expression" in str(exc_info.value)

    def test_validate_inputs_empty_expression(self):
        """Test validation with empty expression."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(operation="calculate", expression="   ")

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_inputs_invalid_type(self):
        """Test validation with invalid expression type."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(operation="calculate", expression=123)

        assert "must be a string" in str(exc_info.value)

    def test_validate_inputs_percentage_missing_params(self):
        """Test validation for percentage with missing params."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(operation="percentage", value=100)

        assert "Missing required parameters" in str(exc_info.value)

    def test_validate_inputs_percentage_invalid_types(self):
        """Test validation for percentage with invalid types."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(
                operation="percentage",
                value="not a number",
                percentage=10
            )

        assert "must be a number" in str(exc_info.value)

    def test_validate_inputs_compound_interest_missing_params(self):
        """Test validation for compound interest with missing params."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(
                operation="compound_interest",
                principal=1000,
                rate=5
            )

        assert "Missing required parameter: time" in str(exc_info.value)

    def test_validate_inputs_unknown_operation(self):
        """Test validation with unknown operation."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        with pytest.raises(ValueError) as exc_info:
            calc.validate_inputs(operation="unknown")

        assert "Unknown operation" in str(exc_info.value)

    def test_get_schema(self):
        """Test getting OpenAI function schema."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        schema = calc.get_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "calculator_v2"
        assert "parameters" in schema["function"]
        assert "operation" in schema["function"]["parameters"]["properties"]

    def test_metadata(self):
        """Test tool metadata."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        assert calc.metadata.name == "calculator_v2"
        assert calc.metadata.version == "2.0.0"
        assert "math" in calc.metadata.tags
        assert calc.metadata.category == "utility"


class TestCalculatorToolV2Run:
    """Tests for CalculatorToolV2 run method (which calls validate + execute)."""

    def test_run_calls_validate_and_execute(self):
        """Test that run method validates and executes."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()
        result = calc.run(operation="calculate", expression="1+1")

        assert result["success"] is True
        assert result["result"] == 2

    def test_run_with_invalid_params_returns_error(self):
        """Test run with invalid params returns error or raises ValueError."""
        from ai_automation_framework.tools.calculator_v2 import CalculatorToolV2

        calc = CalculatorToolV2()

        # The run method may either raise ValueError or return an error dict
        try:
            result = calc.run(operation="calculate")  # Missing expression
            # If it returns a result, it should indicate failure
            assert result.get("success") is False or "error" in result
        except ValueError:
            # If it raises, that's also valid behavior
            pass
