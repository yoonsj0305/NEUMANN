"""Frozen follow-up on the SAME opened SOURCE cohort; no FRESH loader.

prepare --bigbench PATH | run | grade --bigbench PATH | audit
Inference only receives its own TRAIN and a different-fold donor inventory.
"""
from __future__ import annotations
import time
_IMPORT_CPU_START = time.process_time()
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import multiprocessing as mp
import pathlib
import queue
import resource
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
import source_study as old
from reference import execute
from neumann1 import discovery_core as dc, invention_core as ic, spec_core as sc, inverted as iv
from neumann1.q6.contracts import digest
from neumann1.q6.joint_transport import joint_transport
from neumann1.q6.transport import Kernel, tup
PARENT_COLD_IMPORT_CPU_SECONDS = time.process_time() - _IMPORT_CPU_START

OUT = ROOT / "docs/research/q6/results/joint_source_v2_20261113"
CACHE = ROOT.parent / "q6_joint_source_v2_train_cache.json"
ARMS = ("Joint", "OneRole", "TypeCompose", "Primitive", "A", "V", "BudgetOnly")
CODE = ("neumann1/q6/joint_transport.py", "research/q6/joint_source_study.py",
        "tests/q6/test_joint_transport.py", "docs/research/q6/JOINT_SOURCE_V2_PREREG.md")


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def save(path, data):
    with pathlib.Path(path).open("x") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def load(name):
    return json.loads((OUT / name).read_text())


def code_check():
    freeze = load("freeze.json")
    for p, h in freeze["code_sha256"].items():
        assert sha(ROOT / p) == h, p
    for p, h in freeze["protected_sha256"].items():
        assert sha(ROOT / p) == h, p
    for f, h in freeze["inventory_sha256"].items():
        assert sha(old.OUT / ("inventory_fold_%s.json" % f)) == h, f
    return freeze


def prepare(clone):
    if OUT.exists():
        raise SystemExit("REFUSE_EXISTING_FOLLOWUP_DIRECTORY")
    c0 = time.process_time()
    # Matching code is committed BEFORE reconstructing any author observations.
    assert not subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain=v1", "--untracked-files=no"])
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    hashes = {p: sha(ROOT / p) for p in CODE}
    tasks, manifest = old._originals(clone)
    by_id = {t["id"]: t for t in tasks}
    first = json.loads((old.OUT / "freeze.json").read_text())
    assert set(first["cohort"]) == {t["id"] for t in old.cohort(tasks)}
    assert {m["path"]: m["blob_sha1"] for m in manifest} == {
        m["path"]: m["blob_sha1"] for m in first["source_manifest"]}
    # Revalidate real donor methods under the independent literal interpreter.
    arts = json.loads((old.OUT / "source_artifacts.json").read_text())
    valid = []
    for a in arts:
        assert digest({k: v for k, v in a.items() if k != "artifact_id"}) == a["artifact_id"]
        m = a["executable_method"]
        assert a["source_verification"]["method_digest"] == digest(m)
        tid = a["provenance"]["source_id"]
        sol = m["kind"], tup(m["ast"])
        for split in ("train", "test"):
            for inp, goal in by_id[tid][split]:
                value = execute(sol, inp)
                assert type(value) is type(goal) and value == goal, tid
        valid.append(a["artifact_id"])
    # Only this file enters inference. Original receiver gold stays in author git.
    visible = [{k: by_id[tid][k] for k in ("id", "in_types", "out_type", "train")}
               for tid in first["cohort"]]
    save(CACHE, visible)
    OUT.mkdir(parents=True)
    historical = json.loads((ROOT / "docs/experiments/results/spec_core_dev_source.json").read_text())
    historical_cost = sum(r["cpu_seconds"] for r in historical["rule"]["S_rows"].values())
    freeze = {"schema": "neumann.q6.joint-source.v2.freeze", "producer_commit": commit,
              "scope": "POSTFIRST same 40 opened same-author SOURCE tasks; not independent generalization",
              "hypothesis": "joint correspondence adds original exact solutions requiring multiple composed SOURCE roles",
              "cohort": first["cohort"], "source_manifest_digest": digest(manifest),
              "arms": ARMS, "normal_cpu_seconds": 3, "budget_only_cpu_seconds": 12,
              "workers": 2, "wall_timeout_seconds": 90, "start_method": "fork",
              "setup_accounting": "common code-only parent cold import charged once; fresh fork child process CPU resets before each job",
              "code_sha256": hashes, "protected_sha256": first["protected_sha256"],
              "inventory_sha256": {str(f): sha(old.OUT / ("inventory_fold_%d.json" % f)) for f in range(5)},
              "admitted_source_artifacts": valid, "train_cache_sha256": sha(CACHE),
              "historical_source_all_attempts_cpu_seconds": historical_cost,
              "historical_source_and_inverse_costs_complete": False,
              "historical_cost_limit": "common inverse-discovery investment unmeasured; energy unknown",
              "source_reverification_and_preparation_cpu_seconds": time.process_time() - c0,
              "mechanism_gate": ">=1 Joint-only original exact over every comparator, with >=2 composed roles",
              "strong_source_gate": ">=5 such wins; exact two-sided paired p<0.05/6 against each comparator",
              "independent_FRESH_opened": False, "global_Q6": "OPEN",
              "python": sys.version}
    save(OUT / "freeze.json", freeze)
    print(json.dumps({"frozen": len(visible), "arms": ARMS, "donors": len(valid), "commit": commit}), flush=True)


