"""PF-search (CANDIDATE_DESIGN.md 11), the C1-2 failure branch, run once.

* Search target: the move policy only -- a table policy[head, token class] (3 heads x 7 classes: digit, +, =, |,
  node, answer-phase token, other) -> one of the 6 moves.  The update/output controller is learned by gradient
  descent.
* Search: coordinate descent from the all-"stay" table; cell by cell (head-major, classes in order) all 6 moves are
  scored and the best is fixed (ties keep the current move, then the lower move index); at most 3 sweeps; stop
  early when a sweep changes nothing.
* Score of a table: a fresh update controller (same seed, same initial weights, same batch sequence for every
  candidate) is trained for 300 steps with that table (the harness optimiser: AdamW lr 1e-3, betas (0.9, 0.98),
  weight decay 0.1, clip 1.0, warmup 15 steps, cosine to 10 %; Gumbel temperature 1.0 -> 0.1 over the 300 steps),
  then exact-match accuracy on an in-distribution validation set drawn from the training distribution (500
  examples, its own seed; no out-of-distribution data).
* Budget: at most 400 candidate evaluations.  Every candidate's training and validation FLOPs are summed; the total
  is added to the final training FLOPs for the judgment.
* Final training (separately, run.py --kind pf_search --policy <table>): the found table, the update controller
  trained under the section 7 protocol.

  python stage1/pf_search.py --task addition --out stage1/results/c1_2/pf_search_addition
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import json
import math
import multiprocessing as mp
import os
import pathlib
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STEPS = 300
VAL_SIZE = 500
BUDGET = 400
SWEEPS = 3


def evaluate(task, policy, seed=0):
    import torch
    import torch.nn.functional as F
    import tasks as T
    import models as M
    import run as R
    import pf as PFM
    torch.set_num_threads(1)
    cfg = dict(M.SCALES["pf_search"]["1M"], policy=policy)
    torch.manual_seed(seed)
    m = M.build("pf_search", len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    params = [p for n, p in m.named_parameters() if not n.startswith("g.")]
    opt = torch.optim.AdamW(params, lr=1e-3, betas=(0.9, 0.98), weight_decay=0.1)
    warm = max(1, STEPS // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / STEPS)))))
    data = T.train_set(task, 100000, seed)
    rng = random.Random("batches:%d" % seed)
    flops = 0
    t0 = time.time()
    for s in range(STEPS):
        m.train()
        m.tau = 1.0 * 0.1 ** (s / STEPS)
        xb, yb = R.make_batch([data[rng.randrange(len(data))] for _ in range(64)])
        loss = F.cross_entropy(m(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
        flops += PFM.pf_policy_flops(cfg, xb.shape[0], xb.shape[1], len(T.VOCAB), train=True)["total"]
    val = T.train_set(task, VAL_SIZE, 777)                   # in-distribution validation (own seed)
    acc, fl = R.exact_match(m, val, "pf_search", cfg)
    flops += fl
    return {"policy": policy, "score": acc, "flops": flops, "final_loss": round(float(loss), 4),
            "wall_s": round(time.time() - t0, 1)}


def main(a):
    import pf as PFM
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    logf = out / "search_log.jsonl"
    H, C, NM = 3, len(PFM.CLASS_NAMES), len(PFM.MOVES)
    policy = [[0] * C for _ in range(H)]
    done = {}
    if logf.exists():                                         # resume: reuse finished evaluations
        for l in open(logf):
            r = json.loads(l)
            if "policy" in r:
                done[json.dumps(r["policy"])] = r
    n_eval = len(done)
    total_flops = sum(r["flops"] for r in done.values())
    best_score = None
    ex = cf.ProcessPoolExecutor(max_workers=a.workers, mp_context=mp.get_context("spawn"))
    stop = None
    for sweep in range(1, SWEEPS + 1):
        changed = False
        for h in range(H):
            for c in range(C):
                cands = []
                for mv in range(NM):
                    p = [row[:] for row in policy]
                    p[h][c] = mv
                    cands.append(p)
                todo = [p for p in cands if json.dumps(p) not in done]
                if n_eval + len(todo) > BUDGET:
                    stop = "budget"
                    break
                futs = {ex.submit(evaluate, a.task, p): json.dumps(p) for p in todo}
                for fu in cf.as_completed(futs):
                    r = fu.result()
                    r.update({"sweep": sweep, "cell": [h, c], "class": PFM.CLASS_NAMES[c],
                              "move": PFM.MOVES[r["policy"][h][c]]})
                    done[futs[fu]] = r
                    n_eval += 1
                    total_flops += r["flops"]
                    with open(logf, "a") as fh:
                        fh.write(json.dumps(r) + "\n")
                scores = [done[json.dumps(p)]["score"] for p in cands]
                cur = policy[h][c]
                best = max(range(NM), key=lambda mv: (scores[mv], mv == cur, -mv))
                if best != cur:
                    changed = True
                    policy[h][c] = best
                best_score = scores[best]
                print("sweep %d cell (%d,%s) -> %s score %.3f evals %d" % (
                    sweep, h, PFM.CLASS_NAMES[c], PFM.MOVES[best], best_score, n_eval), flush=True)
            if stop:
                break
        if stop:
            break
        if not changed:
            stop = "converged (a sweep changed nothing)"
            break
    ex.shutdown()
    res = {"task": a.task, "policy": policy, "policy_named": {
        "head%d" % h: {PFM.CLASS_NAMES[c]: PFM.MOVES[policy[h][c]] for c in range(C)} for h in range(H)},
        "best_score_in_distribution_validation": best_score, "evaluations": n_eval, "search_flops": total_flops,
        "stopped": stop or "max sweeps", "spec": {"steps_per_candidate": STEPS, "val_size": VAL_SIZE,
                                                    "budget": BUDGET, "sweeps": SWEEPS, "init": "all stay"}}
    (out / "search_result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--task", default="addition")
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=4)
    main(p.parse_args())
