from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass


class CalculationError(ValueError):
    pass


def estimate_downtime_cost(minutes: float, hourly_rate: float) -> float:
    if minutes < 0 or hourly_rate < 0:
        raise CalculationError("Les valeurs doivent etre positives ou nulles.")
    return round((minutes / 60.0) * hourly_rate, 2)


def calculate_trs(availability: float, performance: float, quality: float) -> float:
    vals = (availability, performance, quality)
    if any(v < 0 or v > 100 for v in vals):
        raise CalculationError("Chaque composante du TRS doit etre comprise entre 0 et 100.")
    return round((availability / 100) * (performance / 100) * (quality / 100) * 100, 2)


_CONVERSIONS = {
    ("mm", "cm"): 0.1,
    ("cm", "mm"): 10.0,
    ("cm", "m"): 0.01,
    ("m", "cm"): 100.0,
    ("m", "km"): 0.001,
    ("km", "m"): 1000.0,
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000.0,
    ("ml", "l"): 0.001,
    ("l", "ml"): 1000.0,
    ("min", "h"): 1 / 60,
    ("h", "min"): 60.0,
}


def convert_unit(value: float, from_unit: str, to_unit: str) -> float:
    src = from_unit.strip().lower()
    dst = to_unit.strip().lower()
    if src == dst:
        return float(value)
    key = (src, dst)
    if key not in _CONVERSIONS:
        raise CalculationError(f"Conversion non prise en charge: {from_unit} -> {to_unit}")
    return round(float(value) * _CONVERSIONS[key], 6)


_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_arithmetic(expression: str) -> float:
    if not expression or len(expression) > 120:
        raise CalculationError("Expression vide ou trop longue.")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculationError("Expression invalide.") from exc

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = visit(node.left)
            right = visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise CalculationError("Puissance trop importante.")
            return float(_ALLOWED_BINOPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return float(_ALLOWED_UNARY[type(node.op)](visit(node.operand)))
        raise CalculationError("Seules les operations arithmetiques simples sont autorisees.")

    try:
        result = visit(tree)
    except ZeroDivisionError as exc:
        raise CalculationError("Division par zero.") from exc
    if not math.isfinite(result):
        raise CalculationError("Resultat non fini.")
    return round(result, 8)
