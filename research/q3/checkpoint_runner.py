"""Checkpointed, metered, restartable execution of (family, arm, task) jobs.

Infrastructure only: it never changes what `invention_core.solve` returns.

Guarantees (each covered by tests/test_checkpoint_runner.py):
  * one fresh forked process per job, at most `workers` at a time, each with its OWN result pipe, so a row can
    never be attributed to the wrong job or lost in a shared queue;
  * every job that was started ends in exactly one recorded row with a `status`:
      ok       the job returned a result
      error    the job raised a Python exception (message + traceback tail recorded)
      timeout  the job exceeded `wall_cap_s` and was killed (operational cap, machine dependent)
      died     the job process ended without sending a result (signal / exit code recorded)
    The runner only RECORDS these. Whether error/timeout/died count as failure, exclusion or INCOMPLETE is an
    evaluation-policy decision that must be pre-registered by the harness;
  * each row is appended, flushed and fsync'ed before the next job is scheduled; a torn final line left by a
    crash is truncated on the next start and that job simply runs again;
  * a key is written at most once: duplicate job keys are rejected up front, an exclusive flock on the
    checkpoint prevents two runners appending concurrently, and a checkpoint containing a duplicate key is
    rejected as corrupt;
  * restart: every key already in the checkpoint is skipped (single-attempt policy; no silent retries);
  * if the runner itself dies, its job processes are killed by the kernel (PR_SET_PDEATHSIG), so no orphan keeps
    burning CPU or writes anything.
"""
from __future__ import annotations
import ctypes, fcntl, json, multiprocessing as mp, os, pathlib, resource, signal, time, traceback

STATUSES = ("ok", "error", "timeout", "died")


def solve_job(key, task, spec, costs, budget, memory):
    """Default worker: one invention-core search. Returns a JSON-serialisable row (without key/status)."""
    from neumann1 import invention_core as ic
    r = ic.solve(task, spec, costs, budget, memory)
    return {"fit": r["fit"], "solved": r["solved"], "via": r["via"],
            "candidates": r["candidates"], "work": r["work"],
            "cpu_seconds": r["cpu_seconds"], "size": r["size"],
            "n_train": len(task["train"]), "n_hidden": len(task["test"]),
            "ast": r["ast"],
            "program": ic.show(ic._tup(r["ast"])) if r["ast"] else None}


def _child(conn, worker, key, payload):
    try:                                   # die with the runner: no orphans
        ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, signal.SIGKILL)
    except Exception:
        pass
    t0 = time.perf_counter()
    try:
        row = dict(worker(key, *payload))
        row["status"] = "ok"
    except Exception as e:
        row = {"status": "error", "error": "%s: %s" % (type(e).__name__, e),
               "trace": traceback.format_exc()[-2000:]}
    row["key"] = list(key)
    row["wall_seconds"] = round(time.perf_counter() - t0, 4)
    row["maxrss_kb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    conn.send(row)
    conn.close()


def load(path):
    """Rows by key. Truncates a torn final line; rejects duplicate keys and malformed interior lines."""
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    data = p.read_bytes()
    good = data.rfind(b"\n") + 1
    if good != len(data):                  # crash in the middle of a write
        with open(p, "r+b") as fh:
            fh.truncate(good)
            fh.flush()
            os.fsync(fh.fileno())
        data = data[:good]
    rows = {}
    for n, line in enumerate(data.decode().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)             # malformed interior line -> ValueError (corrupt checkpoint)
        key = tuple(row["key"])
        if key in rows:
            raise ValueError("corrupt checkpoint %s: duplicate key %r at line %d" % (path, key, n))
        if row.get("status") not in STATUSES:
            raise ValueError("corrupt checkpoint %s: bad status at line %d" % (path, n))
        rows[key] = row
    return rows


def done_keys(path):
    return set(load(path))


def run(jobs, path, workers=4, wall_cap_s=None, worker=solve_job, log=None):
    """jobs: iterable of (key_tuple, *payload); payload is passed to `worker(key, *payload)`.
    Returns the rows by key after the run."""
    jobs = [(tuple(j[0]), tuple(j[1:])) for j in jobs]
    keys = [k for k, _ in jobs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate job keys")
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError("checkpoint %s is locked by another runner" % path)
        have = load(path)
        todo = [(k, pl) for k, pl in jobs if k not in have]
        written = set(have)
        ctx = mp.get_context("fork")
        running = {}                       # process -> (key, parent_conn, start_time)

        def write(row):
            key = tuple(row["key"])
            if key in written:             # cannot happen; never write a key twice
                raise RuntimeError("internal error: second row for %r" % (key,))
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            written.add(key)
            if log:
                log(row)

        def receive(conn, wait):
            try:
                if conn.poll(wait):
                    return conn.recv()
            except (EOFError, OSError):
                pass
            return None

        while todo or running:
            while todo and len(running) < workers:
                key, payload = todo.pop(0)
                parent, child = ctx.Pipe(duplex=False)
                p = ctx.Process(target=_child, args=(child, worker, key, payload))
                p.start()
                child.close()
                running[p] = (key, parent, time.time())
            progressed = False
            for p, (key, conn, t0) in list(running.items()):
                row = receive(conn, 0)
                if row is None and not p.is_alive():
                    row = receive(conn, 1.0)          # exited: anything it sent is in the pipe
                    if row is None:
                        p.join()
                        row = {"key": list(key), "status": "died", "exitcode": p.exitcode}
                if row is None and wall_cap_s is not None and time.time() - t0 > wall_cap_s:
                    p.kill()
                    p.join()
                    row = receive(conn, 0) or {"key": list(key), "status": "timeout",
                                               "wall_cap_s": wall_cap_s}
                if row is not None:
                    write(row)
                    p.join()
                    conn.close()
                    del running[p]
                    progressed = True
            if not progressed:
                time.sleep(0.02)
    return load(path)
