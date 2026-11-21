"""H-0 step 1 (stage2/DESIGN.md 9.6, 9.9, 9.10): time estimate before the main run (stop if > 48 h).

Jobs per task (h_tasks.SUITE) and seed s in 15, 16, 17: teacher (rope 1M) + selection-set check, up to three teacher
restarts (s+200, s+300, s+400) with checks (T2), the compile, 4 students (compiled / all-stay x s, s+100), the
selection; per task the 4 BOS baselines (abacus, rope, looped_rr, gru; seed 0).  Bundle 1 = reverse, rev_xor, xor;
bundle 2 = copy, mul1, prefix_sum (9.9).

Rates: measured in G-0 and G-0' (stage2/results/g0, g0p; same machine, 4 runs at a time, 1 thread each).  BOS adds
one token per sequence (ignored).  rev_xor uses xor's rates and xor's G-0 baselines.
  seconds per step = (wall_train_s + wall_eval_s) / steps; teacher / student: the largest over the G-0 and G-0' runs
  of the task; baseline: the G-0 run of the task and kind; compile: the largest G-0 / G-0' compile wall.
Cases (CPU hours; wall = CPU / 4, and + the longest single run of the bundle as a tail bound, per bundle since the
bundles run one after the other):
  worst          every seed uses all four teachers, every teacher, student and baseline 20,000 steps
  measured       per task and seed the mean measured G-0 / G-0' cost (all teachers that seed trained, compile, 4
                 students) and the G-0 baseline walls
  measured + 3 restarts   the measured case plus three worst-case teachers for every seed

  python stage2/h0_time.py        # writes stage2/results/h0/time_estimate.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import h_tasks as HT           # noqa: E402

RES = {"g0": HERE / "results" / "g0", "g0p": HERE / "results" / "g0p"}
OUT = HERE / "results" / "h0"
SEEDS = {"g0": (9, 10, 11), "g0p": (12, 13, 14)}
H0_SEEDS = (15, 16, 17)
MAX_STEPS, SMALL_S, LIMIT = 20000, 60.0, 48
KINDS = ("abacus", "rope", "looped_rr", "gru")
BUNDLES = {1: ("reverse", "rev_xor", "xor"), 2: ("copy", "mul1", "prefix_sum")}


def wall(d):
    f = json.loads((d / "final.json").read_text())
    return f["wall_train_s"] + f["wall_eval_s"], f["steps"]


def measured(src):
    """per seed of G-0 / G-0': (seconds: all teachers + compile + students, teacher (w, n) list, student list, compile)"""
    out, teach, studs, comp = [], [], [], []
    for ph, seeds in SEEDS.items():
        for s in seeds:
            m = 0.0
            for ts in (s, s + 200):
                d = RES[ph] / ("%s_%s__rope__1M__s%d__N100000" % (ph, src, ts))
                if (d / "final.json").exists():
                    w = wall(d)
                    teach.append(w)
                    m += w[0] + SMALL_S
            cd = RES[ph] / ("%s_compile_s%d" % (src, s)) / "compile_result.json"
            if cd.exists():
                c = json.loads(cd.read_text())
                comp.append(c["wall_s"])
                m += c["wall_s"]
                for tag in ("compiled", "allstay"):
                    for sd in (s, s + 100):
                        d = RES[ph] / ("%s_%s__pf_search__1M__s%d__N100000__%s" % (ph, src, sd, tag))
                        if (d / "final.json").exists():
                            w = wall(d)
                            studs.append(w)
                            m += w[0]
            out.append(m + SMALL_S)
    return out, teach, studs, comp


def main():
    per, tot = {}, {b: {"worst": 0.0, "measured": 0.0, "measured_plus_3_restarts": 0.0} for b in BUNDLES}
    longest = {b: 0.0 for b in BUNDLES}
    for b, tasks in BUNDLES.items():
        for t in tasks:
            src = "xor" if t == "rev_xor" else t
            meas, teach, studs, comp = measured(src)
            t_sps = max(w / n for w, n in teach)
            s_sps = max(w / n for w, n in studs)
            t_worst, s_worst, c_max = t_sps * MAX_STEPS, s_sps * MAX_STEPS, max(comp)
            base = {k: wall(RES["g0"] / ("g0_%s__%s__1M__s0__N100000" % (src, k))) for k in KINDS}
            b_worst = sum(w / n * MAX_STEPS for w, n in base.values())
            b_meas = sum(w for w, _ in base.values())
            worst_seed = 4 * (t_worst + SMALL_S) + 4 * s_worst + c_max + SMALL_S
            meas_seed = sum(meas) / len(meas)
            plus_seed = meas_seed + 3 * (t_worst + SMALL_S)
            per[t] = {"bundle": b, "rates_from": src, "teacher_s_per_step": t_sps, "student_s_per_step": s_sps,
                      "teacher_worst_h": t_worst / 3600, "student_worst_h": s_worst / 3600, "compile_max_s": c_max,
                      "baselines_worst_h": b_worst / 3600, "baselines_measured_h": b_meas / 3600,
                      "baseline_longest_worst_h": max(w / n * MAX_STEPS for w, n in base.values()) / 3600,
                      "per_seed_h": {"worst": worst_seed / 3600, "measured": meas_seed / 3600,
                                     "measured_plus_3_restarts": plus_seed / 3600},
                      "measured_per_seed_h_values": [m / 3600 for m in meas]}
            tot[b]["worst"] += 3 * worst_seed + b_worst
            tot[b]["measured"] += 3 * meas_seed + b_meas
            tot[b]["measured_plus_3_restarts"] += 3 * plus_seed + b_meas
            longest[b] = max(longest[b], t_worst, s_worst, max(w / n * MAX_STEPS for w, n in base.values()))
    both = {k: tot[1][k] + tot[2][k] for k in tot[1]}
    res = {"per_task": per, "bundles": {b: list(v) for b, v in BUNDLES.items()},
           "cpu_hours": {"bundle1": {k: v / 3600 for k, v in tot[1].items()},
                         "bundle2": {k: v / 3600 for k, v in tot[2].items()}, "both": {k: v / 3600 for k, v in both.items()}},
           "wall_hours_4_workers_plus_longest_run": {
               "bundle1": {k: (v / 4 + longest[1]) / 3600 for k, v in tot[1].items()},
               "bundle2": {k: (v / 4 + longest[2]) / 3600 for k, v in tot[2].items()},
               "both": {k: (tot[1][k] / 4 + longest[1] + tot[2][k] / 4 + longest[2]) / 3600 for k in both}},
           "longest_run_hours": {b: v / 3600 for b, v in longest.items()}, "limit_hours": LIMIT,
           "note": "rates measured in G-0 and G-0' (stage2/results/g0, g0p); rev_xor = xor's rates"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "time_estimate.json").write_text(json.dumps(res, indent=1))
    print("| task | bundle | teacher worst h | student worst h | baselines worst · measured h | per seed h: worst · measured · +3 restarts |")
    for t, p in per.items():
        print("| %s | %d | %.2f | %.2f | %.2f · %.2f | %.2f · %.2f · %.2f |" % (
            t, p["bundle"], p["teacher_worst_h"], p["student_worst_h"], p["baselines_worst_h"],
            p["baselines_measured_h"], p["per_seed_h"]["worst"], p["per_seed_h"]["measured"],
            p["per_seed_h"]["measured_plus_3_restarts"]))
    print(json.dumps({k: res[k] for k in ("cpu_hours", "wall_hours_4_workers_plus_longest_run", "longest_run_hours")},
                     indent=1))


if __name__ == "__main__":
    main()
