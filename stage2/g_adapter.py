"""G-0 token-only adapter (stage2/DESIGN.md 7.10, item 3): runs the stage-1 C4 pipeline code (stage1/run.py,
stage1/c3_compile.py, stage1/c4_select.py, stage1/pf.py, stage1/models.py) unchanged on the G-0 tasks.  Only tokens,
task data and the token-kind / separator rule of 7.4 are added; no algorithm and no hyperparameter is changed.

What install() changes (all at run time, in the imported stage-1 modules; no stage-1 file is edited):
  1 vocabulary   tasks.VOCAB / tasks.TOK get the three operator tokens '-', '*', '^' appended (ids 120-122; every
                 stage-1 id unchanged, so <pad> = 0, <eos> = 1).  Models built through it have 123 tokens.
  2 tasks        tasks.TASKS / tasks.SPEC get the G-0 suite (g_tasks.SUITE); tasks.draw dispatches those tasks to
                 g_tasks.draw.  tasks.train_set / eval_sets / encode and c4_select.selection_set are the stage-1
                 functions and keep their generation seeds ("train:<task>:<seed>", "eval:...", "select:<task>").
  3 token kinds  pf.token_classes: '-', '*', '^' are given the "+" kind (mapped to '+' before the stage-1 function).
  4 separators   pf.candidates: '-', '*', '^' are PF separators like '+' (the next_sep move), for the PF machine
                 (training, evaluation) and for the compile's head simulation (c3_compile.simulate), which both call
                 pf.candidates.
  5 pre-check    c3_compile.correct_table: the G-0 tasks' correct tables are the G-0a hand tables (exact on every
                 bin): stage2/results/g0a/tables.json (copy, reverse, xor, mul1) and
                 stage2/results/g0/a_prefix_sum/tables.json (prefix_sum).
Stage-1 tasks (addition, parity, ...) generate exactly the same data as before; their token kinds and separators are
unchanged because their sequences contain none of the three new tokens.

Run a stage-1 script through the adapter (its own argparse and main, in the adapted module):
  python stage2/g_adapter.py run --task copy --kind rope --phase g0 --out-root stage2/results/g0 --seed 9 --keep-best
  python stage2/g_adapter.py c3_compile --task copy --seed 9 --teacher <dir>/teacher_best.pt --dependency substitution --out <dir>
"""
from __future__ import annotations
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402
import tasks as T                # noqa: E402  (stage 1)
import pf as PFM                 # noqa: E402  (stage 1)
import g_tasks as G              # noqa: E402

OP_IDS = torch.tensor([G.TOK[s] for s in G.OPS])
TABLE_FILES = {"copy": HERE / "results/g0a/tables.json", "reverse": HERE / "results/g0a/tables.json",
               "xor": HERE / "results/g0a/tables.json", "mul1": HERE / "results/g0a/tables.json",
               "prefix_sum": HERE / "results/g0/a_prefix_sum/tables.json"}
SCRIPTS = ("run", "c3_compile", "c4_select")


def correct_tables():
    out = {}
    for t, f in TABLE_FILES.items():
        e = json.loads(f.read_text())[t]
        assert e["exact_on_all_bins"] and e["correct_table_for_precheck"], (t, f)
        out[t] = [row[:] for row in e["table"]]
    return out


def install():
    if getattr(T, "_g_adapter", False):
        return
    # 1 vocabulary
    assert T.VOCAB == G.VOCAB[:len(T.VOCAB)]
    T.VOCAB = list(G.VOCAB)
    T.TOK.update({s: G.TOK[s] for s in G.OPS})
    # 2 tasks
    T.TASKS = tuple(T.TASKS) + tuple(t for t in G.SUITE if t not in T.TASKS)
    T.SPEC.update({t: G.SPEC[t] for t in G.SUITE})
    stage1_draw = T.draw

    def draw(task, rng, lo, hi, train_dist=False):
        if task in G.SUITE:
            return G.draw(task, rng, lo, hi, train_dist=train_dist)
        return stage1_draw(task, rng, lo, hi, train_dist=train_dist)
    T.draw = draw
    # 3 token kinds
    stage1_classes = PFM.token_classes

    def token_classes(tokens, digit_ids, plus_id, eq_id, bar_id, node_lo, node_hi):
        t = torch.where(torch.isin(tokens, OP_IDS.to(tokens.device)), torch.full_like(tokens, plus_id), tokens)
        return stage1_classes(t, digit_ids, plus_id, eq_id, bar_id, node_lo, node_hi)
    PFM.token_classes = token_classes
    # 4 separators
    stage1_candidates = PFM.candidates

    def candidates(tape, t, h, xt, issep):
        return stage1_candidates(tape, t, h, xt, issep | torch.isin(tape, OP_IDS.to(tape.device)))
    PFM.candidates = candidates
    # 5 pre-check correct tables
    import c3_compile as CC
    stage1_correct = CC.correct_table
    tabs = correct_tables()

    def correct_table(task):
        if task in tabs:
            return [row[:] for row in tabs[task]]
        return stage1_correct(task)
    CC.correct_table = correct_table
    T._g_adapter = True


def run_script(name, argv):
    """execute stage1/<name>.py's `if __name__ == "__main__":` block (its argparse and main) inside the adapted,
    imported module"""
    assert name in SCRIPTS, name
    install()
    import importlib
    mod = importlib.import_module(name)
    path = ROOT / "stage1" / (name + ".py")
    src = path.read_text()
    key = 'if __name__ == "__main__":'
    block = src[src.index(key):].replace(key, "if True:", 1)
    sys.argv = [str(path)] + list(argv)
    exec(compile(block, str(path), "exec"), mod.__dict__)


if __name__ == "__main__":
    run_script(sys.argv[1], sys.argv[2:])
