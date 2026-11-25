"""H-0 token-only adapter (stage2/DESIGN.md 9.1, 9.6): the G-0 adapter (stage2/g_adapter.py) plus the BOS convention.
Runs the stage-1 C4 pipeline code (stage1/run.py, c3_compile.py, c4_select.py, pf.py, models.py) unchanged on the six
H-0 tasks.  Only tokens, task data and the 7.4 token-kind / separator rule are added; no algorithm and no
hyperparameter is changed.

What install() changes (at run time, in the imported stage-1 modules; no stage-1 file is edited):
  1 vocabulary   tasks.VOCAB / tasks.TOK = stage2/h_tasks.py VOCAB: the stage-1 tokens, the G-0 operators '-', '*',
                 '^' (ids 120-122) and '<bos>' (id 123).  Models built through it have 124 tokens.
  2 tasks        tasks.TASKS / tasks.SPEC get the H-0 suite (h_tasks.SUITE: copy, reverse, xor, mul1, prefix_sum,
                 rev_xor); tasks.draw dispatches them to g_tasks.draw (rev_xor: h_tasks.rev_xor, the same draw order)
                 and puts '<bos>' in front of the prompt.  tasks.train_set / eval_sets / encode and
                 c4_select.selection_set are the stage-1 functions with their generation seeds, so every set equals
                 h_tasks.train_set / eval_sets / selection_set (stage2/h0_adapter_check.py).  Stage-1 tasks
                 (addition, parity, ...) are unchanged (no BOS; not run in H-0).
  3 token kinds  pf.token_classes: '-', '*', '^' are the "+" kind (as G-0).  '<bos>' needs no change: it is "other".
  4 separators   pf.candidates: '-', '*', '^' are PF separators (as G-0).  '<bos>' is not a separator; it sits at
                 position 0, the destination of the "start" move.
  5 pre-check    c3_compile.correct_table: the H-0a BOS hand tables (stage2/results/h0a/bos/tables.json, exact on every
                 bin).

  python stage2/h_adapter.py run --task reverse --kind rope --phase h0 --out-root stage2/results/h0 --seed 15 --keep-best
  python stage2/h_adapter.py c3_compile --task reverse --seed 15 --teacher <dir>/teacher_best.pt --dependency substitution --out <dir>
"""
from __future__ import annotations
import json
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
import h_tasks as HT             # noqa: E402

OP_IDS = torch.tensor([HT.TOK[s] for s in HT.OPS])
TABLE_FILE = HERE / "results/h0a/bos/tables.json"
SCRIPTS = ("run", "c3_compile", "c4_select")


def correct_tables():
    tabs = json.loads(TABLE_FILE.read_text())
    out = {}
    for t in HT.SUITE:
        assert tabs[t]["exact_on_all_bins"], t
        out[t] = [row[:] for row in tabs[t]["table"]]
    return out


def h_draw(task, rng, lo, hi, train_dist=False):
    """one H-0 example (prompt with BOS, answer, bin length): g_tasks.draw's logic (rev_xor: the one-length branch)"""
    if task == "rev_xor":
        n = rng.randint(lo, hi)
        p, a = HT.rev_xor(n, rng)
    else:
        p, a, n = G.draw(task, rng, lo, hi, train_dist=train_dist)
    return [HT.BOS] + p, a, n


def install():
    if getattr(T, "_h_adapter", False):
        return
    assert not getattr(T, "_g_adapter", False), "the G-0 adapter is installed in this process"
    # 1 vocabulary
    assert T.VOCAB == HT.VOCAB[:len(T.VOCAB)]
    T.VOCAB = list(HT.VOCAB)
    T.TOK.update({s: HT.TOK[s] for s in HT.OPS + [HT.BOS]})
    # 2 tasks
    T.TASKS = tuple(T.TASKS) + tuple(t for t in HT.SUITE if t not in T.TASKS)
    T.SPEC.update({t: HT.SPEC[t] for t in HT.SUITE})
    stage1_draw = T.draw

    def draw(task, rng, lo, hi, train_dist=False):
        if task in HT.SUITE:
            return h_draw(task, rng, lo, hi, train_dist=train_dist)
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
    T._h_adapter = True


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
