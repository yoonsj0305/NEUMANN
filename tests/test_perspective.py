from dataclasses import replace
import json

import pytest

from experiments.inductive_fixture_cases import coordinate_fixture
from experiments.recursive_summary_cases import lifted_prefix, tree
from neumann1.inductive_perspective import original_execution
from neumann1.perspective import (CostReceipt, PerspectiveProposal, PreparedPerspective,
                                 ProblemView, STAGES)
from neumann1.recursive_summary import reference
from neumann1.structural_data_rights import DataUseError


def prepare(domain, original, program):
    view = ProblemView.opened(domain, original, lineage="opened-fixture-family",
                              asset={"role": "D", "allowed_use": "opened_development_only"})
    proposal = PerspectiveProposal.for_problem(
        view, program, removed_computation=["original unfolding/transition work"],
        reuse_conditions=["same certified original and representation, new valid inputs"],
        origin="OFFLINE_FIXTURE_NOT_LEARNED")
    return view, proposal, PreparedPerspective(view, proposal)


@pytest.mark.parametrize("domain", ["exact_integer_recurrence", "integer_list_right_fold"])
def test_common_contract_preserves_original_goal_and_single_certification(domain, monkeypatch):
    if domain == "exact_integer_recurrence":
        import neumann1.inductive_perspective as module
        original, program = coordinate_fixture()
        checker_name = "check_perspective"
        requests = [{"parameters": [2, 7, 3, 1], "steps": n} for n in [0, 1, 17]]
        expected = [original_execution(original, r["parameters"], r["steps"]) for r in requests]
    else:
        import neumann1.recursive_summary as module
        original, program = lifted_prefix()
        checker_name = "check_summary"
        requests = [tree(v, "balanced") for v in [[], [-5, 4], [4, -5]]]
        expected = [reference(original, v) for v in [[], [-5, 4], [4, -5]]]
    checker = getattr(module, checker_name)
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return checker(*args, **kwargs)
    monkeypatch.setattr(module, checker_name, counted)
    view, proposal, engine = prepare(domain, original, program)
    assert engine.experience.certificate.accepted
    assert engine.decision.action == "ENGINEERING_ONLY"
    assert view.state.goal_sha256 and proposal.problem_sha256 == view.sha256
    for request, answer in zip(requests, expected):
        result, cost = engine.run(request)
        assert result == answer
        assert cost.complete_total("wall_seconds") is None
        assert cost.complete_total("flops") is None
    assert len(calls) == 1  # preparation proof reused; no repeated proof per query
    assert not engine.experience.training_activated and not engine.experience.fresh_eligible


@pytest.mark.parametrize("domain", ["exact_integer_recurrence", "integer_list_right_fold"])
def test_invalid_representation_and_forged_metadata_cannot_authorize_execution(domain):
    original, program = coordinate_fixture() if domain == "exact_integer_recurrence" else lifted_prefix()
    if domain == "exact_integer_recurrence":
        program["decode"]["outputs"].reverse()
        # fixture scalar goal: force a different decoder constant
        program["decode"]["nodes"].append(["const", 8123])
        program["decode"]["outputs"] = [len(program["decode"]["nodes"]) - 1]
    else:
        program["decode"]["outputs"] = ["z1"]
    _, _, engine = prepare(domain, original, program)
    assert not engine.experience.certificate.accepted
    engine.experience = replace(engine.experience,
        certificate=replace(engine.experience.certificate, accepted=True))
    with pytest.raises(ValueError, match="cannot execute"):
        engine.run({"parameters": [2, 7, 3, 1], "steps": 1} if domain == "exact_integer_recurrence" else ["nil"])


def test_unknown_solver_result_blocks_execution(monkeypatch):
    import neumann1.recursive_summary as summary
    monkeypatch.setattr(summary, "check_summary", lambda *a, **kw: {"accepted": False, "status": "UNKNOWN"})
    _, _, engine = prepare("integer_list_right_fold", *lifted_prefix())
    assert engine.decision.action == "FALLBACK"
    assert not engine.experience.certificate.accepted
    with pytest.raises(ValueError, match="cannot execute"):
        engine.run(["nil"])


def test_mutating_caller_payload_does_not_change_certified_engine_or_proposal():
    original, program = lifted_prefix()
    view, proposal, engine = prepare("integer_list_right_fold", original, program)
    problem_identity, proposal_identity = view.sha256, proposal.sha256
    original["empty"][0] = 100
    program["decode"]["outputs"] = ["z1"]
    assert (view.sha256, proposal.sha256) == (problem_identity, proposal_identity)
    assert engine.run(tree([-5, 4], "left"))[0] == [0]


def test_certificate_cannot_transfer_to_changed_original_goal_or_scope():
    original, program = coordinate_fixture()
    view, proposal, _ = prepare("exact_integer_recurrence", original, program)
    changed = json.loads(view.original_json)
    changed["goal"]["outputs"] = [0]
    other_view = replace(view, original_json=json.dumps(changed))
    with pytest.raises(ValueError, match="bind original"):
        PreparedPerspective(other_view, proposal)
    with pytest.raises(ValueError, match="semantic scope"):
        PreparedPerspective(view, replace(proposal, preservation_scope="IEEE float64"))


@pytest.mark.parametrize("role", ["H", "O", "S", "F", "B"])
def test_rights_denial_precedes_problem_validation(role):
    with pytest.raises(DataUseError, match="denied"):
        ProblemView.opened("integer_list_right_fold", {"sealed": "must not parse"},
                           lineage="sealed", asset={"role": role})


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
def test_cost_values_fail_closed(value):
    with pytest.raises(ValueError):
        CostReceipt.observed(wall_seconds={"discovery": value}, scope="test")


def test_complete_cost_requires_every_stage_and_never_sums_unlike_units():
    cost = CostReceipt.observed(wall_seconds={"verify_compile": 0.02}, scope="component only")
    assert cost.complete_total("wall_seconds") is None
    assert cost.complete_total("energy_joules") is None
    assert json.loads(cost.peak_memory_json) == {"peak_ram_bytes": None, "peak_vram_bytes": None}
    with pytest.raises(ValueError, match="same-unit"):
        cost.complete_total("peak_ram_bytes")
    complete = CostReceipt.observed(wall_seconds={stage: 0.01 for stage in STAGES},
                                    scope="synthetic accounting fixture, not measured performance")
    assert complete.complete_total("wall_seconds") == pytest.approx(0.1)
    forged = json.loads(complete.measurements_json)
    forged["wall_seconds"]["investment"] = -100
    with pytest.raises(ValueError, match="nonnegative"):
        replace(complete, measurements_json=json.dumps(forged)).complete_total("wall_seconds")
