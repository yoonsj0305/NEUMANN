"""Contract/semantic negative controls. Fixtures NEVER count as Q6 ability."""
import copy
import importlib.util
import pathlib

import pytest

from neumann1.q6.contracts import Artifact, digest, seal_artifact
from neumann1.q6.transport import checked_type, extract, substitute, transport, tup
from neumann1 import invention_core as ic

P = pathlib.Path(__file__).resolve().parents[2] / "research/q6/reference.py"
SPEC = importlib.util.spec_from_file_location("q6_test_reference", P)
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)


def fixture(ast=("add", ("v", 0), ("k", 1)), ti=("I",), ot="I"):
    method = {"kind": "ast", "ast": ast, "input_types": list(ti), "state_types": list(ti), "output_type": ot}
    return seal_artifact({"producer_commit": "1" * 40, "source_task_digest": "2" * 64,
                          "observation_schema": {"input_types": ti, "output_type": ot},
                          "discovered_representation": {"kind": "typed-ast.v1"},
                          "executable_method": method,
                          "source_verification": {"method_digest": digest(method), "status": "EXACT_OBSERVED_SOURCE",
                                                  "checker": "test-only independent checker"},
                          "provenance": {"scope": "synthetic interface fixture"},
                          "resource_cost": {"discovery_cpu_seconds": None}})


def test_contract_requires_bound_evidence_and_trusted_authority():
    a = fixture()
    assert Artifact.admit(a, lambda _: True).identity == a["artifact_id"]
    with pytest.raises(ValueError):
        Artifact.admit(a, lambda _: False)
    for field in ("source_verification", "resource_cost", "producer_commit"):
        broken = dict(a)
        del broken[field]
        with pytest.raises(ValueError):
            Artifact.admit(broken, lambda _: True)


def test_shuffled_source_structure_is_rejected_even_if_resealed():
    a = fixture()
    b = copy.deepcopy(a)
    b["executable_method"]["ast"] = ["mul", ["v", 0], ["k", 1]]
    b = seal_artifact(b)
    with pytest.raises(ValueError, match="different method"):
        Artifact.admit(b, lambda _: True)


def test_type_compatible_wrong_frozen_relation_fails_original_observations():
    wrong = ("ast", ("add", ("v", 0), ("k", 1)))
    examples = [((x,), x * x + 1) for x in (2, 3, 4)]
    assert not all(REF.execute(wrong, i) == o for i, o in examples)


def test_failed_precondition_is_undefined_not_a_success():
    assert REF.execute(("ast", ("head", ("v", 0))), ((),)) is None


def test_names_only_change_is_replay_and_not_compound_transport():
    inv = extract([Artifact.admit(fixture(), lambda _: True)])
    task = {"id": "different-name", "in_types": ["I"], "out_type": "I",
            "train": [((n,), n + 1) for n in range(4)], "test": ()}
    r = transport(task, inv, cap_s=1)
    assert r["via"] == "replay" and r["candidate_correspondence"] is None


def test_hidden_test_is_rejected_at_inference_boundary():
    inv = extract([Artifact.admit(fixture(), lambda _: True)])
    with pytest.raises(ValueError, match="hidden TEST"):
        transport({"in_types": ["I"], "out_type": "I", "train": [((1,), 2)], "test": [((9,), 10)]}, inv)


def test_single_core_constructs_compound_correspondence_and_no_map_loses_it():
    inv = extract([Artifact.admit(fixture(), lambda _: True)])
    task = {"in_types": ["I"], "out_type": "I", "train": [((n,), n * n + 1) for n in (2, 3, 4, 5)], "test": ()}
    r = transport(task, inv, cap_s=2)
    assert r["verification_status"] == "TRAIN_CONSISTENT" and r["via"] == "compound_transport"
    method = r["transformed_executable_method"]
    sol = method["kind"], tup(method["ast"])
    assert all(REF.execute(sol, (n,)) == n * n + 1 for n in (7, 11, 13))
    removed = transport(task, inv, cap_s=2, mode="C-no-map")
    assert removed["verification_status"] == "UNKNOWN"
    assert all(r["measured_cost"]["phase_cpu_seconds"][k] >= 0 for k in r["measured_cost"]["phase_cpu_seconds"])


def test_capture_avoiding_substitution_with_nested_target_binders():
    # Source sum(element * source_scale), source arity 2.
    src = ("foldrI", ("add", ("mul", ("v", 2), ("v", 1)), ("v", 3)), ("k", 0), ("v", 0))
    target_sum = ("foldrI", ("add", ("v", 1), ("v", 2)), ("k", 0), ("v", 0))
    out = substitute(src, 2, 1, {0: ("v", 0), 1: target_sum})
    assert checked_type(out, ("L",)) == "I"
    assert REF.execute(("ast", out), ((2, 3, 5),)) == 100


def test_source_body_types_cannot_be_forged_as_original_output_type():
    a = fixture(("eq", ("v", 0), ("k", 1)), ot="I")
    with pytest.raises(ValueError, match="result type"):
        extract([Artifact.admit(a, lambda _: True)])
