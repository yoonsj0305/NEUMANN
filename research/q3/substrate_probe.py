"""Which standard list/integer constructors have a definition within reach of the definition language?

Analysis only (no mechanism, no task data): every operation below is specified by self-generated examples and
handed to the same synthesiser iteration 3 uses for gap specifications (substrate + `len`, arguments only),
with a much larger CPU cap.  A found definition is re-checked on fresh self-generated arguments.

python research/q3/substrate_probe.py <cap_s> <out.json>
"""
from __future__ import annotations
import json, random, sys, time
sys.path.insert(0, ".")
from multiprocessing import Pool
from neumann1 import invention_core as ic, spec_core as sc, opgen

L, I = "L", "I"


def _inter(a, b):
    return tuple(v for p in zip(a, b) for v in p)


OPS = {   # name: (argument types, result type, function, argument sampler)
    "append": ((L, L), L, lambda a, b: a + b, None),
    "reverse": ((L,), L, lambda a: a[::-1], None),
    "last": ((L,), I, lambda a: a[-1] if a else None, None),
    "snoc": ((L, I), L, lambda a, v: a + (v,), None),
    "count": ((L, I), I, lambda a, v: a.count(v), None),
    "sum": ((L,), I, lambda a: sum(a), None),
    "maximum": ((L,), I, lambda a: max(a) if a else None, None),
    "nth": ((L, I), I, lambda a, k: a[k] if 0 <= k < len(a) else None, "idx"),
    "drop": ((L, I), L, lambda a, k: a[k:] if 0 <= k <= len(a) else None, "idx"),
    "take": ((L, I), L, lambda a, k: a[:k] if 0 <= k <= len(a) else None, "idx"),
    "init": ((L,), L, lambda a: a[:-1] if a else None, None),
    "rotate": ((L, I), L, lambda a, k: a[k:] + a[:k] if 0 <= k <= len(a) else None, "idx"),
    "replace_at": ((L, I, I), L, lambda a, k, v: a[:k] + (v,) + a[k + 1:] if 0 <= k < len(a) else None, "idx"),
    "insert_at": ((L, I, I), L, lambda a, k, v: a[:k] + (v,) + a[k:] if 0 <= k <= len(a) else None, "idx"),
    "interleave": ((L, L), L, _inter, "same"),
    "zip_add": ((L, L), L, lambda a, b: tuple(x + y for x, y in zip(a, b)), "same"),
    "gather": ((L, L), L, lambda a, ix: tuple(a[i] for i in ix), "perm"),
    "repeat": ((L, I), L, lambda a, k: a * k if 0 <= k <= 4 else None, "small"),
    "sort": ((L,), L, lambda a: tuple(sorted(a)), None),
    "unique": ((L,), L, lambda a: tuple(dict.fromkeys(a)), None),
}


def examples(name, n, seed):
    ats, ret, f, mode = OPS[name]
    rng = random.Random("%s:%d" % (name, seed))
    out = []
    while len(out) < n:
        a = tuple(rng.randint(0, 9) for _ in range(rng.randint(2, 7)))
        args = [a]
        for t in ats[1:]:
            if t == L:
                args.append(tuple(rng.sample(range(len(a)), len(a))) if mode == "perm" else
                            tuple(rng.randint(0, 9) for _ in range(len(a) if mode == "same" else rng.randint(1, 5))))
            else:
                args.append(rng.randint(0, len(a) - 1) if mode == "idx" and len(args) == 1 else
                            rng.randint(0, 3) if mode == "small" else rng.randint(0, 9))
        y = f(*args)
        if y is not None:
            out.append((tuple(args), y))
    return out


def job(a):
    name, cap = a
    ats, ret, _, _ = OPS[name]
    lib = ic.library_from_spec(opgen.seed_spec())
    t0 = time.process_time()
    s = sc.GSearch(lib, ats, ret, examples(name, 10, 0), t0 + cap, consts=())
    r, _ = s.run()
    row = {"operation": name, "type": "(%s) -> %s" % (", ".join(ats), ret), "found": r is not None,
           "candidates": s.n, "cpu_seconds": round(time.process_time() - t0, 2),
           "cost_levels_completed": len(s.levels)}
    if r is not None:
        row["definition"] = ic.show(r[1])
        row["size"] = ic.size(r[1])
        row["holds_on_fresh_arguments"] = all(ic.run_program(r[1], lib, i) == o for i, o in examples(name, 40, 1))
    return row


def main(cap, out):
    with Pool(4) as p:
        rows = p.map(job, [(n, float(cap)) for n in OPS], chunksize=1)
    json.dump({"schema": "neumann.substrate-probe.v1", "cap_cpu_seconds": float(cap),
               "vocabulary": "substrate + len", "rows": rows}, open(out, "w"), indent=1)
    for r in rows:
        print("%-11s %-16s %s %s" % (r["operation"], r["type"],
              ("size %d, %.1fs, fresh %s: %s" % (r["size"], r["cpu_seconds"], r["holds_on_fresh_arguments"], r["definition"]))
              if r["found"] else "NOT FOUND in %.0fs (%d candidates, %d levels)" % (r["cpu_seconds"], r["candidates"], r["cost_levels_completed"]), ""))


if __name__ == "__main__":
    main(*sys.argv[1:3])
