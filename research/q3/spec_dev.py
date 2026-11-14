"""Development runs of the specification-space core on SOURCE tasks only (never evidence).

python research/q3/spec_dev.py <bigbench> <oeis> <cap_s> <arm,arm,...> <rows.jsonl> [family[,family]]

Arms: A (frozen forward enumerator under the same CPU cap), A@k (the same with k times the cap),
S, S_no_state, S_no_inverse, D (sequence specialist, oeis only).
"""
from __future__ import annotations
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import spec_core as sc
import dev_source, sequence_specialist

INV = None


def job(a):
    global INV
    arm, cap, t = a
    if arm == "D":
        tr, te = [o for _, o in t["train"]], [o for _, o in t["test"]]
        p = sequence_specialist.predict(tr, len(te))
        return {"id": t["id"], "arm": arm, "fit": p is not None, "solved": p == te, "cpu_seconds": 0.0}
    if INV is None:
        INV = sc.load_inverses()
    name, _, k = arm.partition("@")
    r = sc.solve(t, cap * (float(k) if k else 1.0), name, INV)
    r.pop("sol")
    r.update(id=t["id"], arm=arm)
    return r


def main(bigbench, oeis, cap, arms, out, fams="rule,oeis"):
    d = dev_source.load(bigbench, oeis)
    done = set()
    try:                                    # resumable: rows already written are kept
        done = {(r["arm"], r["id"]) for r in map(json.loads, open(out))}
    except FileNotFoundError:
        pass
    jobs = [(arm, float(cap), t) for arm in arms.split(",") for f in fams.split(",") for t in d[f]
            if not (arm == "D" and f != "oeis") and (arm, t["id"]) not in done]
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()
    summary(out)


def summary(out):
    rows = [json.loads(l) for l in open(out)]
    for fam in ("rule", "oeis"):
        for arm in sorted({r["arm"] for r in rows}):
            rs = [r for r in rows if r["arm"] == arm and r["id"].startswith(fam)]
            if not rs:
                continue
            via = {}
            for r in rs:
                if r["solved"]:
                    via[r.get("via")] = via.get(r.get("via"), 0) + 1
            print("%-5s %-14s n %3d solved %3d fit %3d cpu %7.1f max %5.1f via %s" % (
                fam, arm, len(rs), sum(r["solved"] for r in rs), sum(r["fit"] for r in rs),
                sum(r["cpu_seconds"] for r in rs), max(r["cpu_seconds"] for r in rs), via))


if __name__ == "__main__":
    main(*sys.argv[1:7])
