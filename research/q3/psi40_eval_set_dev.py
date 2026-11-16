"""DEVELOPMENT ONLY: pre-registered evaluation set for section 40 (PSI40), built before any agent run on it.

Fixed rules (latent_need and task_hash are those of research/q3/psi_eval_set_dev.py, unchanged):
* lr_need30 / lr_ord12 -- new two-routine compositions of the independent list-routines lineage, tasks() rule, seed
  "compose:neumann-q3-psi40-eval-v1", excluding every earlier name (the 228 tasks, section 38 and section 39 sets);
  the first 30 latent-need and the first 12 not latent-need in generation order;
* fst16 -- the first 16 latent-need hidden transducers of research/q3/psi_fst_family.py with the seed
  "neumann-q3-psi40-fst-v1", excluding the section 39 fst16 (the SAME family PSI40 was developed on: disclosed);
* rha16 -- the first 16 latent-need random hidden automata of research/q3/psi40_rha_family.py (a family written for
  this evaluation, never used in development) with the seed "neumann-q3-psi40-rha-v1".
Per task: name and sha256 of canonical {name, train, test} of Env(spec, 0).

  python research/q3/psi40_eval_set_dev.py --out docs/experiments/dev/psi40/eval_set.json
"""
from __future__ import annotations
import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
import psi_fst_family as FST
import psi40_rha_family as RHA
from psi_eval_set_dev import latent_need, task_hash

COMPOSE_SEED = "compose:neumann-q3-psi40-eval-v1"
FST_SEED = "neumann-q3-psi40-fst-v1"
RHA_SEED = "neumann-q3-psi40-rha-v1"


def used_names():
    used = {s.name for s in E.tasks()}
    used |= set(json.load(open("docs/experiments/dev/case2_recovery/names_new24.json")))
    prev = json.load(open("docs/experiments/dev/psi/eval_set.json"))
    used |= {t["name"] for g in ("latent_need30", "ordinary12", "fst16") for t in prev[g]}
    return used


def compositions(used):
    existing = E.tasks()
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


def family(gen, seed, used, n=16, pool=600):
    out, k = [], 0
    for s in gen(seed, pool):
        k += 1
        if s.name in used:
            continue
        try:
            if latent_need(s):
                out.append({"name": s.name, "sha256": task_hash(s), "draw": k})
        except E.Invalid:
            continue
        if len(out) >= n:
            break
    return out, k


def main(a):
    used = used_names()
    need, ordinary, drawn = compositions(used)
    fst, kf = family(FST.generate, FST_SEED, used)
    rha, kr = family(RHA.generate, RHA_SEED, used)
    data = {"schema": "neumann.q3-psi40-eval-set.v1",
            "status": "PRE-REGISTERED before any agent run on these tasks (development; see prereg.json)",
            "rule": __doc__.split("Fixed rules")[1].split("  python")[0].strip(),
            "lr_need30": need, "lr_ord12": ordinary, "fst16": fst, "rha16": rha,
            "compositions_drawn": drawn, "fst_drawn": kf, "rha_drawn": kr}
    p = pathlib.Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(len(need), "lr latent-need,", len(ordinary), "lr ordinary (drawn", drawn, ");", len(fst), "fst (drawn", kf,
          ");", len(rha), "rha (drawn", kr, ")")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(ap.parse_args())
