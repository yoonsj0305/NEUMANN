"""G0 first-query headroom screen, two domains; no learned model or GPU.

Known reductions compete with supplied representations on original-task checks.
Oracle structures are deliberately nondeployable. Upstream solver investment,
FLOPs, energy and money are UNKNOWN; wall ratios are not full-resource claims.
"""
from __future__ import annotations

import os
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import inspect
import json
import math
import multiprocessing as mp
from pathlib import Path
import platform
import queue
import random
import statistics
import time
import warnings

import networkx as nx
import numpy as np
import scipy
from scipy import linalg, optimize, sparse
from scipy.sparse.linalg import cg
from threadpoolctl import threadpool_limits, threadpool_info

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
REPEATS = 3
MULTIPLIER = 10.0
ROUTES = {"graph": ["NX_DIRECT", "MILP_DIRECT", "TWIN_QUOTIENT", "FREE_TWIN"],
          "matrix": ["CHOLESKY_DIRECT", "CG_DIRECT", "PIVOTED_CHOLESKY", "FREE_FACTOR"]}
ORACLE = {"graph": "FREE_TWIN", "matrix": "FREE_FACTOR"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def array_sha(a):
    a = np.ascontiguousarray(a)
    return sha(str(a.dtype).encode() + json.dumps(a.shape).encode() + a.tobytes())


def specs():
    rows = []
    for m in (12, 16):
        for copies in (4, 8, 16):
            for rep in range(2):
                rows.append({"id": f"graph_m{m}_t{copies}_r{rep}", "family": "graph", "m": m,
                             "copies": copies, "seed": 1060600 + m * 100 + rep,
                             "density": (0.25, 0.55)[rep], "large": copies == 16})
    for n in (512, 1024, 2048):
        for rank in (4, 16):
            for rep in range(2):
                rows.append({"id": f"matrix_n{n}_k{rank}_r{rep}", "family": "matrix", "n": n,
                             "rank": rank, "seed": 1062600 + rank * 10 + rep,
                             "large": n == 2048})
    return rows


def runtime_identity():
    identities = {}
    for name in ("numpy", "scipy", "networkx", "threadpoolctl"):
        dist = importlib.metadata.distribution(name)
        identities[name] = {"version": dist.version, "record_sha256": sha(dist.read_text("RECORD").encode())}
    source = Path(inspect.getsourcefile(nx.algorithms.clique))
    identities["networkx_clique_source_sha256"] = sha(source.read_bytes())
    identities["python"] = platform.python_version()
    return identities


def generate(spec):
    rng = np.random.default_rng(spec["seed"])
    if spec["family"] == "graph":
        m, copies = spec["m"], spec["copies"]
        core = np.triu(rng.random((m, m)) < spec["density"], 1)
        core = core | core.T | np.eye(m, dtype=bool)
        labels = np.repeat(np.arange(m), copies)
        adjacency = core[np.ix_(labels, labels)]
        np.fill_diagonal(adjacency, False)
        weights = rng.integers(1, 10, len(labels), dtype=np.int64)
        p = rng.permutation(len(labels))
        return {"adjacency": adjacency[np.ix_(p, p)], "weights": weights[p], "oracle_labels": labels[p]}
    # Public task is SPD A*x=b; scalar identity and rank-reduction family are
    # known to every baseline, but seed, construction factors and labels are not.
    n, k = spec["n"], spec["rank"]
    u = rng.normal(size=(n, k)) / math.sqrt(k)
    a = np.eye(n) + u @ u.T
    b = rng.normal(size=n)
    return {"A": a, "b": b, "oracle_factor": u}


def public_view(case, family):
    names = ("adjacency", "weights") if family == "graph" else ("A", "b")
    return {k: case[k] for k in names}


def graph_nx(public):
    graph = nx.from_numpy_array(public["adjacency"])
    nx.set_node_attributes(graph, {i: int(w) for i, w in enumerate(public["weights"])}, "weight")
    nodes, _ = nx.max_weight_clique(graph, weight="weight")
    return sorted(nodes)


def graph_milp(public):
    adj, weights = public["adjacency"], public["weights"]
    i, j = np.where(np.triu(~adj, 1))
    q = len(i)
    idx = np.arange(q, dtype=np.int32)
    matrix = sparse.csc_matrix((np.ones(2 * q), (np.r_[idx, idx], np.r_[i, j])), shape=(q, len(weights)))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected.*", category=RuntimeWarning)
        result = optimize.milp(-weights.astype(float), integrality=np.ones(len(weights)),
            bounds=optimize.Bounds(0, 1), constraints=optimize.LinearConstraint(matrix, -np.inf, 1),
            options={"time_limit": 5.0, "mip_rel_gap": 0.0, "presolve": True, "threads": 1})
    if not result.success or result.x is None or result.mip_dual_bound is None or abs(result.fun - result.mip_dual_bound) > 1e-6:
        raise ValueError("Original-graph MILP did not certify optimum within frozen budget")
    return np.flatnonzero(result.x > 0.5).tolist()


def discover_twins(public):
    adj = public["adjacency"].copy()
    np.fill_diagonal(adj, True)
    packed = np.packbits(adj, axis=1)
    classes = {}
    labels = []
    for row in packed:
        key = row.tobytes()
        if key not in classes:
            classes[key] = len(classes)
        labels.append(classes[key])
    return np.asarray(labels)


def quotient_clique(public, labels):
    groups = [np.flatnonzero(labels == k) for k in np.unique(labels)]
    representatives = np.array([g[0] for g in groups])
    reduced = public["adjacency"][np.ix_(representatives, representatives)].copy()
    np.fill_diagonal(reduced, False)
    weights = np.array([public["weights"][g].sum() for g in groups])
    picked = graph_nx({"adjacency": reduced, "weights": weights})
    return sorted(int(i) for k in picked for i in groups[k])


def graph_check(public, witness, optimal_weight):
    n = len(public["weights"])
    if not isinstance(witness, list) or any(type(v) is not int or v < 0 or v >= n for v in witness) or len(set(witness)) != len(witness):
        return False
    selected = public["adjacency"][np.ix_(witness, witness)].copy()
    np.fill_diagonal(selected, True)
    return bool(selected.all() and int(public["weights"][witness].sum()) == optimal_weight)


def factor_solve(b, u):
    small = np.eye(u.shape[1]) + u.T @ u
    y = linalg.solve(small, u.T @ b, assume_a="pos", check_finite=True)
    return b - u @ y


def discover_factor(public):
    residual = public["A"].copy()
    residual.flat[::len(residual) + 1] -= 1.0
    c, piv, rank, info = linalg.lapack.dpstrf(residual, lower=1, tol=1e-9, overwrite_a=1)
    if info < 0 or rank == 0:
        raise ValueError("Pivoted Cholesky discovery failed")
    u = np.empty((len(c), rank))
    u[piv - 1] = np.tril(c[:, :rank])
    return u


def matrix_check(public, witness):
    x = np.asarray(witness, dtype=float)
    if x.shape != public["b"].shape or not np.isfinite(x).all():
        return False
    residual = public["A"] @ x - public["b"]
    # A=I+UU' is SPD with lambda_min >=1 by this registered family. Absolute
    # residual bound therefore also bounds absolute solution error in L2.
    return bool(np.linalg.norm(residual) <= 1e-7 * max(1.0, np.linalg.norm(public["b"])))


def solve(public, route, oracle=None):
    if route == "NX_DIRECT":
        return graph_nx(public)
    if route == "MILP_DIRECT":
        return graph_milp(public)
    if route == "TWIN_QUOTIENT":
        return quotient_clique(public, discover_twins(public))
    if route == "FREE_TWIN":
        return quotient_clique(public, oracle)
    if route == "CHOLESKY_DIRECT":
        return linalg.solve(public["A"], public["b"], assume_a="pos", check_finite=True).tolist()
    if route == "CG_DIRECT":
        x, info = cg(public["A"], public["b"], rtol=1e-10, atol=1e-12, maxiter=len(public["b"]))
        if info != 0:
            raise ValueError("CG did not converge")
        return x.tolist()
    if route == "PIVOTED_CHOLESKY":
        return factor_solve(public["b"], discover_factor(public)).tolist()
    if route == "FREE_FACTOR":
        return factor_solve(public["b"], oracle).tolist()
    raise ValueError("Unregistered route")


def observe(public, route, oracle, reference, repeat):
    start = time.perf_counter()
    row = {"route": route, "repeat": repeat, "warmup": repeat < 0,
           "accepted": False, "error": None, "witness": None}
    try:
        # Runtime input scan/hash is charged equally; all solvers receive only
        # public coefficients. No oracle labels/reference/seed enter Direct.
        begin = time.perf_counter()
        row["public_sha256"] = {k: array_sha(v) for k, v in public.items()}
        row["input_scan_seconds"] = time.perf_counter() - begin
        begin = time.perf_counter()
        witness = solve(public, route, oracle if route.startswith("FREE_") else None)
        row["execution_including_transform_seconds"] = time.perf_counter() - begin
        begin = time.perf_counter()
        row["accepted"] = graph_check(public, witness, reference) if "adjacency" in public else matrix_check(public, witness)
        row["verification_seconds"] = time.perf_counter() - begin
        row["witness"] = witness
    except Exception as exc:
        row["error"] = type(exc).__name__ + ": " + str(exc)
    row["complete_seconds"] = time.perf_counter() - start
    return row


def case_worker(spec, directory, channel):
    with threadpool_limits(limits=1):
        try:
            begin = time.perf_counter()
            case = generate(spec)
            public = public_view(case, spec["family"])
            generation = time.perf_counter() - begin
            begin = time.perf_counter()
            if spec["family"] == "graph":
                oracle = case["oracle_labels"]
                # Independent original-graph optimality check. No quotient or
                # construction label enters this reference MILP.
                ref_witness = graph_milp(public)
                reference = int(public["weights"][ref_witness].sum())
                if not graph_check(public, quotient_clique(public, oracle), reference):
                    raise ValueError("Oracle quotient failed original graph check")
                case["reference_optimum"] = np.asarray(reference)
            else:
                oracle, reference = case["oracle_factor"], None
                if not np.allclose(case["A"], np.eye(spec["n"]) + oracle @ oracle.T, rtol=1e-12, atol=1e-12):
                    raise ValueError("Supplied factor identity invalid")
            preparation = time.perf_counter() - begin
            np.savez_compressed(Path(directory) / (spec["id"] + ".npz"), **case)
            channel.put({"kind": "prepared", "spec": spec, "generation_seconds": generation,
                         "reference_and_oracle_validation_seconds": preparation, "threadpools": threadpool_info()})
            cached = None
            cache_investment = None
            for repeat in range(-1, REPEATS):
                order = list(ROUTES[spec["family"]])
                random.Random(10606 + repeat + spec["seed"]).shuffle(order)
                for route in order:
                    channel.put({"kind": "started", "case_id": spec["id"], "route": route, "repeat": repeat})
                    row = observe(public, route, oracle, reference, repeat)
                    row.update({"case_id": spec["id"], "family": spec["family"]})
                    channel.put({"kind": "observation", "record": row})
                    if row["accepted"] and cached is None and not route.startswith("FREE_"):
                        cached = row["witness"]
                        cache_investment = {"route": route, "repeat": repeat, "complete_seconds": row["complete_seconds"]}
            # Independent warm exact-cache floor; discovery is retained above.
            # Not included in first-query gate (an empty cache has no answer).
            if cached is not None:
                begin = time.perf_counter()
                fingerprints = {k: array_sha(v) for k, v in public.items()}
                valid = graph_check(public, cached, reference) if spec["family"] == "graph" else matrix_check(public, cached)
                channel.put({"kind": "cache_floor", "case_id": spec["id"], "accepted": valid,
                             "seconds": time.perf_counter() - begin, "public_sha256": fingerprints,
                             "discovery_investment_not_zero": True, "discovery_investment": cache_investment})
            channel.put({"kind": "done", "case_id": spec["id"]})
        except Exception as exc:
            channel.put({"kind": "case_error", "case_id": spec["id"], "error": type(exc).__name__ + ": " + str(exc)})


def summarize(records):
    cells = []
    for spec in specs():
        family = spec["family"]
        routes = {}
        for route in ROUTES[family]:
            rows = [r for r in records if r["case_id"] == spec["id"] and r["route"] == route and not r["warmup"]]
            valid = len(rows) == REPEATS and all(r["accepted"] and r["complete_seconds"] <= 15 for r in rows)
            routes[route] = {"accepted_repeats": sum(r["accepted"] for r in rows), "eligible": valid,
                             "median_seconds": statistics.median(r["complete_seconds"] for r in rows) if valid else None}
        oracle = routes[ORACLE[family]]
        baseline = [v["median_seconds"] for k, v in routes.items() if k != ORACLE[family] and v["eligible"]]
        ratio = min(baseline) / oracle["median_seconds"] if baseline and oracle["eligible"] else None
        cells.append({"case_id": spec["id"], "family": family, "large": spec["large"], "routes": routes,
                      "strongest_declared_baseline_over_free_structure": ratio})
    decisions = {}
    for family in ROUTES:
        c = [v for v in cells if v["family"] == family]
        ratios = [v["strongest_declared_baseline_over_free_structure"] for v in c]
        complete = all(v is not None for v in ratios)
        gm = math.exp(statistics.mean(math.log(v) for v in ratios)) if complete else None
        large_wins = sum(v["strongest_declared_baseline_over_free_structure"] is not None and
                         v["strongest_declared_baseline_over_free_structure"] >= MULTIPLIER for v in c if v["large"])
        admitted = complete and gm >= MULTIPLIER and large_wins >= 3
        decisions[family] = {"evaluable_cases": sum(v is not None for v in ratios), "cases": len(c),
                             "geomean_speedup": gm, "large_10x_cases": large_wins, "large_cases": 4,
                             "headroom_admitted": admitted}
    return {"status": "COMPLETE" if len(records) == len(specs()) * 4 * (REPEATS + 1) else "INCOMPLETE",
            "decision": "G0_HEADROOM_ADMIT_ARCHITECTURE_DESIGN" if all(x["headroom_admitted"] for x in decisions.values()) else "G0_NO_G1_TRAINING_ADMISSION",
            "families": decisions, "cells": cells,
            "scope": "Supplied true-twin and low-rank factors on declared constructed first-query distributions only",
            "global_optimal_representation_proven": False, "learned_intelligence_evaluated": False,
            "g1_training_started": False, "g2_admitted": False, "global_questions_closed": [],
            "resource_axes_unavailable": ["FLOPs", "energy", "money", "upstream_algorithm_investment"],
            "economic_pareto_claim": False}


def freeze(directory):
    directory.mkdir(parents=True, exist_ok=False)
    prereg = {"schema": "neumann.g0-headroom.v1", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "PREREGISTERED_BEFORE_FULL_GRID_EXECUTION", "specs": specs(), "routes": ROUTES,
              "measured_repeats": REPEATS, "warmup_repeats": 1, "families": 2,
              "criterion": {"speedup": MULTIPLIER, "per_family_geomean": ">=10", "largest_scale_cases": ">=3/4 at >=10x",
                            "all_cases_evaluable": True, "scope": "optimistic first-query matched warm latency only"},
              "baseline_envelope": "Per-case fastest correct median among native and known structural algorithms; no global strongest claim",
              "complete_query_cost": "input array scan/hash + transform/discovery + execution/reconstruction + original-task verification + failed attempts",
              "excluded_but_reported_investment": "imports, worker launch, input generation/storage, offline independent reference and correct free-oracle preparation",
              "free_oracle": "Provided correct structure, not a proof of best possible representation; discovery cost excluded for optimistic screen only",
              "cache_rights": "All first-query caches empty; warm repeated-query exact-cache floor separately reported, native discovery investment retained",
              "thread_budget": 1, "milp_time_limit_seconds": 5.0, "query_eligibility_seconds": 15,
              "worker_event_timeout_seconds": 30, "whole_run_limit_seconds": 1800,
              "matrix_check": "SPD A=I+UU' family; residual L2 <=1e-7*max(1,||b||), implies solution L2 error bound",
              "graph_check": "Original graph clique feasibility/integer weight equals independently certified original-graph MILP optimum",
              "new_producer_exposure": "OPENED_DEVELOPMENT; no claim of fresh learned-model evaluation",
              "missing_historical_assets": "excluded, never required or reconstructed", "sealed_payload_access": False,
              "training": False, "gpu": False, "g2_authorized": False,
              "source_sha256": sha(Path(__file__).read_bytes()), "runtime_identity": runtime_identity(),
              "d0_manifests": {p: sha((WORKSPACE / p).read_bytes()) for p in [
                  "Continuation/D0_CORE_LP_COST_VIEW/manifest.json", "Continuation/D0_CONTROL_FIRST/manifest.json"]},
              "primary_sources": ["https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.clique.max_weight_clique.html",
                  "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html",
                  "https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.lapack.dpstrf.html",
                  "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.cg.html"]}
    raw = (json.dumps(prereg, indent=2) + "\n").encode()
    (directory / "preregister.json").write_bytes(raw)
    (directory / "structural_headroom.py").write_bytes(Path(__file__).read_bytes())
    (ROOT / "docs/experiments/g0_headroom.preregister.json").write_bytes(raw)
    (directory / "freeze-receipt.json").write_text(json.dumps({"preregister_sha256": sha(raw),
        "source_sha256": prereg["source_sha256"], "full_grid_observations_before_freeze": 0,
        "development_checks": "tiny synthetic correctness only, not measured headroom"}, indent=2) + "\n", encoding="utf-8")
    print("G0 preregistered:", sha(raw))


def run(registration, output):
    prereg_raw = registration.read_bytes()
    reg = json.loads(prereg_raw)
    receipt = json.loads((registration.parent / "freeze-receipt.json").read_bytes())
    if sha(prereg_raw) != receipt["preregister_sha256"] or reg["source_sha256"] != sha(Path(__file__).read_bytes()) or reg["runtime_identity"] != runtime_identity():
        raise ValueError("Frozen contract/source/runtime identity drift")
    for p, expected in reg["d0_manifests"].items():
        if sha((WORKSPACE / p).read_bytes()) != expected:
            raise ValueError("D0 provenance changed")
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    inputs.mkdir()
    (output / "preregister.json").write_bytes(prereg_raw)
    begin = time.perf_counter()
    records, events = [], []
    context = mp.get_context("spawn")
    for spec in specs():
        if time.perf_counter() - begin > 1800:
            events.append({"kind": "whole_run_deadline"})
            break
        channel = context.Queue()
        proc = context.Process(target=case_worker, args=(spec, str(inputs), channel))
        proc.start()
        try:
            while True:
                try:
                    event = channel.get(timeout=30)
                except queue.Empty:
                    events.append({"kind": "worker_deadline", "case_id": spec["id"], "budget_seconds": 30})
                    proc.terminate()
                    break
                if event["kind"] == "observation":
                    records.append(event["record"])
                    with (output / "records.jsonl").open("a", encoding="utf-8") as f:
                        f.write(json.dumps(event["record"]) + "\n")
                else:
                    events.append(event)
                    with (output / "events.jsonl").open("a", encoding="utf-8") as f:
                        f.write(json.dumps(event) + "\n")
                if event["kind"] in ("done", "case_error"):
                    break
        finally:
            proc.join(timeout=5)
            if proc.is_alive():
                proc.terminate()
                proc.join()
            channel.close()
        print(spec["id"], "retained observations", len(records), flush=True)
    report = summarize(records)
    report.update({"whole_run_seconds": time.perf_counter() - begin, "registration_sha256": sha(prereg_raw),
                   "observations": len(records), "warmups_retained": sum(r["warmup"] for r in records),
                   "accepted": sum(r["accepted"] for r in records), "events": events,
                   "runtime": {"platform": platform.platform(), "processor": platform.processor(), "identity": runtime_identity()},
                   "new_model_calls": 0, "new_training_calls": 0, "sealed_payloads_read": 0})
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest = {p.relative_to(output).as_posix(): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "decision", "families", "observations", "accepted", "whole_run_seconds"]}), flush=True)


