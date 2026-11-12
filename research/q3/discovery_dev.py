"""SOURCE-only development of the learned discovery policy (never evidence for a gate).

  wake <bigbench> <oeis> <rule:cap_s,oeis:cap_s> <rows.jsonl>
      Experience: the base proposer with the UNTRAINED policy and a large cap on every SOURCE task.
      Resumable.  Rows keep the verified method and every hypothesis tried.
  cv <bigbench> <oeis> <cap_s> <wake_rows.jsonl> <rows.jsonl>
      5-fold cross-validation over SOURCE tasks.  For each fold the policy is fitted on the wake rows of the
      OTHER folds (both domains pooled: one policy), then every arm runs the held-out tasks under the same cap.
        S  the frozen THIRD core (specialist for lists)        D  sequence specialist (oeis only)
        A  base proposer, untrained policy, no memory
        B  A + memory of verified methods (no policy learning)  = the causal control for the policy
        C  B + learned policy (hypothesis weights, generative costs, latent-variable proposals)
        Cw C without the latent-variable proposals (attribution only)
"""
from __future__ import annotations
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc
import dev_source, invention_first as first, sequence_specialist

FOLDS = 5
INV = None
POLICY = {}


def fold_of(tid):
    return int(first.sha256(("neumann-discovery-cv-v1:" + tid).encode()), 16) % FOLDS


def _inv():
    global INV
    if INV is None:
        INV = sc.load_inverses()
    return INV


def _row(t, r, **kw):
    r = dict(r, id=t["id"], in_types=list(t["in_types"]), out_type=t["out_type"], sig=ic.sig_key(t), **kw)
    return r


def wake_job(a):
    t, cap = a
    return _row(t, dc.solve(t, cap, dc.Policy(), _inv(), features=True, replay=False))


def cv_job(a):
    arm, t, cap = a
    if arm == "D":
        tr, te = [o for _, o in t["train"]], [o for _, o in t["test"]]
        p = sequence_specialist.predict(tr, len(te))
        return {"id": t["id"], "arm": arm, "fit": p is not None, "solved": p == te, "cpu_seconds": 0.0}
    if arm == "S":
        r = sc.solve(t, cap, "S", _inv())
    else:
        pol = POLICY[fold_of(t["id"])]
        if arm == "A":
            r = dc.solve(t, cap, dc.Policy(), _inv(), replay=False)
        elif arm == "B":
            r = dc.solve(t, cap, dc.Policy(memory=pol.memory), _inv())
        elif arm == "Cw":                   # ablation: learned weights and costs, no latent-variable proposals
            r = dc.solve(t, cap, dc.Policy(pol.costs, pol.weights, pol.memory), _inv())
        else:
            r = dc.solve(t, cap, pol, _inv())
    r.pop("sol", None)
    return _row(t, r, arm=arm)


def _run(job, jobs, out, key):
    done = set()
    try:
        done = {key(json.loads(l)) for l in open(out)}
    except FileNotFoundError:
        pass
    todo = [j for j in jobs if (j[0], j[1]["id"]) not in done] if len(jobs[0]) == 3 else \
           [j for j in jobs if j[0]["id"] not in done]
    print("jobs", len(jobs), "todo", len(todo), flush=True)
    with Pool(4) as p, open(out, "a") as fh:
        for r in p.imap_unordered(job, todo):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def wake(bigbench, oeis, caps, out):
    """caps: 'rule:120,oeis:30' (CPU seconds per task and family; the experience budget, reported as cost)."""
    d = dev_source.load(bigbench, oeis)
    cap = {k: float(v) for k, v in (c.split(":") for c in caps.split(","))}
    _run(wake_job, [(t, cap[f]) for f in cap for t in d[f]], out, lambda r: r["id"])


def policies(wake_rows):
    rows = [json.loads(l) for l in open(wake_rows)]
    return {f: dc.fit([r for r in rows if fold_of(r["id"]) != f]) for f in range(FOLDS)}, rows


def cv(bigbench, oeis, cap, wake_rows, out):
    global POLICY
    POLICY, _ = policies(wake_rows)
    d = dev_source.load(bigbench, oeis)
    jobs = [(arm, t, float(cap)) for f in ("rule", "oeis") for arm in ("C", "B", "A", "S", "D", "Cw") for t in d[f]
            if not (arm == "D" and f != "oeis")]
    _run(cv_job, jobs, out, lambda r: (r["arm"], r["id"]))


if __name__ == "__main__":
    {"wake": wake, "cv": cv}[sys.argv[1]](*sys.argv[2:])
