"""Hash-pinned MATPOWER case118 DC N-1 reuse mechanism audit.

This is classical rank-one factorization reuse, not a novel power-flow method.
Case data are supplied externally and are not redistributed by NEUMANN.
"""

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter

import numpy as np
import scipy
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import splu


CASE_SHA256 = "bc2e6f22b4b9e776572885ee4b50e4f4ab2ee0c5577e9126e86d906f14c4b5f7"


@dataclass(frozen=True)
class Grid:
    start: np.ndarray
    end: np.ndarray
    weight: np.ndarray
    injections: np.ndarray
    reference: int


def _table(text, field):
    match = re.search(r"mpc\." + field + r"\s*=\s*\[([^\]]+)\];", text)
    if not match:
        raise ValueError(f"missing {field} table")
    lines = [line.split("%", 1)[0].strip().rstrip(";")
             for line in match.group(1).splitlines()]
    rows = [[float(x) for x in line.split()] for line in lines if line]
    result = np.asarray(rows)
    if result.ndim != 2 or not np.isfinite(result).all():
        raise ValueError(f"invalid {field} table")
    return result


def load_case(path: Path):
    content = path.read_bytes()
    if sha256(content).hexdigest() != CASE_SHA256:
        raise ValueError("case118 source hash mismatch")
    text = content.decode("ascii")
    bus, branch, gen = (_table(text, name) for name in ("bus", "branch", "gen"))
    base = re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)\s*;", text)
    if (not base or bus.shape != (118, 13) or branch.shape != (186, 13)
            or gen.shape[1] < 10 or not np.array_equal(bus[:, 0], np.arange(1, 119))
            or np.sum(bus[:, 1] == 3) != 1 or np.any(branch[:, 10] != 1)
            or np.any(branch[:, 3] <= 0) or np.any(branch[:, 9] != 0)
            or np.any(gen[:, 7] != 1)):
        raise ValueError("unsupported DC case interface")
    f, t = branch[:, :2].astype(int).T - 1
    if np.any(f < 0) or np.any(t < 0) or np.any(f >= 118) or np.any(t >= 118):
        raise ValueError("branch endpoint outside bus table")
    taps = np.where(branch[:, 8] == 0, 1.0, branch[:, 8])
    if np.any(taps <= 0):
        raise ValueError("invalid transformer tap")
    injection = -bus[:, 2].copy()
    np.add.at(injection, gen[:, 0].astype(int) - 1, gen[:, 1])
    return Grid(f, t, 1.0 / (branch[:, 3] * taps),
                injection / float(base.group(1)), int(np.flatnonzero(bus[:, 1] == 3)[0]))


def _incidence(grid):
    n, m = len(grid.injections), len(grid.weight)
    nodes = [i for i in range(n) if i != grid.reference]
    mapping = np.full(n, -1, dtype=int)
    mapping[nodes] = np.arange(n - 1)
    rows = np.repeat(np.arange(m), 2)
    cols = mapping[np.column_stack((grid.start, grid.end)).ravel()]
    values = np.tile([1.0, -1.0], m)
    valid = cols >= 0
    return coo_matrix((values[valid], (rows[valid], cols[valid])),
                      shape=(m, n - 1)).tocsr(), np.asarray(nodes)


def _connected_outages(grid):
    n = len(grid.injections)
    good = []
    for outage in range(len(grid.weight)):
        adjacency = [[] for _ in range(n)]
        for k, (u, v) in enumerate(zip(grid.start, grid.end)):
            if k != outage:
                adjacency[u].append(v)
                adjacency[v].append(u)
        seen = {grid.reference}
        stack = [grid.reference]
        while stack:
            for v in adjacency[stack.pop()]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        if len(seen) == n:
            good.append(outage)
    return good


