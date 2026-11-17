"""Representation formation and learning, separated (SOURCE only).

  run12 <bigbench> <oeis> <wake_rows> <rows.jsonl>   arms R1 (substrate only) and R2 (formation) on SOURCE
  run3  <bigbench> <oeis> <wake_rows> <rows.jsonl>   arm R3: R2 + prior fitted on R2's verified
                                                     representations of the OTHER folds
  report <iter1_cv_rows> <iter4_rows> <stage_a_rows> <rows> <record.json>
R0 = the Stage A arm R (rows re-used).  Cap 6 CPU s, everything included, for every arm.
"""
from __future__ import annotations
import collections, json, pathlib, re, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import spec_core as sc, discovery_core as dc, latent as lt
import dev_source, discovery_dev as dd, invention_first as first

CAP = 6.0
ALPHA = 0.05 / 2
LATENT = ("lat", "residual", "transport", "keep")
INV = None
POL = {}


def job(a):
    global INV
    arm, fam, t = a
    if INV is None:
        INV = sc.load_inverses()
    f = dd.fold_of(t["id"])
    key = "R3:%d" % f if arm == "R3" else arm
    r = dc.solve(t, CAP, POL[f], INV, cells=key)
    sol = r.pop("sol", None)
    r.pop("tried", None)
    if sol is not None and sol[0] in LATENT:
        r["kinds"] = lt.kinds(sol)
        r["progs"] = [[c, p, list(ts)] for c, p, ts in lt.programs(sol, t)]
    return dict(r, id=t["id"], arm=arm, family=fam)


