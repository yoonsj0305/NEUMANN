"""Model-free proposal/freeze checks for first P1.9 opened development.

No model weights or inference are used here.  The --proposal surface exists only
to produce the exact pre-score registration object that can then be frozen in
docs/experiments/control_plane_p19.preregister.json.
"""
from __future__ import annotations

from itertools import product
import argparse
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import Budget as FeasibilityBudget, prune_candidates
from neumann1.control_plane_p19_balanced import contract as balanced_contract
from neumann1.control_plane_p19_semantic import (
    build_semantic_bundle, contract as semantic_contract,
)
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p16_catalog import catalog as p16_catalog
from experiments.control_plane_p17_catalog import catalog as p17_catalog
from experiments.control_plane_p18_catalog import catalog as p18_catalog
from experiments.control_plane_p19_catalog import catalog, negative_controls

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/experiments/control_plane_p19.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p19_public.json"
REFERENCES = ROOT / "docs/experiments/control_plane_p19_references.json"

IDS = tuple(["p19d_a0%d" % i for i in range(1,5)] + ["p19d_b0%d" % i for i in range(1,5)])
EXPECTED_CANDIDATE_COUNTS = [2,3,4,3,2,3,4,3]
EXPECTED_B_FORWARDS = [6,10,12,10]

GATE = {
    "observations_exact": 8,
    "a_tasks_exact": 4,
    "b_tasks_exact": 4,
    "overall_accepted_min": 7,
    "a_accepted_exact": 4,
    "b_accepted_min": 3,
    "a_model_calls_exact": 0,
    "a_neural_forward_calls_exact": 0,
    "b_model_calls_exact": 4,
    "b_neural_forward_calls_exact": 38,
    "b_forward_calls_by_task_exact": EXPECTED_B_FORWARDS,
    "generated_calls_exact": 0,
    "feasibility_calls_exact": 24,
    "tool_calls_min": 7,
    "tool_calls_max": 8,
    "verifier_calls_min": 7,
    "verifier_calls_max": 8,
    "semantic_retries": 0,
    "selector_wall_ms": 180000.0,
    "per_item_wall_ms": 240000.0,
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

PIN_PATHS = (
    "neumann1/control_plane_p17.py",
    "neumann1/control_plane_p18.py",
    "neumann1/control_plane_p19.py",
    "neumann1/control_plane_p19_balanced.py",
    "neumann1/control_plane_p19_semantic.py",
    "experiments/control_plane_p19_catalog.py",
    "experiments/control_plane_p19_registration.py",
    "docs/experiments/control_plane_p19_public.json",
    "docs/experiments/control_plane_p19_references.json",
)


def development_architecture():
    return {
        "schema": "neumann.p19-opened-development.v1",
        "stage": "OPENED_DEVELOPMENT_REGISTERED",
        "front_half": "P1.8_FEASIBILITY_FIRST_RETAINED",
        "residual_selector": semantic_contract(),
        "parent_balanced_contract": balanced_contract(),
        "task_mix": "4 fresh A feasibility-reducible + 4 fresh B multi-feasible semantic",
        "feasibility_budget": FeasibilityBudget().__dict__,
        "first_only": True,
        "actual_gemma_run": "NOT_RUN",
        "complete_cost_accounting_required": True,
        "semantic_abstention_is_accounting_complete_if_receipt_complete": True,
        "selector_startup_accounting": "charged once to whole study before B items; excluded from individual B item wall",
        "baseline_rule": "future baselines share extraction/compiler/pruner/tools/checker access",
        "p18_opened_tasks_model_score_reuse": False,
    }


def _satisfies(project, answer):
    domains, rules = project["domains"], project["constraints"]
    if type(answer) is not dict or set(answer) != set(domains):
        return False
    if any(type(answer[k]) is not int or answer[k] not in domains[k] for k in domains):
        return False
    for op, name, other in rules:
        a = answer[name]
        b = answer[other] if type(other) is str else other
        if op == "eq" and a != b: return False
        if op == "ne" and a == b: return False
        if op == "lt" and not a < b: return False
        if op == "le" and not a <= b: return False
    return True


def _all_answers(project):
    names = sorted(project["domains"])
    for vals in product(*(project["domains"][k] for k in names)):
        ans = dict(zip(names, vals))
        if _satisfies(project, ans):
            yield ans


def _data():
    rows = json.loads(PUBLIC.read_bytes())["rows"]
    refs = json.loads(REFERENCES.read_bytes())["rows"]
    if (rows, refs) != catalog():
        raise ValueError("P1.9 catalog/data content drift")
    if tuple(r["task_id"] for r in rows) != IDS or tuple(r["task_id"] for r in refs) != IDS:
        raise ValueError("P1.9 task order drift")
    return rows, refs


def check_construction():
    rows, refs = _data()

    previous = set()
    for old_rows in (p16_catalog()[0], p17_catalog()[0], p18_catalog()[0]):
        for r in old_rows:
            previous.add(" ".join(r["view"]["public"]["query"].lower().split()))
    queries = [" ".join(r["view"]["public"]["query"].lower().split()) for r in rows]
    if len(set(queries)) != len(rows) or set(queries) & previous:
        raise ValueError("P1.9 opened raw obligation duplication")

    candidate_counts = []
    a_unique = b_multi = 0
    b_forwards = []
    for i, (row, ref) in enumerate(zip(rows, refs)):
        parsed, bundle = build_semantic_bundle(row["view"])
        count = len(bundle["candidates"])
        candidate_counts.append(count)
        pruning = prune_candidates(parsed, bundle)
        if pruning["unknown_indexes"]:
            raise ValueError("P1.9 construction feasibility UNKNOWN")

        expected = ref["expected_candidate"]
        if i < 4:
            if pruning["sat_indexes"] != [expected]:
                raise ValueError("P1.9 A must reduce to exactly expected candidate")
            a_unique += 1
        else:
            if len(pruning["sat_indexes"]) < 2 or expected not in pruning["sat_indexes"]:
                raise ValueError("P1.9 B must remain genuinely multi-feasible")
            checker = _checker(ref)
            for idx in pruning["sat_indexes"]:
                project = compile_references(parsed, bundle, idx)["public"]
                answers = list(_all_answers(project))
                if not answers:
                    raise ValueError("P1.9 SAT candidate without exhaustive witness")
                overlap = [a for a in answers if checker(a)]
                if idx == expected:
                    if not overlap:
                        raise ValueError("expected P1.9 B candidate has no original-valid answer")
                elif overlap:
                    raise ValueError("wrong P1.9 B candidate overlaps private original obligation")
            k = len(pruning["sat_indexes"])
            b_forwards.append(2*k + 2*((2*k + 3)//4))
            b_multi += 1

        checker = _checker(ref)
        if not checker(ref["witness"]):
            raise ValueError("P1.9 positive checker control rejected")
        bad = {k: 987654321 for k in ref["private"]["domains"]}
        if checker(bad):
            raise ValueError("P1.9 negative checker control accepted")

    if candidate_counts != EXPECTED_CANDIDATE_COUNTS:
        raise ValueError("P1.9 candidate-count drift")
    if b_forwards != EXPECTED_B_FORWARDS:
        raise ValueError("P1.9 planned B forward-count drift")

    stopped = 0
    for view in negative_controls():
        try:
            build_semantic_bundle(view)
        except Exception:
            stopped += 1
        else:
            raise ValueError("P1.9 negative control admitted")

    return {
        "registration_construction_valid": True,
        "observations": 8,
        "a_tasks": a_unique,
        "b_tasks": b_multi,
        "candidate_counts": candidate_counts,
        "b_planned_forward_calls": b_forwards,
        "b_planned_forward_calls_total": sum(b_forwards),
        "out_of_grammar_stops": stopped,
        "raw_query_dedup_against": ["P1.6", "P1.7", "P1.8"],
        "p18_model_score_reuse": False,
        "model_inference": False,
        "weights_loaded": False,
        **BOUNDARY,
    }


def proposal():
    construction = check_construction()
    rows, refs = _data()
    return {
        "schema": "neumann.p19-opened-development-registration.v1",
        "parent_main": None,
        "architecture": development_architecture(),
        "first_only": True,
        "opened_development": True,
        "scores_seen_at_registration": False,
        "scope": "8 fresh raw CSP obligations: 4 A feasibility-reducible and 4 B multi-feasible semantic-cue tasks; opened development only",
        "task_ids": list(IDS),
        "candidate_counts": EXPECTED_CANDIDATE_COUNTS,
        "public_sha256": digest(rows),
        "references_sha256": digest(refs),
        "gate": GATE,
        "boundaries": BOUNDARY,
        "construction_receipt": construction,
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in PIN_PATHS
        },
    }


def registration():
    if not REG.is_file():
        raise ValueError("frozen P1.9 preregistration required")
    frozen = json.loads(REG.read_bytes())
    current = proposal()
    # parent_main is a publication identity field and is checked literally.
    current["parent_main"] = frozen.get("parent_main")
    if frozen != current:
        raise ValueError("P1.9 frozen registration drift")
    if frozen.get("scores_seen_at_registration") is not False or frozen.get("first_only") is not True:
        raise ValueError("P1.9 pre-score first-only registration required")
    return frozen, *_data()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--proposal", action="store_true")
    args = p.parse_args()
    obj = proposal() if args.proposal else registration()[0]
    print(json.dumps(obj, sort_keys=True, indent=2))
