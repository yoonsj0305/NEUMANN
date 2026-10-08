import copy
from dataclasses import replace
import itertools
import json
from hashlib import sha256
from pathlib import Path
import statistics

import pytest
import sympy as sp

from experiments.inductive_fixture_cases import coordinate_fixture
from neumann1.inductive_perspective import (HORIZON, check_perspective, original_execution, projections, constants)
from neumann1.inductive_symbolic_baseline import from_expressions, discover_polynomial_invariants, propose_polynomial_acceleration
from neumann1.guarded_perspective import (SCOPE, bind_guarded_witness, guarded_obligations,
    check_guarded_perspective, compile_guarded_acceleration)
from neumann1.guarded_symbolic_baseline import propose_guarded_acceleration, compile_discovered_guarded
from neumann1.perspective import ProblemView, PerspectiveProposal, PreparedPerspective
from neumann1.representation_program import ProgramError


def fixture():
    original, _ = coordinate_fixture()
    a, b, k, x, y, z = sp.symbols("a b k x y __z0")
    n = sp.Symbol(HORIZON)
    params, space = original["parameters"], original["parameters"] + original["state"]
    proposal = {"encoding": projections(space, ["x"]), "initial": projections(params, ["a"]),
        "transition": from_expressions(params + ["__z0"], [z+k]),
        "closed_form": from_expressions(params + [HORIZON], [a+k*n]),
        "decode": from_expressions(params + ["__z0"], [z*z+b-a*a])}
    witness = bind_guarded_witness(original, proposal, from_expressions(space, [y-x*x-b+a*a]),
        preservation=constants(space, [1]), transition=constants(space, [0]), goal=constants(space, [1]))
    return original, proposal, witness


def independent_expression(program):
    # Independent DAG traversal and SymPy normalization, not polynomial_forms.
    values = []
    for node in program["nodes"]:
        if node[0] == "input":
            value = sp.Symbol(node[1])
        elif node[0] == "const":
            value = sp.Integer(node[1])
        else:
            a, b = (values[i] for i in node[1:])
            value = a+b if node[0] == "add" else a*b
        values.append(value)
    return [values[i] for i in program["outputs"]]


def independent_proof(problem, proposal, witness):
    """Rebuild all seven identities independently, including substitutions/order."""
    params, state = problem["parameters"], problem["state"]
    initial = dict(zip(map(sp.Symbol, state), independent_expression(problem["initial"])))
    step = dict(zip(map(sp.Symbol, state), independent_expression(problem["transition"])))
    encoding = independent_expression(proposal["encoding"])
    latent = dict(zip([sp.Symbol(f"__z{i}") for i in range(len(encoding))], encoding))
    h = independent_expression(witness["invariant"])[0]
    closed = independent_expression(proposal["closed_form"])
    closed_binding = dict(zip(latent, closed))
    n = sp.Symbol(HORIZON)
    rows = [[h.subs(initial, simultaneous=True)],
        [h.subs(step, simultaneous=True)-independent_expression(witness["multipliers"]["preservation"])[0]*h],
        [e.subs(initial, simultaneous=True)-z for e,z in zip(encoding, independent_expression(proposal["initial"]))],
        [e.subs(step, simultaneous=True)-t.subs(latent, simultaneous=True)-r*h for e,t,r in
            zip(encoding, independent_expression(proposal["transition"]), independent_expression(witness["multipliers"]["transition"]))],
        [g-d.subs(latent, simultaneous=True)-v*h for g,d,v in zip(independent_expression(problem["goal"]),
            independent_expression(proposal["decode"]), independent_expression(witness["multipliers"]["goal"]))],
        [r.subs(n,0)-z for r,z in zip(closed, independent_expression(proposal["initial"]))],
        [r.subs(n,n+1)-t.subs(closed_binding, simultaneous=True) for r,t in zip(closed, independent_expression(proposal["transition"]))]]
    return [all(sp.expand(e) == 0 for e in row) for row in rows]


def test_same_proposal_rejected_universally_and_accepted_only_from_bound_initial_state():
    original, proposal, witness = fixture()
    universal = check_perspective(original, proposal)
    assert universal["failed_obligation"] == "ORIGINAL_GOAL_SUFFICIENT"
    certificate = check_guarded_perspective(original, proposal, witness)
    assert certificate["accepted"] and len(certificate["obligations"]) == 7
    assert certificate["scope"] == SCOPE
    assert (certificate["original_state_dimension"], certificate["latent_state_dimension"]) == (3, 1)
    assert certificate["witness"] == witness
    assert certificate["parameter_domain"] == {p: "mathematical_integer" for p in original["parameters"]}
    engine = compile_guarded_acceleration(original, proposal, witness)
    for params in itertools.product([-2, 0, 3], repeat=4):
        for steps in [0, 1, 2, 5]:
            assert engine.run(params, steps) == original_execution(original, params, steps)
    params, n = (10**40, -10**60, 11, -10**20), 10**100
    assert engine.run(params, n) == ((params[0]+params[3]*n)**2+params[1]-params[0]**2,)
    # This valid reachability result is deliberately false at an arbitrary state.
    assert 99 != 2**2 + 7 - 2**2


