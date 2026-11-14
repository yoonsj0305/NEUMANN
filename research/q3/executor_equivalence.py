"""Differential test: frozen FIRST executor vs. the call-by-need / vector-reuse executor.

Development data only: the self-authored dev family and the SOURCE split of the registered FIRST
families (rule_source, oeis_source; opened legitimately for learning on 2026-11-11). No TARGET file is read.

Three executors per (task, arm):
  frozen  neumann1/invention_core.py exactly as at freeze commit FROZEN_COMMIT (loaded from git)
  off     current core with CALL_BY_NEED = REUSE_VECTORS = False (old evaluation order + work meter)
  on      current core with both switches on

Compared per job: fit, solved, via, returned AST, candidate count, and a SHA-256 over the ordered
trace of every entry reaching `_keep` (context depth, AST, value vector), i.e. every candidate that
is evaluated and not discarded as all-failing.  Also: CPU seconds and (off/on) the work meter.
A job that exceeds the wall cap is recorded as TIMEOUT and is not comparable.

python research/q3/executor_equivalence.py <bigbench_clone> <oeis_clone> <budget> <wall_cap_s> <out.jsonl>
"""
from __future__ import annotations
import hashlib, importlib.util, json, multiprocessing as mp, os, pathlib, subprocess, sys, time
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")

FROZEN_COMMIT = "0954ed5"
WORKERS = 4


def load_frozen():
    src = subprocess.run(["git", "show", FROZEN_COMMIT + ":neumann1/invention_core.py"],
                         check=True, capture_output=True, text=True).stdout
    path = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / ("ic_frozen_%s.py" % FROZEN_COMMIT)
    path.write_text(src)
    spec = importlib.util.spec_from_file_location("ic_frozen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def traced(mod):
    """Wrap Search._keep to hash the ordered trace of kept-or-merged entries."""
    orig = mod.Search._keep
    state = {"h": None, "k": 0}

    def _keep(self, ctx, out, e, t):
        state["h"].update(repr((ctx.depth, e.ast(), e.vec)).encode())
        state["k"] += 1
        return orig(self, ctx, out, e, t)
    mod.Search._keep = _keep
    return state


def job(version, task, arm, budget, frozen_core, q):
    if version == "frozen":
        mod = load_frozen()
    else:
        from neumann1 import invention_core as mod
        mod.CALL_BY_NEED = mod.REUSE_VECTORS = (version == "on")
    st = traced(mod)
    st["h"] = hashlib.sha256()
    spec, costs, memory = (), mod.untrained_costs(), None
    if arm in ("B", "C"):
        memory = [(mod._tup(a), tuple(i), o) for a, i, o in frozen_core["memory"]]
    if arm == "C":
        spec, costs = [tuple(x) for x in frozen_core["spec"]], frozen_core["costs"]
    c0 = time.process_time()
    w0 = getattr(mod, "WORK", [0])[0]
    r = mod.solve(task, spec, mod.cost_for(costs, task), budget, memory)
    q.put({"version": version, "id": task["id"], "arm": arm, "fit": r["fit"],
           "solved": r["solved"], "via": r["via"], "candidates": r["candidates"],
           "ast": repr(r["ast"]), "trace": st["h"].hexdigest(), "trace_len": st["k"],
           "cpu": round(time.process_time() - c0, 4),
           "work": (getattr(mod, "WORK", [0])[0] - w0) if version != "frozen" else None})


def dev_tasks(bigbench, oeis):
    import invention_dev_family, invention_first as h
    src, tgt = invention_dev_family.tasks()
    tasks = [dict(t, id="dev/" + t["id"]) for t in src + tgt]
    reg, _ = h.load_registry()
    s = reg["splits"]
    for clone, key, blobs, loader in ((bigbench, "rule_source", "rule_blobs", h.load_rule),
                                      (oeis, "oeis_source", "oeis_blobs", h.load_oeis)):
        for p in s[key]:
            raw = (pathlib.Path(clone) / p).read_bytes()
            if h.blob_sha(raw) != reg[blobs][p]:
                raise SystemExit("SOURCE_BLOB_MISMATCH " + p)
            tasks.append(loader(p, raw))
    return [t for t in tasks if "unsupported" not in t]


def main(bigbench, oeis, budget, cap, out):
    budget, cap = int(budget), float(cap)
    frozen_core = json.loads(pathlib.Path("docs/experiments/results/invention_core_frozen.json").read_text())
    tasks = dev_tasks(bigbench, oeis)
    done = set()
    if pathlib.Path(out).exists():
        for line in pathlib.Path(out).read_text().splitlines():
            d = json.loads(line)
            done.add((d["version"], d["id"], d["arm"]))
    jobs = [(v, t, a) for t in tasks for a in ("A", "B", "C") for v in ("frozen", "off", "on")
            if (v, t["id"], a) not in done]
    print("tasks %d, jobs to run %d" % (len(tasks), len(jobs)), flush=True)
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    running = {}
    with open(out, "a") as fh:
        def drain():
            while not q.empty():
                d = q.get()
                fh.write(json.dumps(d, sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        while jobs or running:
            while jobs and len(running) < WORKERS:
                v, t, a = jobs.pop(0)
                p = ctx.Process(target=job, args=(v, t, a, budget, frozen_core, q))
                p.start()
                running[p] = (v, t["id"], a, time.time())
            time.sleep(0.05)
            drain()
            for p, (v, tid, a, t0) in list(running.items()):
                if not p.is_alive():
                    p.join()
                    del running[p]
                elif time.time() - t0 > cap:
                    p.kill()
                    p.join()
                    del running[p]
                    fh.write(json.dumps({"version": v, "id": tid, "arm": a, "timeout": cap}) + "\n")
                    fh.flush()
            drain()
        drain()


if __name__ == "__main__":
    main(*sys.argv[1:6])
