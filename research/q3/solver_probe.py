"""Iteration 4, step 2 (diagnosis only): hand each of the 20 constructors, specified by self-generated examples,
to the frozen THIRD solver (`spec_core.solve`, arm S) instead of the plain synthesiser.  No operation-specific
code.  Records which solver stage defines it and whether the multi-argument signature reaches the traversal
stages at all (`spec_core.subtasks` only re-represents single-list and single-integer inputs).

python research/q3/solver_probe.py <cap_s> <out.json>
"""
from __future__ import annotations
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import invention_core as ic, spec_core as sc
import substrate_probe as sp


def task(name):
    ats, ret, _, _ = sp.OPS[name]
    ex = sp.examples(name, 10, 0)
    return {"id": name, "in_types": list(ats), "out_type": ret, "train": ex, "test": sp.examples(name, 40, 1)}


def job(a):
    name, cap = a
    t = task(name)
    r = sc.solve(t, cap, "S", sc.load_inverses())
    return {"operation": name, "type": sp.OPS[name][0], "traversal_stages_available": len(sc.subtasks(t)),
            "defined": r["solved"], "fit": r["fit"], "via": r["via"], "program": r["program"],
            "cpu_seconds": r["cpu_seconds"]}


def main(cap, out):
    with Pool(4) as p:
        rows = p.map(job, [(n, float(cap)) for n in sp.OPS], chunksize=1)
    json.dump({"schema": "neumann.solver-probe.v1", "cap_cpu_seconds": float(cap), "rows": rows}, open(out, "w"), indent=1)
    for r in rows:
        print("%-11s %-14s stages %d  %s %s %s" % (r["operation"], "".join(r["type"]), r["traversal_stages_available"],
              "DEFINED" if r["defined"] else ("fit-wrong" if r["fit"] else "-"), r["via"] or "", (r["program"] or "")[:70]))


if __name__ == "__main__":
    main(*sys.argv[1:3])
