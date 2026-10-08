"""Generated sufficient coordinates and loop elimination with exact certificates.

Known induction and integer polynomial identity are proof infrastructure, not a
learned NEUMANN model. No sampled agreement, tool confidence or hidden solution
can authorize elimination. All proposers receive this same API.
"""
from dataclasses import dataclass
from time import perf_counter

from neumann1.representation_program import (Builder, ProgramError, validate,
                                            polynomial_forms, compile_program)

HORIZON = "__steps"


def projections(inputs, names):
    builder = Builder(inputs)
    return builder.finish([builder.input(name) for name in names])


def constants(inputs, values):
    builder = Builder(inputs)
    return builder.finish([builder.const(value) for value in values])


def split(program):
    validate(program)
    return [{**program, "outputs": [index]} for index in program["outputs"]]


def substitute(program, bindings, inputs):
    """Structural substitution of validated DAGs; never evaluate supplied text."""
    validate(program)
    if set(bindings) != set(program["inputs"]):
        raise ProgramError("Complete substitution interface required")
    builder = Builder(inputs)

    def emit(source, memo):
        result = []
        for i, node in enumerate(source["nodes"]):
            if node[0] == "input":
                target = memo[node[1]]
            elif node[0] == "const":
                target = builder.const(node[1])
            else:
                target = builder.node(node[0], result[node[1]], result[node[2]])
            result.append(target)
        return [result[o] for o in source["outputs"]]

    replacements = {}
    for name, replacement in bindings.items():
        validate(replacement)
        if replacement["inputs"] != inputs or len(replacement["outputs"]) != 1:
            raise ProgramError("Each replacement must be a scalar in the common space")
        replacements[name] = emit(replacement, {v: builder.input(v) for v in inputs})[0]
    return builder.finish(emit(program, replacements))


def _variables(inputs):
    return dict(zip(inputs, split(projections(inputs, inputs))))


def validate_problem(problem):
    if not isinstance(problem, dict) or set(problem) != {"semantics", "parameters", "state", "initial", "transition", "goal"}:
        raise ProgramError("Public recurrence schema only, without Oracle or supervision")
    if problem["semantics"] != "exact_integer_recurrence":
        raise ProgramError("Unbounded integer, unconditional deterministic recurrence required")
    parameters, state = problem["parameters"], problem["state"]
    if not isinstance(parameters, list) or not 1 <= len(parameters) <= 16 or not isinstance(state, list) or not 1 <= len(state) <= 8:
        raise ProgramError("Declared bounded parameter/state interface required")
    names = parameters + state
    if any(not isinstance(v, str) or not v.isidentifier() or v.startswith("__") for v in names) or len(set(names)) != len(names):
        raise ProgramError("Disjoint nonreserved coordinate names required")
    for key, inputs, count in [("initial", parameters, len(state)), ("transition", names, len(state)), ("goal", names, None)]:
        validate(problem[key])
        if problem[key]["inputs"] != inputs or (count is not None and len(problem[key]["outputs"]) != count):
            raise ProgramError("Original ordered state and goal interfaces required")
    return problem


def validate_proposal(problem, proposal):
    validate_problem(problem)
    if not isinstance(proposal, dict) or set(proposal) != {"encoding", "initial", "transition", "closed_form", "decode"}:
        raise ProgramError("Generated representation programs required, without proof labels")
    parameters, state = problem["parameters"], problem["state"]
    validate(proposal["encoding"])
    dimension = len(proposal["encoding"]["outputs"])
    latent = [f"__z{i}" for i in range(dimension)]
    for key, inputs, count in [("encoding", parameters + state, dimension),
                               ("initial", parameters, dimension),
                               ("transition", parameters + latent, dimension),
                               ("closed_form", parameters + [HORIZON], dimension),
                               ("decode", parameters + latent, len(problem["goal"]["outputs"]))]:
        validate(proposal[key])
        if proposal[key]["inputs"] != inputs or len(proposal[key]["outputs"]) != count:
            raise ProgramError("Generated ordered coordinate/goal interface mismatch")
    return latent


