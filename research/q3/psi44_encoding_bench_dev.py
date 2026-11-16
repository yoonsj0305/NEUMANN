"""DEVELOPMENT ONLY (section 44, P0-A): where does the joint SMT encoding spend its time?

Same task (hrt(u=diff;o=gtkeep)), same data (per-step answers along the 8 given examples' prefixes), same operator
range, same CPU cap per variant.  Variants of the section 43 encoding are switched one at a time; 'unknown' is recorded
as a failure to solve, never as impossibility.  A found machine is checked on 200 fresh inputs.

  python research/q3/psi44_encoding_bench_dev.py [cpu cap] [task]
"""
from __future__ import annotations
import json
import random
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import z3
import env_listroutines as E
import psi42_hrt_family as HR
from neumann1 import joint as J
from neumann1.stateid import residual


def data(name):
    spec = HR.parse(name)
    env = E.Env(spec, 0, budget=10 ** 9)
    steps = []
    for (x,), _ in env.initial():
        for i in range(len(x)):
            p = residual(spec.run(list(x[:i])), spec.run(list(x[:i + 1])))
            if p is not None:
                steps.append((tuple(x[:i]), x[i], p))
    return spec, list(dict.fromkeys(steps))


def run(variant, steps, cap, K):
    canon = variant in ("canon", "canon+nomod")
    ops = ("var0", "var1", "var2", "const", "add", "sub", "min", "max") if "nomod" in variant else None
    M = J.JointModel(2, 1, 2, canon=canon, ops_allowed=ops)
    M.solver.add(J._internal_count(M.U) + J._internal_count(M.V) + J._internal_count(M.C) <= K)
    M.solver.set("random_seed", 0)
    for st in steps:
        M.observe_step(*st)
    t0 = time.process_time()
    sol, status = M.solve(cap * 1000)
    return sol, status, round(time.process_time() - t0, 2)


def main(cap=30.0, name="hrt(u=diff;o=gtkeep)"):
    spec, steps = data(name)
    print("task", name, "steps", len(steps))
    for variant in ("section43", "nomod", "canon", "canon+nomod"):
        for K in (2,):
            sol, st, dt = run(variant, steps, cap, K)
            fresh = ""
            if sol:
                rng = random.Random(5)
                ok = sum(J._safe_run(sol, x) == spec.run(list(x)) for x in
                         [tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 8))) for _ in range(200)])
                fresh = "fresh %d/200 %s" % (ok, sol["show"])
            print(variant.ljust(12), "size<=%d" % K, st, dt, fresh, flush=True)




def factored(cap=30.0, names=("hrt(u=diff;o=gtkeep)",)):
    """the factored joint synthesis on the same data, operator range and cap"""
    for name in names:
        spec, steps = data(name)
        env = E.Env(spec, 0, budget=10 ** 9)
        exs = [(x, y) for (x,), y in env.initial()]
        t0 = time.process_time()
        found, info = J.factored_synthesis(steps, exs, t0 + cap)
        dt = round(time.process_time() - t0, 2)
        res = []
        for m in found:
            rng = random.Random(5)
            ok = sum(J.run_factored(m, x) == spec.run(list(x)) for x in
                     [tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 8))) for _ in range(200)])
            res.append((m["show"], ok))
        print(name.ljust(28), "factored", dt, "s", {k: v for k, v in info.items() if k != "regularities"},
              "machines", res, flush=True)


def first_time(cap=30.0, names=("hrt(u=diff;o=gtkeep)",), want=1):
    for name in names:
        spec, steps = data(name)
        env = E.Env(spec, 0, budget=10 ** 9)
        exs = [(x, y) for (x,), y in env.initial()]
        t0 = time.process_time()
        found, info = J.factored_synthesis(steps, exs, t0 + cap, want=want)
        dt = round(time.process_time() - t0, 2)
        res = []
        for m in found:
            rng = random.Random(5)
            ok = sum(J.run_factored(m, x) == spec.run(list(x)) for x in
                     [tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 8))) for _ in range(200)])
            res.append((m["show"], ok))
        print(name.ljust(28), "want=%d" % want, dt, "s", {k: v for k, v in info.items() if k != "regularities"},
              res, flush=True)


def semantics(n=3000, seed=3):
    """P0-A: do the section 43 bit-vector semantics agree with Python's (the environment's) on concrete values?
    Every integer operator of the joint core, both argument signs; mismatches split into in-range ones (a real
    encoding error) and overflow of the 8-bit range (values the bounded encoding cannot represent)."""
    import z3
    rng = random.Random(seed)
    res = {}
    for op in ("add", "sub", "min", "max", "mod"):
        inr = ovf = tot = 0
        for _ in range(n):
            a, b = rng.randrange(-128, 128), rng.randrange(-128, 128)
            d = rng.randrange(2, 11)
            A, B, D = z3.BitVecVal(a, J.BITS), z3.BitVecVal(b, J.BITS), z3.BitVecVal(d, J.BITS)
            if op == "add":
                sv, pv = A + B, a + b
            elif op == "sub":
                sv, pv = A - B, a - b
            elif op == "min":
                sv, pv = z3.If(A < B, A, B), min(a, b)
            elif op == "max":
                sv, pv = z3.If(A < B, B, A), max(a, b)
            else:
                r_ = z3.SRem(A, D)
                sv, pv = z3.If(r_ < 0, r_ + D, r_), a % d
            got = z3.simplify(sv).as_signed_long()
            tot += 1
            if got != pv:
                if -128 <= pv <= 127:
                    inr += 1
                else:
                    ovf += 1
        res[op] = {"checked": tot, "mismatch_in_range": inr, "mismatch_overflow": ovf}
    print(json.dumps(res))
    return res


if __name__ == "__main__":
    # P0-A: the four section 43 encoding variants, then the factored core, on the SAME data / operator range / cap
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 30.0, sys.argv[2] if len(sys.argv) > 2 else "hrt(u=diff;o=gtkeep)")
    first_time(float(sys.argv[1]) if len(sys.argv) > 1 else 30.0,
               (sys.argv[2] if len(sys.argv) > 2 else "hrt(u=diff;o=gtkeep)",), want=1)
