"""Fail-closed evidence analysis checks, not new task-performance observations."""
from copy import deepcopy
import hashlib

import pytest

from experiments.recursive_state_evidence_triage import checked, context_collision, stored_lift
from neumann1.recursive_library_baseline import propose
from neumann1.recursive_summary import check_summary, identity, program


PREFIX = {"semantics": "integer_list_right_fold", "empty": [0],
          "step": program(["head", "r0"], [["max", ["add", "head", "r0"], 0]])}


@pytest.fixture
def evidence():
    found = propose(PREFIX)
    proof = check_summary(PREFIX, found["proposal"])
    assert proof["accepted"]
    certificate = {"accepted": True, "binding": {"source_sha256": "test-source-identity",
                   "projection": {"public": PREFIX}}, "certificate": proof,
                   "proposal_sha256": identity(found["proposal"])}
    case = {"source": {"sha256": "test-source-identity"}, "proposal": found}
    return certificate, case


def test_collision_refutes_goal_only_join_with_reachable_child_goals():
    result = context_collision(PREFIX, [-1], [0], [1])
    assert result["left_a_goal"] == result["left_b_goal"] == [0]
    assert result["right_goal"] == [1]
    assert result["concat_a_goal"] == [0] and result["concat_b_goal"] == [1]
    assert result["goal_only_join_refuted"]


def test_different_child_goals_do_not_establish_join_impossibility():
    assert not context_collision(PREFIX, [-1], [1], [1])["goal_only_join_refuted"]


def test_same_scalar_witness_does_not_refute_sum_goal():
    public = {"semantics": "integer_list_right_fold", "empty": [0],
              "step": program(["head", "r0"], [["add", "head", "r0"]])}
    assert not context_collision(public, [-1], [0], [1])["goal_only_join_refuted"]


def test_hash_mismatch_is_not_accepted_as_evidence(tmp_path):
    path = tmp_path / "source.ml"
    path.write_bytes(b"original")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert checked(path, digest) == digest
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        checked(path, digest)


def test_stored_proof_keeps_original_goal_identity(evidence):
    certificate, case = evidence
    public, proposal = stored_lift(certificate, case)
    assert public == PREFIX and len(proposal["empty"]) == 2


@pytest.mark.parametrize("mutation", ["unknown", "missing", "false", "goal", "proposal", "source", "accepted_only"])
def test_missing_unknown_or_mismatched_proof_rejected(evidence, mutation):
    certificate, case = deepcopy(evidence)
    if mutation == "unknown":
        certificate["certificate"]["obligations"][0]["status"] = "unknown"
    elif mutation == "missing":
        certificate["certificate"]["obligations"].pop()
    elif mutation == "false":
        certificate["certificate"]["accepted"] = False
    elif mutation == "goal":
        certificate["binding"]["projection"]["public"]["empty"] = [1]
    elif mutation == "proposal":
        case["proposal"]["proposal"]["decode"]["outputs"] = ["z1"]
    elif mutation == "source":
        case["source"]["sha256"] = "other-original"
    else:
        certificate["certificate"] = {"accepted": True}
    with pytest.raises(ValueError):
        stored_lift(certificate, case)
