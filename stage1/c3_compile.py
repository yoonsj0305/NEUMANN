"""C3-1 (CANDIDATE_DESIGN.md 13): Learn Soft, Compile Hard -- steps 2-4 of the pipeline for one task.

  2  Dependency extraction from the rope teacher (judgment checkpoint, `run.py --keep-best`), on the first 2,000
     examples of the teacher's training data (T.train_set(task, 100000, 0)).  For every output step t (a position
     whose next token is a target, i.e. the PF step that emits that target) and every input position i <= t:
       s_t(i) = || d(logit of the correct next token at t) / d(token embedding at position i) ||_2,
     normalised over i = 0..t to sum to 1 (main signal).  Auxiliary: the attention weights from query t to key i,
     averaged over layers and heads (recorded, never used for a decision).
  3' Pre-check (13.2): table score of the hand-written correct table vs the all-"stay" table.  Table score = mean
     over output steps of the dependency mass covered by the table's heads, heads taken in order and a position
     counted once (= the greedy-cover score below).  Pass iff score(correct) >= 2 x score(all stay); otherwise the
     task stops here (no compile).  The same comparison on attention weights is recorded only.
     "Correct table" = the hand-written PF rule controller's moves (stage1/pf_rules.py, exact on every bin in C1-1)
     written as a token-class table: addition -> the C1-3 table (stage1/pf_search_v2_check.HAND, exact with a
     hand-written update controller); parity -> the rule controller moves no head, so its table is all "stay".
  3  Compile (13.1-3): a table column = one head's moves for the 7 token classes (6^7 = 279,936 columns).  Every
     column's head path is simulated on the 2,000 inputs with the PF machine's own move code (pf.candidates).  Column
     score = mean over output steps of s_t(h_t), h_t = the position the head reads at step t.  Head 1 = the best
     column; heads 2 and 3 = the best column after zeroing, per output step, the dependency of the positions already
     read (greedy cover).  Ties: the first column in itertools.product order over (digit, +, =, |, node,
     answer-phase, other) with moves in pf.MOVES order -- i.e. "stay" wherever the score does not care.
     Columns that differ only on token classes absent from the 2,000 inputs have identical paths, so each distinct
     restriction to the present classes is simulated once and its score given to all its columns; the argmax is
     taken over all 279,936.  No answers, no reference alignment: inputs and dependencies only.  The overlap with
     the correct table's read positions is recorded as a reference (13.2), not used.
  FLOPs (13.3): extraction = one forward + one backward per distinct output position per batch (backward = 2 x
  forward), analytic rope forward FLOPs of the harness.  The table search is reported as head-simulation operations
  (head moves simulated + score look-ups), a separate column, not FLOPs.

  python stage1/c3_compile.py --task addition --teacher <run dir>/teacher_best.pt --out stage1/results/c3/addition_compile
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks as T
import models as M
import run as R
import pf as PFM

N_EX = 2000
BS = 200
NM, NC, H = len(PFM.MOVES), len(PFM.CLASS_NAMES), 3


def correct_table(task):
    if task == "addition":
        from pf_search_v2_check import HAND
        return [row[:] for row in HAND]
    if task == "parity":
        return [[0] * NC for _ in range(H)]
    raise SystemExit("no correct token-class table declared for %s" % task)


def teacher_forward(m, x):
    """the RopeLM forward written out (same ops as models.RopeBlock) so that the token embeddings are a leaf and the
    attention weights are available.  Returns (embedding leaf, logits, mean attention [B, T, T])"""
    e = m.tok(x).detach().requires_grad_(True)
    h = e
    B, Tn, D = h.shape
    hd = D // m.heads
    cos, sin = M.rope_tables(Tn, hd)
    mask = torch.ones(Tn, Tn, dtype=torch.bool).tril()
    att = torch.zeros(B, Tn, Tn)
    for b in m.blocks:
        q, k, v = b.qkv(b.ln1(h)).view(B, Tn, 3, b.heads, hd).permute(2, 0, 3, 1, 4)
        q = q * cos + M._rotate_half(q) * sin
        k = k * cos + M._rotate_half(k) * sin
        w = ((q @ k.transpose(-1, -2)) / math.sqrt(hd)).masked_fill(~mask, float("-inf")).softmax(-1)
        att = att + w.detach().mean(1) / len(m.blocks)
        a = w @ v
        h = h + b.proj(a.transpose(1, 2).reshape(B, Tn, D))
        h = h + b.mlp(b.ln2(h))
    return e, m.head(m.ln(h)), att


def extract(m, cfg, exs):
    """dependency rows: list over output steps of (example index, t, s_t(0..t), attention_t(0..t)); FLOPs"""
    rows, flops, n_bwd_total = [], 0, 0
    order = sorted(range(len(exs)), key=lambda i: len(exs[i][0]) + len(exs[i][1]))
    maxdiff = 0.0
    for c0 in range(0, len(order), BS):
        idx = order[c0:c0 + BS]
        x, y = R.make_batch([exs[i] for i in idx])
        e, logits, att = teacher_forward(m, x)
        with torch.no_grad():
            maxdiff = max(maxdiff, float((logits - m(x)).abs().max()))
        ts = [t for t in range(x.shape[1]) if bool((y[:, t] != -100).any())]
        for t in ts:
            valid = y[:, t] != -100
            obj = logits[valid, t].gather(1, y[valid, t].unsqueeze(1)).sum()
            g = torch.autograd.grad(obj, e, retain_graph=True)[0]          # [B, T, D]
            s = g.norm(dim=-1)                                              # [B, T]
            for b in valid.nonzero().flatten().tolist():
                r = s[b, :t + 1].double()
                rows.append((idx[b], t, (r / r.sum()).numpy(), att[b, t, :t + 1].double().numpy()))
        fwd = R.fwd_flops("rope", cfg, x.shape[0], x.shape[1], len(T.VOCAB))
        flops += fwd * (1 + 2 * len(ts))
        n_bwd_total += len(ts)
    return rows, flops, n_bwd_total, maxdiff


def class_ids():
    return dict(digits=torch.tensor([T.TOK[d] for d in T.DIGITS]), plus=T.TOK["+"], eq=T.TOK["="], bar=T.TOK["|"],
                node_lo=T.TOK[T.NODES[0]], node_hi=T.TOK[T.NODES[-1]] + 1)


def simulate(exs, rows, columns):
    """read positions [n_columns, n_rows] of one head following each column (list of 7 moves), at every output step
    in `rows`; and the number of head moves simulated (valid steps only)"""
    cols = torch.tensor(columns)                                               # [C, 7]
    C = cols.shape[0]
    want = {}
    for r, (i, t, _, _) in enumerate(rows):
        want.setdefault(i, []).append((t, r))
    out = torch.zeros(C, len(rows), dtype=torch.int32)
    ci = class_ids()
    seps = torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]])
    n_moves = 0
    ex_ids = sorted(want)
    for c0 in range(0, len(ex_ids), 100):
        ids = ex_ids[c0:c0 + 100]
        x, _ = R.make_batch([exs[i] for i in ids])
        B, Tn = x.shape
        last = torch.tensor([max(t for t, _ in want[i]) for i in ids])
        cls = PFM.token_classes(x, ci["digits"], ci["plus"], ci["eq"], ci["bar"], ci["node_lo"], ci["node_hi"])
        issep = torch.isin(x, seps)
        h = torch.zeros(B, C, dtype=torch.long)
        tmax = int(last.max())
        rec = {}
        for t in range(tmax + 1):
            cand = PFM.candidates(x, t, h, x[:, t], issep)                    # [B, C, 6]
            mv = cols[:, cls[:, t]].T                                           # [B, C]
            h = torch.gather(cand, 2, mv.unsqueeze(-1)).squeeze(-1)
            rec[t] = h.clone()
            n_moves += int((last >= t).sum()) * C
        for bi, i in enumerate(ids):
            for t, r in want[i]:
                out[:, r] = rec[t][bi].to(torch.int32)
    return out, n_moves


def present_classes(exs, rows):
    ci = class_ids()
    last = {}
    for i, t, _, _ in rows:
        last[i] = max(last.get(i, -1), t)
    seen = set()
    for i, lt in last.items():
        x, _ = R.make_batch([exs[i]])
        cls = PFM.token_classes(x, ci["digits"], ci["plus"], ci["eq"], ci["bar"], ci["node_lo"], ci["node_hi"])
        seen |= set(cls[0, :lt + 1].tolist())
    return sorted(seen)


def dense(rows, which):
    """[n_rows, Tmax] matrix of the normalised dependency (which=2) or attention (which=3) rows, zero-padded"""
    tm = max(len(r[2]) for r in rows)
    S = np.zeros((len(rows), tm))
    for k, r in enumerate(rows):
        S[k, :len(r[which])] = r[which]
    return S


def table_score(S, paths):
    """greedy-cover score of a table whose heads read `paths` (list of [n_rows] position arrays), in head order:
    per head the mean covered mass after zeroing positions already read; returns (total, per-head list)"""
    S = S.copy()
    ar = np.arange(S.shape[0])
    per = []
    for p in paths:
        per.append(float(S[ar, p].mean()))
        S[ar, p] = 0.0
    return sum(per), per


def main(a):
    t0 = time.time()
    torch.set_num_threads(int(os.environ.get("THREADS", "1")))
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    ck = torch.load(a.teacher, weights_only=False)
    cfg = ck["cfg"]
    m = M.build("rope", len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    m.load_state_dict(ck["model"])
    m.eval()
    exs = T.train_set(a.task, 100000, 0)[:N_EX]
    rows, ext_flops, n_bwd, maxdiff = extract(m, cfg, exs)
    torch.save({"rows": rows}, os.path.join(out, "dependency_rows.pt"))      # local only (gitignored)
    S, A = dense(rows, 2), dense(rows, 3)
    ar = np.arange(len(rows))
    tpos = np.array([r[1] for r in rows])
    res = {"task": a.task, "teacher": {"path": a.teacher, "step": ck["step"], "acc": ck["acc"],
                                       "train_flops_to_judgment": ck["train_flops_cum"]},
           "examples": N_EX, "output_steps": len(rows),
           "extraction": {"flops": ext_flops, "backward_passes": n_bwd,
                          "manual_forward_max_abs_logit_diff": maxdiff},
           "dependency_mass_on_current_position": float(S[ar, tpos].mean()),
           "attention_mass_on_current_position": float(A[ar, tpos].mean())}
    # pre-check (13.2)
    corr = correct_table(a.task)
    stay = [[0] * NC for _ in range(H)]
    pc, _ = simulate(exs, rows, corr)
    ps, _ = simulate(exs, rows, stay)
    pc, ps = pc.numpy(), ps.numpy()
    c_dep, c_dep_h = table_score(S, list(pc))
    s_dep, s_dep_h = table_score(S, list(ps))
    c_att, _ = table_score(A, list(pc))
    s_att, _ = table_score(A, list(ps))
    passed = c_dep >= 2 * s_dep
    res["precheck"] = {"correct_table": {"head%d" % j: {PFM.CLASS_NAMES[c]: PFM.MOVES[corr[j][c]] for c in range(NC)}
                                         for j in range(H)},
                       "dependency": {"correct": c_dep, "correct_per_head": c_dep_h, "all_stay": s_dep,
                                      "ratio": c_dep / s_dep if s_dep > 0 else None},
                       "attention_aux": {"correct": c_att, "all_stay": s_att,
                                         "ratio": c_att / s_att if s_att > 0 else None},
                       "criterion": "score(correct) >= 2 x score(all stay) on the dependency (13.2)",
                       "passed": bool(passed)}
    if not passed:
        res["stopped"] = "pre-check not passed: no compile (13.2)"
        res["wall_s"] = round(time.time() - t0, 1)
        json.dump(res, open(os.path.join(out, "compile_result.json"), "w"), indent=1)
        print(json.dumps(res, indent=1))
        return
    # compile (13.1-3)
    pres = present_classes(exs, rows)
    combos = list(itertools.product(range(NM), repeat=len(pres)))
    cols = []
    for cmb in combos:
        col = [0] * NC
        for c, mv in zip(pres, cmb):
            col[c] = mv
        cols.append(col)
    P, n_moves = simulate(exs, rows, cols)
    P = P.numpy()
    allcols = list(itertools.product(range(NM), repeat=NC))                     # 279,936, product order
    weights = [NM ** (len(pres) - 1 - k) for k in range(len(pres))]
    to_combo = np.array([sum(col[c] * w for c, w in zip(pres, weights)) for col in allcols])
    Sg = S.copy()
    chosen, per_head = [], []
    for j in range(H):
        sc = Sg[ar[None, :], P].mean(1)                                          # [n_combos]
        full = sc[to_combo]
        best = int(np.argmax(full))                                             # first maximum in product order
        col = list(allcols[best])
        chosen.append(col)
        k = int(to_combo[best])
        per_head.append({"column": {PFM.CLASS_NAMES[c]: PFM.MOVES[col[c]] for c in range(NC)},
                         "score_after_cover": float(full[best]),
                         "columns_tied_at_best": int((full == full[best]).sum())})
        Sg[ar, P[k]] = 0.0
    pcomp = [P[int(to_combo[allcols.index(tuple(c))])] for c in chosen]
    tot, _ = table_score(S, pcomp)
    tot_att, _ = table_score(A, pcomp)
    agree = {}
    for j in range(H):                                                          # reference only (13.2)
        agree["correct_head%d_position_read_by_some_compiled_head" % j] = float(
            np.mean(np.any(np.stack(pcomp) == pc[j][None, :], axis=0)))
    res.update({
        "policy": chosen,
        "policy_named": {"head%d" % j: per_head[j]["column"] for j in range(H)},
        "per_head": per_head, "table_score_dependency": tot, "table_score_attention_aux": tot_att,
        "search": {"columns": len(allcols), "present_classes": [PFM.CLASS_NAMES[c] for c in pres],
                   "distinct_paths_simulated": len(cols), "head_moves_simulated": n_moves,
                   "score_lookups": H * len(cols) * len(rows),
                   "head_simulation_operations": n_moves + H * len(cols) * len(rows)},
        "reference_agreement_with_correct_table": agree,
        "wall_s": round(time.time() - t0, 1)})
    json.dump(res, open(os.path.join(out, "compile_result.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    p.add_argument("--teacher", required=True)
    p.add_argument("--out", required=True)
    main(p.parse_args())
