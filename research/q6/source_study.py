"""Q6 first SOURCE-only transport study. No FRESH data path exists here.

prepare --bigbench <blobless-clone>
run
grade

Preparation reads only the 125 old rule SOURCE paths. Fold-specific libraries
exclude each receiver fold. Inference children never receive receiver TEST.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
import math
import multiprocessing as mp
import os
import pathlib
import queue
import resource
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
sys.path.insert(0, str(ROOT / "research/q3"))
from reference import execute, parse_program
from neumann1 import discovery_core as dc, invention_core as ic, spec_core as sc, inverted as iv
from neumann1.q6.contracts import Artifact, digest, seal_artifact
from neumann1.q6.transport import Kernel, checked_type, extract, transport, tup

PIN = "092b196c1f8f14a54bbc62f24759d43bde46dd3b"
BASE = "0d1baec723f249a62a901d100af6e941234a43ac"
OUT = ROOT / "docs/research/q6/results/source_v1_20261112"
SOURCE_DIR = "bigbench/benchmark_tasks/list_functions"
ARMS = ("C", "T", "B", "A", "C-no-map", "S", "V", "BudgetOnly")
PROTECTED = ("neumann1/invention_core.py", "neumann1/spec_core.py", "neumann1/discovery_core.py",
             "neumann1/inverted.py", "docs/experiments/second_evidence_seal.json", "docs/experiments/third_evidence_seal.json")


def file_sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", "-C", str(cwd), *args])


def fold(tid):
    return int(hashlib.sha256(("q6-transport-fold-v1:" + tid).encode()).hexdigest(), 16) % 5


def source_paths():
    paths = [SOURCE_DIR + "/c%03d/task.json" % n for n in range(1, 251)]
    return sorted(paths, key=lambda p: hashlib.sha256(("neumann-invention-first-v1:rule:" + p).encode()).hexdigest())[:125]


def cohort(tasks):
    return sorted(tasks, key=lambda t: hashlib.sha256(("q6-transport-source-v1:" + t["id"]).encode()).hexdigest())[:40]


def _originals(clone):
    import invention_first
    allowed = source_paths()
    # Batch-fetch ONLY authorized SOURCE blobs, not the directory or TARGET.
    lines = git("ls-tree", "-r", PIN, SOURCE_DIR, cwd=clone).decode().splitlines()
    blobs = {l.split("\t")[1]: l.split()[2] for l in lines}
    proc = subprocess.run(["git", "-C", str(clone), "fetch", "--no-tags", "--no-write-fetch-head",
                           "--filter=blob:none", "origin", "--stdin"],
                          input="\n".join(blobs[p] for p in allowed) + "\n", text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    tasks, manifest = [], []
    for p in allowed:
        raw = git("show", PIN + ":" + p, cwd=clone)
        blob = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
        assert blob == blobs[p]
        t = invention_first.load_rule(p, raw)
        tasks.append(t)
        manifest.append({"id": t["id"], "path": p, "blob_sha1": blob,
                         "sha256": hashlib.sha256(raw).hexdigest(), "commit": PIN})
    return tasks, manifest


def prepare(clone):
    if (OUT / "freeze.json").exists():
        raise SystemExit("REFUSE_OVERWRITE_FROZEN_SOURCE_STUDY")
    OUT.mkdir(parents=True, exist_ok=True)
    c0 = time.process_time()
    tasks, manifest = _originals(clone)
    by = {t["id"]: t for t in tasks}
    old = json.loads((ROOT / "docs/experiments/results/spec_core_dev_source.json").read_text())["rule"]["S_rows"]
    assert set(by) == set(old) and len(by) == 125
    meta = {m["id"]: m for m in manifest}
    producer = git("rev-parse", "HEAD").decode().strip()
    artifacts, rejected, verification_cpu = [], [], 0.0
    for tid, receipt in sorted(old.items()):
        if not receipt["solved"]:
            continue
        task = by[tid]
        kind, ast = parse_program(receipt["program"])
        state_types = list(task["in_types"]) if kind == "ast" else list(sc.Z_TYPES)
        output_type = task["out_type"] if kind == "ast" else "I" if kind == "zmap" else "B"
        assert checked_type(ast, tuple(state_types)) == output_type
        v0 = time.process_time()
        evidence = {}
        valid = True
        for split in ("train", "test"):
            predicted = [execute((kind, ast), i) for i, _ in task[split]]
            valid &= all(type(p) is type(o) and p == o for p, (_, o) in zip(predicted, task[split]))
            evidence[split] = {"examples": len(predicted), "predictions_digest": digest(predicted)}
        elapsed = time.process_time() - v0
        verification_cpu += elapsed
        if not valid:
            rejected.append(tid)
            continue
        method = {"kind": kind, "ast": ast, "state_types": state_types,
                  "input_types": task["in_types"], "output_type": task["out_type"]}
        a = seal_artifact({"producer_commit": producer, "source_task_digest": meta[tid]["sha256"],
                           "observation_schema": {"input_types": task["in_types"], "output_type": task["out_type"],
                                                  "authorized_source": "original donor TRAIN and TEST"},
                           "discovered_representation": {"kind": "typed-ast.v1", "state_types": state_types},
                           "executable_method": method,
                           "source_verification": {"status": "EXACT_OBSERVED_SOURCE", "checker": "q6.reference reused independent interpreter",
                                                   "method_digest": digest(method), "observations_digest": digest(task["train"] + task["test"]),
                                                   "finite_scope": evidence},
                           "provenance": {"source_id": tid, "author_blob": meta[tid], "q3_snapshot_commit": BASE,
                                          "original_q3_production_commit": None,
                                          "producer_role": "historical Q3 artifact exporter, not a new Q3 discovery policy"},
                           "resource_cost": {"historical_q3_discovery_cpu_seconds": receipt["cpu_seconds"],
                                             "source_reverification_cpu_seconds": elapsed}})
        # This authority is a trusted boundary established by actual independent
        # source execution above, not by the artifact's self-asserted status.
        trusted_id = a["artifact_id"]
        Artifact.admit(a, lambda d, trusted_id=trusted_id: d["artifact_id"] == trusted_id)
        artifacts.append(a)
    (OUT / "source_artifacts.json").write_text(json.dumps(artifacts, indent=2) + "\n")
    fold_meta = {}
    for f in range(5):
        selected = [a for a in artifacts if fold(a["provenance"]["source_id"]) != f]
        admitted = [Artifact.admit(a, lambda d, aid=a["artifact_id"]: d["artifact_id"] == aid) for a in selected]
        inv = extract(admitted)
        packed = {**inv, "kernels": [k.__dict__ for k in inv["kernels"]], "donor_ids": [a["provenance"]["source_id"] for a in selected],
                  "donor_artifact_ids": [a["artifact_id"] for a in selected],
                  "historical_source_cpu_seconds": sum(a["resource_cost"]["historical_q3_discovery_cpu_seconds"] for a in selected)}
        path = OUT / ("inventory_fold_%d.json" % f)
        path.write_text(json.dumps(packed, indent=2) + "\n")
        fold_meta[f] = {"file_sha256": file_sha(path), "artifact_count": len(selected), "kernel_count": len(inv["kernels"]),
                        "all_kernel_count": inv["all_kernel_count"], "extraction_cpu_seconds": inv["extraction_cpu_seconds"],
                        "historical_source_cpu_seconds": packed["historical_source_cpu_seconds"]}
    targets = cohort(tasks)
    # Hidden receiver labels remain in external original files. The inference
    # manifest stores TRAIN only, and includes only its own fold's donor path.
    visible = [{k: t[k] for k in ("id", "in_types", "out_type", "train")} for t in targets]
    # Keep receiver TRAIN outside git, so benchmark content is not republished.
    cache = ROOT.parent / "q6_source_v1_train_cache.json"
    cache.write_text(json.dumps(visible))
    code_paths = [p for folder in (ROOT / "neumann1/q6", ROOT / "research/q6", ROOT / "tests/q6")
                  for p in folder.glob("*.py")]
    code_paths += [ROOT / "docs/research/q6/CONTRACT_V1.md", ROOT / "docs/research/q6/DESIGN_AND_SOURCE_PREREG_V1.md"]
    freeze = {"schema": "neumann.q6.source-first.v1", "base_commit": BASE, "producer_commit": producer,
              "cohort": [t["id"] for t in targets], "folds": fold_meta, "source_manifest": manifest,
              "admitted_artifacts": len(artifacts), "independent_source_reverification_rejected": rejected,
              "source_verification_cpu_seconds": verification_cpu, "prepare_cpu_seconds": time.process_time() - c0,
              "receiver_train_cache_sha256": file_sha(cache), "source_artifacts_sha256": file_sha(OUT / "source_artifacts.json"),
              "code_sha256": {str(p.relative_to(ROOT)): file_sha(p) for p in code_paths},
              "protected_sha256": {p: file_sha(ROOT / p) for p in PROTECTED},
              "runtime": {"python": sys.version, "platform": sys.platform, "rss_unit": "Linux KiB converted to bytes"},
              "dataset_scope": "opened SOURCE only; no FRESH, OEIS or rule TARGET"}
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: freeze[k] for k in ("cohort", "folds", "admitted_artifacts", "independent_source_reverification_rejected", "prepare_cpu_seconds")}, indent=2), flush=True)


def inventory_for(f):
    d = json.loads((OUT / ("inventory_fold_%d.json" % f)).read_text())
    d["kernels"] = [Kernel(x["artifact_id"], tuple(x["path"]), tup(x["ast"]), tuple(x["in_types"]), x["out_type"])
                    for x in d["kernels"]]
    return d


def worker(payload, q):
    task, arm = payload
    assert task["test"] == ()
    cap = 12 if arm == "BudgetOnly" else 3
    startup = time.process_time()
    inv = sc.load_inverses(str(ROOT / sc.INVERSES))
    inventory = inventory_for(fold(task["id"]))
    assert task["id"] not in inventory["donor_ids"]
    assert all(fold(d) != fold(task["id"]) for d in inventory["donor_ids"])
    remaining = lambda: max(.001, cap - time.process_time())
    fallback = lambda seconds: dc.solve(task, seconds, dc.Policy(), inv)
    if arm == "A":
        raw = fallback(remaining())
        sol = raw.get("sol")
        r = {"via": "q3_core", "measured_cost": {"counts": {"q3_candidates": raw.get("candidates", 0)}}}
    elif arm in ("S", "V"):
        if arm == "S":
            raw = sc.solve(task, remaining(), "S", inv)
        else:
            spec = json.loads((ROOT / "docs/experiments/results/invention_core_frozen.json").read_text())["spec"]
            ops = iv.derive_op_inverses(spec)
            raw = iv.solve(task, remaining(), inv, spec, ops)
        sol = raw.get("sol")
        r = {"via": raw.get("via"), "measured_cost": {"counts": {"q3_candidates": raw.get("candidates", 0)}}}
    else:
        mode = "B" if arm == "B" else "C" if arm == "C" else "T"
        r = transport(task, inventory, cap_s=remaining(), mode=mode, fallback=fallback)
        method = r.get("transformed_executable_method")
        sol = (method["kind"], tup(method["ast"])) if method else None
    r.update({"id": task["id"], "arm": arm, "sol": sol, "program": sc.show(sol),
              "inference_startup_cpu_seconds": startup, "nominal_cpu_cap_seconds": cap,
              "donor_fold": fold(task["id"]), "train_only_inference": True,
              "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024})
    # Charge result construction/serialization to process CPU before emission.
    json.dumps(r)
    r["worker_total_cpu_seconds"] = time.process_time()
    q.put(r)


def run():
    freeze = json.loads((OUT / "freeze.json").read_text())
    if (OUT / "programs.jsonl").exists():
        raise SystemExit("REFUSE_RERUN_FIRST_RECEIVER_RESULTS")
    for p, h in freeze["code_sha256"].items():
        assert file_sha(ROOT / p) == h, p
    cache = ROOT.parent / "q6_source_v1_train_cache.json"
    assert file_sha(cache) == freeze["receiver_train_cache_sha256"]
    visible = json.loads(cache.read_text())
    jobs = []
    for t in visible:
        t["train"] = [(tup(i), tup(o)) for i, o in t["train"]]
        t["test"] = ()
        for a in ARMS:
            jobs.append((t, a))
    ctx, running = mp.get_context("spawn"), {}
    n = 0
    with (OUT / "programs.jsonl").open("w") as fh, gzip.open(OUT / "rejected_correspondences.jsonl.gz", "wt") as failures:
        def record(r):
            nonlocal n
            c0 = time.process_time()
            ledger = r.pop("rejected_candidate_ledger", [])
            failures.write(json.dumps({"id": r["id"], "arm": r["arm"], "rejected_candidates": ledger}, separators=(",", ":")) + "\n")
            failures.flush()
            r["rejected_candidate_ledger_count"] = len(ledger)
            r["rejected_candidate_ledger_sha256"] = digest(ledger)
            r["parent_recording_cpu_seconds"] = time.process_time() - c0
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            n += 1
            if n % 16 == 0:
                print("completed", n, "/", 320, flush=True)
        while jobs or running:
            while jobs and len(running) < 2:
                pl = jobs.pop(0)
                q = ctx.Queue()
                p = ctx.Process(target=worker, args=(pl, q))
                p.start()
                running[p] = q, pl[0]["id"], pl[1], time.monotonic()
            for p, (q, tid, arm, started) in list(running.items()):
                try:
                    r = q.get_nowait()
                except queue.Empty:
                    r = None
                if r is not None:
                    record(r)
                    p.join(timeout=1)
                    if p.is_alive():
                        p.terminate()
                        p.join()
                    q.close()
                    del running[p]
                elif time.monotonic() - started > 90 or (not p.is_alive() and p.exitcode):
                    if p.is_alive():
                        p.terminate()
                    p.join()
                    record({"id": tid, "arm": arm, "sol": None, "error": "TIMEOUT_OR_WORKER_FAILURE", "exitcode": p.exitcode})
                    q.close()
                    del running[p]
            time.sleep(.01)


def exact_p(w, l):
    n = w + l
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(w, l) + 1)) / 2 ** n)


def grade(clone):
    if (OUT / "result.json").exists():
        raise SystemExit("REFUSE_OVERWRITE_FIRST_Q6_RESULT")
    freeze = json.loads((OUT / "freeze.json").read_text())
    rows = [json.loads(line) for line in (OUT / "programs.jsonl").open()]
    expected = {(a, i) for a in ARMS for i in freeze["cohort"]}
    keys = [(r["arm"], r["id"]) for r in rows]
    if set(keys) != expected or len(keys) != len(set(keys)):
        raise ValueError("INVALID_INCOMPLETE_PAIRED_COHORT")
    program_sha = file_sha(OUT / "programs.jsonl")
    tasks, _ = _originals(clone)
    tasks = {t["id"]: t for t in tasks if t["id"] in freeze["cohort"]}
    solved, grades = {a: set() for a in ARMS}, []
    for r in rows:
        t = tasks[r["id"]]
        sol = tup(r["sol"]) if r.get("sol") is not None else None
        predictions, execute_cpu = {}, 0.0
        for split in ("train", "test"):
            c0 = time.process_time()
            predictions[split] = [execute(sol, i) for i, _ in t[split]] if sol else []
            execute_cpu += time.process_time() - c0
        v0 = time.process_time()
        def exact(split):
            return sol is not None and all(type(p) is type(o) and p == o for p, (_, o) in zip(predictions[split], t[split]))
        fit = exact("train")
        ok = fit and exact("test")
        check_cpu = time.process_time() - v0
        if ok:
            solved[r["arm"]].add(r["id"])
        grades.append({**r, "independent_fit": fit, "independent_solved": ok,
                       "independent_execution_cpu_seconds": execute_cpu, "independent_check_cpu_seconds": check_cpu,
                       "predictions_digest": digest(predictions)})
    union = set().union(*(solved[a] for a in ARMS if a != "C"))
    exclusive = sorted(solved["C"] - union)
    attributed = [r for r in grades if r["arm"] == "C" and r["id"] in exclusive and
                  r.get("via") == "compound_transport" and r.get("candidate_correspondence", {}).get("compound")]
    comparisons = {a: {"C_only": len(solved["C"] - solved[a]), "other_only": len(solved[a] - solved["C"]),
                        "p": exact_p(len(solved["C"] - solved[a]), len(solved[a] - solved["C"]))} for a in ARMS if a != "C"}
    totals = {a: math.fsum(r.get("worker_total_cpu_seconds", 0) + r.get("parent_recording_cpu_seconds", 0) +
                           r.get("independent_execution_cpu_seconds", 0) + r.get("independent_check_cpu_seconds", 0)
                           for r in grades if r["arm"] == a) for a in ARMS}
    investment = freeze["prepare_cpu_seconds"]
    # Source-Q3 discovery investment is once per historical donor, not per kernel.
    arts = json.loads((OUT / "source_artifacts.json").read_text())
    historical = sum(a["resource_cost"]["historical_q3_discovery_cpu_seconds"] for a in arts)
    horizons = {str(n): {a: {"accounting_only_total_cpu_seconds": historical + investment + n * totals[a] / 40,
                            "assumption": "uniform recurrence of the measured 40-source receiver distribution; not a new run or iso-capability break-even"}
                         for a in ("B", "T", "C", "C-no-map")} for n in (1, 10, 100)}
    report = {"schema": "neumann.q6.source-transport-first.v1", "scope": "opened SOURCE development only",
              "tasks": 40, "jobs": len(rows), "programs_sha256_before_grading": program_sha,
              "solved": {a: len(v) for a, v in solved.items()},
              "fit": {a: sum(r["independent_fit"] for r in grades if r["arm"] == a) for a in ARMS},
              "total_measured_cpu_seconds": totals, "C_only_all_comparators": exclusive,
              "compound_attributed_exclusive": [r["id"] for r in attributed], "paired": comparisons,
              "mechanism_positive": bool(attributed),
              "strong_source_gate": len(attributed) >= 5 and all(comparisons[a]["p"] < .0125 for a in ("T", "S", "V")),
              "errors": [r for r in rows if "error" in r], "extraction_and_preparation_cpu_seconds": investment,
              "historical_donor_q3_investment_cpu_seconds": historical, "reuse_horizon_scenarios": horizons,
              "accounting_limit": "process CPU through result serialization + parent recording + independent checking; queue-tail/OS-wide overhead not separately metered; energy/money UNKNOWN",
              "global_Q6": "OPEN", "independent_FRESH_opened": False, "grades": grades}
    (OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("grades", "reuse_horizon_scenarios")}, indent=2), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("prepare", "run", "grade"))
    ap.add_argument("--bigbench")
    args = ap.parse_args()
    if args.command == "prepare":
        prepare(pathlib.Path(args.bigbench))
    elif args.command == "run":
        run()
    else:
        grade(pathlib.Path(args.bigbench))
