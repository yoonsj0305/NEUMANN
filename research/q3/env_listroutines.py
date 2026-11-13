"""Black-box SOURCE environment for active structural discovery (development only).

The routines are transcribed from lucasem/list-routines (commit 23c8f099dc981a7552d50471b2e097e5beea6e20,
Racket, written by an independent author for the DreamCoder list domain): `evaluate`, the input constraint and
the input generator of every list-input routine, with the authors' own example parameters.  Integer-input
routines (fibonacci, prime, prime-largest-less-than, range) are excluded: a query on an integer IS an answer.

Nothing in `neumann1/` imports this module.  The agent sees an `Env` object that exposes only:
  initial()      the initial observation (8 input-output examples)
  query(x)       the output for a valid input x, charged against a per-task budget (invalid inputs and inputs
                 equal to a hidden test input are charged and return None)
The hidden test inputs, the routine, its parameters and its generator are never exposed.

A second tier composes two routines (outer(inner(x))) with a fixed seed: both parts are the independent
author's; the choice to compose is the developer's and is disclosed.
"""
from __future__ import annotations
import random

PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101,
          103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199)


class Invalid(Exception):
    pass


# --------------------------------------------------------------- generators (prelude.rkt)
def rlist(rng, n, lo=0, hi=17):
    return [rng.randrange(lo, hi) for _ in range(n)]


def with_occurrence(rng, n, where, update):
    cnt = 0 if n == 0 else 1 + rng.randrange(n)
    l = rlist(rng, n)
    for _ in range(200):
        c = sum(1 for x in l if where(x))
        if c == cnt:
            return l
        if c < cnt:
            l[rng.randrange(n)] = update()
        else:
            l[next(i for i, x in enumerate(l) if where(x))] = rng.randrange(0, 17)
    return l


def flip(rng, p=0.5):
    return rng.random() < p


# --------------------------------------------------------------- routines
def _sqrt_int(x):
    if x < 0:
        return False
    r = int(round(x ** 0.5))
    return r * r == x


def dedup(l):
    out = []
    for x in l:
        if not out or out[-1] != x:
            out.append(x)
    return out


R = {}   # id: (evaluate(l, p), min_len(p), generate(rng, p, n) or None, len_default(rng, p), example params)


def routine(rid, ev, params=({},), min_len=lambda p: 0, gen=None, len_default=None):
    R[rid] = (ev, min_len, gen, len_default or (lambda rng, p: rng.randrange(8)), list(params))


K = lambda p: p["k"]
occ_k = lambda rng, p, n: with_occurrence(rng, n, lambda x: x == p["k"], lambda: p["k"]) if flip(rng) else rlist(rng, n)
len1 = lambda rng, p: rng.randrange(1, 8)
lenk = lambda rng, p: rng.randrange(p["k"], p["k"] + 8)

routine("add-k", lambda l, p: [x + K(p) for x in l], [{"k": 1}, {"k": 2}, {"k": 3}, {"k": -2}, {"k": 10}])
routine("append-k", lambda l, p: l + [K(p)], [{"k": 2}, {"k": 3}, {"k": -2}, {"k": 10}])
routine("count-k", lambda l, p: sum(1 for x in l if x == K(p)), [{"k": 2}, {"k": 3}, {"k": 10}], gen=occ_k)
routine("dedup", lambda l, p: dedup(l))
routine("drop-k", lambda l, p: l[K(p):], [{"k": 2}, {"k": 3}, {"k": 5}], min_len=K, len_default=lenk)
routine("dup", lambda l, p: [y for x in l for y in (x, x)])
routine("empty", lambda l, p: not l, gen=lambda rng, p, n: [] if flip(rng, 0.2) else rlist(rng, n))
routine("has-k", lambda l, p: p["k"] in l, [{"k": 2}, {"k": 3}, {"k": 10}], gen=occ_k)
routine("head", lambda l, p: l[0], min_len=lambda p: 1, len_default=len1)
routine("identify-geq-k", lambda l, p: [1 if x >= K(p) else 0 for x in l], [{"k": 2}, {"k": 3}, {"k": 7}],
        gen=lambda rng, p, n: with_occurrence(rng, n, lambda x: x == p["_v"], lambda: p["_v"])
        if flip(rng) else rlist(rng, n))
routine("identify-is-mod-k", lambda l, p: [1 if x % K(p) == 0 else 0 for x in l], [{"k": 2}, {"k": 3}, {"k": 7}], gen=occ_k)
routine("identify-is-prime", lambda l, p: [1 if x in PRIMES else 0 for x in l])
routine("identify-k", lambda l, p: [1 if x == K(p) else 0 for x in l],
        [{"k": 1}, {"k": 2}, {"k": 3}, {"k": -2}, {"k": 10}], gen=occ_k)