def test_independent_normalizer_and_explicit_math_validate_seven_identities():
    original, proposal, witness = fixture()
    assert independent_proof(original, proposal, witness) == [True]*7
    for _, lhs, rhs in guarded_obligations(original, proposal, witness):
        assert all(sp.expand(l-r) == 0 for l, r in zip(independent_expression(lhs), independent_expression(rhs)))
    a, b, k, x, y = sp.symbols("a b k x y")
    h = y-x*x-b+a*a
    assert sp.expand(h.subs({x: a, y: b}, simultaneous=True)) == 0
    assert sp.expand(h.subs({x: x+k, y: y+2*k*x+k*k}, simultaneous=True)-h) == 0


def test_nonunit_preservation_nonzero_transition_multiplier_and_vector_goal():
    original, proposal, witness = fixture()
    a,b,k,x,y,t,z = sp.symbols("a b k x y t __z0")
    h, offset = y-x*x-b+a*a, b-a*a
    next_x = x+k+h
    original["transition"] = from_expressions(original["parameters"]+original["state"], [next_x, sp.expand(next_x**2+offset+2*h), 3*t+1])
    original["goal"] = projections(original["parameters"]+original["state"], ["y","x"])
    proposal["decode"] = from_expressions(original["parameters"]+["__z0"], [z*z+offset,z])
    space = original["parameters"]+original["state"]
    witness = bind_guarded_witness(original, proposal, witness["invariant"], preservation=constants(space,[2]),
        transition=constants(space,[1]), goal=constants(space,[1,0]))
    assert check_guarded_perspective(original, proposal, witness)["accepted"]
    assert independent_proof(original, proposal, witness) == [True]*7
    engine = compile_guarded_acceleration(original, proposal, witness)
    assert engine.run((2,7,3,1),5) == original_execution(original,(2,7,3,1),5) == (52,7)
    original["goal"]["outputs"].reverse()
    witness = bind_guarded_witness(original, proposal, witness["invariant"], **witness["multipliers"])
    assert check_guarded_perspective(original, proposal, witness)["failed_obligation"] == "GUARDED_GOAL"


@pytest.mark.parametrize("mutation,failed", [("initial", "INITIAL_INVARIANT"),
    ("transition", "INDUCTIVE_PRESERVATION"), ("goal", "GUARDED_GOAL"),
    ("invariant", "INITIAL_INVARIANT"), ("q", "INDUCTIVE_PRESERVATION"),
    ("r", "GUARDED_TRANSITION"), ("v", "GUARDED_GOAL"),
    ("latent_initial", "ENCODE_INITIAL"), ("closed_base", "CLOSED_BASE"), ("closed_step", "CLOSED_STEP")])
def test_false_bound_claims_are_refuted_even_with_fresh_hashes(mutation, failed):
    original, proposal, witness = fixture()
    params, space = original["parameters"], original["parameters"] + original["state"]
    a, b, c, k, x, y, t = sp.symbols("a b c k x y t")
    n = sp.Symbol(HORIZON)
    if mutation == "initial":
        original["initial"] = from_expressions(params, [a, b+1, c])
    elif mutation == "transition":
        original["transition"] = from_expressions(space, [x+k, y+2*k*x+k*k+1, 3*t+1])
    elif mutation == "goal":
        original["goal"] = projections(space, ["t"])
    elif mutation == "invariant":
        witness["invariant"] = from_expressions(space, [y-x*x])
    elif mutation in {"q", "r", "v"}:
        key = {"q": "preservation", "r": "transition", "v": "goal"}[mutation]
        witness["multipliers"][key] = constants(space, [2])
    elif mutation == "latent_initial":
        proposal["initial"] = from_expressions(params, [a+1])
    elif mutation == "closed_base":
        proposal["closed_form"] = from_expressions(params+[HORIZON], [a+k*n+1])
    else:
        proposal["closed_form"] = from_expressions(params+[HORIZON], [a+k*n+n*(n-1)*(n-2)*(n-3)])
    witness = bind_guarded_witness(original, proposal, witness["invariant"], **witness["multipliers"])
    proof = check_guarded_perspective(original, proposal, witness)
    assert not proof["accepted"] and proof["failed_obligation"] == failed
    with pytest.raises(ProgramError, match="Uncertified"):
        compile_guarded_acceleration(original, proposal, witness)


