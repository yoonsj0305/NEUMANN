"""Phase A'' harness diagnosis (CLAUDE.md: rope < 95 % on associative recall -> harness problem, debugging allowed;
check first: the loss is on the answer tokens only, the answer position / mask, the evaluation decoding).

Uses the harness's own make_batch / exact_match / model builder / optimiser settings.
  D1  mask and answer position on associative-recall batches
  D2  loss on answer tokens only: the loss computed by the harness equals CE restricted to the answer positions
  D3  gradients reach every parameter
  D4  evaluation decoding: teacher-forced exact match == real greedy decoding, on a partly trained rope model
  D5  controls in the same token format, rope, 2,000 steps, same optimiser: the answer is the value of the LAST pair
      (position only, no key matching) and the value of the FIRST pair
  python stage1/diag_phaseA3.py [--steps 2000] > stage1/results/phaseA3_checks/diag.txt
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

DIG = [T.TOK[d] for d in T.DIGITS]


def train(model, data, steps, seed=0, lr=1e-3):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, betas=(0.9, 0.98), weight_decay=0.1)
    warm = max(1, steps // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / steps)))))
    rng = random.Random(seed)
    for _ in range(steps):
        xb, yb = R.make_batch([data[rng.randrange(len(data))] for _ in range(64)])
        loss = F.cross_entropy(model(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
    return float(loss)


@torch.no_grad()
def greedy(model, exs):
    ok = 0
    for p, a in exs:
        x = torch.tensor([p])
        out = []
        for _ in range(len(a) + 2):
            nx = int(model(x)[0, -1].argmax())
            out.append(nx)
            if nx == T.EOS:
                break
            x = torch.cat([x, torch.tensor([[nx]])], 1)
        ok += out == a
    return ok / len(exs)


def variant(which, n, rng):
    """same token format as assoc; the answer is the value of the last / first pair"""
    p, _ = T.assoc(n, rng)
    vals = p[:-3][1::2]
    return p, [vals[-1] if which == "last" else vals[0]]


def main(a):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    out = {}
    # D1 / D2
    data = T.train_set("assoc_n4", 2000, 0)
    xb, yb = R.make_batch(data[:64])
    rows = []
    for i, (p, ans) in enumerate(data[:64]):
        pos = (yb[i] != -100).nonzero().flatten().tolist()
        rows.append(pos == [len(p) - 1, len(p)] and T.VOCAB[int(xb[i, len(p) - 1])] == "="
                    and [int(yb[i, j]) for j in pos] == ans)
    out["D1_mask_answer_position_ok"] = f"{sum(rows)}/{len(rows)}"
    cfg = M.SCALES["rope"]["1M"]
    m = M.build("rope", len(T.VOCAB), DIG, cfg)
    logits = m(xb)
    full = F.cross_entropy(logits.reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
    sel = yb != -100
    manual = F.cross_entropy(logits[sel], yb[sel])
    out["D2_loss_equals_answer_only_CE"] = bool(torch.allclose(full, manual))
    out["D2_target_tokens_per_example"] = sorted(set(int(s) for s in sel.sum(1)))
    # D3
    full.backward()
    nograd = [n for n, p_ in m.named_parameters() if p_.grad is None or float(p_.grad.abs().sum()) == 0]
    out["D3_params_without_gradient"] = nograd
    # D4: partly trained model, teacher-forced vs greedy
    m = M.build("rope", len(T.VOCAB), DIG, cfg)
    train(m, T.train_set("assoc_n4", 100000, 0), 300)
    ev = T.eval_sets("assoc_n4", 300, 10)["id_4-4"]
    tf, _ = R.exact_match(m, ev, "rope", cfg)
    out["D4_teacher_forced_vs_greedy"] = [round(tf, 4), round(greedy(m, ev), 4)]
    # D5: position-only controls
    for which in ("last", "first"):
        rng = random.Random("diag:%s" % which)
        d = [T.encode(*variant(which, 4, rng)) for _ in range(100000)]
        rng2 = random.Random("diag-eval:%s" % which)
        e = [T.encode(*variant(which, 4, rng2)) for _ in range(500)]
        torch.manual_seed(0)
        m = M.build("rope", len(T.VOCAB), DIG, cfg)
        lo = train(m, d, a.steps)
        acc, _ = R.exact_match(m, e, "rope", cfg)
        out["D5_control_value_of_%s_pair_n4_%dsteps" % (which, a.steps)] = {"acc": acc, "final_loss": round(lo, 4)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=2000)
    main(p.parse_args())
