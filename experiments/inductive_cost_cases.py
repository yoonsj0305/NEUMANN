"""Constructed opened-development coupled recurrences, not fresh benchmarks."""
import random

from neumann1.inductive_perspective import HORIZON, projections, split, substitute
from neumann1.polynomial_translation_native import combination, join, polynomial, from_forms
from neumann1.representation_program import Builder, polynomial_forms


def make_case(degree, shear, seed):
    parameters, state = ["a", "b", "c", "k"], ["s", "t", "w"]
    inputs, latent_inputs = parameters + state, parameters + ["__z0", "__z1"]
    v = dict(zip(inputs, split(projections(inputs, inputs))))
    u = combination(inputs, [v["s"], v["t"]], [1, -shear])
    rng = random.Random(seed)
    coefficients = {j: rng.choice([-2, -1, 1, 2]) for j in range(1, degree + 1)}
    primitive_in_s = polynomial(inputs, "s", coefficients)
    replacement = {**v, "s": u}
    Pu = substitute(primitive_in_s, replacement, inputs)
    shifted = combination(inputs, [u, v["k"]], [1, 1])
    shifted_P = substitute(primitive_in_s, {**v, "s": shifted}, inputs)
    q = combination(inputs, [shifted_P, Pu], [1, -1])
    first = combination(inputs, [v["s"], v["k"], q], [1, 1, shear])
    second = combination(inputs, [v["t"], q], [1, 1])
    b = Builder(inputs)
    third = b.finish([b.add(b.mul(b.const(3), b.input("w")), b.const(1))])
    transition = from_forms(inputs, polynomial_forms(join(inputs, [first, second, third])))
    problem = {"semantics": "exact_integer_recurrence", "parameters": parameters, "state": state,
               "initial": projections(parameters, ["a", "b", "c"]), "transition": transition,
               "goal": projections(inputs, ["t"])}
    invariant = combination(inputs, [v["t"], Pu], [1, -1])
    encoding = join(inputs, [u, invariant])
    pv = dict(zip(parameters, split(projections(parameters, parameters))))
    initial = substitute(encoding, {**pv, **dict(zip(state, split(problem["initial"])))}, parameters)
    cv_inputs = parameters + [HORIZON]
    cv = dict(zip(cv_inputs, split(projections(cv_inputs, cv_inputs))))
    initial_closed = [substitute(p, {name: cv[name] for name in parameters}, cv_inputs) for p in split(initial)]
    b = Builder(cv_inputs)
    kn = b.finish([b.mul(b.input("k"), b.input(HORIZON))])
    closed = join(cv_inputs, [combination(cv_inputs, [initial_closed[0], kn], [1, 1]), initial_closed[1]])
    lv = dict(zip(latent_inputs, split(projections(latent_inputs, latent_inputs))))
    proposal = {"encoding": encoding, "initial": initial,
                "transition": join(latent_inputs, [combination(latent_inputs, [lv["__z0"], lv["k"]], [1, 1]), lv["__z1"]]),
                "closed_form": closed,
                "decode": combination(latent_inputs, [lv["__z1"], polynomial(latent_inputs, "__z0", coefficients)], [1, 1])}
    requests, expected = [], []
    horizons = [100000] + [999, 9999, 19999]*5
    for i, n in enumerate(horizons):
        params = [rng.randint(-3, 3), rng.randint(-3, 3), rng.randint(-3, 3), rng.choice([-2, -1, 1, 2])]
        a, b0, c, k = params
        x0 = a-shear*b0
        answer = b0 + sum(coefficient * ((x0+k*n)**j - x0**j) for j, coefficient in coefficients.items())
        requests.append({"parameters": params, "steps": n})
        expected.append([answer])
    return problem, proposal, requests, expected, {"degree": degree, "shear": shear, "seed": seed, "coefficients": coefficients}
