"""P0.2 preregistered adversarial evaluation for set-level geometric matching.

Uses disjoint seeds, no tuning, no program synthesis, no JEPA.
Preserves P0/P0.1 receipts. Local scope only.
"""
from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from itertools import product

import numpy as np
from scipy.spatial.distance import cdist

from experiments.prh_good_views_p0 import observations, orthogonal, normalize
from experiments.prh_pairfree_geometry_p01 import fingerprints, match_pair_free

CONTRACT = {
    "schema": "neumann.prh.relation.stress.p02.v1",
    "created_for": "first-only adversarial opened-development assessment",
    "seeds": [46001, 46002, 46003, 46004],
    "items": 128,
    "dimension": 8,
    "sensor_noise_std": 0.035,
    "out_of_family_sensor_nonlinearity": "tanh(3.0*z)",
    "dropout_count": 16,
    "geometric_consistency_threshold": 0.08,
    "threshold_provenance": "chosen after P0.1 diagnostics; independent P0.2 seeds; not a P0.1 confirmatory gate",
    "gate": {
        "rotation_positive_min_recall": 0.90,
        "independent_worlds_max_false_accept": 0,
        "symmetric_sets_max_false_accept": 0,
        "dropout_fail_closed_required": True,
    },
    "new_training": False,
    "JEPA": "NOT_RUN",
    "Q1_to_Q7": "OPEN",
    "original_task_program_discovery": "NOT_RUN",
}


def symmetric_scene(seed: int) -> tuple[np.ndarray, np.ndarray]:
    d = CONTRACT["dimension"]
    # +/- orthogonal basis vectors: every item has identical distance fingerprint.
    points = np.concatenate([np.eye(d), -np.eye(d)], axis=0)
    return points @ orthogonal(seed + 11, d), points @ orthogonal(seed + 12, d)


def has_indistinguishable_fingerprints(view: np.ndarray, atol: float = 1e-10) -> bool:
    sig, _ = fingerprints(view)
    distance = cdist(sig, sig)
    np.fill_diagonal(distance, np.inf)
    return bool(np.min(distance) <= atol)


def guarded_match(x: np.ndarray, y: np.ndarray, threshold: float) -> dict:
    """Conservative degraded mode: refuse unsupported scenes, never invent pairs."""
    if x.shape != y.shape:
        return {"status": "ABSTAIN_PARTIAL_SCENE", "mapping": None}
    if has_indistinguishable_fingerprints(x) or has_indistinguishable_fingerprints(y):
        return {"status": "ABSTAIN_SYMMETRY", "mapping": None}
    result = match_pair_free(x, y)
    if result["relative_pairwise_distance_error"] > threshold:
        return {
            "status": "ABSTAIN_GEOMETRY_MISMATCH", "mapping": None,
            "relative_pairwise_distance_error": result["relative_pairwise_distance_error"],
        }
    return {
        "status": "ACCEPT_GEOMETRIC_CORRESPONDENCE", "mapping": result["mapping"],
        "relative_pairwise_distance_error": result["relative_pairwise_distance_error"],
    }


def nonlinear_observations(seed: int, count: int, noise: float) -> tuple[np.ndarray, np.ndarray]:
    d = CONTRACT["dimension"]
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(count, d))
    a, b = orthogonal(seed + 1, d), orthogonal(seed + 2, d)
    x = z @ a + rng.normal(0, noise, size=(count, d))
    y = np.tanh(3.0 * (z @ b)) + rng.normal(0, noise, size=(count, d))
    return normalize(x), normalize(y)


def evaluate(condition: str, seed: int) -> dict:
    n = CONTRACT["items"]
    d = CONTRACT["dimension"]
    noise = CONTRACT["sensor_noise_std"]
    a, b = orthogonal(seed + 1, d), orthogonal(seed + 2, d)
    if condition == "rigid_same_scene":
        x, y = observations(n, seed + 100, a, b, noise)
    elif condition == "independent_worlds":
        x, _ = observations(n, seed + 100, a, b, noise)
        _, y = observations(n, seed + 200, a, b, noise)
    elif condition == "metric_warp":
        x, y = nonlinear_observations(seed + 100, n, noise)
    elif condition == "partial_scene":
        x, full_y = observations(n, seed + 100, a, b, noise)
        y = full_y[:-CONTRACT["dropout_count"]]
    elif condition == "equidistant_symmetry":
        x, y = symmetric_scene(seed)
    else:
        raise ValueError(condition)
    rng = np.random.default_rng(seed + 301)
    permutation = rng.permutation(len(y))
    shuffled = y[permutation]
    t0 = time.perf_counter_ns()
    unguarded = None
    if x.shape == y.shape:
        unguarded = match_pair_free(x, shuffled)
    guarded = guarded_match(x, shuffled, CONTRACT["geometric_consistency_threshold"])
    duration = time.perf_counter_ns() - t0
    truth_applicable = condition in {"rigid_same_scene", "metric_warp", "equidistant_symmetry"}
    if unguarded is not None and truth_applicable:
        indexes = permutation[np.asarray(unguarded["mapping"])]
        matched = int(np.sum(indexes == np.arange(len(x))))
        recall = matched / len(x)
    else:
        matched, recall = None, None
    return {
        "condition": condition,
        "seed": seed,
        "items_a": len(x),
        "items_b": len(y),
        "unguarded_correct": matched,
        "unguarded_recall": recall,
        "unguarded_geometry_error": (unguarded["relative_pairwise_distance_error"] if unguarded else None),
        "guarded_status": guarded["status"],
        "guarded_accepted": guarded["mapping"] is not None,
        "total_wall_ns": duration,
    }


def run() -> dict:
    conditions = [
        "rigid_same_scene", "independent_worlds", "metric_warp",
        "partial_scene", "equidistant_symmetry",
    ]
    rows = [evaluate(condition, seed) for condition, seed in product(conditions, CONTRACT["seeds"])]
    def cell(name):
        return [r for r in rows if r["condition"] == name]
    g = CONTRACT["gate"]
    admitted = (
        all(r["unguarded_recall"] >= g["rotation_positive_min_recall"] and r["guarded_accepted"] for r in cell("rigid_same_scene"))
        and sum(r["guarded_accepted"] for r in cell("independent_worlds")) <= g["independent_worlds_max_false_accept"]
        and sum(r["guarded_accepted"] for r in cell("equidistant_symmetry")) <= g["symmetric_sets_max_false_accept"]
        and all(r["guarded_status"] == "ABSTAIN_PARTIAL_SCENE" for r in cell("partial_scene"))
    )
    return {
        "contract": CONTRACT,
        "rows": rows,
        "local_gate": "P02_GUARDED_RIGID_SCENES_PASS" if admitted else "P02_GUARDED_RIGID_SCENES_FAIL",
        "global_q1_to_q7": "OPEN",
        "frontier_capability_evidence": "NOT_RUN",
        "new_program_discovery_evidence": "NOT_RUN",
        "cost_telemetry": {"flops": None, "energy_joule": None, "peak_ram_bytes": None, "total_cost_usd": None},
        "environment": {"numpy": np.__version__, "python": platform.python_version()},
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"local_gate": result["local_gate"], "rows": result["rows"]}, indent=2))


if __name__ == "__main__":
    main()
