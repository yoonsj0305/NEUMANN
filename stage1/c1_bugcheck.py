"""C1-1 branch step 1: implementation bug check (once), run because PF addition stayed below 0.95 in-distribution.

  B1  the machine on addition with hand-written rules: exact (task 1b, re-run here on the evaluation sets)
  B2  the learned PF in evaluation mode is causal and deterministic
  B3  component isolation: the head moves are FORCED to the hand-written rules' moves (recorded from the rules
      machine on the same batch) and only the learned update controller f (+ embedding) is trained, same optimiser
      and batches as the harness, 3,000 steps, then the in-distribution evaluation with the same forced moves.
      Learns -> the machine, the read path and f are sound and the failure is in learning the moves (g);
      does not learn -> a defect in the f / register / output path.
  B4  at initialisation, on addition batches: gradient on the move logits at the OUTPUT steps (where the heads
      must move) vs at the prompt steps
  python stage1/c1_bugcheck.py > stage1/results/c1_checks/bugcheck_addition.json
"""
from __future__ import annotations
import json
import math
import os
import random
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(__file__))
import tasks as T
import models as M
import run as R
from pf_rules import Rules, RuleModel

CFG = M.SCALES["pf"]["1M"]
DIG = [T.TOK[d] for d in T.DIGITS]


def rule_moves(pf, tokens):
    """the per-step moves the hand-written rules take on these tokens"""
    rules = Rules("addition", pf.H, pf.R, pf.K, pf.V)
    moves = []

    class Rec:
        def move(self, x, regs, prev):
            m = rules.move(x, regs, prev)
            moves.append(m)
            return m

        def update(self, x, regs, reads):
            return rules.update(x, regs, reads)
    with torch.no_grad():
        pf(tokens, controller=Rec())
    return moves


def main():
    torch.set_num_threads(1)
    out = {}
    ev = T.eval_sets("addition", 1000, 500)
    torch.manual_seed(0)
    pf = M.build("pf", len(T.VOCAB), DIG, CFG)
    out["B1_rules_exact"] = {l: R.exact_match(RuleModel(pf, "addition"), ex[:300], "pf", CFG)[0] for l, ex in ev.items()}
    pf.eval()
    x, _ = R.make_batch(T.train_set("addition", 8, 0))
    y = x.clone()
    cut = x.shape[1] // 2
    y[:, cut:] = torch.randint(2, len(T.VOCAB), y[:, cut:].shape)
    with torch.no_grad():
        a1, a2, b1 = pf(x), pf(x), pf(y)
    out["B2_eval_causal_and_deterministic"] = bool(torch.equal(a1, a2) and torch.equal(a1[:, :cut], b1[:, :cut]))
    # B3
    torch.manual_seed(0)
    pf = M.build("pf", len(T.VOCAB), DIG, CFG)
    params = [p for n, p in pf.named_parameters() if not n.startswith("g.")]
    steps = 3000
    opt = torch.optim.AdamW(params, lr=1e-3, betas=(0.9, 0.98), weight_decay=0.1)
    warm = max(1, steps // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / steps)))))
    data = T.train_set("addition", 100000, 0)
    rng = random.Random("batches:0")
    curve = []
    for s in range(steps):
        pf.train()
        pf.tau = 1.0 * 0.1 ** (s / steps)
        xb, yb = R.make_batch([data[rng.randrange(len(data))] for _ in range(64)])
        fm = rule_moves(pf, xb)
        loss = F.cross_entropy(pf(xb, forced_moves=fm).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
        if (s + 1) % 500 == 0:
            pf.eval()
            ex = ev["id_1-10"][:500]
            ok = 0
            with torch.no_grad():
                for i in range(0, len(ex), 100):
                    xx, yy = R.make_batch(ex[i:i + 100])
                    pred = pf(xx, forced_moves=rule_moves(pf, xx)).argmax(-1)
                    m = yy != -100
                    ok += int(((pred == yy) | ~m).all(1).sum())
            curve.append([s + 1, round(float(loss), 4), ok / len(ex)])
            print("B3", curve[-1], flush=True)
    out["B3_forced_rule_moves_learned_f"] = {"steps": steps, "curve_step_loss_id_acc": curve}
    # B4
    torch.manual_seed(0)
    pf = M.build("pf", len(T.VOCAB), DIG, CFG)
    pf.train()
    pf.debug = []
    ex = T.train_set("addition", 64, 1)
    xb, yb = R.make_batch(ex)
    F.cross_entropy(pf(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100).backward()
    out_pos, pro_pos = [], []
    for t, (ml, _) in enumerate(pf.debug):
        g = ml.grad.abs().sum(-1).sum(-1) if ml.grad is not None else torch.zeros(len(ex))   # [B]
        for b, (p, a) in enumerate(ex):
            if t < len(p) - 1:
                pro_pos.append(float(g[b]))
            elif t < len(p) + len(a) - 1:
                out_pos.append(float(g[b]))
    out["B4_move_logit_grad_mean_abs"] = {"prompt_steps": sum(pro_pos) / len(pro_pos),
                                          "output_steps": sum(out_pos) / len(out_pos),
                                          "output_steps_nonzero_share": sum(v > 0 for v in out_pos) / len(out_pos)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
