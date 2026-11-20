"""G-0' step 1 (stage2/DESIGN.md 7.11, 7.12): time estimate before the main run (stop if > 48 h).

Jobs: per task (the frozen suite) and seed s in 12, 13, 14: a teacher (rope 1M), its selection-set check, at most one
teacher restart (seed s + 200) with its check, the compile, 4 students (compiled / all-stay x seeds s, s + 100), the
selection.  No baselines (the G-0 baselines are reused, 7.11).

Rates are the G-0 measurements (stage2/results/g0, same machine, 4 runs at a time, 1 thread each), not the G-0 bench
(which underestimated the students under 4-way load):
  seconds per step (training + evaluations) of a run = (wall_train_s + wall_eval_s) / steps, per task the largest over
  the G-0 teachers (rope, seeds 9-11) and over the G-0 students (pf_search, all 4 tables x restarts);
  compile = the largest G-0 compile wall of the task.
Cases:
  worst          every teacher restarted, every teacher and student 20,000 steps
  G-0 measured   each task and seed as its G-0 mean (teacher + compile + 4 students, measured walls), no restart
  G-0 + restarts the G-0 measured case plus one worst-case teacher per seed (every teacher restarted)
Wall with 4 workers = CPU / 4, and CPU / 4 + the longest single run as a tail bound.

  python stage2/g0p_time.py        # writes stage2/results/g0p/time_estimate.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g_tasks as G            # noqa: E402

G0 = HERE / "results" / "g0"
OUT = HERE / "results" / "g0p"
SEEDS_G0, SEEDS = (9, 10, 11), (12, 13, 14)
MAX_STEPS = 20000
SMALL_S = 60.0                 # a selection-set check or a selection (G-0 selections took about 10 s)


def wall(d):
    f = json.loads((d / "final.json").read_text())
    return f["wall_train_s"] + f["wall_eval_s"], f["steps"]


def main():
    per, tot = {}, {"worst": 0.0, "g0_measured": 0.0, "g0_plus_restarts": 0.0}
    longest = 0.0
    for t in G.SUITE:
        teach = [wall(G0 / ("g0_%s__rope__1M__s%d__N100000" % (t, s))) for s in SEEDS_G0]
        studs, comp, meas = [], [], []
        for s in SEEDS_G0:
            cd = G0 / ("%s_compile_s%d" % (t, s)) / "compile_result.json"
            m = wall(G0 / ("g0_%s__rope__1M__s%d__N100000" % (t, s)))[0]
            if cd.exists():
                c = json.loads(cd.read_text())["wall_s"]
                comp.append(c)
                m += c
                for tag in ("compiled", "allstay"):
                    for sd in (s, s + 100):
                        w = wall(G0 / ("g0_%s__pf_search__1M__s%d__N100000__%s" % (t, sd, tag)))
                        studs.append(w)
                        m += w[0]
                meas.append(m)
        t_sps = max(w / n for w, n in teach)
        s_sps = max(w / n for w, n in studs)
        t_worst, s_worst, c_max = t_sps * MAX_STEPS, s_sps * MAX_STEPS, max(comp)
        worst_seed = 2 * t_worst + 4 * s_worst + c_max + 3 * SMALL_S
        meas_seed = sum(meas) / len(meas) + 2 * SMALL_S
        per[t] = {"teacher_s_per_step": t_sps, "student_s_per_step": s_sps, "teacher_worst_h": t_worst / 3600,
                  "student_worst_h": s_worst / 3600, "compile_max_s": c_max,
                  "per_seed_h": {"worst": worst_seed / 3600, "g0_measured": meas_seed / 3600,
                                 "g0_plus_restarts": (meas_seed + t_worst + SMALL_S) / 3600},
                  "g0_measured_per_seed_h_values": [m / 3600 for m in meas]}
        tot["worst"] += len(SEEDS) * worst_seed
        tot["g0_measured"] += len(SEEDS) * meas_seed
        tot["g0_plus_restarts"] += len(SEEDS) * (meas_seed + t_worst + SMALL_S)
        longest = max(longest, t_worst, s_worst)
    res = {"per_task": per, "cpu_hours": {k: v / 3600 for k, v in tot.items()},
           "wall_hours_4_workers": {k: v / 4 / 3600 for k, v in tot.items()},
           "wall_hours_4_workers_plus_longest_run": {k: (v / 4 + longest) / 3600 for k, v in tot.items()},
           "longest_run_hours": longest / 3600, "limit_hours": 48,
           "note": "rates measured in G-0 (stage2/results/g0); no baselines (reused from G-0)"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "time_estimate.json").write_text(json.dumps(res, indent=1))
    print("| task | teacher worst h | student worst h | compile max s | per seed h: worst · G-0 measured · + restart |")
    for t, p in per.items():
        print("| %s | %.2f | %.2f | %.0f | %.2f · %.2f · %.2f |" % (t, p["teacher_worst_h"], p["student_worst_h"],
                                                           p["compile_max_s"], p["per_seed_h"]["worst"],
                                                           p["per_seed_h"]["g0_measured"],
                                                           p["per_seed_h"]["g0_plus_restarts"]))
    print(json.dumps({k: res[k] for k in ("cpu_hours", "wall_hours_4_workers", "wall_hours_4_workers_plus_longest_run",
                                          "longest_run_hours")}, indent=1))


if __name__ == "__main__":
    main()
