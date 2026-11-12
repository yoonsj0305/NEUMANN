"""Development validation of inverted inventions on the opened TARGET list families (never first-exposure).

  run <bigbench> <ec> <oeis> <cap_s> <rows.jsonl>     arms S, V0, V on rule TARGET and dc (resumable)
  report <rows.jsonl> <record.json>                    the pre-defined criterion J1-J3 per family

The inventions are the 8 abstractions of the frozen core (learned on SOURCE before FIRST; file unchanged).
V0 = the same recursive goal graph with primitive inverses only: the control with the inventions removed.
The opened TARGET sets are development-only since SECOND failed on them; nothing here is evidence for a gate.
"""
from __future__ import annotations
import collections, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import spec_core as sc, inverted as iv
import invention_eval2 as ev2, invention_first as first

FAMILIES = ("rule", "dc")
ARMS = ("V", "V0", "S")
ALPHA = 0.05 / 2                  # Bonferroni over the two families (V vs V0)
MIN_EXCLUSIVE = 5
SPEC = [tuple(x) for x in json.loads(pathlib.Path(first.FROZEN).read_text())["spec"]]
OPS = iv.derive_op_inverses(SPEC)
INV = None


def job(a):
    global INV
    arm, t, cap = a
    if INV is None:
        INV = sc.load_inverses()
    r = sc.solve(t, cap, "S", INV) if arm == "S" else iv.solve(t, cap, INV, SPEC, OPS if arm == "V" else {})
    r.pop("sol", None)
    r.pop("levels", None)
    return dict(r, id=t["id"], arm=arm)


def run(bigbench, ec, oeis, cap, out):
    fams = ev2.plan_tasks("second", bigbench, ec, oeis)
    done = set()
    try:
        done = {(r["arm"], r["id"]) for r in map(json.loads, open(out))}
    except FileNotFoundError:
        pass
    jobs = [(arm, t, float(cap)) for f in FAMILIES for arm in ARMS for t in fams[f]
            if "unsupported" not in t and (arm, t["id"]) not in done]
    print("todo", len(jobs), "ops", OPS, flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def report(rows_path, out):
    rows = [json.loads(l) for l in open(rows_path)]
    rec = {"schema": "neumann.discovery-policy.iteration.v1", "label": "iteration 2: inverted inventions",
           "note": "development validation on opened TARGET list families; not evidence for any gate",
           "inventions": [n for n, *_ in SPEC], "recoverable_arguments": OPS,
           "alpha_per_test": ALPHA, "min_exclusive": MIN_EXCLUSIVE, "families": {}}
    for fam in FAMILIES:
        by = {}
        for r in rows:
            if r["id"].startswith(fam + "/"):
                by.setdefault(r["arm"], {})[r["id"]] = r
        n = len(by["V"])
        assert all(len(v) == n for v in by.values()), {a: len(v) for a, v in by.items()}
        so = {a: {i for i, r in v.items() if r["solved"]} for a, v in by.items()}
        cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
        w, l = len(so["V"] - so["V0"]), len(so["V0"] - so["V"])
        p = first.mcnemar(w, l)
        excl = sorted(so["V"] - so["V0"] - so["S"])
        k = {"J1": {"V_only": w, "V0_only": l, "mcnemar_p": p, "pass": w >= MIN_EXCLUSIVE and p < ALPHA},
             "J2": {"exclusive": excl, "pass": len(excl) >= MIN_EXCLUSIVE},
             "J3": {"cpu_V": cpu["V"], "cpu_V0": cpu["V0"], "pass": cpu["V"] <= cpu["V0"]}}
        rec["families"][fam] = {
            "tasks": n, "solved": {a: len(s) for a, s in so.items()},
            "fit": {a: sum(r["fit"] for r in v.values()) for a, v in by.items()}, "cpu_seconds": cpu,
            "criterion": k, "pass": all(v["pass"] for v in k.values()),
            "V_via": dict(collections.Counter(str(by["V"][i]["via"]) for i in so["V"])),
            "V_vs_S": {"V_only": len(so["V"] - so["S"]), "S_only": len(so["S"] - so["V"]),
                       "mcnemar_p": first.mcnemar(len(so["V"] - so["S"]), len(so["S"] - so["V"]))},
            "V_only_vs_V0": {i: {"cpu": by["V"][i]["cpu_seconds"], "program": by["V"][i]["program"]}
                             for i in sorted(so["V"] - so["V0"])},
            "solved_ids": {a: sorted(s) for a, s in so.items()}}
    rec["iteration_pass"] = all(f["pass"] for f in rec["families"].values())
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    for fam, f in rec["families"].items():
        print(fam, f["solved"], "cpu", f["cpu_seconds"], "via", f["V_via"])
        print("  ", {k: {x: y for x, y in v.items() if x != "exclusive"} for k, v in f["criterion"].items()},
              "exclusive", len(f["criterion"]["J2"]["exclusive"]), "V vs S", f["V_vs_S"], "PASS" if f["pass"] else "FAIL")
    print("ITERATION 2", "PASS" if rec["iteration_pass"] else "FAIL")


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1]](*sys.argv[2:])
