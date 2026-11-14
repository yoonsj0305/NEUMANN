"""SELF-AUTHORED development family for the invention core (NOT evidence).

Written by the engine developer purely to debug the mechanism.  Nothing here
is an independent original; no result on it is a capability claim.
"""
from __future__ import annotations
import random


def _f(name, fn, out="L"):
    return name, fn, out


FUNCS = [
    _f("tail", lambda x: x[1:] if x else None),
    _f("drop2", lambda x: x[2:] if len(x) >= 2 else None),
    _f("cons5", lambda x: (5,) + x), _f("cons0", lambda x: (0,) + x),
    _f("app7", lambda x: x + (7,)), _f("app3", lambda x: x + (3,)),
    _f("rev", lambda x: x[::-1]),
    _f("inc", lambda x: tuple(v + 1 for v in x)),
    _f("add3", lambda x: tuple(v + 3 for v in x)),
    _f("dec", lambda x: tuple(v - 1 for v in x)),
    _f("dbl", lambda x: tuple(v * 2 for v in x)),
    _f("mul3", lambda x: tuple(v * 3 for v in x)),
    _f("sq", lambda x: tuple(v * v for v in x)),
    _f("mod2", lambda x: tuple(v % 2 for v in x)),
    _f("mod3", lambda x: tuple(v % 3 for v in x)),
    _f("zero", lambda x: tuple(0 for v in x)),
    _f("evens", lambda x: tuple(v for v in x if v % 2 == 0)),
    _f("odds", lambda x: tuple(v for v in x if v % 2 == 1)),
    _f("gt3", lambda x: tuple(v for v in x if v > 3)),
    _f("gt5", lambda x: tuple(v for v in x if v > 5)),
    _f("lt4", lambda x: tuple(v for v in x if v < 4)),
    _f("ne0", lambda x: tuple(v for v in x if v != 0)),
    _f("eq2", lambda x: tuple(v for v in x if v == 2)),
    _f("len", lambda x: len(x), "I"), _f("sum", lambda x: sum(x), "I"),
    _f("last", lambda x: x[-1] if x else None, "I"),
    _f("max", lambda x: max(x) if x else None, "I"),
    _f("cnt_gt3", lambda x: sum(v > 3 for v in x), "I"),
    _f("cnt_even", lambda x: sum(v % 2 == 0 for v in x), "I"),
    _f("last1", lambda x: x[-1:]), _f("init", lambda x: x[:-1] if x else None),
    _f("dup", lambda x: tuple(v for v in x for _ in (0, 1))),
    _f("head1", lambda x: x[:1]),
    _f("lenL", lambda x: (len(x),)), _f("sumL", lambda x: (sum(x),)),
    _f("rev_inc", lambda x: tuple(v + 1 for v in x[::-1])),
    _f("inc_evens", lambda x: tuple(v + 1 for v in x if v % 2 == 0)),
    _f("dbl_gt3", lambda x: tuple(v * 2 for v in x if v > 3)),
    _f("rev_tail", lambda x: x[1:][::-1] if x else None),
    _f("sum_evens", lambda x: sum(v for v in x if v % 2 == 0), "I"),
    _f("len_gt5", lambda x: len([v for v in x if v > 5]), "I"),
    _f("app_len", lambda x: x + (len(x),)),
    _f("cons_sum", lambda x: (sum(x),) + x),
    _f("rev_odds", lambda x: tuple(v for v in x[::-1] if v % 2 == 1)),
    _f("add2_rev", lambda x: tuple(v + 2 for v in x)[::-1]),
    _f("dec_ne0", lambda x: tuple(v - 1 for v in x if v != 0)),
    _f("sq_lt4", lambda x: tuple(v * v for v in x if v < 4)),
    _f("mul3_odds", lambda x: tuple(v * 3 for v in x if v % 2 == 1)),
    _f("nth2", lambda x: x[2] if len(x) > 2 else None, "I"),
    _f("nth3", lambda x: x[3] if len(x) > 3 else None, "I"),
    _f("nth1L", lambda x: x[1:2] if len(x) > 1 else None),
    _f("nth4L", lambda x: x[4:5] if len(x) > 4 else None),
    _f("take2", lambda x: x[:2] if len(x) >= 2 else None),
    _f("take3", lambda x: x[:3] if len(x) >= 3 else None),
    _f("take4", lambda x: x[:4] if len(x) >= 4 else None),
    _f("drop3", lambda x: x[3:] if len(x) >= 3 else None),
    _f("drop4", lambda x: x[4:] if len(x) >= 4 else None),
    _f("take_h", lambda x: x[1:1 + x[0]] if x and len(x) > x[0] else None),
    _f("drop_h", lambda x: x[1 + x[0]:] if x and len(x) > x[0] else None),
    _f("nth_h", lambda x: x[x[0]] if x and len(x) > x[0] else None, "I"),
    _f("cnt_h", lambda x: sum(v == x[0] for v in x) if x else None, "I"),
    _f("rm_h", lambda x: tuple(v for v in x if v != x[0]) if x else None),
    _f("gt_h", lambda x: tuple(v for v in x if v > x[0]) if x else None),
    _f("swap01", lambda x: (x[1], x[0]) + x[2:] if len(x) >= 2 else None),
    _f("rot1", lambda x: x[1:] + x[:1] if x else None),
    _f("app_h", lambda x: x + x[:1] if x else None),
    _f("app_last", lambda x: x + x[-1:] if x else None),
    _f("len_m1", lambda x: len(x) - 1 if x else None, "I"),
    _f("sum_m_h", lambda x: sum(x) - x[0] if x else None, "I"),
    _f("rev_take3", lambda x: x[:3][::-1] if len(x) >= 3 else None),
    _f("take2_rev", lambda x: x[::-1][:2] if len(x) >= 2 else None),
    _f("last2", lambda x: x[-2:] if len(x) >= 2 else None),
    _f("idx", lambda x: tuple(range(len(x)))),
    _f("add_idx", lambda x: tuple(v + i for i, v in enumerate(x))),
    _f("max_m_min", lambda x: max(x) - min(x) if x else None, "I"),
    _f("min", lambda x: min(x) if x else None, "I"),
    _f("cnt0", lambda x: sum(v == 0 for v in x), "I"),
    _f("rep3", lambda x: x * 3),
    _f("app_rev", lambda x: x + x[::-1]),
    _f("concat_tail", lambda x: x + x[1:] if x else None),
]
TARGET = {"rev_inc", "inc_evens", "dbl_gt3", "rev_tail", "sum_evens",
          "len_gt5", "app_len", "cons_sum", "rev_odds", "add2_rev",
          "dec_ne0", "sq_lt4", "mul3_odds", "add3", "mul3", "gt5", "lt4",
          "cnt_even", "mod3", "app3", "nth3", "nth4L", "take4", "drop4",
          "nth_h", "gt_h", "app_last", "sum_m_h", "take2_rev", "last2",
          "max_m_min", "cnt0", "app_rev", "concat_tail", "rot1"}


def tasks(seed=7, n_train=8, n_test=8):
    out = []
    for i, (name, fn, ot) in enumerate(FUNCS):
        rng = random.Random(seed * 100 + i)
        ex = []
        while len(ex) < n_train + n_test:
            xs = tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 7)))
            y = fn(xs)
            if y is not None:
                ex.append(((xs,), y))
        out.append({"id": name, "in_types": ["L"], "out_type": ot,
                    "train": ex[:n_train], "test": ex[n_train:]})
    src = [t for t in out if t["id"] not in TARGET]
    tgt = [t for t in out if t["id"] in TARGET]
    return src, tgt
