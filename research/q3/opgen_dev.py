"""Iteration 3 (SOURCE only): failure-derived operation generation.

  invent <bigbench> <oeis> <iter1_cv_rows> <cap_s> <ops_rows.jsonl>
      For every SOURCE task that arm B (learned policy + memory; iteration 1's arm C) did not TRAIN-verify,
      synthesise operations from its gaps (`opgen.gaps`).  Hidden tests are never read.  Resumable.
  cv <bigbench> <oeis> <cap_s> <wake_rows> <ops_rows> <rows.jsonl>
      The same 5 folds as iteration 1.  For a fold, the policy AND the operation set use the other folds only.
        Cn  B + recursive goal graph, no generated operation      (C with the generation removed)
        C   Cn + generated operations (forward at a fixed cost, backward where recoverable)
      A, B, S, D are the rows of iteration 1 (same code, cap and folds).
  report <iter1_cv_rows> <ops_rows> <rows> <record.json>
"""
from __future__ import annotations
import collections, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc, opgen
import dev_source, discovery_dev as dd, invention_first as first

ALPHA = 0.05 / 2                 # Bonferroni over the two domains (C vs Cn)
MIN_TASKS = 5
INV = None
FOLD = {}


def _inv():
    global INV
    if INV is None:
        INV = sc.load_inverses()
    return INV


def invent_job(a):
    t, cap = a
    ops, meta = opgen.gaps(t, _inv(), cap)
    return dict(meta, id=t["id"], ops=ops)


def _resume(out, key):
    try:
        return {key(json.loads(l)) for l in open(out)}
    except FileNotFoundError:
        return set()


