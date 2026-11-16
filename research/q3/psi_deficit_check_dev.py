"""DEVELOPMENT ONLY (Phase 1 of section 39): is the failure of a positions task a representation deficit?

Developer-side diagnosis with an unlimited oracle (NOT an agent run, no result is counted): from the reachable
transitions of the 8 initial examples, (answer(u), x) -> answer(u.x), fit a list Update with the existing R2 cell
construction (synth_cells), once on the answer state alone and once with the latent h = len(u) (h' = h + 1 from 0);
a fitted Update is folded over 200 fresh random inputs.

  python research/q3/psi_deficit_check_dev.py "prepend-k(k=10) | positions"
"""
import sys, json, time
sys.path.insert(0, '.'); sys.path.insert(0, 'research/q3')
import env_listroutines as E
from neumann1 import active as ac
name = sys.argv[1]
spec = {s.name: s for s in E.tasks()}[name]
ac._inv()
env = E.Env(spec, 0, budget=10**9)
ex = env.initial()
f = lambda u: env.query(tuple(u))
rows_n, rows_l = [], []
for (x,), y in ex:
    for i in range(len(x)):
        u, v = x[:i], x[:i+1]
        a, b = f(u), f(v)
        if a is None or b is None: continue
        rows_n.append(((a, x[i]), b))
        rows_l.append(((a, i, x[i]), b))            # latent h = len(u), computed by the fold h' = h + 1 from 0
def fit(in_t, rows, cap):
    t0 = time.process_time(); g, ast = ac.synth_cells(in_t, rows, t0 + cap); return g, ast, round(time.process_time() - t0, 2)
conf = {}
for (a, e), b in rows_n: conf.setdefault((a, e), set()).add(b)
print("transitions", len(rows_n), "conflicting (state,e) without latent", sum(len(v) > 1 for v in conf.values()))
for cap in (5, 20):
    g, ast, c = fit(("L", "I"), rows_n, cap); print("no latent cap", cap, "fit", g is not None, c)
    g, ast, c = fit(("L", "I", "I"), rows_l, cap); print("latent len cap", cap, "fit", g is not None, c, ast[1] if ast else None)
    if g:
        import random
        rng = random.Random(5); ok = tot = 0
        for _ in range(200):
            x = tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 9)))
            y = f(x)
            if y is None: continue
            st, h = f(()), 0
            for e in x:
                st = g((st, h, e)); h += 1
                if st is None: break
            tot += 1; ok += st == y
        print("   fresh fold", ok, "/", tot); break
