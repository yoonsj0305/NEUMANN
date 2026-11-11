"""Aggregate executor_equivalence.py output.  python research/q3/executor_equivalence_report.py <in.jsonl> <out.json>"""
from __future__ import annotations
import collections, json, sys

FIELDS = ("fit", "solved", "via", "candidates", "ast", "trace", "trace_len")


def main(inp, out):
    rows = [json.loads(l) for l in open(inp) if l.strip()]
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["id"], r["arm"])][r["version"]] = r
    rep = {"jobs": len(rows), "task_arm_pairs": len(by), "per_arm": {}}
    for arm in ("A", "B", "C"):
        pairs = {k: v for k, v in by.items() if k[1] == arm}
        complete = {k: v for k, v in pairs.items()
                    if len(v) == 3 and not any("timeout" in x for x in v.values())}
        mism = {"frozen_vs_on": [], "frozen_vs_off": []}
        for k, v in complete.items():
            for o in ("on", "off"):
                d = [f for f in FIELDS if v["frozen"][f] != v[o][f]]
                if d:
                    mism["frozen_vs_" + o].append({"id": k[0], "fields": d})
        to = collections.Counter(x["version"] for v in pairs.values() for x in v.values() if "timeout" in x)
        only_frozen_to = [k[0] for k, v in pairs.items()
                          if "timeout" in v.get("frozen", {}) and "on" in v and "timeout" not in v["on"]]
        cpu = {ver: round(sum(v[ver]["cpu"] for v in complete.values()), 2) for ver in ("frozen", "off", "on")}
        work = {ver: sum(v[ver]["work"] for v in complete.values()) for ver in ("off", "on")}
        sp = sorted(((v["frozen"]["cpu"] / max(v["on"]["cpu"], 1e-4), k[0], v["frozen"]["cpu"], v["on"]["cpu"],
                      v["off"]["work"], v["on"]["work"]) for v in complete.values()), reverse=True)[:8]
        rep["per_arm"][arm] = {
            "pairs": len(pairs), "complete_triples": len(complete),
            "mismatches": {k: len(v) for k, v in mism.items()}, "mismatch_detail": mism,
            "timeouts_by_version": dict(to), "frozen_timeout_but_on_completed": only_frozen_to,
            "cpu_seconds_on_complete": cpu, "work_on_complete": work,
            "work_ratio_off_over_on": round(work["off"] / max(work["on"], 1), 3),
            "cpu_ratio_frozen_over_on": round(cpu["frozen"] / max(cpu["on"], 1e-9), 3),
            "solved_on_complete": {ver: sum(v[ver]["solved"] for v in complete.values())
                                   for ver in ("frozen", "on")},
            "top_speedups": [{"id": i, "frozen_cpu": a, "on_cpu": b, "work_off": wo, "work_on": wn,
                              "ratio": round(r, 1)} for r, i, a, b, wo, wn in sp]}
    json.dump(rep, open(out, "w"), indent=1, sort_keys=True)
    for arm, a in rep["per_arm"].items():
        print(arm, {k: a[k] for k in ("pairs", "complete_triples", "mismatches", "timeouts_by_version",
                                      "cpu_ratio_frozen_over_on", "work_ratio_off_over_on")})


if __name__ == "__main__":
    main(*sys.argv[1:3])
