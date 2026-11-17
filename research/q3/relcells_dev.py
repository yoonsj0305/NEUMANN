"""Stage A (first-principles redefinition): relational factorisation, one principle, two semantic domains.

  run <bigbench> <ec> <oeis> <wake_rows> <rows.jsonl>
      arms R (relational cells: self sources + linked relations) and R0 (the same construction with both removed)
      on rule SOURCE and OEIS SOURCE (gating) and on rule TARGET and dc (reported only: used by iteration 4)
  report <iter1_cv_rows> <iter4_rows> <third_rows> <rows> <record.json>
"""
from __future__ import annotations
import collections, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import spec_core as sc, discovery_core as dc
import dev_source, discovery_dev as dd, invention_eval2 as ev2, invention_first as first, cells_dev

CAP = 6.0
ALPHA = 0.05 / 2
INV = None
POL = {}


def job(a):
    global INV
    arm, fam, t = a
    if INV is None:
        INV = sc.load_inverses()
    pol = POL[dd.fold_of(t["id"])] if fam in ("rule", "oeis") else POL["all"]
    r = dc.solve(t, CAP, pol, INV, cells={"R": "rel", "R0": "rel0"}[arm])
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
    jobs = [(arm, f, t) for f, ts in fams.items() for arm in ("R", "R0") for t in ts if (arm, t["id"]) not in done]
    print("todo", len(jobs), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def report(iter1_rows, iter4_rows, third_rows, rows_path, out):
    rows = [json.loads(l) for l in open(rows_path)]
    old = [r for r in map(json.loads, open(iter1_rows)) if r["arm"] in ("A", "C", "S", "D")]
    for r in old:
        r["arm"] = {"C": "B"}.get(r["arm"], r["arm"])
        r["family"] = r["id"].split("/")[0]
    it4 = [dict(r, arm={"C": "C4"}.get(r["arm"], r["arm"])) for r in map(json.loads, open(iter4_rows))]
    third = [{"id": r["key"][2], "arm": "S", "solved": r["solved"], "cpu_seconds": r["cpu_seconds"],
              "family": {"rule": "rule_target", "dc": "dc"}[r["key"][0]]}
             for r in map(json.loads, open(third_rows)) if r["key"][1] == "S" and r["key"][0] in ("rule", "dc")]
    rec = {"schema": "neumann.stage-a.v1", "label": "Stage A: relational factorisation, two semantic domains",
           "cap_cpu_seconds": CAP, "alpha_per_test": ALPHA, "families": {}}
    for fam in ("rule", "oeis", "rule_target", "dc"):
        by = {}
        for r in rows + old + it4 + third:
            if r["family"] == fam:
                by.setdefault(r["arm"], {})[r["id"]] = r
        n = len(by["R"])
        assert all(len(v) == n for v in by.values()), (fam, {a: len(v) for a, v in by.items()})
        so = {a: {i for i, r in v.items() if r["solved"]} for a, v in by.items()}
        cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
        gain = sorted(so["R"] - so["R0"])
        attributed = [i for i in gain if "self" in str(by["R"][i]["via"]) or "linked" in str(by["R"][i]["via"])]
        rivals = [a for a in ("A", "B", "Cn", "C4", "R0", "S", "D") if a in so]
        excl = sorted(so["R"] - set().union(*[so[a] for a in rivals]))
        vs = cells_dev._vs(so, "R", "R0")
        k = {"A1": vs["first_only"] >= 5 and vs["mcnemar_p"] < ALPHA, "A2": len(excl) >= 3,
             "A3": bool(gain) and len(attributed) >= 0.8 * len(gain), "A4": cpu["R"] <= 1.05 * cpu["R0"]}
        gating = fam in ("rule", "oeis")
        rec["families"][fam] = {
            "tasks": n, "gating": gating, "solved": {a: len(s) for a, s in so.items()}, "cpu_seconds": cpu,
            "R_vs_R0": vs, "R_vs_Cn": cells_dev._vs(so, "R", "Cn") if "Cn" in so else None,
            "R_vs_D": cells_dev._vs(so, "R", "D") if "D" in so else None,
            "exclusive": excl, "gain_attributed_to_self_or_linked": len(attributed),
            "criterion": k, "pass": all(k.values()) if gating else None,
            "R_fit": sum(r["fit"] for r in by["R"].values()),
            "R_via": dict(collections.Counter(str(by["R"][i]["via"]).split(":")[0] for i in so["R"])),
            "gain": {i: {"via": by["R"][i]["via"], "program": by["R"][i]["program"]} for i in gain},
            "R0_only": sorted(so["R0"] - so["R"]), "solved_ids": {a: sorted(s) for a, s in so.items()}}
    rec["stage_a_pass"] = all(f["pass"] for f in rec["families"].values() if f["gating"])
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    for fam, f in rec["families"].items():
        print(fam, "gating" if f["gating"] else "reported", f["solved"], "cpu", f["cpu_seconds"])
        print("   R vs R0", f["R_vs_R0"], "excl", len(f["exclusive"]), "attributed", f["gain_attributed_to_self_or_linked"],
              "criterion", f["criterion"], "->", f["pass"])
    print("STAGE A", "PASS" if rec["stage_a_pass"] else "FAIL")


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1]](*sys.argv[2:])
