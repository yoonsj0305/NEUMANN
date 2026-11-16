"""DEVELOPMENT ONLY: verdicts of the pre-registered section 41 evaluation from raw rows -- no new run.

Rules of docs/experiments/dev/psi41/prereg.json (frozen before the evaluation):
* verified solve: hidden test passed AND every random diagnostic SOURCE input correct (300 inputs);
* robust: strict majority of an arm's runs on a task (base run, plus replicates when replicated);
* CORE EVIDENCE (per task): R robustly verifies it with an accepted machine containing an identified state, and none
  of A, Q (PSI40 as frozen in section 40) and Rno (R with the identified state withheld) robustly verifies it;
* V2 rule (frozen V2 criterion, R in D's place, RDq in Dq's): >= 5 tasks solved by R (hidden test) with an accepted
  machine of m >= 2 state components that RDq does not solve; reported also with verified solves (substantive);
* V2 verdict: PASS if the rule is met AND >= 5 of its tasks carry core evidence; FAIL if the rule is not met;
  OPEN otherwise;
* REGRESSION: tasks A robustly verifies and R does not; cost: real CPU and formation queries per arm and group.
Official sealed verdicts are not changed by anything computed here.

  python research/q3/psi41_verdict_dev.py --base run1.jsonl [--reps ...] [--dq rdq.jsonl]
"""
from __future__ import annotations
import argparse
import json
import math

GROUPS = ("fst", "rha", "lr_need12", "lr_ord12")


def verified(r):
    s = r.get("semantic_random300")
    return bool(r and r["solved"] and s and s[0] == s[1] and s[1] > 0)


def accepted_m(r):
    return max([1 + len(m.get("components") or []) for m in r["machines"] if m["challenge"] is True] or [0])


def states(r):
    return [c.get("update") for m in r["machines"] if m["challenge"] is True
            for c in m.get("components") or [] if c.get("source") == "psi40"]


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
    group = {t["name"]: g for g in GROUPS for t in ev.get(g, [])}
    arms = sorted({x for v in by.values() for x in v})
    out = {"tasks": len(by), "arms": {}, "groups": {}}
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
        out["groups"][g] = {arm: {"robust_verified": sorted(n for n in names if arm in by[n] and robust(arm, n)),
                                  "hidden_test_only": sorted(n for n in names if arm in by[n] and by[n][arm]["solved"]
                                                             and not verified(by[n][arm])),
                                  "cpu": round(sum(by[n][arm]["cpu"] for n in names if arm in by[n]), 2)}
                            for arm in arms if any(arm in by[n] for n in names)}
    ctrl = ("A", "Q", "Rno")
    core = []
    for n, v in sorted(by.items()):
        if "R" in v and robust("R", n) and states(v["R"]) and all(not robust(c, n) for c in ctrl if c in v):
            core.append({"task": n, "group": group.get(n), "states": states(v["R"]), "R_runs": runs[("R", n)],
                         "control_runs": {c: runs.get((c, n)) for c in ctrl if c in v},
                         "semantic": v["R"].get("semantic_random300")})
    out["core_evidence"] = core
    out["R_regressions_vs_A"] = sorted(n for n, v in by.items() if "A" in v and "R" in v and robust("A", n)
                                       and not robust("R", n))
    both = [n for n, v in by.items() if "A" in v and "R" in v]
    r_only = sorted(n for n in both if robust("R", n) and not robust("A", n))
    a_only = sorted(n for n in both if robust("A", n) and not robust("R", n))
    out["R_vs_A"] = {"R_only": r_only, "A_only": a_only, "p": round(mcnemar(len(r_only), len(a_only)), 4)}
    both = [n for n, v in by.items() if "Q" in v and "R" in v]
    out["R_vs_Q"] = {"R_only": sorted(n for n in both if robust("R", n) and not robust("Q", n)),
                     "Q_only": sorted(n for n in both if robust("Q", n) and not robust("R", n))}
    dq = {r["name"]: r for r in load(a.dq)}
    v2 = sorted(n for n, v in by.items() if "R" in v and v["R"]["solved"] and accepted_m(v["R"]) >= 2
                and n in dq and not dq[n]["solved"])
    core_names = {c["task"] for c in core}
    out["V2_rule"] = {"frozen_metric_tasks": v2, "count": len(v2), "threshold": 5, "met": len(v2) >= 5,
                      "substantive_verified_tasks": [n for n in v2 if verified(by[n]["R"])],
                      "with_core_evidence": [n for n in v2 if n in core_names], "rdq_runs": len(dq)}
    met, coren = len(v2) >= 5, len([n for n in v2 if n in core_names])
    out["V2_verdict"] = "PASS" if met and coren >= 5 else ("FAIL" if not met else "OPEN")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--reps", nargs="*")
    ap.add_argument("--dq", nargs="*")
    ap.add_argument("--eval-set", default="docs/experiments/dev/psi41/eval_set.json")
    main(ap.parse_args())
