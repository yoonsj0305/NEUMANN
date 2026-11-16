"""DEVELOPMENT ONLY (section 44): the pre-registered independent evaluation set for the factored joint core.

Built by a fixed rule before any agent run on these tasks:
* the whole parameter space of research/q3/psi42_hrt_family.py (6 update kinds; summod m in {5, 7, 10}, satsum B in
  10..24; 5 output kinds: 110 tasks);
* every task name that appears anywhere in the repository's docs/ and research/ files or in the section 42-44 working
  files is EXCLUDED (the 24 development tasks, the 16 section 42 evaluation tasks, anything else ever written down);
* EVERY remaining task forms the set, in name order -- no sampling, no choice -- in two groups fixed by
  research/q3/psi_eval_set_dev.latent_need (the answer-as-state is insufficient in both directions):
    latent_need  -- the primary group (the property every earlier HRT set was drawn by);
    other        -- the rest (generalisation to output kinds absent from development, e.g. delta; and regression).
Per task: name and sha256 of canonical {name, train, test} of Env(spec, 0).

  python research/q3/psi44_eval_set_dev.py --out docs/experiments/dev/psi44/eval_set.json [--extra-used file ...]
"""
from __future__ import annotations
import argparse
import glob
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import psi42_hrt_family as HR
import psi_eval_set_dev as PE

NAME = re.compile(r"hrt\(u=[a-z0-9]+;o=[a-z0-9]+\)")


def space():
    out = []
    for u in HR.UPDATES:
        ps = [None] if u not in ("summod", "satsum") else ((5, 7, 10) if u == "summod" else range(10, 25))
        for p in ps:
            for o in HR.OUTPUTS:
                out.append(HR.HRTSpec(u, p, o).name)
    return out


def used_names(extra):
    used = set()
    for f in glob.glob("docs/**/*", recursive=True) + glob.glob("research/**/*", recursive=True) + list(extra):
        p = pathlib.Path(f)
        if p.is_file():
            used |= set(NAME.findall(p.read_text(errors="ignore")))
    return used


def main(a):
    used = used_names(a.extra_used or [])
    allx = space()
    unused = sorted(n for n in allx if n not in used)
    rows = []
    for n in unused:
        spec = HR.parse(n)
        rows.append({"name": n, "sha256": PE.task_hash(spec),
                     "group": "latent_need" if PE.latent_need(spec) else "other"})
    out = {"schema": "neumann.q3-psi44-eval-set.v1",
           "status": "PRE-REGISTERED before any agent run on these tasks",
           "rule": "every task of the psi42_hrt_family parameter space (110 tasks) whose name appears nowhere in "
                   "docs/, research/ or the section 42-44 working files, in name order; groups by "
                   "psi_eval_set_dev.latent_need; sha256 of {name, train, test} of Env(spec, 0)",
           "space": len(allx), "excluded_as_used": len(set(allx) & used), "unused": len(unused),
           "groups": {g: sum(r["group"] == g for r in rows) for g in ("latent_need", "other")},
           "hrt": rows}
    s = json.dumps(out, indent=1, sort_keys=True)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(s + "\n")
    print(len(rows), "tasks;", hashlib.sha256(json.dumps([r["name"] for r in rows]).encode()).hexdigest())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--extra-used", nargs="*")
    main(p.parse_args())
