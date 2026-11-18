"""C1-3 check before PF-search v2 (CLAUDE.md C1-3, CANDIDATE_DESIGN.md 12): does the loss score tell the hand-written
correct move table from the all-"stay" table?

Hand-written table (token-class table, the same 3 x 7 form the search explores):
  head 0: answer-phase token -> right; every other class -> stay      (sits on a_0, then walks a_1, a_2, ...)
  head 1: "+" -> next_sep (onto "+"); "=" -> right (onto b_0); answer-phase token -> right; others -> stay
  head 2: stay everywhere (unused)
With these moves the heads read a_i and b_i at the step that outputs c_i; past the end of an operand a head reads "+"
(head 0) or "=" (head 1) and then walks on, so an update controller must remember "operand exhausted" -- a flag set
by the first non-digit read.

  E  expressiveness: the PF machine with the table's moves and a hand-written update controller (registers: phase,
     carry, a-exhausted, b-exhausted) on the baseline evaluation sets (all examples): is it exact?  (shows the table
     is a correct algorithm for some update controller; not a learning result)
  S  scores: the PF-search v2 score (stage1/pf_search.py evaluate(score="loss"): 300 steps of update-controller
     training, then the in-distribution validation answer-token mean cross-entropy) of the two tables.
     Criterion, declared before running: the loss score distinguishes the two tables iff, at the search's seed
     (0), score(hand table) < score(all stay).  Seeds 1 and 2 are reported only (spread of the score), not used.
     If it does not distinguish them: no search; stop and report (CLAUDE.md C1-3).

  python stage1/pf_search_v2_check.py > stage1/results/c1_3_checks/pf_search_v2_check.json
"""
from __future__ import annotations
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks as T
import models as M
import run as R
import pf as PFM
import pf_search as PS

STAY, RIGHT, LEFT, NSEP, START, CONTENT = range(6)
C = {n: i for i, n in enumerate(PFM.CLASS_NAMES)}
HAND = [[STAY] * 7 for _ in range(3)]
HAND[0][C["answer_phase"]] = RIGHT
HAND[1][C["+"]] = NSEP
HAND[1][C["="]] = RIGHT
HAND[1][C["answer_phase"]] = RIGHT
ALL_STAY = [[STAY] * 7 for _ in range(3)]
DIG = {T.TOK[str(d)]: d for d in range(10)}


class TableController:
    """moves from the class table; registers r0 = phase (0 prompt, 2 answer), r1 = carry, r2 = a exhausted,
    r3 = b exhausted"""

    def __init__(self, table, cls, V, K):
        self.table, self.cls, self.V, self.K, self.t = torch.tensor(table), cls, V, K, 0

    def move(self, x, regs, prev):
        mv = self.table[:, self.cls[:, self.t]].T                                  # [B, H]
        self.t += 1
        return F.one_hot(mv, 6).float()

    def update(self, x, regs, reads):
        reg = regs.argmax(-1).tolist()
        rd = reads.argmax(-1).tolist()
        newr, outs = [], []
        for b in range(x.shape[0]):
            xi, r = int(x[b]), list(reg[b])
            o = T.EOS
            if xi == T.TOK["="] or r[0] == 2:
                r[0] = 2
                if rd[b][0] not in DIG:
                    r[2] = 1
                if rd[b][1] not in DIG:
                    r[3] = 1
                if r[2] and r[3]:
                    o = T.TOK["1"] if r[1] else T.EOS
                    r[1] = 0
                else:
                    s = (0 if r[2] else DIG[rd[b][0]]) + (0 if r[3] else DIG[rd[b][1]]) + r[1]
                    o, r[1] = T.TOK[str(s % 10)], s // 10
            newr.append(r)
            outs.append(o)
        return F.one_hot(torch.tensor(newr), self.K).float(), F.one_hot(torch.tensor(outs), self.V).float() * 100.0


class TableRuleModel(nn.Module):
    def __init__(self, pf, table):
        super().__init__()
        self.pf, self.table = pf, table

    def forward(self, tokens, offset=None, recur=None):
        c = self.pf.class_ids
        cls = PFM.token_classes(tokens, c["digits"], c["plus"], c["eq"], c["bar"], c["node_lo"], c["node_hi"])
        return PFM.PF.forward(self.pf, tokens, controller=TableController(self.table, cls, self.pf.V, self.pf.K))


def main():
    torch.set_num_threads(1)
    out = {"hand_table": {"head%d" % h: {PFM.CLASS_NAMES[c]: PFM.MOVES[HAND[h][c]] for c in range(7)}
                          for h in range(3)}}
    cfg = dict(M.SCALES["pf_search"]["1M"], policy=HAND)
    torch.manual_seed(0)
    pf = M.build("pf_search", len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    ev = T.eval_sets("addition", 1000, 500)
    with torch.no_grad():
        out["E_expressiveness_hand_table_with_hand_update_controller"] = {
            l: R.exact_match(TableRuleModel(pf, HAND), ex, "pf_search", cfg)[0] for l, ex in ev.items()}
    jobs = [(name, tab, seed) for seed in (0, 1, 2) for name, tab in (("hand", HAND), ("all_stay", ALL_STAY))]
    res = {}
    with cf.ProcessPoolExecutor(max_workers=int(os.environ.get("WORKERS", "3")),
                                mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(PS.evaluate, "addition", tab, seed, "loss"): (name, seed) for name, tab, seed in jobs}
        for fu in cf.as_completed(futs):
            name, seed = futs[fu]
            r = fu.result()
            res.setdefault(name, {})["seed%d" % seed] = {
                "val_loss": r["score"], "val_acc": r["val_acc"], "final_train_loss": r["final_loss"],
                "flops": r["flops"], "wall_s": r["wall_s"]}
    out["S_scores"] = res
    h0, s0 = res["hand"]["seed0"]["val_loss"], res["all_stay"]["seed0"]["val_loss"]
    out["criterion"] = "distinguishes iff score(hand) < score(all stay) at seed 0 (declared before running)"
    out["distinguishes"] = h0 < s0
    out["seed0_difference_all_stay_minus_hand"] = s0 - h0
    out["check_flops_total"] = sum(v["flops"] for d in res.values() for v in d.values())
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
