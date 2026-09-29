"""Independent Q2 opportunity screen with a verified fast direct comparator."""

from __future__ import annotations

import json
import os
import platform
from statistics import median
from time import perf_counter_ns

import numpy

import benchmark_v068
from neumann1.learned_compression_dataset import (
    generate_learned_compression_cell,
    learned_scale_grid,
)
from neumann1.residual_headroom_dataset import (
    prior_v036_signatures,
    v036_final_examples,
)
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.verified_direct import solve_verified_numeric_or_exact


CASES_PER_CELL = 4
REPEATS = 5
METHODS = ("direct_exact", "direct_verified_numeric", "learned_mlp", "target_leaf")


def _cases():
    forbidden = set(prior_v036_signatures())
    forbidden.update(case.signature for case in v036_final_examples())
    forbidden.update(case.signature for case in benchmark_v068._cases())
    output = []
    for k, n in learned_scale_grid():
        cell = generate_learned_compression_cell(
            k, n, count=CASES_PER_CELL, split="v069_final",
            seed=690_000 + 1000 * k + n,
            forbidden_signatures=frozenset(forbidden),
        )
        output.extend(cell)
        forbidden.update(case.signature for case in cell)
    if len(output) != len(learned_scale_grid()) * CASES_PER_CELL:
        raise AssertionError("incomplete final grid")
    return tuple(output)


def _time_once(case, method, scorer):
    if method in ("direct_exact", "learned_mlp", "target_leaf"):
        prior = "direct" if method == "direct_exact" else method
        row = benchmark_v068._time_once(case, prior, scorer)
        return {
            "total_ms": row["total_ms"],
            "score_ms": row["score_ms"],
            "checker_ms": row["checker_ms"],
            "fallback": False,
            "proposal_status": "not_applicable",
            "verified": row["verified"],
        }

    if method != "direct_verified_numeric":
        raise ValueError(method)
    started = perf_counter_ns()
    result = solve_verified_numeric_or_exact(case.full_system)
    finished = perf_counter_ns()
    truth = dict(zip(case.full_system.variables, case.full_system.ground_truth))
    if result.answer != truth:
        raise AssertionError("numeric/fallback path did not match exact truth")
    return {
        "total_ms": (finished - started) / 1e6,
        "score_ms": 0.0,
        "checker_ms": 0.0,
        "fallback": result.used_exact_fallback,
        "proposal_status": result.proposal_status,
        "verified": True,
    }


def run():
    cases = _cases()
    scorer = fit_frozen_v033_scorer()
    rows = []
    for case in cases:
        for method in METHODS:
            _time_once(case, method, scorer)  # untimed warm-up
        samples = {method: [] for method in METHODS}
        for repetition in range(REPEATS):
            for offset in range(len(METHODS)):
                method = METHODS[(repetition + offset) % len(METHODS)]
                samples[method].append(_time_once(case, method, scorer))
        summaries = {}
        for method in METHODS:
            measured = samples[method]
            if any(row["verified"] is not True for row in measured):
                raise AssertionError("unverified method")
            summaries[method] = {
                "median_total_ms": median(row["total_ms"] for row in measured),
                "median_score_ms": median(row["score_ms"] for row in measured),
                "median_checker_ms": median(row["checker_ms"] for row in measured),
                "min_total_ms": min(row["total_ms"] for row in measured),
                "max_total_ms": max(row["total_ms"] for row in measured),
                "fallback_count": sum(row["fallback"] for row in measured),
                "proposal_status": sorted(set(
                    row["proposal_status"] for row in measured
                )),
            }
        rows.append({"k": case.core_dimension, "n": case.apparent_dimension,
                     "case_index": case.example_index, "methods": summaries})

    cells = []
    for k, n in learned_scale_grid():
        group = [row for row in rows if (row["k"], row["n"]) == (k, n)]
        methods = {
            method: {
                "median_total_ms": median(
                    row["methods"][method]["median_total_ms"] for row in group
                ),
                "sum_case_medians_ms": sum(
                    row["methods"][method]["median_total_ms"] for row in group
                ),
            }
            for method in METHODS
        }
        cells.append({"k": k, "n": n, "methods": methods})

    def advantage(cell):
        direct = min(cell["methods"][method]["median_total_ms"]
                     for method in METHODS[:2])
        compressed = min(cell["methods"][method]["median_total_ms"]
                         for method in METHODS[2:])
        return compressed / direct

    opportunity = (
        all(advantage(cell) <= 0.8 for cell in cells if cell["n"] == 32)
        and all(advantage(cell) <= 1.1 for cell in cells if cell["n"] <= 8)
    )
    return {
        "experiment": "v0.0.69 strong verified direct baseline",
        "environment": {"python": platform.python_version(),
                        "platform": platform.platform(),
                        "numpy": numpy.__version__,
                        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                        "omp_num_threads": os.environ.get("OMP_NUM_THREADS")},
        "protocol": {"cases_per_cell": CASES_PER_CELL, "repeats": REPEATS},
        "exact_verified_cases_per_method": len(rows),
        "numeric_fallback_count": sum(
            row["methods"]["direct_verified_numeric"]["fallback_count"]
            for row in rows
        ),
        "affine_family_compression_opportunity": opportunity,
        "cells": cells,
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
