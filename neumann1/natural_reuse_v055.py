"""External unmodified-matrix opportunity audit and abstaining reuse gate.

No corpus files are shipped with the package. The full source-family selection,
hashes, candidate, and decision are frozen before the first full audit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from random import Random
from time import perf_counter_ns

import numpy as np
from scipy.io import mmread
from scipy.sparse import csr_matrix, issparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

from neumann1.numeric_order_v052 import original_residual


# NIST Harwell–Boeing BCSSTRUC1: all 13 K/stiffness matrices, ordered by name.
MATRICES = {
    "bcsstk01": (48, "567560f75b952d9c14c0d193ded5d80370d7ca26fe49f9e67deee55f22e55699"),
    "bcsstk02": (66, "cd27f10160c063ae16d07ec99efa61c02b83bb5689ef5009985194d2e59c238a"),
    "bcsstk03": (112, "af8c2febc38a88016b1726fbd0e6dff310b13a47fe81a036ee14604d5b846323"),
    "bcsstk04": (132, "11aa7f961f13eb47752e7f7dddaa5ffb3213c0158ef8bb1f30cae59088771694"),
    "bcsstk05": (153, "f69d081ee645980a230909473991f5d5edfd3ee1c1637c5dceb3b7a174705eb3"),
    "bcsstk06": (420, "a1cc30e594d4d20d89d7132b517741082d3f3b3501e7e4839142acf4dc1f24d1"),
    "bcsstk07": (420, "046c84c4004af525ded737bcc0946ff5f336e011077da37af7740c0d8a6a3a92"),
    "bcsstk08": (1074, "5945836beb24009e8a94b58242d9b5c6cfd261117595898149d3fa9c99c084f7"),
    "bcsstk09": (1083, "4688c5c78f72e369316796a73cf8e8d9c014d50478285698e40706811472ea5c"),
    "bcsstk10": (1086, "4509c305bf1ac80ddeb749530dff43591595a3c8c486603911d71c8f97854c6d"),
    "bcsstk11": (1473, "9e045576f4332f9ace5760317654869157b9d90954db4cdee72eb29d9354cc46"),
    "bcsstk12": (1473, "8b5ce9bf6f78b6f5c2693e9c70e0554ef5273753bf246c8237d616e1283b049a"),
    "bcsstk13": (2003, "4cc1206dce6081cd72065368f28c7beb093786c215f88c9d56b0dd6451779646"),
}
POLICIES = ("NATURAL", "COLAMD", "GATED_REUSE")


def load_pinned(path: Path, name: str) -> csr_matrix:
    expected_n, expected_hash = MATRICES[name]
    if sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError(f"original gzip SHA-256 mismatch: {name}")
    matrix = mmread(path)
    if not issparse(matrix) or matrix.shape != (expected_n, expected_n):
        raise ValueError(f"format/shape mismatch: {name}")
    matrix = matrix.tocsr().astype(np.float64)
    matrix.sum_duplicates()
    matrix.sort_indices()
    if not np.isfinite(matrix.data).all() or (matrix - matrix.T).nnz:
        raise ValueError(f"nonsymmetric or nonfinite: {name}")
    return matrix


def _key(part: csr_matrix) -> bytes:
    return sha256(part.indptr.tobytes() + part.indices.tobytes() +
                  part.data.tobytes() + str(part.shape).encode()).digest()


def _equal(left: csr_matrix, right: csr_matrix) -> bool:
    return (left.shape == right.shape and np.array_equal(left.indptr, right.indptr)
            and np.array_equal(left.indices, right.indices)
            and np.array_equal(left.data, right.data))


def detect_repeats(matrix: csr_matrix) -> tuple[list[tuple[np.ndarray, csr_matrix, int]], int]:
    count, labels = connected_components(matrix, directed=False)
    if count == 1:
        return [], 1  # No extraction/hash required for the default path.
    representatives: dict[bytes, list[tuple[csr_matrix, int]]] = {}
    parts = []
    for i in range(count):
        indices = np.flatnonzero(labels == i)
        part = matrix[indices, :][:, indices].tocsr()
        part.sort_indices()
        key = _key(part)
        match = next((candidate for candidate in representatives.get(key, [])
                      if _equal(candidate[0], part)), None)
        if match is None:
            representative = i
            representatives.setdefault(key, []).append((part, i))
        else:
            representative = match[1]
        parts.append((indices, part, representative))
    return parts, sum(len(bucket) for bucket in representatives.values())


@dataclass(frozen=True)
class Trial:
    policy: str
    total_ns: int
    gate_ns: int
    components: int
    distinct_blocks: int
    factorizations: int
    backward_error: float
    solution_error: float
    valid: bool


def run_trial(matrix: csr_matrix, rhs: np.ndarray, truth: np.ndarray,
              policy: str) -> Trial:
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    start = perf_counter_ns()
    gate_ns = 0
    components = distinct = 1
    if policy == "GATED_REUSE":
        parts, distinct = detect_repeats(matrix)
        components = len(parts) if parts else 1
        gate_ns = perf_counter_ns() - start
    if policy != "GATED_REUSE" or distinct == components:
        # Explicit abstention: the entire original system uses the fixed
        # NATURAL fallback. The candidate pays the scan before this path.
        native_policy = policy if policy != "GATED_REUSE" else "NATURAL"
        factor = splu(matrix.tocsc(), permc_spec=native_policy)
        x = factor.solve(rhs)
        factorizations = 1
    else:
        cache = {}
        x = np.empty_like(rhs)
        factorizations = 0
        for indices, part, representative in parts:
            if representative not in cache:
                cache[representative] = splu(part.tocsc(), permc_spec="NATURAL")
                factorizations += 1
            x[indices] = cache[representative].solve(rhs[indices])
    backward, solution = original_residual(matrix, x, rhs, truth)
    total_ns = perf_counter_ns() - start
    valid = bool(np.isfinite(backward) and np.isfinite(solution)
                 and backward <= 1e-10 and solution <= 1e-7)
    return Trial(policy, total_ns, gate_ns, components, distinct, factorizations,
                 backward, solution, valid)


def audit_case(matrix: csr_matrix, name: str) -> dict:
    if name not in MATRICES:
        raise ValueError("outside pinned corpus")
    truth = np.sin(np.arange(matrix.shape[0], dtype=np.float64) + 1)
    rhs = matrix @ truth
    for policy in POLICIES:
        if not run_trial(matrix, rhs, truth, policy).valid:
            raise ValueError(f"warmup failed: {name}/{policy}")
    rows = {policy: [] for policy in POLICIES}
    for repetition in range(7):
        policies = list(POLICIES)
        Random(55 + list(MATRICES).index(name) * 100 + repetition).shuffle(policies)
        for policy in policies:
            trial = run_trial(matrix, rhs, truth, policy)
            if not trial.valid:
                raise ValueError(f"original verification failed: {name}/{policy}/{repetition}")
            rows[policy].append(asdict(trial))
    medians = {p: float(np.median([row["total_ns"] for row in rows[p]])) for p in POLICIES}
    observed = rows["GATED_REUSE"][0]
    if any((r["components"], r["distinct_blocks"]) !=
           (observed["components"], observed["distinct_blocks"])
           for r in rows["GATED_REUSE"]):
        raise ValueError("nondeterministic repeat detection")
    best_native = min(medians["NATURAL"], medians["COLAMD"])
    return {"name": name, "n": matrix.shape[0], "nnz": matrix.nnz,
            "components": observed["components"], "distinct_blocks": observed["distinct_blocks"],
            "rows": rows, "median_total_ns": medians,
            "gate_vs_natural": (medians["NATURAL"] - medians["GATED_REUSE"]) / medians["NATURAL"],
            "gate_vs_best_native_diagnostic": (best_native - medians["GATED_REUSE"]) / best_native}


def cross_file_exact_groups(matrices: dict[str, csr_matrix]) -> list[list[str]]:
    """Descriptive corpus-level recurrence; no stream cache is timed here."""
    seen: dict[bytes, list[tuple[str, csr_matrix]]] = {}
    groups = []
    for name in MATRICES:
        matrix = matrices[name]
        key = _key(matrix)
        match = next((entry for entry in seen.get(key, []) if _equal(entry[1], matrix)), None)
        if match is None:
            seen.setdefault(key, []).append((name, matrix))
            groups.append([name])
        else:
            next(group for group in groups if group[0] == match[0]).append(name)
    return groups


def summarize(cases: list[dict]) -> dict:
    if [c["name"] for c in cases] != list(MATRICES):
        raise ValueError("missing or reordered original matrices")
    repeated = [c for c in cases if c["distinct_blocks"] < c["components"]]
    winners = [c for c in repeated if c["gate_vs_best_native_diagnostic"] >= 0.20]
    abstention_regressions = sum(c["gate_vs_natural"] < -0.10 for c in cases
                                 if c["distinct_blocks"] == c["components"])
    passed = len(winners) >= 2 and abstention_regressions == 0
    return {"criterion": ">=2 natural repeated matrices with >=20% win vs best native, no >10% abstention regression",
            "repeated_matrices": len(repeated), "qualifying_winners": len(winners),
            "abstention_regressions_gt_10pct": abstention_regressions,
            "decision": "NATURAL_REUSE_OPPORTUNITY_VISIBLE" if passed else "NO_NATURAL_REUSE_OPPORTUNITY"}
