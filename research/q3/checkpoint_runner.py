"""Checkpointed, metered, restartable execution of (family, arm, task) jobs.

Infrastructure only: it never changes what `invention_core.solve` returns.

* one fresh forked process per job, at most `workers` at a time;
* every finished job is appended as one JSON line and flushed + fsync'ed before the next is scheduled, so a
  crash or container loss keeps every completed row;
* on restart, jobs whose key is already in the checkpoint are skipped (the key is (family, arm, task id));
* an exception inside a job is recorded as {"error": ...} for that job only;
* `wall_cap_s` (optional) kills a job that runs longer and records {"timeout": cap}. Whether a TIMEOUT row
  counts as a failure is a SEARCH-POLICY decision that must be pre-registered; this runner only records it;
* per job: candidates, work meter, CPU seconds of the job process, wall seconds, peak RSS of the job process.
"""
from __future__ import annotations
import json, multiprocessing as mp, os, pathlib, resource, time, traceback


def _worker(key, task, spec, costs, budget, memory, q):
    from neumann1 import invention_core as ic
    t0 = time.perf_counter()
    try:
        r = ic.solve(task, spec, costs, budget, memory)
        row = {"fit": r["fit"], "solved": r["solved"], "via": r["via"],
               "candidates": r["candidates"], "work": r["work"],
               "cpu_seconds": r["cpu_seconds"], "size": r["size"],
               "program": ic.show(ic._tup(r["ast"])) if r["ast"] else None}
    except Exception as e:            # recorded, never silently dropped
        row = {"error": "%s: %s" % (type(e).__name__, e), "trace": traceback.format_exc()[-2000:]}
    row.update({"key": list(key), "wall_seconds": round(time.perf_counter() - t0, 4),
                "maxrss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    q.put(row)


def done_keys(path):
    p = pathlib.Path(path)
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text().splitlines():
        if line.strip():
            out.add(tuple(json.loads(line)["key"]))
    return out


def run(jobs, path, workers=4, wall_cap_s=None, log=None):
    """jobs: iterable of (key_tuple, task, spec, costs, budget, memory)."""
    skip = done_keys(path)
    todo = [j for j in jobs if tuple(j[0]) not in skip]
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    running = {}
    with open(path, "a") as fh:
        def write(row):
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            if log:
                log(row)

        def drain():
            while True:
                try:
                    write(q.get_nowait())
                except Exception:
                    return
        while todo or running:
            while todo and len(running) < workers:
                key, task, spec, costs, budget, memory = todo.pop(0)
                p = ctx.Process(target=_worker, args=(key, task, spec, costs, budget, memory, q))
                p.start()
                running[p] = (key, time.time())
            time.sleep(0.02)
            drain()
            for p, (key, t0) in list(running.items()):
                if not p.is_alive():
                    p.join()
                    del running[p]
                elif wall_cap_s is not None and time.time() - t0 > wall_cap_s:
                    p.kill()
                    p.join()
                    del running[p]
                    write({"key": list(key), "timeout": wall_cap_s})
            drain()
        # a job that exited between the last drain and its join
        deadline = time.time() + 2
        while time.time() < deadline:
            drain()
            time.sleep(0.05)
    return done_keys(path)
