"""L2b-0 baseline tasks (stage3/DESIGN.md 11.3, 11.5-3, 11.7, 11.10-2): multi_add and mulNM as stage-1 style tasks,
data generators only.  Vocabulary: stage2/g_tasks (the G-0 vocabulary: '+', '*', '=' exist; stage-1 ids unchanged).
Generation seeds as stage 1 ("train:<task>:<seed>", "eval:<task>:id", "eval:<task>:<lo>-<hi>").

Formats (prompt -> answer, then <eos>; numbers least significant digit first, canonical = no leading zero):
  multi_add  a_1 + a_2 + ... + a_k =   ->  sum           mulNM  A * B =  ->  A x B
Draw (the R draw, stage3/recomb.composite_example): mulNM n, m independent uniform in the bin; multi_add k uniform in
the bin's k range and every operand's digit count independent uniform in the bin.  Bin coordinate = the digit range.
Bins (11.5-3, + mulNM 51-100 of 11.7 / 11.10-1):
  mulNM      training / in-distribution 1-10; out of distribution 11-20, 21-30, 31-50, 51-100
  multi_add  training / in-distribution (k 2-5, 1-10); out of distribution (k 6-10, 11-20), (k 11-20, 21-30),
             (k 21-40, 31-50)
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "stage2"))
sys.path.insert(0, os.path.join(HERE, "..", "stage1"))
import g_tasks as G         # noqa: E402

VOCAB, TOK = G.VOCAB, G.TOK
SUITE = ("multi_add", "mulNM")
SPEC = {"mulNM": {"train": (1, 10), "id": (1, 10), "ood": [(11, 20), (21, 30), (31, 50), (51, 100)]},
        "multi_add": {"train": (1, 10), "id": (1, 10), "ood": [(11, 20), (21, 30), (31, 50)]}}
K_RANGE = {(1, 10): (2, 5), (11, 20): (6, 10), (21, 30): (11, 20), (31, 50): (21, 40)}


def _num(rng, ndig):
    return rng.randrange(10) if ndig == 1 else rng.randrange(10 ** (ndig - 1), 10 ** ndig)


def _seq(v):
    return list(str(v)[::-1])


def draw(task, rng, lo, hi, train_dist=False):
    """one example (prompt, answer, bin coordinate hi); the same draw as stage3/recomb.composite_example"""
    if task == "mulNM":
        a, b = _num(rng, rng.randint(lo, hi)), _num(rng, rng.randint(lo, hi))
        return _seq(a) + ["*"] + _seq(b) + ["="], _seq(a * b), hi
    nums = [_num(rng, rng.randint(lo, hi)) for _ in range(rng.randint(*K_RANGE[(lo, hi)]))]
    p = []
    for j, v in enumerate(nums):
        p += (["+"] if j else []) + _seq(v)
    return p + ["="], _seq(sum(nums)), hi
