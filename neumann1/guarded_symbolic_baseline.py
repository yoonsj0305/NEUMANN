"""Bounded known symbolic bridge: conserved polynomial -> initial-bound guard.

Eliminate one state variable with unit linear coefficient, reuse native polynomial
acceleration, then require the independent guarded checker. No learned discovery.
"""
from time import perf_counter

from neumann1.inductive_perspective import projections, split, substitute, proof_obligations, validate_problem
from neumann1.inductive_symbolic_baseline import (_sympy, expressions, from_expressions,
    discover_polynomial_invariants, propose_polynomial_acceleration, state_closure)
from neumann1.guarded_perspective import (bind_guarded_witness, difference,
    check_guarded_perspective, compile_guarded_acceleration)
from neumann1.representation_program import ProgramError


def _lift(program, inputs):
    variables = dict(zip(inputs, split(projections(inputs, inputs))))
    return substitute(program, {name: variables[name] for name in program["inputs"]}, inputs)


def initial_bound_invariant(problem, invariant):
    """P(s,p) - P(I(p),p), not just a conserved expression without its level."""
    params, state = problem["parameters"], problem["state"]
    variables = dict(zip(params, split(projections(params, params))))
    initial_value = substitute(invariant, {**variables, **dict(zip(state, split(problem["initial"])))}, params)
    return difference(invariant, _lift(initial_value, params + state))


def propose_guarded_acceleration(problem, *, invariant_degree=2, closed_degree=3, max_features=128, max_candidates=16):
    begin, attempts = perf_counter(), []
    try:
        validate_problem(problem)
        if type(max_candidates) is not int or not 1 <= max_candidates <= 16:
            raise ProgramError("Bounded guarded candidate budget 1..16 required")
        sp = _sympy()
        params, state = problem["parameters"], problem["state"]
        inputs = params + state
        relevant = state_closure(problem)
        discovery = discover_polynomial_invariants(problem, degree=invariant_degree, max_features=max_features)
        for found in discovery["invariants"]:
            guard = initial_bound_invariant(problem, found["program"])
            h = expressions(guard)[0]
            for removed in relevant:
                if len(attempts) >= max_candidates:
                    raise ProgramError("Guarded candidate budget exceeded: UNKNOWN")
                symbol = sp.Symbol(removed)
                polynomial = sp.Poly(h, symbol)
                if polynomial.degree() != 1 or polynomial.coeff_monomial(symbol) not in (sp.Integer(1), sp.Integer(-1)):
                    attempts.append({"removed": removed, "status": "OUTSIDE_UNIT_LINEAR_ELIMINATION"})
                    continue
                replacement = sp.expand(-polynomial.coeff_monomial(1) / polynomial.coeff_monomial(symbol))
                kept = [s for s in state if s != removed]
                if not kept:
                    attempts.append({"removed": removed, "status": "ZERO_DIMENSION_OUTSIDE_EXISTING_IR"})
                    continue
                mapping = {symbol: replacement}
                reduced = {"semantics": problem["semantics"], "parameters": params, "state": kept,
                    "initial": {**problem["initial"], "outputs": [problem["initial"]["outputs"][state.index(s)] for s in kept]},
                    "transition": from_expressions(params + kept, [sp.expand(e.xreplace(mapping)) for s, e in zip(state, expressions(problem["transition"])) if s in kept]),
                    "goal": from_expressions(params + kept, [sp.expand(e.xreplace(mapping)) for e in expressions(problem["goal"])])}
                native = propose_polynomial_acceleration(reduced, degree=closed_degree)
                if not native.get("certificate", {}).get("accepted"):
                    attempts.append({"removed": removed, "status": native["status"]})
                    continue
                proposal = {**native["proposal"], "encoding": _lift(native["proposal"]["encoding"], inputs)}
                if len(proposal["encoding"]["outputs"]) >= len(relevant):
                    attempts.append({"removed": removed, "status": "NO_ADDITIONAL_STATE_ELIMINATION"})
                    continue
                variables = dict(zip(inputs, split(projections(inputs, inputs))))
                advanced = substitute(guard, {**{p: variables[p] for p in params}, **dict(zip(state, split(problem["transition"])))}, inputs)
                old = proof_obligations(problem, proposal)
                residuals = [advanced, difference(old[1][1], old[1][2]), difference(old[2][1], old[2][2])]
                generators = [symbol] + [sp.Symbol(v) for v in inputs if v != removed]
                multipliers = []
                for residual in residuals:
                    values = []
                    for value in expressions(residual):
                        quotient, remainder = sp.div(value, h, *generators, domain="ZZ")
                        if remainder != 0:
                            raise ProgramError("Residual not in the single-invariant polynomial ideal")
                        values.append(sp.expand(quotient))
                    multipliers.append(from_expressions(inputs, values))
                witness = bind_guarded_witness(problem, proposal, guard, preservation=multipliers[0], transition=multipliers[1], goal=multipliers[2])
                certificate = check_guarded_perspective(problem, proposal, witness)
                attempts.append({"removed": removed, "status": certificate["status"]})
                if certificate["accepted"]:
                    return {"status": "CERTIFIED_GUARDED_NATIVE_PROPOSAL", "proposal": proposal, "witness": witness,
                        "certificate": certificate, "removed_state": removed, "retained_state": native["retained_state"],
                        "invariant_discovery_goal_sufficiency": discovery["goal_sufficiency_established"],
                        "goal_sufficiency_established": True, "attempts": attempts, "learned": False, "oracle_used": False,
                        "discovery_seconds": perf_counter()-begin}
        return {"status": "ABSTAINED_NO_CERTIFIED_STATE_ELIMINATION", "attempts": attempts,
            "goal_sufficiency_established": False, "learned": False, "oracle_used": False, "discovery_seconds": perf_counter()-begin}
    except (ProgramError, ValueError, TypeError, KeyError, RecursionError) as exc:
        return {"status": "NOT_VERIFIED", "error": str(exc), "attempts": attempts,
            "goal_sufficiency_established": False, "learned": False, "oracle_used": False, "discovery_seconds": perf_counter()-begin}


def compile_discovered_guarded(problem, result):
    """Never trust result/certificate accepted labels; independently recheck programs."""
    if "proposal" not in result or "witness" not in result:
        raise ProgramError("No guarded programs to certify")
    return compile_guarded_acceleration(problem, result["proposal"], result["witness"])
