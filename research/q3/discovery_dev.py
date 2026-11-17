"""SOURCE-only development of the learned discovery policy (never evidence for a gate).

  wake <bigbench> <oeis> <rule:cap_s,oeis:cap_s> <rows.jsonl>
      Experience: the base proposer with the UNTRAINED policy and a large cap on every SOURCE task.
      Resumable.  Rows keep the verified method and every hypothesis tried.
  cv <bigbench> <oeis> <cap_s> <wake_rows.jsonl> <rows.jsonl>
      5-fold cross-validation over SOURCE tasks.  For each fold the policy is fitted on the wake rows of the
      OTHER folds (both domains pooled: one policy), then every arm runs the held-out tasks under the same cap.
        S  the frozen THIRD core (specialist for lists)        D  sequence specialist (oeis only)
        A  base proposer, untrained policy, no memory
        B  A + memory of verified methods (no policy learning)  = the causal control for the policy
        C  B + learned policy (hypothesis weights, generative costs, latent-variable proposals)
        Cw C without the latent-variable proposals (attribution only)
"""
from __future__ import annotations
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc
import dev_source, invention_first as first, sequence_specialist

FOLDS = 5
INV = None
POLICY = {}


def fold_of(tid):
    return int(first.sha256(("neumann-discovery-cv-v1:" + tid).encode()), 16) % FOLDS


def _inv():
    global INV
    if INV is None:
        INV = sc.load_inverses()
    return INV


def _row(t, r, **kw):
    r = dict(r, id=t["id"], in_types=list(t["in_types"]), out_type=t["out_type"], sig=ic.sig_key(t), **kw)
    return r


def wake_job(a):
    t, cap = a
    return _row(t, dc.solve(t, cap, dc.Policy(), _inv(), features=True, replay=False))


def cv_job(a):
    arm, t, cap = a
    if arm == "D":
        tr, te = [o for _, o in t["train"]], [o for _, o in t["test"]]
        p = sequence_specialist.predict(tr, len(te))
        return {"id": t["id"], "arm": arm, "fit": p is not None, "solved": p == te, "cpu_seconds": 0.0}
    if arm == "S":
        r = sc.solve(t, cap, "S", _inv())
    else:
        pol = POLICY[fold_of(t["id"])]
        if arm == "A":
            r = dc.solve(t, cap, dc.Policy(), _inv(), replay=False)
        elif arm == "B":
            r = dc.solve(t, cap, dc.Policy(memory=pol.memory), _inv())
        elif arm == "Cw":                   # ablation: learned weights and costs, no latent-variable proposals
            r = dc.solve(t, cap, dc.Policy(pol.costs, pol.weights, pol.memory), _inv())
        else:
            r = dc.solve(t, cap, pol, _inv())
    r.pop("sol", None)
    return _row(t, r, arm=arm)


def _run(job, jobs, out, key):
    done = set()
    try:
        done = {key(json.loads(l)) for l in open(out)}
    except FileNotFoundError:
        pass
    todo = [j for j in jobs if (j[0], j[1]["id"]) not in done] if len(jobs[0]) == 3 else \
           [j for j in jobs if j[0]["id"] not in done]
    print("jobs", len(jobs), "todo", len(todo), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, todo):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def wake(bigbench, oeis, caps, out):
    """caps: 'rule:120,oeis:30' (CPU seconds per task and family; the experience budget, reported as cost)."""
    d = dev_source.load(bigbench, oeis)
    cap = {k: float(v) for k, v in (c.split(":") for c in caps.split(","))}
    _run(wake_job, [(t, cap[f]) for f in cap for t in d[f]], out, lambda r: r["id"])


def policies(wake_rows):
    rows = [json.loads(l) for l in open(wake_rows)]
    return {f: dc.fit([r for r in rows if fold_of(r["id"]) != f]) for f in range(FOLDS)}, rows


def cv(bigbench, oeis, cap, wake_rows, out):
    global POLICY
    POLICY, _ = policies(wake_rows)
    d = dev_source.load(bigbench, oeis)
    jobs = [(arm, t, float(cap)) for f in ("rule", "oeis") for arm in ("C", "B", "A", "S", "D", "Cw") for t in d[f]
            if not (arm == "D" and f != "oeis")]
    _run(cv_job, jobs, out, lambda r: (r["arm"], r["id"]))


ALPHA = 0.05 / 4                  # Bonferroni over 2 domains x {C vs B, C vs A}
MIN_EXCLUSIVE = 5


def _vs(so, a, b):
    w, l = len(so[a] - so[b]), len(so[b] - so[a])
    return {"first_only": w, "second_only": l, "mcnemar_p": first.mcnemar(w, l)}


