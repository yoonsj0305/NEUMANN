"""P1.2 full-S4 advisory routing; opened development only.

The complete mean has no selected Latin subset. Mapping interactions are
marginalized, not proven absent. Leave-one-balanced-orbit-out sensitivity is
a new operational statistic, never a re-evaluation of the P1.1 gate.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, digest, finite, public_view, snapshot
from neumann1.control_plane_p1_contract import MODEL, PUBLIC_SHA256, TASK_IDS
from neumann1.control_plane_p11 import (CODES, SEMANTICS, CodePlan, CodedFailure,
                                      NextCodeBackend, audit_codes, plan_cost, prompt_for)

SCHEMA = "neumann.control-plane-p1.2.v1"
CODE_TOKEN_IDS = (236776, 236799, 236780, 236796)
PERMUTATIONS = tuple(itertools.permutations(range(4)))
# Quotient by cyclic code shifts: six disjoint balanced four-map orbits.
# Lexicographic definitions depend only on the group, never observed scores.
ORBIT_BASES = sorted({min(tuple((v+k)%4 for v in p) for k in range(4)) for p in PERMUTATIONS})
ORBITS = tuple(tuple(PERMUTATIONS.index(tuple((v+k)%4 for v in base)) for k in range(4))
               for base in ORBIT_BASES)
CRITERIA = {"numeric_tolerance_nats": 0.05, "loo_centered_tolerance_nats": 0.5,
            "minimum_full_margin_nats": 0.5, "all_loo_winners_stable": True,
            "distinct_winners": 2, "dominant_winner_max": 10,
            "centered_task_range_min_nats": 0.001}
P11_FIRST_SHA256 = "6bdc2cc9435cefd8a3e99d1d0bc3589bd3b6ad84e50be83db877b1dde769e3ec"


@dataclass(frozen=True)
class Budget:
    context_tokens: int = 4096
    evaluated_tokens: int = 589824
    padded_tokens: int = 589824
    input_rows: int = 864
    score_rows: int = 3456
    scored_tokens: int = 3456
    forward_calls: int = 432
    task_wall_ms: float = 120000.0
    controller_wall_ms: float = 540000.0
    study_wall_ms: float = 1800000.0


def validate_group(permutations=PERMUTATIONS, orbits=ORBITS):
    if tuple(permutations) != PERMUTATIONS or len(set(permutations)) != 24:
        raise ValueError("all 24 registered lexicographic bijections required")
    if tuple(tuple(o) for o in orbits) != ORBITS or sorted(i for o in orbits for i in o) != list(range(24)):
        raise ValueError("six registered disjoint balanced orbits required")
    for orbit in orbits:
        if any(sorted(permutations[i][r] for i in orbit) != list(range(4)) for r in range(4)):
            raise ValueError("every omitted orbit must be balanced")


def contract():
    validate_group()
    return {"schema": SCHEMA, "model": dict(MODEL), "codes": list(CODES), "code_token_ids": list(CODE_TOKEN_IDS), "semantics": dict(SEMANTICS),
            "permutations": snapshot(PERMUTATIONS), "balanced_orbit_indices": snapshot(ORBITS),
            "criteria": dict(CRITERIA), "budget": asdict(Budget()),
            "development_public_sha256": PUBLIC_SHA256,
            "modes": ["batch4", "unbatched1", "reverse_batch4"],
            "statistic": "equal_mean_logprob_over_all_24_bijections",
            "robustness_statistic": "centered_full24_vs_each_balanced_leave4_out20_mean",
            "p11_verdict_replaced": False, "p11_first_sha256": P11_FIRST_SHA256,
            "per_mapping_interactions_may_remain": True, "all_24_permutations": True,
            "task_prior_calibration": False, "historical_score_reuse": False,
            "development_only": True, "p2_admitted": False, "decision3_admitted": False,
            "fresh_validation": "UNREGISTERED_UNOPENED_PENDING_DEVELOPMENT_AND_ARCHITECTURE_FREEZE",
            "generated_calls": 0, "tool_calls": 0, "frontier_calls": 0,
            "new_training": False, "sealed_data_opened": False}


def _winner(row):
    return ROUTES[max(range(4), key=lambda r: (row[r], -r))]


def _center(row):
    mean = math.fsum(row) / 4
    return [v-mean for v in row]


def aggregate(matrix):
    validate_group()
    if len(matrix) != 24 or any(len(row) != 4 for row in matrix):
        raise ValueError("exactly 24 four-code log-probability rows required")
    matrix = [[finite(v) for v in row] for row in matrix]
    if any(v > 0 for row in matrix for v in row):
        raise ValueError("nonpositive log probabilities required")
    aligned = [[matrix[i][p[r]] for r in range(4)] for i, p in enumerate(PERMUTATIONS)]
    scores = [math.fsum(row[r] for row in aligned)/24 for r in range(4)]
    orbit_scores = [[math.fsum(aligned[i][r] for i in orbit)/4 for r in range(4)] for orbit in ORBITS]
    loo = [[math.fsum(aligned[i][r] for i in range(24) if i not in orbit)/20 for r in range(4)]
           for orbit in ORBITS]
    centered = _center(scores)
    delta = max(abs(v-centered[r]) for row in loo for r, v in enumerate(_center(row)))
    # Report remaining interactions; passing LOO does NOT assert these are small.
    orbit_delta = max(abs(a-b) for ga in orbit_scores for gb in orbit_scores
                      for a, b in zip(_center(ga), _center(gb)))
    per_map_range = max(max(_center(row)[r] for row in aligned)-min(_center(row)[r] for row in aligned)
                        for r in range(4))
    ranked = sorted(scores, reverse=True)
    return {"scores": dict(zip(ROUTES, scores)), "winner": _winner(scores),
            "margin_nats": ranked[0]-ranked[1], "orbit_scores": orbit_scores,
            "loo_scores": loo, "loo_winners": [_winner(row) for row in loo],
            "all_loo_winners_stable": all(_winner(row) == _winner(scores) for row in loo),
            "max_centered_loo_delta_nats": delta,
            "max_centered_orbit_pair_delta_nats": orbit_delta,
            "max_centered_per_mapping_range_nats": per_map_range}


def score_development(view, encode_prefix, code_ids, backend, ledger, remaining_ms):
    original = public_view(view); began = perf_counter_ns(); passes = []
    try:
        for mode, size, order in (("batch4", 4, list(range(24))), ("unbatched1", 1, list(range(24))),
                                  ("reverse_batch4", 4, list(reversed(range(24))))):
            start = perf_counter_ns()
            observation = {"mode": mode, "status": "STARTED", "order": order, "batch_size": size}
            passes.append(observation)
            plan = CodePlan(tuple(tuple(encode_prefix(prompt_for(original, PERMUTATIONS[i]))) for i in order),
                            tuple(code_ids))
            costs = plan_cost(plan, size)
            observation.update(prefixes=snapshot(plan.prefixes), code_ids=list(code_ids), planned=costs)
            if any(ledger[k]+v > getattr(Budget(), k) for k, v in costs.items()):
                raise ValueError("study cost admission cap")
            left = min(Budget().task_wall_ms-(perf_counter_ns()-began)/1e6, remaining_ms())
            if left <= 0:
                raise TimeoutError("complete task/study/controller deadline")
            try:
                result = backend.evaluate(plan, size, left)
            except CodedFailure as exc:
                for k, v in exc.known_cost.items(): ledger[k] += v
                observation.update(known_partial_cost=exc.known_cost, backend_complete_ms=exc.complete_ms)
                raise
            actual = result["cost"]
            for k, v in actual.items(): ledger[k] += v
            if actual != costs:
                raise ValueError("exact backend accounting mismatch")
            rows = result["scores"]
            if len(rows) != 24 or any(len(row) != 4 for row in rows):
                raise ValueError("exact full-S4 matrix required")
            matrix = [None]*24
            for i, row in zip(order, rows): matrix[i] = [finite(v) for v in row]
            aggregate(matrix)
            observation.update(status="COMPLETE", matrix=matrix, actual=actual,
                               peak_accelerator_memory_bytes=result["peak_accelerator_memory_bytes"],
                               complete_ms=(perf_counter_ns()-start)/1e6)
            if remaining_ms() <= 0 or (perf_counter_ns()-began)/1e6 > Budget().task_wall_ms:
                raise TimeoutError("completed scoring over deadline; retained")
        matrices = [p["matrix"] for p in passes]
        delta = max(abs(matrices[0][r][c]-m[r][c]) for m in matrices[1:] for r in range(24) for c in range(4))
        result = {"status": "COMPLETE", "summary": aggregate(matrices[0]), "numeric_delta_nats": delta}
    except Exception as exc:
        result = {"status": "FAILED", "error": type(exc).__name__+": "+str(exc)}
    result.update(passes=passes, complete_ms=(perf_counter_ns()-began)/1e6,
                  view_sha256=digest(original), trace_sha256=digest(passes))
    return result


def evaluate_development(records, unchanged, accounting_complete, generated_calls, controller_ms, study_ms):
    boundary = {"p2_admitted": False, "decision3_admitted": False, "general_capability_gate": "NOT_EVALUATED",
                "global_questions_closed": [], "development_only": True, "fresh_validation_registered": False}
    def result(verdict, reason): return {**boundary, "verdict": verdict, "reason": reason}
    if generated_calls != 0: return result("FAIL", "GENERATION_FORBIDDEN")
    if len(records) != 12 or unchanged is not True or not accounting_complete:
        return result("NOT_EVALUATED", "INCOMPLETE_OR_IDENTITY_DRIFT")
    if tuple(r.get("task_id") for r in records) != TASK_IDS:
        return result("NOT_EVALUATED", "DEVELOPMENT_COVERAGE_DRIFT")
    if finite(controller_ms, True) > Budget().controller_wall_ms or finite(study_ms, True) > Budget().study_wall_ms:
        return result("FAIL", "COMPLETE_COST_WALL_CAP")
    winners = []; centered = []
    for record in records:
        if record["status"] != "COMPLETE": return result("NOT_EVALUATED", "INCOMPLETE")
        if finite(record["complete_ms"], True) > Budget().task_wall_ms: return result("FAIL", "TASK_WALL_CAP")
        s = record["summary"]
        if finite(record["numeric_delta_nats"], True) > CRITERIA["numeric_tolerance_nats"]:
            return result("FAIL", "NUMERICAL_OR_ORDER_INSTABILITY")
        if finite(s["max_centered_loo_delta_nats"], True) > CRITERIA["loo_centered_tolerance_nats"]:
            return result("FAIL", "FULL_MEAN_ORBIT_SENSITIVITY")
        if finite(s["margin_nats"], True) <= CRITERIA["minimum_full_margin_nats"] or s["all_loo_winners_stable"] is not True:
            return result("FAIL", "AMBIGUOUS_OR_UNSTABLE_FULL_MEAN_WINNER")
        winners.append(s["winner"]); centered.append(_center([finite(s["scores"][r]) for r in ROUTES]))
    spread = max(max(row[r] for row in centered)-min(row[r] for row in centered) for r in range(4))
    okay = len(set(winners)) >= CRITERIA["distinct_winners"] and max(winners.count(r) for r in ROUTES) <= CRITERIA[
        "dominant_winner_max"] and spread >= CRITERIA["centered_task_range_min_nats"]
    return {**result("PASS" if okay else "FAIL", "DEVELOPMENT_DIAGNOSTIC_ONLY" if okay else "DEGENERATE_ROUTE_SELECTION"),
            "winner_counts": {r: winners.count(r) for r in ROUTES}, "centered_task_range_nats": spread,
            "next": "FREEZE_ARCHITECTURE_THEN_REGISTER_FRESH_OPENED_VALIDATION" if okay else "PRESERVE_FIRST_DEVELOPMENT_FAILURE"}
