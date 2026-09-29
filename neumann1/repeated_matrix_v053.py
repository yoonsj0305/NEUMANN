"""Exact repeated-component reuse on interleaved copies of real matrices."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from random import Random
from time import perf_counter_ns

import numpy as np
from scipy.sparse import csr_matrix, eye, kron
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

from neumann1.numeric_order_v052 import original_residual


BASES = ("bcsstk05", "bcsstk09")
COPIES = (1, 2, 4, 8, 16)
POLICIES = ("NATURAL", "COLAMD", "REUSE")


def interleaved_replicas(base: csr_matrix, copies: int) -> tuple[csr_matrix, np.ndarray, np.ndarray]:
    if copies not in COPIES:
        raise ValueError("unregistered copy count")
    # Vertex i of copy j is at i*copies+j; component labels remain interleaved.
    matrix = kron(base, eye(copies, format="csr"), format="csr")
    truth = np.empty(matrix.shape[0], dtype=np.float64)
    for j in range(copies):
        truth[j::copies] = np.sin(np.arange(base.shape[0]) * 0.03 + j * 0.17 + 1)
    return matrix, matrix @ truth, truth


def _fingerprint(matrix: csr_matrix) -> bytes:
    return sha256(matrix.indptr.tobytes() + matrix.indices.tobytes() +
                  matrix.data.tobytes() + str(matrix.shape).encode()).digest()


def _equal(left: csr_matrix, right: csr_matrix) -> bool:
    return (left.shape == right.shape and np.array_equal(left.indptr, right.indptr)
            and np.array_equal(left.indices, right.indices)
            and np.array_equal(left.data, right.data))


@dataclass(frozen=True)
class Trial:
    policy: str
    total_ns: int
    discovery_ns: int
    unique_factors: int
    factor_nnz: int
    backward_error: float
    solution_error: float
    valid: bool


def run_trial(matrix: csr_matrix, rhs: np.ndarray, truth: np.ndarray,
              policy: str) -> Trial:
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    start = perf_counter_ns()
    discovery_ns = 0
    if policy != "REUSE":
        factor = splu(matrix.tocsc(), permc_spec=policy)
        x = factor.solve(rhs)
        factors, factor_nnz = 1, factor.L.nnz + factor.U.nnz
    else:
        discovery_start = perf_counter_ns()
        components, labels = connected_components(matrix, directed=False)
        groups = [np.flatnonzero(labels == i) for i in range(components)]
        seen: dict[bytes, list[tuple[csr_matrix, int]]] = {}
        jobs = []
        factor_nnz = 0
        for indices in groups:
            part = matrix[indices, :][:, indices].tocsr()
            part.sort_indices()
            key = _fingerprint(part)
            match = next((entry for entry in seen.get(key, []) if _equal(entry[0], part)), None)
            if match is None:
                representative = len(jobs)
                seen.setdefault(key, []).append((part, representative))
            else:
                representative = match[1]
            jobs.append((indices, part, representative))
        discovery_ns = perf_counter_ns() - discovery_start
        x = np.empty_like(rhs)
        factors = 0
        factor_cache = {}
        for indices, part, representative in jobs:
            if representative not in factor_cache:
                factor = splu(part.tocsc(), permc_spec="NATURAL")
                factor_cache[representative] = factor
                factors += 1
                factor_nnz += factor.L.nnz + factor.U.nnz
            else:
                factor = factor_cache[representative]
            x[indices] = factor.solve(rhs[indices])
    backward, solution = original_residual(matrix, x, rhs, truth)
    elapsed = perf_counter_ns() - start
    valid = bool(np.isfinite(backward) and np.isfinite(solution) and
                 backward <= 1e-10 and solution <= 1e-7)
    return Trial(policy, elapsed, discovery_ns, factors, factor_nnz,
                 backward, solution, valid)


def audit_case(base: csr_matrix, name: str, copies: int, repeats: int = 7) -> dict:
    if name not in BASES or copies not in COPIES or repeats != 7:
        raise ValueError("outside frozen protocol")
    matrix, rhs, truth = interleaved_replicas(base, copies)
    for policy in POLICIES:
        if not run_trial(matrix, rhs, truth, policy).valid:
            raise ValueError(f"warmup verification failed: {name}/{copies}/{policy}")
    rows = {policy: [] for policy in POLICIES}
    for repeat in range(repeats):
        policies = list(POLICIES)
        Random(53 + BASES.index(name) * 1000 + copies * 10 + repeat).shuffle(policies)
        for policy in policies:
            trial = run_trial(matrix, rhs, truth, policy)
            if not trial.valid:
                raise ValueError(f"original verification failed: {name}/{copies}/{policy}/{repeat}")
            rows[policy].append(asdict(trial))
    medians = {p: float(np.median([row["total_ns"] for row in rows[p]])) for p in POLICIES}
    return {"name": name, "copies": copies, "n": matrix.shape[0], "nnz": matrix.nnz,
            "rows": rows, "median_total_ns": medians,
            "reuse_vs_natural": (medians["NATURAL"]-medians["REUSE"])/medians["NATURAL"],
            "reuse_vs_best_native_diagnostic":
                (min(medians["NATURAL"], medians["COLAMD"])-medians["REUSE"])
                / min(medians["NATURAL"], medians["COLAMD"])}


def summarize(cases: list[dict]) -> dict:
    if [(c["name"], c["copies"]) for c in cases] != [(n, k) for n in BASES for k in COPIES]:
        raise ValueError("missing or reordered cases")
    large = [c for c in cases if c["copies"] in (8, 16)]
    wins = sum(c["reuse_vs_natural"] >= 0.20 for c in large)
    return {"criterion": "REUSE >=20% faster than fixed NATURAL on >=3/4 cases at k=8,16",
            "qualifying_large_cases": wins,
            "decision": "REUSE_OPPORTUNITY_VISIBLE" if wins >= 3 else "NO_REUSE_OPPORTUNITY"}
