"""Aggregate executor_equivalence.py output: every job accounted for, comparable jobs verified, costs.

python research/q3/executor_equivalence_report.py <in.jsonl> <out.json> [expected_tasks]
"""
from __future__ import annotations
import collections, hashlib, json, sys

FIELDS = ("fit", "solved", "via", "candidates", "ast", "trace", "trace_len")
VERSIONS, ARMS = ("frozen", "off", "on"), ("A", "B", "C")


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def dist(xs):
    return {"n": len(xs), "min": round(min(xs), 3), "p10": round(pct(xs, .10), 3), "median": round(pct(xs, .50), 3),
            "p90": round(pct(xs, .90), 3), "p99": round(pct(xs, .99), 3), "max": round(max(xs), 3)} if xs else {"n": 0}


def main(inp, out, expected_tasks=None):
    raw = open(inp, "rb").read()
    rows = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
    keys = collections.Counter((r["version"], r["id"], r["arm"]) for r in rows)
    ids = sorted({r["id"] for r in rows})
    expected = {(v, i, a) for v in VERSIONS for i in ids for a in ARMS}
    rep = {"input_sha256": hashlib.sha256(raw).hexdigest(), "rows": len(rows), "tasks": len(ids),
           "families": dict(collections.Counter(i.split("/")[0] for i in ids)),
           "expected_jobs": len(expected), "duplicate_keys": sum(c > 1 for c in keys.values()),
           "missing_jobs": sorted(expected - set(keys))[:50], "missing_count": len(expected - set(keys)),
           "status": {}, "per_arm": {}, "timeouts": [], "all_mismatches": []}
    if expected_tasks is not None:
        rep["expected_tasks"] = int(expected_tasks)
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["id"], r["arm"])][r["version"]] = r
        st = "timeout" if "timeout" in r else "ok"
        rep["status"].setdefault(r["version"], collections.Counter())[st] += 1
        if st == "timeout":
            rep["timeouts"].append([r["id"], r["arm"], r["version"]])
    rep["status"] = {v: dict(c) for v, c in rep["status"].items()}
    for arm in ARMS:
        pairs = {k: v for k, v in by.items() if k[1] == arm}
        ok = lambda v, ver: ver in v and "timeout" not in v[ver]
        triple = {k: v for k, v in pairs.items() if all(ok(v, x) for x in VERSIONS)}
        fo = {k: v for k, v in pairs.items() if ok(v, "frozen") and ok(v, "on")}
        mism = {}
        for name, a, b, pool in (("frozen_vs_on", "frozen", "on", fo), ("frozen_vs_off", "frozen", "off", triple),
                                 ("off_vs_on", "off", "on", {k: v for k, v in pairs.items()
                                                             if ok(v, "off") and ok(v, "on")})):
            bad = [{"id": k[0], "arm": arm, "pair": name, "fields": [f for f in FIELDS if v[a][f] != v[b][f]]}
                   for k, v in pool.items() if any(v[a][f] != v[b][f] for f in FIELDS)]
            mism[name] = {"comparable": len(pool), "mismatches": len(bad)}
            rep["all_mismatches"] += bad
        not_comparable = {k[0]: [x for x in VERSIONS if not ok(v, x)] for k, v in pairs.items()
                          if not (ok(v, "frozen") and ok(v, "on"))}
        cpu = {ver: round(sum(v[ver]["cpu"] for v in triple.values()), 2) for ver in VERSIONS}
        work = {ver: sum(v[ver]["work"] for v in triple.values()) for ver in ("off", "on")}
        ratio_cpu = [v["frozen"]["cpu"] / max(v["on"]["cpu"], 1e-3) for v in fo.values() if v["frozen"]["cpu"] >= 0.05]
        ratio_work = [v["off"]["work"] / max(v["on"]["work"], 1) for v in triple.values() if v["off"]["work"] > 0]
        worst = sorted(fo.values(), key=lambda v: -v["frozen"]["cpu"])[:5]
        slower = sorted(((v["on"]["cpu"] - v["frozen"]["cpu"], k[0], v["frozen"]["cpu"], v["on"]["cpu"])
                         for k, v in fo.items()), reverse=True)[:3]
        on_all = [v["on"] for v in pairs.values() if ok(v, "on")]
        rep["per_arm"][arm] = {
            "pairs": len(pairs), "complete_triples": len(triple), "frozen_and_on_comparable": len(fo),
            "equality": mism, "not_comparable_frozen_vs_on": not_comparable,
            "solved_frozen_on_comparable": sum(v["frozen"]["solved"] for v in fo.values()),
            "solved_on_on_comparable": sum(v["on"]["solved"] for v in fo.values()),
            "cpu_seconds_triples": cpu, "cpu_ratio_frozen_over_on_total": round(cpu["frozen"] / max(cpu["on"], 1e-9), 2),
            "work_triples": work, "work_ratio_off_over_on_total": round(work["off"] / max(work["on"], 1), 2),
            "per_task_cpu_ratio_frozen_over_on": dist(ratio_cpu),
            "per_task_work_ratio_off_over_on": dist(ratio_work),
            "cpu_seconds_per_task": {ver: dist([v[ver]["cpu"] for v in triple.values()]) for ver in VERSIONS},
            "on_cpu_all_completed": dist([r["cpu"] for r in on_all]),
            "on_timeouts": sum(1 for v in pairs.values() if "on" in v and "timeout" in v["on"]),
            "worst_frozen_cpu_cases": [{"id": v["frozen"]["id"], "frozen_cpu": v["frozen"]["cpu"], "on_cpu": v["on"]["cpu"],
                                        "off_work": v.get("off", {}).get("work"), "on_work": v["on"]["work"]}
                                       for v in worst],
            "largest_on_slowdowns_seconds": [{"id": i, "frozen_cpu": a, "on_cpu": b, "delta": round(d, 3)}
                                             for d, i, a, b in slower]}
    json.dump(rep, open(out, "w"), indent=1, sort_keys=True)
    print("rows %d tasks %d expected %d missing %d duplicates %d" % (
        rep["rows"], rep["tasks"], rep["expected_jobs"], rep["missing_count"], rep["duplicate_keys"]))
    print("status", rep["status"], "| mismatches", len(rep["all_mismatches"]))
    for arm, a in rep["per_arm"].items():
        print(arm, json.dumps({k: a[k] for k in ("complete_triples", "frozen_and_on_comparable", "equality",
                                                 "cpu_seconds_triples", "cpu_ratio_frozen_over_on_total",
                                                 "work_ratio_off_over_on_total", "on_timeouts")}))
        print("   cpu ratio per task", a["per_task_cpu_ratio_frozen_over_on"])
        print("   work ratio per task", a["per_task_work_ratio_off_over_on"])
        print("   on cpu (all completed)", a["on_cpu_all_completed"])
        print("   worst", a["worst_frozen_cpu_cases"][:3])
        print("   slowdowns", a["largest_on_slowdowns_seconds"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