@pytest.mark.parametrize("mutation", ["problem_hash", "initial_hash", "proposal_hash", "stale_payload", "label", "dimension", "zero_guard", "max_terms", "max_work"])
def test_unknown_schema_hash_and_budget_fail_closed(mutation):
    original, proposal, witness = fixture()
    kwargs = {}
    if mutation.endswith("_hash"):
        witness[mutation.replace("_hash", "_sha256")] = "0"*64
    elif mutation == "stale_payload":
        proposal["decode"]["nodes"].append(["const", 1])
        proposal["decode"]["outputs"] = [len(proposal["decode"]["nodes"])-1]
    elif mutation == "label":
        witness["accepted"] = True
    elif mutation == "dimension":
        witness["multipliers"]["transition"]["outputs"] *= 2
    elif mutation == "zero_guard":
        witness["invariant"] = constants(original["parameters"]+original["state"], [0])
    else:
        kwargs = {"max_terms": 1} if mutation == "max_terms" else {"max_product_work": 1}
    proof = check_guarded_perspective(original, proposal, witness, **kwargs)
    assert not proof["accepted"] and proof["status"] == "NOT_VERIFIED"
    with pytest.raises(ProgramError):
        compile_guarded_acceleration(original, proposal, witness, **kwargs)


def test_certified_executor_owns_snapshot_and_certificate_is_descriptive_copy():
    original, proposal, witness = fixture()
    engine = compile_guarded_acceleration(original, proposal, witness)
    prior = engine.certificate
    original["initial"]["outputs"].reverse()
    proposal["decode"]["outputs"] = [0]
    witness["multipliers"]["goal"]["outputs"] = [0]
    prior["accepted"] = False
    assert engine.certificate["accepted"]
    assert engine.run((2,7,3,1), 5) == (52,)
    assert not check_guarded_perspective(original, proposal, witness)["accepted"]


@pytest.mark.parametrize("params,n", [([2,7,3,1], -1), ([2,7,3,1], True), ([2.0,7,3,1], 3), ([2,7], 3), (None, 3)])
def test_guarded_runtime_domain_is_enforced(params, n):
    with pytest.raises(ProgramError):
        compile_guarded_acceleration(*fixture()).run(params, n)


def test_symbolic_discovery_binds_initial_condition_and_generates_new_smaller_program():
    original, _ = coordinate_fixture()
    assert discover_polynomial_invariants(original)["goal_sufficiency_established"] is False
    result = propose_guarded_acceleration(original)
    assert result["status"] == "CERTIFIED_GUARDED_NATIVE_PROPOSAL"
    assert result["goal_sufficiency_established"] and not result["invariant_discovery_goal_sufficiency"]
    assert result["retained_state"] == ["x"] and result["removed_state"] == "y"
    assert not result["learned"] and not result["oracle_used"]
    assert compile_discovered_guarded(original, result).run((-4,11,-2,-3),17) == original_execution(original, (-4,11,-2,-3),17)
    bad = copy.deepcopy(result)
    bad["proposal"]["decode"]["outputs"] = [0]
    bad["certificate"]["accepted"] = True
    with pytest.raises(ProgramError):
        compile_discovered_guarded(original, bad)


@pytest.mark.parametrize("mutation", ["no_invariant", "irrelevant_goal", "feature_budget", "candidate_budget"])
def test_symbolic_discovery_abstains_without_proven_additional_elimination(mutation):
    original, _ = coordinate_fixture()
    kwargs = {}
    if mutation == "no_invariant":
        a,b,c,k,x,y,t = sp.symbols("a b c k x y t")
        original["transition"] = from_expressions(original["parameters"]+original["state"], [x+k, y+2*k*x+k*k+1, 3*t+1])
    elif mutation == "irrelevant_goal":
        original["goal"] = projections(original["parameters"]+original["state"], ["t"])
    else:
        kwargs = {"max_features": 1} if mutation == "feature_budget" else {"max_candidates": 1}
    assert not propose_guarded_acceleration(original, **kwargs)["goal_sufficiency_established"]


