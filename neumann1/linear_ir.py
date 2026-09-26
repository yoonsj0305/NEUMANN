from __future__ import annotations
import ast
import re
from dataclasses import dataclass
from typing import Dict

from .types import Problem, Representation, IRKind, CostLedger, VerificationResult


def _merge(a: Dict[str, float], b: Dict[str, float], scale_b: float = 1.0) -> Dict[str, float]:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0.0) + scale_b * v
        if abs(out[k]) < 1e-12:
            del out[k]
    return out


def _scale(coeffs: Dict[str, float], factor: float) -> Dict[str, float]:
    return {k: factor * v for k, v in coeffs.items()}


def _linearize(node: ast.AST) -> tuple[Dict[str, float], float]:
    """Return (variable coefficients, constant) for a controlled linear expression."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return {}, float(node.value)

    if isinstance(node, ast.Name):
        return {node.id: 1.0}, 0.0

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        c, k = _linearize(node.operand)
        factor = -1.0 if isinstance(node.op, ast.USub) else 1.0
        return _scale(c, factor), factor * k

    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        lc, lk = _linearize(node.left)
        rc, rk = _linearize(node.right)
        sign = 1.0 if isinstance(node.op, ast.Add) else -1.0
        return _merge(lc, rc, sign), lk + sign * rk

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        lc, lk = _linearize(node.left)
        rc, rk = _linearize(node.right)
        left_is_const = not lc
        right_is_const = not rc
        if left_is_const and right_is_const:
            return {}, lk * rk
        if left_is_const:
            return _scale(rc, lk), lk * rk
        if right_is_const:
            return _scale(lc, rk), rk * lk
        raise ValueError("nonlinear multiplication detected")

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        lc, lk = _linearize(node.left)
        rc, rk = _linearize(node.right)
        if rc or abs(rk) < 1e-12:
            raise ValueError("division must be by a nonzero scalar constant")
        return _scale(lc, 1.0 / rk), lk / rk

    raise ValueError(f"unsupported linear-expression syntax: {type(node).__name__}")


def _parse_expression(text: str) -> tuple[Dict[str, float], float]:
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError as exc:
        raise ValueError("invalid controlled linear expression") from exc
    return _linearize(node)


def parse_controlled_linear_system(text: str) -> tuple[list[str], list[list[float]], list[float]]:
    statements = [x.strip() for x in re.split(r"[;\n]+", text) if x.strip()]
    if not statements:
        raise ValueError("empty controlled linear-system input")

    equations: list[tuple[Dict[str, float], float]] = []
    variable_order: list[str] = []

    for i, statement in enumerate(statements):
        statement = re.sub(r"^\s*(?:solve|equation)\s*:\s*", "", statement, flags=re.I)
        if any(op in statement for op in ("<", ">", "!=")):
            raise ValueError("inequality or non-equality relation is not a linear-system equation")
        if statement.count("=") != 1:
            raise ValueError("each controlled linear statement must contain exactly one equality")

        lhs_text, rhs_text = [x.strip() for x in statement.split("=", 1)]
        lhs_c, lhs_k = _parse_expression(lhs_text)
        rhs_c, rhs_k = _parse_expression(rhs_text)
        coeffs = _merge(lhs_c, rhs_c, -1.0)
        rhs_value = -(lhs_k - rhs_k)

        if not coeffs:
            raise ValueError("equation contains no variables")

        for name in list(lhs_c) + list(rhs_c):
            if name not in variable_order:
                variable_order.append(name)
        equations.append((coeffs, rhs_value))

    if len(equations) < 2:
        raise ValueError("controlled linear system requires at least two equations")
    if len(variable_order) != len(equations):
        raise ValueError("controlled compiler currently requires a square system")

    A = [[float(coeffs.get(v, 0.0)) for v in variable_order] for coeffs, _ in equations]
    b = [float(rhs) for _, rhs in equations]
    return variable_order, A, b


class ControlledLinearSystemStructureFormer:
    """Compile a narrow algebraic equality grammar into a solver-ready linear-system IR."""

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        try:
            variables, A, b = parse_controlled_linear_system(problem.raw_text)
        except ValueError as exc:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale=str(exc),
            )
        return Representation(
            kind=IRKind.LINEAR_SYSTEM,
            payload={"variables": variables, "A": A, "b": b},
            confidence=1.0,
            rationale="controlled linear equations compiled to solver-ready matrix IR",
        )


@dataclass(frozen=True)
class LinearSemanticContract:
    variables: tuple[str, ...]
    A: tuple[tuple[float, ...], ...]
    b: tuple[float, ...]


class LinearSemanticVerifier:
    """Benchmark-side semantic verifier for controlled linear-system fixtures."""

    def verify_representation(self, problem: Problem, representation: Representation, ledger: CostLedger) -> VerificationResult:
        contract = problem.metadata.get("linear_semantic_contract")
        ledger.verification_steps += 1
        if not contract:
            return VerificationResult(False, "missing linear semantic contract")
        if representation.kind != IRKind.LINEAR_SYSTEM:
            return VerificationResult(False, "wrong representation kind")

        expected_vars = list(contract["variables"])
        actual_vars = list(representation.payload.get("variables", []))
        if actual_vars != expected_vars:
            return VerificationResult(False, "variable order differs from semantic contract")

        expected_A = contract["A"]
        expected_b = contract["b"]
        actual_A = representation.payload.get("A", [])
        actual_b = representation.payload.get("b", [])
        if len(actual_A) != len(expected_A) or len(actual_b) != len(expected_b):
            return VerificationResult(False, "linear-system dimensions differ from semantic contract")

        for erow, arow in zip(expected_A, actual_A):
            ledger.verification_steps += len(erow)
            if len(erow) != len(arow) or any(abs(float(e) - float(a)) > 1e-9 for e, a in zip(erow, arow)):
                return VerificationResult(False, "coefficient matrix differs from semantic contract")
        if any(abs(float(e) - float(a)) > 1e-9 for e, a in zip(expected_b, actual_b)):
            return VerificationResult(False, "right-hand side differs from semantic contract")
        return VerificationResult(True, "linear-system representation faithful to contract")
