"""Summary of SOURCE-only development rows of the specification-space core (never evidence for a gate).

python research/q3/spec_dev_report.py <rule_rows.jsonl> <oeis_rows.jsonl> <cap_s>
Writes docs/experiments/results/spec_core_dev_source.json (ids, outcomes and the system's own programs only).
"""
from __future__ import annotations
import collections, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import invention_first as first

OUT = "docs/experiments/results/spec_core_dev_source.json"


def load(path):
    by = {}
    for l in open(path):
        r = json.loads(l)
        by.setdefault(r["arm"], {})[r["id"]] = r
    return by


def vs(by, a, b):
    sa, sb = ({i for i, r in by[x].items() if r["solved"]} for x in (a, b))
    w, l = len(sa - sb), len(sb - sa)
    return {"first_only": w, "second_only": l, "mcnemar_p": first.mcnemar(w, l)}


def main(rule, oeis, cap):
    cap = float(cap)
    out = {"schema": "neumann.spec-core.dev-source.v1", "cap_cpu_seconds": cap,
           "note": "development data (SOURCE splits) only; tuned on these tasks; not evidence for any gate"}
    for fam, path in (("rule", rule), ("oeis", oeis)):
        by = load(path)
        so = lambda a: {i for i, r in by[a].items() if r["solved"]}
        f = {"tasks": len(next(iter(by.values()))), "arms": {}}
        for a, rows in sorted(by.items()):
            assert len(rows) == f["tasks"], (fam, a, len(rows))
            f["arms"][a] = {"solved": len(so(a)), "fit": sum(r["fit"] for r in rows.values()),
                            "cpu_seconds": round(sum(r["cpu_seconds"] for r in rows.values()), 1),
                            "via": dict(collections.Counter(str(r.get("via")) for r in rows.values() if r["solved"])),
                            "solved_after_80pct_of_cap": sum(r["solved"] and r["cpu_seconds"] > 0.8 * cap * (4 if a == "A@4" else 1)
                                                             for r in rows.values())}
        for b in by:
            if b != "S":
                f["S_vs_" + b] = vs(by, "S", b)
        if "A@4" in by:
            gap = sorted(by["S"][i]["cpu_seconds"] for i in so("S") - so("A@4"))
            f["S_cpu_on_tasks_A@4_failed"] = {"n": len(gap), "median": gap[len(gap) // 2], "max": gap[-1],
                                              "total": round(sum(gap), 1),
                                              "A@4_total_on_same_tasks": round(sum(by["A@4"][i]["cpu_seconds"] for i in so("S") - so("A@4")), 1)}
        both = so("S") & so("A")
        f["cpu_on_tasks_both_solve"] = {"n": len(both), "S": round(sum(by["S"][i]["cpu_seconds"] for i in both), 1),
                                        "A": round(sum(by["A"][i]["cpu_seconds"] for i in both), 1)}
        chain = [by["S"][i]["size"] for i in so("S") if by["S"][i]["via"] == "chain"]
        f["chain_solution_sizes"] = sorted(chain)
        f["S_rows"] = {i: {"solved": r["solved"], "fit": r["fit"], "via": r["via"], "cpu_seconds": r["cpu_seconds"],
                           "program": r["program"]} for i, r in sorted(by["S"].items())}
        f["solved_ids"] = {a: sorted(so(a)) for a in by}
        out[fam] = f
    pathlib.Path(OUT).write_text(json.dumps(out, indent=1, sort_keys=True))
    for fam in ("rule", "oeis"):
        f = out[fam]
        print(fam, {a: (d["solved"], d["cpu_seconds"]) for a, d in f["arms"].items()})
        print({k: v for k, v in f.items() if k.startswith("S_vs_") or k.startswith("S_cpu") or k.startswith("cpu_on")})
        print("via", f["arms"]["S"]["via"], "fit", f["arms"]["S"]["fit"], "chain sizes", f["chain_solution_sizes"],
              "late", {a: d["solved_after_80pct_of_cap"] for a, d in f["arms"].items()})


if __name__ == "__main__":
    main(*sys.argv[1:4])