def worker(payload, output):
    task, arm = payload
    try:
        assert task["test"] == ()
        cap = 12 if arm == "BudgetOnly" else 3
        inventory = old.inventory_for(old.fold(task["id"]))
        assert task["id"] not in inventory["donor_ids"]
        assert all(old.fold(tid) != old.fold(task["id"]) for tid in inventory["donor_ids"])
        inverse = sc.load_inverses(str(ROOT / sc.INVERSES))
        remaining = lambda: max(.001, cap - time.process_time())
        fallback = lambda seconds: dc.solve(task, seconds, dc.Policy(), inverse)
        if arm == "A":
            raw = fallback(remaining())
            sol = raw.get("sol")
            row = {"via": "unchanged_q3", "measured_cost": {"counts": {"candidates": raw.get("candidates", 0)}}}
        elif arm == "V":
            spec = json.loads((ROOT / "docs/experiments/results/invention_core_frozen.json").read_text())["spec"]
            ops = iv.derive_op_inverses(spec)
            raw = iv.solve(task, remaining(), inverse, spec, ops)
            sol = raw.get("sol")
            row = {"via": raw.get("via"), "measured_cost": {"counts": {"candidates": raw.get("candidates", 0)}}}
        else:
            if arm == "Primitive":
                inventory["kernels"] = [
                    Kernel("BACKGROUND_EXECUTOR_PRIMITIVE:" + p.name, (),
                           (p.name,) + tuple(("v", j) for j in range(p.arity)),
                           tuple(t for t, _ in p.params), p.ret)
                    for p in ic.base_library().values()
                    if p.kind == "fo" and p.arity and not any(bt for _, bt in p.params)]
            mode = "TypeCompose" if arm == "BudgetOnly" else "Joint" if arm == "Primitive" else arm
            row = joint_transport(task, inventory, cap_s=remaining(), mode=mode, fallback=fallback)
            method = row.get("transformed_executable_method")
            sol = (method["kind"], tup(method["ast"])) if method else None
        ledger = row.pop("rejected_candidate_ledger", [])
        row.update({"id": task["id"], "arm": arm, "sol": sol, "program": sc.show(sol),
                    "nominal_cpu_cap_seconds": cap, "train_only_inference": True,
                    "rejected_candidates_count": len(ledger), "rejected_candidates_digest": digest(ledger),
                    "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024})
        json.dumps(row)
        row["worker_total_cpu_seconds"] = time.process_time()
        output.put((row, ledger))
    except BaseException as e:
        output.put(({"id": task["id"], "arm": arm, "sol": None,
                     "error": type(e).__name__ + ": " + str(e),
                     "worker_total_cpu_seconds": time.process_time()}, []))


def run():
    freeze = code_check()
    assert sha(CACHE) == freeze["train_cache_sha256"]
    if (OUT / "programs.jsonl").exists():
        raise SystemExit("REFUSE_RERUN_FROZEN_FOLLOWUP")
    jobs = []
    for raw in json.loads(CACHE.read_text()):
        task = {**raw, "train": [(tup(i), tup(o)) for i, o in raw["train"]], "test": ()}
        jobs.extend((task, arm) for arm in ARMS)
    # Code-only parent never loads receiver gold in run(). Fork creates fresh
    # per-job processes with no state learned from any prior receiver. Charge
    # the shared cold import once; child CPU includes its inventory loading.
    ctx, active, n = mp.get_context("fork"), {}, 0
    study_wall, study_cpu = time.monotonic(), time.process_time()
    with (OUT / "programs.jsonl").open("x") as out, gzip.open(OUT / "rejected_candidates.jsonl.gz", "xt") as failed:
        def record(row, ledger):
            nonlocal n
            c0 = time.process_time()
            failed.write(json.dumps({"id": row["id"], "arm": row["arm"], "candidates": ledger}) + "\n")
            failed.flush()
            row["parent_recording_cpu_seconds"] = time.process_time() - c0
            out.write(json.dumps(row, separators=(",", ":")) + "\n")
            out.flush()
            n += 1
            if n % 14 == 0:
                print(json.dumps({"completed": n, "total": len(freeze["cohort"]) * len(ARMS),
                                  "wall_seconds": round(time.monotonic() - study_wall, 1)}), flush=True)
        while jobs or active:
            while jobs and len(active) < 2:
                payload = jobs.pop(0)
                q = ctx.Queue()
                p = ctx.Process(target=worker, args=(payload, q))
                p.start()
                active[p] = q, payload, time.monotonic()
            for p, (q, payload, started) in list(active.items()):
                try:
                    row, ledger = q.get_nowait()
                except queue.Empty:
                    row = None
                if row is not None:
                    record(row, ledger)
                    p.join(timeout=1)
                    if p.is_alive():
                        p.terminate()
                        p.join()
                    q.close()
                    del active[p]
                elif time.monotonic() - started > 90 or (not p.is_alive() and p.exitcode):
                    if p.is_alive():
                        p.terminate()
                    p.join()
                    record({"id": payload[0]["id"], "arm": payload[1], "sol": None,
                            "error": "TIMEOUT_OR_WORKER_FAILURE", "exitcode": p.exitcode}, [])
                    q.close()
                    del active[p]
            time.sleep(.01)
    save(OUT / "prediction_seal.json", {"programs_sha256": sha(OUT / "programs.jsonl"),
        "failed_candidates_sha256": sha(OUT / "rejected_candidates.jsonl.gz"), "jobs": n,
        "study_wall_seconds": time.monotonic() - study_wall,
        "parent_controller_cpu_seconds": time.process_time() - study_cpu,
        "parent_cold_import_cpu_seconds": PARENT_COLD_IMPORT_CPU_SECONDS,
        "parent_total_process_cpu_seconds": time.process_time(),
        "receiver_gold_read_by_inference": False})


def grade(clone):
    freeze = code_check()
    if (OUT / "result.json").exists():
        raise SystemExit("REFUSE_REGRADING_FIRST_FOLLOWUP_RESULT")
    seal = load("prediction_seal.json")
    assert sha(OUT / "programs.jsonl") == seal["programs_sha256"]
    rows = [json.loads(line) for line in (OUT / "programs.jsonl").open()]
    expected = {(tid, a) for tid in freeze["cohort"] for a in ARMS}
    assert len(rows) == len(expected) and {(r["id"], r["arm"]) for r in rows} == expected
    tasks, _ = old._originals(clone)
    by_id = {t["id"]: t for t in tasks}
    solved, grades = {a: set() for a in ARMS}, []
    for row in rows:
        t = by_id[row["id"]]
        sol = tup(row["sol"]) if row.get("sol") else None
        c0 = time.process_time()
        predicted = {}
        for split in ("train", "test"):
            predicted[split] = [execute(sol, i) for i, _ in t[split]] if sol else []
        execute_cost = time.process_time() - c0
        c0 = time.process_time()
        exact = lambda split: sol is not None and all(type(v) is type(g) and v == g
                    for v, (_, g) in zip(predicted[split], t[split]))
        fit, ok = exact("train"), exact("train") and exact("test")
        if ok:
            solved[row["arm"]].add(row["id"])
        grades.append({**row, "independent_fit": fit, "independent_solved": ok,
                       "original_TEST_passed": sum(type(v) is type(g) and v == g
                            for v, (_, g) in zip(predicted["test"], t["test"])) if sol else 0,
                       "original_TEST_total": len(t["test"]), "prediction_digest": digest(predicted),
                       "independent_execution_cpu_seconds": execute_cost,
                       "independent_check_cpu_seconds": time.process_time() - c0})
    other_union = set().union(*(v for a, v in solved.items() if a != "Joint"))
    exclusive = solved["Joint"] - other_union
    attributed = [r["id"] for r in grades if r["arm"] == "Joint" and r["id"] in exclusive
                  and (r.get("candidate_correspondence") or {}).get("compound_role_count", 0) >= 2]
    paired = {a: {"joint_only": len(solved["Joint"] - solved[a]), "comparator_only": len(solved[a] - solved["Joint"]),
                  "p_two_sided_exact": old.exact_p(len(solved["Joint"] - solved[a]), len(solved[a] - solved["Joint"]))}
              for a in ARMS if a != "Joint"}
    totals = {a: sum(r.get("worker_total_cpu_seconds", 0) + r["independent_execution_cpu_seconds"] +
                    r["independent_check_cpu_seconds"] for r in grades if r["arm"] == a) for a in ARMS}
    report = {"schema": "neumann.q6.joint-source.v2.result", "scope": freeze["scope"], "tasks": len(freeze["cohort"]),
              "jobs": len(rows), "solved": {a: len(v) for a, v in solved.items()},
              "solved_task_ids": {a: sorted(v) for a, v in solved.items()},
              "fit": {a: sum(r["independent_fit"] for r in grades if r["arm"] == a) for a in ARMS},
              "joint_exclusive_all_comparators": sorted(exclusive), "multiple_compound_role_attributed": sorted(attributed),
              "mechanism_gate_pass": bool(attributed),
              "strong_source_gate_pass": len(attributed) >= 5 and all(v["p_two_sided_exact"] < .05 / 6 for v in paired.values()),
              "paired": paired, "process_and_grade_cpu_seconds": totals, "errors": [r for r in rows if r.get("error")],
              "prediction_seal": seal, "source_preparation_cpu_seconds": freeze["source_reverification_and_preparation_cpu_seconds"],
              "historical_source_all_attempts_cpu_seconds": freeze["historical_source_all_attempts_cpu_seconds"],
              "accounting_complete": False, "energy_joules": None, "monetary_cost": None,
              "full_cost_10x_claim": False, "same_capability_speedup": None,
              "global_Q6": "OPEN", "independent_FRESH_opened": False, "grades": grades}
    save(OUT / "result.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("grades", "solved_task_ids")}, indent=2), flush=True)


def audit():
    freeze = code_check()
    seal = load("prediction_seal.json")
    assert sha(OUT / "programs.jsonl") == seal["programs_sha256"]
    assert sha(OUT / "rejected_candidates.jsonl.gz") == seal["failed_candidates_sha256"]
    rows = [json.loads(line) for line in (OUT / "programs.jsonl").open()]
    report = load("result.json")
    grades = {(r["id"], r["arm"]): r for r in report["grades"]}
    failures = {}
    with gzip.open(OUT / "rejected_candidates.jsonl.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            failures[r["id"], r["arm"]] = r["candidates"]
    assert len(rows) == len(grades) == len(failures) == len(freeze["cohort"]) * len(ARMS)
    for row in rows:
        key = row["id"], row["arm"]
        assert all(grades[key][k] == v for k, v in row.items())
        if not row.get("error"):
            assert digest(failures[key]) == row["rejected_candidates_digest"]
            assert len(failures[key]) == row["rejected_candidates_count"]
            assert row["train_only_inference"]
    assert not report["independent_FRESH_opened"] and report["global_Q6"] == "OPEN"
    summary = {"code_and_protected_hashes": "PASS", "programs_and_grades": len(rows),
               "rejected_candidate_ledgers": len(failures), "old_SOURCE_inventories_unchanged": 5,
               "independent_FRESH_opened": False, "scope": "integrity only, not independent scientific evidence"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "grade", "audit"))
    parser.add_argument("--bigbench")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(pathlib.Path(args.bigbench))
    elif args.command == "grade":
        grade(pathlib.Path(args.bigbench))
    elif args.command == "run":
        run()
    else:
        audit()