def _verify(grid, theta, outage):
    """Scatter original surviving branch flows, independently of sparse LPs."""
    if not np.isfinite(theta).all() or abs(theta[grid.reference]) > 1e-12:
        raise ValueError("invalid restored angles")
    flow = grid.weight * (theta[grid.start] - theta[grid.end])
    flow[outage] = 0.0
    balance = np.zeros(len(theta))
    np.add.at(balance, grid.start, flow)
    np.add.at(balance, grid.end, -flow)
    keep = np.arange(len(theta)) != grid.reference
    degree = np.zeros(len(theta))
    weights = grid.weight.copy()
    weights[outage] = 0.0
    np.add.at(degree, grid.start, weights)
    np.add.at(degree, grid.end, weights)
    scale = max(1.0, np.max(np.abs(grid.injections[keep])),
                2 * np.max(degree[keep]) * np.max(np.abs(theta)))
    error = float(np.max(np.abs(balance[keep] - grid.injections[keep])) / scale)
    if error > 1e-10:
        raise ValueError(f"original outage residual failed: {outage}: {error}")
    return error


def execute(grid, mode):
    if mode not in ("native", "reuse"):
        raise ValueError("unknown policy")
    start_time = perf_counter()
    c, nodes = _incidence(grid)
    connected = _connected_outages(grid)
    base = (c.T @ diags(grid.weight) @ c).tocsc()
    rhs = grid.injections[nodes]
    fallback = 0
    if mode == "reuse":
        factor = splu(base)
        base_solution = factor.solve(rhs)
    answers = {}
    worst_error = 0.0
    for k in connected:
        if mode == "reuse":
            vector = c.getrow(k).toarray().ravel()
            y = factor.solve(vector)
            denom = 1 - grid.weight[k] * float(vector @ y)
        if mode == "native" or not np.isfinite(denom) or denom <= 1e-10:
            if mode == "reuse":
                fallback += 1
            mask = np.arange(len(grid.weight)) != k
            original = (c[mask].T @ diags(grid.weight[mask]) @ c[mask]).tocsc()
            reduced = splu(original).solve(rhs)
        else:
            reduced = base_solution + y * (grid.weight[k] *
                                         float(vector @ base_solution) / denom)
        full = np.zeros(len(grid.injections))
        full[nodes] = reduced
        worst_error = max(worst_error, _verify(grid, full, k))
        answers[k] = full
    return {"elapsed_s": perf_counter() - start_time, "connected": len(connected),
            "disconnected": len(grid.weight) - len(connected), "fallback": fallback,
            "max_original_residual": worst_error}, answers


def audit(path: Path):
    grid = load_case(path)
    execute(grid, "native")
    execute(grid, "reuse")
    trials = []
    for i in range(7):
        modes = ("native", "reuse") if i % 2 == 0 else ("reuse", "native")
        pair = {}
        answers = {}
        for mode in modes:
            pair[mode], answers[mode] = execute(grid, mode)
        if answers["native"].keys() != answers["reuse"].keys():
            raise ValueError("capability mismatch")
        diff = max(float(np.max(np.abs(answers["native"][k] - answers["reuse"][k])))
                   for k in answers["native"])
        if diff > 1e-8:
            raise ValueError(f"angle mismatch: {diff}")
        pair["max_angle_difference_rad"] = diff
        trials.append(pair)
    native = float(np.median([p["native"]["elapsed_s"] for p in trials]))
    reuse = float(np.median([p["reuse"]["elapsed_s"] for p in trials]))
    return {"protocol": "v0.0.66 frozen mechanism, not specialized-solver superiority",
            "source_sha256": CASE_SHA256, "scipy_version": scipy.__version__,
            "buses": len(grid.injections), "branches": len(grid.weight),
            "trials": trials, "median_native_s": native, "median_reuse_s": reuse,
            "ratio_candidate_over_native": reuse / native,
            "decision": ("LOCAL_REUSE_MECHANISM_SUPPORTED" if reuse <= 0.8 * native
                         else "NO_LOCAL_REUSE_ADVANTAGE")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.case)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("trials",)}, indent=2))
