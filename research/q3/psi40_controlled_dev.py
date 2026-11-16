"""DEVELOPMENT ONLY (section 40, P0-E controlled case 1): representation sufficiency with the TRUE hidden state given.

Developer-side oracle (not an agent run, nothing counted): for each hidden-transducer task of the section 39 set (now
development data), the true automaton state s is given as an executable latent, exposed before (s) and after (s')
reading the element, exactly as PSI40 exposes a constructed automaton.  The list Update z' = G(z, s, s', x) is fitted
with the unchanged R2 cell construction from the reachable transitions of the 8 initial examples, at several CPU
caps, and folded over 200 fresh random inputs.  It separates the representation defect (no Update even with the true
state) from the identification defect (the state was not found) and measures the CPU the synthesis needs.

  python research/q3/psi40_controlled_dev.py docs/experiments/dev/psi/eval_set.json [length floor, s]
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
import psi_fst_family as FF


def true_step(spec):
    def step(s, v):
        hit = spec._p(v)
        if spec.trans == "count":
            return (s + 1) % spec.k if hit else s
        if spec.trans == "toggle":
            return (s + 1) % spec.k if hit else 0
        return min(spec.k - 1, s + 1) if hit else s
    return step


def main(path, caps=(2.0, 5.0, 10.0, 20.0), floor=0.0):
    from neumann1 import latent
    latent.LENGTH_FLOOR = floor
    ac._inv()
    out = []
    for t in json.load(open(path))["fst16"]:
        spec = FF.parse(t["name"])
        env = E.Env(spec, 0, budget=10 ** 9)
        f = lambda u: env.query(tuple(u))
        st = true_step(spec)
        rows = []
        for (x,), _ in env.initial():
            s = 0
            for i in range(len(x)):
                u, v = x[:i], x[:i + 1]
                s2 = st(s, x[i])
                a, b = f(u), f(v)
                if a is not None and b is not None:
                    rows.append(((a, s, s2, x[i]), b))
                s = s2
        rows = list(dict.fromkeys(rows))
        res = {"task": t["name"], "transitions": len(rows)}
        for cap in caps:
            t0 = time.process_time()
            g, ast = ac.synth_cells((ac.T_L, ac.T_I, ac.T_I, ac.T_I), rows, t0 + cap)
            used = round(time.process_time() - t0, 2)
            ok = tot = 0
            if g is not None:
                rng = random.Random(5)
                for _ in range(200):
                    x = tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 9)))
                    z, s = spec.run([]), 0              # developer-side truth (the oracle blocks hidden-test inputs)
                    for v in x:
                        s2 = st(s, v)
                        z = g((z, s, s2, v))
                        s = s2
                        if z is None:
                            break
                    tot += 1
                    ok += z == spec.run(list(x))
            res["cap%g" % cap] = {"fit": g is not None, "cpu": used, "fresh": [ok, tot],
                                  "update": ast[1] if ast else None}
            if g is not None and ok == tot:
                break
        out.append(res)
        print(json.dumps(res), flush=True)
    print(json.dumps({"tasks": len(out), "fitted_exact": sum(any(v.get("fit") and v["fresh"][0] == v["fresh"][1]
                                                                   for k, v in r.items() if k.startswith("cap"))
                                                               for r in out)}))


if __name__ == "__main__":
    # argv: eval_set.json [LENGTH_FLOOR seconds]
    main(sys.argv[1], floor=float(sys.argv[2]) if len(sys.argv) > 2 else 0.0)
