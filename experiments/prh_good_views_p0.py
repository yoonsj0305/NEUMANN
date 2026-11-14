"""NEUMANN P0: falsifiable, CPU-only probe of good-view alignment.

This is *not* a JEPA implementation or proof of program discovery.  It tests
whether positive-pair provenance alone can align independent observations,
and whether a cheaper exact linear method exhausts this constructed case.

No model sees hidden latent states or evaluation pairing labels.  Each test
query is matched against the full, permuted candidate pool.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

SCHEMA = "neumann.prh.good-views.p0.v1"
CONTRACT = {
    "schema": SCHEMA,
    "scope": "synthetic-alignment-mechanism-only",
    "prior_global_gates": {f"Q{i}": "OPEN" for i in range(1, 8)},
    "model": "orthogonal-procrustes-closed-form-no-NN",
    "train_pairs": 512,
    "eval_cases_per_cell": 128,
    "dimension": 8,
    "observation_noise_std": 0.035,
    "base_seed": 20261103,
    "cell_names": ["iid", "sparse-structure", "new-sensor"],
    "controls": ["raw-unrotated", "unrelated-pairing", "same-view-corruption"],
    "gate": {
        "iid_retrieval_r1_min": 0.80,
        "iid_good_minus_unrelated_min": 0.50,
        "sparse_retrieval_r1_min": 0.50,
        "new_sensor_is_diagnostic_only": True,
    },
    "is_not": [
        "JEPA/LeJEPA reproducibility",
        "oracle-free executable program discovery",
        "Q3/Q4/Q5/Q6/Q7 closure",
        "frontier-gap evidence",
    ],
}


def orthogonal(seed: int, dimension: int) -> np.ndarray:
    """Create deterministic orthogonal sensor frame; fix QR sign ambiguity."""
    rng = np.random.default_rng(seed)
    q, r = np.linalg.qr(rng.standard_normal((dimension, dimension)))
    return q @ np.diag(np.where(np.diag(r) < 0, -1.0, 1.0))


def normalize(x: np.ndarray) -> np.ndarray:
    length = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(length < 1e-12):
        raise ValueError("degenerate view")
    return x / length


def observations(count: int, seed: int, left: np.ndarray, right: np.ndarray,
                 noise: float, *, mode: str = "iid") -> tuple[np.ndarray, np.ndarray]:
    """Return independent sensors of the same unobserved state, no state labels."""
    rng = np.random.default_rng(seed)
    dim = left.shape[0]
    latent = rng.normal(size=(count, dim))
    if mode == "sparse":
        mask = np.zeros_like(latent)
        chosen = np.argsort(np.abs(latent), axis=1)[:, -2:]
        np.put_along_axis(mask, chosen, 1.0, axis=1)
        latent *= mask
    elif mode != "iid":
        raise ValueError("invalid latent mode")
    # Dissimilar measurement errors are genuinely independent per sensor.
    a = latent @ left + rng.normal(0, noise, (count, dim))
    b = latent @ right + rng.normal(0, noise, (count, dim))
    return normalize(a), normalize(b)


def procrustes(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Best single orthogonal rotation, learned without latent labels."""
    if left.shape != right.shape or left.ndim != 2:
        raise ValueError("matched 2D training pairs required")
    u, _, vt = np.linalg.svd(left.T @ right, full_matrices=False)
    return u @ vt


def top1(left: np.ndarray, right: np.ndarray, rotation: np.ndarray,
         *, permutation_seed: int) -> dict:
    """Full-pool retrieval without giving candidate identities to encoder."""
    rng = np.random.default_rng(permutation_seed)
    perm = rng.permutation(len(right))
    similarities = (left @ rotation) @ right[perm].T
    winners = np.argmax(similarities, axis=1)
    actual = perm[winners]
    successes = int(np.sum(actual == np.arange(len(left))))
    return {"correct": successes, "total": len(left), "recall_at_1": successes / len(left)}


def run() -> dict:
    p = CONTRACT
    n, dim, seed, noise = (p["train_pairs"], p["dimension"], p["base_seed"],
                           p["observation_noise_std"])
    sensor_a, sensor_b = orthogonal(seed + 1, dim), orthogonal(seed + 2, dim)
    x, y = observations(n, seed + 3, sensor_a, sensor_b, noise)
    t0 = time.perf_counter_ns()
    good = procrustes(x, y)
    good_fit_ns = time.perf_counter_ns() - t0
    rng = np.random.default_rng(seed + 4)
    unrelated = procrustes(x, y[rng.permutation(n)])
    bad_view = procrustes(x, normalize(x + rng.normal(0, noise, x.shape)))

    # Freeze distinct unseen test draws; no fitting on any of these arrays.
    cells = {
        "iid": observations(p["eval_cases_per_cell"], seed + 101,
                            sensor_a, sensor_b, noise),
        "sparse-structure": observations(p["eval_cases_per_cell"], seed + 102,
                                         sensor_a, sensor_b, noise, mode="sparse"),
        "new-sensor": observations(p["eval_cases_per_cell"], seed + 103,
                                   sensor_a, orthogonal(seed + 104, dim), noise),
    }
    outcomes = {}
    for k, (left, right) in cells.items():
        t0 = time.perf_counter_ns()
        outcomes[k] = {
            "good_views": top1(left, right, good, permutation_seed=seed + 110),
            "raw_unrotated": top1(left, right, np.eye(dim), permutation_seed=seed + 110),
            "unrelated_pairing": top1(left, right, unrelated, permutation_seed=seed + 110),
            "same_view_corruption": top1(left, right, bad_view, permutation_seed=seed + 110),
        }
        outcomes[k]["whole_cell_eval_ns"] = time.perf_counter_ns() - t0

    gate = p["gate"]
    iid = outcomes["iid"]
    passed = (
        iid["good_views"]["recall_at_1"] >= gate["iid_retrieval_r1_min"]
        and iid["good_views"]["recall_at_1"] - iid["unrelated_pairing"]["recall_at_1"]
        >= gate["iid_good_minus_unrelated_min"]
        and outcomes["sparse-structure"]["good_views"]["recall_at_1"]
        >= gate["sparse_retrieval_r1_min"]
    )
    return {
        "contract": p,
        "test_result": "P0_ALIGNMENT_MECHANISM_PASS" if passed else "P0_ALIGNMENT_MECHANISM_FAIL",
        "q1_to_q7": "OPEN",
        "cells": outcomes,
        "measured_fit_ns": good_fit_ns,
        "fit_examples": n,
        "latency_note": "CPU perf_counter_ns, wall-clock only; not hardware energy or FLOPs",
        "energy_joule": None,
        "flops": None,
        "peak_ram_bytes": None,
        "gpu_vram_bytes": None,
        "monetary_cost_usd": None,
        "platform": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "interpretation": "P0 tests cross-view alignment. Classical Procrustes is a strong lower-cost comparator; no neural model, new program or frontier claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None,
                        help="Write machine-readable evidence without replacing an existing file")
    args = parser.parse_args()
    result = run()
    message = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf8") as f:
            f.write(message)
    print(message)


if __name__ == "__main__":
    main()