def test_common_interface_keeps_guarded_scope_separate_and_reuses_one_certificate(monkeypatch):
    import neumann1.guarded_perspective as module
    original, proposal, witness = fixture()
    view = ProblemView.opened("exact_integer_recurrence_guarded", original, lineage="opened-coordinate-fixture",
        asset={"role": "D", "allowed_use": "opened_development_only"})
    program = {"proposal": proposal, "witness": witness}
    bound = PerspectiveProposal.for_problem(view, program, removed_computation=["3 states to 1; no original unfolding"],
        reuse_conditions=["same bound original and proof; new exact inputs"], origin="ENGINEERING_FIXTURE_NOT_LEARNED")
    checker, calls = module.check_guarded_perspective, []
    def counted(*a, **kw):
        calls.append(1)
        return checker(*a, **kw)
    monkeypatch.setattr(module, "check_guarded_perspective", counted)
    engine = PreparedPerspective(view, bound)
    assert engine.experience.certificate.accepted and engine.decision.action == "ENGINEERING_ONLY"
    for n in [0,1,7]:
        output, costs = engine.run({"parameters": [2,7,3,1], "steps": n})
        assert output == ((2+n)**2+3,) and costs.complete_total("wall_seconds") is None
    assert len(calls) == 1
    with pytest.raises(ValueError, match="semantic scope"):
        PreparedPerspective(view, replace(bound, preservation_scope="all arbitrary integer states"))
    program["witness"]["problem_sha256"] = "0"*64
    invalid = PerspectiveProposal.for_problem(view, program, removed_computation=["claimed"], reuse_conditions=["claimed"], origin="invalid")
    blocked = PreparedPerspective(view, invalid)
    blocked.experience = replace(blocked.experience, certificate=replace(blocked.experience.certificate, accepted=True))
    with pytest.raises(ValueError, match="cannot execute"):
        blocked.run({"parameters": [2,7,3,1], "steps": 1})


def test_probe_gives_native_identical_goal_fusion_and_compilation_rights():
    from experiments.guarded_fixture_probe import fuse_goal, supplied_fixture, requests, expected
    original, proposal, _ = supplied_fixture()
    native = propose_polynomial_acceleration(original)
    strong, free = fuse_goal(original, native["proposal"]), fuse_goal(original, proposal)
    rows = [tuple(p)+(n,) for p,n in requests()]
    assert strong.run(rows) == free.run(rows) == [expected(row) for row in rows]
    assert strong.source == free.source
    assert (strong.add_calls,strong.mul_calls) == (free.add_calls,free.mul_calls)


def test_retained_first_probe_is_bound_complete_and_independently_verified():
    root = Path(__file__).resolve().parents[1]
    contract_path = root/"docs/experiments/guarded_fixture_probe.preregister.json"
    report = json.loads((root/"docs/research/guarded_fixture_probe_first_2026-10-08.json").read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert report["contract_sha256"] == sha256(contract_path.read_bytes()).hexdigest()
    assert report["contract"] == contract
    assert all(sha256((root/p).read_bytes()).hexdigest() == h for p,h in contract["source_sha256"].items())
    from experiments.guarded_fixture_probe import supplied_fixture, expected, ROUTES
    original, _, _ = supplied_fixture()
    from neumann1.guarded_perspective import digest
    assert digest(original) == contract["original_problem_sha256"]
    rows = report["observations"]
    assert len(rows) == 27 and all(r["status"] == "VERIFIED" for r in rows)
    assert len({(r["route"],r["count"],r["repeat"]) for r in rows}) == 27
    assert len({r["fused_goal_sha256"] for r in rows}) == 1
    assert len({(r["fused_add_calls"],r["fused_mul_calls"]) for r in rows}) == 1
    for row in rows:
        assert row["outputs"] == [list(expected(tuple(p)+(n,))) for p,n in contract["requests"][:row["count"]]]
        if row["route"] != "STRONG_NATIVE_SYMBOLIC":
            certificate = row["certificate"]
            witness = certificate["witness"]
            assert certificate["witness_sha256"] == digest(witness)
            assert certificate["problem_sha256"] == digest(original)
            proposal = contract["supplied_proposal"] if row["route"] == "FREE_VALID_GUARDED" else propose_guarded_acceleration(original)["proposal"]
            assert certificate["proposal_sha256"] == digest(proposal)
            assert independent_proof(original, proposal, witness) == [True]*7
    for count in [1,64]:
        by_key = {(r["route"],r["repeat"]):r["operational_parent_wall_seconds"] for r in rows if r["count"] == count}
        actual = statistics.geometric_mean(by_key[(ROUTES[0],i)]/by_key[(ROUTES[2],i)] for i in range(3))
        assert actual == report["ratios"][f"cold{count}_native_over_free"]
    assert report["engineering_cost_conclusion"] == "NO_MEANINGFUL_HEADROOM"
    assert report["complete_total_including_investment"] is None
    assert contract["gates"]["G1"] is False and contract["gates"]["G2"] is False