routine("index-k", lambda l, p: l[K(p) - 1], [{"k": 2}, {"k": 3}], min_len=K, len_default=lenk)
routine("intersperse-k", lambda l, p: [y for x in l for y in (p["k"], x)][1:], [{"k": 1}, {"k": 10}, {"k": -2}, {"k": 0}])
routine("is-evens", lambda l, p: all(x % 2 == 0 for x in l),
        gen=lambda rng, p, n: [2 * x for x in rlist(rng, n)] if flip(rng) else rlist(rng, n))
routine("is-mod-k", lambda l, p: all(x % K(p) == 0 for x in l), [{"k": 2}, {"k": 3}, {"k": 5}],
        gen=lambda rng, p, n: [K(p) * x for x in rlist(rng, n)] if flip(rng) else rlist(rng, n))
routine("is-odds", lambda l, p: all(x % 2 == 1 for x in l),
        gen=lambda rng, p, n: [2 * x + 1 for x in rlist(rng, n)] if flip(rng) else rlist(rng, n))
routine("is-primes", lambda l, p: all(x in PRIMES for x in l),
        gen=lambda rng, p, n: rng.sample(PRIMES, n) if flip(rng) else rlist(rng, n))
routine("is-squares", lambda l, p: all(_sqrt_int(x) for x in l),
        gen=lambda rng, p, n: [x * x for x in rlist(rng, n)] if flip(rng) else rlist(rng, n))
_mult = lambda rng, p, n: with_occurrence(rng, n, lambda x: x % K(p) == 0, lambda: K(p) * rng.randrange(10)) \
    if flip(rng) and K(p) > 1 else rlist(rng, n)
routine("keep-mod-k", lambda l, p: [x for x in l if x % K(p) == 0], [{"k": 2}, {"k": 3}, {"k": 5}], gen=_mult)
routine("kth-largest", lambda l, p: sorted(l, reverse=True)[K(p) - 1], [{"k": 2}, {"k": 3}], min_len=K, len_default=lenk)
routine("kth-smallest", lambda l, p: sorted(l)[K(p) - 1], [{"k": 2}, {"k": 3}], min_len=K, len_default=lenk)
routine("last", lambda l, p: l[-1], min_len=lambda p: 1, len_default=len1)
routine("len", lambda l, p: len(l))
routine("max", lambda l, p: max(l), min_len=lambda p: 1, len_default=len1)
routine("min", lambda l, p: min(l), min_len=lambda p: 1, len_default=len1)
routine("modulo-k", lambda l, p: [x % K(p) for x in l], [{"k": 2}, {"k": 3}, {"k": 10}])
routine("mult-k", lambda l, p: [x * K(p) for x in l], [{"k": 2}, {"k": 3}, {"k": -2}, {"k": 10}])
routine("pop", lambda l, p: l[:-1], min_len=lambda p: 1, len_default=len1)
routine("positions", lambda l, p: [i for i, x in enumerate(l) if x != 0])
routine("pow-base-k", lambda l, p: [K(p) ** x for x in l], [{"k": 2}, {"k": 3}, {"k": 4}],
        gen=lambda rng, p, n: rlist(rng, n, 0, 12))
routine("pow-k", lambda l, p: [x ** K(p) for x in l], [{"k": 2}, {"k": 3}, {"k": 4}])
routine("prepend-k", lambda l, p: [K(p)] + l, [{"k": 2}, {"k": 3}, {"k": -2}, {"k": 10}])
routine("product", lambda l, p: __import__("math").prod(l), min_len=lambda p: 1, len_default=len1)
routine("remove-mod-k", lambda l, p: [x for x in l if x % K(p) != 0], [{"k": 2}, {"k": 3}, {"k": 5}], gen=_mult)
routine("repeat-k", lambda l, p: l * K(p), [{"k": 2}, {"k": 3}, {"k": 5}], len_default=lambda rng, p: rng.randrange(6))
routine("replace-all-k-with-n", lambda l, p: [p["n"] if x == K(p) else x for x in l],
        [{"k": 1, "n": 2}, {"k": 2, "n": 10}, {"k": 3, "n": -2}, {"k": 5, "n": 0}], gen=occ_k)
routine("replace-index-k-with-n", lambda l, p: l[:K(p) - 1] + [p["n"]] + l[K(p):],
        [{"k": 1, "n": 2}, {"k": 2, "n": 10}, {"k": 3, "n": -2}, {"k": 5, "n": 0}], min_len=K, len_default=lenk)
