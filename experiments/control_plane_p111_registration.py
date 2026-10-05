"""Model-free P1.11 opened-development registration and construction controls."""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import re

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import prune_candidates
from neumann1.control_plane_p110 import minimal_semantic_contrast
from neumann1.control_plane_p111 import contract as p111_contract, semantic_role_ir
from neumann1.control_plane_p111_semantic import build_bundle, contract as semantic_contract
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p16_catalog import catalog as p16_catalog
from experiments.control_plane_p17_catalog import catalog as p17_catalog
from experiments.control_plane_p18_catalog import catalog as p18_catalog
from experiments.control_plane_p19_catalog import catalog as p19_catalog
from experiments.control_plane_p110_catalog import catalog as p110_catalog
from experiments.control_plane_p111_catalog import catalog, negative_controls

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/experiments/control_plane_p111.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p111_public.json"
REFERENCES = ROOT / "docs/experiments/control_plane_p111_references.json"

GATE = {
    "observations_exact": 12,
    "accepted_min": 9,
    "model_calls_exact": 12,
    "neural_forward_calls_exact": 12,
    "generated_calls_exact": 0,
    "feasibility_calls_exact": 35,
    "selector_complete_exact": 12,
    "lexical_unique_selections_exact": 0,
    "selector_wall_ms": 10000.0,
    "per_item_wall_ms": 15000.0,
    "whole_study_wall_ms": 240000.0,
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
COUNTS = [2, 3, 4, 2, 3, 4, 3, 2, 3, 4, 3, 2]
EXPECTED = [1, 1, 1, 0, 0, 3, 2, 0, 1, 2, 2, 1]

_STOP = {
    "a", "an", "and", "the", "to", "that", "from", "toward", "into", "of",
    "is", "used", "stage", "component", "module", "device", "element",
    "artifact", "path", "one", "whether", "before", "final", "which", "can",
    "be", "by", "for", "this",
}


def development_architecture():
    return {
        "stage": "OPENED_DEVELOPMENT_REGISTERED",
        "p0": "P1.11 frozen semantic micro-executor",
        "task_mix": "12 fresh fully multi-feasible semantic role-matching tasks",
        "semantic_ir": "TARGET_ROLE_PLUS_SOURCE_BOUND_CANDIDATE_ROLE_DESCRIPTIONS",
        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
        "model_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        "model_parameters": 22713216,
        "model_state_elements_total": 22713728,
        "non_parameter_state_elements": 512,
        "device": "Tesla T4 / cuda",
        "precision": "float32",
        "pooling": "attention-mask mean pooling then L2 normalization",
        "score": "cosine target-to-candidate",
        "forward_calls_per_item": 1,
        "large_generative_model_on_primary_path": False,
        "first_only": True,
        "actual_model_run": "NOT_RUN",
        "complete_cost_accounting_required": True,
        "artifact_acquisition": "exact revision before study; file SHA-256 manifest retained",
        "baseline_rule": "model-free exact-token lexical-overlap anti-triviality control shares the same Semantic Role IR; future capability claims still require stronger shared baselines",
    }


def _tokens(text):
    if type(text) is not str:
        raise ValueError("lexical baseline text required")
    return tuple(
        token for token in re.findall(r"[a-z]+", text.lower())
        if token not in _STOP
    )


def lexical_overlap_receipt(ir):
    target = set(_tokens(ir["target_role"]))
    rows = []
    for candidate in ir["candidates"]:
        role = set(_tokens(candidate["role"]))
        overlap = sorted(target & role)
        rows.append({
            "entity": candidate["entity"],
            "overlap_tokens": overlap,
            "score": len(overlap),
        })
    best = max(row["score"] for row in rows)
    winners = [row["entity"] for row in rows if row["score"] == best]
    return {
        "target_tokens": sorted(target),
        "candidates": rows,
        "unique_selection": winners[0] if len(winners) == 1 else None,
        "max_overlap": best,
    }


def _satisfies(project, answer):
    domains, rules = project["domains"], project["constraints"]
    if type(answer) is not dict or set(answer) != set(domains):
        return False
    if any(type(answer[k]) is not int or answer[k] not in domains[k] for k in domains):
        return False
    for op, name, other in rules:
        left = answer[name]
        right = answer[other] if type(other) is str else other
        if op == "eq" and left != right:
            return False
        if op == "ne" and left == right:
            return False
        if op == "lt" and not left < right:
            return False
        if op == "le" and not left <= right:
            return False
    return True


def _all_answers(project):
    names = sorted(project["domains"])
    for values in product(*(project["domains"][name] for name in names)):
        answer = dict(zip(names, values))
        if _satisfies(project, answer):
            yield answer


def semantic_ir_from_bundle(view, parsed, bundle, eligible):
    contrast = minimal_semantic_contrast(view, parsed, bundle, eligible)
    bindings = contrast["bindings"]
    by_candidate = {
        row["candidate_index"]: row["entity"]["surface"]
        for row in bindings
    }
    if set(by_candidate) != set(eligible):
        raise ValueError("complete source-bound P1.11 candidate identity required")
    source_entities = sorted(row["entity"]["surface"] for row in bindings)
    if len(set(source_entities)) != len(source_entities):
        raise ValueError("distinct P1.11 source entities required")
    ir = semantic_role_ir(view["instruction"], sorted(source_entities), source_entities=sorted(source_entities))
    return ir, by_candidate


def registration():
    reg = json.loads(REG.read_bytes())
    rows = json.loads(PUBLIC.read_bytes())["rows"]
    refs = json.loads(REFERENCES.read_bytes())["rows"]
    if (rows, refs) != catalog():
        raise ValueError("P1.11 catalog content drift")
    if reg["architecture"] != development_architecture() or reg["gate"] != GATE or reg["boundaries"] != BOUNDARY:
        raise ValueError("P1.11 architecture/gate drift")
    if reg["scores_seen_at_registration"] is not False or reg["first_only"] is not True:
        raise ValueError("P1.11 pre-score first-only registration required")
    repair = reg.get("identity_repair")
    if repair != {
        "revision": "P1.11.1",
        "historical_archive_sha256": "d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0",
        "historical_verdict": "NOT_EVALUATED",
        "historical_reason": "INCOMPLETE_OR_COVERAGE_DRIFT",
        "historical_error": "P1.11 frozen model parameter-count drift",
        "historical_observations": 0,
        "historical_model_calls": 0,
        "historical_neural_forward_calls": 0,
        "task_scores_seen": False,
        "task_or_gate_changed": False,
        "repair_scope": "MODEL_PARAMETER_IDENTITY_ONLY",
    }:
        raise ValueError("P1.11.1 identity-repair provenance drift")
    if reg.get("p110_task_score_reuse") is not False:
        raise ValueError("P1.10 task-score reuse forbidden")
    ids = [row["task_id"] for row in rows]
    if reg["task_ids"] != ids or ids != [row["task_id"] for row in refs]:
        raise ValueError("P1.11 task order drift")
    if reg["candidate_counts"] != COUNTS or reg["expected_candidate_positions"] != EXPECTED:
        raise ValueError("P1.11 candidate/expected-position drift")
    if digest(rows) != reg["public_sha256"] or digest(refs) != reg["references_sha256"]:
        raise ValueError("P1.11 data hash drift")
    core = p111_contract()
    if core["model"]["model_revision"] != reg["architecture"]["model_revision"]:
        raise ValueError("P1.11 model revision drift")
    if core["forward_calls_per_ambiguous_item"] != 1 or core["large_generative_model_on_primary_path"] is not False:
        raise ValueError("P1.11 micro-executor contract drift")
    if core["future_actual_requires_new_registered_tasks"] is not True or core["p110_task_score_reuse"] is not False:
        raise ValueError("P1.11 fresh-task boundary drift")
    if semantic_contract()["p110_task_reuse"] is not False:
        raise ValueError("P1.11 semantic registry reuse drift")
    return reg, rows, refs


def check_construction():
    _, rows, refs = registration()
    previous = set()
    for old_rows in (
        p16_catalog()[0], p17_catalog()[0], p18_catalog()[0],
        p19_catalog()[0], p110_catalog()[0],
    ):
        for row in old_rows:
            previous.add(" ".join(row["view"]["public"]["query"].lower().split()))
    queries = [" ".join(row["view"]["public"]["query"].lower().split()) for row in rows]
    if len(set(queries)) != len(rows) or set(queries) & previous:
        raise ValueError("P1.11 raw obligation duplication")

    counts = []
    multi = 0
    lexical_unique = 0
    exact_overlap_pairs = 0
    ir_sha256 = []

    for row, ref in zip(rows, refs):
        parsed, bundle = build_bundle(row["view"])
        count = len(bundle["candidates"])
        counts.append(count)
        pruning = prune_candidates(parsed, bundle)
        if pruning["unknown_indexes"]:
            raise ValueError("P1.11 construction feasibility UNKNOWN")
        if pruning["sat_indexes"] != list(range(count)):
            raise ValueError("P1.11 set must remain fully multi-feasible")

        ir, by_candidate = semantic_ir_from_bundle(
            row["view"], parsed, bundle, pruning["sat_indexes"]
        )
        ir_sha256.append(digest(ir))
        lexical = lexical_overlap_receipt(ir)
        if lexical["unique_selection"] is not None:
            lexical_unique += 1
        exact_overlap_pairs += sum(bool(c["overlap_tokens"]) for c in lexical["candidates"])
        if any(c["score"] != 0 for c in lexical["candidates"]):
            raise ValueError("P1.11 exact-token anti-triviality control failed")

        expected = ref["expected_candidate"]
        expected_entity = by_candidate[expected]
        if expected_entity not in {candidate["entity"] for candidate in ir["candidates"]}:
            raise ValueError("expected P1.11 semantic entity missing")

        checker = _checker(ref)
        for index in pruning["sat_indexes"]:
            project = compile_references(parsed, bundle, index)["public"]
            answers = list(_all_answers(project))
            if not answers:
                raise ValueError("SAT candidate without exhaustive witness")
            overlap = [answer for answer in answers if checker(answer)]
            if index == expected:
                if not overlap:
                    raise ValueError("expected P1.11 candidate has no original-valid answer")
            elif overlap:
                raise ValueError("wrong P1.11 candidate overlaps private original obligation")
        if not checker(ref["witness"]):
            raise ValueError("P1.11 positive checker control rejected")
        bad = {name: 987654321 for name in ref["private"]["domains"]}
        if checker(bad):
            raise ValueError("P1.11 negative checker control accepted")
        multi += 1

    stopped = 0
    for view in negative_controls():
        try:
            build_bundle(view)
        except Exception:
            stopped += 1
        else:
            raise ValueError("P1.11 negative control admitted")

    if counts != COUNTS:
        raise ValueError("P1.11 prospective candidate shape drift")
    if lexical_unique != GATE["lexical_unique_selections_exact"] or exact_overlap_pairs != 0:
        raise ValueError("P1.11 lexical anti-triviality drift")

    return {
        "registration_valid": True,
        "observations": len(rows),
        "multi_feasible_tasks": multi,
        "candidate_counts": counts,
        "expected_forward_calls": [1] * len(rows),
        "total_expected_forward_calls": len(rows),
        "feasibility_calls_expected": sum(counts),
        "lexical_unique_selections": lexical_unique,
        "exact_overlap_candidate_pairs": exact_overlap_pairs,
        "semantic_ir_sha256": ir_sha256,
        "out_of_grammar_stops": stopped,
        "model_inference": False,
        "weights_loaded": False,
        **BOUNDARY,
    }


if __name__ == "__main__":
    print(json.dumps(check_construction(), sort_keys=True))
