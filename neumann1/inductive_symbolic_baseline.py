"""Public-only, bounded native synthesis using pinned SymPy 1.14.0.

Dependency closure, polynomial interpolation and invariant nullspaces are known
symbolic methods. They are strong comparison infrastructure, not learned LPS.
Interpolation proposes; the separate universal checker decides correctness.
"""
from itertools import product
from math import gcd, lcm
from time import perf_counter

from neumann1.representation_program import Builder, ProgramError, polynomial_forms, reachable_nodes
from neumann1.inductive_perspective import (HORIZON, check_perspective, projections,
    split, substitute, validate_problem)


def _sympy():
    import sympy as sp
    if sp.__version__ != "1.14.0":
        raise ProgramError("Pinned SymPy 1.14.0 required")
    return sp


def expressions(program):
    sp = _sympy()
    variables = [sp.Symbol(v) for v in program["inputs"]]
    return [sum((sp.Integer(c) * sp.prod(v ** e for v, e in zip(variables, exponents))
                 for exponents, c in form.items()), sp.Integer(0)) for form in polynomial_forms(program)]


def from_expressions(inputs, values):
    sp = _sympy()
    builder = Builder(inputs)
    memo = {sp.Symbol(v): builder.input(v) for v in inputs}

    def convert(value):
        if value in memo:
            return memo[value]
        if value.is_Integer:
            result = builder.const(int(value))
        elif value.is_Add or value.is_Mul:
            result = builder.combine("add" if value.is_Add else "mul", [convert(a) for a in value.args])
        elif value.is_Pow and value.exp.is_Integer and 0 <= int(value.exp) <= 16:
            result = builder.combine("mul", [convert(value.base)] * int(value.exp))
        else:
            raise ProgramError("Native result outside integer coefficient polynomial grammar")
        memo[value] = result
        return result
    return builder.finish([convert(value) for value in values])


def state_closure(problem):
    validate_problem(problem)
    state = set(problem["state"])

    def used(program):
        return {program["nodes"][i][1] for i in reachable_nodes(program) if program["nodes"][i][0] == "input"} & state
    needed = used(problem["goal"])
    previous = None
    while needed != previous:
        previous = needed.copy()
        for name, output in zip(problem["state"], problem["transition"]["outputs"]):
            if name in needed:
                needed |= used({**problem["transition"], "outputs": [output]})
    return [v for v in problem["state"] if v in needed]


def propose_polynomial_acceleration(problem, *, degree=3):
    begin = perf_counter()
    try:
        sp = _sympy()
        validate_problem(problem)
        if type(degree) is not int or not 1 <= degree <= 3:
            raise ProgramError("Registered native polynomial proposal budget 1..3")
        parameters, state = problem["parameters"], problem["state"]
        retained = state_closure(problem) or [state[0]]
        positions = [state.index(v) for v in retained]
        latent = [f"__z{i}" for i in range(len(retained))]
        initial = {**problem["initial"], "outputs": [problem["initial"]["outputs"][i] for i in positions]}
        trans = {**problem["transition"], "outputs": [problem["transition"]["outputs"][i] for i in positions]}
        symbols = [sp.Symbol(v) for v in retained]
        latent_symbols = [sp.Symbol(v) for v in latent]
        mapping = dict(zip(symbols, latent_symbols))
        transition_exprs = expressions(trans)
        initial_exprs = expressions(initial)
        samples = [initial_exprs]
        current = initial_exprs
        for _ in range(degree):
            current = [sp.expand(e.subs(dict(zip(symbols, current)), simultaneous=True)) for e in transition_exprs]
            samples.append(current)
        horizon = sp.Symbol(HORIZON)
        closed = [sp.expand(sp.interpolate([(n, samples[n][i]) for n in range(degree + 1)], horizon)) for i in range(len(retained))]
        proposal = {"encoding": projections(parameters + state, retained), "initial": initial,
                    "transition": from_expressions(parameters + latent, [e.xreplace(mapping) for e in transition_exprs]),
                    "closed_form": from_expressions(parameters + [HORIZON], closed),
                    "decode": from_expressions(parameters + latent, [e.xreplace(mapping) for e in expressions(problem["goal"])])}
        certificate = check_perspective(problem, proposal)
        return {"status": "CERTIFIED_NATIVE_PROPOSAL" if certificate["accepted"] else "ABSTAINED_UNPROVEN_INTERPOLATION",
                "proposal": proposal, "certificate": certificate, "retained_state": retained,
                "learned": False, "oracle_used": False, "discovery_seconds": perf_counter() - begin}
    except (ProgramError, ValueError, TypeError, KeyError) as exc:
        return {"status": "ABSTAINED_OUTSIDE_NATIVE_GRAMMAR", "error": str(exc), "learned": False,
                "oracle_used": False, "discovery_seconds": perf_counter() - begin}


def discover_polynomial_invariants(problem, *, degree=2, max_features=128):
    """Solve p(F(s))-p(s)=0 over a bounded state-monomial basis exactly."""
    begin = perf_counter()
    sp = _sympy()
    validate_problem(problem)
    if type(degree) is not int or not 1 <= degree <= 3:
        raise ProgramError("Bounded native invariant degree required")
    state, parameters = problem["state"], problem["parameters"]
    exponents = [e for e in product(range(degree + 1), repeat=len(state)) if 1 <= sum(e) <= degree]
    if len(exponents) > max_features:
        raise ProgramError("Invariant feature budget exceeded")
    inputs = parameters + state
    variables = dict(zip(inputs, split(projections(inputs, inputs))))
    transition = dict(zip(state, split(problem["transition"])))
    monomials, residuals = [], []
    for powers in exponents:
        builder = Builder(inputs)
        monomial = builder.finish([builder.combine("mul", [builder.input(v) for v, e in zip(state, powers) for _ in range(e)])])
        advanced = substitute(monomial, {**{p: variables[p] for p in parameters}, **transition}, inputs)
        before, after = polynomial_forms(monomial)[0], polynomial_forms(advanced)[0]
        residuals.append({e: after.get(e, 0) - before.get(e, 0) for e in set(before) | set(after) if after.get(e, 0) != before.get(e, 0)})
        monomials.append(monomial)
    keys = sorted({e for r in residuals for e in r})
    matrix = sp.Matrix([[r.get(e, 0) for r in residuals] for e in keys]) if keys else sp.zeros(0, len(monomials))
    invariants = []
    for vector in matrix.nullspace():
        multiplier = lcm(*(int(c.q) for c in vector))
        integer = [int(c * multiplier) for c in vector]
        divisor = gcd(*integer)
        integer = [c // divisor for c in integer]
        value = sum((c * expressions(m)[0] for c, m in zip(integer, monomials)), sp.Integer(0))
        candidate = from_expressions(inputs, [sp.expand(value)])
        advanced = substitute(candidate, {**{p: variables[p] for p in parameters}, **transition}, inputs)
        assert polynomial_forms(candidate) == polynomial_forms(advanced)
        invariants.append({"program": candidate, "coefficients": integer, "universally_checked": True})
    return {"invariants": invariants, "degree": degree, "monomial_features": len(monomials),
            "learned": False, "oracle_used": False, "discovery_seconds": perf_counter() - begin,
            "goal_sufficiency_established": False}
