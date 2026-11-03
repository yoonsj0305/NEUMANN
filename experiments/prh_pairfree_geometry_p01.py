"""P0.1: independent-sensor pair-free matching via rigid-invariant geometry.

Independent from immutable P0 evidence. Does not use gold test pairings in matching.
Neither JEPA nor novel program synthesis; pair-free retrieval is a classical control.
"""
from __future__ import annotations

import json
import platform
import time

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist, pdist, squareform

from experiments.prh_good_views_p0 import observations, orthogonal

CONTRACT = {
    "schema": "neumann.prh.pairfree-geometry.p01.v1",
    "stage": "OPENED_DEVELOPMENT_FIRST_RUN_ONLY",
    "base_seed": 20261104,
    "dimension": 8,
    "cases_per_cell": 128,
    "observation_noise_std": 0.035,
    "gate": {"new_sensor_r1_min": 0.75, "new_sensor_sparse_r1_min": 0.50},
    "controls": ["raw-coordinate-dot-product", "independent-world-sets"],
    "new_training": False,
    "gold_pair_ids_as_input": False,
    "global_questions_closed": [],
}


def fingerprints(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if x.ndim != 2 or x.shape[0] < 3:
        raise ValueError("2D collection with >=3 items required")
    d = squareform(pdist(x, metric="euclidean"))
    return np.sort(d, axis=1), d


def match_pair_free(x: np.ndarray, y: np.ndarray) -> dict:
    """Permutation- and rotation-invariant *set-level* matching, no labels."""
    if x.shape != y.shape:
        raise ValueError("equal full-scene cardinality and dimensionality required")
    fx, dx = fingerprints(x)
    fy, dy = fingerprints(y)
    # Matching uses only the multiset of within-view distances around each item.
    cost = cdist(fx, fy, metric="euclidean")
    left, right = linear_sum_assignment(cost)
    mapping = np.empty(len(x), dtype=np.int64)
    mapping[left] = right
    # Independent geometry consistency check, not original hidden identities.
    rel_error = np.linalg.norm(dx - dy[np.ix_(mapping, mapping)]) / max(np.linalg.norm(dx), 1e-12)
    return {
        "mapping": mapping.tolist(),
        "mean_fingerprint_distance": float(np.mean(cost[np.arange(len(x)), mapping])),
        "relative_pairwise_distance_error": float(rel_error),
    }


def run() -> dict:
    p = CONTRACT
    n, d, s, noise = p["cases_per_cell"], p["dimension"], p["base_seed"], p["observation_noise_std"]
    # Each cell uses completely fresh latent draws, disjoint from P0.
    a = orthogonal(s + 1, d)
    b = orthogonal(s + 2, d)
    cells = {
        "new_sensor_iid": observations(n, s + 100, a, b, noise),
        "new_sensor_sparse": observations(n, s + 101, a, b, noise, mode="sparse"),
    }
    negx, _ = observations(n, s + 102, a, b, noise)
    _, negy = observations(n, s + 103, a, b, noise)
    cells["independent_world_sets"] = (negx, negy)
    records = {}
    for key, (x, y) in cells.items():
        permutation = np.random.default_rng(s + 777).permutation(n)
        shuffled = y[permutation]
        t0 = time.perf_counter_ns()
        predicted = match_pair_free(x, shuffled)
        cost_ns = time.perf_counter_ns() - t0
        ground_truth_index = permutation[np.asarray(predicted["mapping"])]
        good_count = int(np.sum(ground_truth_index == np.arange(n))) if key != "independent_world_sets" else None
        raw_mapping = np.argmax(x @ shuffled.T, axis=1)
        raw_good = int(np.sum(permutation[raw_mapping] == np.arange(n))) if key != "independent_world_sets" else None
        records[key] = {
            "pairfree_correct": good_count,
            "pairfree_r1": (good_count / n) if good_count is not None else None,
            "raw_coordinate_correct": raw_good,
            "raw_coordinate_r1": (raw_good / n) if raw_good is not None else None,
            "geometry_consistency_error": predicted["relative_pairwise_distance_error"],
            "mean_fingerprint_distance": predicted["mean_fingerprint_distance"],
            "complete_pairfree_wall_ns": cost_ns,
            "candidate_count": n,
        }
    passed = (records["new_sensor_iid"]["pairfree_r1"] >= p["gate"]["new_sensor_r1_min"]
              and records["new_sensor_sparse"]["pairfree_r1"] >= p["gate"]["new_sensor_sparse_r1_min"])
    return {
        "contract": p,
        "result": "P01_RELATIONAL_ALIGNMENT_LOCAL_PASS" if passed else "P01_RELATIONAL_ALIGNMENT_LOCAL_FAIL",
        "cells": records,
        "q1_to_q7": "OPEN",
        "jepa_training": "NOT_RUN",
        "new_executable_program": "NOT_DISCOVERED",
        "independent_task_verification": "NOT_RUN",
        "energy_joule": None,
        "peak_memory_bytes": None,
        "flops": None,
        "cost_usd": None,
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
    }


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"result": result["result"], "cells": result["cells"]}, indent=2))
