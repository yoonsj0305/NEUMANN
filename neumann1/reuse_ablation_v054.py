"""Separate component splitting from exact numeric factorization reuse."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from random import Random
from time import perf_counter_ns

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

from neumann1.numeric_order_v052 import original_residual
from neumann1.repeated_matrix_v053 import BASES, COPIES, interleaved_replicas


POLICIES = ("SPLIT_NO_REUSE", "EXACT_REUSE")


def discover(matrix: csr_matrix) -> list[tuple[np.ndarray, csr_matrix]]:
    count, labels = connected_components(matrix, directed=False)
    parts = []
    for i in range(count):
        indices = np.flatnonzero(labels == i)
        part = matrix[indices, :][:, indices].tocsr()
        part.sort_indices()
        parts.append((indices, part))
    return parts


def _key(part: csr_matrix) -> bytes:
    return sha256(part.indptr.tobytes() + part.indices.tobytes() +
                  part.data.tobytes() + str(part.shape).encode()).digest()


def _same(a: csr_matrix, b: csr_matrix) -> bool:
    return (a.shape == b.shape and np.array_equal(a.indptr, b.indptr) and
            np.array_equal(a.indices, b.indices) and np.array_equal(a.data, b.data))


@dataclass(frozen=True)
class Trial:
    policy: str
    total_ns: int
    discovery_ns: int
    factorizations: int
    total_factor_nnz: int
    backward_error: float
    solution_error: float
    valid: bool


def run_trial(matrix: csr_matrix, rhs: np.ndarray, truth: np.ndarray,
              policy: str) -> Trial:
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    start = perf_counter_ns()
    parts = discover(matrix)
    discovery_ns = perf_counter_ns() - start
    # SPLIT is not charged for the reuse path's hashing or equality checks.
    cache: dict[bytes, list[tuple[csr_matrix, object]]] = {}
    x = np.empty_like(rhs)
    factors, factor_nnz = 0, 0
    for indices, part in parts:
        factor = None
        key = None
        if policy == "EXACT_REUSE":
            key = _key(part)
            match = next((entry for entry in cache.get(key, []) if _same(entry[0], part)), None)
            if match is not None:
                factor = match[1]
        if factor is None:
            factor = splu(part.tocsc(), permc_spec="NATURAL")
            factors += 1
            factor_nnz += factor.L.nnz + factor.U.nnz
            if policy == "EXACT_REUSE":
                cache.setdefault(key, []).append((part, factor))
        x[indices] = factor.solve(rhs[indices])
    backward, solution = original_residual(matrix, x, rhs, truth)
    elapsed = perf_counter_ns() - start
    valid = bool(np.isfinite(backward) and np.isfinite(solution) and
                 backward <= 1e-10 and solution <= 1e-7)
    return Trial(policy, elapsed, discovery_ns, factors, factor_nnz,
                 backward, solution, valid)


def audit_case(base: csr_matrix, name: str, copies: int) -> dict:
    if name not in BASES or copies not in COPIES:
        raise ValueError("outside frozen protocol")
    matrix, rhs, truth = interleaved_replicas(base, copies)
    for policy in POLICIES:
        if not run_trial(matrix, rhs, truth, policy).valid:
            raise ValueError("warmup verification failed")
    rows = {policy: [] for policy in POLICIES}
    for repeat in range(7):
        policies = list(POLICIES)
        Random(54 + BASES.index(name) * 1000 + copies * 10 + repeat).shuffle(policies)
        for policy in policies:
            trial = run_trial(matrix, rhs, truth, policy)
            if not trial.valid or trial.factorizations != (1 if policy == "EXACT_REUSE" else copies):
                raise ValueError(f"verification or factor count failed: {name}/{copies}/{policy}/{repeat}")
            rows[policy].append(asdict(trial))
    medians = {p: float(np.median([r["total_ns"] for r in rows[p]])) for p in POLICIES}
    return {"name": name, "copies": copies, "n": matrix.shape[0], "nnz": matrix.nnz,
            "rows": rows, "median_total_ns": medians,
            "reuse_vs_split": (medians["SPLIT_NO_REUSE"]-medians["EXACT_REUSE"])
                              / medians["SPLIT_NO_REUSE"]}


def summarize(cases: list[dict]) -> dict:
    if [(c["name"], c["copies"]) for c in cases] != [(n, k) for n in BASES for k in COPIES]:
        raise ValueError("missing or reordered cases")
    wins = sum(c["reuse_vs_split"] >= 0.20 for c in cases if c["copies"] in (8, 16))
    return {"criterion": "EXACT_REUSE >=20% faster than SPLIT_NO_REUSE on >=3/4 k=8,16 cases",
            "qualifying_large_cases": wins,
            "decision": "REUSE_MECHANISM_SUPPORTED" if wins >= 3 else "REUSE_MECHANISM_NOT_SUPPORTED"}
