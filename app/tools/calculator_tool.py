"""
Calculator tool implementation.

Safely evaluates basic arithmetic expressions (e.g. "2+2", "8*5",
"100/4", "50-8") using Python's ast module instead of eval(). Only
numeric literals combined with +, -, *, and / are permitted; anything
else (names, calls, attributes, imports, comprehensions, strings, etc.)
is rejected as unsafe. No AI logic, external API calls, or persistence
is implemented here.
"""

import ast
import operator
import re
from typing import Callable, Dict, Optional, Type, Union

from app.tools.base_tool import BaseTool

Number = Union[int, float]

_ALLOWED_BINARY_OPERATORS: Dict[Type[ast.operator], Callable[[Number, Number], Number]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_ALLOWED_UNARY_OPERATORS: Dict[Type[ast.unaryop], Callable[[Number], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_ALLOWED_NODE_TYPES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.UAdd,
    ast.USub,
)

_SAFE_CHARS_PATTERN = re.compile(r"[0-9.\s+\-*/()]+")
_OPERATOR_PATTERN = re.compile(r"[+\-*/]")
_DIGIT_PATTERN = re.compile(r"\d")


def _extract_expression(text: str) -> Optional[str]:
    """Find the first arithmetic-looking substring within free text.

    Args:
        text: Arbitrary input text (e.g. "What is 2+2?" or just "2+2").

    Returns:
        The first candidate substring containing only digits, a decimal
        point, whitespace, parentheses, and +/-*/ operators, provided it
        contains at least one digit and one operator. None if no such
        substring exists.
    """
    for candidate in _SAFE_CHARS_PATTERN.findall(text):
        candidate = candidate.strip()
        if (
            candidate
            and _DIGIT_PATTERN.search(candidate)
            and _OPERATOR_PATTERN.search(candidate)
        ):
            return candidate
    return None


def _validate_node(node: ast.AST) -> None:
    """Recursively ensure an AST node tree contains only safe elements.

    Args:
        node: The AST node (and its children) to validate.

    Raises:
        ValueError: If the node, or any descendant, is not on the
            whitelist of allowed arithmetic node types, or a constant is
            not a plain int/float.
    """
    if not isinstance(node, _ALLOWED_NODE_TYPES):
        raise ValueError(f"Unsafe expression element: {type(node).__name__}")
    if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
        raise ValueError("Only numeric constants are allowed")
    for child in ast.iter_child_nodes(node):
        _validate_node(child)


def _evaluate(node: ast.AST) -> Number:
    """Recursively evaluate a validated arithmetic AST node.

    Args:
        node: A previously validated AST node (see `_validate_node`).

    Returns:
        The numeric result of evaluating the node.

    Raises:
        ValueError: If an unsupported operator is encountered.
        ZeroDivisionError: If the expression divides by zero.
    """
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.BinOp):
        op_func = _ALLOWED_BINARY_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_evaluate(node.left), _evaluate(node.right))

    if isinstance(node, ast.UnaryOp):
        op_func = _ALLOWED_UNARY_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_evaluate(node.operand))

    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def _format_number(value: Number) -> str:
    """Format a numeric result for display.

    Args:
        value: The numeric value to format.

    Returns:
        The value as a string, without a trailing ".0" for whole-number
        floats (e.g. 25.0 -> "25").
    """
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class CalculatorTool(BaseTool):
    """Tool that safely evaluates basic arithmetic expressions.

    Attributes:
        name: Short identifier for this tool.
        description: Human-readable summary of what this tool does.
    """

    name: str = "calculator_tool"
    description: str = (
        "Safely evaluates basic arithmetic expressions using addition, "
        "subtraction, multiplication, and division (e.g. '2+2', '8*5', "
        "'100/4', '50-8')."
    )

    def can_handle(self, query: str) -> bool:
        """Determine whether this tool can answer the given query.

        Args:
            query: The user's input text.

        Returns:
            True if a safe arithmetic expression can be extracted and
            parsed from the query, False otherwise.
        """
        expression = _extract_expression(query)
        if expression is None:
            return False
        try:
            self._parse_safe(expression)
        except (SyntaxError, ValueError):
            return False
        return True

    def run(self, query: str) -> str:
        """Evaluate the arithmetic expression found in the query.

        Args:
            query: The user's input text.

        Returns:
            A string of the form "<expression> = <result>", or a
            friendly error message if no valid/safe expression could be
            found or evaluated.
        """
        expression = _extract_expression(query)
        if expression is None:
            return "I couldn't find a valid arithmetic expression to calculate."

        try:
            tree = self._parse_safe(expression)
            result = _evaluate(tree.body)
        except ZeroDivisionError:
            return f"I can't calculate '{expression}' because division by zero is undefined."
        except (SyntaxError, ValueError):
            return f"'{expression}' is not a valid or safe arithmetic expression."

        return f"{expression} = {_format_number(result)}"

    @staticmethod
    def _parse_safe(expression: str) -> ast.Expression:
        """Parse an expression into an AST and validate it is safe.

        Args:
            expression: The arithmetic expression source text.

        Returns:
            The parsed and validated AST expression node.

        Raises:
            SyntaxError: If the expression is not valid Python syntax.
            ValueError: If the expression contains disallowed elements.
        """
        tree = ast.parse(expression, mode="eval")
        _validate_node(tree)
        return tree
