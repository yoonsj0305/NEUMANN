"""DEVELOPMENT ONLY: summary of A / D / E rows from research/q3/budgeted_reach_dev.py (no new run).

  python research/q3/budgeted_reach_summary_dev.py rows1.jsonl [rows2.jsonl ...] > summary.json
"""
from __future__ import annotations
import json
import sys


def load(paths):
    out = []
    for p in paths:
        out += [json.loads(l) for l in open(p) if l.strip()]
    return out


def per_arm(rows):
    arms = {}
    for r in rows:
        a = arms.setdefault(r["arm"], {"runs": 0, "solved": [], "challenge_passed": [], "formed": [],
                                       "queries": 0, "formation_queries": 0, "reach_queries": 0,
                                       "state_queries": 0, "reachable_obs": 0, "reachable_total": 0,
                                       "conflict_components": 0, "updates_synthesised": 0,
                                       "round0_fold_failures": 0, "cpu": 0.0, "formation_cpu": 0.0,
                                       "degraded": 0, "fallback": 0, "semantic": [0, 0], "cost": {}})
        a["runs"] += 1
        if r["solved"]:
            a["solved"].append(r["name"])
            if r.get("semantic_random300"):
                a["semantic"][0] += r["semantic_random300"][0]
                a["semantic"][1] += r["semantic_random300"][1]
        if any(m["challenge"] is True for m in r["machines"]):
            a["challenge_passed"].append(r["name"])
        if any(m["formed"] for m in r["machines"]):
            a["formed"].append(r["name"])
        a["queries"] += r["queries"]
        a["formation_queries"] += r["formation_queries"]
        a["reach_queries"] += r["reach_queries"]
        a["state_queries"] += sum(v for k, v in r["cost"].items() if k.startswith("states:") or k == "formation:reach")
        a["reachable_obs"] += r["reachable_transitions_observed"][0]
        a["reachable_total"] += r["reachable_transitions_observed"][1]
        a["cpu"] += r["cpu"]
        a["formation_cpu"] += r["formation_cpu"]
        for m in r["machines"]:
            a["conflict_components"] += m["conflict_components"]
            a["updates_synthesised"] += m["updates_synthesised"]
            a["round0_fold_failures"] += m["round0_fold_failures"] or 0
            if m.get("reach"):
                a["degraded"] += bool(m["reach"].get("degraded"))
                a["fallback"] += bool(m["reach"].get("fallback"))
        for k, v in r["cost"].items():
            a["cost"][k] = a["cost"].get(k, 0) + v
    for a in arms.values():
        a["solved"] = sorted(a["solved"])
        a["challenge_passed"] = sorted(a["challenge_passed"])
        a["formed"] = sorted(a["formed"])
        a["cpu"] = round(a["cpu"], 2)
        a["formation_cpu"] = round(a["formation_cpu"], 2)
    return arms


def paired(rows, a, b):
    by = {}
    for r in rows:
        by.setdefault((r["name"], r["seed_kind"]), {})[r["arm"]] = r
    new = sorted(k[0] + " @" + k[1] for k, v in by.items() if a in v and b in v and v[a]["solved"] and not v[b]["solved"])
    lost = sorted(k[0] + " @" + k[1] for k, v in by.items() if a in v and b in v and v[b]["solved"] and not v[a]["solved"])
    return {"new": new, "lost": lost}


def main(paths):
    rows = load(paths)
    out = {"rows": len(rows), "arms": per_arm(rows)}
    for a, b in (("D", "A"), ("E", "A"), ("E", "D")):
        out["%s_vs_%s" % (a, b)] = paired(rows, a, b)
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
