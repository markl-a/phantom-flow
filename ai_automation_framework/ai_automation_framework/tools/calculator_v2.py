"""
计算器工具 V2 - 使用新的工具系统。

这个模块展示了如何使用新的 BaseTool 基类来创建标准化的工具。
这是 common_tools.py 中 CalculatorTool 的重构版本。
"""

from typing import Dict, Any
import ast
import operator

from ai_automation_framework.core.tool_registry import (
    BaseTool,
    ToolMetadata,
    register_tool
)


@register_tool
class CalculatorToolV2(BaseTool):
    """数学计算工具 - 使用新的工具系统。

    这是 CalculatorTool 的重构版本，展示了如何使用新的 BaseTool 基类。
    支持安全的数学表达式计算、百分比计算和复利计算。

    示例用法：
        >>> from ai_automation_framework.core.tool_registry import get_tool_registry
        >>> registry = get_tool_registry()
        >>> calc = registry.get_tool("calculator_v2")
        >>> result = calc.run(operation="calculate", expression="2+2*3")
        >>> print(result)
        {'expression': '2+2*3', 'result': 8, 'success': True}
    """

    metadata = ToolMetadata(
        name="calculator_v2",
        version="2.0.0",
        author="AI Automation Framework",
        description="安全的数学计算工具，支持基本运算、百分比和复利计算",
        category="utility",
        dependencies=[],
        tags=["math", "calculation", "utility"]
    )

    def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数。

        支持三种操作模式：
        1. calculate: 需要 expression 参数
        2. percentage: 需要 value 和 percentage 参数
        3. compound_interest: 需要 principal, rate, time 参数（可选 n）

        Args:
            **kwargs: 操作参数

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 当参数无效时
        """
        operation = kwargs.get('operation', 'calculate')

        if operation == 'calculate':
            if 'expression' not in kwargs:
                raise ValueError("Missing required parameter: expression")
            if not isinstance(kwargs['expression'], str):
                raise ValueError("expression must be a string")
            if not kwargs['expression'].strip():
                raise ValueError("expression cannot be empty")

        elif operation == 'percentage':
            if 'value' not in kwargs or 'percentage' not in kwargs:
                raise ValueError("Missing required parameters: value, percentage")
            if not isinstance(kwargs['value'], (int, float)):
                raise ValueError("value must be a number")
            if not isinstance(kwargs['percentage'], (int, float)):
                raise ValueError("percentage must be a number")

        elif operation == 'compound_interest':
            required = ['principal', 'rate', 'time']
            for param in required:
                if param not in kwargs:
                    raise ValueError(f"Missing required parameter: {param}")
                if not isinstance(kwargs[param], (int, float)):
                    raise ValueError(f"{param} must be a number")

            # 验证可选参数 n
            if 'n' in kwargs and not isinstance(kwargs['n'], int):
                raise ValueError("n must be an integer")

        else:
            raise ValueError(f"Unknown operation: {operation}")

        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行计算操作。

        Args:
            operation: 操作类型 ('calculate', 'percentage', 'compound_interest')
            **kwargs: 根据操作类型的特定参数

        Returns:
            Dict[str, Any]: 计算结果
        """
        operation = kwargs.get('operation', 'calculate')

        try:
            if operation == 'calculate':
                return self._calculate(kwargs['expression'])
            elif operation == 'percentage':
                return self._calculate_percentage(
                    kwargs['value'],
                    kwargs['percentage']
                )
            elif operation == 'compound_interest':
                return self._calculate_compound_interest(
                    kwargs['principal'],
                    kwargs['rate'],
                    kwargs['time'],
                    kwargs.get('n', 1)
                )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation
            }

    def _calculate(self, expression: str) -> Dict[str, Any]:
        """安全地计算数学表达式。

        使用 AST（抽象语法树）来安全地评估数学表达式，
        防止代码注入攻击。

        Args:
            expression: 数学表达式字符串

        Returns:
            Dict[str, Any]: 包含计算结果或错误信息
        """
        # 定义允许的运算符
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def safe_eval(node):
            """安全地评估 AST 节点。"""
            if isinstance(node, ast.Constant):  # Python 3.8+
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError(f"Invalid constant: {node.value}")
            elif isinstance(node, ast.Num):  # Python 3.7 兼容性
                return node.n
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return operators[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                return operators[op_type](safe_eval(node.operand))
            elif isinstance(node, ast.Expression):
                return safe_eval(node.body)
            else:
                raise ValueError(f"Unsupported expression type: {type(node).__name__}")

        try:
            # 解析表达式为 AST
            tree = ast.parse(expression, mode='eval')
            result = safe_eval(tree)
            return {
                "expression": expression,
                "result": result,
                "success": True
            }
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as e:
            return {
                "expression": expression,
                "error": str(e),
                "success": False
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": f"Evaluation error: {str(e)}",
                "success": False
            }

    def _calculate_percentage(self, value: float, percentage: float) -> Dict[str, Any]:
        """计算百分比。

        Args:
            value: 基础值
            percentage: 百分比

        Returns:
            Dict[str, Any]: 计算结果
        """
        result = (value * percentage) / 100
        return {
            "value": value,
            "percentage": percentage,
            "result": result,
            "success": True
        }

    def _calculate_compound_interest(
        self,
        principal: float,
        rate: float,
        time: float,
        n: int = 1
    ) -> Dict[str, float]:
        """计算复利。

        公式: A = P(1 + r/n)^(nt)
        其中:
            A = 最终金额
            P = 本金
            r = 年利率（小数形式）
            n = 每年复利次数
            t = 时间（年）

        Args:
            principal: 本金
            rate: 年利率（百分比形式，如 5 表示 5%）
            time: 时间（年）
            n: 每年复利次数（默认为 1）

        Returns:
            Dict[str, float]: 包含计算详情的字典
        """
        amount = principal * (1 + (rate/100)/n) ** (n * time)
        interest = amount - principal

        return {
            "principal": principal,
            "rate": rate,
            "time": time,
            "compound_frequency": n,
            "final_amount": round(amount, 2),
            "interest_earned": round(interest, 2),
            "success": True
        }

    def get_schema(self) -> Dict[str, Any]:
        """返回工具的 OpenAI function calling schema。

        这个 schema 可以用于 OpenAI 的 function calling 功能，
        让 AI 模型知道如何调用这个工具。

        Returns:
            Dict[str, Any]: OpenAI function calling schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["calculate", "percentage", "compound_interest"],
                            "description": "计算操作类型",
                            "default": "calculate"
                        },
                        "expression": {
                            "type": "string",
                            "description": "数学表达式（用于 calculate 操作），例如: '2+2*3', '(10-5)/2'"
                        },
                        "value": {
                            "type": "number",
                            "description": "数值（用于 percentage 操作）"
                        },
                        "percentage": {
                            "type": "number",
                            "description": "百分比（用于 percentage 操作）"
                        },
                        "principal": {
                            "type": "number",
                            "description": "本金（用于 compound_interest 操作）"
                        },
                        "rate": {
                            "type": "number",
                            "description": "年利率百分比（用于 compound_interest 操作），例如: 5 表示 5%"
                        },
                        "time": {
                            "type": "number",
                            "description": "时间（年）（用于 compound_interest 操作）"
                        },
                        "n": {
                            "type": "integer",
                            "description": "每年复利次数（用于 compound_interest 操作），例如: 1=年复利, 4=季复利, 12=月复利",
                            "default": 1
                        }
                    },
                    "required": []  # 根据 operation 动态确定
                }
            }
        }


# 便捷函数
def calculate(expression: str) -> Dict[str, Any]:
    """便捷函数：计算数学表达式。

    Args:
        expression: 数学表达式

    Returns:
        Dict[str, Any]: 计算结果
    """
    from ai_automation_framework.core.tool_registry import get_tool_registry
    registry = get_tool_registry()
    calc = registry.get_tool("calculator_v2")
    return calc.run(operation="calculate", expression=expression)


def calculate_percentage(value: float, percentage: float) -> Dict[str, Any]:
    """便捷函数：计算百分比。

    Args:
        value: 基础值
        percentage: 百分比

    Returns:
        Dict[str, Any]: 计算结果
    """
    from ai_automation_framework.core.tool_registry import get_tool_registry
    registry = get_tool_registry()
    calc = registry.get_tool("calculator_v2")
    return calc.run(operation="percentage", value=value, percentage=percentage)


def calculate_compound_interest(
    principal: float,
    rate: float,
    time: float,
    n: int = 1
) -> Dict[str, Any]:
    """便捷函数：计算复利。

    Args:
        principal: 本金
        rate: 年利率（百分比）
        time: 时间（年）
        n: 每年复利次数

    Returns:
        Dict[str, Any]: 计算结果
    """
    from ai_automation_framework.core.tool_registry import get_tool_registry
    registry = get_tool_registry()
    calc = registry.get_tool("calculator_v2")
    return calc.run(
        operation="compound_interest",
        principal=principal,
        rate=rate,
        time=time,
        n=n
    )
