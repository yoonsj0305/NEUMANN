"""DEVELOPMENT ONLY: a second problem family for Predictive State Invention -- hidden finite-state transducers.

Developer-authored generator (disclosed; NOT an independent author's lineage).  A task reads an integer list
x_1..x_n (values 0..16, lengths 0..7, the list-routines input distribution) through a hidden automaton with k states:
    s_0 = 0;  s_i = T(s_{i-1}, P(x_i));  answer = [O(s_i, x_i) for i]  (or only the positions where O is defined)
P is a predicate on the element (x >= t, x mod m == 0, x == c), T a transition rule (count P-hits mod k, toggle on a
P-hit with reset on a miss, or saturate at k-1), O an output rule (x if s == 0 else 0; the state s; x + s; keep x only
when s == 0).  Nothing of this generator is visible to the agent: it sees the same Env interface (8 initial examples,
10 hidden tests, charged queries).  Task names encode every parameter so a task can be rebuilt and hashed.
"""
from __future__ import annotations
import random
import sys

sys.path.insert(0, "research/q3")
import env_listroutines as E

PREDS = {"geq": lambda t: (lambda x: x >= t), "mod": lambda m: (lambda x: x % m == 0), "eq": lambda c: (lambda x: x == c)}
TRANS = ("count", "toggle", "saturate")
OUTS = ("x_if_s0", "state", "x_plus_s", "keep_if_s0")


class FSTSpec:
    def __init__(self, k, pred, arg, trans, out):
        self.k, self.pred, self.arg, self.trans, self.out = k, pred, arg, trans, out
        self.parts = [("fst", {})]
        self._p = PREDS[pred](arg)

    @property
    def name(self):
        return "fst(k=%d,pred=%s%d,trans=%s,out=%s)" % (self.k, self.pred, self.arg, self.trans, self.out)

    def run(self, x):
        s, out = 0, []
        for v in x:
            if not isinstance(v, int):
                raise E.Invalid
            hit = self._p(v)
            if self.trans == "count":
                s = (s + 1) % self.k if hit else s
            elif self.trans == "toggle":
                s = (s + 1) % self.k if hit else 0
            else:
                s = min(self.k - 1, s + 1) if hit else s
            if self.out == "x_if_s0":
                out.append(v if s == 0 else 0)
            elif self.out == "state":
                out.append(s)
            elif self.out == "x_plus_s":
                out.append(v + s)
            elif s == 0:
                out.append(v)
        if len(out) > 40:
            raise E.Invalid
        return tuple(out)

    def sample(self, rng):
        n = rng.randrange(8)
        return tuple(rng.randrange(0, 17) for _ in range(n))


def parse(name):
    body = name[len("fst("):-1]
    kv = dict(p.split("=") for p in body.split(","))
    pred = next(p for p in PREDS if kv["pred"].startswith(p))
    return FSTSpec(int(kv["k"]), pred, int(kv["pred"][len(pred):]), kv["trans"], kv["out"])


def generate(seed, n):
    rng = random.Random(seed)
    out, seen = [], set()
    while len(out) < n:
        pred = rng.choice(sorted(PREDS))
        arg = {"geq": rng.randrange(3, 14), "mod": rng.randrange(2, 6), "eq": rng.randrange(0, 17)}[pred]
        s = FSTSpec(rng.choice((2, 3)), pred, arg, rng.choice(TRANS), rng.choice(OUTS))
        if s.name not in seen:
            seen.add(s.name)
            out.append(s)
    return out
