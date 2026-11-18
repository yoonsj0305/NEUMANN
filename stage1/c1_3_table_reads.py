"""C1-3 description of a move table (not a learning result): at every answer step that outputs c_k, which operand
digit does each head read?  Share of (example, k) with k < operand length where head j reads a_k / b_k exactly.

  python stage1/c1_3_table_reads.py <search_result.json> > out.json
"""
from __future__ import annotations
import json
import sys
import os

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks as T
import pf as PFM
import run as R
from pf_search_v2_check import HAND


def reads_share(table, exs):
    x, _ = R.make_batch(exs)
    B, Tn = x.shape
    ids = dict(digits=torch.tensor([T.TOK[d] for d in T.DIGITS]), plus=T.TOK["+"], eq=T.TOK["="], bar=T.TOK["|"],
               node_lo=T.TOK[T.NODES[0]], node_hi=T.TOK[T.NODES[-1]] + 1)
    cls = PFM.token_classes(x, ids["digits"], ids["plus"], ids["eq"], ids["bar"], ids["node_lo"], ids["node_hi"])
    tab = torch.tensor(table)
    issep = torch.isin(x, torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]]))
    h = torch.zeros(B, 3, dtype=torch.long)
    pos = []
    for t in range(Tn):
        cand = PFM.candidates(x, t, h, x[:, t], issep)
        mv = tab[:, cls[:, t]].T
        h = torch.gather(cand, 2, mv.unsqueeze(-1)).squeeze(-1)
        pos.append(h.clone())
    cnt = {"a": [0, 0, 0], "b": [0, 0, 0]}
    n = {"a": 0, "b": 0}
    for i, (p, _) in enumerate(exs):
        la = p.index(T.TOK["+"])
        lb = len(p) - la - 2
        eq = len(p) - 1
        for k in range(max(la, lb)):
            t = eq + k                                     # the step whose output is c_k
            for name, ln, off in (("a", la, 0), ("b", lb, la + 1)):
                if k < ln:
                    n[name] += 1
                    for j in range(3):
                        cnt[name][j] += int(pos[t][i, j]) == off + k
    return {"head%d" % j: {"reads_a_k": cnt["a"][j] / n["a"], "reads_b_k": cnt["b"][j] / n["b"]} for j in range(3)}


if __name__ == "__main__":
    found = json.load(open(sys.argv[1]))["policy"]
    exs = T.train_set("addition", 500, 777)
    print(json.dumps({"found_table": reads_share(found, exs), "hand_table": reads_share(HAND, exs),
                      "data": "in-distribution validation set of the search (500, seed 777)"}, indent=1))
