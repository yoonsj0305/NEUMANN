"""DEVELOPMENT ONLY, OFFLINE (section 42): do closed predictive coordinates (test outcomes whose transitions are a
function of (outcome, element)) exist for the HRT tasks, with unlimited oracle data?  Developer-side, nothing counted.

  python research/q3/psi42_psr_offline_dev.py <names.json>
"""
import sys, json, random, itertools
sys.path.insert(0,'.'); sys.path.insert(0,'research/q3')
import env_listroutines as E, psi42_hrt_family as HR
from neumann1.stateid import residual
from psi42_controlled_dev import registers
rng = random.Random(3)
res_all = {"closed_1": 0, "closed_2": 0, "none": 0}
for name in json.load(open(sys.argv[1])):
    spec = HR.parse(name)
    run = lambda x: spec.run(list(x))
    pre = list({tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 6))) for _ in range(250)})
    tests = [(v,) for v in range(0, 17, 2)] + [(a, b) for a in (0, 8, 16) for b in (1, 9)]
    coord = {w: {u: residual(run(u), run(u + w)) for u in pre} for w in tests}
    def closed(ws):
        seen = {}
        for u in pre:
            for e in range(17):
                v = u + (e,)
                cu = tuple(coord[w][u] for w in ws)
                cv = tuple(residual(run(v), run(v + w)) for w in ws)
                if seen.setdefault((cu, e), cv) != cv:
                    return False
        return True
    def informative(ws):
        return len({tuple(coord[w][u] for w in ws) for u in pre}) >= 3
    c1 = [w for w in tests if informative([w]) and closed([w])]
    c2 = [] if c1 else [p for p in itertools.combinations(tests, 2) if informative(list(p)) and closed(list(p))][:1]
    # does the closed coordinate separate every pair of distinct registers? (sufficiency of the coordinate)
    k = "closed_1" if c1 else ("closed_2" if c2 else "none")
    res_all[k] += 1
    print(name.ljust(28), k, (c1[:2] or c2[:1]))
print(res_all)
