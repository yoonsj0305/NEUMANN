"""Iteration 4, step 1 (analysis only): are the 12 constructors iteration 3 did not define EXPRESSIBLE in the
definition language (substrate + `len`), and at what cost level?

The witness programs below were written by the developer as a measuring device.  They are never imported by
any solver, never given to the system, and are not evidence of invention.  A witness that reproduces the
operation on 40 fresh self-generated arguments proves expressibility; its size is its cost level under the
uniform order the synthesiser uses.  The number of candidates needed to reach that level is extrapolated from
the per-level counts the synthesiser itself reports.

python research/q3/op_witnesses.py <out.json>
"""
from __future__ import annotations
import json, sys, time
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import invention_core as ic, spec_core as sc, opgen
import substrate_probe as sp

V = lambda i: ("v", i)
K = lambda c: ("k", c)


def rev(x):                     # reverse a list expression x; binders at the current depth d are passed in
    return lambda d: ("foldlL", ("cons", V(d), V(d + 1)), ("nil",), x(d))


def drop(n, x):                 # drop n elements: tail applied n times
    return lambda d: ("foldrL", ("tail", V(d + 1)), x(d), ("range", n(d)))


def take(n, x):                 # reverse(drop(len x - n, reverse x))
    return lambda d: rev(drop(lambda e: ("sub", ("len", x(e)), n(e)), rev(x)))(d)


def app(x, y):
    return lambda d: ("foldrL", ("cons", V(d), V(d + 1)), y(d), x(d))


def nth(x, i):
    return lambda d: ("head", drop(i, x)(d))


a, b, c = (lambda d: V(0)), (lambda d: V(1)), (lambda d: V(2))
WITNESS = {
    # name: (program builder at depth = number of arguments)
    "take": lambda d: take(b, a)(d),
    "init": lambda d: rev(lambda e: ("tail", rev(a)(e)))(d),
    "rotate": lambda d: app(drop(b, a), take(b, a))(d),
    "replace_at": lambda d: app(take(b, a), lambda e: ("cons", V(2), drop(lambda f: ("add", V(1), K(1)), a)(e)))(d),
    "insert_at": lambda d: app(take(b, a), lambda e: ("cons", V(2), drop(b, a)(e)))(d),
    # binder of the outer fold over range(len a): index i = $d, accumulator = $d+1
    "interleave": lambda d: ("foldrL", ("cons", nth(a, lambda e: V(d))(d + 2),
                                        ("cons", nth(b, lambda e: V(d))(d + 2), V(d + 1))),
                             ("nil",), ("range", ("len", V(0)))),
    "zip_add": lambda d: ("map", ("add", nth(a, lambda e: V(d))(d + 1), nth(b, lambda e: V(d))(d + 1)),
                          ("range", ("len", V(0)))),
    "gather": lambda d: ("map", nth(a, lambda e: V(d))(d + 1), V(1)),
    "repeat": lambda d: ("foldrL", app(a, lambda e: V(d + 1))(d + 2), ("nil",), ("range", V(1))),
    "maximum": lambda d: ("foldlI", ("ifI", ("lt", V(d + 1), V(d)), V(d), V(d + 1)), ("head", V(0)), V(0)),
    # insertion sort: insert element e (= $d) into the sorted accumulator s (= $d+1)
    "sort": lambda d: ("foldrL", app(lambda e: ("filter", ("lt", V(e), V(d)), V(d + 1)),
                                     lambda e: ("cons", V(d), ("filter", ("not", ("lt", V(e), V(d))), V(d + 1))))(d + 2),
                       ("nil",), V(0)),
    "unique": lambda d: rev(lambda e: ("foldlL", ("ifL", ("isnil", ("filter", ("eq", V(e), V(e + 2)), V(e + 1))),
                                                         ("cons", V(e), V(e + 1)), V(e + 1)), ("nil",), V(0)))(d),
}


def growth(lib):
    """Candidates per completed cost level, as the synthesiser reports them on an operation it cannot define."""
    ats, ret = sp.OPS["interleave"][0], sp.OPS["interleave"][1]
    s = sc.GSearch(lib, ats, ret, sp.examples("interleave", 10, 0), time.process_time() + 60, consts=())
    s.run()
    return s.levels


def main(out):
    lib = ic.library_from_spec(opgen.seed_spec())
    lv = growth(lib)
    steps = [lv[i] / lv[i - 1] for i in range(len(lv) - 3, len(lv)) if lv[i - 1]]
    g = sum(steps) / len(steps)
    rows = []
    for name, build in WITNESS.items():
        ats = sp.OPS[name][0]
        ast = build(len(ats))
        ok = all(ic.run_program(ast, lib, i) == o for i, o in sp.examples(name, 40, 1))
        size = ic.size(ast)
        est = lv[-1] * g ** (size - len(lv)) if size > len(lv) else None
        rows.append({"operation": name, "type": sp.OPS[name][0], "witness": ic.show(ast), "witness_holds": ok,
                     "cost_level": size, "levels_completed_in_60s": len(lv),
                     "estimated_candidates_to_reach": est,
                     "estimated_cpu_seconds_at_measured_rate": est / (lv[-1] / 60.0) if est else None})
    rec = {"schema": "neumann.op-witnesses.v1", "levels": lv, "growth_per_level": round(g, 2), "rows": rows,
           "note": "developer-written witnesses; analysis only; never given to any solver"}
    json.dump(rec, open(out, "w"), indent=1)
    print("candidates at completed levels", lv, "growth %.2f/level" % g)
    for r in rows:
        print("%-10s holds %s  level %2d  est. candidates %.1e  est. CPU %.1e s   %s" % (
            r["operation"], r["witness_holds"], r["cost_level"], r["estimated_candidates_to_reach"] or 0,
            r["estimated_cpu_seconds_at_measured_rate"] or 0, r["witness"][:80]))


if __name__ == "__main__":
    main(sys.argv[1])
