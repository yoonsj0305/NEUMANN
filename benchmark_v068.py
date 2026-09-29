"""Frozen end-to-end latency audit of the learned affine compressor."""

from __future__ import annotations

import json
import os
import platform
import statistics
from time import perf_counter_ns

import numpy
import scipy
import sklearn

from neumann1.learned_compression import check_scored_proposals
from neumann1.learned_compression_dataset import (
    generate_learned_compression_cell,
    learned_scale_grid,
)
from neumann1.residual_headroom_dataset import (
    prior_v036_signatures,
    v036_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
    score_candidates,
)
from neumann1.structural_compression import (
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


LEARNED_THRESHOLD = 0.40
TARGET_LEAF_THRESHOLD = 0.10
CASES_PER_CELL = 4
REPEATS = 5
METHODS = ("direct", "learned_mlp", "target_leaf")


def _cases():
    forbidden = set(prior_v036_signatures())
    forbidden.update(example.signature for example in v036_final_examples())
    output = []
    for k, n in learned_scale_grid():
        cell = generate_learned_compression_cell(
            k,
            n,
            count=CASES_PER_CELL,
            split="v068_final",
            seed=680_000 + 1000 * k + n,
            forbidden_signatures=frozenset(forbidden),
        )
        output.extend(cell)
        forbidden.update(example.signature for example in cell)
    if len(output) != len(learned_scale_grid()) * CASES_PER_CELL:
        raise AssertionError("incomplete final grid")
    return tuple(output)


def _time_once(example, method, scorer):
    if method == "direct":
        started = perf_counter_ns()
        answer, counts = solve_exact_gauss_jordan(example.full_system)
        solved = perf_counter_ns()
        verified, _ = verify_exact_full_system(example.full_system, answer)
        finished = perf_counter_ns()
        accepted, rejected = 0, 0
        score_ns, check_ns = 0, 0
        solve_ns, verify_ns = solved - started, finished - solved
        solver_ops = counts.arithmetic_ops
        candidate_count = 0
    else:
        started = perf_counter_ns()
        scored = score_candidates(example, method, frozen_scorer=scorer)
        scored_at = perf_counter_ns()
        threshold = (
            LEARNED_THRESHOLD if method == "learned_mlp"
            else TARGET_LEAF_THRESHOLD
        )
        budget = sum(item.score >= threshold for item in scored)
        checked = check_scored_proposals(
            example, scored, proposal_budget=budget
        )
        finished = perf_counter_ns()
        result = checked.materialized
        answer = result.full_answer
        verified = result.verified and result.ground_truth_equivalent
        accepted = len(checked.accepted_candidates)
        rejected = len(checked.rejected_candidates)
        candidate_count = len(scored)
        solver_ops = result.solver_counts.arithmetic_ops
        score_ns, check_ns = scored_at - started, finished - scored_at
        solve_ns, verify_ns = 0, 0

    truth = dict(zip(example.full_system.variables, example.full_system.ground_truth))
    if not verified or answer != truth:
        raise AssertionError(f"unverified result for {method}")
    return {
        "score_ms": score_ns / 1e6,
        "checker_ms": check_ns / 1e6,
        "solve_ms": solve_ns / 1e6,
        "verify_ms": verify_ns / 1e6,
        "total_ms": (finished - started) / 1e6,
        "solver_ops_final_only": solver_ops,
        "candidates": candidate_count,
        "accepted": accepted,
        "rejected": rejected,
        "verified": verified,
    }


def run():
    scorer = fit_frozen_v033_scorer()
    cases = _cases()
    rows = []
    for example in cases:
        # Every path receives the same first-use exclusion and the same repeats.
        for method in METHODS:
            _time_once(example, method, scorer)
        samples = {method: [] for method in METHODS}
        for repeat in range(REPEATS):
            for offset in range(len(METHODS)):
                method = METHODS[(repeat + offset) % len(METHODS)]
                samples[method].append(_time_once(example, method, scorer))
        summary = {}
        for method in METHODS:
            measurements = samples[method]
            summary[method] = {
                key: (statistics.median(item[key] for item in measurements)
                      if key.endswith("_ms") else measurements[0][key])
                for key in measurements[0]
            }
            summary[method]["total_ms_min"] = min(
                item["total_ms"] for item in measurements
            )
            summary[method]["total_ms_max"] = max(
                item["total_ms"] for item in measurements
            )
        rows.append({
            "k": example.core_dimension,
            "n": example.apparent_dimension,
            "case_index": example.example_index,
            "methods": summary,
        })

    cells = []
    for k, n in learned_scale_grid():
        group = [row for row in rows if (row["k"], row["n"]) == (k, n)]
        methods = {}
        for method in METHODS:
            methods[method] = {
                "median_total_ms": statistics.median(
                    row["methods"][method]["total_ms"] for row in group
                ),
                "sum_case_medians_ms": sum(
                    row["methods"][method]["total_ms"] for row in group
                ),
                "median_score_ms": statistics.median(
                    row["methods"][method]["score_ms"] for row in group
                ),
                "median_checker_ms": statistics.median(
                    row["methods"][method]["checker_ms"] for row in group
                ),
                "median_final_solver_ops": statistics.median(
                    row["methods"][method]["solver_ops_final_only"]
                    for row in group
                ),
            }
        cells.append({"k": k, "n": n, "methods": methods})

    large_pass = all(
        cell["methods"]["learned_mlp"]["median_total_ms"]
        <= .8 * cell["methods"]["target_leaf"]["median_total_ms"]
        and cell["methods"]["learned_mlp"]["median_total_ms"]
        < cell["methods"]["direct"]["median_total_ms"]
        for cell in cells if cell["n"] >= 16
    )
    small_pass = all(
        cell["methods"]["learned_mlp"]["median_total_ms"]
        <= 1.1 * cell["methods"]["target_leaf"]["median_total_ms"]
        for cell in cells if cell["n"] <= 8
    )
    return {
        "experiment": "v0.0.68 full-path iso-capability gate",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": numpy.__version__, "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        },
        "frozen_checkpoint_sha256": scorer.fitted_state_sha256,
        "protocol": {"cases_per_cell": CASES_PER_CELL, "repeats": REPEATS,
                     "learned_threshold": LEARNED_THRESHOLD,
                     "target_leaf_threshold": TARGET_LEAF_THRESHOLD},
        "all_verified": all(
            row["methods"][method]["verified"]
            for row in rows for method in METHODS
        ),
        "local_learned_compute_advantage": large_pass and small_pass,
        "cells": cells,
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
