"""DEVELOPMENT ONLY: summary of the section 38 arms (A, E, EFb, EFc, EFbc) from budgeted_reach_dev.py rows.

Verified solve = hidden test of the opened development task passed AND correct on every random diagnostic SOURCE
input of the semantic check (outside the budget).  Challenge = the machine's own independent SOURCE challenge.
First-Update success (per machine) = its first main-round attempt produced an Update (the first decision event
is a "round k" line, not "no update ..." or the synthesis fallback).

  python research/q3/case2_recovery_summary_dev.py rows.jsonl [...] > summary.json
"""
from __future__ import annotations
import json
import sys


def verified(r):
    s = r.get("semantic_random300")
    return bool(r["solved"] and s and s[0] == s[1] and s[1] > 0)


def first_update(m):
    for e in m["events"]:
        if e.startswith("round "):
            return True
        if e.startswith("no update") or e.startswith("reachability synthesis fallback") or e == "query limit" \
                or e.startswith("too few defined"):
            return False
    return None


def arm_stats(rows):
    out = {}
    for r in rows:
        a = out.setdefault(r["arm"], {"runs": 0, "solved": [], "verified": [], "challenge_passed": [],
                                      "formation_queries": 0, "queries": 0, "cpu": 0.0, "formation_cpu": 0.0,
                                      "machines": 0, "first_update_ok": 0, "first_update_known": 0,
                                      "fallback_runs": 0, "fallback_machines": 0, "fallback_then_verified": 0,
                                      "reach_queries": 0, "semantic": [0, 0]})
        a["runs"] += 1
        tag = r["name"] + ("" if r.get("seed_kind", "base") == "base" else " @" + r["seed_kind"])
        if r["solved"]:
            a["solved"].append(tag)
        if verified(r):
            a["verified"].append(tag)
        if r.get("semantic_random300"):
            a["semantic"][0] += r["semantic_random300"][0]
            a["semantic"][1] += r["semantic_random300"][1]
        if any(m["challenge"] is True for m in r["machines"]):
            a["challenge_passed"].append(tag)
        a["formation_queries"] += r["formation_queries"]
        a["reach_queries"] += r["reach_queries"]
        a["queries"] += r["queries"]
        a["cpu"] += r["cpu"]
        a["formation_cpu"] += r["formation_cpu"]
        fb = False
        for m in r["machines"]:
            a["machines"] += 1
            f = first_update(m)
            if f is not None:
                a["first_update_known"] += 1
                a["first_update_ok"] += f
            if (m.get("reach") or {}).get("synthesis_fallback_used"):
                a["fallback_machines"] += 1
                fb = True
        a["fallback_runs"] += fb
        a["fallback_then_verified"] += fb and verified(r)
    for a in out.values():
        n = len(a["verified"])
        a["cpu"] = round(a["cpu"], 2)
        a["formation_cpu"] = round(a["formation_cpu"], 2)
        a["cpu_per_verified_solve"] = round(a["cpu"] / n, 2) if n else None
        a["formation_queries_per_verified_solve"] = round(a["formation_queries"] / n, 2) if n else None
        a["first_update_rate"] = round(a["first_update_ok"] / a["first_update_known"], 3) if a["first_update_known"] else None
        for k in ("solved", "verified", "challenge_passed"):
            a[k] = sorted(a[k])
    return out


def paired(rows, arm, base="A"):
    by = {}
    for r in rows:
        by.setdefault((r["name"], r.get("seed_kind", "base")), {})[r["arm"]] = r
    new = sorted(k[0] for k, v in by.items() if arm in v and base in v and verified(v[arm]) and not verified(v[base]))
    lost = sorted(k[0] for k, v in by.items() if arm in v and base in v and verified(v[base]) and not verified(v[arm]))
    return {"new_verified": new, "lost_verified": lost, "net": len(new) - len(lost)}


def main(paths):
    rows = [json.loads(l) for p in paths for l in open(p) if l.strip()]
    out = {"rows": len(rows), "arms": arm_stats(rows)}
    for arm in sorted(out["arms"]):
        if arm != "A":
            out[arm + "_vs_A"] = paired(rows, arm)
    if "E" in out["arms"]:
        for arm in ("EFb", "EFc", "EFbc"):
            if arm in out["arms"]:
                out[arm + "_vs_E"] = paired(rows, arm, "E")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