def _go(arms, bigbench, oeis, wake_rows, out):
    global POL
    POL, _ = dd.policies(wake_rows)
    src = dev_source.load(bigbench, oeis)
    done = set()
    try:
        done = {(r["arm"], r["id"]) for r in map(json.loads, open(out))}
    except FileNotFoundError:
        pass
    jobs = [(arm, f, t) for f in ("rule", "oeis") for arm in arms for t in src[f] if (arm, t["id"]) not in done]
    print("todo", len(jobs), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def run12(bigbench, oeis, wake_rows, out):
    dc.LATENT_CFG.update({"R1": lt.Cfg(subst=True), "R2": lt.Cfg(subst=True, latent=True)})
    _go(("R2", "R1"), bigbench, oeis, wake_rows, out)


def priors(rows):
    r2 = [r for r in rows if r["arm"] == "R2" and r["fit"] and r.get("progs") is not None]
    out = {}
    for f in range(dd.FOLDS):
        exp = [(r["kinds"], [(c, p, ts) for c, p, ts in r["progs"]]) for r in r2 if dd.fold_of(r["id"]) != f]
        out[f] = lt.fit_prior(exp)
    return out


def run3(bigbench, oeis, wake_rows, out):
    rows = [json.loads(l) for l in open(out)]
    for f, cfg in priors(rows).items():
        dc.LATENT_CFG["R3:%d" % f] = cfg
        print("fold", f, "order", cfg.order, "contexts", sorted(cfg.prior), flush=True)
    _go(("R3",), bigbench, oeis, wake_rows, out)


def _shape(p):
    return re.sub(r"\b\d+\b", "#", p or "")


def _vs(so, a, b):
    w, l = len(so[a] - so[b]), len(so[b] - so[a])
    return {"first_only": w, "second_only": l, "mcnemar_p": first.mcnemar(w, l)}


def report(iter1_rows, iter4_rows, stage_a_rows, rows_path, out):
    rows = [json.loads(l) for l in open(rows_path)]
    old = [r for r in map(json.loads, open(iter1_rows)) if r["arm"] in ("A", "C", "S", "D")]
    for r in old:
        r["arm"] = {"C": "B"}.get(r["arm"], r["arm"])
        r["family"] = r["id"].split("/")[0]
    it4 = [dict(r, arm={"C": "C4"}.get(r["arm"], r["arm"])) for r in map(json.loads, open(iter4_rows))]
    sa = [dict(r, arm="R0") for r in map(json.loads, open(stage_a_rows)) if r["arm"] == "R"]
    rec = {"schema": "neumann.formation-learning.v1", "cap_cpu_seconds": CAP, "alpha_per_test": ALPHA, "domains": {}}
    for fam in ("rule", "oeis"):
        by = {}
        for r in rows + old + it4 + sa:
            if r["family"] == fam:
                by.setdefault(r["arm"], {})[r["id"]] = r
        n = len(by["R2"])
        assert all(len(v) == n for v in by.values()), (fam, {a: len(v) for a, v in by.items()})
        so = {a: {i for i, r in v.items() if r["solved"]} for a, v in by.items()}
        cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
        d = {"tasks": n, "solved": {a: len(s) for a, s in so.items()}, "cpu_seconds": cpu,
             "fit": {a: sum(r["fit"] for r in by[a].values()) for a in ("R0", "R1", "R2") + (("R3",) if "R3" in by else ())}}
        # formation: R2 vs R1
        gain = sorted(so["R2"] - so["R1"])
        formed = [i for i in gain if any(k in str(by["R2"][i]["via"]) for k in ("residual", "transport"))]
        rivals = [a for a in ("A", "B", "S", "D", "Cn", "C4", "R0", "R1") if a in so]
        excl = sorted(so["R2"] - set().union(*[so[a] for a in rivals]))
        v = _vs(so, "R2", "R1")
        d["formation"] = {"R2_vs_R1": v, "exclusive": excl, "gain_through_formed_latent": len(formed),
                          "criterion": {"F1": v["first_only"] >= 5 and v["mcnemar_p"] < ALPHA, "F2": len(excl) >= 3,
                                        "F3": bool(gain) and len(formed) >= 0.8 * len(gain),
                                        "F4": cpu["R2"] <= 1.05 * cpu["R1"]},
                          "gain": {i: {"via": by["R2"][i]["via"], "program": by["R2"][i]["program"]} for i in gain},
                          "R1_only": sorted(so["R1"] - so["R2"])}
        d["formation"]["pass"] = all(d["formation"]["criterion"].values())
        d["substrate_R1_vs_R0"] = _vs(so, "R1", "R0")
        if "R3" in by:                                      # learning: R3 vs R2
            g3 = sorted(so["R3"] - so["R2"])
            train_shapes = {f: {_shape(r["program"]) for r in by["R2"].values()
                                if r["fit"] and dd.fold_of(r["id"]) != f} for f in range(dd.FOLDS)}
            dup = [i for i in g3 if _shape(by["R3"][i]["program"]) in train_shapes[dd.fold_of(i)]]
            clean = [i for i in g3 if i not in dup]
            l3 = sorted(so["R2"] - so["R3"])
            p_clean = first.mcnemar(len(clean), len(l3))
            both = so["R3"] & so["R2"]
            c3 = sum(by["R3"][i]["cpu_seconds"] for i in both)
            c2 = sum(by["R2"][i]["cpu_seconds"] for i in both)
            d["learning"] = {"R3_vs_R2": _vs(so, "R3", "R2"), "gain_same_shape_as_training_fold": dup,
                             "gain_clean": clean, "mcnemar_p_clean": p_clean,
                             "cpu_on_tasks_both_solve": {"n": len(both), "R3": round(c3, 1), "R2": round(c2, 1)},
                             "criterion": {"L1_capability": len(clean) >= 5 and p_clean < ALPHA,
                                           "L2_cost": len(so["R3"]) >= len(so["R2"]) and c3 <= 0.7 * c2},
                             "gain": {i: {"via": by["R3"][i]["via"], "program": by["R3"][i]["program"]} for i in g3}}
            d["learning"]["pass"] = any(d["learning"]["criterion"].values())
        rec["domains"][fam] = d
    rec["formation_pass"] = all(d["formation"]["pass"] for d in rec["domains"].values())
    rec["learning_pass"] = all(d.get("learning", {}).get("pass", False) for d in rec["domains"].values())
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    for fam, d in rec["domains"].items():
        print(fam, d["solved"], "cpu", {a: d["cpu_seconds"][a] for a in d["fit"]}, "fit", d["fit"])
        f = d["formation"]
        print("   formation R2 vs R1", f["R2_vs_R1"], "excl", len(f["exclusive"]), "formed", f["gain_through_formed_latent"],
              f["criterion"], "->", f["pass"], "| substrate R1 vs R0", d["substrate_R1_vs_R0"])
        if "learning" in d:
            l = d["learning"]
            print("   learning R3 vs R2", l["R3_vs_R2"], "clean", len(l["gain_clean"]), "dup", len(l["gain_same_shape_as_training_fold"]),
                  l["cpu_on_tasks_both_solve"], l["criterion"], "->", l["pass"])
    print("FORMATION", "PASS" if rec["formation_pass"] else "FAIL", "| LEARNING", "PASS" if rec["learning_pass"] else "FAIL")


if __name__ == "__main__":
    {"run12": run12, "run3": run3, "report": report}[sys.argv[1]](*sys.argv[2:])
