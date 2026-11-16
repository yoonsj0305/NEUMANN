"""DEVELOPMENT ONLY: verdicts of the pre-registered section 40 evaluation from raw rows -- no new run.

Rules are those of docs/experiments/dev/psi40/prereg.json (frozen before the evaluation):
* verified solve: hidden test passed AND every random diagnostic SOURCE input correct (300 inputs);
* robust: an arm robustly verifies a task when it verifies it in a strict majority of its runs (base run, plus the
  replicates when the task was replicated);
* CORE EVIDENCE (per task): Q (PSI40) robustly verifies it with an accepted machine that contains a PSI40 state, and
  none of A, P (PSI39), AL (A + the length floor) and Qno (PSI40 with the state withheld) robustly verifies it;
* V2 rule (the frozen formal V2 criterion, Q in D's place, QDq in Dq's): >= 5 tasks solved by Q with an accepted
  machine of m >= 2 state components that QDq (Q's SOURCE queries replayed, solved passively) does not solve;
  PSI40 attribution = how many of those tasks have a PSI40 state in the accepted machine and are not solved by Qno;
* REGRESSION: tasks A robustly verifies and Q does not (reported, never excluded);
* cost: real CPU and formation SOURCE queries per arm and group.
Official sealed verdicts are not changed by anything computed here.

  python research/q3/psi40_verdict_dev.py --base run1.jsonl [--reps r2.jsonl r3.jsonl seeds.jsonl] [--dq qdq.jsonl]
"""
from __future__ import annotations
import argparse
import json
import math


def verified(r):
    s = r.get("semantic_random300")
    return bool(r and r["solved"] and s and s[0] == s[1] and s[1] > 0)


def accepted_m(r):
    """state components of the accepted machine: the answer plus every added component (continuation or invented)"""
    best = 0
    for m in r["machines"]:
        if m["challenge"] is True:
            best = max(best, 1 + len(m.get("components") or []))
    return best


def psi40_states(r):
    return [c.get("update") for m in r["machines"] if m["challenge"] is True
            for c in m.get("components") or [] if c.get("source") == "psi40"]


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n)


def load(paths):
    return [json.loads(l) for p in paths or [] for l in open(p) if l.strip()]


def main(a):
    base = load(a.base)
    by = {}
    for r in base:
        by.setdefault(r["name"], {})[r["arm"]] = r
    runs = {}
    for r in base + load(a.reps):
        runs.setdefault((r["arm"], r["name"]), []).append(verified(r))

    def robust(arm, name):
        v = runs.get((arm, name), [])
        return bool(v) and 2 * sum(v) > len(v)
    ev = json.load(open(a.eval_set))
    group = {t["name"]: g for g in ("lr_need30", "lr_ord12", "fst16", "rha16") for t in ev[g]}
    out = {"tasks": len(by), "arms": {}, "groups": {}}
    arms = sorted({x for v in by.values() for x in v})
    for arm in arms:
        rs = [v[arm] for v in by.values() if arm in v]
        out["arms"][arm] = {"runs": len(rs), "verified": sum(verified(r) for r in rs),
                            "robust_verified": sum(robust(arm, r["name"]) for r in rs),
                            "solved": sum(r["solved"] for r in rs), "cpu": round(sum(r["cpu"] for r in rs), 2),
                            "formation_queries": sum(r["formation_queries"] for r in rs)}
    for g in ("lr_need30", "lr_ord12", "fst16", "rha16"):
        names = [n for n in by if group.get(n) == g]
        out["groups"][g] = {arm: {"robust_verified": sorted(n for n in names if arm in by[n] and robust(arm, n)),
                                  "cpu": round(sum(by[n][arm]["cpu"] for n in names if arm in by[n]), 2)}
                            for arm in arms if any(arm in by[n] for n in names)}
    ctrl = ("A", "P", "AL", "Qno")
    core = []
    for n, v in sorted(by.items()):
        if "Q" in v and robust("Q", n) and psi40_states(v["Q"]) and all(not robust(c, n) for c in ctrl if c in v):
            core.append({"task": n, "group": group.get(n), "states": psi40_states(v["Q"]),
                         "Q_runs": runs[("Q", n)], "control_runs": {c: runs.get((c, n)) for c in ctrl if c in v},
                         "semantic": v["Q"].get("semantic_random300")})
    out["core_evidence"] = core
    out["Q_regressions_vs_A"] = sorted(n for n, v in by.items() if "A" in v and "Q" in v and robust("A", n)
                                       and not robust("Q", n))
    both = [n for n, v in by.items() if "A" in v and "Q" in v]
    q_only = sorted(n for n in both if robust("Q", n) and not robust("A", n))
    a_only = sorted(n for n in both if robust("A", n) and not robust("Q", n))
    out["Q_vs_A"] = {"Q_only": q_only, "A_only": a_only, "p": round(mcnemar(len(q_only), len(a_only)), 4)}
    dq = {r["name"]: r for r in load(a.dq)}
    v2 = sorted(n for n, v in by.items() if "Q" in v and v["Q"]["solved"] and accepted_m(v["Q"]) >= 2
                and n in dq and not dq[n]["solved"])
    attr = sorted(n for n in v2 if psi40_states(by[n]["Q"]) and not ("Qno" in by[n] and by[n]["Qno"]["solved"]))
    out["V2_rule"] = {"tasks": v2, "count": len(v2), "threshold": 5, "met": len(v2) >= 5,
                      "psi40_attribution": attr, "psi40_attribution_count": len(attr), "qdq_runs": len(dq)}
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--reps", nargs="*")
    ap.add_argument("--dq", nargs="*")
    ap.add_argument("--eval-set", default="docs/experiments/dev/psi40/eval_set.json")
    main(ap.parse_args())
