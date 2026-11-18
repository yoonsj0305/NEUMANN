"""C4 (CANDIDATE_DESIGN.md 15): Occam selection for one task and seed between the student trained with the compiled
table (a) and the student trained with the all-"stay" table (b).

* Each student is taken at its judgment checkpoint (highest in-distribution evaluation accuracy, earliest if tied;
  the weights kept by run.py --keep-best as teacher_best.pt, checked against final.json).
* Selection-only validation data: 1,000 new in-distribution examples (the training length range, drawn as the
  training distribution) from their own generation seed "select:<task>" (training uses "train:<task>:<seed>", the
  evaluation sets "eval:..."), the same set for every seed.  Exact-match accuracy, the harness's evaluation code.
* Rule: the higher selection accuracy; if the two differ by at most 0.005, the table with fewer moving heads
  (a head is moving if its column is not all "stay"; the all-stay table has 0).  If the compiled table is itself all
  "stay", only one student exists and it is selected.
* Out-of-distribution data is not read here.

  python stage1/c4_select.py --task addition --seed 6
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks as T
import models as M
import run as R

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "results" / "c4"
N_SEL = 1000
TOL = 0.005


def selection_set(task, n=N_SEL):
    rng = random.Random("select:%s" % task)
    lo, hi = T.SPEC[task]["id"]
    return [T.encode(*T.draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(n)]


def moving_heads(policy):
    return sum(any(mv != 0 for mv in col) for col in policy)


def student(run_dir, sel):
    ck = torch.load(run_dir / "teacher_best.pt", weights_only=False)
    fin = json.loads((run_dir / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"], "kept checkpoint is not the judgment checkpoint"
    cfg = ck["cfg"]
    m = M.build("pf_search", len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    m.load_state_dict(ck["model"])
    acc, fl = R.exact_match(m, sel, "pf_search", cfg)
    return {"run": str(run_dir.relative_to(HERE.parent)), "judgment_step": ck["step"], "selection_accuracy": acc,
            "moving_heads": moving_heads(cfg["policy"]), "policy": cfg["policy"], "selection_eval_flops": fl}


def main(a):
    torch.set_num_threads(1)
    sel = selection_set(a.task)
    base = "c4_%s__pf_search__1M__s%d__N100000" % (a.task, a.seed)
    out = {"task": a.task, "seed": a.seed,
           "selection_set": {"generation_seed": "select:%s" % a.task, "size": N_SEL,
                             "lengths": list(T.SPEC[a.task]["id"]), "draw": "training distribution"},
           "rule": "higher selection accuracy; if |difference| <= %.3f, fewer moving heads (all stay = 0)" % TOL,
           "students": {}}
    for tag in ("compiled", "allstay"):
        d = RES / (base + "__" + tag)
        if (d / "final.json").exists():
            out["students"][tag] = student(d, sel)
    st = out["students"]
    if len(st) == 1:
        out["selected"] = next(iter(st))
        out["reason"] = "the compiled table is all stay: one student"
    else:
        diff = st["compiled"]["selection_accuracy"] - st["allstay"]["selection_accuracy"]
        out["difference_compiled_minus_allstay"] = diff
        if abs(diff) <= TOL:
            out["selected"] = min(st, key=lambda k: st[k]["moving_heads"])
            out["reason"] = "within %.3f: fewer moving heads" % TOL
        else:
            out["selected"] = "compiled" if diff > 0 else "allstay"
            out["reason"] = "higher selection accuracy"
    p = RES / ("selection_%s_s%d.json" % (a.task, a.seed))
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "students"}), {k: v["selection_accuracy"] for k, v in st.items()})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    p.add_argument("--seed", type=int, required=True)
    main(p.parse_args())
