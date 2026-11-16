"""DEVELOPMENT ONLY (section 40): a third problem family -- random hidden automata (RHA).

Written and frozen BEFORE any agent run on it; never used in development.  Developer-authored (disclosed), with
structures chosen to differ from the section 39 transducers (and some outside PSI40's one-guard automaton class):

* k in {2, 3, 4} hidden states, start 0;
* the element x (0..16) is mapped to a class by ONE or TWO predicates from templates unlike the section 39 ones:
  x < t;  x odd;  (x mod m) < r;  x in {a, b}  (two predicates give up to four classes);
* a uniformly random transition table delta(s, class), redrawn until every state is reachable from 0 and every two
  states are distinguishable by the outputs;
* output per element, appended to the answer: keep x when the new state is in a random proper subset S of the states;
  x when the new state is 0, otherwise -1;  or x + (new state).
The agent sees the usual Env interface only (8 initial examples, 10 hidden tests, charged queries).  Names encode
every parameter so that a task can be rebuilt and hashed.
"""
from __future__ import annotations
import random
import sys

sys.path.insert(0, "research/q3")
import env_listroutines as E


def _pred(p):
    kind = p[0]
    if kind == "lt":
        return lambda x: x < p[1]
    if kind == "odd":
        return lambda x: x % 2 == 1
    if kind == "modlt":
        return lambda x: x % p[1] < p[2]
    return lambda x: x in (p[1], p[2])


def _pshow(p):
    return p[0] + "".join("_%d" % v for v in p[1:])


def _pparse(s):
    parts = s.split("_")
    return tuple([parts[0]] + [int(v) for v in parts[1:]])


class RHASpec:
    def __init__(self, k, preds, delta, out):
        self.k, self.preds, self.delta, self.out = k, list(preds), dict(delta), out
        self.parts = [("rha", {})]
        self._p = [_pred(p) for p in self.preds]
        self.ncls = 2 ** len(self.preds)

    def cls(self, x):
        c = 0
        for f in self._p:
            c = 2 * c + int(bool(f(x)))
        return c

    @property
    def name(self):
        d = "".join(str(self.delta[(s, c)]) for s in range(self.k) for c in range(self.ncls))
        o = self.out[0] + ("_" + "".join(map(str, self.out[1])) if self.out[0] == "keepset" else "")
        return "rha(k=%d;p=%s;d=%s;o=%s)" % (self.k, "+".join(_pshow(p) for p in self.preds), d, o)

    def emit(self, s2, x):
        kind = self.out[0]
        if kind == "keepset":
            return [x] if s2 in self.out[1] else []
        if kind == "mark":
            return [x if s2 == 0 else -1]
        return [x + s2]

    def run(self, x):
        s, out = 0, []
        for v in x:
            if not isinstance(v, int):
                raise E.Invalid
            s = self.delta[(s, self.cls(v))]
            out += self.emit(s, v)
        if len(out) > 40:
            raise E.Invalid
        return tuple(out)

    def sample(self, rng):
        return tuple(rng.randrange(0, 17) for _ in range(rng.randrange(8)))


def parse(name):
    body = name[len("rha("):-1]
    kv = dict(p.split("=") for p in body.split(";"))
    k = int(kv["k"])
    preds = [_pparse(p) for p in kv["p"].split("+")]
    ncls = 2 ** len(preds)
    d = kv["d"]
    delta = {(s, c): int(d[s * ncls + c]) for s in range(k) for c in range(ncls)}
    o = kv["o"].split("_")
    out = ("keepset", tuple(int(ch) for ch in o[1])) if o[0] == "keepset" else (o[0],)
    return RHASpec(k, preds, delta, out)


def _well_formed(spec):
    reps = []
    for c in range(spec.ncls):
        xs = [x for x in range(17) if spec.cls(x) == c]
        if not xs:
            return False
        reps.append(xs[len(xs) // 2])
    seen, todo = {0}, [0]
    while todo:
        s = todo.pop()
        for c in range(spec.ncls):
            t = spec.delta[(s, c)]
            if t not in seen:
                seen.add(t)
                todo.append(t)
    if len(seen) != spec.k:
        return False

    def outs(s, word):
        o = []
        for x in word:
            s = spec.delta[(s, spec.cls(x))]
            o.append(tuple(spec.emit(s, x)))
        return tuple(o)
    words = [()]
    for _ in range(4):
        words += [w + (x,) for w in words if len(w) == len(words[-1]) for x in reps]
    for a in range(spec.k):
        for b in range(a + 1, spec.k):
            if all(outs(a, w) == outs(b, w) for w in words):
                return False
    return True


def generate(seed, n):
    rng = random.Random(seed)
    out, seen = [], set()
    while len(out) < n:
        k = rng.choice((2, 3, 4))
        npred = 1 if rng.random() < 0.6 else 2
        preds = []
        for _ in range(npred):
            kind = rng.choice(("lt", "odd", "modlt", "in2"))
            if kind == "lt":
                preds.append(("lt", rng.randrange(3, 14)))
            elif kind == "odd":
                preds.append(("odd",))
            elif kind == "modlt":
                m = rng.choice((3, 4, 5))
                preds.append(("modlt", m, rng.randrange(1, m)))
            else:
                a, b = sorted(rng.sample(range(17), 2))
                preds.append(("in2", a, b))
        ncls = 2 ** npred
        delta = {(s, c): rng.randrange(k) for s in range(k) for c in range(ncls)}
        okind = rng.choice(("keepset", "mark", "plus"))
        if okind == "keepset":
            sub = tuple(sorted(rng.sample(range(k), rng.randrange(1, k))))
            o = ("keepset", sub)
        else:
            o = (okind,)
        spec = RHASpec(k, preds, delta, o)
        if spec.name in seen or not _well_formed(spec):
            continue
        seen.add(spec.name)
        out.append(spec)
    return out
