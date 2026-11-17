"""DEVELOPMENT ONLY: whole-machine A / B / C on the opened list-routines tasks of section 31 (same seed, budget).

  A  default formation (FOLD_REACH_SYNTH off: the legacy first-fit cell Update)
  B  probe-diversified candidates for the last list component (synth_cells_candidates, k = 4; the candidate with
     the fewest initial-example fold errors is adopted -- the section 34 mechanism inside the machine)
  C  reachability-guided, fold-constrained synthesis of the last list component (synth_cells_fold)
Follow-up observation-policy arms (NOT part of the matched A/B/C synthesis comparison: they change WHICH states
are queried, within the same 60-query budget):
  D  REACH_TRAJ: the state trajectories are the initial examples' own prefixes (reachable fold states) instead of
     the synthetic ascending / descending / random ones; synthesis as in A
  CD D and C together

Every arm: run_arm("D") exactly as research/q3/active_dev.job (Env(spec, 0, budget=60), cap 30 s,
seed = sha256(name) % 1000), so total CPU cap and SOURCE query budget are identical; only the Update synthesis
call of the last list component differs.  With --vclock every module (and this harness) reads the deterministic
virtual clock of research/q3/vclock.py, so a rerun reproduces the run exactly (RNG and timing noise excluded).
Solved = the hidden test of the opened development task (evaluation only, never seen by the agent); the
independent SOURCE challenge verdict is the machine's own (CHALLENGE fresh inputs after formation).

  python research/q3/fold_reach_machine_dev.py --names-file docs/experiments/dev/update_snapshots/post_synthesis_first_failure.json \
    --arms A,B,C --out /tmp/fold_reach_machine.jsonl --vclock
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
from neumann1 import active as ac

_REAL_FOLD = ac.synth_cells_fold


def _b_candidates(in_types, rows, deadline, fold_errors, reach_inputs, k=4):
    """Arm B through the same hook: the section 34 candidates, the best initial-example fold adopted."""
    cands = ac.synth_cells_candidates(in_types, rows, deadline, k=4)
    best = None
    for g, ast in cands:
        e = fold_errors(g)
        if best is None or (e is not None and (best[0] is None or e < best[0])):
            best = (e, g, ast)
    info = {"candidates": len(cands), "errors": best[0] if best else None, "source": "probe4"}
    return (best[1], best[2], info) if best else (None, None, info)


def set_arm(arm):
    ac.GOAL_UPDATE_SYNTH = False
    ac.CAPTURE_UPDATE_TRANSITIONS = False
    ac.MIN_SYNTH_CPU = 0.0
    ac.REPAIR = False
    ac.FOLD_REACH_SYNTH = arm in ("B", "C", "CD")
    ac.REACH_TRAJ = arm in ("D", "CD")
    ac.synth_cells_fold = _b_candidates if arm == "B" else _REAL_FOLD


def h(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def summarise(rec):
    f = rec.get("formation") or {}
    ms = []
    for m in f.get("machines", []):
        ms.append({"dir": m.get("direction"), "events": m.get("events", [])[:40], "update": m.get("update"),
                   "W": [c.get("w") for c in m.get("components", [])], "challenge": m.get("challenge"),
                   "queries": m.get("queries_used"), "cpu": m.get("cpu"), "fold_reach": m.get("fold_reach"),
                   "query_purpose": m.get("query_purpose"), "formed": m.get("formed", False)})
    return ms


def job(arm, name, cap, use_vclock):
    """One (arm, task) in a FRESH process: no cache or clock history is shared between jobs."""
    clock = None
    if use_vclock:
        import vclock
        clock = vclock.install(vclock.VirtualTime(), extra=(sys.modules[__name__],))
    specs = {s.name: s for s in E.tasks()}
    ac._inv()
    set_arm(arm)
    env = E.Env(specs[name], 0, budget=60)
    c0 = time.process_time()
    pred, rec = ac.run_arm("D", env, cap, seed=h(name) % 1000)
    return {"arm": arm, "name": name, "scope": "DEVELOPMENT_ONLY_OPENED_LIST_ROUTINES",
            "clock": "virtual" if clock else "process_time", "cap": cap, "budget": 60,
            "solved": bool(pred is not None and env._score(pred)), "via": rec.get("via"),
            "queries": env.used, "cpu": round(time.process_time() - c0, 3),
            "machines": summarise(rec),
            "log_sha256": hashlib.sha256(json.dumps([[list(x), y if not isinstance(y, tuple) else list(y)]
                                                     for x, y in env.log]).encode()).hexdigest()}


def run(args):
    import concurrent.futures as cf
    import multiprocessing as mp
    names = sorted(json.loads(pathlib.Path(args.names_file).read_text()))
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {(r["arm"], r["name"]) for r in map(json.loads, out.read_text().splitlines())} if out.exists() else set()
    todo = [(arm, name) for name in names for arm in args.arms.split(",") if (arm, name) not in done]
    with cf.ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn"),
                                max_tasks_per_child=1) as ex:
        futs = {ex.submit(job, arm, name, args.cap, args.vclock): (arm, name) for arm, name in todo}
        for fut in cf.as_completed(futs):
            row = fut.result()
            with open(out, "a") as fh:
                fh.write(json.dumps(row, sort_keys=True, default=list) + "\n")
            print(row["arm"], row["name"], "solved", row["solved"], "via", row["via"], "q", row["queries"],
                  "cpu", row["cpu"], "challenge", [m["challenge"] for m in row["machines"]], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--names-file", required=True)
    p.add_argument("--arms", default="A,B,C")
    p.add_argument("--out", required=True)
    p.add_argument("--cap", type=float, default=30.0)
    p.add_argument("--vclock", action="store_true")
    p.add_argument("--workers", type=int, default=3)
    run(p.parse_args())
