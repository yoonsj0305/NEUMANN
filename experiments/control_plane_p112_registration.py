"""P1.12 model-free opened-development registration and construction controls."""
from __future__ import annotations

from pathlib import Path
import json, sys

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import prune_candidates
from neumann1.control_plane_p112 import MODEL, contract as p112_contract, build_joint_pairs
from neumann1.control_plane_p112_semantic import build_bundle, contract as semantic_contract
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p16_catalog import catalog as p16_catalog
from experiments.control_plane_p17_catalog import catalog as p17_catalog
from experiments.control_plane_p18_catalog import catalog as p18_catalog
from experiments.control_plane_p19_catalog import catalog as p19_catalog
from experiments.control_plane_p110_catalog import catalog as p110_catalog
from experiments.control_plane_p111_catalog import catalog as p111_catalog
from experiments.control_plane_p111_registration import (
    semantic_ir_from_bundle, lexical_overlap_receipt, _all_answers,
)
from experiments.control_plane_p112_catalog import catalog, negative_controls

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"docs/experiments/control_plane_p112_public.json"
REFERENCES=ROOT/"docs/experiments/control_plane_p112_references.json"
REG=ROOT/"docs/experiments/control_plane_p112.preregister.json"

GATE={
    "observations_exact": 12,
    "accepted_min": 9,
    "model_calls_exact": 12,
    "neural_forward_calls_exact": 12,
    "generated_calls_exact": 0,
    "feasibility_calls_exact": 35,
    "selector_complete_exact": 12,
    "lexical_unique_selections_exact": 0,
    "selector_wall_ms": 10000,
    "per_item_wall_ms": 15000,
    "whole_study_wall_ms": 240000,
    "out_of_grammar_controls_exact": 4
}
BOUNDARY={
    "development_only": True,
    "fresh_validation_registered": False,
    "p2_registration_admitted": False,
    "p2_admitted": False,
    "decision3_admitted": False,
    "global_questions_closed": []
}
COUNTS=[2,3,4,2,3,4,3,2,3,4,3,2]
EXPECTED=[1,0,1,1,2,0,1,0,2,2,1,1]
ARCHITECTURE={
    "stage": "OPENED_DEVELOPMENT_REGISTERED",
    "p0": "P1.12 joint cross-encoder semantic judge",
    "task_mix": "12 newly authored fully multi-feasible functional-role tasks",
    "semantic_ir": "JOINT_TARGET_CANDIDATE_ROLE_PAIRS",
    "model_id": "cross-encoder/ms-marco-MiniLM-L6-v2",
    "model_revision": "ce0834f22110de6d9222af7a7a03628121708969",
    "expected_model_parameters": 22713601,
    "expected_model_safetensors_sha256": "821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae",
    "device": "Tesla T4 / cuda",
    "precision": "float32",
    "score": "one joint scalar relevance logit per target-candidate pair",
    "decision": "unique raw top-1 without margin/absolute threshold",
    "forward_calls_per_item": 1,
    "all_candidate_pairs_batched_together": True,
    "large_generative_model_on_primary_path": False,
    "first_only": True,
    "actual_model_run": "NOT_RUN",
    "complete_cost_accounting_required": True,
    "artifact_acquisition": "exact model revision and full per-file SHA-256 manifest before timed study",
    "baseline_rule": "exact-token lexical overlap anti-triviality check, not a strong capability baseline"
}


def registration():
    reg=json.loads(REG.read_bytes())
    rows=json.loads(PUBLIC.read_bytes())["rows"]
    refs=json.loads(REFERENCES.read_bytes())["rows"]
    if (rows,refs)!=catalog():
        raise ValueError("P1.12 fresh catalog content drift")
    if (reg["architecture"]!=ARCHITECTURE or reg["gate"]!=GATE or
            reg["boundaries"]!=BOUNDARY):
        raise ValueError("P1.12 preregistered architecture/gate drift")
    if (reg["first_only"] is not True or
            reg["scores_seen_at_registration"] is not False or
            reg["p111_task_score_reuse"] is not False or
            reg["p111_tasks_as_p112_evidence"] is not False):
        raise ValueError("P1.12 preregistration and leakage boundary drift")
    ids=[r["task_id"] for r in rows]
    if ids!=reg["task_ids"] or ids!=[r["task_id"] for r in refs]:
        raise ValueError("P1.12 task coverage/order drift")
    if reg["candidate_counts"]!=COUNTS or reg["expected_candidate_positions"]!=EXPECTED:
        raise ValueError("P1.12 task-shape drift")
    if digest(rows)!=reg["public_sha256"] or digest(refs)!=reg["references_sha256"]:
        raise ValueError("P1.12 frozen task/reference hash drift")
    core=p112_contract()
    if (core["model"]["model_revision"]!=ARCHITECTURE["model_revision"] or
            core["model"]["expected_parameters"]!=ARCHITECTURE["expected_model_parameters"] or
            core["forward_calls_per_ambiguous_item"]!=1 or
            core["cross_encoder_joint_interaction"] is not True or
            core["confidence_threshold"] is not None or
            core["p111_tasks_as_p112_evidence"] is not False):
        raise ValueError("P1.12 model/selection contract drift")
    if semantic_contract()["p111_task_reuse"] is not False:
        raise ValueError("P1.12 fresh semantic registry drift")
    return reg,rows,refs