routine("reverse", lambda l, p: l[::-1])
routine("rotate-k", lambda l, p: (l[(-K(p)) % len(l):] + l[:(-K(p)) % len(l)]) if l else [],
        [{"k": 1}, {"k": 3}, {"k": -2}, {"k": 10}])
routine("slice-k-n", lambda l, p: l[K(p) - 1:K(p) - 1 + p["n"]],
        [{"k": 2, "n": 2}, {"k": 2, "n": 3}, {"k": 3, "n": 3}, {"k": 3, "n": 4}],
        min_len=lambda p: p["k"] + p["n"] + 1, len_default=lambda rng, p: rng.randrange(p["k"] + p["n"] + 1, p["k"] + p["n"] + 9))
routine("sort", lambda l, p: sorted(l))
routine("sum", lambda l, p: sum(l))
routine("tail", lambda l, p: l[1:], min_len=lambda p: 1, len_default=len1)
routine("take-k", lambda l, p: l[:K(p)], [{"k": 2}, {"k": 3}, {"k": 5}], min_len=K, len_default=lenk)
routine("uniq", lambda l, p: list(dict.fromkeys(l)))


def _norm(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v
    return tuple(v)


class Spec:
    """A hidden task: one routine instance, or outer(inner(x))."""

    def __init__(self, parts):
        self.parts = parts                      # [(rid, params)] applied left to right

    @property
    def name(self):
        return " | ".join("%s%s" % (r, "(" + ",".join("%s=%s" % kv for kv in sorted(p.items()) if not kv[0].startswith("_")) + ")" if p else "")
                          for r, p in self.parts)

    def run(self, x):
        v = list(x)
        for i, (rid, p) in enumerate(self.parts):
            ev, min_len, _, _, _ = R[rid]
            if not isinstance(v, list) or len(v) < min_len(p):
                raise Invalid
            try:
                v = ev(v, p)
            except (IndexError, ValueError, ZeroDivisionError):
                raise Invalid
            if isinstance(v, bool) and i < len(self.parts) - 1:
                raise Invalid
            if isinstance(v, list) and (len(v) > 40 or any(abs(e) > 10 ** 12 for e in v)):
                raise Invalid
        return _norm(v)

    def sample(self, rng):
        rid, p = self.parts[0]
        _, min_len, gen, len_default, _ = R[rid]
        for _ in range(50):
            n = len_default(rng, p)
            if n < min_len(p):
                continue
            q = dict(p)
            if rid == "identify-geq-k":
                q["_v"] = rng.randrange(K(p), K(p) + 4) if flip(rng) else rng.randrange(K(p) - 4, K(p))
            x = gen(rng, q, n) if gen else rlist(rng, n)
            try:
                self.run(x)
                return tuple(x)
            except Invalid:
                continue
        raise Invalid


def tasks(seed=0, n_compose=120):
    out = []
    for rid in sorted(R):
        for p in R[rid][4]:
            out.append(Spec([(rid, p)]))
    rng = random.Random("compose:%d" % seed)
    singles = list(out)
    listy = [s for s in singles if isinstance(s.run(s.sample(random.Random(1))), tuple)]
    seen = set()
    while len(seen) < n_compose:
        a, b = rng.choice(listy), rng.choice(singles)
        s = Spec(a.parts + b.parts)
        if s.name in seen:
            continue
        try:
            s.sample(random.Random(2))
        except Invalid:
            continue
        seen.add(s.name)
        out.append(s)
    return out


class Env:
    """The only interface the agent gets.  Every query is charged; the budget is fixed per task."""

    def __init__(self, spec, seed, n_train=8, n_test=10, budget=8):
        rng = random.Random("%s:%d" % (spec.name, seed))
        xs = []
        for _ in range(400):
            if len(xs) == n_train + n_test:
                break
            x = spec.sample(rng)
            if x not in xs:
                xs.append(x)
        if len(xs) < n_train + n_test:
            raise Invalid
        self._spec, self._test = spec, xs[n_train:]
        self._train = [((x,), spec.run(x)) for x in xs[:n_train]]
        self.budget, self.used, self.log = budget, 0, []

    def initial(self):
        return list(self._train)

    def query(self, x):
        if self.used >= self.budget:
            return None
        self.used += 1
        x = tuple(x)
        if x in self._test:
            self.log.append((x, "blocked"))
            return None
        try:
            y = self._spec.run(list(x))
        except Invalid:
            self.log.append((x, "invalid"))
            return None
        self.log.append((x, y))
        return y

    # evaluation only (never given to the agent)
    def _score(self, predict):
        try:
            return all(predict((x,)) == self._spec.run(list(x)) for x in self._test)
        except Exception:
            return False
