"""Safe arithmetic evaluation for spoken calculations."""

import ast
import math
import operator


def calculate(expression):
    """Evaluate a basic arithmetic expression without executing arbitrary code."""
    expression = expression.lower().replace("divided by", "/")
    expression = expression.replace("multiplied by", "*")
    expression = expression.replace("times", "*")
    expression = expression.replace("plus", "+")
    expression = expression.replace("minus", "-")
    expression = expression.replace("to the power of", "**")
    tree = ast.parse(expression, mode="eval")
    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    def evaluate(node):
        # Walk only the explicitly supported AST nodes; never eval user input.
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            left = evaluate(node.left)
            right = evaluate(node.right)
            return operations[type(node.op)](left, right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            left = evaluate(node.left)
            right = evaluate(node.right)
            return operations[type(node.op)](left, right)
        raise ValueError("Only basic arithmetic is supported.")

    result = evaluate(tree)
    if not isinstance(result, (int, float)) or not math.isfinite(result):
        raise ValueError("The result is not a finite number.")
    return result


def _format_number(value):
    return str(int(value)) if value == int(value) else str(value)
