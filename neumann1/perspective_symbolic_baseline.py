"""Reusable bounded egglog comparator for exact-integer representation programs.

This is G1's prospective SYMBOLIC baseline infrastructure, not a learned NEUMANN
policy, G1 admission or proof of a new architecture. Never apply ring rewrites
to floating-point programs without an additional semantics contract.
"""
from __future__ import annotations

from importlib.metadata import version
from time import perf_counter

from egglog import (EGraph, Expr, StringLike, eq, get_callable_args,
                    get_callable_fn, get_literal_value, i64Like, rewrite, ruleset, vars_)


class IntegerExpr(Expr):
    def __init__(self, value: i64Like) -> None: ...

    @classmethod
    def var(cls, name: StringLike) -> IntegerExpr: ...

    def __add__(self, other: IntegerExpr) -> IntegerExpr: ...

    def __mul__(self, other: IntegerExpr) -> IntegerExpr: ...


a, b, c = vars_("a b c", IntegerExpr)
INTEGER_RING = ruleset(
    rewrite(a + b).to(b + a),
    rewrite(a * b).to(b * a),
    rewrite((a + b) + c).to(a + (b + c)),
    rewrite((a * b) * c).to(a * (b * c)),
    rewrite(a * (b + c)).to(a * b + a * c),
    rewrite(a * b + a * c).to(a * (b + c)),
    rewrite(a + IntegerExpr(0)).to(a),
    rewrite(a * IntegerExpr(1)).to(a),
    rewrite(a * IntegerExpr(0)).to(IntegerExpr(0)),
)


def validate_ast(ast, *, semantics="exact_integer", max_nodes=128):
    if semantics != "exact_integer":
        raise ValueError("Only exact-integer semantics admits these ring rules")
    count = 0

    def visit(node):
        nonlocal count
        count += 1
        if count > max_nodes or not isinstance(node, list) or len(node) < 2:
            raise ValueError("Malformed or oversized representation AST")
        if node[0] == "var" and len(node) == 2 and isinstance(node[1], str) and node[1].isidentifier():
            return
        if node[0] == "int" and len(node) == 2 and type(node[1]) is int and -(2**63) <= node[1] < 2**63:
            return
        if node[0] in ("add", "mul") and len(node) == 3:
            visit(node[1]); visit(node[2])
            return
        raise ValueError("Unregistered public expression constructor")

    visit(ast)
    return count


def to_expr(ast):
    if ast[0] == "var":
        return IntegerExpr.var(ast[1])
    if ast[0] == "int":
        return IntegerExpr(ast[1])
    left, right = to_expr(ast[1]), to_expr(ast[2])
    return left + right if ast[0] == "add" else left * right


def to_ast(expr):
    fn, args = get_callable_fn(expr), get_callable_args(expr)
    if fn == IntegerExpr:
        return ["int", int(get_literal_value(args[0]))]
    if fn == IntegerExpr.var:
        return ["var", str(get_literal_value(args[0]))]
    if fn == IntegerExpr.__add__:
        return ["add", to_ast(args[0]), to_ast(args[1])]
    if fn == IntegerExpr.__mul__:
        return ["mul", to_ast(args[0]), to_ast(args[1])]
    raise ValueError("Extracted unsupported representation")


def optimize_representation(ast, *, semantics="exact_integer", iterations=4):
    if version("egglog") != "14.0.0" or type(iterations) is not int or not 1 <= iterations <= 8:
        raise ValueError("Pinned symbolic backend and bounded iteration contract required")
    begin = perf_counter()
    original_nodes = validate_ast(ast, semantics=semantics)
    graph = EGraph()
    original = to_expr(ast)
    graph.register(original)
    _, original_tree_cost = graph.extract(original, include_cost=True)
    graph.run(iterations, ruleset=INTEGER_RING)
    result, cost = graph.extract(original, include_cost=True)
    graph.check(eq(original).to(result))
    representation = to_ast(result)
    validate_ast(representation, semantics=semantics)
    return {"representation": representation, "original_nodes": original_nodes,
            "original_tree_cost": original_tree_cost,
            "extracted_tree_cost": cost, "equivalence": "EGGLOG_EQUALITY_UNDER_DECLARED_INTEGER_RING_AXIOMS",
            "iterations": iterations, "complete_seconds": perf_counter() - begin,
            "learned": False, "oracle_used": False, "semantics": semantics,
            "global_optimum_proven": False, "downstream_execution_cost_measured": False}


def evaluate_integer(ast, bindings):
    validate_ast(ast)

    def visit(node):
        if node[0] == "int":
            return node[1]
        if node[0] == "var":
            value = bindings[node[1]]
            if type(value) is not int:
                raise ValueError("Exact integer binding required")
            return value
        left, right = visit(node[1]), visit(node[2])
        return left + right if node[0] == "add" else left * right

    return visit(ast)
