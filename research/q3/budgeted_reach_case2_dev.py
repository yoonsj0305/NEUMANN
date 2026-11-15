"""DEVELOPMENT ONLY: CASE 2 of the budgeted-reachability directive -- the needed reachable states are observed but
the Update is not synthesised.  How much CPU does the EXISTING synthesiser need on policy E's own tables?

1. capture: run_arm("D") with policy E (frozen) and CAPTURE_UPDATE_TRANSITIONS, keep each machine's first
   Update-failure table (SOURCE-observed transitions only; development snapshot format of section 29);
2. replay (no SOURCE in the arm): synth_cells on that table at real CPU caps (time.process_time());
   diagnostic only: initial-example fold errors (one-component W, root observed) and accuracy on fresh SOURCE
   inputs from a separate Env (outside every budget).  No new synthesiser, no candidate expansion.

  python research/q3/budgeted_reach_case2_dev.py --names-file names.json --caps 5,10,20,40 --out rows.jsonl
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import random
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
import budgeted_reach_dev as B
from neumann1 import active as ac


def freeze(x):
    return tuple(freeze(i) for i in x) if isinstance(x, list) else x


def capture(spec):
    B.set_arm("E")
    ac.CAPTURE_UPDATE_TRANSITIONS = True
    try:
        env = E.Env(spec, 0, budget=60)
        _, rec = ac.run_arm("D", env, 30.0, seed=B.h(spec.name) % 1000)
    finally:
        ac.CAPTURE_UPDATE_TRANSITIONS = False
        B.set_arm("A")
    return [m["first_update_failure"] for m in (rec.get("formation") or {}).get("machines", [])
            if m.get("first_update_failure")]


def fold_errors(snap, g, examples):
    if snap["W"] != [[]] or snap["accumulators"]:
        return None
    root = next((t["state"] for t in snap["transitions"] if t["prefix"] == []), None)
    z = freeze(root) if root is not None else ((),)
    bad = 0
    for (x,), y in examples:
        st = z
        for e in (x if snap["direction"] == "prefix" else x[::-1]):
            st = (g(st + (e,)),)
            if st[0] is None:
                break
        bad += st[0] != y
    return bad


def fresh(spec, snap, g, n=40):
    if snap["W"] != [[]] or snap["accumulators"]:
        return None
    root = next((t["state"] for t in snap["transitions"] if t["prefix"] == []), None)
    z = freeze(root) if root is not None else ((),)
    oracle = E.Env(spec, 0, budget=10 ** 9)
    rng = random.Random(4242)
    ok = tot = 0
    for _ in range(n):
        x = tuple(rng.randrange(0, 17) for _ in range(rng.randrange(1, 9)))
        y = oracle.query(x)
        if y is None:
            continue
        st = z
        for e in (x if snap["direction"] == "prefix" else x[::-1]):
            st = (g(st + (e,)),)
            if st[0] is None:
                break
        tot += 1
        ok += st[0] == y
    return [ok, tot]


def job(name, caps):
    spec = {s.name: s for s in E.tasks()}[name]
    ac._inv()
    examples = E.Env(spec, 0, budget=60).initial()
    out = []
    for snap in capture(spec):
        rows = [(freeze(r["inputs"]), freeze(r["output"])) for r in snap["rows"]]
        res = {"name": name, "direction": snap["direction"], "W": snap["W"], "component": snap["failed_component"],
               "table_sha256": snap["sha256"], "transitions": len(snap["transitions"]),
               "max_state_len": max((len(t["state"][0]) for t in snap["transitions"]
                                     if isinstance(t["state"][0], list)), default=0),
               "output_type": snap["output_type"], "replay": []}
        for cap in caps:
            t0 = time.process_time()
            if snap["output_type"] == "L":
                g, ast = ac.synth_cells(tuple(snap["in_types"]), rows, t0 + cap)
            else:
                g, ast = ac.synth_multi(tuple(snap["in_types"]), snap["output_type"], rows, t0 + cap)
            used = time.process_time() - t0
            r = {"cap": cap, "fit": g is not None, "cpu": round(used, 3)}
            if g is not None:
                r["ast"] = ast[1] if isinstance(ast, tuple) and ast and ast[0] == "cells" else repr(ast)
                r["fold_errors"] = fold_errors(snap, g, examples)
                r["fresh_correct"] = fresh(spec, snap, g)
            res["replay"].append(r)
            if g is not None:
                break                         # a larger cap repeats the same first fit; stop at the first fit
        out.append(res)
    return out


def run(args):
    import concurrent.futures as cf
    import multiprocessing as mp
    names = json.loads(pathlib.Path(args.names_file).read_text())
    caps = [float(c) for c in args.caps.split(",")]
    with cf.ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn"),
                                max_tasks_per_child=1) as ex:
        for rows in ex.map(job, names, [caps] * len(names)):
            with open(args.out, "a") as fh:
                for r in rows:
                    fh.write(json.dumps(r, sort_keys=True) + "\n")
                    print(r["name"], r["direction"], r["W"], "transitions", r["transitions"],
                          [(x["cap"], x["fit"], x["cpu"], x.get("fold_errors"), x.get("fresh_correct")) for x in r["replay"]],
                          flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--names-file", required=True)
    p.add_argument("--caps", default="5,10,20,40")
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=1)
    run(p.parse_args())
