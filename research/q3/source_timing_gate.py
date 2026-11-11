"""Gate before freezing SECOND/FRESH: cost of every arm on SOURCE tasks at the real budgets, new executor.

Development data only (rule_source, oeis_source). Deterministic sample: the first N tasks of each SOURCE split in
the FIRST registry's salted order. Uses the checkpoint runner and the exact arm definitions of invention_eval2.

python research/q3/source_timing_gate.py <bigbench> <oeis> <n_per_family> <wall_cap_s> <rows.jsonl> <out.json>
"""
from __future__ import annotations
import collections, json, pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import invention_core as ic
import checkpoint_runner as cr
import invention_eval2 as ev
import invention_first as first


def pct(xs, q):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(q * len(xs)))], 3) if xs else None


def main(bigbench, oeis, n, cap, rows_path, out):
    n, cap = int(n), float(cap)
    reg, _ = first.load_registry()
    core, _ = ev.load_core(ev.FROZEN)
    main_arms, secondary = ev.arms_first(core)
    jobs, sample = [], {}
    for fam, clone, key, blobs, loader in (("rule", bigbench, "rule_source", "rule_blobs", first.load_rule),
                                           ("oeis", oeis, "oeis_source", "oeis_blobs", first.load_oeis)):
        src = set(reg["splits"][key])
        ordered = [p for p in first.order(sorted(reg[blobs]), fam) if p in src]
        tasks = []
        for p in ordered:
            raw = (pathlib.Path(clone) / p).read_bytes()
            if first.blob_sha(raw) != reg[blobs][p]:
                raise SystemExit("SOURCE_BLOB_MISMATCH " + p)
            t = loader(p, raw)
            if "unsupported" not in t:
                tasks.append(t)
            if len(tasks) == n:
                break
        sample[fam] = [t["id"] for t in tasks]
        arms = dict(main_arms)
        if fam == "rule":
            arms.update(secondary)
        for arm, (spec, costs, memory, budget) in arms.items():
            for t in tasks:
                jobs.append(((fam, arm, t["id"]), t, spec, ic.cost_for(costs, t), budget, memory))
    print("jobs", len(jobs), flush=True)
    rows = cr.run(jobs, rows_path, workers=4, wall_cap_s=cap,
                  log=lambda r: print(r["key"], r["status"], r.get("cpu_seconds"), flush=True)
                  if r["status"] != "ok" or r.get("cpu_seconds", 0) > 120 else None)
    rep = {"sample": sample, "wall_cap_s": cap, "core_code_sha256": ev.sha_file("neumann1/invention_core.py"),
           "status": dict(collections.Counter(r["status"] for r in rows.values())), "arms": {}}
    for (fam, arm) in sorted({(k[0], k[1]) for k in rows}):
        rs = [r for k, r in rows.items() if k[0] == fam and k[1] == arm]
        ok = [r for r in rs if r["status"] == "ok"]
        cpu = [r["cpu_seconds"] for r in ok]
        rep["arms"]["%s/%s" % (fam, arm)] = {
            "jobs": len(rs), "ok": len(ok), "non_ok": {r["key"][2]: r["status"] for r in rs if r["status"] != "ok"},
            "solved_in_sample_NOT_evidence": sum(r["solved"] for r in ok),
            "via": dict(collections.Counter(str(r["via"]) for r in ok)),
            "cpu_seconds": {"total": round(sum(cpu), 1), "median": pct(cpu, .5), "p90": pct(cpu, .9),
                            "p99": pct(cpu, .99), "max": pct(cpu, 1.0)},
            "work": {"total": sum(r["work"] for r in ok), "max": max((r["work"] for r in ok), default=None)},
            "candidates_total": sum(r["candidates"] for r in ok),
            "maxrss_kb_max": max((r["maxrss_kb"] for r in ok), default=None)}
    rep["max_cpu_seconds_any_job"] = max((r["cpu_seconds"] for r in rows.values() if r["status"] == "ok"), default=None)
    json.dump(rep, open(out, "w"), indent=1, sort_keys=True)
    for k, a in rep["arms"].items():
        print(k, a["ok"], "/", a["jobs"], a["cpu_seconds"], "rss", a["maxrss_kb_max"], a["non_ok"])
    print("status", rep["status"], "max cpu", rep["max_cpu_seconds_any_job"])


if __name__ == "__main__":
    main(*sys.argv[1:7])
