"""DEVELOPMENT ONLY (section 41): fixed-rule task sets for Phase 3 (unused development tasks) and Phase 4 (the
pre-registered evaluation).  Same generators and latent-need rule as sections 39-40; every earlier name excluded.

  python research/q3/psi41_task_set_dev.py phase3 --out docs/experiments/dev/psi41/phase3_set.json
  python research/q3/psi41_task_set_dev.py eval   --out docs/experiments/dev/psi41/eval_set.json
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import psi_fst_family as FST
import psi40_rha_family as RHA
from psi40_eval_set_dev import used_names, compositions as _unused, family

SEEDS = {"phase3": ("neumann-q3-psi41-phase3-fst", "neumann-q3-psi41-phase3-rha", 8),
         "eval": ("neumann-q3-psi41-eval-fst", "neumann-q3-psi41-eval-rha", 16)}


def main(a):
    used = used_names()
    p40 = json.load(open("docs/experiments/dev/psi40/eval_set.json"))
    used |= {t["name"] for g in ("lr_need30", "lr_ord12", "fst16", "rha16") for t in p40[g]}
    ph3 = pathlib.Path("docs/experiments/dev/psi41/phase3_set.json")
    if a.which == "eval" and ph3.exists():
        used |= {t["name"] for g in ("fst", "rha") for t in json.loads(ph3.read_text())[g]}
    fs, rs, n = SEEDS[a.which]
    fst, kf = family(FST.generate, fs, used, n=n)
    rha, kr = family(RHA.generate, rs, used, n=n)
    data = {"schema": "neumann.q3-psi41-%s-set.v1" % a.which, "fst": fst, "rha": rha, "fst_drawn": kf,
            "rha_drawn": kr, "rule": "first n latent-need tasks of each generator with the seeds above, every earlier "
                                     "name excluded; sha256 of {name, train, test} of Env(spec, 0)"}
    if a.which == "eval":
        # a regression guard in the independent list-routines lineage: the first 12 latent-need and 12 ordinary new
        # compositions with the seed "compose:neumann-q3-psi41-eval-v1" (every earlier name excluded)
        import random
        import env_listroutines as E
        from psi_eval_set_dev import latent_need, task_hash
        existing = E.tasks()
        singles = [s_ for s_ in existing if len(s_.parts) == 1]
        listy = [s_ for s_ in singles if isinstance(s_.run(s_.sample(random.Random(1))), tuple)]
        rng = random.Random("compose:neumann-q3-psi41-eval-v1")
        need, ordinary, seen, drawn = [], [], set(), 0
        while (len(need) < 12 or len(ordinary) < 12) and drawn < 20000:
            drawn += 1
            s_ = E.Spec(rng.choice(listy).parts + rng.choice(singles).parts)
            if s_.name in used or s_.name in seen:
                continue
            seen.add(s_.name)
            try:
                s_.sample(random.Random(2))
                h_ = task_hash(s_)
                ln_ = latent_need(s_)
            except E.Invalid:
                continue
            rec_ = {"name": s_.name, "sha256": h_, "draw": drawn}
            if ln_ and len(need) < 12:
                need.append(rec_)
            elif not ln_ and len(ordinary) < 12:
                ordinary.append(rec_)
        data.update({"lr_need12": need, "lr_ord12": ordinary, "compositions_drawn": drawn})
    p = pathlib.Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(len(fst), "fst,", len(rha), "rha")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=("phase3", "eval"))
    ap.add_argument("--out", required=True)
    main(ap.parse_args())
