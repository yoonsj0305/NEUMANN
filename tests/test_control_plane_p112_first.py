"""P1.12 model-free fresh opened-development registration tests."""
import json
from pathlib import Path

import pytest

from experiments.control_plane_p112_catalog import catalog, negative_controls
from experiments.control_plane_p112_registration import (
    registration, check_construction, COUNTS, EXPECTED, GATE, BOUNDARY,
    ROOT, PUBLIC, REFERENCES, REG,
)
from neumann1.control_plane_p112_semantic import build_bundle
from neumann1.control_plane_p112 import build_joint_pairs
from neumann1.control_plane_v1 import digest


def test_p112_freeze_and_gate_before_any_score():
    reg,rows,refs=registration()
    assert len(rows)==len(refs)==12
    assert reg["scores_seen_at_registration"] is False
    assert reg["p111_task_score_reuse"] is False
    assert reg["p111_tasks_as_p112_evidence"] is False
    assert reg["candidate_counts"]==COUNTS
    assert reg["expected_candidate_positions"]==EXPECTED
    assert reg["gate"]==GATE
    assert reg["boundaries"]==BOUNDARY
    assert reg["architecture"]["expected_model_safetensors_sha256"]=="821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae"
    assert reg["public_sha256"]==digest(rows)
    assert reg["references_sha256"]==digest(refs)


def test_all_twelve_are_fully_multifeasible_not_lexical_toys():
    result=check_construction()
    assert result["registration_valid"] is True
    assert result["observations"]==12
    assert result["multi_feasible_tasks"]==12
    assert result["candidate_counts"]==COUNTS
    assert result["feasibility_calls_expected"]==35
    assert result["out_of_grammar_stops"]==4
    assert result["lexical_unique_selections"]==0
    assert len(result["joint_pair_ir_sha256"])==12
    assert result["model_inference"] is False
    assert result["weights_loaded"] is False


def test_new_task_and_old_task_vocab_independent():
    rows,refs=catalog()
    assert all(r["task_id"].startswith("p112d_") for r in rows)
    assert all(ref["task_id"]==r["task_id"] for r,ref in zip(rows,refs))
    assert len({r["view"]["instruction"] for r in rows})==12
    assert len({r["view"]["public"]["query"] for r in rows})==12
    assert all("p111d" not in str(r) for r in rows)


def test_canonical_source_entity_binding():
    row,_=catalog()
    ins=row[0]["view"]["instruction"]
    ir=build_joint_pairs(ins,["X","Y"])
    assert ir["pairs"][0]["entity"]=="X"
    assert ir["pairs"][1]["entity"]=="Y"
    assert ir["pairs"][1]["candidate_text"]=="Candidate role: trusted timestamp authority"


def test_unregistered_instruction_does_not_parse():
    for view in negative_controls():
        with pytest.raises(Exception):
            build_bundle(view)


def test_p112_artifacts_are_exactly_pinned_not_runtime_generated():
    p=json.loads(PUBLIC.read_bytes())["rows"]
    r=json.loads(REFERENCES.read_bytes())["rows"]
    reg=json.loads(REG.read_bytes())
    assert (p,r)==catalog()
    assert reg["public_sha256"]==digest(p)
    assert reg["references_sha256"]==digest(r)
