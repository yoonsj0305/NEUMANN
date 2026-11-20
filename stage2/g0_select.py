"""G-0 selection (stage2/DESIGN.md 7.4) for one task and seed: four students -- the compiled table and the all-"stay"
table, each trained twice (restart 0 = run seed s, restart 1 = run seed s + 100; stage1/run.py --seed, so the restart
changes the initialisation, the batch order and the training sample, all from the same distribution) -- or two when
the compiled table is itself all "stay".

* Each student at its judgment checkpoint (highest in-distribution evaluation accuracy, earliest if tied; the weights
  kept by run.py --keep-best, checked against final.json) -- stage1/c4_select.student, unchanged, via the adapter.
* Selection-only data: "select:<task>", 1,000 new in-distribution examples (stage1/c4_select.selection_set).
* Rule: the highest selection accuracy; students within 0.005 of it (5 examples of 1,000, compared as integer counts)
  are tied, and among them the one with fewer moving heads, then the smaller restart number, is selected.
* Out-of-distribution data is not read here.

  python stage2/g0_select.py --task copy --seed 9      # writes stage2/results/g0/selection_copy_s9.json
  python stage2/g0_select.py --task copy --seed 12 --phase g0p      # G-0' (7.12): stage2/results/g0p, runs g0p_*
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g_adapter as A          # noqa: E402

RES = HERE / "results" / "g0"
TOL_COUNT = 5                  # 0.005 of the 1,000 selection examples


def name(task, seed, tag, phase="g0"):
    return "%s_%s__pf_search__1M__s%d__N100000__%s" % (phase, task, seed, tag)


def main(a):
    res = HERE / "results" / a.phase
    A.install()
    import torch
    import c4_select as CS
    torch.set_num_threads(1)
    sel = CS.selection_set(a.task)
    out = {"task": a.task, "seed": a.seed,
           "selection_set": {"generation_seed": "select:%s" % a.task, "size": len(sel), "draw": "training distribution"},
           "rule": "highest selection accuracy; within 0.005 (<= %d of %d examples): fewer moving heads, then the "
                   "smaller restart number" % (TOL_COUNT, len(sel)),
           "students": {}}
    for tag in ("compiled", "allstay"):
        for restart, sd in enumerate((a.seed, a.seed + 100)):
            d = res / name(a.task, sd, tag, a.phase)
            if (d / "final.json").exists():
                s = CS.student(d, sel)
                s.update(tag=tag, restart=restart, run_seed=sd, correct=round(s["selection_accuracy"] * len(sel)))
                out["students"]["%s_r%d" % (tag, restart)] = s
    st = out["students"]
    best = max(s["correct"] for s in st.values())
    pool = sorted(k for k, s in st.items() if best - s["correct"] <= TOL_COUNT)
    pick = min(pool, key=lambda k: (st[k]["moving_heads"], st[k]["restart"]))
    out.update({"best_correct": best, "tied_within_tolerance": pool, "selected": pick,
                "selected_run": st[pick]["run"],
                "reason": ("highest selection accuracy" if len(pool) == 1 else
                           "tied within 0.005: fewer moving heads, then the smaller restart number")})
    p = res / ("selection_%s_s%d.json" % (a.task, a.seed))
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("task", "seed", "selected", "reason")}),
          {k: v["selection_accuracy"] for k, v in st.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--phase", default="g0", help="results/<phase>/ and the run-name prefix (g0, or g0p for G-0')")
    main(ap.parse_args())
