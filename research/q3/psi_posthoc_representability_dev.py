"""DEVELOPMENT ONLY, POST-HOC (section 39): is the hidden state of each evaluation FST inside PSI's hypothesis space?

Run after the pre-registered evaluation; it changes nothing and no verdict depends on it.  Developer-side (uses the
generator's true state, never visible to the agent).  For every fst16 task and every latent candidate PSI considers
(neumann1.active.accumulators(), the same list for every task, from the starts PSI uses: 0, 1, below, above), fold the
candidate over random inputs and test whether the true automaton state s_i is a FUNCTION of the candidate value h_i
at every prefix (h refines s: an Update could then compute the output from (answer, h, x)).

  python research/q3/psi_posthoc_representability_dev.py docs/experiments/dev/psi/eval_set.json
"""
from __future__ import annotations
import json
import random
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from neumann1 import active as ac
import psi_fst_family as F


def states(spec, x):
    s, out = 0, []
    for v in x:
        hit = spec._p(v)
        if spec.trans == "count":
            s = (s + 1) % spec.k if hit else s
        elif spec.trans == "toggle":
            s = (s + 1) % spec.k if hit else 0
        else:
            s = min(spec.k - 1, s + 1) if hit else s
        out.append(s)
    return out


def main(path):
    ac._inv()
    cands = [c for c in ac.accumulators() if c["t"] == ac.T_I]
    rng = random.Random(11)
    inputs = [tuple(rng.randrange(0, 17) for _ in range(rng.randrange(1, 10))) for _ in range(300)]
    res = []
    for t in json.load(open(path))["fst16"]:
        spec = F.parse(t["name"])
        hits = []
        for c in cands:
            for z in (0, 1, -1, 17):
                f, ok = {}, True
                for x in inputs:
                    h = z
                    for v, s in zip(x, states(spec, x)):
                        h = ac._acc_step(c["fn"], h, v)
                        if h is None or f.setdefault(h, s) != s:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    hits.append((c["size"], c["show"], z))
        hits.sort()
        res.append({"task": t["name"], "capturing_candidates": len(hits), "smallest": hits[:3]})
        print(t["name"], len(hits), hits[:2], flush=True)
    print(json.dumps({"candidates_integer": len(cands), "tasks": res,
                      "fst_tasks_with_a_capturing_candidate": sum(r["capturing_candidates"] > 0 for r in res)},
                     indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