def report(wake_rows, cv_rows, out, label):
    """The pre-defined criterion K1-K4 per domain, and the immutable record of the iteration."""
    import collections
    pols, wrows = policies(wake_rows)
    rows = [json.loads(l) for l in open(cv_rows)]
    rec = {"schema": "neumann.discovery-policy.iteration.v1", "label": label,
           "note": "SOURCE-only development; cross-validated; not evidence for any gate",
           "alpha_per_test": ALPHA, "min_exclusive": MIN_EXCLUSIVE, "folds": FOLDS, "domains": {},
           "experience": {}, "policy_fold0": {}}
    for fam in ("rule", "oeis"):
        ws = [r for r in wrows if r["id"].startswith(fam + "/")]
        rec["experience"][fam] = {"tasks": len(ws), "cpu_seconds": round(sum(r["cpu_seconds"] for r in ws), 1),
                                  "train_verified": sum(r["fit"] for r in ws),
                                  "via": dict(collections.Counter(str(r["via"]) for r in ws if r["fit"]))}
        by = {}
        for r in rows:
            if r["id"].startswith(fam + "/"):
                by.setdefault(r["arm"], {})[r["id"]] = r
        n = len(by["C"])
        assert all(len(v) == n for v in by.values()), {a: len(v) for a, v in by.items()}
        so = {a: {i for i, r in v.items() if r["solved"]} for a, v in by.items()}
        cpu = {a: round(sum(r["cpu_seconds"] for r in v.values()), 1) for a, v in by.items()}
        rivals = [a for a in ("A", "B", "S", "D") if a in by]
        excl = sorted(so["C"] - set().union(*[so[a] for a in rivals]))
        k = {"K1": _vs(so, "C", "B"), "K2": _vs(so, "C", "A")}
        k["K1"]["pass"] = k["K1"]["first_only"] >= MIN_EXCLUSIVE and k["K1"]["mcnemar_p"] < ALPHA
        k["K2"]["pass"] = len(so["C"]) > len(so["A"]) and k["K2"]["mcnemar_p"] < ALPHA
        k["K3"] = {"exclusive": excl, "pass": len(excl) >= MIN_EXCLUSIVE}
        k["K4"] = {"cpu_C": cpu["C"], "cpu_B": cpu["B"], "pass": cpu["C"] <= cpu["B"]}
        rec["domains"][fam] = {
            "tasks": n, "solved": {a: len(s) for a, s in so.items()}, "fit": {a: sum(r["fit"] for r in v.values()) for a, v in by.items()},
            "cpu_seconds": cpu, "criterion": k, "pass": all(v["pass"] for v in k.values()),
            "C_via": dict(collections.Counter(str(by["C"][i]["via"]) for i in so["C"])),
            "C_vs_S": _vs(so, "C", "S"), "C_vs_Cw": _vs(so, "C", "Cw") if "Cw" in so else None,
            "B_vs_A": _vs(so, "B", "A"), "A_vs_S": _vs(so, "A", "S"),
            "C_only_vs_B": {i: {"via": by["C"][i]["via"], "program": by["C"][i]["program"]} for i in sorted(so["C"] - so["B"])},
            "B_only_vs_C": sorted(so["B"] - so["C"]),
            "solved_ids": {a: sorted(s) for a, s in so.items()}}
    p0 = pols[0]
    rec["policy_fold0"] = {"weights": {"/".join([k[0], k[1], ",".join(map(str, k[2]))]): round(v, 4)
                                       for k, v in sorted(p0.weights.items(), key=lambda kv: -kv[1])},
                           "features": [[ic.show(f), list(st), t] for f, st, t in p0.features],
                           "memory_size": len(p0.memory), "cost_contexts": ["/".join(k) for k in sorted(p0.costs)]}
    rec["iteration_pass"] = all(d["pass"] for d in rec["domains"].values())
    import pathlib
    pathlib.Path(out).write_text(json.dumps(rec, indent=1, sort_keys=True))
    for fam, d in rec["domains"].items():
        print(fam, d["solved"], "cpu", d["cpu_seconds"])
        print("  ", {k: {x: y for x, y in v.items() if x != "exclusive"} for k, v in d["criterion"].items()},
              "exclusive", len(d["criterion"]["K3"]["exclusive"]), "PASS" if d["pass"] else "FAIL")
        print("   C via", d["C_via"], "C vs S", d["C_vs_S"], "C vs Cw", d["C_vs_Cw"])
    print("experience", rec["experience"])
    print("ITERATION", "PASS" if rec["iteration_pass"] else "FAIL")


if __name__ == "__main__":
    {"wake": wake, "cv": cv, "report": report}[sys.argv[1]](*sys.argv[2:])
