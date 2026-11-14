"""Read-only post-result checklist for an eval2 result (items fixed in the static audit §5 before any outcome).

Reported next to the registered verdicts, never instead of them.
python research/q3/invention_eval2_report.py <plan>
"""
from __future__ import annotations
import collections, json, pathlib, re, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import invention_eval2 as ev
import invention_first as first
from neumann1 import invention_core as ic

MAIN = ("A", "A4", "B", "C", "C_no_inventions", "C_no_learned_prior", "B_L", "C_L", "D")


def main(plan):
    res = json.loads(pathlib.Path(ev.P(plan, "result")).read_text())
    core, _ = ev.load_core(ev.FROZEN)
    lib = ic.library_from_spec([tuple(x) for x in core["spec"]])
    out = {"plan": plan, "label": res["label"], "verdict": res["verdict"], "integrity": res.get("integrity"),
           "unresolved": len(res["unresolved"]), "families": {}}
    out["inventions_expanded_size"] = {n: ic.expand(ic._tup(b), lib) for n, _, _, b in core["spec"]}
    for fam, data in res["families"].items():
        rows = {k: r for k, r in data["rows"].items() if "unsupported" not in r}
        arms = [a for a in MAIN if rows and a in next(iter(rows.values()))]
        f = {"tasks": data["tasks"], "usable": data["usable"], "arms": {}}
        for a in arms:
            rs = [r[a] for r in rows.values()]
            d = {"solved": sum(r["solved"] for r in rs), "fit": sum(r["fit"] for r in rs),
                 "unresolved": sum("unresolved" in r for r in rs)}
            d["train_fit_precision"] = round(d["solved"] / d["fit"], 3) if d["fit"] else None
            if a != "D":
                d.update({"cpu_seconds": round(sum(r["seconds"] for r in rs), 1),
                          "work": sum(r["work"] for r in rs), "candidates": sum(r["candidates"] for r in rs),
                          "via": dict(collections.Counter(str(r["via"]) for r in rs if r["solved"])),
                          "wrong_replays": sum(r["via"] == "replay" and not r["solved"] for r in rs),
                          "fit_but_wrong_using_memory": sum(bool(r["fit"] and not r["solved"] and r["program"]
                                                                 and re.search(r"\bm\d+\b", r["program"])) for r in rs),
                          "budget_exhausted": sum((not r["fit"]) and "unresolved" not in r for r in rs)})
            f["arms"][a] = d
        c = "C" if "C" in arms else None
        if c:
            rivals = [a for a in ("A", "A4", "B", "D") if a in arms]
            excl = {k: r for k, r in rows.items() if r[c]["solved"] and not any(r[a]["solved"] for a in rivals)}
            f["C_exclusive"] = len(excl)
            f["C_exclusive_inventions"] = dict(collections.Counter(i for r in excl.values() for i in r[c]["inventions"]))
            f["C_exclusive_programs"] = {k: r[c]["program"] for k, r in sorted(excl.items())}
            if "C_no_inventions" in arms:
                att = [k for k, r in excl.items() if not r["C_no_inventions"]["solved"]]
                f["C_exclusive_invention_attributable"] = len(att)
                f["C_exclusive_also_solved_without_inventions"] = len(excl) - len(att)
                f["C_exclusive_solved_by_C_no_learned_prior"] = sum(r["C_no_learned_prior"]["solved"] for r in excl.values())
            f["B_vs_A"] = {"B_only": sum(r["B"]["solved"] and not r["A"]["solved"] for r in rows.values()),
                           "A_only": sum(r["A"]["solved"] and not r["B"]["solved"] for r in rows.values())}
            f["C_solved_also_solved_by_A4"] = sum(r[c]["solved"] and r["A4"]["solved"] for r in rows.values())
            f["P3_compute_wording"] = (
                "C beats A4 at lower or equal CPU" if f["arms"][c]["solved"] > f["arms"]["A4"]["solved"]
                and f["arms"][c]["cpu_seconds"] <= f["arms"]["A4"]["cpu_seconds"] else
                "C solved %d vs A4 %d; CPU C %.0f s vs A4 %.0f s (candidate-matched 4x, NOT compute-matched)" % (
                    f["arms"][c]["solved"], f["arms"]["A4"]["solved"], f["arms"][c]["cpu_seconds"],
                    f["arms"]["A4"]["cpu_seconds"]))
            hid = collections.Counter(r[c]["n_hidden"] for r in rows.values())
            f["hidden_tests_distribution"] = {str(k): v for k, v in sorted(hid.items(), key=lambda kv: str(kv[0]))}
            weak = {k for k, r in rows.items() if r[c]["n_hidden"] is not None and r[c]["n_hidden"] <= 1}
            if weak:
                strong = [r for k, r in rows.items() if k not in weak]
                f["sensitivity_without_tasks_with_0_or_1_hidden_test"] = dict(
                    ev.p2(strong), removed=len(weak))
        out["families"][fam] = f
    pathlib.Path(ev.P(plan, "result").replace("_result.json", "_checklist.json")).write_text(
        json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in out.items() if k != "families"}, indent=1))
    for fam, f in out["families"].items():
        print("\n##", fam, f["tasks"], "tasks", f["usable"], "usable")
        for a, d in f["arms"].items():
            print("  %-20s solved %3d fit %3d prec %s cpu %s work %s unresolved %d" % (
                a, d["solved"], d["fit"], d["train_fit_precision"], d.get("cpu_seconds"), d.get("work"), d["unresolved"]))
        for k, v in f.items():
            if k not in ("arms", "C_exclusive_programs", "tasks", "usable"):
                print("  ", k, v)


if __name__ == "__main__":
    main(sys.argv[1])
