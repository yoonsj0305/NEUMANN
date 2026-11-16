"""DEVELOPMENT ONLY (section 42): controlled checks on hidden register transducers -- developer-side oracle, nothing
counted.

1. sufficiency: with the TRUE register exposed before (h) and after (h') the element, is the list Update
   z' = G(z, h, h', x) found by the unchanged R2 cell construction from the reachable transitions of the 8 initial
   examples, and is it exact on 200 fresh inputs?
2. representability in section 41's space: does any fold of the fixed universal list (neumann1.active.accumulators(),
   from the starts PSI uses) induce the same STATE PARTITION as the true register on 300 random prefixes (equal
   register value <=> equal fold value)?  If none does, the state lies outside the PSI41 hypothesis space.

  python research/q3/psi42_controlled_dev.py <names.json> [length floor]
"""
from __future__ import annotations
import json
import random
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import active as ac
import env_listroutines as E
import psi42_hrt_family as HR


def registers(spec, x):
    h, out = 0, []
    for v in x:
        h2 = spec.step(h, v)
        out.append((h, h2))
        h = h2
    return out


def same_partition(fvals, tvals):
    m1, m2 = {}, {}
    for a, b in zip(fvals, tvals):
        if a is None:
            return False
        if m1.setdefault(a, b) != b or m2.setdefault(b, a) != a:
            return False
    return True


def main(path, floor=1.5):
    from neumann1 import latent
    latent.LENGTH_FLOOR = floor
    ac._inv()
    accs = ac.accumulators()
    rng = random.Random(11)
    seqs = [tuple(rng.randrange(0, 17) for _ in range(rng.randrange(1, 8))) for _ in range(300)]
    for name in json.load(open(path)):
        spec = HR.parse(name)
        env = E.Env(spec, 0, budget=10 ** 9)
        f = lambda u: env.query(tuple(u))
        rows = []
        for (x,), _ in env.initial():
            for i, (h, h2) in enumerate(registers(spec, x)):
                a, b = f(x[:i]), f(x[:i + 1])
                if a is not None and b is not None:
                    rows.append(((a, h, h2, x[i]), b))
        rows = list(dict.fromkeys(rows))
        res = {"task": name, "transitions": len(rows)}
        t0 = time.process_time()
        g, ast = ac.synth_cells((ac.T_L, ac.T_I, ac.T_I, ac.T_I), rows, t0 + 5.0)
        ok = tot = 0
        if g is not None:
            r2 = random.Random(5)
            for _ in range(200):
                x = tuple(r2.randrange(0, 17) for _ in range(r2.randrange(0, 9)))
                z = spec.run([])
                for v, (h, h2) in zip(x, registers(spec, x)):
                    z = g((z, h, h2, v))
                    if z is None:
                        break
                tot += 1
                ok += z == spec.run(list(x))
        res["sufficiency"] = {"fit": g is not None, "cpu": round(time.process_time() - t0, 2), "fresh": [ok, tot],
                              "update": ast[1] if ast else None}
        truth = [registers(spec, s)[-1][1] for s in seqs]
        hit = []
        for c in accs:
            for z in ([0, 1, -1, 17] if c["t"] == ac.T_I else [()]):
                vals = []
                for s in seqs:
                    h = z
                    for v in s:
                        h = ac._acc_step(c["fn"], h, v)
                        if h is None:
                            break
                    vals.append(h)
                if same_partition(vals, truth):
                    hit.append((c["show"], z))
        res["in_universal_fold_list"] = hit[:3]
        print(json.dumps(res), flush=True)




if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1.5)
