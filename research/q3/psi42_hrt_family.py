"""DEVELOPMENT ONLY (section 42): hidden register transducers (HRT) -- a computational structure that is NOT a small
finite-state machine.

Written before any agent run on it.  Developer-authored (disclosed).  A task reads an integer list x_1..x_n (values
0..16, lengths 0..7) through a hidden NUMERIC register h (start 0) and appends output after each element:
    h' = U(h, x)        U in: max(h, x); (h + x) mod m; x (the previous element); h + 1 if x > h else h;
                        min(B, h + x) (a saturating sum); x - h
    output O(h, h', x)  O in: h' + x;  x - h (the change against the old register);  x if x > h else nothing;
                        h' mod 5;  x if h' is even else nothing
Nothing of this generator is visible to the agent: the same Env interface (8 initial examples, 10 hidden tests,
charged queries).  Names encode every parameter so a task can be rebuilt and hashed.
"""
from __future__ import annotations
import random
import sys

sys.path.insert(0, "research/q3")
import env_listroutines as E

UPDATES = ("max", "summod", "prev", "countgt", "satsum", "diff")
OUTPUTS = ("plusx", "delta", "gtkeep", "mod5", "evenkeep")


class HRTSpec:
    def __init__(self, u, up, o):
        self.u, self.up, self.o = u, up, o
        self.parts = [("hrt", {})]

    @property
    def name(self):
        return "hrt(u=%s%s;o=%s)" % (self.u, self.up if self.up is not None else "", self.o)

    def step(self, h, x):
        if self.u == "max":
            return max(h, x)
        if self.u == "summod":
            return (h + x) % self.up
        if self.u == "prev":
            return x
        if self.u == "countgt":
            return h + 1 if x > h else h
        if self.u == "satsum":
            return min(self.up, h + x)
        return x - h

    def emit(self, h, h2, x):
        if self.o == "plusx":
            return [h2 + x]
        if self.o == "delta":
            return [x - h]
        if self.o == "gtkeep":
            return [x] if x > h else []
        if self.o == "mod5":
            return [h2 % 5]
        return [x] if h2 % 2 == 0 else []

    def run(self, x):
        h, out = 0, []
        for v in x:
            if not isinstance(v, int):
                raise E.Invalid
            h2 = self.step(h, v)
            out += self.emit(h, h2, v)
            h = h2
        if len(out) > 40:
            raise E.Invalid
        return tuple(out)

    def sample(self, rng):
        return tuple(rng.randrange(0, 17) for _ in range(rng.randrange(8)))


def parse(name):
    body = name[len("hrt("):-1]
    kv = dict(p.split("=") for p in body.split(";"))
    u = kv["u"]
    kind = next(k for k in sorted(UPDATES, key=len, reverse=True) if u.startswith(k))
    up = int(u[len(kind):]) if u[len(kind):] else None
    return HRTSpec(kind, up, kv["o"])


def generate(seed, n):
    rng = random.Random(seed)
    out, seen, tries = [], set(), 0
    while len(out) < n and tries < 10000:
        tries += 1
        u = rng.choice(UPDATES)
        up = rng.choice((5, 7, 10)) if u == "summod" else (rng.randrange(10, 25) if u == "satsum" else None)
        s = HRTSpec(u, up, rng.choice(OUTPUTS))
        if s.name not in seen:
            seen.add(s.name)
            out.append(s)
    return out
