"""DEVELOPMENT ONLY: pre-registered evaluation set for Predictive State Invention (section 39).

Built by fixed rules before any agent runs on these tasks:
* latent_need(spec): developer-side classification with the reference function (never visible to the agent):
  the answer-as-state W = [()] is insufficient in BOTH directions -- among 150 sampled prefixes (values from the
  task's own initial examples, seed 3) and 4 next elements each, two prefixes with the same answer and the same next
  element get different next answers.  A task property, decided before any agent run.
* list-routines (same lineage): new two-routine compositions with the tasks() rule and the seed string
  "compose:neumann-q3-psi-eval-v1", excluding every earlier name (the 228 tasks and the section 38 compositions):
    latent_need30  -- the first 30 latent-need compositions in generation order
    ordinary12     -- the first 12 compositions that are NOT latent-need (a regression check)
* fst16 -- the first 16 latent-need hidden finite-state transducers of research/q3/psi_fst_family.py with the seed
  "neumann-q3-psi-fst-v1" (a developer-authored second family).
Per task: name and sha256 of canonical {name, train, test} of Env(spec, 0).

  python research/q3/psi_eval_set_dev.py --out docs/experiments/dev/psi/eval_set.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import random
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
import psi_fst_family as FST

COMPOSE_SEED = "compose:neumann-q3-psi-eval-v1"
FST_SEED = "neumann-q3-psi-fst-v1"


def latent_need(spec, n=150, seed=3):
    env = E.Env(spec, 0, budget=10 ** 9)
    vals = sorted({v for (x,), _ in env.initial() for v in x}) or list(range(10))
    memo = {}

    def f(u):
        if u not in memo:
            memo[u] = env.query(u)
        return memo[u]
    res = {}
    for direction in ("prefix", "suffix"):
        rng = random.Random(seed)
        seen, hit = {}, False
        for _ in range(n):
            u = tuple(rng.choice(vals) for _ in range(rng.randrange(0, 7)))
            a = f(u)
            if a is None:
                continue
            for e in rng.sample(vals, min(4, len(vals))):
                v = u + (e,) if direction == "prefix" else (e,) + u
                b = f(v)
                if b is None:
                    continue
                if (a, e) in seen and seen[(a, e)] != b:
                    hit = True
                    break
                seen.setdefault((a, e), b)
            if hit:
                break
        res[direction] = hit
    return res["prefix"] and res["suffix"]


def task_hash(spec):
    env = E.Env(spec, 0, budget=60)
    data = {"name": spec.name, "train": [[list(x), list(y) if isinstance(y, tuple) else y] for (x,), y in env._train],
            "test": [list(x) for x in env._test]}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compositions():
    existing = E.tasks()
    used = {s.name for s in existing}
    used |= set(json.load(open("docs/experiments/dev/case2_recovery/names_new24.json")))
    singles = [s for s in existing if len(s.parts) == 1]
    listy = [s for s in singles if isinstance(s.run(s.sample(random.Random(1))), tuple)]
    rng = random.Random(COMPOSE_SEED)
    need, ordinary, seen, drawn = [], [], set(), 0
    while (len(need) < 30 or len(ordinary) < 12) and drawn < 20000:
        drawn += 1
        a, b = rng.choice(listy), rng.choice(singles)
        s = E.Spec(a.parts + b.parts)
        if s.name in used or s.name in seen:
            continue
        seen.add(s.name)
        try:
            s.sample(random.Random(2))
            h = task_hash(s)
            ln = latent_need(s)
        except E.Invalid:
            continue
        rec = {"name": s.name, "sha256": h, "draw": drawn}
        if ln and len(need) < 30:
            need.append(rec)
        elif not ln and len(ordinary) < 12:
            ordinary.append(rec)
    return need, ordinary, drawn


def fst16():
    out, k = [], 0
    for s in FST.generate(FST_SEED, 400):
        k += 1
        try:
            if latent_need(s):
                out.append({"name": s.name, "sha256": task_hash(s), "draw": k})
        except E.Invalid:
            continue
        if len(out) >= 16:
            break
    return out, k


def main(a):
    need, ordinary, drawn = compositions()
    fst, kf = fst16()
    data = {"schema": "neumann.q3-psi-eval-set.v1",
            "status": "PRE-REGISTERED before any agent run on these tasks (development; see prereg.json)",
            "rule": __doc__.split("Built by fixed rules before any agent runs on these tasks:")[1].split("  python")[0].strip(),
            "latent_need30": need, "ordinary12": ordinary, "fst16": fst,
            "compositions_drawn": drawn, "fst_drawn": kf}
    p = pathlib.Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(len(need), "latent-need,", len(ordinary), "ordinary (drawn", drawn, ");", len(fst), "fst (drawn", kf, ")")
    for grp in ("latent_need30", "ordinary12", "fst16"):
        print(grp, [t["name"] for t in data[grp]][:40])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(ap.parse_args())
