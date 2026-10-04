"""Model-free frozen P1.7 opened-development registration and checker controls."""
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p13 import admissibility
from neumann1.control_plane_p17 import (
    build_candidates, compile_references, contract, interpret_and_execute,
)
from experiments.control_plane_p14_catalog import catalog as p14_catalog
from experiments.control_plane_p15_catalog import catalog as p15_catalog
from experiments.control_plane_p16_catalog import catalog as p16_catalog
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p17_catalog import catalog, negative_controls

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/experiments/control_plane_p17.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p17_public.json"
REFERENCES = ROOT / "docs/experiments/control_plane_p17_references.json"

GATE = {
    "observations_exact": 12,
    "unique_tasks_exact": 8,
    "ambiguous_tasks_exact": 4,
    "overall_accepted_min": 11,
    "unique_accepted_exact": 8,
    "ambiguous_accepted_min": 3,
    "unique_model_calls_exact": 0,
    "ambiguous_model_calls_exact": 4,
    "unique_neural_forward_calls_exact": 0,
    "ambiguous_neural_forward_calls_exact": 144,
    "generated_calls_exact": 0,
    "semantic_retries": 0,
    "per_item_wall_ms": 180000.0,
    "whole_study_wall_ms": 1800000.0,
    "out_of_grammar_controls_exact": 4,
}
BOUNDARY = {
    "development_only": True,
    "fresh_validation_registered": False,
    "p2_registration_admitted": False,
    "p2_admitted": False,
    "decision3_admitted": False,
    "global_questions_closed": [],
}


def development_architecture():
    value = dict(contract())
    value.update(
        stage="OPENED_DEVELOPMENT_REGISTERED",
        actual_gemma_run="NOT_RUN",
        development_registration="REGISTERED",
        development_task_mix="8 unique zero-neural + 4 bounded pronoun-selection tasks",
        ambiguous_semantics=(
            "public instruction requires selecting the pronoun binding that makes all stated "
            "constraints jointly satisfiable; construction control proves exactly one original-valid candidate"
        ),
        first_only=True,
        complete_cost_accounting_required=True,
    )
    return value


def registration():
    reg = json.loads(REG.read_bytes())
    rows = json.loads(PUBLIC.read_bytes())["rows"]
    refs = json.loads(REFERENCES.read_bytes())["rows"]
    if (rows, refs) != catalog():
        raise ValueError("P1.7 catalog content drift")
    if reg["architecture"] != development_architecture() or reg["gate"] != GATE or reg["boundaries"] != BOUNDARY:
        raise ValueError("P1.7 architecture/gate/boundary drift")
    if reg["first_only"] is not True or reg["scores_seen_at_registration"] is not False:
        raise ValueError("P1.7 first-only pre-score registration required")
    ids = [r["task_id"] for r in rows]
    if reg["task_ids"] != ids or ids != [r["task_id"] for r in refs]:
        raise ValueError("P1.7 ordered task coverage drift")
    if digest(rows) != reg["public_sha256"] or digest(refs) != reg["references_sha256"]:
        raise ValueError("P1.7 data hash drift")
    for path, expected in reg["source_sha256"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("P1.7 source byte drift: " + path)
    return reg, rows, refs


def _candidate_original_valid(row, ref, bundle, index):
    proposal = compile_references(row["view"], bundle, index)
    try:
        answer = _executor(proposal["route"], proposal["public"])
    except Exception:
        return False
    return _hidden_verifier(ref)(row["view"], answer)


def check_construction():
    _, rows, refs = registration()

    previous = set()
    for prior in (p14_catalog()[0], p15_catalog()[0], p16_catalog()[0]):
        for row in prior:
            if "query" in row["view"]["public"]:
                previous.add(" ".join(row["view"]["public"]["query"].lower().split()))
    queries = [" ".join(r["view"]["public"]["query"].lower().split()) for r in rows]
    if len(set(queries)) != len(rows) or set(queries) & previous:
        raise ValueError("duplicate opened raw obligation")

    candidate_counts = []
    deterministic_accepts = 0
    unique_original_valid_ambiguous = 0
    for i, (row, ref) in enumerate(zip(rows, refs)):
        if set(row) != {"task_id", "view"} or set(row["view"]) != {"instruction", "public"} or set(row["view"]["public"]) != {"query"}:
            raise ValueError("hidden reference field in public view")
        admitted = admissibility(row["view"])
        if admitted["admissible_routes"] != ["DIRECT"] or admitted["interpretation_required"] is not True:
            raise ValueError("raw obligation must stop at unchanged P1.3")

        check = _checker(ref)
        if not check(ref["witness"]):
            raise ValueError("original positive checker control rejected")
        bad = "987654321" if ref["family"] == "math_logic" else {k:987654321 for k in ref["private"]["domains"]}
        if check(bad):
            raise ValueError("original negative checker control accepted")

        bundle = build_candidates(row["view"])
        count = len(bundle["candidates"])
        candidate_counts.append(count)
        expected_path = "UNIQUE" if i < 8 else "AMBIGUOUS"
        if ref["semantic_path"] != expected_path:
            raise ValueError("semantic-path registration drift")

        if i < 8:
            if count != 1:
                raise ValueError("unique development item must have one candidate")
            def forbidden():
                raise AssertionError("unique construction control must never construct neural selector")
            record = interpret_and_execute(
                row["view"], _executor, _hidden_verifier(ref), forbidden
            )
            if not record["accepted"] or record["model_calls"] != 0 or record["neural_forward_calls"] != 0:
                raise ValueError("deterministic unique construction control failed")
            deterministic_accepts += 1
        else:
            expected_counts = (2, 3, 4, 3)
            if count != expected_counts[i - 8]:
                raise ValueError("ambiguous candidate count drift")
            valid = [
                j for j in range(count)
                if _candidate_original_valid(row, ref, bundle, j)
            ]
            if valid != [ref["expected_candidate"]]:
                raise ValueError("ambiguous public consistency does not identify exactly one original-valid candidate")
            unique_original_valid_ambiguous += 1

    stopped = 0
    for view in negative_controls():
        try:
            build_candidates(view)
        except Exception:
            stopped += 1
        else:
            raise ValueError("out-of-grammar construction control admitted")

    if [r["family"] for r in refs[:4]] != ["math_logic"] * 4:
        raise ValueError("P1.7 arithmetic composition drift")
    if any(r["family"] != "constraint_planning" for r in refs[4:]):
        raise ValueError("P1.7 CSP composition drift")

    return {
        "registration_valid": True,
        "observations": 12,
        "unique_tasks": 8,
        "ambiguous_tasks": 4,
        "candidate_counts": candidate_counts,
        "deterministic_unique_accepts": deterministic_accepts,
        "ambiguous_unique_original_valid_controls": unique_original_valid_ambiguous,
        "positive_checker_controls": 12,
        "negative_checker_controls": 12,
        "out_of_grammar_stops": stopped,
        "dedup_scope": "normalized raw text against P1.4/P1.5/P1.6; no semantic-novelty claim",
        "model_inference": False,
        "weights_loaded": False,
        **BOUNDARY,
    }


if __name__ == "__main__":
    print(json.dumps(check_construction(), sort_keys=True))
