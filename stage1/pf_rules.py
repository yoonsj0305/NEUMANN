"""Hand-written controllers for the PF expressiveness check (CLAUDE.md C1-1, task 1b): the learned g and f are
replaced by fixed rules; the machine (moves, reads, causality, registers) is the PF code itself.  This checks that
the machine is implemented correctly and that the answer is representable -- it is not a learning result.

Register use: reg0 = phase, reg1 = carry / parity.  Heads: head 0 (and head 1 for addition)."""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F

import tasks as T

STAY, RIGHT, LEFT, NSEP, START, CONTENT = range(6)
DIG = {T.TOK[str(d)]: d for d in range(10)}
SEPS = {T.TOK["+"], T.TOK["="], T.TOK["|"]}
NODE = set(T.TOK[n] for n in T.NODES)


class Rules:
    def __init__(self, task, H, R, K, V):
        self.task, self.H, self.R, self.K, self.V = task, H, R, K, V

    def _onehot_moves(self, mv):
        return F.one_hot(torch.tensor(mv), 6).float()

    def move(self, x, regs, prev):
        B = x.shape[0]
        reg = regs.argmax(-1)                                     # [B, R]
        pr = [[(int(prev[b, j].argmax()) if float(prev[b, j].sum()) > 0 else -1) for j in range(self.H)]
              for b in range(B)]
        out = []
        for b in range(B):
            xi, ph = int(x[b]), int(reg[b, 0])
            mv = [STAY] * self.H
            if self.task == "addition":
                if ph == 0 and xi == T.TOK["+"]:
                    mv[1] = NSEP                                  # head 1 onto '+'
                elif ph == 1:
                    mv[1] = RIGHT                                 # head 1 onto b_0
                elif ph == 2:
                    for j in (0, 1):
                        mv[j] = STAY if pr[b][j] in SEPS else RIGHT
            elif self.task in ("mqar", "mqar_n4"):
                if ph == 1 and xi in NODE:
                    mv[0] = CONTENT                               # just after the key equal to the query
                elif ph == 1 and xi in DIG:
                    mv[0] = START
            out.append(mv)
        return self._onehot_moves(out)

    def update(self, x, regs, reads):
        B = x.shape[0]
        reg = regs.argmax(-1).tolist()
        rd = reads.argmax(-1).tolist()
        newr, outs = [], []
        for b in range(B):
            xi = int(x[b])
            r = list(reg[b])
            ph = r[0]
            o = T.EOS
            if self.task == "addition":
                if xi == T.TOK["="] or ph == 2:
                    a, c = rd[b][0], rd[b][1]
                    if a in SEPS and c in SEPS:
                        o = T.TOK["1"] if r[1] else T.EOS
                        r[1] = 0
                    else:
                        s = DIG.get(a, 0) + DIG.get(c, 0) + r[1]
                        o, r[1] = T.TOK[str(s % 10)], s // 10
                if xi == T.TOK["+"]:
                    r[0] = 1
                elif ph == 1:
                    r[0] = 3
                if xi == T.TOK["="]:
                    r[0] = 2
            elif self.task == "parity":
                if xi == T.TOK["="]:
                    o, r[0] = T.TOK[str(r[1])], 2
                elif ph != 2 and xi in DIG:
                    r[1] ^= DIG[xi]
            else:                                                 # MQAR
                if ph == 1 and xi in NODE:
                    o = rd[b][0]                                  # the value under head 0
                if xi == T.TOK["|"]:
                    r[0] = 1
            newr.append(r)
            outs.append(o)
        regs_new = F.one_hot(torch.tensor(newr), self.K).float()
        logits = F.one_hot(torch.tensor(outs), self.V).float() * 100.0
        return regs_new, logits


class RuleModel(nn.Module):
    """the PF machine driven by hand-written rules, with the harness's model interface"""

    def __init__(self, pf, task):
        super().__init__()
        self.pf = pf
        self.rules = Rules(task, pf.H, pf.R, pf.K, pf.V)

    def forward(self, tokens, offset=None, recur=None):
        return self.pf(tokens, controller=self.rules)
