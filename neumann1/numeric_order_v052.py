"""Pinned real-matrix ordering audit with original-equation verification.

The module is an experiment, not a runtime route or a compression claim.
External Matrix Market inputs are never packaged with NEUMANN.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from random import Random
from time import perf_counter_ns

import numpy as np
from scipy.io import mmread
from scipy.sparse import csc_matrix, csr_matrix, issparse
from scipy.sparse.csgraph import reverse_cuthill_mckee
from scipy.sparse.linalg import splu


MATRICES = {
    "bcsstk05": (153, "f69d081ee645980a230909473991f5d5edfd3ee1c1637c5dceb3b7a174705eb3"),
    "bcsstk06": (420, "a1cc30e594d4d20d89d7132b517741082d3f3b3501e7e4839142acf4dc1f24d1"),
    "bcsstk09": (1083, "4688c5c78f72e369316796a73cf8e8d9c014d50478285698e40706811472ea5c"),
    "bcsstk10": (1086, "4509c305bf1ac80ddeb749530dff43591595a3c8c486603911d71c8f97854c6d"),
}
NATIVE = ("COLAMD", "MMD_AT_PLUS_A", "MMD_ATA", "NATURAL")
POLICIES = (*NATIVE, "RCM")
BACKWARD_TOL = 1e-10
SOLUTION_TOL = 1e-7


def load_pinned(path: Path, name: str) -> csr_matrix:
    expected_n, expected_hash = MATRICES[name]
    if sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError(f"original compressed file checksum mismatch: {name}")
    matrix = mmread(path)
    if not issparse(matrix) or matrix.shape != (expected_n, expected_n):
        raise ValueError(f"matrix format or shape mismatch: {name}")
    matrix = matrix.tocsr().astype(np.float64)
    matrix.sum_duplicates()
    if not np.isfinite(matrix.data).all() or (matrix - matrix.T).nnz:
        raise ValueError(f"nonfinite or nonsymmetric matrix: {name}")
    return matrix


def original_residual(matrix: csr_matrix, x: np.ndarray, rhs: np.ndarray,
                      truth: np.ndarray) -> tuple[float, float]:
    """Original, unpermuted equation and known-solution checks."""
    residual = matrix @ x - rhs
    row_norm = np.asarray(abs(matrix).sum(axis=1)).ravel().max()
    denominator = row_norm * np.linalg.norm(x, ord=np.inf) + np.linalg.norm(rhs, ord=np.inf)
    backward = float(np.linalg.norm(residual, ord=np.inf) / denominator)
    solution = float(np.linalg.norm(x - truth, ord=np.inf) /
                     np.linalg.norm(truth, ord=np.inf))
    return backward, solution


@dataclass(frozen=True)
class Trial:
    policy: str
    total_ns: int
    order_ns: int
    factor_nnz: int
    backward_error: float
    solution_error: float
    valid: bool


def run_trial(matrix: csr_matrix, rhs: np.ndarray, truth: np.ndarray,
              policy: str) -> Trial:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    start = perf_counter_ns()
    order_ns = 0
    if policy == "RCM":
        order_start = perf_counter_ns()
        order = reverse_cuthill_mckee(matrix, symmetric_mode=True)
        permuted = matrix[order, :][:, order].tocsc()
        order_ns = perf_counter_ns() - order_start
        factor = splu(permuted, permc_spec="NATURAL")
        permuted_x = factor.solve(rhs[order])
        x = np.empty_like(permuted_x)
        x[order] = permuted_x
    else:
        factor = splu(csc_matrix(matrix), permc_spec=policy)
        x = factor.solve(rhs)
    backward, solution = original_residual(matrix, x, rhs, truth)
    elapsed = perf_counter_ns() - start
    valid = bool(np.isfinite(backward) and np.isfinite(solution) and
                 backward <= BACKWARD_TOL and solution <= SOLUTION_TOL)
    return Trial(policy, elapsed, order_ns, factor.L.nnz + factor.U.nnz,
                 backward, solution, valid)


def audit_matrix(matrix: csr_matrix, name: str, repeats: int = 7) -> dict:
    if repeats != 7:
        raise ValueError("first-audit protocol requires seven paired repetitions")
    truth = np.sin(np.arange(matrix.shape[0], dtype=np.float64) + 1)
    rhs = matrix @ truth
    # Warmups are discarded; complete paths still check the original problem.
    for policy in POLICIES:
        if not run_trial(matrix, rhs, truth, policy).valid:
            raise ValueError(f"warmup verification failed: {name}/{policy}")
    rows = {policy: [] for policy in POLICIES}
    for repeat in range(repeats):
        order = list(POLICIES)
        Random(52 + list(MATRICES).index(name) * 100 + repeat).shuffle(order)
        for policy in order:
            trial = run_trial(matrix, rhs, truth, policy)
            if not trial.valid:
                raise ValueError(f"original-equation verification failed: {name}/{policy}/{repeat}")
            rows[policy].append(asdict(trial))
    medians = {policy: float(np.median([row["total_ns"] for row in trials]))
               for policy, trials in rows.items()}
    strongest_native = min(medians[policy] for policy in NATIVE if policy != "NATURAL")
    return {
        "name": name, "n": matrix.shape[0], "nnz": matrix.nnz,
        "rows": rows, "median_total_ns": medians,
        "rcm_improvement_vs_best_native": (strongest_native - medians["RCM"]) / strongest_native,
        "rcm_improvement_vs_colamd": (medians["COLAMD"] - medians["RCM"]) / medians["COLAMD"],
    }


def summarize(cases: list[dict]) -> dict:
    if len(cases) != len(MATRICES) or [c["name"] for c in cases] != list(MATRICES):
        raise ValueError("missing or reordered pinned cases")
    wins = sum(c["rcm_improvement_vs_best_native"] >= 0.20 for c in cases)
    return {"criterion": "RCM >=20% faster than best native median on >=2/4",
            "qualifying_cases": wins,
            "decision": "DETERMINISTIC_OPPORTUNITY_VISIBLE" if wins >= 2 else "NO_RCM_OPPORTUNITY"}