def replay(directory):
    manifest = json.loads((directory / "manifest.json").read_bytes())
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and p.name not in ("manifest.json", "replay.json")}
    if actual != set(manifest):
        raise ValueError("Replay exact file coverage mismatch")
    for n, expected in manifest.items():
        path = (directory / n).resolve()
        if not path.is_relative_to(directory.resolve()) or sha(path.read_bytes()) != expected:
            raise ValueError("Retained original bytes changed")
    rows = [json.loads(x) for x in (directory / "records.jsonl").read_text().splitlines()]
    checked = 0
    with threadpool_limits(limits=1):
        for spec in specs():
            case_rows = [r for r in rows if r["case_id"] == spec["id"]]
            with np.load(directory / "inputs" / (spec["id"] + ".npz"), allow_pickle=False) as z:
                public = {k: z[k] for k in (("adjacency", "weights") if spec["family"] == "graph" else ("A", "b"))}
                reference = int(z["reference_optimum"]) if spec["family"] == "graph" else None
            for row in case_rows:
                if row.get("public_sha256") != {k: array_sha(v) for k, v in public.items()}:
                    raise ValueError("Original public identity mismatch")
                if row["witness"] is not None:
                    valid = graph_check(public, row["witness"], reference) if spec["family"] == "graph" else matrix_check(public, row["witness"])
                    if valid != row["accepted"]:
                        raise ValueError("Original-task witness validity changed")
                    checked += 1
    report = json.loads((directory / "report.json").read_bytes())
    recalculated = summarize(rows)
    for k in recalculated:
        if recalculated[k] != report[k]:
            raise ValueError("Frozen gate replay changed: " + k)
    result = {"valid": True, "original_witnesses_rechecked": checked, "new_solver_calls": 0,
              "new_model_calls": 0, "sealed_payloads_read": 0, "decision": report["decision"]}
    (directory / "replay.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["freeze", "run", "replay"])
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(args.directory)
    elif args.action == "run":
        run(args.registration, args.output)
    else:
        replay(args.directory)
