"""Reachability-guarded extension of the frozen universal recurrence checker.

One polynomial invariant, seven exact identities, mathematical integers only.
Witness hashes identify claims; only recomputing the identities authorizes use.
Historical universal code and its registered source hashes remain unchanged.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from time import perf_counter

from neumann1.inductive_perspective import (constants, projections, split,
    substitute, proof_obligations, validate_proposal)
from neumann1.representation_program import Builder, ProgramError, validate, polynomial_forms, compile_program

CERTIFICATE_TYPE = "REACHABILITY_GUARDED_SINGLE_POLYNOMIAL_V1"
SCOPE = "original ordered goal from the bound initial state; all integer parameters and nonnegative integer horizons"


def snapshot(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(snapshot(value).encode("utf-8")).hexdigest()


def _pairwise(left, right, operation):
    if left["inputs"] != right["inputs"] or len(left["outputs"]) != len(right["outputs"]):
        raise ProgramError("Ordered polynomial vector interfaces must match")
    count = len(left["outputs"])
    names = [f"__L{i}" for i in range(count)] + [f"__R{i}" for i in range(count)]
    builder = Builder(names)
    outputs = []
    for i in range(count):
        a, b = builder.input(names[i]), builder.input(names[count+i])
        outputs.append(builder.mul(a, b) if operation == "mul" else builder.add(a, builder.mul(builder.const(-1), b)))
    return substitute(builder.finish(outputs), dict(zip(names, split(left) + split(right))), left["inputs"])


def difference(left, right):
    return _pairwise(left, right, "sub")


def _times_invariant(multiplier, invariant):
    broadcast = {**invariant, "outputs": invariant["outputs"] * len(multiplier["outputs"])}
    return _pairwise(multiplier, broadcast, "mul")


def bind_guarded_witness(problem, proposal, invariant, *, preservation, transition, goal):
    """Bind supplied proof programs, without claiming or checking their truth."""
    return json.loads(snapshot({"certificate_type": CERTIFICATE_TYPE,
        "problem_sha256": digest(problem), "initial_sha256": digest(problem["initial"]),
        "proposal_sha256": digest(proposal), "invariant": invariant,
        "multipliers": {"preservation": preservation, "transition": transition, "goal": goal}}))


def guarded_obligations(problem, proposal, witness):
    latent = validate_proposal(problem, proposal)
    required = {"certificate_type", "problem_sha256", "initial_sha256", "proposal_sha256", "invariant", "multipliers"}
    if not isinstance(witness, dict) or set(witness) != required or witness["certificate_type"] != CERTIFICATE_TYPE:
        raise ProgramError("Separate guarded witness schema required; accepted labels are not authority")
    if (witness["problem_sha256"] != digest(problem) or witness["initial_sha256"] != digest(problem["initial"])
            or witness["proposal_sha256"] != digest(proposal)):
        raise ProgramError("Guarded witness binding hash mismatch")
    params, state = problem["parameters"], problem["state"]
    space = params + state
    invariant, multipliers = witness["invariant"], witness["multipliers"]
    validate(invariant)
    if invariant["inputs"] != space or len(invariant["outputs"]) != 1:
        raise ProgramError("One scalar invariant in the original state space required")
    if not isinstance(multipliers, dict) or set(multipliers) != {"preservation", "transition", "goal"}:
        raise ProgramError("Exactly three ordered multiplier programs required")
    for key, count in [("preservation", 1), ("transition", len(latent)), ("goal", len(problem["goal"]["outputs"]))]:
        validate(multipliers[key])
        if multipliers[key]["inputs"] != space or len(multipliers[key]["outputs"]) != count:
            raise ProgramError("Proof multiplier dimension or input mismatch")
    pv = dict(zip(params, split(projections(params, params))))
    ov = dict(zip(space, split(projections(space, space))))
    initial_guard = substitute(invariant, {**pv, **dict(zip(state, split(problem["initial"])))}, params)
    next_guard = substitute(invariant, {**{p: ov[p] for p in params}, **dict(zip(state, split(problem["transition"])))}, space)
    old = proof_obligations(problem, proposal)
    return [("INITIAL_INVARIANT", initial_guard, constants(params, [0])),
        ("INDUCTIVE_PRESERVATION", next_guard, _times_invariant(multipliers["preservation"], invariant)),
        old[0],
        ("GUARDED_TRANSITION", difference(old[1][1], old[1][2]), _times_invariant(multipliers["transition"], invariant)),
        ("GUARDED_GOAL", difference(old[2][1], old[2][2]), _times_invariant(multipliers["goal"], invariant)),
        old[3], old[4]]


def check_guarded_perspective(problem, proposal, witness, *, max_terms=8192, max_product_work=2_000_000):
    begin, checked = perf_counter(), []
    try:
        if type(max_terms) is not int or max_terms < 1 or type(max_product_work) is not int or max_product_work < 1:
            raise ProgramError("Positive exact proof budgets required")
        obligations = guarded_obligations(problem, proposal, witness)
        if not polynomial_forms(witness["invariant"], max_terms, max_product_work)[0]:
            raise ProgramError("Nonzero polynomial invariant required")
        for name, lhs, rhs in obligations:
            left, right = [polynomial_forms(p, max_terms, max_product_work) for p in (lhs, rhs)]
            valid = left == right
            checked.append({"obligation": name, "accepted": valid, "lhs_sha256": digest(lhs), "rhs_sha256": digest(rhs),
                "left_terms": sum(map(len, left)), "right_terms": sum(map(len, right))})
            if not valid:
                return {"status": "REJECTED", "accepted": False, "certificate_type": CERTIFICATE_TYPE,
                    "failed_obligation": name, "obligations": checked, "verification_seconds": perf_counter()-begin}
        return {"status": "CERTIFIED", "accepted": True, "certificate_type": CERTIFICATE_TYPE,
            "authority": "SEVEN_EXACT_POLYNOMIAL_IDENTITIES_PLUS_REACHABILITY_INDUCTION", "scope": SCOPE,
            "problem_sha256": digest(problem), "initial_sha256": digest(problem["initial"]),
            "proposal_sha256": digest(proposal), "witness_sha256": digest(witness), "witness": witness,
            "parameter_domain": {p: "mathematical_integer" for p in problem["parameters"]},
            "horizon_domain": "nonnegative_mathematical_integer", "goal_output_order": problem["goal"]["outputs"],
            "original_state_dimension": len(problem["state"]), "latent_state_dimension": len(proposal["encoding"]["outputs"]),
            "obligations": checked, "verification_seconds": perf_counter()-begin}
    except (ProgramError, TypeError, KeyError, ValueError, RecursionError) as exc:
        return {"status": "NOT_VERIFIED", "accepted": False, "certificate_type": CERTIFICATE_TYPE,
            "obligations": checked, "error": str(exc), "verification_seconds": perf_counter()-begin}


@dataclass(frozen=True)
class CertifiedGuardedAcceleration:
    parameter_count: int
    _closed_function: object
    _decode_function: object
    _certificate_json: str

    @property
    def certificate(self):
        return json.loads(self._certificate_json)

    def run(self, parameters, steps):
        if (type(steps) is not int or steps < 0 or not isinstance(parameters, (tuple, list))
                or len(parameters) != self.parameter_count or any(type(p) is not int for p in parameters)):
            raise ProgramError("Exact parameters and nonnegative integer horizon required")
        parameters = tuple(parameters)
        return self._decode_function(parameters + self._closed_function(parameters + (steps,)))


def compile_guarded_acceleration(problem, proposal, witness, **budgets):
    # Detach caller payloads before checking/compiling; certificate property returns a copy.
    problem, proposal, witness = json.loads(snapshot([problem, proposal, witness]))
    certificate = check_guarded_perspective(problem, proposal, witness, **budgets)
    if not certificate["accepted"]:
        raise ProgramError("Uncertified guarded representation must not execute: " + certificate["status"])
    return CertifiedGuardedAcceleration(len(problem["parameters"]), compile_program(proposal["closed_form"]).function,
        compile_program(proposal["decode"]).function, snapshot(certificate))
