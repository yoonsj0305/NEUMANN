"""DEVELOPMENT ONLY: verdicts of the pre-registered section 44 evaluation from raw rows -- no new run.

Rules of docs/experiments/dev/psi44/prereg.json (frozen before the evaluation):
* verified solve: hidden test passed AND every random diagnostic SOURCE input correct (300 inputs);
* robust: strict majority of an arm's runs on a task (base run, plus replicates where pre-registered);
* CORE EVIDENCE (per task): K robustly verifies it with an accepted machine containing the factored joint latent
  (component source psi44), and none of A, R (section 41, unchanged) and Kno (K with the joint machine withheld,
  same queries) robustly verifies it;
* V2 rule (frozen V2 criterion, K in D's place, KDq in Dq's): >= 5 tasks solved by K (hidden test) with an accepted
  machine of m >= 2 state components that KDq (K's SOURCE queries replayed, solved passively) does not solve;
  reported also with verified solves (substantive);
* V2 verdict: PASS if the rule is met AND >= 5 of its tasks carry core evidence; FAIL if not met; OPEN otherwise;
* REGRESSION: tasks A or R robustly verifies and K does not.
Official sealed verdicts are not changed by anything computed here.

  python research/q3/psi44_verdict_dev.py --base run1.jsonl [--reps ...] [--dq kdq.jsonl]
"""
from __future__ import annotations
import argparse
import json
import math

GROUPS = ("latent_need", "other")


def verified(r):
    s = r.get("semantic_random300")
    return bool(r and r["solved"] and s and s[0] == s[1] and s[1] > 0)


def accepted_m(r):
    return max([1 + len(m.get("components") or []) for m in r["machines"] if m["challenge"] is True] or [0])


def joint(r):
    return [c.get("update") for m in r["machines"] if m["challenge"] is True
            for c in m.get("components") or [] if c.get("source") == "psi44"]


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)


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

    def robust(arm, n):
        v = runs.get((arm, n), [])
        return bool(v) and 2 * sum(v) > len(v)
    ev = json.load(open(a.eval_set))
    group = {t["name"]: t.get("group", "latent_need") for t in ev["hrt"]}   # earlier sets: latent-need only
    arms = sorted({x for v in by.values() for x in v})
    out = {"tasks": len(by), "eval_set_tasks": len(group), "arms": {}, "groups": {}}
    for arm in arms:
        rs = [v[arm] for v in by.values() if arm in v]
        out["arms"][arm] = {"runs": len(rs), "verified": sum(verified(r) for r in rs),
                            "robust_verified": sum(robust(arm, r["name"]) for r in rs),
                            "hidden_test_solved": sum(r["solved"] for r in rs),
                            "hidden_test_only": sum(r["solved"] and not verified(r) for r in rs),
                            "cpu": round(sum(r["cpu"] for r in rs), 2),
                            "formation_queries": sum(r["formation_queries"] for r in rs)}
    for g in GROUPS:
        names = [n for n in by if group.get(n) == g]
        out["groups"][g] = {"tasks": len(names)}
        out["groups"][g].update({arm: {"robust_verified": sorted(n for n in names if arm in by[n] and robust(arm, n)),
                                       "hidden_test_only": sorted(n for n in names if arm in by[n]
                                                                  and by[n][arm]["solved"] and not verified(by[n][arm]))}
                                 for arm in arms if any(arm in by[n] for n in names)})
    ctrl = ("A", "R", "Kno")
    core = []
    for n, v in sorted(by.items()):
        if "K" in v and robust("K", n) and joint(v["K"]) and all(not robust(c, n) for c in ctrl if c in v):
            core.append({"task": n, "group": group.get(n), "machine": joint(v["K"]), "K_runs": runs[("K", n)],
                         "control_runs": {c: runs.get((c, n)) for c in ctrl if c in v},
                         "semantic": v["K"].get("semantic_random300")})
    out["core_evidence"] = core
    out["core_evidence_by_group"] = {g: sum(c["group"] == g for c in core) for g in GROUPS}
    out["K_regressions"] = sorted(n for n, v in by.items() if "K" in v and not robust("K", n)
                                  and any(c in v and robust(c, n) for c in ("A", "R")))
    for c in ("A", "R"):
        both = [n for n, v in by.items() if c in v and "K" in v]
        k_only = sorted(n for n in both if robust("K", n) and not robust(c, n))
        c_only = sorted(n for n in both if robust(c, n) and not robust("K", n))
        out["K_vs_" + c] = {"K_only": len(k_only), c + "_only": c_only, "p": round(mcnemar(len(k_only), len(c_only)), 6)}
    dq = {r["name"]: r for r in load(a.dq)}
    v2 = sorted(n for n, v in by.items() if "K" in v and v["K"]["solved"] and accepted_m(v["K"]) >= 2
                and n in dq and not dq[n]["solved"])
    core_names = {c["task"] for c in core}
    out["V2_rule"] = {"frozen_metric_tasks": v2, "count": len(v2), "threshold": 5, "met": len(v2) >= 5,
                      "substantive_verified_tasks": [n for n in v2 if verified(by[n]["K"])],
                      "with_core_evidence": [n for n in v2 if n in core_names], "kdq_runs": len(dq),
                      "by_group": {g: sum(group.get(n) == g for n in v2) for g in GROUPS}}
    met, coren = len(v2) >= 5, len([n for n in v2 if n in core_names])
    out["V2_verdict"] = "PASS" if met and coren >= 5 else ("FAIL" if not met else "OPEN")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--reps", nargs="*")
    ap.add_argument("--dq", nargs="*")
    ap.add_argument("--eval-set", default="docs/experiments/dev/psi44/eval_set.json")
    main(ap.parse_args())
