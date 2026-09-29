"""Strong batched PTDF-style comparator for hash-pinned MATPOWER N-1 cases.

Only the DC angle problem is modeled; this is neither MATPOWER execution nor
an AC security calculation. Source cases are external, never redistributed.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter

import numpy as np
import scipy
from scipy.sparse import diags
from scipy.sparse.linalg import splu

from benchmark_v066 import Grid, _incidence, _table, _verify


PINS = {
    118: "bc2e6f22b4b9e776572885ee4b50e4f4ab2ee0c5577e9126e86d906f14c4b5f7",
    300: "69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5",
}


def load_grid(path, size):
    data = path.read_bytes()
    if sha256(data).hexdigest() != PINS[size]:
        raise ValueError("power-grid source hash mismatch")
    text = data.decode("ascii")
    bus, branch, gen = (_table(text, name) for name in ("bus", "branch", "gen"))
    base = re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)\s*;", text)
    identifiers = bus[:, 0].astype(int)
    ids = {key: i for i, key in enumerate(identifiers)}
    if (not base or bus.shape != (size, 13) or len(ids) != size
            or not np.array_equal(identifiers, bus[:, 0])
            or branch.shape[1] != 13 or gen.shape[1] < 10
            or np.sum(bus[:, 1] == 3) != 1
            or np.any(branch[:, 10] != 1) or np.any(gen[:, 7] != 1)
            or np.any(branch[:, 3] == 0) or np.any(branch[:, 9] != 0)
            or any(int(v) not in ids for v in branch[:, :2].ravel())
            or any(int(v) not in ids for v in gen[:, 0])):
        raise ValueError("unsupported DC case interface")
    tap = np.where(branch[:, 8] == 0, 1.0, branch[:, 8])
    if np.any(tap <= 0):
        raise ValueError("invalid transformer tap")
    f = np.array([ids[int(v)] for v in branch[:, 0]])
    t = np.array([ids[int(v)] for v in branch[:, 1]])
    injections = -bus[:, 2].copy()
    np.add.at(injections, [ids[int(v)] for v in gen[:, 0]], gen[:, 1])
    return Grid(f, t, 1.0 / (branch[:, 3] * tap),
                injections / float(base.group(1)), int(np.flatnonzero(bus[:, 1] == 3)[0]))


def connected_outages(grid):
    """Return nonbridge edge IDs, preserving parallel edges by edge ID."""
    n = len(grid.injections)
    adjacency = [[] for _ in range(n)]
    for k, (u, v) in enumerate(zip(grid.start, grid.end)):
        adjacency[u].append((v, k))
        adjacency[v].append((u, k))
    tin = np.full(n, -1, dtype=int)
    low = np.zeros(n, dtype=int)
    bridges = set()
    tick = 0

    def visit(u, parent_edge):
        nonlocal tick
        tin[u] = low[u] = tick
        tick += 1
        for v, edge in adjacency[u]:
            if edge == parent_edge:
                continue
            if tin[v] >= 0:
                low[u] = min(low[u], tin[v])
            else:
                visit(v, edge)
                low[u] = min(low[u], low[v])
                if low[v] > tin[u]:
                    bridges.add(edge)

    visit(grid.reference, -1)
    if np.any(tin < 0):
        raise ValueError("base grid is disconnected")
    return [k for k in range(len(grid.weight)) if k not in bridges]


def query_sets(grid, size):
    start = perf_counter()
    valid = connected_outages(grid)
    results = {}
    for count in (1, 8, 32, len(valid)):
        label = str(count) if count != len(valid) else "all"
        seed = int.from_bytes(sha256(f"v067/{size}/{label}".encode()).digest()[:8], "big")
        chosen = (valid if count == len(valid) else sorted(
            np.random.default_rng(seed).choice(valid, count, replace=False).tolist()))
        results[label] = chosen
    return results, len(grid.weight) - len(valid), perf_counter() - start


def execute(grid, query, mode, threshold=None):
    start = perf_counter()
    if mode == "router":
        if threshold is None:
            raise ValueError("router threshold missing")
        selected = "scalar" if len(query) <= threshold else "batch"
    else:
        selected = mode
    if selected not in ("scalar", "batch"):
        raise ValueError("unknown policy")
    valid = set(connected_outages(grid))
    if not query or any(k not in valid for k in query):
        raise ValueError("query includes disconnected or invalid outage")
    c, nodes = _incidence(grid)
    base = (c.T @ diags(grid.weight) @ c).tocsc()
    rhs = grid.injections[nodes]
    factor = splu(base)
    baseline = factor.solve(rhs)
    setup_end = perf_counter()
    columns = c[query].toarray().T
    if selected == "batch":
        sensitivities = factor.solve(np.asfortranarray(columns))
    else:
        sensitivities = np.column_stack([factor.solve(columns[:, j])
                                         for j in range(len(query))])
    answers = {}
    fallback = 0
    for j, k in enumerate(query):
        direction = columns[:, j]
        response = sensitivities[:, j]
        denominator = 1 - grid.weight[k] * float(direction @ response)
        if not np.isfinite(denominator) or abs(denominator) <= 1e-10:
            fallback += 1
            mask = np.arange(len(grid.weight)) != k
            original = (c[mask].T @ diags(grid.weight[mask]) @ c[mask]).tocsc()
            reduced = splu(original).solve(rhs)
        else:
            reduced = baseline + response * (grid.weight[k] *
                                             float(direction @ baseline) / denominator)
        full = np.zeros(len(grid.injections))
        full[nodes] = reduced
        answers[k] = full
    sensitivity_end = perf_counter()
    worst = max(_verify(grid, answers[k], k) for k in query)
    end = perf_counter()
    return {"elapsed_s": end - start, "setup_s": setup_end - start,
            "sensitivity_and_reconstruction_s": sensitivity_end - setup_end,
            "verification_s": end - sensitivity_end, "mode": selected,
            "fallback": fallback, "max_original_residual": worst}, answers


def measured_trials(grid, query, modes, threshold=None):
    for mode in modes:
        execute(grid, query, mode, threshold)
    trials = []
    for i in range(7):
        order = list(modes[i % len(modes):] + modes[:i % len(modes)])
        record, answers = {}, {}
        for mode in order:
            record[mode], answers[mode] = execute(grid, query, mode, threshold)
        reference = answers[modes[0]]
        difference = max(float(np.max(np.abs(reference[k] - answers[mode][k])))
                         for mode in modes[1:] for k in query)
        if difference > 1e-8:
            raise ValueError(f"original-angle capability mismatch: {difference}")
        record["max_angle_difference_rad"] = difference
        trials.append(record)
    return {"trials": trials, "medians_s": {
        mode: float(np.median([trial[mode]["elapsed_s"] for trial in trials]))
        for mode in modes}}


def development(path):
    start = perf_counter()
    grid = load_grid(path, 118)
    parse_s = perf_counter() - start
    queries, disconnected, selection_s = query_sets(grid, 118)
    rows = {label: {"query_ids": query,
                    **measured_trials(grid, query, ("scalar", "batch"))}
            for label, query in queries.items()}
    counts = [0, 1, 8, 32, len(queries["all"])]
    costs = {cutoff: sum(rows[label]["medians_s"][
        "scalar" if len(query) <= cutoff else "batch"]
        for label, query in queries.items()) for cutoff in counts}
    threshold = min(counts, key=lambda c: (costs[c], c not in (0, counts[-1]), c))
    return {"scope": "case118 nonblind development", "source_sha256": PINS[118],
            "scipy_version": scipy.__version__, "parse_s": parse_s,
            "query_selection_s": selection_s, "disconnected": disconnected,
            "rows": rows, "threshold_candidates_s": costs,
            "chosen_threshold": threshold}


def holdout(path, threshold):
    start = perf_counter()
    grid = load_grid(path, 300)
    parse_s = perf_counter() - start
    queries, disconnected, selection_s = query_sets(grid, 300)
    rows = {label: {"query_ids": query,
                    **measured_trials(grid, query, ("scalar", "batch", "router"),
                                      threshold=threshold)}
            for label, query in queries.items()}
    totals = {mode: sum(row["medians_s"][mode] for row in rows.values())
              for mode in ("scalar", "batch", "router")}
    per_case = all(row["medians_s"]["router"] <= 1.10 * min(
        row["medians_s"]["scalar"], row["medians_s"]["batch"])
        for row in rows.values())
    return {"scope": "case300 first holdout; parser format inspected before freeze",
            "source_sha256": PINS[300], "scipy_version": scipy.__version__,
            "parse_s": parse_s, "query_selection_s": selection_s,
            "disconnected": disconnected, "threshold_from_118": threshold,
            "rows": rows, "sum_of_medians_s": totals,
            "decision": ("ADAPTIVE_ROUTING_ADVANTAGE" if per_case and
                         totals["router"] <= 0.9 * min(totals["scalar"], totals["batch"])
                         else "NO_ROUTING_ADVANTAGE")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--size", type=int, choices=(118, 300), required=True)
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.size == 300 and args.threshold is None:
        parser.error("holdout requires the precommitted development threshold")
    result = (development(args.case) if args.size == 118 else
              holdout(args.case, args.threshold))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows",)}, indent=2))
