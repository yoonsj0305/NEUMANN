"""Stage A follow-up, step 1 (diagnosis only; SOURCE only; nothing is given to any solver).

For every rule SOURCE task the Stage A arm R did not solve, separate:
  generalisation  R fit TRAIN but failed the hidden tests (from the Stage A rows)
  search          the same construction finds a hidden-test-correct representation at 10x the cap
  not found       nothing that fits TRAIN at 10x the cap (candidate: not expressible in the relation language)
Also records how much of each answer is observable as copies of input cells (provenance coverage).

python research/q3/failure_split.py <bigbench> <oeis> <stage_a_rows> <cap_s> <out.json>
"""
from __future__ import annotations
import collections, json, sys, time
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import invention_core as ic, spec_core as sc, relcells as rc
import dev_source


def coverage(t):
    cells = hit = 0
    for (x,), y in t["train"]:
        for v in y:
            cells += 1
            hit += v in x
    return round(hit / cells, 3) if cells else None


def job(a):
    t, cap = a
    lib = ic.base_library()
    t0 = time.process_time()
    sol = rc.solve(t, time.process_time() + cap, sc.load_inverses(), lib)
    ok = sol is not None and all(rc.run(sol, lib, i, t) == o for i, o in t["test"])
    return {"id": t["id"], "found": sol is not None, "solved": ok, "cpu": round(time.process_time() - t0, 2),
            "program": rc.show(sol) if sol else None, "provenance_coverage": coverage(t),
            "len_equal": all(len(i[0]) == len(o) for i, o in t["train"]),
            "len_change": sorted({len(o) - len(i[0]) for i, o in t["train"]})}


def main(bigbench, oeis, rows, cap, out):
    d = {t["id"]: t for t in dev_source.load(bigbench, oeis)["rule"]}
    R = {r["id"]: r for r in map(json.loads, open(rows)) if r["arm"] == "R" and r["family"] == "rule"}
    fail = [i for i, r in R.items() if not r["solved"]]
    gen = [i for i in fail if R[i]["fit"]]
    with Pool(4) as p:
        res = p.map(job, [(d[i], float(cap)) for i in sorted(fail) if i not in gen], chunksize=1)
    cat = {}
    for i in gen:
        cat[i] = "generalisation"
    for r in res:
        cat[r["id"]] = "search" if r["solved"] else ("generalisation_at_10x" if r["found"] else "not_found_at_10x")
    rec = {"schema": "neumann.failure-split.v1", "cap_10x_cpu_seconds": float(cap), "failed": len(fail),
           "categories": dict(collections.Counter(cat.values())), "per_task": cat,
           "rows_10x": res, "stage_a_fit_wrong": {i: R[i]["program"] for i in gen}}
    json.dump(rec, open(out, "w"), indent=1, sort_keys=True)
    print(rec["categories"])
    for r in res:
        print(r["id"], cat[r["id"]], "cov", r["provenance_coverage"], "len", r["len_change"], (r["program"] or "")[:80])


if __name__ == "__main__":
    main(*sys.argv[1:6])
