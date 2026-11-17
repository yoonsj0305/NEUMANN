"""Read-only report over the frozen core and the FIRST result (no scoring logic).

python research/q3/invention_first_report.py
"""
from __future__ import annotations
import json, pathlib, sys
from collections import Counter
sys.path.insert(0, ".")
from neumann1 import invention_core as ic

FROZEN = "docs/experiments/results/invention_core_frozen.json"
RESULT = "docs/experiments/results/invention_first_result.json"


def main():
    frozen = json.loads(pathlib.Path(FROZEN).read_text())
    print("## Frozen core")
    print("source solved %d / %d usable; history %s" % (
        len(frozen["source_solved"]), frozen["source_usable"], frozen["history"]))
    spec = [tuple(x) for x in frozen["spec"]]
    lib = ic.library_from_spec(spec)
    for name, ret, params, body in spec:
        sig = ", ".join(t + ("(%s)" % ",".join(bt) if bt else "") for t, bt in params)
        flat = ic.expand(ic._tup(body), lib)
        print("| `%s` | (%s) → %s | `%s` | %d |" % (name, sig, ret, ic.show(ic._tup(body)), flat))
    if not pathlib.Path(RESULT).exists():
        return
    res = json.loads(pathlib.Path(RESULT).read_text())
    print("\n## Verdict\n", json.dumps(res["verdict"], indent=1))
    wake = sum(h["wake_candidates"] for h in frozen["history"])
    print("\nSOURCE investment: %d candidates, %.0f s wall (4 workers)" % (wake, frozen["train_wall_s"]))
    for fam, data in res["families"].items():
        rows = {k: r for k, r in data["rows"].items() if "unsupported" not in r}
        s = res["summary"][fam]
        print("\n## %s: %d tasks (%d usable)" % (fam, s["tasks"], s["usable"]))
        for arm in ("A", "A4", "B", "C", "C_no_inventions", "C_no_learned_prior", "D"):
            if arm in s:
                a = s[arm]
                prec = "%.0f%%" % (100 * a["solved"] / a["fit"]) if a["fit"] else "-"
                print("| %s | %d | %.1f%% | %d | %s | %s | %s |" % (
                    arm, a["solved"], 100 * a["solved"] / s["tasks"], a["fit"], prec,
                    a.get("candidates", "-"), a.get("cpu_seconds", "-")))
        for k, v in s.items():
            if k.startswith("C_") and not isinstance(v, dict) or k.startswith("C_vs") or k.startswith("lost") or k.startswith("search"):
                print("  ", k, v)
        rivals = [a for a in ("A", "A4", "B", "D") if a in next(iter(rows.values()))]
        excl = {k: r for k, r in rows.items()
                if r["C"]["solved"] and not any(r[a]["solved"] for a in rivals)}
        use = Counter(i for r in excl.values() for i in r["C"]["inventions"])
        print("   exclusive wins use inventions:", dict(use.most_common()))
        via = Counter(r["C"]["via"] for r in rows.values() if r["C"]["solved"])
        print("   C solved via:", dict(via), "| B via:", dict(Counter(
            r["B"]["via"] for r in rows.values() if r["B"]["solved"])))
        for k in sorted(excl)[:12]:
            print("   ", k, excl[k]["C"]["candidates"], excl[k]["C"]["program"])


if __name__ == "__main__":
    main()
