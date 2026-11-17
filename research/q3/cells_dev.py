"""Iteration 4: constructed cell representations.  Causal test on SOURCE, development validation on the opened
list families (rule TARGET, dc), never first exposure.

  run <bigbench> <ec> <oeis> <wake_rows> <rows.jsonl>     arms C, Cn on SOURCE (5-fold policies) and on the
                                                          validation families (policy fitted on all SOURCE)
  report <iter1_cv_rows> <third_rows> <rows> <record.json>
Cn = the iteration-1 configuration (learned policy + memory) = C with representation construction removed.
"""
from __future__ import annotations
import collections, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import spec_core as sc, discovery_core as dc, cells
import dev_source, discovery_dev as dd, invention_eval2 as ev2, invention_first as first

CAP = 6.0
INV = None
POL = {}


def job(a):
    global INV
    arm, fam, t = a
    if INV is None:
        INV = sc.load_inverses()
    pol = POL[dd.fold_of(t["id"])] if fam in ("rule", "oeis") else POL["all"]
    r = dc.solve(t, CAP, pol, INV, cells=(arm == "C"))
    r.pop("sol", None)
    r.pop("tried", None)
    return dict(r, id=t["id"], arm=arm, family=fam)


def run(bigbench, ec, oeis, wake_rows, out):
    global POL
    POL, wrows = dd.policies(wake_rows)
    POL["all"] = dc.fit(wrows)
    src = dev_source.load(bigbench, oeis)
    val = ev2.plan_tasks("second", bigbench, ec, oeis)
    fams = {"rule": src["rule"], "oeis": src["oeis"],
            "rule_target": [t for t in val["rule"] if "unsupported" not in t],
            "dc": [t for t in val["dc"] if "unsupported" not in t]}
    done = set()
    try:
        done = {(r["arm"], r["id"]) for r in map(json.loads, open(out))}
    except FileNotFoundError:
        pass
    jobs = [(arm, f, t) for f, ts in fams.items() for arm in ("C", "Cn") for t in ts if (arm, t["id"]) not in done]
    print("todo", len(jobs), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def _vs(so, a, b):
    w, l = len(so[a] - so[b]), len(so[b] - so[a])
    return {"first_only": w, "second_only": l, "mcnemar_p": first.mcnemar(w, l)}


def report(iter1_rows, third_rows, rows_path, out):
    rows = [json.loads(l) for l in open(rows_path)]
    old = [r for r in map(json.loads, open(iter1_rows)) if r["arm"] in ("A", "C", "S", "D")]
    for r in old:
        r["arm"] = {"C": "B"}.get(r["arm"], r["arm"])
        r["family"] = r["id"].split("/")[0]
    third = []
    for r in map(json.loads, open(third_rows)):
        if r["key"][1] == "S" and r["key"][0] in ("rule", "dc"):
            third.append({"id": r["key"][2], "arm": "S", "solved": r["solved"], "cpu_seconds": r["cpu_seconds"],
                          "family": {"rule": "rule_target", "dc": "dc"}[r["key"][0]]})
    rec = {"schema": "neumann.discovery-policy.iteration.v1",
           "label": "iteration 4: constructed cell representations", "cap_cpu_seconds": CAP,
           "note": "SOURCE causal test + development validation on opened list families; not evidence for any gate",
           "families": {}}
    for fam in ("rule", "oeis", "rule_target", "dc"):
        by = {}
        for r in rows + old + third:
            if r["family"] == fam:
                by.setdefault(r["arm"], {})[r["id"]] = r
        n = len(by["C"])
        assert all(len(v) == n for v in by.values()), (fam, {a: len(v) for a, v in by.items()})
        so = {a: {i for i, r in v.items() if r["solved"]} for a, v in by.items()}
        cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
        gain = sorted(so["C"] - so["Cn"])
        via = {i: by["C"][i]["via"] for i in gain}
        cls = collections.Counter(v.split(":", 1)[1] for v in via.values() if str(v).startswith("cells:"))
        rivals = [a for a in ("A", "B", "Cn", "S", "D") if a in so]
        f = {"tasks": n, "solved": {a: len(s) for a, s in so.items()}, "cpu_seconds": cpu,
             "C_vs_Cn": _vs(so, "C", "Cn"), "exclusive": sorted(so["C"] - set().union(*[so[a] for a in rivals])),
             "gain_structure_classes": dict(cls),
             "C_solved_via_cells": sum(str(by["C"][i]["via"]).startswith("cells:") for i in so["C"]),
             "C_fit_via_cells": sum(r["fit"] and str(r["via"]).startswith("cells:") for r in by["C"].values()),
             "gain": {i: {"via": via[i], "program": by["C"][i]["program"]} for i in gain},
             "Cn_only": {i: by["C"][i]["via"] for i in sorted(so["Cn"] - so["C"])},
             "solved_ids": {a: sorted(s) for a, s in so.items()}}
        w, p = f["C_vs_Cn"]["first_only"], f["C_vs_Cn"]["mcnemar_p"]
        if fam == "rule":
            k = {"R1": w >= 5 and p < 0.01, "R2": len(f["exclusive"]) >= 5,
                 "R3": len(cls) >= 3 and max(cls.values()) <= 0.6 * sum(cls.values()) if cls else False,
                 "R4": cpu["C"] <= cpu["Cn"]}
        elif fam in ("rule_target", "dc"):
            k = {"V1": w >= 5 and p < 0.025, "V2": len(f["exclusive"]) >= 5}
        else:
            k = {}
        f["criterion"] = k
        f["pass"] = all(k.values()) if k else None
        rec["families"][fam] = f
    rec["iteration_pass"] = all(f["pass"] for f in rec["families"].values() if f["pass"] is not None)
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    for fam, f in rec["families"].items():
        print(fam, f["solved"], "cpu", f["cpu_seconds"])
        print("   C vs Cn", f["C_vs_Cn"], "exclusive", len(f["exclusive"]), "classes", f["gain_structure_classes"],
              "criterion", f["criterion"], "->", f["pass"])
    print("ITERATION 4", "PASS" if rec["iteration_pass"] else "FAIL")


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1]](*sys.argv[2:])
