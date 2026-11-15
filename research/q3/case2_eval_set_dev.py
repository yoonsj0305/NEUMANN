"""DEVELOPMENT ONLY: pre-registered evaluation set for the CASE-2 recovery experiment (section 38).

Fixed BEFORE any result on these tasks is produced:
* 24 NEW two-routine compositions from the independent author's routines in env_listroutines (the same lineage):
  the composition rule of env_listroutines.tasks() (outer routine with a list output, then any routine; valid on
  Random(2)), with the rng seed string "compose:neumann-q3-case2-eval-v1"; names among the existing 228 tasks are
  excluded; the task must build an Env(spec, 0) (8 initial examples, 10 hidden tests, the unchanged generator).
  Difficulty stratification by final output type with quotas proportional to the existing 120 compositions
  (88 L / 19 I / 13 B): L 18, I 4, B 2; candidates are taken in generation order until each quota is full.
* 12 regression tasks: list-routines tasks solved by the Gate E baseline (docs/experiments/dev/gateE/
  lr_baseline.jsonl) that were never used in a policy-E experiment (not among the 11 development tasks, the 60
  unsolved or the 24 solved transfer tasks of section 36), first 12 by sha256("neumann-q3-case2-regression-v1:" +
  name).
Per task: the name and sha256 of canonical JSON {"name", "train", "test"} (the hidden tests enter only the hash).

  python research/q3/case2_eval_set_dev.py --out docs/experiments/dev/case2_recovery/eval_set.json
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

SEED = "compose:neumann-q3-case2-eval-v1"
QUOTA = {"L": 18, "I": 4, "B": 2}
REG_SALT = "neumann-q3-case2-regression-v1:"


def otype(v):
    return "B" if isinstance(v, bool) else "I" if isinstance(v, int) else "L"


def task_hash(spec):
    env = E.Env(spec, 0, budget=60)
    data = {"name": spec.name, "train": [[list(x), list(y) if isinstance(y, tuple) else y] for (x,), y in env._train],
            "test": [list(x) for x in env._test]}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), env


def new_compositions():
    existing = E.tasks()
    names = {s.name for s in existing}
    singles = [s for s in existing if len(s.parts) == 1]
    listy = [s for s in singles if isinstance(s.run(s.sample(random.Random(1))), tuple)]
    rng = random.Random(SEED)
    chosen, seen, filled, tried = [], set(), {k: 0 for k in QUOTA}, 0
    while any(filled[k] < QUOTA[k] for k in QUOTA) and tried < 100000:
        tried += 1
        a, b = rng.choice(listy), rng.choice(singles)
        s = E.Spec(a.parts + b.parts)
        if s.name in names or s.name in seen:
            continue
        seen.add(s.name)
        try:
            v = s.run(s.sample(random.Random(2)))
            h, env = task_hash(s)
        except E.Invalid:
            continue
        t = otype(env._train[0][1])
        if filled[t] >= QUOTA[t]:
            continue
        filled[t] += 1
        chosen.append({"name": s.name, "output_type": t, "sha256": h, "candidate_index": tried})
    return chosen, tried


def regression_set():
    lr = [json.loads(l) for l in open("docs/experiments/dev/gateE/lr_baseline.jsonl")]
    used = set(json.load(open("docs/experiments/dev/budgeted_reach/dev11_names.json")))
    used |= set(json.load(open("docs/experiments/dev/budgeted_reach/transfer_unsolved60.json")))
    used |= set(json.load(open("docs/experiments/dev/budgeted_reach/transfer_solved24.json")))
    pool = sorted(r["name"] for r in lr if r["solved"] and r["name"] not in used)
    pick = sorted(pool, key=lambda n: hashlib.sha256((REG_SALT + n).encode()).hexdigest())[:12]
    specs = {s.name: s for s in E.tasks()}
    out = []
    for n in sorted(pick):
        h, env = task_hash(specs[n])
        out.append({"name": n, "output_type": otype(env._train[0][1]), "sha256": h})
    return out, len(pool)


def main(args):
    comps, tried = new_compositions()
    reg, pool = regression_set()
    data = {"schema": "neumann.q3-case2-eval-set.v1",
            "status": "PRE-REGISTERED before any run on these tasks (development only; same list-routines lineage)",
            "new_compositions": {"rule": __doc__.split("Fixed BEFORE")[1].split("* 12 regression")[0].strip(),
                                 "seed": SEED, "quota": QUOTA, "candidates_drawn": tried, "tasks": comps},
            "regression": {"rule": "Gate E baseline-solved, never used in a policy-E experiment; first 12 by "
                                   "sha256('%s' + name)" % REG_SALT, "pool_size": pool, "tasks": reg},
            "env": "env_listroutines.Env(spec, 0, n_train=8, n_test=10, budget=60); hidden tests enter only the hash"}
    p = pathlib.Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(len(comps), "new;", len(reg), "regression; candidates drawn", tried)
    for c in comps + reg:
        print(c["output_type"], c["name"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(ap.parse_args())
