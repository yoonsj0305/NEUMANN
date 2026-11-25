"""G-0' main run (stage2/DESIGN.md 7.11, 7.12 -- 7.12 first): the G-0 pipeline (stage2/g0_orchestrate.py) with one
change, the teacher restart; fresh seeds 12, 13, 14; no baselines (the G-0 baselines are reused).  Every job is a
stage-1 script run through the token-only adapter (stage2/g_adapter.py), one thread each, at most WORKERS at a time.
Re-runnable: the state is read from the result files, unfinished runs continue from their last checkpoint.

Per task (g_tasks.SUITE) and seed s in 12, 13, 14:
  teacher   rope 1M, stage-1 protocol (N = 1e5, at most 20,000 steps, early stop, judgment checkpoint kept), seed s
  check     stage2/g0p_teacher_check.py: in-distribution accuracy on "select:<task>" at the judgment checkpoint
            -> < 0.95: teacher restart, seed s + 200 (same protocol), and its check
               -> still < 0.95: pipeline failure "teacher" (stop)
            (the dependency extraction, the pre-check and the compile are unchanged; the compile reads the teacher
            that passed, with its own training data: c3_compile --seed <its run seed>)
  compile   c3_compile.py --dependency substitution (pre-check gate on): no table -> failure "precheck" (stop)
  students  pf_search on the compiled table and on the all-"stay" table, run seeds s and s + 100 (restarts 0, 1)
  select    stage2/g0_select.py --phase g0p, then the selection, the teacher check(s), the compile result and the raw
            records of the teacher(s) and the students are committed and pushed -- the out-of-distribution values of
            that task and seed are looked at only after this commit
Total FLOPs (stage2/g0p_report.py): both teachers when restarted.

The background-session limit: as G-0 (--max-wall, graceful cut after the next checkpoint).  Every launch, exit and
stop is written to stage2/results/g0p/QUEUE_LOG.txt.

  python stage2/g0p_orchestrate.py [--max-wall 6900] [--workers 4]      (exit 0: all done, 3: stopped at the limit)
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RES = HERE / "results" / "g0p"
sys.path.insert(0, str(HERE))
import g_tasks as G            # noqa: E402

PY = sys.executable
SEEDS = (12, 13, 14)
TEACHER_RESTART = 200
TEACHER_MIN_ID = 0.95
CUT_LEAD = 900
LOGDIR = pathlib.Path(os.environ.get("G0_LOGDIR", "/tmp/g0_logs"))
LOCK = os.environ.get("G0_GITLOCK", "/tmp/g0_git.lock")
QLOG = RES / "QUEUE_LOG.txt"
ALLSTAY = RES / "allstay_policy.json"
FOOTER = ("\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
          "Claude-Session: https://claude.ai/code/session_01VSWBvg7gXA6QqLM5pig7M5")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def qlog(msg):
    with open(QLOG, "a") as fh:
        fh.write("%s %s\n" % (now(), msg))


def rname(task, kind, seed, tag=""):
    return "g0p_%s__%s__1M__s%d__N100000%s" % (task, kind, seed, ("__" + tag) if tag else "")


def rdir(*a):
    return RES / rname(*a)


def jload(p):
    return json.loads(pathlib.Path(p).read_text())


def git(args, check=True):
    return subprocess.run(["flock", LOCK, "git"] + args, cwd=ROOT, check=check, capture_output=True, text=True)


def tracked(p):
    return subprocess.run(["git", "ls-files", "--error-unmatch", str(p)], cwd=ROOT, capture_output=True).returncode == 0


def commit(paths, msg):
    git(["add"] + [str(p) for p in paths])
    r = git(["commit", "-q", "-m", msg + FOOTER], check=False)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        qlog("git commit failed: %s" % (r.stderr.strip()[:200]))
        return
    for i in range(4):
        if git(["push", "-q", "origin", "stage2/g"], check=False).returncode == 0:
            return
        time.sleep(2 ** (i + 1))
    qlog("git push failed (will be pushed with a later commit)")


def run_files(d):
    return [d / f for f in ("config.json", "env.json", "log.jsonl", "final.json") if (d / f).exists()]


class Job:
    def __init__(self, key, cmd, kind, rundir=None, est=0.0, env=None, after=None):
        self.key, self.cmd, self.kind, self.rundir, self.est, self.env, self.after = key, cmd, kind, rundir, est, env, after
        self.proc, self.rows_cut, self.cut_seen, self.cut = None, None, None, False


def run_cmd(task, kind, seed, tag="", policy=None, keep=False):
    d = rdir(task, kind, seed, tag)
    cmd = [PY, str(HERE / "g_adapter.py"), "run", "--task", task, "--kind", kind, "--phase", "g0p",
           "--out-root", str(RES), "--seed", str(seed), "--threads", "1"]
    if keep:
        cmd.append("--keep-best")
    if tag:
        cmd += ["--tag", tag]
    if policy:
        cmd += ["--policy", str(policy)]
    if (d / "log.jsonl").exists():
        cmd.append("--resume")
    return cmd, d


def rows(d):
    p = d / "log.jsonl"
    return sum(1 for l in open(p) if l.strip()) if p.exists() else 0


def est_seconds(task, kind):
    """ordering only: worst-case hours of stage2/results/g0p/time_estimate.json (G-0 measured rates)"""
    p = RES / "time_estimate.json"
    if p.exists():
        e = jload(p)["per_task"].get(task)
        if e:
            return 3600 * e["teacher_worst_h" if kind == "rope" else "student_worst_h"]
    return 3600.0


def pipeline_state(task, s):
    """(jobs ready to run, status string)"""
    down = 4 * est_seconds(task, "pf_search")
    passed = None
    for k, ts in enumerate((s, s + TEACHER_RESTART)):
        td = rdir(task, "rope", ts)
        if not (td / "final.json").exists():
            cmd, d = run_cmd(task, "rope", ts, keep=True)
            return [Job("teacher %s s%d" % (task, ts), cmd, "run", d,
                        est_seconds(task, "rope") * (2 - k) + down)], "teacher" if k == 0 else "teacher restart"
        chk = RES / ("teacher_select_%s_s%d.json" % (task, ts))
        if not chk.exists():
            cmd = [PY, str(HERE / "g0p_teacher_check.py"), "--task", task, "--seed", str(ts)]
            return [Job("check %s s%d" % (task, ts), cmd, "select", None, 1e9)], "teacher check"
        if jload(chk)["passed"]:
            passed = ts
            break
    if passed is None:
        r = [jload(RES / ("teacher_select_%s_s%d.json" % (task, ts)))["selection_accuracy"]
             for ts in (s, s + TEACHER_RESTART)]
        return [], "failed: teacher select %.3f, restart %.3f < %.2f" % (r[0], r[1], TEACHER_MIN_ID)
    td = rdir(task, "rope", passed)
    teachers = [t for t in (s, s + TEACHER_RESTART) if (rdir(task, "rope", t) / "final.json").exists()]
    cd = RES / ("%s_compile_s%d" % (task, s))
    if not (cd / "compile_result.json").exists():
        cmd = [PY, str(HERE / "g_adapter.py"), "c3_compile", "--task", task, "--seed", str(passed),
               "--teacher", str(td / "teacher_best.pt"), "--dependency", "substitution", "--out", str(cd)]
        return [Job("compile %s s%d" % (task, s), cmd, "compile", None, 1e9, env={"THREADS": "1"})], "compile"
    cr = jload(cd / "compile_result.json")
    if "policy" not in cr:
        return [], "failed: pre-check (ratio %s)" % cr["precheck"]["dependency"]["ratio"]
    same = all(m == 0 for col in cr["policy"] for m in col)
    studs = ([] if same else [("compiled", cd / "compile_result.json")]) + [("allstay", ALLSTAY)]
    jobs = []
    for tag, pol in studs:
        for sd in (s, s + 100):
            d = rdir(task, "pf_search", sd, tag)
            if not (d / "final.json").exists():
                cmd, d = run_cmd(task, "pf_search", sd, tag, pol, keep=True)
                jobs.append(Job("student %s s%d %s" % (task, sd, tag), cmd, "run", d, est_seconds(task, "pf_search")))
    if jobs:
        return jobs, "students"
    sel = RES / ("selection_%s_s%d.json" % (task, s))
    if sel.exists() and tracked(sel):
        return [], "selected"
    cmd = [PY, str(HERE / "g0_select.py"), "--task", task, "--seed", str(s), "--phase", "g0p"]

    def after(job, task=task, s=s, sel=sel, cd=cd, studs=studs, teachers=teachers):
        if not sel.exists():
            return
        sj = jload(sel)
        acc = " · ".join("%s %.3f" % (k, v["selection_accuracy"]) for k, v in sj["students"].items())
        checks = [RES / ("teacher_select_%s_s%d.json" % (task, t)) for t in teachers]
        commit([sel, cd / "compile_result.json"] + checks, "stage2 G-0′ 선택: %s 시드 %d (선택 %s; 선택용 검증 %s)"
               % (task, s, sj["selected"], acc))
        files = []
        for t in teachers:
            files += run_files(rdir(task, "rope", t))
        for tag, _ in studs:
            for sd in (s, s + 100):
                files += run_files(rdir(task, "pf_search", sd, tag))
        commit(files + [QLOG], "stage2 G-0′: %s 시드 %d 교사·학생 원자료 (선택 커밋 뒤)" % (task, s))
    return [Job("select %s s%d" % (task, s), cmd, "select", None, 1e9, after=after)], "select"


def main(a):
    RES.mkdir(parents=True, exist_ok=True)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    if not ALLSTAY.exists():
        ALLSTAY.write_text(json.dumps({"policy": [[0] * 7 for _ in range(3)],
                                       "note": "G-0' all-stay table (7.4), the C4 student (b)"}, indent=1))
    t0 = time.time()
    t_cut, t_end = t0 + a.max_wall - CUT_LEAD, t0 + a.max_wall
    qlog("orchestrator start (workers %d, max_wall %d, python %s)" % (a.workers, a.max_wall, PY))
    running, failed = {}, {}
    while True:
        tnow = time.time()
        # finished jobs
        for key, j in list(running.items()):
            rc = j.proc.poll()
            if rc is None:
                continue
            del running[key]
            if j.cut:
                qlog("cut %s (after its checkpoint at log row %d)" % (key, rows(j.rundir) if j.rundir else -1))
                continue
            qlog("exit %s code %d" % (key, rc))
            if rc != 0:
                failed[key] = failed.get(key, 0) + 1
            elif j.after:
                j.after(j)
        # status and ready jobs
        ready, status = [], {}
        for task in G.SUITE:
            for s in SEEDS:
                js, st = pipeline_state(task, s)
                status["%s s%d" % (task, s)] = st
                ready += js
        ready = [j for j in ready if j.key not in running and failed.get(j.key, 0) < 2]
        if not ready and not running:
            if any(v >= 2 for v in failed.values()):
                qlog("stopped: jobs failed twice: %s" % [k for k, v in failed.items() if v >= 2])
                return 2
            qlog("all done: %s" % json.dumps(status, ensure_ascii=False))
            return 0
        # graceful cut: a training run is stopped one poll after its next log row (its checkpoint is written before
        # the row), unless it finished in the meantime (a finishing run writes final.json right after its last row)
        if tnow >= t_cut:
            for key, j in running.items():
                if j.kind != "run" or j.cut:
                    continue
                n = rows(j.rundir)
                if j.rows_cut is None:
                    j.rows_cut = n
                elif j.cut_seen is not None:
                    j.cut = True
                    j.proc.send_signal(signal.SIGTERM)
                elif n > j.rows_cut:
                    j.cut_seen = tnow
        if tnow >= t_end:
            for key, j in running.items():
                if not j.cut:
                    j.cut = True
                    j.proc.send_signal(signal.SIGTERM)
            for key, j in running.items():
                try:
                    j.proc.wait(60)
                except subprocess.TimeoutExpired:
                    j.proc.kill()
                qlog("stopped at the limit: %s (log rows %d)" % (key, rows(j.rundir) if j.rundir else -1))
            qlog("orchestrator stop at the limit: %s" % json.dumps(status, ensure_ascii=False))
            return 3
        # launch
        ready.sort(key=lambda j: -j.est)
        for j in ready:
            if len(running) >= a.workers:
                break
            if j.kind in ("run", "compile") and tnow >= t_cut:
                continue
            if j.kind == "select" and tnow >= t_end - 300:
                continue
            env = dict(os.environ, **(j.env or {}))
            out = open(LOGDIR / (j.key.replace(" ", "_") + ".out"), "a")
            j.proc = subprocess.Popen(j.cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, env=env)
            running[j.key] = j
            qlog("launch %s%s" % (j.key, " (resume)" if "--resume" in j.cmd else ""))
        time.sleep(a.poll)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-wall", type=float, default=6900)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--poll", type=float, default=10)
    sys.exit(main(ap.parse_args()))
