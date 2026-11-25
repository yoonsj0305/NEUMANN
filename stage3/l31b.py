"""3-1 after the first revision (stage3/DESIGN.md 6.10 and 6.11, which take precedence over 6.5-6.9).  The first
3-1a run (stage3/l31.py, results/3-1/3-1a/) is kept unchanged; this module reuses its data and machine helpers.

Changes against stage3/l31.py (6.10 numbering):
  1. teacher dependency = C3-3 content substitution (stage1/c3_compile.extract_substitution), not the gradient norm.
  2. positions t and t-1 are always covered (the student has x_t and the shift S): left out of the CP-SAT objective,
     added to the union in every coverage figure (oracle, hand, all-stay, synthesized alike).
  3. monotone routing candidates: Q = 1 solved with the all-stay hint; Q = k solved with the Q = k-1 candidate as
     hint (moved to a machine with one more, unused state); the candidate is the better of the two by
     synthesis-sample coverage (ties: the moved Q = k-1 candidate).  The hand program is never a hint.
  4. output state q' (Q' in 1..floor(4/Q)): routing fixed; CP-SAT over q'_t and delta'(q', q, kind(x_t), kinds read)
     minimising the (d) conflicts of the synthesis sample (key = 3-0 (d) key with the combined state (q, q') in
     place of q, at t and t-1 as the student sees it); ties: fewer q'-changing delta' cells; unused cells keep q'.
     The combined machine is an L1 program with Q x Q' <= 4 states (index q * Q' + q').  Q' is chosen by the (d)
     conflicts on the length 8-10 set against the key -> output table of the synthesis sample (6.11-1): conflicts
     inside the set + steps covered by that table with another output; uncovered steps are not counted (their
     share is recorded); fewest, ties the smaller Q'.
  5. correct read = (ii): some head reads the oracle supply position (steps without <eos>).  Also reported with the
     free positions t, t-1 counted as read (2); the check result is stopped on if the two disagree.
  6. MQAR t0 = the first query step (first '|' + 1) whatever the tokens after it (l1.first_scored patched for MQAR).
  6.11-4: (c') compares positions, segment bits and the combined state (q, q').

  gate1 --task T          check 1 (oracle, five tasks): routing Q 1-4, Q selection, q' synthesis, A1
  gate3 --task T          check 3 (rope seed 0 teacher, substitution dependency on the first 2,000)
  a1_30_mqar              3-0 A1 for MQAR again with the t0 fix (results/3-0/a1_mqar_t0fix/)
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np               # noqa: E402
import torch                     # noqa: E402

import l1                        # noqa: E402
import l31                       # noqa: E402

RES = pathlib.Path(os.environ.get("L31B_OUT", HERE / "results" / "3-1"))
GATE = RES / os.environ.get("L31B_GATE_DIR", "3-1a2")
CACHE = pathlib.Path(os.environ.get("L31_CACHE", "/tmp/l31_cache"))
H, KINDS, MOVES = l1.H, l1.KINDS, l1.MOVES
TIME_S = float(os.environ.get("L31_TIME", "600"))
W_DEP = 1000
HAND_Q = {"dup": 2, "interleave": 2, "repeat": 3, "pairswap": 3, "mqar": 2}
cpu_s = l31.cpu_s


def setup(task):
    l31.setup(task)
    if task == "mqar":                                         # 6.10-6: t0 = the first query step
        import tasks as T
        bar = T.TOK["|"]
        l1.first_scored = lambda tokens: (tokens == bar).float().argmax(1) + 1
        l1._t0_first_query = True


def env_info():
    e = l31.env_info()
    e["module"] = "stage3/l31b.py"
    e["cp_sat"]["max_time_in_seconds"] = TIME_S
    import h0a
    e["code"] = h0a.env(["stage3/l31b.py", "stage3/l31.py", "stage3/l1.py"])
    return e


# ---------------------------------------------------------------- dependency (6.10-1)
def rows_teacher_sub(task, run_dir, exs, ids, tag):
    """C3-3 content-substitution dependency of the judgment checkpoint on exs[ids]; cached"""
    import tasks as T
    import models as M
    import c3_compile as CC
    CACHE.mkdir(parents=True, exist_ok=True)
    cpath = CACHE / ("sub__%s.npz" % tag)
    if cpath.exists():
        z = np.load(cpath, allow_pickle=True)
        return z["rows"].item(), json.loads(str(z["info"]))
    ck = torch.load(pathlib.Path(run_dir) / "teacher_best.pt", weights_only=False)
    fin = json.loads((pathlib.Path(run_dir) / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    cfg = ck["cfg"]
    m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], cfg)
    m.load_state_dict(ck["model"])
    m.eval()
    t0, w0 = cpu_s(), time.time()
    rr, flops, xinfo = CC.extract_substitution(m, cfg, [exs[i] for i in ids])
    rows = {}
    for (k, t, s, _) in rr:
        rows.setdefault(ids[k], []).append((t, np.asarray(s)))
    for i in rows:
        rows[i].sort(key=lambda r: r[0])
    info = {"teacher_run": str(pathlib.Path(run_dir).resolve().relative_to(ROOT)), "teacher_step": ck["step"],
            "teacher_train_flops_to_judgment": ck["train_flops_cum"], "examples": len(ids),
            "dependency": "content substitution (stage1/c3_compile.extract_substitution, C3-3 change 1)",
            "extraction_flops": flops, "extraction_cpu_s": cpu_s() - t0, "extraction_wall_s": time.time() - w0,
            **xinfo}
    np.savez(cpath, rows=np.array(rows, dtype=object), info=json.dumps(info))
    return rows, info


# ---------------------------------------------------------------- coverage with the free positions (6.10-2)
def coverage(rows, ids, paths, free=True):
    tot, n = 0.0, 0
    for i in ids:
        P = paths[i]
        for t, w in rows[i]:
            pos = {int(P[h, t]) for h in range(H)}
            if free:
                pos |= {t} | ({t - 1} if t >= 1 else set())
            tot += sum(w[p] for p in pos)
            n += 1
    return tot / n


def covs(rows, syn, sel, ids_all, paths, free=True):
    return {"synthesis_sample": coverage(rows, syn, paths, free), "selection_8_10": coverage(rows, sel, paths, free),
            "all": coverage(rows, ids_all, paths, free)}


def paths_of(exs, ids, tens):
    return {i: v[2] for i, v in l31.batch_paths(exs, ids, tens).items()}


def embed(MU, DEL, Qn):
    """a program moved to a machine with Qn >= Q states (the new states unused)"""
    Q = MU.shape[1]
    MUe = torch.zeros(H, Qn, 7, dtype=torch.long)
    MUe[:, :Q] = MU
    DELe = torch.arange(Qn)[:, None, None, None, None].expand(Qn, 7, 7, 7, 7).clone()
    DELe[:Q] = DEL
    return MUe, DELe


def all_stay(Q=1):
    return torch.zeros(H, Q, 7, dtype=torch.long), torch.arange(Q)[:, None, None, None, None].expand(Q, 7, 7, 7, 7).clone()


# ---------------------------------------------------------------- routing synthesis (6.5 + 6.10-2, 3)
def synth_routing(exs, rows, syn_ids, Q, hint, time_s=TIME_S):
    """CP-SAT as stage3/l31.synthesize (table-encoded transitions) with the free positions left out of the
    objective and `hint` (MU, DEL with Q states) as the solution hint"""
    import tasks as T
    import pf as PFM
    import run as R
    from ortools.sat.python import cp_model
    t_start, c_start = time.time(), cpu_s()
    seps = torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]])
    data, kset = [], set()
    for i in syn_ids:
        tl = max(t for t, _ in rows[i])
        xb, _ = R.make_batch([exs[i]])
        x = xb[:, :tl + 1]
        cls = l1.kinds_of(x)[0].tolist()
        issep = torch.isin(x, seps)
        cand = [PFM.candidates(x, t, torch.arange(max(t, 1))[None, :], x[:, t], issep)[0].tolist() for t in range(tl + 1)]
        data.append((i, tl, cls, cand))
        kset |= set(cls)
    KX = KR = sorted(kset)
    R_ = len(KR)
    rmap = {k: j for j, k in enumerate(KR)}
    m = cp_model.CpModel()
    MU = {(h, q, k): m.NewIntVar(0, len(MOVES) - 1, "") for h in range(H) for q in range(Q) for k in KX}
    DEL = {(q, k, a): m.NewIntVar(0, Q - 1, "") for q in range(Q) for k in KX for a in range(R_ ** H)} if Q > 1 else {}
    cov_terms, var, n_rows = [], {}, 0
    for (i, tl, cls, cand) in data:
        q = m.NewConstant(0)
        prev = [None] * H
        rw = dict(rows[i])
        for t in range(tl + 1):
            kx = cls[t]
            ps, krs = [], []
            for h in range(H):
                if Q == 1:
                    mv = MU[(h, 0, kx)]
                else:
                    mv = m.NewIntVar(0, len(MOVES) - 1, "")
                    m.AddElement(q, [MU[(h, qq, kx)] for qq in range(Q)], mv)
                p = m.NewIntVar(0, t, "")
                if t == 0:
                    m.AddElement(mv, cand[0][0], p)
                else:
                    m.AddAllowedAssignments([prev[h], mv, p], [(pp, k, cand[t][pp][k]) for pp in range(len(cand[t]))
                                                               for k in range(len(MOVES))])
                kr = m.NewIntVar(0, R_ - 1, "")
                m.AddElement(p, [rmap[cls[j]] for j in range(t + 1)], kr)
                ps.append(p)
                krs.append(kr)
                prev[h] = p
            var[(i, t)] = (q, ps)
            if t in rw:
                n_rows += 1
                w = rw[t]
                for j in range(t + 1):
                    if j >= t - 1:                                     # free positions t, t-1 (6.10-2)
                        continue
                    wi = int(round(W_DEP * float(w[j])))
                    if wi <= 0:
                        continue
                    bs = []
                    for h in range(H):
                        b = m.NewBoolVar("")
                        m.Add(ps[h] == j).OnlyEnforceIf(b)
                        bs.append(b)
                    c = m.NewBoolVar("")
                    m.AddBoolOr(bs).OnlyEnforceIf(c)
                    cov_terms.append((wi, c))
            if Q > 1 and t < tl:
                idx2 = m.NewIntVar(0, Q * R_ ** H - 1, "")
                m.Add(idx2 == q * R_ ** H + sum(krs[h] * R_ ** (H - 1 - h) for h in range(H)))
                qn = m.NewIntVar(0, Q - 1, "")
                m.AddElement(idx2, [DEL[(qq, kx, a)] for qq in range(Q) for a in range(R_ ** H)], qn)
                q = qn
    ns = []
    for v in MU.values():
        b = m.NewBoolVar("")
        m.Add(v == 0).OnlyEnforceIf(b.Not())
        ns.append(b)
    ch = []
    for (qq, k, a), v in DEL.items():
        b = m.NewBoolVar("")
        m.Add(v == qq).OnlyEnforceIf(b.Not())
        ch.append(b)
    w_ns = len(ch) + 1
    big = (len(ns) + 1) * w_ns
    m.Maximize(big * sum(w * c for w, c in cov_terms) - w_ns * sum(ns) - sum(ch))
    hMU, hDEL = hint
    assert hMU.shape[1] == Q
    for (h, qq, k), v in MU.items():
        m.AddHint(v, int(hMU[h, qq, k]))
    for (qq, k, a), v in DEL.items():
        r = [KR[(a // R_ ** (H - 1 - h)) % R_] for h in range(H)]
        m.AddHint(v, int(hDEL[qq, k, r[0], r[1], r[2]]))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_s
    s.parameters.num_workers = 1
    s.parameters.random_seed = 0
    st = s.Solve(m)
    status = s.StatusName(st)
    assert status in ("OPTIMAL", "FEASIBLE"), status
    MU_t = torch.zeros(H, Q, 7, dtype=torch.long)
    for (h, qq, k), v in MU.items():
        MU_t[h, qq, k] = s.Value(v)
    DEL_t = torch.arange(Q)[:, None, None, None, None].expand(Q, 7, 7, 7, 7).clone()
    for (qq, k, a), v in DEL.items():
        r = [KR[(a // R_ ** (H - 1 - h)) % R_] for h in range(H)]
        DEL_t[qq, k, r[0], r[1], r[2]] = s.Value(v)
    sol = {i: (torch.tensor([[s.Value(var[(i, t)][1][h]) for t in range(tl + 1)] for h in range(H)]),
               torch.tensor([s.Value(var[(i, t)][0]) for t in range(tl + 1)])) for (i, tl, cls, cand) in data}
    used_mu, used_del = set(), set()                             # 6.9-2
    for (i, tl, cls, cand) in data:
        P, Qs = sol[i]
        for t in range(tl + 1):
            for h in range(H):
                used_mu.add((h, int(Qs[t]), cls[t]))
            if t < tl:
                used_del.add((int(Qs[t]), cls[t]) + tuple(cls[int(P[h, t])] for h in range(H)))
    MU_o = torch.zeros_like(MU_t)
    for key in used_mu:
        MU_o[key] = MU_t[key]
    DEL_o = torch.arange(Q)[:, None, None, None, None].expand(Q, 7, 7, 7, 7).clone()
    for key in used_del:
        DEL_o[key] = DEL_t[key]
    pp = l31.batch_paths(exs, syn_ids, (MU_o, DEL_o))             # 6.9-7 execution check
    same = sum(bool((pp[i][2][:, :tl + 1] == sol[i][0]).all()) and bool((pp[i][3][:tl + 1] == sol[i][1]).all())
               for (i, tl, cls, cand) in data)
    info = {"Q": Q, "status": status, "proved_optimal": status == "OPTIMAL", "objective": s.ObjectiveValue(),
            "bound": s.BestObjectiveBound(),
            "gap_relative": (s.BestObjectiveBound() - s.ObjectiveValue()) / max(1.0, abs(s.ObjectiveValue())),
            "rows": n_rows, "coverage_terms": len(cov_terms), "mu_cells": len(MU), "delta_cells": len(DEL),
            "kinds": [KINDS[k] for k in KX], "wall_s": time.time() - t_start, "cpu_s": cpu_s() - c_start,
            "time_limit_s": time_s, "workers": 1, "random_seed": 0,
            "exec_check_examples_equal": same / len(data)}
    return MU_o, DEL_o, info


def routing_candidates(exs, rows, syn, sel, ids_cov, ids_paths, prefix, d):
    """monotone candidates Q = 1..4 (6.10-3); files <prefix>_route_Q<k>.json in d; returns {Q: (MU, DEL, record)}"""
    cands = {}
    hint = all_stay(1)
    for Q in (1, 2, 3, 4):
        f = d / ("%s_route_Q%d.json" % (prefix, Q))
        if f.exists():
            MU, DEL, rec = l31.load_prog(f)
            cands[Q] = (MU, DEL, rec)
            hint = embed(MU, DEL, Q + 1)
            continue
        MUs, DELs, info = synth_routing(exs, rows, syn, Q, hint)
        assert info["exec_check_examples_equal"] == 1.0, "execution check failed (6.9-7): stop"
        ps_s = paths_of(exs, syn, (MUs, DELs))
        cov_solver = coverage(rows, syn, ps_s)
        if Q > 1:
            pe = paths_of(exs, syn, hint)
            cov_moved = coverage(rows, syn, pe)
        else:
            cov_moved = None
        use_solver = Q == 1 or cov_solver > cov_moved
        MU, DEL = (MUs, DELs) if use_solver else hint
        pa = paths_of(exs, ids_cov, (MU, DEL))
        rec = {"Q": Q, "solver": info, "candidate": "cp-sat" if use_solver else "moved Q-1 candidate",
               "coverage_synthesis_sample_cp_sat": cov_solver, "coverage_synthesis_sample_moved": cov_moved,
               "coverage": covs(rows, syn, sel, ids_cov, pa), "coverage_without_free": covs(rows, syn, sel, ids_cov, pa, False)}
        l31.save_prog(f, MU, DEL, rec)
        print(prefix, "Q", Q, info["status"], "cpu %.0f" % info["cpu_s"], rec["candidate"], "cov", rec["coverage"], flush=True)
        cands[Q] = (MU, DEL, json.loads(f.read_text()))
        hint = embed(MU, DEL, Q + 1)
    return cands


def select_routing(exs, ids_paths, cands):
    """dedup (paths equal to a smaller Q's on ids_paths) and selection by selection-set coverage (0.005)"""
    paths = {Q: paths_of(exs, ids_paths, (c[0], c[1])) for Q, c in cands.items()}
    dup_of = {}
    for Q in sorted(cands):
        for q2 in sorted(cands):
            if q2 < Q and q2 not in dup_of and all(bool((paths[Q][i] == paths[q2][i]).all()) for i in ids_paths):
                dup_of[Q] = q2
                break
    kept = [Q for Q in sorted(cands) if Q not in dup_of]
    sc = {Q: cands[Q][2]["coverage"]["selection_8_10"] for Q in kept}
    best = max(sc.values())
    pick = min(Q for Q in kept if sc[Q] >= best - 0.005)
    return pick, dup_of, kept


# ---------------------------------------------------------------- output state (6.10-4, 6.11-1)
def dkey_steps(exs, ids, tens, mv):
    """[(i, t, key, y)] over the scored steps; key = 3-0 (d) key with the machine's state"""
    import run as R
    out = []
    for j in range(0, len(ids), 128):
        bid = ids[j:j + 128]
        x, y = R.make_batch([exs[i] for i in bid])
        P, Qt = l1.l1_paths(x, None, tens)
        Bt = l1.segment_bits(x, P)
        for b, i in enumerate(bid):
            for t in (y[b] != -100).nonzero()[:, 0].tolist():
                k = (int(x[b, t]),) + tuple((int(x[b, P[b, h, t]]), int(Bt[b, h, t])) for h in mv) + (int(Qt[b, t]),)
                k += (int(x[b, t - 1]),) + tuple((int(x[b, P[b, h, t - 1]]), int(Bt[b, h, t - 1])) for h in mv) + (int(Qt[b, t - 1]),)
                out.append((i, t, k, int(y[b, t])))
    return out


def d_selection(exs, syn, sel, tens, mv):
    """6.11-1: table = synthesis-sample key -> output; on the selection set: conflicts inside the set + steps covered by
    the table with another output; uncovered steps not counted (share recorded)"""
    tab = {}
    for _, _, k, v in dkey_steps(exs, syn, tens, mv):
        tab.setdefault(k, v)
    own, inside, wrong, cov, n = {}, 0, 0, 0, 0
    for _, _, k, v in dkey_steps(exs, sel, tens, mv):
        n += 1
        if k in own and own[k] != v:
            inside += 1
        own.setdefault(k, v)
        if k in tab:
            cov += 1
            wrong += tab[k] != v
    return {"conflicts": inside + wrong, "inside_set": inside, "vs_synthesis_table": wrong, "key_coverage": cov / n,
            "scored_steps": n}


def combine(MU, DEL, Qp, DP):
    """routing (MU, DEL; Q states) + output state (DP [Qp, Q, 7, 7, 7, 7] -> next q') as one L1 program, state q*Qp+q'"""
    Q = MU.shape[1]
    Qc = Q * Qp
    MUc = torch.zeros(H, Qc, 7, dtype=torch.long)
    DELc = torch.zeros(Qc, 7, 7, 7, 7, dtype=torch.long)
    for q in range(Q):
        for qp in range(Qp):
            MUc[:, q * Qp + qp] = MU[:, q]
            DELc[q * Qp + qp] = DEL[q] * Qp + DP[qp, q]
    return MUc, DELc


def synth_output(exs, syn, MU, DEL, Qp, time_s=TIME_S):
    """CP-SAT for q' with the routing fixed; returns the combined program and info"""
    from ortools.sat.python import cp_model
    import run as R
    t_start, c_start = time.time(), cpu_s()
    Q = MU.shape[1]
    mv = l31.moving_t(MU)
    pp = l31.batch_paths(exs, syn, (MU, DEL))
    steps = dkey_steps(exs, syn, (MU, DEL), mv)
    m = cp_model.CpModel()
    ctx_ids, DP, qv = {}, {}, {}
    trans = []
    for i in syn:
        x, cls, P, Qt = pp[i]
        tl = max(t for (ii, t, _, _) in steps if ii == i)
        qv[(i, 0)] = m.NewConstant(0)
        for t in range(tl):
            c = (int(Qt[t]), int(cls[t])) + tuple(int(cls[int(P[h, t])]) for h in range(H))
            if c not in ctx_ids:
                ctx_ids[c] = len(ctx_ids)
                for a in range(Qp):
                    DP[(a, ctx_ids[c])] = m.NewIntVar(0, Qp - 1, "")
            qn = m.NewIntVar(0, Qp - 1, "")
            m.AddElement(qv[(i, t)], [DP[(a, ctx_ids[c])] for a in range(Qp)], qn)
            qv[(i, t + 1)] = qn
            trans.append((i, t, c))
    lits = {}
    for key, v in qv.items():
        if isinstance(v, int) or Qp == 1:
            continue
        bs = [m.NewBoolVar("") for _ in range(Qp)]
        for a, b in enumerate(bs):
            m.Add(v == a).OnlyEnforceIf(b)
            m.Add(v != a).OnlyEnforceIf(b.Not())
        lits[key] = bs
    V = max(y for (_, _, _, y) in steps) + 1
    outv, mism = {}, []
    for (i, t, k, y) in steps:
        mb = m.NewBoolVar("")
        mism.append(mb)
        for a in range(Qp):
            for b in range(Qp):
                key = (k, a, b)
                if key not in outv:
                    outv[key] = m.NewIntVar(0, V - 1, "")
                la = [] if (i, t - 1) not in lits else [lits[(i, t - 1)][a]]
                lb = [] if (i, t) not in lits else [lits[(i, t)][b]]
                if (i, t - 1) not in lits and a != 0:
                    continue
                if (i, t) not in lits and b != 0:
                    continue
                m.Add(outv[key] == y).OnlyEnforceIf(la + lb + [mb.Not()])
    ch = []
    for (a, c), v in DP.items():
        b = m.NewBoolVar("")
        m.Add(v == a).OnlyEnforceIf(b.Not())
        ch.append(b)
        m.AddHint(v, a)
    m.Minimize((len(ch) + 1) * sum(mism) + sum(ch))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_s
    s.parameters.num_workers = 1
    s.parameters.random_seed = 0
    st = s.Solve(m)
    status = s.StatusName(st)
    assert status in ("OPTIMAL", "FEASIBLE"), status
    qsol = {key: s.Value(v) for key, v in qv.items()}
    used = {(qsol[(i, t)], c) for (i, t, c) in trans}
    DPt = torch.arange(Qp)[:, None, None, None, None, None].expand(Qp, Q, 7, 7, 7, 7).clone()
    for (a, cid), v in DP.items():
        c = [cc for cc, j in ctx_ids.items() if j == cid][0]
        if (a, c) in used:
            DPt[(a,) + c] = s.Value(v)
    MUc, DELc = combine(MU, DEL, Qp, DPt)
    pc = l31.batch_paths(exs, syn, (MUc, DELc))                  # execution check: positions and q' as solved
    same = 0
    for i in syn:
        tl = max(t for (_, t) in qsol if _ == i)
        Qc = pc[i][3][:tl + 1]
        same += bool((pc[i][2] == pp[i][2]).all()) and all(int(Qc[t]) == int(pp[i][3][t]) * Qp + qsol[(i, t)] for t in range(tl + 1))
    info = {"Qp": Qp, "status": status, "proved_optimal": status == "OPTIMAL",
            "synthesis_sample_conflicts_solver": int(sum(s.Value(b) for b in mism)),
            "changing_delta_p_cells": int(sum(s.Value(b) for b in ch)), "contexts": len(ctx_ids),
            "keys": len({k for (_, _, k, _) in steps}), "steps": len(steps),
            "wall_s": time.time() - t_start, "cpu_s": cpu_s() - c_start, "time_limit_s": time_s,
            "exec_check_examples_equal": same / len(syn)}
    return MUc, DELc, info


def output_candidates(exs, syn, sel, MU, DEL, prefix, d):
    Q = MU.shape[1]
    mv = l31.moving_t(MU)
    res = {}
    for Qp in range(1, 4 // Q + 1):
        f = d / ("%s_out_Q%d_Qp%d.json" % (prefix, Q, Qp))
        if f.exists():
            MUc, DELc, rec = l31.load_prog(f)
        else:
            if Qp == 1:
                MUc, DELc, info = MU, DEL, {"Qp": 1, "status": "no output state"}
            else:
                MUc, DELc, info = synth_output(exs, syn, MU, DEL, Qp)
                assert info["exec_check_examples_equal"] == 1.0, "q' execution check failed: stop"
            rec = {"Q": Q, "Qp": Qp, "solver": info, "d_selection_8_10": d_selection(exs, syn, sel, (MUc, DELc), mv),
                   "d_synthesis_sample": d_selection(exs, syn, syn, (MUc, DELc), mv)}
            l31.save_prog(f, MUc, DELc, rec)
            rec = json.loads(f.read_text())
            print(prefix, "Q", Q, "Qp", Qp, "d sel", rec["d_selection_8_10"], flush=True)
        res[Qp] = (MUc, DELc, rec)
    sc = {Qp: r[2]["d_selection_8_10"]["conflicts"] for Qp, r in res.items()}
    pick = min(Qp for Qp in res if sc[Qp] == min(sc.values()))
    return pick, res


# ---------------------------------------------------------------- check 1 (oracle) with the revised A1
def a1(task, tens, mv):
    """(b), (c') with positions, bits and the combined state, correct read (ii) [strict and with t, t-1 as read],
    (d) with the combined state (3-0 definitions)"""
    import tasks as T
    import run as R
    prog_h = l1.PROGRAMS[task]
    tens_h = l1.program_tensors(prog_h)
    rng = random.Random("l30:causal:%s" % task)
    pool = sorted({T.TOK[d] for d in T.DIGITS} | {T.TOK[s] for s in ("+", "=", "|", "-", "*", "^")} | {T.EOS}
                  | ({T.TOK[v] for v in T.NODES} if task == "mqar" else set()))
    evs = T.eval_sets(task, 2000, 500)
    sets = {}
    for lab, ex in evs.items():
        caus = inv = n_sc = ok = ok_free = 0
        for j in range(0, len(ex), 128):
            chunk = ex[j:j + 128]
            x, y = R.make_batch(chunk)
            P, Qt = l1.l1_paths(x, None, tens)
            Ph, Qh = l1.l1_paths(x, None, tens_h)
            Bt = l1.segment_bits(x, P)
            t0 = l1.first_scored(x)
            x2 = x.clone()
            ts = []
            for b, e in enumerate(chunk):
                n = len(e[0]) + len(e[1])
                caus += bool((P[b, :, :n] <= torch.arange(n)[None, :]).all())
                t = rng.randint(int(t0[b]), n - 1)
                ts.append(t)
                for p in range(t + 1, n):
                    x2[b, p] = rng.choice(pool)
            P2, Q2 = l1.l1_paths(x2, None, tens)
            B2 = l1.segment_bits(x2, P2)
            for b, t in enumerate(ts):
                inv += (bool((P[b, :, :t + 1] == P2[b, :, :t + 1]).all()) and bool((Bt[b, :, :t + 1] == B2[b, :, :t + 1]).all())
                        and bool((Qt[b, :t + 1] == Q2[b, :t + 1]).all()))
            for b in range(x.shape[0]):
                for t in (y[b] != -100).nonzero()[:, 0].tolist():
                    if int(y[b, t]) == T.EOS:
                        continue
                    n_sc += 1
                    pos = int(Ph[b, prog_h["supply"][int(Qh[b, t])], t])
                    hit = any(int(P[b, hh, t]) == pos for hh in range(H))
                    ok += hit
                    ok_free += hit or pos in (t, t - 1)
        sets[lab] = {"examples": len(ex), "b_causal_p_le_t": caus / len(ex),
                     "c_prime_invariance_t_ge_t0_positions_bits_state": inv / len(ex),
                     "correct_read_ii": ok / n_sc, "correct_read_ii_free_t_t1": ok_free / n_sc,
                     "scored_steps_without_eos": n_sc}
        print(task, lab, sets[lab], flush=True)
    d = l1.d_check(task, lambda x: l1.l1_paths(x, None, tens), mv, evs, use_q=True)
    base = all(s["b_causal_p_le_t"] == 1.0 and s["c_prime_invariance_t_ge_t0_positions_bits_state"] == 1.0
               for s in sets.values()) and d["conflicts_0_everywhere"]
    return {"sets": sets, "d": d, "moving_heads": mv,
            "a1_all_strict": bool(base and all(s["correct_read_ii"] == 1.0 for s in sets.values())),
            "a1_all_free": bool(base and all(s["correct_read_ii_free_t_t1"] == 1.0 for s in sets.values()))}


def cmd_gate1(a):
    torch.set_num_threads(1)
    setup(a.task)
    GATE.mkdir(parents=True, exist_ok=True)
    exs, ns = l31.train_with_n(a.task, l1.SEED_DATA_A2, l31.N_ALL)
    syn, sel = l31.pick_sets(a.task, ns)
    ids_all = list(range(l31.N_ALL))
    rows = l31.rows_oracle(a.task, exs, ids_all)
    prefix = "oracle_%s" % a.task
    cands = routing_candidates(exs, rows, syn, sel, ids_all, ids_all, prefix, GATE)
    pick, dup_of, kept = select_routing(exs, ids_all, cands)
    MU, DEL, rec = cands[pick]
    qp, outs = output_candidates(exs, syn, sel, MU, DEL, prefix, GATE)
    MUc, DELc, orec = outs[qp]
    pc = paths_of(exs, ids_all, (MUc, DELc))
    cov = covs(rows, syn, sel, ids_all, pc)
    res = a1(a.task, (MUc, DELc), l31.moving_t(MUc))
    ok_cov = cov["synthesis_sample"] == 1.0
    out = {"check": "6.6-1 oracle recovery (6.10, 6.11)", "task": a.task,
           "routing": {Q: {"coverage": c[2]["coverage"], "candidate": c[2]["candidate"],
                           "solver": {k: c[2]["solver"][k] for k in ("status", "proved_optimal", "gap_relative", "cpu_s")},
                           "program": c[2]["program"]} for Q, c in cands.items()},
           "selected_Q": pick, "dedup_discarded": dup_of, "kept": kept,
           "output_state": {Qp: {"d_selection_8_10": r[2]["d_selection_8_10"], "d_synthesis_sample": r[2]["d_synthesis_sample"],
                                 "solver": r[2]["solver"]} for Qp, r in outs.items()},
           "selected_Qp": qp, "combined_states": int(MUc.shape[1]), "program": l31.prog_table(MUc, DELc),
           "oracle_coverage_free": cov, "coverage_1.000_on_synthesis_sample": ok_cov, "a1": res,
           "pass_strict": bool(ok_cov and res["a1_all_strict"]), "pass_free": bool(ok_cov and res["a1_all_free"]),
           "t0_rule": "first query step (6.10-6)" if a.task == "mqar" else "first '='", "env": env_info()}
    out["pass"] = out["pass_strict"] if out["pass_strict"] == out["pass_free"] else None
    (GATE / ("gate1_%s.json" % a.task)).write_text(json.dumps(out, indent=1, default=str))
    print(a.task, "gate1 Q", pick, "Qp", qp, "cov", cov, "pass strict/free", out["pass_strict"], out["pass_free"])


# ---------------------------------------------------------------- check 3 (teacher rope seed 0)
def cmd_gate3(a):
    torch.set_num_threads(1)
    setup(a.task)
    GATE.mkdir(parents=True, exist_ok=True)
    run_dir = HERE / "results" / "3-0" / ("l30_%s__rope__1M__s0__N100000" % a.task)
    exs, ns = l31.train_with_n(a.task, 0, l31.N_ALL)
    syn, sel = l31.pick_sets(a.task, ns)
    ids_all = list(range(l31.N_ALL))
    rows, info = rows_teacher_sub(a.task, run_dir, exs, ids_all, "%s__%s" % (a.task, run_dir.name))
    prefix = "teacher_%s" % a.task
    cands = routing_candidates(exs, rows, syn, sel, ids_all, ids_all, prefix, GATE)
    pick, dup_of, kept = select_routing(exs, ids_all, cands)
    hp = paths_of(exs, ids_all, l1.program_tensors(l1.PROGRAMS[a.task]))
    sp = paths_of(exs, ids_all, all_stay(1))
    hand = covs(rows, syn, sel, ids_all, hp)
    hand_nf = covs(rows, syn, sel, ids_all, hp, False)
    stay = covs(rows, syn, sel, ids_all, sp)
    stay_nf = covs(rows, syn, sel, ids_all, sp, False)
    hq = HAND_Q[a.task]
    got = cands[hq][2]["coverage"]["all"]
    thr = hand["all"] - 0.01
    per = {}
    for Q, c in cands.items():
        pa = paths_of(exs, ids_all, (c[0], c[1]))
        per[Q] = {"coverage": c[2]["coverage"], "coverage_without_free": c[2]["coverage_without_free"],
                  "candidate": c[2]["candidate"],
                  "solver": {k: c[2]["solver"][k] for k in ("status", "proved_optimal", "gap_relative", "cpu_s")},
                  "program": c[2]["program"],
                  "supply_agreement_without_eos": l31.supply_agreement(a.task, exs, ids_all, pa, False),
                  "supply_agreement_with_eos": l31.supply_agreement(a.task, exs, ids_all, pa, True)}
    out = {"check": "6.6-3 real teacher dependency (6.10-1/2/3 corrected threshold)", "task": a.task,
           "teacher": info, "hand_Q": hq, "hand_coverage": hand, "hand_coverage_without_free": hand_nf,
           "all_stay_coverage": stay, "all_stay_coverage_without_free": stay_nf,
           "hand_over_all_stay": {"with_free": hand["all"] / stay["all"] if stay["all"] > 0 else None,
                                  "without_free": hand_nf["all"] / stay_nf["all"] if stay_nf["all"] > 0 else None},
           "per_Q": per, "candidate_at_hand_Q_all_2000": got, "threshold": thr, "pass": bool(got >= thr),
           "time_limit_s": TIME_S, "selection_recorded": {"selected_Q": pick, "dedup_discarded": dup_of, "kept": kept},
           "env": env_info()}
    (GATE / ("gate3_%s.json" % a.task)).write_text(json.dumps(out, indent=1, default=str))
    print(a.task, "gate3 hand", hand, "stay", stay, "at hand Q", hq, got, "thr", thr, "pass", out["pass"])


def cmd_a1_30_mqar(a):
    """3-0 A1 for MQAR with the t0 fix; written to results/3-0/a1_mqar_t0fix/a1_mqar.json (the first stays)"""
    setup("mqar")
    l1.OUT = HERE / "results" / "3-0" / "a1_mqar_t0fix"
    l1.install = lambda task: None
    a.task = "mqar"
    l1.cmd_a1(a)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ("gate1", "gate3"):
        q = sp.add_parser(name)
        q.add_argument("--task", required=True)
    sp.add_parser("a1_30_mqar")
    a = p.parse_args()
    {"gate1": cmd_gate1, "gate3": cmd_gate3, "a1_30_mqar": cmd_a1_30_mqar}[a.cmd](a)


if __name__ == "__main__":
    main()
