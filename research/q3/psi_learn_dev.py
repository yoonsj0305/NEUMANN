"""DEVELOPMENT ONLY: learn the PSI discovery policy (which latent hypothesis to synthesise first) from experience.

Experience = every latent candidate PSI gave a synthesis attempt in P runs on TRAINING tasks only (already-used
development tasks, never the pre-registered evaluation set).  Label 1 iff the candidate was adopted AND the machine
it belongs to passed the independent SOURCE challenge; 0 otherwise (no Update, folds wrongly, or adopted and
refuted).  Features are psi.features() of the current task's evidence (no task name, no answer).

  python research/q3/psi_learn_dev.py --rows p_rows.jsonl [...] --out policy.json
"""
from __future__ import annotations
import argparse
import json
import sys

sys.path.insert(0, ".")
from neumann1 import psi as P


def experience(paths):
    data, src = [], []
    for path in paths:
        for line in open(path):
            if not line.strip():
                continue
            r = json.loads(line)
            if r["arm"] != "P":
                continue
            for m in r["machines"]:
                verified = m.get("challenge") is True
                for p in m.get("psi") or []:
                    for t in p.get("tried", []):
                        y = int(t["outcome"] == "ok" and verified and p.get("outcome") == "adopted"
                                and p.get("adopted") == t["vars"])
                        data.append((t["feat"], y))
                        src.append({"task": r["name"], "vars": t["vars"], "label": y, "outcome": t["outcome"]})
    return data, src


def main(a):
    data, src = experience(a.rows)
    w = P.update_discovery_policy(data) if data else {}
    out = {"schema": "neumann.q3-psi-policy.v1", "weights": w, "n": len(data), "positives": sum(y for _, y in data),
           "training_rows": a.rows, "training_tasks": sorted({s["task"] for s in src}), "examples": src}
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
    print("experience", len(data), "positives", out["positives"], "tasks", len(out["training_tasks"]))
    print(json.dumps(w, sort_keys=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    main(ap.parse_args())
