"""3-0 tasks (stage3/DESIGN.md 5.1): data generators only.  Vocabulary and conventions: stage2/g_tasks.py (the G-0
vocabulary, stage-1 ids unchanged); generation seeds as stage 1 ("train:<task>:<seed>", "eval:<task>:id",
"eval:<task>:<lo>-<hi>", "select:<task>").  No new token.

Formats (prompt -> answer, then <eos>; digits i.i.d. uniform 0-9):
  dup         s_0 .. s_{n-1} =              ->  s_0 s_0 s_1 s_1 .. s_{n-1} s_{n-1}
  interleave  a_0 .. a_{n-1} + b_0 .. b_{n-1} =  ->  a_0 b_0 a_1 b_1 .. a_{n-1} b_{n-1}      (|a| = |b| = n)
  repeat      s_0 .. s_{n-1} =              ->  s_0 .. s_{n-1} s_0 .. s_{n-1}
  pairswap    s_0 .. s_{n-1} =              ->  s_1 s_0 s_3 s_2 .. s_{n-1} s_{n-2}    (n even)
Length n (the bin coordinate): uniform in the range (G-0 one-operand rule); training 1-10, in-distribution 1-10,
out-of-distribution 11-20 / 21-30 / 31-40.  pairswap: n uniform over the EVEN numbers of the range; training and
in-distribution 2-10, out-of-distribution 12-20 / 22-30 / 32-40 (5.1).
MQAR (record only) is the stage-1 task (stage1/tasks.py mqar), unchanged.
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "stage2"))
sys.path.insert(0, os.path.join(HERE, "..", "stage1"))
import g_tasks as G         # noqa: E402

VOCAB, TOK = G.VOCAB, G.TOK
SUITE = ("dup", "interleave", "repeat", "pairswap")                     # the four verdict tasks (5.1)
DIGIT_SPEC = {"train": (1, 10), "id": (1, 10), "ood": [(11, 20), (21, 30), (31, 40)]}
EVEN_SPEC = {"train": (2, 10), "id": (2, 10), "ood": [(12, 20), (22, 30), (32, 40)]}
SPEC = {"dup": DIGIT_SPEC, "interleave": DIGIT_SPEC, "repeat": DIGIT_SPEC, "pairswap": EVEN_SPEC}


def _digits(n, rng):
    return [str(rng.randrange(10)) for _ in range(n)]


def dup(n, rng):
    s = _digits(n, rng)
    return s + ["="], [c for c in s for _ in range(2)]


def interleave(n, rng):
    a, b = _digits(n, rng), _digits(n, rng)
    return a + ["+"] + b + ["="], [c for pair in zip(a, b) for c in pair]


def repeat(n, rng):
    s = _digits(n, rng)
    return s + ["="], s + s


def pairswap(n, rng):
    assert n % 2 == 0
    s = _digits(n, rng)
    return s + ["="], [s[i ^ 1] for i in range(n)]


GEN = {"dup": dup, "interleave": interleave, "repeat": repeat, "pairswap": pairswap}


def draw(task, rng, lo, hi, train_dist=False):
    """one example (prompt, answer, n); the same single rng.randint draw as g_tasks.draw (pairswap: over the even
    numbers lo..hi)"""
    if task == "pairswap":
        assert lo % 2 == 0 and hi % 2 == 0
        n = 2 * rng.randint(lo // 2, hi // 2)
    else:
        n = rng.randint(lo, hi)
    p, a = GEN[task](n, rng)
    return p, a, n
