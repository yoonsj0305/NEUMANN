"""Exact public native reduction for a bounded coupled polynomial translation.

Known linear-combination cancellation and polynomial antidifferences. A strong
comparison algorithm, not neural inference or NEUMANN novelty. No SymPy import
is needed, so a heavyweight CAS startup is not treated as unavoidable baseline
cost. Every generated proposal still needs the common induction certificate.
"""
from neumann1.representation_program import Builder, ProgramError, polynomial_forms, validate
from neumann1.inductive_perspective import (HORIZON, projections, split, substitute, validate_problem)


def emit(builder, program):
    validate(program)
    if program["inputs"] != builder.inputs:
        raise ProgramError("Common symbolic space required")
    values = []
    for node in program["nodes"]:
        values.append(builder.input(node[1]) if node[0] == "input" else
                      builder.const(node[1]) if node[0] == "const" else
                      builder.node(node[0], values[node[1]], values[node[2]]))
    return [values[o] for o in program["outputs"]]


def combination(inputs, programs, coefficients):
    b = Builder(inputs)
    terms = [b.mul(b.const(c), emit(b, p)[0]) for p, c in zip(programs, coefficients)]
    return b.finish([b.combine("add", terms)])


def join(inputs, programs):
    b = Builder(inputs)
    return b.finish([emit(b, p)[0] for p in programs])


def polynomial(inputs, variable, coefficients):
    b = Builder(inputs)
    x = b.input(variable)
    return b.finish([b.combine("add", [b.mul(b.const(c), b.combine("mul", [x]*degree)) for degree, c in coefficients.items()])])


def from_forms(inputs, forms):
    b = Builder(inputs)
    outputs = []
    for form in forms:
        outputs.append(b.combine("add", [b.mul(b.const(c), b.combine("mul", [b.input(v) for v, degree in zip(inputs, e) for _ in range(degree)]))
                                         for e, c in sorted(form.items())]))
    return b.finish(outputs)


def propose(problem, *, max_degree=8):
    """Recover u=s-m*t and P(u) from public transition coefficients only."""
    validate_problem(problem)
    parameters, state = problem["parameters"], problem["state"]
    if "k" not in parameters or len(state) != 3 or not 2 <= max_degree <= 8:
        raise ProgramError("Outside declared native translation grammar")
    inputs = parameters + state
    s, t, w = state
    variables = dict(zip(inputs, split(projections(inputs, inputs))))
    original_transitions = split(problem["transition"])
    deltas = [combination(inputs, [p, variables[name]], [1, -1]) for p, name in zip(original_transitions[:2], state[:2])]
    forms = [polynomial_forms(p)[0] for p in deltas]
    candidates = [e for e in set(forms[0]) | set(forms[1]) if sum(e[len(parameters):]) >= 1 and sum(e) >= 2 and forms[1].get(e, 0)]
    if not candidates:
        raise ProgramError("No nonlinear cancellation direction")
    e = sorted(candidates)[-1]
    numerator, denominator = forms[0].get(e, 0), forms[1][e]
    if numerator % denominator:
        raise ProgramError("Nonintegral native shear outside grammar")
    shear = numerator // denominator
    u = combination(inputs, [variables[s], variables[t]], [1, -shear])
    shifted_u = combination(inputs, deltas, [1, -shear])
    if polynomial_forms(shifted_u) != polynomial_forms(variables["k"]):
        raise ProgramError("Cancelled public coordinate is not the declared translation")
    latent = ["__z0", "__z1"]
    latent_inputs = parameters + latent
    lv = dict(zip(latent_inputs, split(projections(latent_inputs, latent_inputs))))
    reconstructed_s = combination(latent_inputs, [lv["__z0"], lv["__z1"]], [1, shear])
    replacements = {**{p: lv[p] for p in parameters}, s: reconstructed_s, t: lv["__z1"], w: projections(latent_inputs, ["__z1"])}
    q = polynomial_forms(substitute(deltas[1], replacements, latent_inputs))[0]
    k_position = parameters.index("k")
    coefficients = {}
    for exponent, coefficient in q.items():
        degree = exponent[k_position]
        if degree >= 1 and sum(exponent) == degree:
            coefficients[degree] = coefficient
    if not coefficients or max(coefficients) > max_degree:
        raise ProgramError("Native primitive polynomial degree outside budget")
    # Build P of the recovered coordinate by structural substitution.
    primitive_latent = polynomial(latent_inputs, "__z0", coefficients)
    primitive_source = substitute(primitive_latent, {**{p: variables[p] for p in parameters}, "__z0": u, "__z1": variables[t]}, inputs)
    invariant = combination(inputs, [variables[t], primitive_source], [1, -1])
    encoding = join(inputs, [u, invariant])
    pv = dict(zip(parameters, split(projections(parameters, parameters))))
    initial = substitute(encoding, {**pv, **dict(zip(state, split(problem["initial"])))}, parameters)
    cv_inputs = parameters + [HORIZON]
    cv = dict(zip(cv_inputs, split(projections(cv_inputs, cv_inputs))))
    initial_in_closed = [substitute(p, {name: cv[name] for name in parameters}, cv_inputs) for p in split(initial)]
    b = Builder(cv_inputs)
    product = b.finish([b.mul(b.input("k"), b.input(HORIZON))])
    closed = join(cv_inputs, [combination(cv_inputs, [initial_in_closed[0], product], [1, 1]), initial_in_closed[1]])
    physical_t = combination(latent_inputs, [lv["__z1"], primitive_latent], [1, 1])
    physical_s = combination(latent_inputs, [lv["__z0"], physical_t], [1, shear])
    # Irrelevant third coordinate is intentionally unavailable to the decoder.
    # If the original goal needs it, the universal goal obligation rejects this.
    decoder = substitute(problem["goal"], {**{p: lv[p] for p in parameters}, s: physical_s, t: physical_t, w: lv["__z1"]}, latent_inputs)
    transition = join(latent_inputs, [combination(latent_inputs, [lv["__z0"], lv["k"]], [1, 1]), lv["__z1"]])
    return {"encoding": encoding, "initial": initial, "transition": transition, "closed_form": closed, "decode": decoder}
