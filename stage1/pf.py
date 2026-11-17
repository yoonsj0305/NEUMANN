"""C1 Pointer Fold (PF) — stage1/CANDIDATE_DESIGN.md section 3 (frozen 2026-11-17).

State: R registers, each one of K symbols (discrete, initial 0); H read heads, each pointing at one tape position
(initial 0).  The tape is the token sequence itself (read-only); generated answer tokens are part of it
(autoregressive).  One step per processed token x_t, the same cell in the input and the output phase:

  1. move   g(embed(x_t), onehot(registers), onehot(previous reads r_1..r_H)) -> one move per head
            ordered moves {stay, right, left, to next separator, to start}; content move {just after the next
            position holding the same symbol as x_t}
  2. read   r_j = tape[h_j]
  3. update f(embed(x_t), onehot(registers), onehot(r_1..r_H)) -> new register values (K-way each) and the logits
            of the output token (the prediction of x_{t+1})

Discretisation: straight-through Gumbel-softmax while training (forward hard, backward soft), argmax in evaluation.
Head moves get a gradient path (CLAUDE.md C1-1): at every step the symbol under each of the 6 candidate moves is
read, and the read is the straight-through weighted sum of the 6 (forward = the chosen move's symbol, backward
through the soft move probabilities).  Head positions themselves are integers (no gradient).

Precise move semantics (the design names the moves; these are the exact definitions used, all causal -- a head
never reads beyond the current position t, so teacher-forced and autoregressive runs are the same machine):
  stay        h
  right       min(h + 1, t)
  left        max(h - 1, 0)
  next sep    the first p > h with p <= t and tape[p] in {+, =, |}; stay if none
  start       0
  content     p + 1 for the first p >= h with p < t and tape[p] == x_t; stay if none
Separators: +, =, |.  Initial size (pre-declared): R=4, K=16, H=3, controllers 2 hidden layers of 256.
Embedding width of embed(x_t): 64 (not fixed by the design; recorded in config).
"""
from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

MOVES = ("stay", "right", "left", "next_sep", "start", "content")


def mlp(i, h, o):
    return nn.Sequential(nn.Linear(i, h), nn.GELU(), nn.Linear(h, h), nn.GELU(), nn.Linear(h, o))


def candidates(tape, t, h, xt, issep):
    """candidate positions [B, H, 6] for heads at h [B, H] at step t (all <= t)"""
    B, T = tape.shape
    pos = torch.arange(T, device=tape.device)
    stay = h
    right = torch.clamp(h + 1, max=t)
    left = torch.clamp(h - 1, min=0)
    start = torch.zeros_like(h)
    vs = issep[:, None, :] & (pos[None, None, :] > h[:, :, None]) & (pos[None, None, :] <= t)
    nsep = torch.where(vs.any(-1), vs.float().argmax(-1), h)
    vc = (tape == xt[:, None])[:, None, :] & (pos[None, None, :] >= h[:, :, None]) & (pos[None, None, :] < t)
    cont = torch.where(vc.any(-1), vc.float().argmax(-1) + 1, h)
    return torch.stack([stay, right, left, nsep, start, cont], -1)


class PF(nn.Module):
    def __init__(self, vocab, R=4, K=16, H=3, hidden=256, emb=64, sep_ids=(), **_):
        super().__init__()
        self.kind = "pf"
        self.V, self.R, self.K, self.H = vocab, R, K, H
        self.emb = nn.Embedding(vocab, emb)
        din = emb + R * K + H * vocab
        self.g = mlp(din, hidden, H * len(MOVES))
        self.f = mlp(din, hidden, R * K + vocab)
        self.register_buffer("sep_ids", torch.tensor(list(sep_ids), dtype=torch.long), persistent=False)
        self.tau = 1.0
        self.debug = None                      # list: keeps per-step move / register logits for gradient tests

    def pick(self, logits):
        """straight-through Gumbel (training) or argmax one-hot (evaluation) over the last dim"""
        if self.training:
            return F.gumbel_softmax(logits, tau=self.tau, hard=True, dim=-1)
        return F.one_hot(logits.argmax(-1), logits.shape[-1]).to(logits.dtype)

    def forward(self, tokens, offset=None, recur=None, controller=None):
        """logits [B, T, V]: position t predicts token t + 1.  `controller` (hand-written rules, checks only)
        replaces g and f: controller.move(x, regs, prev_reads) -> [B, H, 6] one-hot,
        controller.update(x, regs, reads) -> (new regs [B, R, K] one-hot, output logits [B, V])."""
        B, T = tokens.shape
        dev = tokens.device
        issep = torch.isin(tokens, self.sep_ids)
        regs = torch.zeros(B, self.R, self.K, device=dev)
        regs[:, :, 0] = 1.0
        h = torch.zeros(B, self.H, dtype=torch.long, device=dev)
        reads = torch.zeros(B, self.H, self.V, device=dev)
        out = []
        for t in range(T):
            xt = tokens[:, t]
            e = self.emb(xt)
            if controller is None:
                ml = self.g(torch.cat([e, regs.flatten(1), reads.flatten(1)], -1)).view(B, self.H, len(MOVES))
                w = self.pick(ml)
            else:
                ml = None
                w = controller.move(xt, regs, reads)
            cand = candidates(tokens, t, h, xt, issep)                                 # [B, H, 6]
            sym = torch.gather(tokens[:, None, :].expand(B, self.H, T), 2, cand)       # [B, H, 6]
            reads = (w.unsqueeze(-1) * F.one_hot(sym, self.V).to(w.dtype)).sum(-2)    # ST weighted read
            h = torch.gather(cand, 2, w.argmax(-1, keepdim=True)).squeeze(-1)
            if controller is None:
                fo = self.f(torch.cat([e, regs.flatten(1), reads.flatten(1)], -1))
                rl = fo[:, :self.R * self.K].view(B, self.R, self.K)
                regs = self.pick(rl)
                logits = fo[:, self.R * self.K:]
            else:
                rl = None
                regs, logits = controller.update(xt, regs, reads)
            if self.debug is not None and ml is not None:
                ml.retain_grad()
                rl.retain_grad()
                self.debug.append((ml, rl))
            out.append(logits)
        return torch.stack(out, 1)


def pf_flops(cfg, B, T, V, train=False):
    """analytic FLOPs of B sequences of length T: the two controllers (dense matmuls), the 6-candidate reads (the
    straight-through weighted sum), the symbol / separator position index (one update per step, one lookup per
    head and indexed move, O(log T) comparisons).  Training = 3 x forward."""
    R, K, H, hid, emb = cfg["R"], cfg["K"], cfg["H"], cfg["hidden"], cfg["emb"]
    din = emb + R * K + H * V
    mm = 2 * (din * hid + hid * hid + hid * H * len(MOVES)) + 2 * (din * hid + hid * hid + hid * (R * K + V))
    reads = 2 * H * len(MOVES) * V
    index = 1 + 2 * H * math.ceil(math.log2(T + 1))
    fwd = B * T * (mm + reads + index)
    return {"total": 3 * fwd if train else fwd, "matmul": B * T * mm * (3 if train else 1),
            "reads": B * T * reads * (3 if train else 1), "index": B * T * index}
