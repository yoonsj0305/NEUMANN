"""Independent original-graph optimality certificates and G0 cost diagnosis.

Extends verification, never replaces first records/verdict or supplies a new
performance pass criterion. No model or optimizer calls.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import time

import numpy as np


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exact_graph_certificate(adj, weights):
    """Exhaustive integer proof after independently checked true-twin classes."""
    groups = {}
    for i in range(len(adj)):
        closed = adj[i].copy()
        closed[i] = True
        key = closed.tobytes()
        groups.setdefault(key, []).append(i)
    classes = list(groups.values())
    m = len(classes)
    if m > 20 or np.any(weights <= 0):
        raise ValueError("Outside certificate checker budget/positive-weight premise")
    # Check complete block constancy against ORIGINAL adjacency, independently
    # of latent construction labels and the producer's quotient implementation.
    neighbors, sums = [], []
    for i, group in enumerate(classes):
        internal = adj[np.ix_(group, group)].copy()
        np.fill_diagonal(internal, True)
        if not internal.all():
            raise ValueError("Class is not an original clique")
        bits = 0
        for j, other in enumerate(classes):
            if i == j:
                continue
            block = adj[np.ix_(group, other)]
            if not (block.all() or not block.any()):
                raise ValueError("Nonconstant original cross-class adjacency")
            if block.all():
                bits |= 1 << j
        neighbors.append(bits)
        sums.append(int(weights[group].sum()))
    # Exhaustive recurrence covers every class subset: a clique on mask is a
    # clique on rest plus a vertex adjacent to every rest vertex.
    valid = bytearray(1 << m)
    valid[0] = 1
    values = [0] * (1 << m)
    best, best_mask, feasible = 0, 0, 1
    for mask in range(1, 1 << m):
        bit = mask & -mask
        index = bit.bit_length() - 1
        rest = mask ^ bit
        if valid[rest] and rest & ~neighbors[index] == 0:
            valid[mask] = 1
            values[mask] = values[rest] + sums[index]
            feasible += 1
            if values[mask] > best:
                best, best_mask = values[mask], mask
    witness = [i for k, group in enumerate(classes) if best_mask & (1 << k) for i in group]
    return {"optimal_integer_weight": best, "witness": witness, "classes": classes,
            "class_weights": sums, "adjacency_bitmasks": neighbors,
            "all_subsets_checked": 1 << m, "feasible_subsets": feasible,
            "valid_subset_table_sha256": sha(bytes(valid)),
            "scope": "Complete original positive-weight true-twin reduction proof plus exhaustive class subsets"}


def analyze(first, output):
    output.mkdir(parents=True, exist_ok=False)
    manifest_raw = (first / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    for name, expected in manifest.items():
        path = (first / name).resolve()
        if not path.is_relative_to(first.resolve()) or sha(path.read_bytes()) != expected:
            raise ValueError("First evidence changed")
    report = json.loads((first / "report.json").read_bytes())
    rows = [json.loads(x) for x in (first / "records.jsonl").read_text().splitlines()]
    certificates = []
    start = time.perf_counter()
    for cell in report["cells"]:
        if cell["family"] != "graph":
            continue
        with np.load(first / "inputs" / (cell["case_id"] + ".npz"), allow_pickle=False) as z:
            proof = exact_graph_certificate(z["adjacency"], z["weights"])
            reference = int(z["reference_optimum"])
        if proof["optimal_integer_weight"] != reference:
            raise ValueError("Original MILP optimum disagrees with independent exhaustive proof")
        proof["case_id"] = cell["case_id"]
        certificates.append(proof)
    cost = []
    wins = {"graph": Counter(), "matrix": Counter()}
    for cell in report["cells"]:
        family = cell["family"]
        oracle = "FREE_TWIN" if family == "graph" else "FREE_FACTOR"
        eligible = [k for k, v in cell["routes"].items() if k != oracle and v["eligible"]]
        best = min(eligible, key=lambda k: cell["routes"][k]["median_seconds"])
        wins[family][best] += 1
        by_route = {}
        for route in cell["routes"]:
            r = [v for v in rows if v["case_id"] == cell["case_id"] and v["route"] == route and not v["warmup"]]
            by_route[route] = {key: statistics.median(v[key] for v in r) for key in [
                "input_scan_seconds", "execution_including_transform_seconds", "verification_seconds", "complete_seconds"]}
        # Report only diagnostic sensitivity, NEVER substitute for frozen gate.
        without_scan = min(v["execution_including_transform_seconds"] + v["verification_seconds"]
                           for k, v in by_route.items() if k != oracle) / (
                               by_route[oracle]["execution_including_transform_seconds"] + by_route[oracle]["verification_seconds"])
        cost.append({"case_id": cell["case_id"], "family": family, "fastest_baseline": best,
                     "route_stage_medians_seconds": by_route,
                     "diagnostic_speedup_without_fingerprint_scan": without_scan,
                     "alternate_gate_pass": "NOT_DEFINED_NO_POSTHOC_ADMISSION"})
    result = {"schema": "neumann.g0-independent-diagnosis.v1", "first_manifest_sha256": sha(manifest_raw),
              "first_verdict_unchanged": report["decision"], "original_graph_optimality_proofs": certificates,
              "exhaustive_original_graph_proofs_pass": len(certificates), "cost_diagnosis": cost,
              "fastest_comparator_case_counts": {k: dict(v) for k, v in wins.items()},
              "fingerprint_sensitivity_geomean": {f: float(np.exp(np.mean(np.log([
                  v["diagnostic_speedup_without_fingerprint_scan"] for v in cost if v["family"] == f])))) for f in wins},
              "verification_analysis_seconds": time.perf_counter() - start, "new_optimizer_calls": 0,
              "new_model_calls": 0, "new_training_calls": 0, "sealed_payloads_read": 0,
              "candidate_disposition": {
                  "single_true_twin_learned_selector": "NO_G1_INVESTMENT; retain known reducer as baseline/building block",
                  "single_low_rank_learned_selector": "NO_G1_INVESTMENT; retain mature direct/CG/factor baselines",
                  "learned_composed_representation_generation": "RESEARCH_HYPOTHESIS; new headroom contract required, not admitted"},
              "limitations": ["Not a proof that all graph/matrix representations lack benefit",
                  "Includes public input scan in frozen primary pipeline; scan-removal diagnosis is not a new pass",
                  "Tiny latent clique cores and constructed SPD factors are not frontier tasks",
                  "12 cases per domain/3 timing repeats are a bounded screen, not independent general-intelligence evidence"]}
    (output / "diagnosis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps({"diagnosis.json": sha((output / "diagnosis.json").read_bytes()),
        "source_sha256": sha(Path(__file__).read_bytes())}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["exhaustive_original_graph_proofs_pass", "fastest_comparator_case_counts", "fingerprint_sensitivity_geomean", "verification_analysis_seconds"]}))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--first", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    analyze(args.first, args.output)
