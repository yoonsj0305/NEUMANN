"""Post-primary SOURCE causal control: same matcher, background primitives only."""
from __future__ import annotations
import json
import multiprocessing as mp
import pathlib
import resource
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
from source_study import OUT, cohort, fold, inventory_for, _originals
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc
from neumann1.q6.transport import Kernel, transport, tup
from neumann1.q6.contracts import digest
from reference import execute


def worker(task):
    cap = 3
    inv = sc.load_inverses(str(ROOT / sc.INVERSES))
    library = inventory_for(fold(task["id"]))
    known = []
    for p in ic.base_library().values():
        if p.kind != "fo" or not p.arity or any(bt for _, bt in p.params):
            continue
        known.append(Kernel("BACKGROUND_EXECUTOR_PRIMITIVE:" + p.name, (),
                            (p.name,) + tuple(("v", j) for j in range(p.arity)),
                            tuple(t for t, _ in p.params), p.ret))
    library["kernels"] = known
    fallback = lambda seconds: dc.solve(task, seconds, dc.Policy(), inv)
    r = transport(task, library, cap_s=max(.001, cap - time.process_time()), mode="C", fallback=fallback)
    m = r.get("transformed_executable_method")
    r.update(id=task["id"], arm="PrimitiveContext", sol=(m["kind"], m["ast"]) if m else None,
             control_scope="same transport and memory, source kernels replaced by background first-order primitive contexts",
             worker_total_cpu_seconds=time.process_time(), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    # Detailed rejected candidates are counted/digested, not mistaken for wins.
    failed = r.pop("rejected_candidate_ledger", [])
    r["failed_candidates_count"] = len(failed)
    r["failed_candidates_digest"] = digest(failed)
    return r


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bigbench", required=True)
    args = ap.parse_args()
    programs = OUT / "primitive_control_programs.jsonl"
    if programs.exists():
        raise SystemExit("REFUSE_CONTROL_RERUN")
    visible = json.loads((ROOT.parent / "q6_source_v1_train_cache.json").read_text())
    jobs = [{**t, "train": [(tup(i), tup(o)) for i, o in t["train"]], "test": ()} for t in visible]
    rows = []
    with programs.open("w") as f, mp.get_context("spawn").Pool(2, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(worker, jobs, chunksize=1):
            rows.append(r)
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
            f.flush()
    program_digest = __import__("hashlib").sha256(programs.read_bytes()).hexdigest()
    tasks, _ = _originals(pathlib.Path(args.bigbench))
    tasks = {t["id"]: t for t in tasks}
    grades = []
    for r in rows:
        t = tasks[r["id"]]
        sol = tup(r["sol"]) if r.get("sol") else None
        def exact(split):
            return sol is not None and all(execute(sol, i) == o for i, o in t[split])
        grades.append({**r, "independent_fit": exact("train"),
                       "independent_solved": exact("train") and exact("test")})
    primary = json.loads((OUT / "result.json").read_text())
    wins = set(primary["compound_attributed_exclusive"])
    solved = {r["id"] for r in grades if r["independent_solved"]}
    report = {"scope": "post-primary causal validation on opened SOURCE; no fresh/general Q6 claim",
              "programs_sha256_before_control_grading": program_digest, "tasks": len(rows),
              "solved": len(solved), "fit": sum(r["independent_fit"] for r in grades),
              "same_original_witnesses_solved_without_source_kernels": sorted(wins & solved),
              "source_principle_attribution_survives": sorted(wins - solved),
              "cpu_seconds": sum(r["worker_total_cpu_seconds"] for r in rows), "grades": grades}
    (OUT / "primitive_control_result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "grades"}, indent=2))


if __name__ == "__main__":
    main()
