"""Failure classification of arm D rows (directive §10): which step of state formation stopped, per task.

python research/q3/active_failures.py <rows.jsonl>
"""
import collections, json, sys

CAT = [("query limit", "budget: query limit reached during formation"),
       ("deadline", "budget: CPU deadline reached during formation"),
       ("no informative continuation", "representation: continuation grammar exhausted (no component adds information)"),
       ("no update for component", "search or representation: no Update program found for a component"),
       ("too few defined transitions", "observation: answer undefined on the designed trajectories"),
       ("state insufficient, component limit", "representation: more than 4 components needed"),
       ("counterexample not localisable", "observation: counterexample inside undefined prefixes")]


def main(path):
    rows = [json.loads(l) for l in open(path)]
    by = {}
    for r in rows:
        by.setdefault(r["arm"], {})[r["name"]] = r
    D = by["D"]
    others = {k for a, v in by.items() if a != "D" for k, r in v.items() if r["solved"]}
    out = collections.Counter()
    adopt = collections.Counter()
    for k, r in D.items():
        f = r.get("formation", {})
        adopt[f.get("adoption", "no machine accepted" if not f.get("formed") else "machine")] += 1
        if f.get("formed"):
            out["formed (challenge passed)"] += 1
            continue
        ev = [e for m in f.get("machines", []) for e in m.get("events", [])]
        ch = [m.get("challenge") for m in f.get("machines", [])]
        if False in ch:
            out["formed but failed the independent challenge"] += 1
            continue
        last = ev[-1] if ev else "not attempted"
        cat = next((c for key, c in CAT if key in last), "other: " + last)
        out[cat] += 1
    print(json.dumps({"tasks": len(D), "outcome": dict(out), "adoption": dict(adopt)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