def invent(bigbench, oeis, iter1_rows, cap, out):
    d = dev_source.load(bigbench, oeis)
    failed = {r["id"] for r in map(json.loads, open(iter1_rows)) if r["arm"] == "C" and not r["fit"]}
    done = _resume(out, lambda r: r["id"])
    jobs = [(t, float(cap)) for f in ("rule", "oeis") for t in d[f] if t["id"] in failed and t["id"] not in done]
    print("failed", len(failed), "todo", len(jobs), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(invent_job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def fold_sets(wake_rows, ops_rows):
    pols, _ = dd.policies(wake_rows)
    rows = [json.loads(l) for l in open(ops_rows)]
    out = {}
    for f in range(dd.FOLDS):
        held = {r["id"] for r in rows if dd.fold_of(r["id"]) == f}
        spec, table, rec = opgen.select(rows, exclude=held)
        out[f] = (pols[f], spec, table, rec)
    return out


def cv_job(a):
    arm, t, cap = a
    pol, spec, _, rec = FOLD[dd.fold_of(t["id"])]
    if arm == "Cn":
        r = dc.solve(t, cap, pol, _inv(), spec=opgen.seed_spec(), ops={})
    else:
        r = dc.solve(t, cap, pol, _inv(), spec=spec, ops=rec)
    r.pop("sol", None)
    r.pop("tried", None)
    return dict(r, id=t["id"], arm=arm)


def cv(bigbench, oeis, cap, wake_rows, ops_rows, out):
    global FOLD
    FOLD = fold_sets(wake_rows, ops_rows)
    d = dev_source.load(bigbench, oeis)
    done = _resume(out, lambda r: (r["arm"], r["id"]))
    jobs = [(arm, t, float(cap)) for f in ("rule", "oeis") for arm in ("C", "Cn") for t in d[f]
            if (arm, t["id"]) not in done]
    print("todo", len(jobs), {f: [(o["name"], o["program"], o["support"]) for o in v[2]] for f, v in FOLD.items()},
          flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(cv_job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def report(iter1_rows, wake_rows, ops_rows, rows_path, out):
    sets = fold_sets(wake_rows, ops_rows)
    inv_rows = [json.loads(l) for l in open(ops_rows)]
    rows = [r for r in map(json.loads, open(iter1_rows)) if r["arm"] in ("A", "C", "S", "D")]
    for r in rows:
        r["arm"] = {"C": "B"}.get(r["arm"], r["arm"])          # iteration 1's arm C is this iteration's arm B
    rows += [json.loads(l) for l in open(rows_path)]
    name_key = {(f, o["name"]): o for f, v in sets.items() for o in v[2]}
    rec = {"schema": "neumann.discovery-policy.iteration.v1",
           "label": "iteration 3: failure-derived operation generation (SOURCE 5-fold CV)",
           "note": "SOURCE-only development; not evidence for any gate", "alpha_per_test": ALPHA,
           "invention": {"tasks": len(inv_rows), "cpu_seconds": round(sum(r["cpu_seconds"] for r in inv_rows), 1),
                         "specifications_posed": sum(r["specs"] for r in inv_rows),
                         "definitions_synthesised": sum(len(r["ops"]) for r in inv_rows),
                         "distinct_definitions": len({o["key"] for r in inv_rows for o in r["ops"]})},
           "operations_by_fold": {str(f): v[2] for f, v in sets.items()}, "domains": {}}
    for fam in ("rule", "oeis"):
        by = {}
        for r in rows:
            if r["id"].startswith(fam + "/"):
                by.setdefault(r["arm"], {})[r["id"]] = r
        n = len(by["C"])
        assert all(len(v) == n for v in by.values()), {a: len(v) for a, v in by.items()}
        so = {a: {i for i, r in v.items() if r["solved"]} for a, v in by.items()}
        cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
        used = {i: [name_key[(dd.fold_of(i), n_)] for n_ in by["C"][i].get("ops_used", []) if n_ != "len"]
                for i in so["C"]}
        used = {i: v for i, v in used.items() if v}
        gain = sorted(so["C"] - so["Cn"])
        keys = collections.Counter(o["key"] for i in gain for o in used.get(i, []))
        novel = sorted({o["program"] for v in used.values() for o in v if o["same_as_existing"] is None})
        w, l = len(so["C"] - so["Cn"]), len(so["Cn"] - so["C"])
        g = {"G1_new_operation_used": {"programs": novel, "pass": len(novel) >= 1},
             "G2_tasks_solved_with_a_generated_operation": {"n": len(used), "pass": len(used) >= MIN_TASKS},
             "G3_causal": {"C_only": w, "Cn_only": l, "mcnemar_p": first.mcnemar(w, l),
                           "pass": w >= MIN_TASKS and first.mcnemar(w, l) < ALPHA},
             "G4_not_concentrated": {"operations_in_gain": dict(keys),
                                     "pass": len(keys) >= 2 and max(keys.values()) <= 0.75 * max(1, len(gain))},
             "G5_cost": {"cpu_C": cpu["C"], "cpu_Cn": cpu["Cn"], "pass": cpu["C"] <= cpu["Cn"]}}
        rivals = [a for a in ("A", "B", "Cn", "S", "D") if a in by]
        rec["domains"][fam] = {
            "tasks": n, "solved": {a: len(s) for a, s in so.items()}, "cpu_seconds": cpu, "criterion": g,
            "pass": all(v["pass"] for v in g.values()),
            "C_vs_B": {"C_only": len(so["C"] - so["B"]), "B_only": len(so["B"] - so["C"]),
                       "mcnemar_p": first.mcnemar(len(so["C"] - so["B"]), len(so["B"] - so["C"]))},
            "solved_by_C_and_no_other_arm": sorted(so["C"] - set().union(*[so[a] for a in rivals])),
            "gain": {i: {"via": by["C"][i]["via"], "ops": [o["program"] for o in used.get(i, [])],
                         "program": by["C"][i]["program"]} for i in gain},
            "Cn_only": sorted(so["Cn"] - so["C"]), "solved_ids": {a: sorted(s) for a, s in so.items()}}
    rec["iteration_pass"] = all(d["pass"] for d in rec["domains"].values())
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    print("invention", rec["invention"])
    for f, ops in rec["operations_by_fold"].items():
        print("fold", f, [(o["name"], o["program"], o["support"], o["same_as_existing"], o["recoverable_arguments"]) for o in ops])
    for fam, d in rec["domains"].items():
        print(fam, d["solved"], "cpu", d["cpu_seconds"])
        for k, v in d["criterion"].items():
            print("   ", k, v)
        print("    C vs B", d["C_vs_B"], "exclusive", len(d["solved_by_C_and_no_other_arm"]), "PASS" if d["pass"] else "FAIL")
    print("ITERATION 3", "PASS" if rec["iteration_pass"] else "FAIL")


if __name__ == "__main__":
    {"invent": invent, "cv": cv, "report": report}[sys.argv[1]](*sys.argv[2:])