def proof_obligations(problem, proposal):
    latent = validate_proposal(problem, proposal)
    parameters, state = problem["parameters"], problem["state"]
    original_space, closed_space = parameters + state, parameters + [HORIZON]
    pv, ov, cv = _variables(parameters), _variables(original_space), _variables(closed_space)
    encoded_initial = substitute(proposal["encoding"], {**pv, **dict(zip(state, split(problem["initial"])))}, parameters)
    encoded_next = substitute(proposal["encoding"], {**{p: ov[p] for p in parameters}, **dict(zip(state, split(problem["transition"])))}, original_space)
    encoded = dict(zip(latent, split(proposal["encoding"])))
    latent_next = substitute(proposal["transition"], {**{p: ov[p] for p in parameters}, **encoded}, original_space)
    decoded = substitute(proposal["decode"], {**{p: ov[p] for p in parameters}, **encoded}, original_space)
    closed_zero = substitute(proposal["closed_form"], {**pv, HORIZON: constants(parameters, [0])}, parameters)
    builder = Builder(closed_space)
    next_horizon = builder.finish([builder.add(builder.input(HORIZON), builder.const(1))])
    closed_next = substitute(proposal["closed_form"], {**{p: cv[p] for p in parameters}, HORIZON: next_horizon}, closed_space)
    closed_transition = substitute(proposal["transition"], {**{p: cv[p] for p in parameters}, **dict(zip(latent, split(proposal["closed_form"])))}, closed_space)
    return [("ENCODE_INITIAL", encoded_initial, proposal["initial"]),
            ("TRANSITION_COMMUTES", encoded_next, latent_next),
            ("ORIGINAL_GOAL_SUFFICIENT", problem["goal"], decoded),
            ("CLOSED_BASE", closed_zero, proposal["initial"]),
            ("CLOSED_STEP", closed_next, closed_transition)]


def check_perspective(problem, proposal, *, max_terms=8192, max_product_work=2_000_000):
    begin = perf_counter()
    checked = []
    try:
        for name, lhs, rhs in proof_obligations(problem, proposal):
            left = polynomial_forms(lhs, max_terms=max_terms, max_product_work=max_product_work)
            right = polynomial_forms(rhs, max_terms=max_terms, max_product_work=max_product_work)
            valid = left == right
            checked.append({"obligation": name, "accepted": valid, "left_terms": sum(map(len, left)), "right_terms": sum(map(len, right))})
            if not valid:
                return {"status": "REJECTED", "accepted": False, "obligations": checked,
                        "failed_obligation": name, "verification_seconds": perf_counter() - begin}
        return {"status": "CERTIFIED", "accepted": True, "obligations": checked,
                "scope": "original ordered goal for all integer parameters and all nonnegative integer horizons",
                "authority": "FIVE_EXACT_POLYNOMIAL_IDENTITIES_PLUS_INDUCTION",
                "verification_seconds": perf_counter() - begin}
    except (ProgramError, TypeError, KeyError, ValueError, RecursionError) as exc:
        return {"status": "NOT_VERIFIED", "accepted": False, "obligations": checked,
                "error": str(exc), "verification_seconds": perf_counter() - begin}


@dataclass(frozen=True)
class CertifiedAcceleration:
    parameter_count: int
    closed: object
    decode: object
    certificate: dict

    def run(self, parameters, steps):
        if type(steps) is not int or steps < 0 or len(parameters) != self.parameter_count or any(type(p) is not int for p in parameters):
            raise ProgramError("Exact parameters and nonnegative integer horizon required")
        latents = self.closed.run([tuple(parameters) + (steps,)])[0]
        return self.decode.run([tuple(parameters) + latents])[0]


def compile_acceleration(problem, proposal):
    certificate = check_perspective(problem, proposal)
    if not certificate["accepted"]:
        raise ProgramError("Uncertified representation must not eliminate execution")
    return CertifiedAcceleration(len(problem["parameters"]), compile_program(proposal["closed_form"]), compile_program(proposal["decode"]), certificate)


def original_execution(problem, parameters, steps, *, max_steps=10000):
    validate_problem(problem)
    if type(steps) is not int or not 0 <= steps <= max_steps:
        raise ProgramError("Bounded original engineering replay required")
    initial, transition, goal = [compile_program(problem[k]) for k in ["initial", "transition", "goal"]]
    current = initial.run([tuple(parameters)])[0]
    for _ in range(steps):
        current = transition.run([tuple(parameters) + current])[0]
    return goal.run([tuple(parameters) + current])[0]
