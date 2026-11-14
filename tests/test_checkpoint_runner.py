"""Checkpoint runner: every started job ends in exactly one recorded row; restart loses and repeats nothing."""
import json, os, signal, subprocess, sys, time
import pytest
sys.path.insert(0, "research/q3")
import checkpoint_runner as cr
from neumann1 import invention_core as ic

VOLATILE = ("wall_seconds", "cpu_seconds", "maxrss_kb")


def _jobs(n=6):
    import invention_dev_family
    src, _ = invention_dev_family.tasks()
    un = ic.untrained_costs()["*"]
    return [(("dev", "A", t["id"]), t, (), un, 2000, None) for t in src[:n]]


def _stable(rows):
    return {k: {f: v for f, v in r.items() if f not in VOLATILE} for k, r in rows.items()}


# ---- workers used to provoke every terminal status (module level: forked children import them) ----
def w_echo(key, x):
    time.sleep(0.15)
    return {"value": x * 2}


def w_raise(key, x):
    raise ValueError("boom %s" % x)


def w_exit(key, x):
    os._exit(7)


def w_sigkill(key, x):
    os.kill(os.getpid(), signal.SIGKILL)


def w_hang(key, x):
    time.sleep(3600)


def w_mixed(key, kind):
    return {"ok": w_echo, "raise": w_raise, "exit": w_exit, "kill": w_sigkill, "hang": w_hang}[kind](key, 1)


def test_restart_skips_done_and_matches_fresh(tmp_path):
    jobs = _jobs()
    part = tmp_path / "part.jsonl"
    cr.run(jobs[:3], part, workers=2)
    assert len(cr.done_keys(part)) == 3
    rows = cr.run(jobs, part, workers=2)               # restart: only the 3 missing run
    assert len(rows) == 6 and len(part.read_text().splitlines()) == 6
    fresh = cr.run(jobs, tmp_path / "fresh.jsonl", workers=2)
    assert _stable(rows) == _stable(fresh)
    assert all(r["status"] == "ok" and "n_hidden" in r for r in rows.values())


def test_every_terminal_status_is_recorded_exactly_once(tmp_path):
    kinds = ["ok", "raise", "exit", "kill", "hang", "ok"]
    jobs = [(("t", k, str(i)), k) for i, k in enumerate(kinds)]
    out = tmp_path / "s.jsonl"
    rows = cr.run(jobs, out, workers=3, wall_cap_s=1.0, worker=w_mixed)
    got = {k[1] + k[2]: r for k, r in rows.items()}
    assert len(rows) == len(jobs) == len(out.read_text().splitlines())
    assert got["ok0"]["status"] == got["ok5"]["status"] == "ok" and got["ok0"]["value"] == 2
    assert got["raise1"]["status"] == "error" and "boom" in got["raise1"]["error"]
    assert got["exit2"]["status"] == "died" and got["exit2"]["exitcode"] == 7
    assert got["kill3"]["status"] == "died" and got["kill3"]["exitcode"] == -signal.SIGKILL
    assert got["hang4"]["status"] == "timeout" and got["hang4"]["wall_cap_s"] == 1.0
    again = cr.run(jobs, out, workers=3, wall_cap_s=1.0, worker=w_mixed)   # single attempt: nothing reruns
    assert again == rows and len(out.read_text().splitlines()) == len(jobs)


def test_torn_final_line_is_truncated_and_job_reruns(tmp_path):
    jobs = [(("t", "ok", str(i)), i) for i in range(4)]
    out = tmp_path / "torn.jsonl"
    cr.run(jobs[:3], out, workers=2, worker=w_echo)
    lines = out.read_text().splitlines(keepends=True)
    out.write_text("".join(lines[:2]) + lines[2][: len(lines[2]) // 2])     # crash mid-write of row 3
    assert len(cr.load(out)) == 2 and out.read_text().endswith("\n")
    rows = cr.run(jobs, out, workers=2, worker=w_echo)
    assert sorted(rows) == sorted(tuple(j[0]) for j in jobs)
    assert len(out.read_text().splitlines()) == 4


def test_duplicates_are_rejected(tmp_path):
    out = tmp_path / "d.jsonl"
    with pytest.raises(ValueError):
        cr.run([(("a",), 1), (("a",), 2)], out, worker=w_echo)
    cr.run([(("a",), 1)], out, worker=w_echo)
    line = out.read_text()
    out.write_text(line + line)                                             # a second writer's row
    with pytest.raises(ValueError):
        cr.load(out)


def test_second_runner_on_same_checkpoint_is_refused(tmp_path):
    out = tmp_path / "lock.jsonl"
    code = ("import sys,time; sys.path.insert(0,'research/q3'); sys.path.insert(0,'tests');"
            "import checkpoint_runner as cr, test_checkpoint_runner as t;"
            "cr.run([(('h',), 'hang')], sys.argv[1], workers=1, wall_cap_s=4, worker=t.w_mixed)")
    p = subprocess.Popen([sys.executable, "-c", code, str(out)])
    try:
        deadline = time.time() + 10
        while not out.exists() and time.time() < deadline:
            time.sleep(0.05)
        time.sleep(0.3)
        with pytest.raises(RuntimeError):
            cr.run([(("x",), 1)], out, worker=w_echo)
    finally:
        p.kill()
        p.wait()


def test_runner_killed_mid_run_restarts_without_loss_duplicates_or_orphans(tmp_path):
    out = tmp_path / "k.jsonl"
    marker = "CKPT_MARKER_%d" % os.getpid()
    code = ("import sys; sys.path.insert(0,'research/q3'); sys.path.insert(0,'tests');"
            "import checkpoint_runner as cr, test_checkpoint_runner as t;"
            "cr.run([(('k', str(i)), i) for i in range(12)], sys.argv[1], workers=2, worker=t.w_echo)")
    p = subprocess.Popen([sys.executable, "-c", code, str(out), marker])
    deadline = time.time() + 20
    while time.time() < deadline and (not out.exists() or len(out.read_text().splitlines()) < 3):
        time.sleep(0.02)
    p.send_signal(signal.SIGKILL)
    p.wait()
    time.sleep(0.5)
    assert subprocess.run(["pgrep", "-f", marker], capture_output=True).stdout == b""   # no orphan job
    before = len(cr.load(out))
    assert 3 <= before < 12
    jobs = [(("k", str(i)), i) for i in range(12)]
    rows = cr.run(jobs, out, workers=2, worker=w_echo)
    assert len(rows) == 12 and len(out.read_text().splitlines()) == 12
    fresh = cr.run(jobs, tmp_path / "f.jsonl", workers=2, worker=w_echo)
    assert _stable(rows) == _stable(fresh)
