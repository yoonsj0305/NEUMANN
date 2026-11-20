"""G-0 step 4 (stage2/DESIGN.md 7.8): time estimate before the main run.

  bench     For every task of the suite and every model of the run (rope = teacher and baseline, pf_search = student,
            abacus, looped_rr, gru): stage1/run.py through the adapter, BENCH_STEPS training steps and one evaluation
            (in-distribution 1,000 + three out-of-distribution bins of 500, as every 1,000 steps in the real run),
            WORKERS runs at a time on the 4 cores, as in the main run.  Written to a scratch directory (not results).
  estimate  seconds per training step and per evaluation from the bench; per run
            worst case = 20,000 steps + 20 evaluations,
            stage-1-like case = the step count of the matching stage-1 run (same kind; addition-like or parity-like
            task), at most 20,000;
            total CPU and wall time with 4 workers (wall = CPU / 4, plus the longest single run as a tail bound).
            Jobs: per task and seed s in 9-11 a teacher, the compile (measured stage-1 C4 compile time, scaled by
            output steps), 4 students; per task 4 baselines (seed 0).

  python stage2/g0_time.py bench --out <scratch dir>
  python stage2/g0_time.py estimate --bench <scratch dir>      # writes stage2/results/g0/time_estimate.json
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import g_tasks as G            # noqa: E402

KINDS = ("rope", "pf_search", "abacus", "looped_rr", "gru")
BENCH_STEPS = 40
MAX_STEPS, EVAL_EVERY = 20000, 1000
SEEDS = 3
# stage-1 step counts of comparable runs (final.json "steps"): addition-like (copy, reverse, mul1, prefix_sum) and
# parity-like (xor: bits) -- teacher = C4 rope seeds 6-8, students = C4 pf_search (mean of compiled/allstay),
# baselines = Phase A / A' / A'' seed 0
STAGE1_RUNS = {
    "rope_teacher": {"addition": "stage1/results/c4/c4_addition__rope__1M__s{s}__N100000",
                     "parity": "stage1/results/c4/c4_parity__rope__1M__s{s}__N100000"},
    "pf_search": {"addition": "stage1/results/c4/c4_addition__pf_search__1M__s{s}__N100000__{tag}",
                  "parity": "stage1/results/c4/c4_parity__pf_search__1M__s{s}__N100000__{tag}"},
    "rope": {"addition": "stage1/results/phaseA4/phaseA4_addition__rope__1M__s0__N100000",
             "parity": "stage1/results/phaseA4/phaseA4_parity__rope__1M__s0__N100000"},
    "abacus": {"addition": "stage1/results/phaseA/addition__abacus__1M__s0__N100000",
               "parity": "stage1/results/phaseA/parity__abacus__1M__s0__N100000"},
    "looped_rr": {"addition": "stage1/results/phaseA2/phaseA2_addition__looped_rr__1M__s0__N100000",
                  "parity": "stage1/results/phaseA2/phaseA2_parity__looped_rr__1M__s0__N100000"},
    "gru": {"addition": "stage1/results/phaseA/addition__gru__1M__s0__N100000",
            "parity": "stage1/results/phaseA/parity__gru__1M__s0__N100000"},
}


def bench(a):
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pol = out / "allstay_policy.json"
    pol.write_text(json.dumps({"policy": [[0] * 7 for _ in range(3)]}))
    lines = []
    for t in G.SUITE:
        for k in KINDS:
            if (out / ("bench_%s__%s__1M__s0__N100000" % (t, k)) / "final.json").exists():
                continue
            lines.append("%s %s" % (t, k))
    script = ("%s %s run --task $0 --kind $1 --phase bench --out-root %s --seed 0 --threads 1 --max-steps %d "
              "--eval-every %d --policy %s > %s/$0_$1.out 2>&1; echo $0 $1 $?"
              % (sys.executable, HERE / "g_adapter.py", out, BENCH_STEPS, BENCH_STEPS, pol, out))
    subprocess.run(["xargs", "-P", str(a.workers), "-L", "1", "bash", "-c", script], input="\n".join(lines),
                   text=True, cwd=ROOT, check=True)


def stage1_steps(kind, like):
    p = STAGE1_RUNS[kind][like]
    if kind == "rope_teacher":
        vals = [json.loads((ROOT / p.format(s=s) / "final.json").read_text())["steps"] for s in (6, 7, 8)]
    elif kind == "pf_search":
        vals = [json.loads((ROOT / p.format(s=s, tag=tag) / "final.json").read_text())["steps"]
                for s in (6, 7, 8) for tag in ("compiled", "allstay")]
    else:
        vals = [json.loads((ROOT / p / "final.json").read_text())["steps"]]
    return sum(vals) / len(vals), vals


def estimate(a):
    b = pathlib.Path(a.bench)
    per = {}
    for t in G.SUITE:
        like = "parity" if t == "xor" else "addition"
        for k in KINDS:
            f = json.loads((b / ("bench_%s__%s__1M__s0__N100000" % (t, k)) / "final.json").read_text())
            sps = f["wall_train_s"] / f["steps"]
            spe = f["wall_eval_s"]                       # one evaluation
            n_ev = MAX_STEPS // EVAL_EVERY
            worst = sps * MAX_STEPS + spe * n_ev
            roles = ["student"] if k == "pf_search" else (["teacher", "baseline"] if k == "rope" else ["baseline"])
            for role in roles:
                key = "rope_teacher" if role == "teacher" else k
                st_mean, st_vals = stage1_steps(key, like)
                typ = sps * st_mean + spe * max(1, round(st_mean / EVAL_EVERY))
                per["%s|%s|%s" % (t, k, role)] = {"s_per_step": sps, "s_per_eval": spe, "worst_s": worst,
                                                  "stage1_like_steps": st_mean, "stage1_like_steps_values": st_vals,
                                                  "stage1_like_s": typ}
    # compile: measured stage-1 C4 addition compile (wall from the queue log) scaled by output steps per example
    comp = {}
    for t in G.SUITE:
        comp[t] = a.compile_s * {"copy": 11 / 12, "reverse": 11 / 12, "xor": 17 / 12, "mul1": 12 / 12,
                                 "prefix_sum": 11 / 12}[t]
    tot = {"worst": 0.0, "stage1_like": 0.0}
    longest = {"worst": 0.0, "stage1_like": 0.0}
    rows = []
    for t in G.SUITE:
        for role, k, n in (("teacher", "rope", SEEDS), ("student", "pf_search", 4 * SEEDS), ("baseline", "rope", 1),
                           ("baseline", "abacus", 1), ("baseline", "looped_rr", 1), ("baseline", "gru", 1)):
            e = per["%s|%s|%s" % (t, k, role)]
            tot["worst"] += n * e["worst_s"]
            tot["stage1_like"] += n * e["stage1_like_s"]
            longest["worst"] = max(longest["worst"], e["worst_s"])
            longest["stage1_like"] = max(longest["stage1_like"], e["stage1_like_s"])
            rows.append((t, role, k, n, e["s_per_step"], e["s_per_eval"], e["worst_s"], e["stage1_like_s"]))
        tot["worst"] += SEEDS * comp[t]
        tot["stage1_like"] += SEEDS * comp[t]
    res = {"per_run": {"%s|%s" % (k.split("|")[0], k.split("|")[1]): v for k, v in per.items()
                       if not k.endswith("|teacher")},
           "per_run_role": per, "compile_s": comp,
           "cpu_hours": {k: v / 3600 for k, v in tot.items()},
           "wall_hours_4_workers": {k: tot[k] / 4 / 3600 for k in tot},
           "wall_hours_4_workers_plus_longest_run": {k: (tot[k] / 4 + longest[k]) / 3600 for k in tot},
           "longest_run_hours": {k: v / 3600 for k, v in longest.items()},
           "limit_hours": 48,
           "note": "worst = every run 20,000 steps and 20 evaluations; stage1_like = the step counts of the matching "
                   "stage-1 runs. Bench: %d steps + 1 evaluation per run, 4 runs at a time, 1 thread each."
                   % BENCH_STEPS}
    (HERE / "results" / "g0" / "time_estimate.json").write_text(json.dumps(res, indent=1))
    print("| task | role | kind | runs | s/step | s/eval | worst h/run | stage-1-like h/run |")
    for r in rows:
        print("| %s | %s | %s | %d | %.3f | %.1f | %.2f | %.2f |" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6] / 3600,
                                                                   r[7] / 3600))
    print(json.dumps({k: res[k] for k in ("cpu_hours", "wall_hours_4_workers", "wall_hours_4_workers_plus_longest_run",
                                          "longest_run_hours")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("bench", "estimate"))
    ap.add_argument("--out")
    ap.add_argument("--bench")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--compile-s", type=float, default=450.0, help="stage-1 C4 addition compile wall seconds")
    a = ap.parse_args()
    bench(a) if a.mode == "bench" else estimate(a)