def check_construction():
    _, rows, refs = registration()
    previous=set()
    for old_rows in (
        p16_catalog()[0],p17_catalog()[0],p18_catalog()[0],
        p19_catalog()[0],p110_catalog()[0],p111_catalog()[0]
    ):
        for r in old_rows:
            previous.add(" ".join(r["view"]["public"]["query"].lower().split()))
    queries=[" ".join(r["view"]["public"]["query"].lower().split()) for r in rows]
    if len(set(queries))!=len(rows) or set(queries)&previous:
        raise ValueError("P1.12 duplicate old/raw query")

    counts=[]; pair_hashes=[]; multi=0; lexical_unique=0
    for row,ref in zip(rows,refs):
        parsed,bundle=build_bundle(row["view"])
        n=len(bundle["candidates"])
        counts.append(n)
        pruning=prune_candidates(parsed,bundle)
        if pruning["unknown_indexes"] or pruning["sat_indexes"]!=list(range(n)):
            raise ValueError("P1.12 candidate feasibility/coverage drift")

        semantic,by_candidate=semantic_ir_from_bundle(
            row["view"],parsed,bundle,pruning["sat_indexes"]
        )
        src_entities=sorted(c["entity"] for c in semantic["candidates"])
        joint=build_joint_pairs(row["view"]["instruction"],src_entities)
        pair_hashes.append(digest(joint))
        if [p["entity"] for p in joint["pairs"]]!=src_entities:
            raise ValueError("P1.12 source-bound pair order drift")
        for pair,c in zip(joint["pairs"],semantic["candidates"]):
            if pair["entity"]!=c["entity"] or not pair["candidate_text"].endswith(c["role"]):
                raise ValueError("P1.12 candidate role drift")

        lexical=lexical_overlap_receipt(semantic)
        lexical_unique+=int(lexical["unique_selection"] is not None)
        if any(p["score"]!=0 for p in lexical["candidates"]):
            raise ValueError("P1.12 lexical overlap control failed")

        exp=ref["expected_candidate"]
        if by_candidate[exp] not in src_entities:
            raise ValueError("P1.12 expected source binding absent")
        checker=_checker(ref)
        for idx in pruning["sat_indexes"]:
            project=compile_references(parsed,bundle,idx)["public"]
            possible=list(_all_answers(project))
            if not possible:
                raise ValueError("P1.12 supposedly SAT candidate has no witness")
            valid=any(checker(ans) for ans in possible)
            if valid!=(idx==exp):
                raise ValueError("P1.12 wrong candidate accepts original obligation")
        if not checker(ref["witness"]):
            raise ValueError("P1.12 positive witness rejected")
        if checker({name:999999 for name in ref["private"]["domains"]}):
            raise ValueError("P1.12 negative witness accepted")
        multi+=1
    stopped=0
    for view in negative_controls():
        try: build_bundle(view)
        except Exception: stopped+=1
        else: raise ValueError("P1.12 out-of-grammar control accepted")
    if counts!=COUNTS or sum(counts)!=GATE["feasibility_calls_exact"]:
        raise ValueError("P1.12 candidate count drift")
    if lexical_unique!=0 or stopped!=4:
        raise ValueError("P1.12 lexical/grammar drift")
    return {
        "registration_valid":True,
        "observations":len(rows),
        "multi_feasible_tasks":multi,
        "candidate_counts":counts,
        "expected_forward_calls":[1]*len(rows),
        "total_expected_forward_calls":len(rows),
        "feasibility_calls_expected":sum(counts),
        "lexical_unique_selections":lexical_unique,
        "joint_pair_ir_sha256":pair_hashes,
        "out_of_grammar_stops":stopped,
        "model_inference":False,
        "weights_loaded":False,
        **BOUNDARY
    }


if __name__=="__main__":
    if "--emit-hashes" in sys.argv:
        rows,refs=catalog()
        print(json.dumps({"public_sha256":digest(rows),"references_sha256":digest(refs)}))
    else:
        print(json.dumps(check_construction(),sort_keys=True))
