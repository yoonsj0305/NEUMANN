"""One new learned-program-generation study; opened SOURCE only.

Run with OPENBLAS_NUM_THREADS=1. Discovery children receive no original TEST.
The heldout selfplay and original outcomes are reported separately.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import pathlib
import queue
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q3"))
from neumann1 import invention_core as ic, semantic_program_generator as gen
from neumann1 import spec_core as sc, inverted as iv
from independent_invention_audit import execute, paired_p, parse_program

DEST = ROOT / "docs/experiments/results/semantic_program_generator_20261112"
ARMS = ("C", "U", "P", "M", "E", "S", "V")
PIN = "092b196c1f8f14a54bbc62f24759d43bde46dd3b"


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def tup(v):
    return tuple(tup(x) for x in v) if isinstance(v, list) else v


def experience():
    with gzip.open(DEST / "selfplay.json.gz", "rt") as f:
        return [dict(t, ast=tup(t["ast"]), train=[(tup(i), tup(o)) for i, o in t["train"]],
                     test=[(tup(i), tup(o)) for i, o in t["test"]]) for t in json.load(f)]


def select_ids():
    r = json.loads((ROOT / "docs/experiments/results/spec_core_dev_source.json").read_text())["rule"]["S_rows"]
    return sorted((i for i, x in r.items() if not x["solved"]),
                  key=lambda i: hashlib.sha256(("neumann-semantic-generator-v1:" + i).encode()).hexdigest())[:24]


def originals(clone):
    # Reuse the existing original-format loader, not any model/learning path.
    import invention_first
    tasks, manifest = [], []
    for tid in select_ids():
        path = "bigbench/benchmark_tasks/list_functions/%s/task.json" % tid.split("/")[1]
        raw = subprocess.check_output(["git", "-C", str(clone), "show", PIN + ":" + path])
        blob = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
        actual = subprocess.check_output(["git", "-C", str(clone), "rev-parse", PIN + ":" + path]).decode().strip()
        assert actual == blob
        task = invention_first.load_rule(path, raw)
        assert task["id"] == tid
        tasks.append(task)
        manifest.append({"id": tid, "path": path, "commit": PIN, "blob_sha1": blob,
                         "sha256": hashlib.sha256(raw).hexdigest()})
    return tasks, manifest


class EqualGrammarSearch(ic.Search):
    def __init__(self, task, deadline):
        super().__init__(ic.base_library(), ic.uniform_costs(), task["in_types"], task["out_type"],
                         task["train"], 10 ** 12, consts=gen.CONSTS, max_nb=gen.MAX_SCOPE - 1)
        self.deadline = deadline

    def _cand(self, ctx, p, kids, out):
        if not (self.n & 255) and time.process_time() > self.deadline:
            raise ic.Budget()
        return super()._cand(ctx, p, kids, out)


def worker(payload, q):
    task, arm = payload
    assert task["test"] == ()
    c0 = time.process_time()
    seed = int(hashlib.sha256(task["id"].encode()).hexdigest()[:8], 16)
    if arm in ("C", "U", "P"):
        model = gen.SemanticProgramGenerator() if arm == "U" else gen.SemanticProgramGenerator.load(DEST / "model.npz")
        r = model.invent(task["train"], task["in_types"], task["out_type"], cap_s=max(.01, 3 - (time.process_time() - c0)),
                         seed=seed, conditioned=arm != "P")
        r["sol"] = ("ast", r.pop("ast")) if r.get("ast") is not None else None
    elif arm == "M":
        ast, tried = None, 0
        for t in experience()[:-64]:
            if time.process_time() - c0 >= 3:
                break
            if t["in_types"] != task["in_types"] or t["out_type"] != task["out_type"]:
                continue
            tried += 1
            if all(ic.run_program(t["ast"], gen.LIB, i) == o for i, o in task["train"]):
                ast = t["ast"]
                break
        r = {"sol": ("ast", ast) if ast is not None else None, "proposed": tried}
    elif arm == "E":
        s = EqualGrammarSearch(task, c0 + 3)
        ast = s.run()
        r = {"sol": ("ast", ast) if ast is not None else None, "proposed": s.n}
    else:
        inv = sc.load_inverses(str(ROOT / sc.INVERSES))
        if arm == "S":
            r = sc.solve(task, max(.01, 3 - (time.process_time() - c0)), "S", inv)
        else:
            spec = json.loads((ROOT / "docs/experiments/results/invention_core_frozen.json").read_text())["spec"]
            # Derivation cost is charged inside the per-task discovery cap.
            ops = iv.derive_op_inverses(spec)
            r = iv.solve(task, max(.01, 3 - (time.process_time() - c0)), inv, spec, ops)
    sol = r.get("sol")
    r.update({"id": task["id"], "arm": arm, "cpu_seconds": time.process_time() - c0,
              "program": sc.show(sol), "train_only": True})
    q.put(r)


def run_jobs(tasks, destination):
    jobs = [({**{k: t[k] for k in ("id", "in_types", "out_type", "train")}, "test": ()}, a)
            for t in tasks for a in ARMS]
    ctx = mp.get_context("spawn")
    running, results = {}, []
    with destination.open("w") as fh:
        def record(r):
            results.append(r)
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            if len(results) % 24 == 0:
                print("completed", len(results), "/", len(tasks) * len(ARMS), flush=True)
        while jobs or running:
            while jobs and len(running) < 2:
                payload = jobs.pop(0)
                q = ctx.Queue()
                p = ctx.Process(target=worker, args=(payload, q))
                p.start()
                running[p] = q, payload[0]["id"], payload[1], time.monotonic()
            for p, (q, tid, arm, start) in list(running.items()):
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
                elif time.monotonic() - start > 30 or (not p.is_alive() and p.exitcode):
                    if p.is_alive():
                        p.terminate()
                    p.join()
                    record({"id": tid, "arm": arm, "sol": None, "program": None,
                            "error": "TIMEOUT_OR_WORKER_FAILURE", "exitcode": p.exitcode})
                    q.close()
                    del running[p]
            time.sleep(.01)
    return results


def grade(rows, tasks, teachers):
    by_task = {t["id"]: t for t in tasks}
    known = {gen.canonical(t["ast"]) for t in teachers}
    grades = []
    for r in rows:
        t = by_task[r["id"]]
        sol = tup(r["sol"]) if r.get("sol") is not None else None
        tr = [execute(sol, i) for i, _ in t["train"]] if sol else []
        te = [execute(sol, i) for i, _ in t["test"]] if sol else []
        def exact(pred, pairs):
            return sol is not None and len(pred) == len(pairs) and all(type(v) is type(o) and v == o
                                                                      for v, (_, o) in zip(pred, pairs))
        fit = exact(tr, t["train"])
        grades.append({**r, "independent_fit": fit, "independent_solved": fit and exact(te, t["test"]),
                       "novel_ast": bool(sol and sol[0] == "ast" and gen.canonical(sol[1]) not in known),
                       "test_predictions_sha256": hashlib.sha256(json.dumps(te).encode()).hexdigest()})
    solved = {a: {r["id"] for r in grades if r["arm"] == a and r["independent_solved"]} for a in ARMS}
    exclusives = sorted(solved["C"] - set().union(*(solved[a] for a in ARMS if a != "C")))
    tests = {a: {"C_only": len(solved["C"] - solved[a]), "other_only": len(solved[a] - solved["C"]),
                 "p": paired_p(len(solved["C"] - solved[a]), len(solved[a] - solved["C"]))}
             for a in ARMS if a != "C"}
    cpu = {a: math.fsum(r.get("cpu_seconds", 0) for r in rows if r["arm"] == a) for a in ARMS}
    errors = [r for r in rows if "error" in r]
    return {"tasks": len(tasks), "rows": len(rows), "solved": {a: len(s) for a, s in solved.items()},
            "fit": {a: sum(r["independent_fit"] for r in grades if r["arm"] == a) for a in ARMS},
            "cpu_seconds": cpu, "C_exclusive": exclusives, "paired": tests, "errors": errors,
            "learned_exclusive_evidence": bool(exclusives),
            "strong_local_gate": len(exclusives) >= 5 and all(tests[a]["p"] < .025 for a in ("E", "S"))
                                 and all(cpu["C"] <= cpu[a] for a in ("E", "S")),
            "grades": grades}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bigbench", required=True)
    args = ap.parse_args()
    if any((DEST / name).exists() for name in ("original_programs.jsonl", "synthetic_programs.jsonl")):
        raise SystemExit("REFUSE_RERUN: preserve first outcomes; choose a new hypothesis instead")
    tasks, manifest = originals(args.bigbench)
    all_experience = experience()
    teachers, synthetic = all_experience[:-64], all_experience[-64:]
    receipt = json.loads((DEST / "training.json").read_text())
    assert sha(DEST / "model.npz") == receipt["model_sha256"]
    assert sha(ROOT / "neumann1/semantic_program_generator.py") == receipt["code_sha256"]
    assert sha(ROOT / "docs/research/SEMANTIC_PROGRAM_GENERATOR_PREREG_2026_11_12.md") == receipt["prereg_sha256"]
    freeze = {"training": receipt, "original_manifest": manifest, "cohort": select_ids(),
              "study_code_sha256": sha(__file__), "independent_checker_sha256": sha(ROOT / "research/q3/independent_invention_audit.py")}
    (DEST / "freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
    # All original discovery programs are frozen before any original outcome scoring.
    original_rows = run_jobs(tasks, DEST / "original_programs.jsonl")
    original_commit = sha(DEST / "original_programs.jsonl")
    original = grade(original_rows, tasks, teachers)
    original["programs_sha256_before_grading"] = original_commit
    (DEST / "original_result.json").write_text(json.dumps(original, indent=2) + "\n")
    print("ORIGINAL_RESULT", json.dumps({k: v for k, v in original.items() if k != "grades"}), flush=True)
    synthetic_rows = run_jobs(synthetic, DEST / "synthetic_programs.jsonl")
    synthetic_commit = sha(DEST / "synthetic_programs.jsonl")
    syn = grade(synthetic_rows, synthetic, teachers)
    syn["programs_sha256_before_grading"] = synthetic_commit
    syn["note"] = "self-generated heldout behaviours; not independent original-author evidence"
    (DEST / "synthetic_result.json").write_text(json.dumps(syn, indent=2) + "\n")
    print("SYNTHETIC_RESULT", json.dumps({k: v for k, v in syn.items() if k != "grades"}), flush=True)


if __name__ == "__main__":
    main()
