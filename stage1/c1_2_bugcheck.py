"""C1-2 branch step 1: implementation bug check (once), run because PF (C1-2) addition stayed below 0.95 in-distribution.

  D1  the PF2 machine on addition with the hand-written rules: exact (evaluation sets, 300 per bin)
  D2  the PF2 model in evaluation mode is causal and deterministic
  D3  direction of the C1-2 move signal: the update controller f is trained with the heads FORCED to the
      hand-written rules' moves (as C1-1 B3) until it solves addition; then, with the heads following the rules, at
      every target step and head the 6 counterfactual losses L_j(m) are computed exactly as PF2 does.  Is the rules'
      move the argmin of L_j(m) (where the 6 values are not all equal)?  If yes, the signal points the right way once
      f uses the reads; the failure is then the joint optimisation (moves need a competent f, f needs moves)
  D4  the move-logit gradient of the C1-2 signal at output steps on a checkpoint of the C1-2 addition run vs at
      initialisation (same batch)
  python stage1/c1_2_bugcheck.py [--ckpt path] > stage1/results/c1_2_checks/bugcheck_addition.json
"""
from __future__ import annotations
import argparse
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
import pf as PFM
from pf_rules import RuleModel
from c1_bugcheck import rule_moves

CFG = M.SCALES["pf2"]["1M"]
DIG = [T.TOK[d] for d in T.DIGITS]


@torch.no_grad()
def counterfactual_losses(m, tokens, targets, moves):
    """with the heads following `moves` (list of [B, H, 6] one-hots), at every target step the 18 losses L_j(m) of
    PF2 (head j takes move m, the others keep the given move).  Returns a list of (t, L [B, H, 6], chosen [B, H],
    target mask [B])"""
    B, Tn = tokens.shape
    issep = torch.isin(tokens, m.sep_ids)
    regs = torch.zeros(B, m.R, m.K)
    regs[:, :, 0] = 1.0
    h = torch.zeros(B, m.H, dtype=torch.long)
    out = []
    nm = len(PFM.MOVES)
    for t in range(Tn):
        xt = tokens[:, t]
        e = m.emb(xt)
        idx = moves[t].argmax(-1)
        cand = PFM.candidates(tokens, t, h, xt, issep)
        sym = torch.gather(tokens[:, None, :].expand(B, m.H, Tn), 2, cand)
        reads = F.one_hot(torch.gather(sym, 2, idx.unsqueeze(-1)).squeeze(-1), m.V).float()
        h = torch.gather(cand, 2, idx.unsqueeze(-1)).squeeze(-1)
        yt = targets[:, t]
        tm = yt != -100
        if bool(tm.any()):
            cf = reads.unsqueeze(1).unsqueeze(1).expand(B, m.H, nm, m.H, m.V).clone()
            oh = F.one_hot(sym, m.V).float()
            for j in range(m.H):
                cf[:, j, :, j, :] = oh[:, j]
            x_cf = torch.cat([e.unsqueeze(1).expand(B, m.H * nm, e.shape[-1]),
                              regs.flatten(1).unsqueeze(1).expand(B, m.H * nm, m.R * m.K),
                              cf.view(B, m.H * nm, m.H * m.V)], -1)
            lg = m.f(x_cf.reshape(B * m.H * nm, -1))[:, m.R * m.K:]
            L = F.cross_entropy(lg, yt.clamp(min=0).repeat_interleave(m.H * nm), reduction="none").view(B, m.H, nm)
            out.append((t, L, idx.clone(), tm.clone()))
        fo = m.f(torch.cat([e, regs.flatten(1), reads.flatten(1)], -1))
        regs = F.one_hot(fo[:, :m.R * m.K].view(B, m.R, m.K).argmax(-1), m.K).float()
    return out


def move_grad_output_steps(m, ex):
    xb, yb = R.make_batch(ex)
    m.train()
    m.targets = yb
    m.debug = []
    torch.manual_seed(1)
    m(xb)
    m.aux.backward()
    vals = []
    for t, (ml, _) in enumerate(m.debug):
        g = ml.grad.abs().mean(-1).mean(-1) if ml.grad is not None else torch.zeros(len(ex))
        for b, e in enumerate(ex):
            if len(e[0]) - 1 <= t < len(e[0]) + len(e[1]) - 1:
                vals.append(float(g[b]))
    m.debug = None
    return sum(vals) / len(vals)


