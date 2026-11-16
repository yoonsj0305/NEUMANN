"""DEVELOPMENT ONLY (section 43): offline check of joint latent invention (neumann1/joint.py) on HRT tasks.

The true register is NEVER given.  Data, per mode:
  examples  -- the 8 given input/output examples only (whole-output constraints; no SOURCE query)
  steps     -- per-step answers along the 8 examples' prefixes (what observed trajectories provide)
A found machine is folded over 200 fresh random inputs against the generator (developer-side truth).

  python research/q3/psi43_joint_offline_dev.py <names.json> <examples|steps> <cpu per task> [cpu per size]
"""
from __future__ import annotations
import json
import random
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
import psi42_hrt_family as HR
from neumann1 import joint as J
from neumann1.stateid import residual


def main(path, mode, budget, size_timeout):
    exact = 0
    names = json.load(open(path))
    for name in names:
        spec = HR.parse(name)
        env = E.Env(spec, 0, budget=10 ** 9)
        t0 = time.process_time()
        if mode == "examples":
            sol, info = J.synthesise_by_size([(x, y) for (x,), y in env.initial()], t0 + budget,
                                             size_timeout=size_timeout)
        else:
            steps = []
            for (x,), _ in env.initial():
                for i in range(len(x)):
                    p = residual(spec.run(list(x[:i])), spec.run(list(x[:i + 1])))
                    if p is not None:
                        steps.append((tuple(x[:i]), x[i], p))
            sol, info = J.synthesise_steps_by_size(steps, t0 + budget, size_timeout=size_timeout)
        row = {"task": name, "mode": mode, "cpu": round(time.process_time() - t0, 1), "sizes": info.get("sizes")}
        if sol is not None:
            rng = random.Random(5)
            ok = tot = 0
            for _ in range(200):
                xx = tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 8)))
                tot += 1
                ok += J._safe_run(sol, xx) == spec.run(list(xx))
            exact += ok == tot
            row.update({"solution": sol["show"], "fresh": [ok, tot]})
        print(json.dumps(row), flush=True)
    print(json.dumps({"exact": exact, "tasks": len(names)}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else 4.0)
