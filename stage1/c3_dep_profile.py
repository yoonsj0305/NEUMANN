"""C3-2 description (not a learning result): where the addition teacher's normalised input-gradient dependency sits
at the output steps -- mean s_t(position) over output steps for a_k, b_k (k = the answer digit being emitted, when
k < operand length), the "+" and "=" positions and the current position.  Reads the local dependency_rows.pt of a
compile directory.   python stage1/c3_dep_profile.py <compile dir> <data seed>"""
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks as T

d, seed = sys.argv[1], int(sys.argv[2])
rows = torch.load(os.path.join(d, "dependency_rows.pt"), weights_only=False)["rows"]
exs = T.train_set("addition", 100000, seed)[:2000]
acc = {"a_k": [], "b_k": [], "plus": [], "eq": [], "current": []}
for i, t, s, _ in rows:
    p = exs[i][0]
    la = p.index(T.TOK["+"])
    lb = len(p) - la - 2
    k = t - (len(p) - 1)
    if k < la:
        acc["a_k"].append(s[k])
    if k < lb:
        acc["b_k"].append(s[la + 1 + k])
    acc["plus"].append(s[la])
    acc["eq"].append(s[len(p) - 1])
    acc["current"].append(s[t])
print(json.dumps({k: float(np.mean(v)) for k, v in acc.items()}))
