"""
Workflow Condition Evaluation Service

Evaluates conditional expressions for workflow branching logic.
Supports JavaScript-like expressions with safe evaluation.
"""

import ast
import operator
import re
from typing import Any, Dict, Optional


class ConditionEvaluator:
    """Evaluates conditional expressions in workflow execution."""

    # Safe operators for evaluation
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """Initialize evaluator with optional context.

        Args:
            context: Dictionary of variables available in the expression
        """
        self.context = context or {}

    def evaluate(self, expression: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Evaluate a conditional expression.

        Args:
            expression: The condition expression to evaluate
            context: Optional additional context variables

        Returns:
            Boolean result of the expression

        Raises:
            ValueError: If the expression is invalid or unsafe
        """
        if not expression or not expression.strip():
            return True  # Empty condition is always true

        # Merge contexts
        eval_context = {**self.context, **(context or {})}

        try:
            # Parse the expression
            tree = ast.parse(expression.strip(), mode='eval')

            # Evaluate safely
            result = self._eval_node(tree.body, eval_context)

            # Convert to boolean
            return bool(result)

        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        except Exception as e:
            raise ValueError(f"Error evaluating condition: {e}")

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""

        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value

        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            raise ValueError(f"Undefined variable: {node.id}")

        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, context) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            if isinstance(node.op, ast.Not):
                return not operand
            elif isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_type = type(node.op)
            if op_type in self.SAFE_OPERATORS:
                return self.SAFE_OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_type = type(op)
                if op_type in self.SAFE_OPERATORS:
                    if not self.SAFE_OPERATORS[op_type](left, right):
                        return False
                    left = right
                else:
                    raise ValueError(f"Unsupported comparison operator: {op_type.__name__}")
            return True

        elif isinstance(node, ast.Call):
            # Prevent function calls for security
            raise ValueError("Function calls are not allowed in conditions")

        elif isinstance(node, ast.Attribute):
            # Prevent attribute access for security
            raise ValueError("Attribute access is not allowed in conditions")

        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            slice_value = self._eval_node(node.slice, context)
            return value[slice_value]

        elif isinstance(node, ast.List):
            return [self._eval_node(elt, context) for elt in node.elts]

        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k, context): self._eval_node(v, context)
                for k, v in zip(node.keys, node.values)
            }

        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elt, context) for elt in node.elts)

        elif isinstance(node, ast.Expression):
            return self._eval_node(node.body, context)

        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    def validate_expression(self, expression: str) -> tuple[bool, Optional[str]]:
        """Validate if an expression is syntactically correct and safe.

        Args:
            expression: The expression to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expression or not expression.strip():
            return True, None

        try:
            tree = ast.parse(expression.strip(), mode='eval')
            # Try to evaluate with empty context to check for syntax errors
            self._eval_node(tree.body, {})
            return True, None
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Invalid expression: {e}"


def evaluate_condition(expression: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to evaluate a condition.

    Args:
        expression: The condition expression
        context: Optional context variables

    Returns:
        Boolean result of the expression
    """
    evaluator = ConditionEvaluator(context)
    return evaluator.evaluate(expression, context)


def validate_condition(expression: str) -> tuple[bool, Optional[str]]:
    """Validate a condition expression.

    Args:
        expression: The expression to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    evaluator = ConditionEvaluator()
    return evaluator.validate_expression(expression)
