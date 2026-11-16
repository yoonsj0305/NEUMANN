"""DEVELOPMENT ONLY: verdicts of the pre-registered PSI evaluation (section 39) from raw rows -- no new run.

Rules are those of docs/experiments/dev/psi/prereg.json (frozen before the evaluation):
* verified solve: hidden test of the task passed AND every random diagnostic SOURCE input correct;
* runs of one (arm, task): the base run plus every replicate given (same seed again, seeds 1 and 2); an arm
  "robustly verifies" a task when it verifies it in a strict majority of its runs (one run = the base run alone);
* invention evidence (per task): P robustly verifies it with an accepted machine that contains a PSI latent, and
  none of A, AR (repair control), AF (CPU-floor control) and Pno (the same experiments, latent withheld) does;
* V1 rule (frozen V1 criterion, applied to this set as development evidence): P vs A on verified solves, net >= 10,
  exact two-sided McNemar p < 0.05, >= 2 structure classes among the P-only tasks;
* V2 rule (frozen): >= 5 tasks solved by P with an accepted machine of m >= 2 components that PDq (P's queries
  replayed, solved passively) does not solve;
* V3 rule (frozen, with Pl in E's place and P in D's place): Pl-only >= 5 with p < 0.05, or solved(Pl) >= solved(P)
  with total CPU(Pl) <= 0.7 x CPU(P).
Official sealed verdicts are not changed by anything computed here.

  python research/q3/psi_verdict_dev.py --base run1.jsonl [--reps rep2.jsonl rep3.jsonl seeds.jsonl] [--pdq pdq.jsonl]
"""
from __future__ import annotations
import argparse
import json
import math


def verified(r):
    s = r.get("semantic_random300")
    return bool(r and r["solved"] and s and s[0] == s[1] and s[1] > 0)


def accepted_m(r):
    """number of state components (W + invented variables) of the accepted machine (challenge passed), 0 if none"""
    best = 0
    for m in r["machines"]:
        if m["challenge"] is True:
            best = max(best, len(m.get("components") or []) + 1)
    return best


def psi_latents(r):
    return ["h' = %s from %s" % (c.get("update"), c.get("init")) for m in r["machines"] if m["challenge"] is True
            for c in m.get("components") or [] if c.get("source") == "psi"]


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n)


def load(paths):
    return [json.loads(l) for p in paths or [] for l in open(p) if l.strip()]


def family(name):
    return "fst" if name.startswith("fst(") else "list"


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
    groups = json.load(open(a.eval_set)) if a.eval_set else {}
    out = {"tasks": len(by), "arms": {}, "groups": {}}
    for arm in sorted({x for v in by.values() for x in v}):
        rs = [v[arm] for v in by.values() if arm in v]
        out["arms"][arm] = {"runs": len(rs), "verified": sum(verified(r) for r in rs),
                            "robust_verified": sum(robust(arm, r["name"]) for r in rs),
                            "solved": sum(r["solved"] for r in rs), "cpu": round(sum(r["cpu"] for r in rs), 2),
                            "formation_queries": sum(r["formation_queries"] for r in rs),
                            "challenge_passed": sum(any(m["challenge"] is True for m in r["machines"]) for r in rs)}
    for g in ("latent_need30", "ordinary12", "fst16"):
        names = [t["name"] for t in groups.get(g, [])]
        out["groups"][g] = {arm: sorted(n for n in names if n in by and arm in by[n] and robust(arm, n))
                            for arm in sorted({x for n in names if n in by for x in by[n]})}
    ctrl = ("A", "AR", "AF", "Pno")
    inv = []
    for n, v in sorted(by.items()):
        if "P" in v and robust("P", n) and psi_latents(v["P"]) and all(not robust(c, n) for c in ctrl if c in v):
            inv.append({"task": n, "family": family(n), "latents": psi_latents(v["P"]),
                        "controls_run": [c for c in ctrl if c in v], "P_runs": runs[("P", n)],
                        "control_runs": {c: runs.get((c, n)) for c in ctrl if c in v},
                        "semantic": v["P"].get("semantic_random300"),
                        "psi_rounds": [{k: p.get(k) for k in ("why", "outcome", "distinctions", "adopted", "cpu",
                                                               "queries")}
                                       for m in v["P"]["machines"] for p in m.get("psi") or []]})
    out["invention_evidence"] = inv
    lost = sorted(n for n, v in by.items() if "A" in v and "P" in v and robust("A", n) and not robust("P", n))
    out["P_regressions_vs_A"] = lost
    both = [n for n, v in by.items() if "A" in v and "P" in v]
    p_only = sorted(n for n in both if robust("P", n) and not robust("A", n))
    a_only = sorted(n for n in both if robust("A", n) and not robust("P", n))
    p1 = mcnemar(len(p_only), len(a_only))
    out["V1_rule_P_vs_A"] = {"P_only": p_only, "A_only": a_only, "net": len(p_only) - len(a_only), "p": round(p1, 4),
                             "structure_classes": sorted({family(n) for n in p_only}),
                             "met": len(p_only) - len(a_only) >= 10 and p1 < 0.05
                             and len({family(n) for n in p_only}) >= 2}
    pdq = {r["name"]: r for r in load(a.pdq)}
    v2 = sorted(n for n, v in by.items() if "P" in v and v["P"]["solved"] and accepted_m(v["P"]) >= 2
                and n in pdq and not pdq[n]["solved"])
    out["V2_rule"] = {"tasks": v2, "count": len(v2), "threshold": 5, "met": len(v2) >= 5,
                      "pdq_runs": len(pdq), "P_solved_m_ge_2": sorted(n for n, v in by.items() if "P" in v
                                                                       and v["P"]["solved"] and accepted_m(v["P"]) >= 2)}
    both = [n for n, v in by.items() if "Pl" in v and "P" in v]
    if both:
        pl_only = sorted(n for n in both if by[n]["Pl"]["solved"] and not by[n]["P"]["solved"])
        p_only = sorted(n for n in both if by[n]["P"]["solved"] and not by[n]["Pl"]["solved"])
        sp, sl = sum(by[n]["P"]["solved"] for n in both), sum(by[n]["Pl"]["solved"] for n in both)
        cp, cl = sum(by[n]["P"]["cpu"] for n in both), sum(by[n]["Pl"]["cpu"] for n in both)
        p3 = mcnemar(len(pl_only), len(p_only))
        out["V3_rule_Pl_vs_P"] = {"tasks": len(both), "Pl_only": pl_only, "P_only": p_only, "p": round(p3, 4),
                                  "solved_P": sp, "solved_Pl": sl, "cpu_P": round(cp, 2), "cpu_Pl": round(cl, 2),
                                  "met": (len(pl_only) >= 5 and p3 < 0.05) or (sl >= sp and cl <= 0.7 * cp)}
        tried = {}
        for arm in ("P", "Pl"):
            att = adopted = 0
            for n in both:
                for m in by[n][arm]["machines"]:
                    for p in m.get("psi") or []:
                        att += len(p.get("tried") or [])
                        adopted += p.get("outcome") == "adopted"
            tried[arm] = {"synthesis_attempts": att, "adoptions": adopted}
        out["V3_rule_Pl_vs_P"]["process"] = tried
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--reps", nargs="*")
    ap.add_argument("--pdq", nargs="*")
    ap.add_argument("--eval-set", default="docs/experiments/dev/psi/eval_set.json")
    main(ap.parse_args())
