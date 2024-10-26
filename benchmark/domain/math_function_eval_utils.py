"""This module contains utility functions for evaluating mathematical functions."""

import ast
import math
import operator
from typing import Any


class MathFunctionEvalUtils:
    """Utility functions for evaluating mathematical string functions."""

    _allowed_node_operator_map: dict[type, Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Eq: operator.eq,
    }
    _allowed_math_functions = {name for name in dir(math) if not name.startswith("__")}

    @staticmethod
    def _is_string_math_evaluation_safety(lookup: str) -> bool:
        """Check if the string math evaluation is safe.

        The function will check if the string math evaluation is safe and
        raise an error if the string math evaluation is not safe.

        Raise:
            ValueError: If the string math evaluation is not safe.
        """
        calculation_tree = ast.parse(lookup, mode="eval")

        allowed_math_functions = {
            name for name in dir(math) if not name.startswith("__")
        }
        allowed_nodes_for_calculation = {
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.BitXor,
            ast.USub,
            ast.UAdd,
            ast.Load,
            ast.Constant,
            ast.Compare,
            ast.Name,
            ast.Eq,
            ast.Attribute,
        }
        for node in ast.walk(calculation_tree):
            NODE_OPERATION_IS_NOT_ALLOWED = not isinstance(
                node, tuple(allowed_nodes_for_calculation)
            ) and not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in allowed_math_functions
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "math"
            )
            if NODE_OPERATION_IS_NOT_ALLOWED:
                raise ValueError(f"{node} is an invalid expression.")

        return True

    @staticmethod
    def _eval_binop(left: ast.AST, op: ast.AST, right: ast.AST):
        """Evaluate a binary operation (e.g. add, sub -> 1 + 1) between two operands.

        Args:
            left: The left operand of the binary operation.
            op: The operator of the binary operation. Must be a type that is in the
                _allowed_node_operator_map of MathFunctionEvalUtils.
            right: The right operand of the binary operation.

        Returns:
            The result of the binary operation.

        Raises:
            ValueError: If the operator is not valid
                (i.e., not in _allowed_node_operator_map).
        """
        if type(op) not in MathFunctionEvalUtils._allowed_node_operator_map:
            raise ValueError(f"{op} is not a valid operator")
        return MathFunctionEvalUtils._allowed_node_operator_map[type(op)](
            MathFunctionEvalUtils.more_safe_eval(left),
            MathFunctionEvalUtils.more_safe_eval(right),
        )

    @staticmethod
    def _eval_unaryop(op: ast.AST, operand: ast.AST):
        """Evaluate a unary operation (e.g. negative -> -1) on the given operand.

        Args:
            op: The unary operator to be applied. The type of `op` must be in the
                `_allowed_node_operator_map` of `MathFunctionEvalUtils`.
            operand: The operand on which the unary operation is to be performed.

        Returns:
            The result of applying the unary operator to the operand.

        Raises:
            ValueError: If `op` is not a valid operator according to
                        `_allowed_node_operator_map`.
        """
        if type(op) not in MathFunctionEvalUtils._allowed_node_operator_map:
            raise ValueError(f"{op} is not a valid operator")
        return MathFunctionEvalUtils._allowed_node_operator_map[type(op)](
            MathFunctionEvalUtils.more_safe_eval(operand)
        )

    @staticmethod
    def _eval_call(func: ast.AST, args: list[ast.expr]):
        """Evaluate a function call from `import math` with the provided arguments.

        Args:
            func: The function attribute node representing the math function.
            args: A list of arguments to be passed to the math function.

        Returns:
            The result of the evaluated math function.

        Raises:
            ValueError: If the provided function is not a
                valid math function or does not belong to the 'math' module.
        """
        if not isinstance(func, ast.Attribute):
            raise ValueError(f"{func} is not a valid math function.")
        if (
            func.attr not in MathFunctionEvalUtils._allowed_math_functions
            or not isinstance(func.value, ast.Name)
            or func.value.id != "math"
        ):
            raise ValueError(f"{func} is not a valid math function.")
        return getattr(math, func.attr)(
            *map(MathFunctionEvalUtils.more_safe_eval, args)
        )

    @staticmethod
    def more_safe_eval(node: ast.AST) -> float:
        """Safely evaluates an abstract syntax tree (AST) node and returns a float.

        This method evaluates a subset of Python expressions represented as AST nodes.
        It supports basic arithmetic operations, unary operations, comparisons, and
        certain math functions from the `math` module. The evaluation is restricted to
        ensure safety by only allowing specific operations and functions.

        Args:
            node: The AST node to evaluate.

        Returns:
            The result of a mathematic function passed from a string and
            to a AST node and calculated stepwise.

        Raises:
            ValueError: If the node contains an invalid operator or function.
            TypeError: If the node type is not supported.
        """
        match node:
            case ast.Constant(value) if isinstance(value, (int, float)):
                return value
            case ast.BinOp(left, op, right):
                return MathFunctionEvalUtils._eval_binop(left, op, right)
            case ast.UnaryOp(op, operand):
                return MathFunctionEvalUtils._eval_unaryop(op, operand)
            case ast.Compare(left, [op], [right]):
                return int(left == right)
            case ast.Call(func, args):
                return MathFunctionEvalUtils._eval_call(func, args)
            case _:
                raise TypeError(node)
