"""G-0' teacher check (stage2/DESIGN.md 7.12): the in-distribution accuracy of a rope teacher at its judgment checkpoint
(teacher_best.pt, kept by run.py --keep-best and checked against final.json) on the selection-only set
"select:<task>" (1,000 new in-distribution examples, stage1/c4_select.selection_set, the set the students are selected
on), with stage1/run.py exact_match, through the token-only adapter.  Passed iff >= 0.95.  Out-of-distribution data
is not read.

  python stage2/g0p_teacher_check.py --task xor --seed 12      # writes stage2/results/g0p/teacher_select_xor_s12.json
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g_adapter as A          # noqa: E402

RES = HERE / "results" / "g0p"
MIN_ID = 0.95


def main(a):
    A.install()
    import torch
    import tasks as T
    import models as M
    import run as R
    import c4_select as CS
    torch.set_num_threads(1)
    d = RES / ("g0p_%s__rope__1M__s%d__N100000" % (a.task, a.seed))
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"], "kept checkpoint is not the judgment checkpoint"
    cfg = ck["cfg"]
    m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], cfg)
    m.load_state_dict(ck["model"])
    sel = CS.selection_set(a.task)
    with torch.no_grad():
        acc, fl = R.exact_match(m, sel, "rope", cfg)
    out = {"task": a.task, "run_seed": a.seed, "run": str(d.relative_to(HERE.parent)) if d.is_relative_to(HERE.parent) else str(d), "judgment_step": ck["step"],
           "selection_set": {"generation_seed": "select:%s" % a.task, "size": len(sel)},
           "selection_accuracy": acc, "selection_correct": round(acc * len(sel)), "threshold": MIN_ID,
           "passed": acc >= MIN_ID, "selection_eval_flops": fl,
           "judgment_train_flops": fin["judgment"]["train_flops_cum"], "run_steps": fin["steps"]}
    p = RES / ("teacher_select_%s_s%d.json" % (a.task, a.seed))
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("task", "run_seed", "judgment_step", "selection_accuracy", "passed")}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--seed", type=int, required=True, help="the teacher's run seed (s or s + 200)")
    main(ap.parse_args())