def main(a):
    torch.set_num_threads(1)
    out = {}
    ev = T.eval_sets("addition", 1000, 500)
    torch.manual_seed(0)
    m = M.build("pf2", len(T.VOCAB), DIG, CFG)
    out["D1_rules_exact"] = {l: R.exact_match(RuleModel(m, "addition"), ex[:300], "pf2", CFG)[0] for l, ex in ev.items()}
    m.eval()
    x, _ = R.make_batch(T.train_set("addition", 8, 0))
    y = x.clone()
    cut = x.shape[1] // 2
    y[:, cut:] = torch.randint(2, len(T.VOCAB), y[:, cut:].shape)
    with torch.no_grad():
        a1, a2, b1 = m(x), m(x), m(y)
    out["D2_eval_causal_and_deterministic"] = bool(torch.equal(a1, a2) and torch.equal(a1[:, :cut], b1[:, :cut]))
    # D3: f trained under the rules' moves, then the direction of the C1-2 signal
    torch.manual_seed(0)
    m = M.build("pf2", len(T.VOCAB), DIG, CFG)
    params = [p for n, p in m.named_parameters() if not n.startswith("g.")]
    steps = a.f_steps
    opt = torch.optim.AdamW(params, lr=1e-3, betas=(0.9, 0.98), weight_decay=0.1)
    warm = max(1, steps // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / steps)))))
    data = T.train_set("addition", 100000, 0)
    rng = random.Random("batches:0")
    for s in range(steps):
        m.train()
        m.tau = 1.0 * 0.1 ** (s / steps)
        xb, yb = R.make_batch([data[rng.randrange(len(data))] for _ in range(64)])
        loss = F.cross_entropy(PFM.PF.forward(m, xb, forced_moves=rule_moves(m, xb)).reshape(-1, len(T.VOCAB)),
                               yb.reshape(-1), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
    m.eval()
    ex = ev["id_1-10"][:200]
    xx, yy = R.make_batch(ex)
    fm = rule_moves(m, xx)
    with torch.no_grad():
        pred = PFM.PF.forward(m, xx, forced_moves=fm).argmax(-1)
    msk = yy != -100
    f_acc = float(((pred == yy) | ~msk).all(1).float().mean())
    rows = counterfactual_losses(m, xx, yy, fm)
    informative = agree = 0
    per_head = [[0, 0] for _ in range(m.H)]
    for t, L, idx, tm in rows:
        for b in range(L.shape[0]):
            if not bool(tm[b]):
                continue
            for j in range(m.H):
                Lj = L[b, j]
                if float(Lj.max() - Lj.min()) < 1e-6:
                    continue                                      # all 6 moves read the same: no information
                informative += 1
                per_head[j][0] += 1
                ok = float(Lj[idx[b, j]]) <= float(Lj.min()) + 1e-6
                agree += ok
                per_head[j][1] += ok
    out["D3_signal_direction_with_competent_f"] = {
        "f_training_steps_with_rule_moves": steps, "f_id_accuracy_with_rule_moves": f_acc,
        "informative_head_step_pairs": informative,
        "rule_move_is_argmin_share": agree / max(informative, 1),
        "per_head_informative_and_agree": per_head}
    # D4
    ex = T.train_set("addition", 64, 1)
    torch.manual_seed(0)
    m0 = M.build("pf2", len(T.VOCAB), DIG, CFG)
    d4 = {"init_move_logit_grad_output_steps": move_grad_output_steps(m0, ex)}
    if a.ckpt and os.path.exists(a.ckpt):
        c = torch.load(a.ckpt, weights_only=False)
        m1 = M.build("pf2", len(T.VOCAB), DIG, CFG)
        m1.load_state_dict(c["model"])
        m1.tau = 0.1 ** (c["state"]["step"] / 20000)
        d4["checkpoint_step"] = c["state"]["step"]
        d4["checkpoint_move_logit_grad_output_steps"] = move_grad_output_steps(m1, ex)
    out["D4_move_signal_gradient"] = d4
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="")
    p.add_argument("--f-steps", type=int, default=1500)
    main(p.parse_args())
