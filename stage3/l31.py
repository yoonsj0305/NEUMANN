"""3-1: automatic L1 synthesis from input dependencies (stage3/DESIGN.md 6.5-6.7; 6.9 takes precedence).

Synthesis (6.5, 6.9):
  * program (Q, mu, delta) of the L1 machine (stage3/l1.py: l1_paths), H = 3 heads, Q = 1, 2, 3, 4 separately.
  * objective: dependency covered by the union of the heads' read positions at every output step (rows of
    stage1/c3_compile.py: one per scored step, <eos> included), weights round(1000 x normalised dependency);
    lexicographic tie-breaks with weights below the coverage resolution: fewer non-stay mu cells, then fewer
    state-changing delta cells.
  * CP-SAT (OR-Tools), 1 worker, random_seed 0, 600 s per (source, Q).  Integer variables + element constraints
    (6.9-7): head positions, states, kinds of the reads; candidate positions precomputed with pf.candidates exactly as
    l1_paths does.  Variables only for the kinds present in the synthesis sample (other cells: stay / keep q).
  * synthesis sample: the first 100 examples of length 1-7 (pairswap 2-6) of the data; selection set: the first 300
    of length 8-10 (6.9-1).  After solving, mu cells not used on the synthesis sample -> stay, delta cells -> keep q
    (6.9-2).  Execution check: l1_paths on the overwritten program == the solver's paths and states on the whole
    sample (1.000, else stop; 6.9-7).
  * dedup (6.5): a Q = k solution whose read paths equal a smaller Q's on all of the first 2,000 is discarded.
  * Q selection (6.9-1): coverage on the selection set; within 0.005 the smaller Q.

  synth --source {oracle,l0,teacher} --task T [--table i] [--teacher-run DIR] --Q k   one solve -> json
  gate1 / gate2 / gate3                                                                  the 3-1a checks (6.6)
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import resource
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

OUT = pathlib.Path(os.environ.get("L31_OUT", HERE / "results" / "3-1"))
CACHE = pathlib.Path(os.environ.get("L31_CACHE", "/tmp/l31_cache"))
H = l1.H
KINDS, MOVES = l1.KINDS, l1.MOVES
N_SYN, N_SEL, N_ALL = 100, 300, 2000
TIME_S = float(os.environ.get("L31_TIME", "600"))
W_DEP = 1000
ENC = os.environ.get("L31_ENC", "table")


def cpu_s():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


# ---------------------------------------------------------------- data
def setup(task):
    if task in l1.C1_TASKS:
        import c0a
        c0a.install(task)
    else:
        l1.install(task)


def train_with_n(task, seed, k):
    """the first k examples of tasks.train_set(task, 100000, seed) with their length n (same rng sequence)"""
    import tasks as T
    rng = random.Random("train:%s:%d" % (task, seed))
    lo, hi = T.SPEC[task]["train"]
    out = []
    for _ in range(k):
        if task in T.MQAR:
            n = rng.randint(lo, hi)
            out.append((T.encode_mqar(*T.mqar(n, rng)), n))
        else:
            d = T.draw(task, rng, lo, hi, train_dist=True)
            out.append((T.encode(*d[:2]), d[2]))
    ref = T.train_set(task, 100000, seed)[:k]
    assert [e for e, _ in out] == ref, "length replay differs from train_set"
    return [e for e, _ in out], [n for _, n in out]


def pick_sets(task, ns):
    hi_syn = 6 if task == "pairswap" else 7
    syn = [i for i, n in enumerate(ns) if n <= hi_syn][:N_SYN]
    sel = [i for i, n in enumerate(ns) if 8 <= n <= 10][:N_SEL]
    assert len(syn) == N_SYN and len(sel) == N_SEL, (len(syn), len(sel))
    return syn, sel


def batch_paths(exs, ids, tens, bs=100):
    """{i: (x [T], cls [T], P [H, T], Qt [T])} on the unpadded length of each example"""
    import run as R
    out = {}
    for j in range(0, len(ids), bs):
        bid = ids[j:j + bs]
        x, _ = R.make_batch([exs[i] for i in bid])
        P, Qt = l1.l1_paths(x, None, tens)
        cls = l1.kinds_of(x)
        for b, i in enumerate(bid):
            n = len(exs[i][0]) + len(exs[i][1])
            out[i] = (x[b, :n], cls[b, :n], P[b, :, :n], Qt[b, :n])
    return out


def scored_steps(exs, ids):
    import run as R
    out = {}
    for j in range(0, len(ids), 200):
        bid = ids[j:j + 200]
        x, y = R.make_batch([exs[i] for i in bid])
        for b, i in enumerate(bid):
            out[i] = [(t, int(y[b, t])) for t in (y[b] != -100).nonzero()[:, 0].tolist()]
    return out


# ---------------------------------------------------------------- dependency rows {i: [(t, weights[0..t])]}
def rows_oracle(task, exs, ids):
    """hand program's output-supply position, one-hot; <eos> step: the supply head (by state) read position (6.9-3)"""
    prog = l1.PROGRAMS[task]
    tens = l1.program_tensors(prog)
    pp = batch_paths(exs, ids, tens)
    sc = scored_steps(exs, ids)
    rows = {}
    for i in ids:
        _, _, P, Qt = pp[i]
        rows[i] = []
        for t, _ in sc[i]:
            w = np.zeros(t + 1)
            w[int(P[prog["supply"][int(Qt[t])], t])] = 1.0
            rows[i].append((t, w))
    return rows


def rows_l0(table, exs, ids):
    """one-hot of the table's moving heads' positions, the moving heads equally weighted (6.6-2)"""
    import c1a
    import run as R
    mv = c1a.moving(table)
    sc = scored_steps(exs, ids)
    rows = {}
    for j in range(0, len(ids), 100):
        bid = ids[j:j + 100]
        x, _ = R.make_batch([exs[i] for i in bid])
        P = c1a.read_paths(x, table)
        for b, i in enumerate(bid):
            rows[i] = []
            for t, _ in sc[i]:
                w = np.zeros(t + 1)
                for h in mv:
                    w[int(P[b, h, t])] += 1.0 / len(mv)
                rows[i].append((t, w))
    return rows


def rows_teacher(task, run_dir, exs, ids, tag):
    """C3 gradient dependency of the teacher's judgment checkpoint (c3_compile.extract) on exs[ids]; cached"""
    import tasks as T
    import models as M
    import c3_compile as CC
    CACHE.mkdir(parents=True, exist_ok=True)
    cpath = CACHE / ("%s.npz" % tag)
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
    t0 = cpu_s()
    rr, flops, n_bwd, maxdiff = CC.extract(m, cfg, [exs[i] for i in ids])
    rows = {}
    for (k, t, s, _) in rr:
        rows.setdefault(ids[k], []).append((t, np.asarray(s)))
    for i in rows:
        rows[i].sort(key=lambda r: r[0])
    info = {"teacher_run": str(pathlib.Path(run_dir).resolve().relative_to(ROOT)), "teacher_step": ck["step"],
            "teacher_train_flops_to_judgment": ck["train_flops_cum"], "examples": len(ids),
            "extraction_flops": flops, "backward_passes": n_bwd, "manual_forward_max_abs_logit_diff": maxdiff,
            "extraction_cpu_s": cpu_s() - t0}
    np.savez(cpath, rows=np.array(rows, dtype=object), info=json.dumps(info))
    return rows, info


def coverage(rows, ids, paths, heads=None):
    """mean over the output steps of the dependency mass on the union of the heads' read positions"""
    tot, n = 0.0, 0
    for i in ids:
        P = paths[i]
        for t, w in rows[i]:
            pos = {int(P[h, t]) for h in (range(H) if heads is None else heads)}
            tot += sum(w[p] for p in pos)
            n += 1
    return tot / n


# ---------------------------------------------------------------- CP-SAT synthesis
def synthesize(exs, rows, syn_ids, Q, time_s=TIME_S):
    import tasks as T
    import pf as PFM
    from ortools.sat.python import cp_model
    t_start, c_start = time.time(), cpu_s()
    seps = torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]])
    data = []
    kx_set, kr_set = set(), set()
    for i in syn_ids:
        tl = max(t for t, _ in rows[i])
        import run as R
        xb, _ = R.make_batch([exs[i]])
        x = xb[:, :tl + 1]
        cls = l1.kinds_of(x)[0].tolist()
        issep = torch.isin(x, seps)
        cand = []
        for t in range(tl + 1):
            L = max(t, 1)
            hh = torch.arange(L)[None, :]
            c = PFM.candidates(x, t, hh, x[:, t], issep)[0]                 # [L, 6]: prior position -> move
            cand.append(c.tolist())
        data.append((i, tl, cls, cand))
        kx_set |= set(cls)
        kr_set |= set(cls)
    KX = sorted(kx_set)
    KR = sorted(kr_set)
    R_ = len(KR)
    rmap = {k: j for j, k in enumerate(KR)}
    m = cp_model.CpModel()
    MU = {(h, q, k): m.NewIntVar(0, len(MOVES) - 1, "mu%d_%d_%d" % (h, q, k)) for h in range(H) for q in range(Q)
          for k in KX}
    DEL = {}
    if Q > 1:
        for q in range(Q):
            for k in KX:
                for a in range(R_ ** H):
                    DEL[(q, k, a)] = m.NewIntVar(0, Q - 1, "d%d_%d_%d" % (q, k, a))
    cov_terms = []
    var = {}
    n_rows = 0
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
                p = m.NewIntVar(0, t, "p%d_%d_%d" % (i, h, t))
                flat = [c for row in cand[t] for c in row]
                if t == 0:
                    m.AddElement(mv, cand[0][0], p)
                elif ENC == "table":
                    m.AddAllowedAssignments([prev[h], mv, p], [(pp, k, cand[t][pp][k]) for pp in range(len(cand[t]))
                                                               for k in range(len(MOVES))])
                else:
                    idx = m.NewIntVar(0, len(flat) - 1, "")
                    m.Add(idx == prev[h] * len(MOVES) + mv)
                    m.AddElement(idx, flat, p)
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
                qn = m.NewIntVar(0, Q - 1, "q%d_%d" % (i, t + 1))
                m.AddElement(idx2, [DEL[(qq, kx, a)] for qq in range(Q) for a in range(R_ ** H)], qn)
                q = qn
    ns = []
    for key, v in MU.items():
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
    covexpr = sum(w * c for w, c in cov_terms)
    m.Maximize(big * covexpr - w_ns * sum(ns) - sum(ch))
    # search (implementation, 6.9-7): branch on the table cells first (paths and states then follow by propagation);
    # hint = the all-stay / keep-q program (always feasible)
    tab = [MU[k] for k in sorted(MU)] + [DEL[k] for k in sorted(DEL)]
    mode = os.environ.get("L31_SEARCH", "default")
    if mode in ("fixed", "strategy"):
        m.AddDecisionStrategy(tab, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)
    for k in sorted(MU):
        m.AddHint(MU[k], 0)
    for k in sorted(DEL):
        m.AddHint(DEL[k], k[0])
    s = cp_model.CpSolver()
    if mode == "fixed":
        s.parameters.search_branching = cp_model.FIXED_SEARCH
    s.parameters.max_time_in_seconds = time_s
    s.parameters.num_workers = 1
    s.parameters.random_seed = 0
    st = s.Solve(m)
    status = s.StatusName(st)
    assert status in ("OPTIMAL", "FEASIBLE"), status
    MU_t = torch.zeros(H, Q, len(KINDS), dtype=torch.long)
    for (h, qq, k), v in MU.items():
        MU_t[h, qq, k] = s.Value(v)
    DEL_t = torch.arange(Q)[:, None, None, None, None].expand(Q, 7, 7, 7, 7).clone()
    for (qq, k, a), v in DEL.items():
        r = [(a // R_ ** (H - 1 - h)) % R_ for h in range(H)]
        DEL_t[qq, k, KR[r[0]], KR[r[1]], KR[r[2]]] = s.Value(v)
    sol = {}
    for (i, tl, cls, cand) in data:
        sol[i] = (torch.tensor([[s.Value(var[(i, t)][1][h]) for t in range(tl + 1)] for h in range(H)]),
                  torch.tensor([s.Value(var[(i, t)][0]) for t in range(tl + 1)]))
    # 6.9-2: cells not used on the synthesis sample -> stay / keep q
    used_mu, used_del = set(), set()
    for (i, tl, cls, cand) in data:
        P, Qs = sol[i]
        for t in range(tl + 1):
            for h in range(H):
                used_mu.add((h, int(Qs[t]), cls[t]))
            if t < tl:
                used_del.add((int(Qs[t]), cls[t]) + tuple(cls[int(P[h, t])] for h in range(H)))
    MU_o = torch.zeros_like(MU_t)
    for (h, qq, k) in used_mu:
        MU_o[h, qq, k] = MU_t[h, qq, k]
    DEL_o = torch.arange(Q)[:, None, None, None, None].expand(Q, 7, 7, 7, 7).clone()
    for key in used_del:
        DEL_o[key] = DEL_t[key]
    # 6.9-7 execution check on the overwritten program
    pp = batch_paths(exs, syn_ids, (MU_o, DEL_o))
    same = 0
    for (i, tl, cls, cand) in data:
        P, Qs = sol[i]
        same += bool((pp[i][2][:, :tl + 1] == P).all()) and bool((pp[i][3][:tl + 1] == Qs).all())
    cov_val = sum(w * s.Value(c) for w, c in cov_terms)
    info = {"Q": Q, "status": status, "proved_optimal": status == "OPTIMAL",
            "objective": s.ObjectiveValue(), "bound": s.BestObjectiveBound(),
            "gap_relative": (s.BestObjectiveBound() - s.ObjectiveValue()) / max(1.0, abs(s.ObjectiveValue())),
            "coverage_int": cov_val, "coverage_int_bound": s.BestObjectiveBound() / big,
            "coverage_rounded_mean": cov_val / (W_DEP * n_rows),
            "coverage_rounded_mean_bound": s.BestObjectiveBound() / big / (W_DEP * n_rows),
            "rows": n_rows, "nonstay_mu_cells_solver": int(sum(s.Value(b) for b in ns)),
            "changing_delta_cells_solver": int(sum(s.Value(b) for b in ch)),
            "kinds_x": [KINDS[k] for k in KX], "kinds_read": [KINDS[k] for k in KR],
            "mu_cells": len(MU), "delta_cells": len(DEL), "coverage_terms": len(cov_terms),
            "wall_s": time.time() - t_start, "cpu_s": cpu_s() - c_start, "time_limit_s": time_s,
            "workers": 1, "random_seed": 0,
            "used_mu_cells": len(used_mu), "used_delta_cells": len(used_del),
            "exec_check_examples_equal": same / len(data)}
    return MU_o, DEL_o, info


def prog_table(MU, DEL):
    """readable program: non-stay mu cells and non-keep delta cells"""
    Q = MU.shape[1]
    mu = {"head%d" % h: {"q%d %s" % (q, KINDS[k]): MOVES[int(MU[h, q, k])] for q in range(Q) for k in range(7)
                         if int(MU[h, q, k]) != 0} for h in range(H)}
    dl = []
    for idx in (DEL != torch.arange(Q)[:, None, None, None, None]).nonzero().tolist():
        q, k, a, b, c = idx
        dl.append({"q": q, "kind_x": KINDS[k], "reads": [KINDS[a], KINDS[b], KINDS[c]], "next": int(DEL[q, k, a, b, c])})
    return {"Q": Q, "mu_non_stay": mu, "delta_non_keep": dl, "moving_heads": moving_t(MU)}


def moving_t(MU):
    return [h for h in range(H) if bool((MU[h] != 0).any())]


def save_prog(path, MU, DEL, extra):
    d = dict(extra)
    d["program"] = prog_table(MU, DEL)
    d["MU"] = MU.tolist()
    d["DEL_nonkeep"] = d["program"]["delta_non_keep"]
    path.write_text(json.dumps(d, indent=1))


def load_prog(path):
    d = json.loads(pathlib.Path(path).read_text())
    MU = torch.tensor(d["MU"], dtype=torch.long)
    Q = MU.shape[1]
    DEL = torch.arange(Q)[:, None, None, None, None].expand(Q, 7, 7, 7, 7).clone()
    for c in d["DEL_nonkeep"]:
        DEL[c["q"], KINDS.index(c["kind_x"]), KINDS.index(c["reads"][0]), KINDS.index(c["reads"][1]),
            KINDS.index(c["reads"][2])] = c["next"]
    return MU, DEL, d


def env_info():
    import h0a
    import ortools
    e = h0a.env(["stage3/l31.py", "stage3/l1.py"])
    e["ortools"] = ortools.__version__
    e["cp_sat"] = {"num_workers": 1, "random_seed": 0, "max_time_in_seconds": TIME_S}
    return e


# ---------------------------------------------------------------- shared: per-source data and rows
def source_data(a):
    """(exs, syn, sel, ids_all, rows over ids_all, meta) for one source"""
    setup(a.task)
    if a.source == "oracle":
        seed = l1.SEED_DATA_A2
    elif a.source == "l0":
        import c1
        seed = c1.compiled(a.task, a.table)["data_seed"]
    else:
        seed = json.loads((pathlib.Path(a.teacher_run) / "final.json").read_text())["seed"]
    exs, ns = train_with_n(a.task, seed, N_ALL)
    syn, sel = pick_sets(a.task, ns)
    ids_all = list(range(N_ALL))
    meta = {"data": "tasks.train_set(%s, 100000, %d)" % (a.task, seed), "data_seed": seed,
            "synthesis_sample": {"rule": "first %d with length %s" % (N_SYN, "2-6" if a.task == "pairswap" else "<= 7"),
                                 "indices_max": max(syn), "lengths": sorted(set(ns[i] for i in syn))},
            "selection_set": {"rule": "first %d with length 8-10" % N_SEL, "indices_max": max(sel)},
            "all": "first %d" % N_ALL}
    if a.source == "oracle":
        rows = rows_oracle(a.task, exs, ids_all)
    elif a.source == "l0":
        import c1
        rows = rows_l0(c1.compiled(a.task, a.table)["policy"], exs, ids_all)
    else:
        tag = "%s__%s" % (a.task, pathlib.Path(a.teacher_run).name)
        rows, info = rows_teacher(a.task, a.teacher_run, exs, ids_all, tag)
        meta["teacher"] = info
    return exs, syn, sel, ids_all, rows, meta


def src_name(a):
    if a.source == "oracle":
        return "oracle_%s" % a.task
    if a.source == "l0":
        return "l0_%s_table%d" % (a.task, a.table)
    return "teacher_%s" % pathlib.Path(a.teacher_run).name


def cmd_deps(a):
    torch.set_num_threads(1)
    exs, syn, sel, ids_all, rows, meta = source_data(a)
    print(json.dumps(meta.get("teacher", {})))


def cmd_synth(a):
    torch.set_num_threads(1)
    exs, syn, sel, ids_all, rows, meta = source_data(a)
    MU, DEL, info = synthesize(exs, rows, syn, a.Q)
    pp = batch_paths(exs, ids_all, (MU, DEL))
    paths = {i: v[2] for i, v in pp.items()}
    cov = {"synthesis_sample": coverage(rows, syn, paths), "selection_8_10": coverage(rows, sel, paths),
           "all_2000": coverage(rows, ids_all, paths)}
    d = OUT / "3-1a" if a.stage == "gate" else OUT
    d.mkdir(parents=True, exist_ok=True)
    out = d / ("synth_%s_Q%d.json" % (src_name(a), a.Q))
    save_prog(out, MU, DEL, {"source": a.source, "task": a.task, "table": a.table, "meta": meta, "solver": info,
                             "coverage": cov, "env": env_info()})
    print(src_name(a), "Q", a.Q, info["status"], "cov", cov, "exec", info["exec_check_examples_equal"],
          "cpu %.0f" % info["cpu_s"], flush=True)
    assert info["exec_check_examples_equal"] == 1.0, "execution check failed (6.9-7): stop"


def select_q(task, exs, ids_all, sols):
    """dedup (paths equal to a smaller Q's on all 2,000) and selection by selection-set coverage (0.005 -> smaller Q)"""
    paths = {}
    for Q, (MU, DEL, d) in sorted(sols.items()):
        pp = batch_paths(exs, ids_all, (MU, DEL))
        paths[Q] = {i: v[2] for i, v in pp.items()}
    dup_of = {}
    for Q in sorted(sols):
        for q2 in sorted(sols):
            if q2 < Q and q2 not in dup_of and all(bool((paths[Q][i] == paths[q2][i]).all()) for i in ids_all):
                dup_of[Q] = q2
                break
    kept = [Q for Q in sorted(sols) if Q not in dup_of]
    best = max(sols[Q][2]["coverage"]["selection_8_10"] for Q in kept)
    pick = min(Q for Q in kept if sols[Q][2]["coverage"]["selection_8_10"] >= best - 0.005)
    return pick, dup_of, kept, paths


def supply_agreement(task, exs, ids, paths, with_eos):
    """fraction of output steps whose hand-program supply position (6.9-3 at <eos>) is read by some head"""
    prog = l1.PROGRAMS[task]
    hp = batch_paths(exs, ids, l1.program_tensors(prog))
    sc = scored_steps(exs, ids)
    import tasks as T
    n = ok = 0
    for i in ids:
        _, _, P, Qt = hp[i]
        for t, y in sc[i]:
            if not with_eos and y == T.EOS:
                continue
            pos = int(P[prog["supply"][int(Qt[t])], t])
            n += 1
            ok += any(int(paths[i][h, t]) == pos for h in range(H))
    return ok / n


# ---------------------------------------------------------------- A1 on a synthesized program (6.6-1)
def a1_synth(task, tens, syn_exs_paths):
    """(b), (c') t >= t0, correct read, (d) on T.eval_sets(task, 2000, 500).  Correct read in two forms: (i) the
    supply head per state taken from the synthesis sample (the smallest head that reads the hand supply position at
    every non-eos scored step of that state); (ii) some head reads the hand supply position (= oracle coverage
    without <eos>).  Both are reported."""
    import tasks as T
    import run as R
    MU, DEL = tens
    mv = moving_t(MU)
    prog_h = l1.PROGRAMS[task]
    tens_h = l1.program_tensors(prog_h)
    supply = syn_exs_paths
    rng = random.Random("l30:causal:%s" % task)
    pool = sorted({T.TOK[d] for d in T.DIGITS} | {T.TOK[s] for s in ("+", "=", "|", "-", "*", "^")} | {T.EOS}
                  | ({T.TOK[v] for v in T.NODES} if task == "mqar" else set()))
    evs = T.eval_sets(task, 2000, 500)
    sets = {}
    for lab, ex in evs.items():
        caus = inv = n_sc = ok_i = ok_ii = 0
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
                    h = supply.get(int(Qt[b, t]))
                    ok_i += h is not None and int(x[b, P[b, h, t]]) == int(y[b, t])
                    pos = int(Ph[b, prog_h["supply"][int(Qh[b, t])], t])
                    ok_ii += any(int(P[b, hh, t]) == pos for hh in range(H))
        sets[lab] = {"examples": len(ex), "b_causal_p_le_t": caus / len(ex),
                     "c_prime_invariance_t_ge_t0_positions_bits_q": inv / len(ex),
                     "correct_read_i_supply_head_by_state": ok_i / n_sc,
                     "correct_read_ii_hand_supply_position_read": ok_ii / n_sc, "scored_steps_without_eos": n_sc}
        print(task, lab, sets[lab], flush=True)
    d = l1.d_check(task, lambda x: l1.l1_paths(x, None, tens), mv, evs, use_q=True)
    base = all(s["b_causal_p_le_t"] == 1.0 and s["c_prime_invariance_t_ge_t0_positions_bits_q"] == 1.0
               for s in sets.values()) and d["conflicts_0_everywhere"]
    ok_i = base and all(s["correct_read_i_supply_head_by_state"] == 1.0 for s in sets.values())
    ok_ii = base and all(s["correct_read_ii_hand_supply_position_read"] == 1.0 for s in sets.values())
    return {"sets": sets, "d": d, "moving_heads": mv, "supply_head_by_state_from_sample": supply,
            "a1_all_with_correct_read_i": ok_i, "a1_all_with_correct_read_ii": ok_ii}


def supply_heads_from_sample(task, exs, syn, tens):
    import tasks as T
    prog_h = l1.PROGRAMS[task]
    hp = batch_paths(exs, syn, l1.program_tensors(prog_h))
    sp = batch_paths(exs, syn, tens)
    sc = scored_steps(exs, syn)
    cand = {}
    for i in syn:
        _, _, Ph, Qh = hp[i]
        _, _, P, Qt = sp[i]
        for t, y in sc[i]:
            if y == T.EOS:
                continue
            pos = int(Ph[prog_h["supply"][int(Qh[t])], t])
            ok = {h for h in range(H) if int(P[h, t]) == pos}
            q = int(Qt[t])
            cand[q] = cand[q] & ok if q in cand else ok
    return {q: min(v) for q, v in cand.items() if v}, {q: sorted(v) for q, v in cand.items()}


def load_sols(prefix, d):
    sols = {}
    for Q in (1, 2, 3, 4):
        p = d / ("synth_%s_Q%d.json" % (prefix, Q))
        if p.exists():
            MU, DEL, dd = load_prog(p)
            sols[Q] = (MU, DEL, dd)
    return sols


def cmd_gate1(a):
    """6.6-1 oracle recovery"""
    torch.set_num_threads(1)
    a.source, a.table = "oracle", None
    exs, syn, sel, ids_all, rows, meta = source_data(a)
    d = OUT / "3-1a"
    sols = load_sols("oracle_%s" % a.task, d)
    assert sorted(sols) == [1, 2, 3, 4], sorted(sols)
    pick, dup_of, kept, paths = select_q(a.task, exs, ids_all, sols)
    MU, DEL, dd = sols[pick]
    cov = dd["coverage"]
    supply, supply_all = supply_heads_from_sample(a.task, exs, syn, (MU, DEL))
    a1 = a1_synth(a.task, (MU, DEL), supply)
    cov_ok = cov["synthesis_sample"] == 1.0
    res = {"check": "6.6-1 oracle recovery", "task": a.task, "selected_Q": pick, "dedup_discarded": dup_of,
           "per_Q": {Q: {"coverage": sols[Q][2]["coverage"], "solver": {k: sols[Q][2]["solver"][k] for k in
                                                                         ("status", "proved_optimal", "gap_relative", "cpu_s", "coverage_rounded_mean", "coverage_rounded_mean_bound")},
                         "program": sols[Q][2]["program"]} for Q in sorted(sols)},
           "selected_program": dd["program"], "selected_coverage": cov, "coverage_1.000_on_synthesis_sample": cov_ok,
           "supply_heads_from_sample_candidates": supply_all, "a1": a1,
           "pass_correct_read_i": bool(cov_ok and a1["a1_all_with_correct_read_i"]),
           "pass_correct_read_ii": bool(cov_ok and a1["a1_all_with_correct_read_ii"]), "meta": meta, "env": env_info()}
    res["pass"] = res["pass_correct_read_i"] if res["pass_correct_read_i"] == res["pass_correct_read_ii"] else None
    (d / ("gate1_%s.json" % a.task)).write_text(json.dumps(res, indent=1, default=str))
    print(a.task, "gate1 selected Q", pick, "cov", cov, "pass (i, ii)", res["pass_correct_read_i"], res["pass_correct_read_ii"])


def cmd_gate2(a):
    """6.6-2 L0 regression: Q = 1 on the table's one-hot; coverage 1.000; output-step read positions equal as sets"""
    torch.set_num_threads(1)
    import c1
    import c1a
    import run as R
    a.source = "l0"
    d = OUT / "3-1a"
    res = {"check": "6.6-2 L0 regression", "task": a.task, "tables": {}}
    for i in (1, 2, 3):
        a.table, a.Q = i, 1
        exs, syn, sel, ids_all, rows, meta = source_data(a)
        p = d / ("synth_%s_Q1.json" % src_name(a))
        MU, DEL, dd = load_prog(p)
        table = c1.compiled(a.task, i)["policy"]
        mv_t, mv_s = c1a.moving(table), moving_t(MU)
        pp = batch_paths(exs, ids_all, (MU, DEL))
        sc = scored_steps(exs, ids_all)
        eq = {}
        for lab, ids in (("synthesis_sample", syn), ("selection_8_10", sel), ("all_2000", ids_all)):
            n = ok = 0
            for j in range(0, len(ids), 100):
                bid = ids[j:j + 100]
                x, _ = R.make_batch([exs[k] for k in bid])
                P0 = c1a.read_paths(x, table)
                for b, k in enumerate(bid):
                    for t, _ in sc[k]:
                        n += 1
                        ok += {int(P0[b, h, t]) for h in mv_t} == {int(pp[k][2][h, t]) for h in mv_s}
            eq[lab] = ok / n
        cov = dd["coverage"]
        passed = all(v == 1.0 for v in cov.values()) and all(v == 1.0 for v in eq.values())
        res["tables"]["table%d" % i] = {"source": str(c1.SRC[a.task][i - 1].relative_to(ROOT)), "policy": table,
                                        "moving_heads_table": mv_t, "synthesized": dd["program"],
                                        "coverage": cov, "read_positions_equal_as_sets": eq,
                                        "solver": dd["solver"], "pass": passed, "meta": meta}
        print(a.task, i, "cov", cov, "sets equal", eq, "pass", passed, flush=True)
    res["pass"] = all(v["pass"] for v in res["tables"].values())
    res["env"] = env_info()
    (d / ("gate2_%s.json" % a.task)).write_text(json.dumps(res, indent=1, default=str))


def cmd_gate3(a):
    """6.6-3 real teacher (3-0 B rope seed 0): best Q coverage on the 2,000 >= hand coverage - 0.01"""
    torch.set_num_threads(1)
    a.source, a.table = "teacher", None
    a.teacher_run = str(HERE / "results" / "3-0" / ("l30_%s__rope__1M__s0__N100000" % a.task))
    exs, syn, sel, ids_all, rows, meta = source_data(a)
    d = OUT / "3-1a"
    sols = load_sols(src_name(a), d)
    assert sorted(sols) == [1, 2, 3, 4], sorted(sols)
    hp = batch_paths(exs, ids_all, l1.program_tensors(l1.PROGRAMS[a.task]))
    hpaths = {i: v[2] for i, v in hp.items()}
    hand = {"synthesis_sample": coverage(rows, syn, hpaths), "selection_8_10": coverage(rows, sel, hpaths),
            "all_2000": coverage(rows, ids_all, hpaths)}
    pick, dup_of, kept, paths = select_q(a.task, exs, ids_all, sols)
    evs = None
    per = {}
    for Q in sorted(sols):
        MU, DEL, dd = sols[Q]
        import tasks as T
        evs = evs or T.eval_sets(a.task, 2000, 500)
        dchk = l1.d_check(a.task, lambda x: l1.l1_paths(x, None, (MU, DEL)), moving_t(MU), evs, use_q=True)
        per[Q] = {"coverage": dd["coverage"], "program": dd["program"],
                  "solver": {k: dd["solver"][k] for k in ("status", "proved_optimal", "gap_relative", "cpu_s",
                                                         "coverage_rounded_mean", "coverage_rounded_mean_bound")},
                  "supply_agreement_all_2000_without_eos": supply_agreement(a.task, exs, ids_all, paths[Q], False),
                  "supply_agreement_all_2000_with_eos": supply_agreement(a.task, exs, ids_all, paths[Q], True),
                  "d_conflicts_recorded": {s: v["conflicts_within_set"] + v["covered_steps_vs_train_table_wrong"]
                                           for s, v in dchk["sets"].items()},
                  "d_train_conflicts": dchk["train_conflicts"]}
        print(a.task, "Q", Q, json.dumps({k: per[Q][k] for k in ("coverage", "supply_agreement_all_2000_without_eos",
                                                                    "d_conflicts_recorded")}), flush=True)
    best = max(per[Q]["coverage"]["all_2000"] for Q in per)
    b30 = json.loads((HERE / "results" / "3-0" / ("b_%s.json" % a.task)).read_text())
    res = {"check": "6.6-3 real teacher dependency", "task": a.task, "teacher": meta.get("teacher"),
           "hand_coverage": hand, "hand_coverage_3_0_B": b30["hand_program"]["coverage"], "per_Q": per,
           "best_coverage_all_2000": best, "threshold": hand["all_2000"] - 0.01,
           "pass": bool(best >= hand["all_2000"] - 0.01),
           "selection_recorded": {"selected_Q": pick, "dedup_discarded": dup_of, "kept": kept}, "meta": meta,
           "env": env_info()}
    (d / ("gate3_%s.json" % a.task)).write_text(json.dumps(res, indent=1, default=str))
    print(a.task, "gate3 hand", hand, "best", best, "pass", res["pass"], "selected Q", pick)


# ---------------------------------------------------------------- 3-1 main run (6.7 with 6.9)
TEACHER_SEEDS = (41, 42, 43)
BASE30 = HERE / "results" / "3-0"


def teacher_dir(task, seed):
    return OUT / ("l31_%s__rope__1M__s%d__N100000" % (task, seed))


def cmd_teacher_check(a):
    """6.9-6 / G-0' 7.12: in-distribution exact match of the judgment checkpoint on select:<task> (1,000); >= 0.95"""
    setup(a.task)
    import tasks as T
    import models as M
    import run as R
    import c4_select as CS
    torch.set_num_threads(1)
    d = teacher_dir(a.task, a.seed)
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
    m.load_state_dict(ck["model"])
    sel = CS.selection_set(a.task)
    with torch.no_grad():
        acc, fl = R.exact_match(m, sel, "rope", ck["cfg"])
    out = {"task": a.task, "run_seed": a.seed, "run": d.name, "judgment_step": ck["step"],
           "selection_set": {"generation_seed": "select:%s" % a.task, "size": len(sel)}, "selection_accuracy": acc,
           "threshold": 0.95, "passed": acc >= 0.95, "selection_eval_flops": fl,
           "judgment_train_flops": fin["judgment"]["train_flops_cum"], "judgment_wall_train_s": fin["judgment"]["wall_train_s_cum"]}
    (OUT / ("teacher_select_%s_s%d.json" % (a.task, a.seed))).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("task", "run_seed", "selection_accuracy", "passed")}))


def used_teacher(task, s):
    """the teacher of teacher seed s: s if it passed its check, else s + 200 (None if both failed)"""
    for seed in (s, s + 200):
        p = OUT / ("teacher_select_%s_s%d.json" % (task, seed))
        if p.exists() and json.loads(p.read_text())["passed"]:
            return seed
    return None


def choice_path(task, s):
    return OUT / ("choice_%s_t%d.json" % (task, s))


def cmd_choose(a):
    """dedup + Q selection (6.9-1) on the synthesized candidates of teacher seed s; record coverages and agreements"""
    torch.set_num_threads(1)
    seed = used_teacher(a.task, a.seed)
    a.source, a.table, a.teacher_run = "teacher", None, str(teacher_dir(a.task, seed))
    exs, syn, sel, ids_all, rows, meta = source_data(a)
    sols = load_sols(src_name(a), OUT)
    assert sorted(sols) == [1, 2, 3, 4], sorted(sols)
    pick, dup_of, kept, paths = select_q(a.task, exs, ids_all, sols)
    hp = batch_paths(exs, ids_all, l1.program_tensors(l1.PROGRAMS[a.task]))
    hpaths = {i: v[2] for i, v in hp.items()}
    hand = {"synthesis_sample": coverage(rows, syn, hpaths), "selection_8_10": coverage(rows, sel, hpaths),
            "all_2000": coverage(rows, ids_all, hpaths)}
    per = {Q: {"coverage": sols[Q][2]["coverage"], "program": sols[Q][2]["program"],
               "solver": {k: sols[Q][2]["solver"][k] for k in ("status", "proved_optimal", "gap_relative", "cpu_s",
                                                               "coverage_rounded_mean", "coverage_rounded_mean_bound",
                                                               "exec_check_examples_equal")},
               "supply_agreement_all_2000_without_eos": supply_agreement(a.task, exs, ids_all, paths[Q], False),
               "supply_agreement_all_2000_with_eos": supply_agreement(a.task, exs, ids_all, paths[Q], True)}
           for Q in sorted(sols)}
    MU, DEL, dd = sols[pick]
    res = {"task": a.task, "teacher_seed": a.seed, "teacher_run_seed": seed, "selected_Q": pick,
           "dedup_discarded": dup_of, "kept": kept,
           "rule": "selection-set (length 8-10, first 300) coverage; within 0.005 the smaller Q (6.9-1)",
           "per_Q": per, "hand_coverage_same_dependency": hand, "meta": meta, "MU": MU.tolist(),
           "DEL_nonkeep": dd["DEL_nonkeep"], "program": dd["program"],
           "synthesis_cpu_s_total": sum(sols[Q][2]["solver"]["cpu_s"] for Q in sols), "env": env_info()}
    choice_path(a.task, a.seed).write_text(json.dumps(res, indent=1, default=str))
    print(a.task, a.seed, "selected Q", pick, {Q: per[Q]["coverage"]["selection_8_10"] for Q in per}, "hand", hand)


def register_choice(task, s):
    MU, DEL, d = load_prog(choice_path(task, s))
    Q = MU.shape[1]
    name = "synth_%s_t%d" % (task, s)
    l1.PROGRAMS[name] = {"Q": Q, "mu": {h: {(q, KINDS[k]): MOVES[int(MU[h, q, k])] for q in range(Q) for k in range(7)
                                            if int(MU[h, q, k]) != 0} for h in range(H)},
                         "tensors": (MU, DEL)}
    if not getattr(l1, "_l31_patch", False):
        orig = l1.program_tensors
        l1.program_tensors = lambda prog: prog["tensors"] if "tensors" in prog else orig(prog)
        l1._l31_patch = True
    l1.register(name)
    return name


def student_seed(s, restart):
    return s + 10 + 100 * restart


def student_dir(task, s, restart):
    return OUT / ("l31_%s__l1read__1M__s%d__N100000__synth_t%d" % (task, student_seed(s, restart), s))


def cmd_train(a):
    setup(a.task)
    register_choice(a.task, a.seed)
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in l1.PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    src = src.replace("input + hard reads of the hand L1 program", "input + hard reads of the synthesized L1 program (stage3/l31.py)")
    argv = ["--task", a.task, "--kind", "l1read", "--scale", "1M", "--seed", str(student_seed(a.seed, a.restart)),
            "--N", "100000", "--max-steps", "20000", "--phase", "l31", "--out-root", str(OUT), "--threads", "1",
            "--tag", "synth_t%d" % a.seed, "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


def cmd_select(a):
    """C-1 rule: the two restarts' judgment checkpoints on select:<task>; within 5 of 1,000 the smaller restart"""
    setup(a.task)
    register_choice(a.task, a.seed)
    import tasks as T
    import models as M
    import c4_select as CS
    import c1
    torch.set_num_threads(1)
    sel = CS.selection_set(a.task)
    counts = {}
    for r in (0, 1):
        d = student_dir(a.task, a.seed, r)
        ck = torch.load(d / "teacher_best.pt", weights_only=False)
        fin = json.loads((d / "final.json").read_text())
        assert ck["step"] == fin["judgment"]["step"]
        m = M.build("l1read", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
        m.load_state_dict(ck["model"])
        m.eval()
        counts[r] = c1.exact(m, sel)
    best = max(counts.values())
    pool = [r for r in (0, 1) if best - counts[r] <= 5]
    pick = min(pool)
    res = {"task": a.task, "teacher_seed": a.seed, "selection_set": {"generation_seed": "select:%s" % a.task, "size": len(sel)},
           "correct": counts, "accuracy": {r: c / len(sel) for r, c in counts.items()}, "tied_within_tolerance": pool,
           "selected_restart": pick, "selected_seed": student_seed(a.seed, pick),
           "rule": "highest selection accuracy; within 0.005 (<= 5 of 1,000) the smaller restart", "env": env_info()}
    (OUT / ("selection_%s_t%d.json" % (a.task, a.seed))).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("task", "teacher_seed", "accuracy", "selected_restart")}))


def jl(p):
    return json.loads(pathlib.Path(p).read_text())


def baselines30(task):
    import baseline_table as BT
    acc, budget, time_s = {}, {}, {}
    for k in ("abacus", "rope", "looped_rr", "gru"):
        d = BASE30 / ("l30_%s__%s__1M__s0__N100000" % (task, k))
        f = jl(d / "final.json")
        acc[k] = BT.judged(d)[1]
        budget[k] = f["train_flops"] / f["steps"] * 20000
        time_s[k] = {"judgment_wall_train_s": f["judgment"]["wall_train_s_cum"], "wall_train_s": f["wall_train_s"]}
    labs = list(acc["rope"])
    best = {l: max(v[l] for v in acc.values()) for l in labs}
    best_kind = {l: [k for k in acc if acc[k][l] == best[l]] for l in labs}
    return {"best": best, "best_kind": best_kind, "by_kind": acc, "budget": max(budget.values()), "time_s": time_s}


def cmd_report(a):
    out = {"design": "stage3/DESIGN.md 6.7 (verdict 7.7 with the 9.12 budget), 6.9", "tasks": {}}
    wins = 0
    for t in l1.VERDICT_TASKS:
        B = baselines30(t)
        labs = list(B["best"])
        rows = []
        for s in TEACHER_SEEDS:
            r = {"teacher_seed": s}
            seeds = [x for x in (s, s + 200) if (OUT / ("teacher_select_%s_s%d.json" % (t, x))).exists()]
            checks = [jl(OUT / ("teacher_select_%s_s%d.json" % (t, x))) for x in seeds]
            r["teacher_checks"] = {c["run_seed"]: c["selection_accuracy"] for c in checks}
            used = used_teacher(t, s)
            r["teacher_used"] = used
            if used is None:
                r["failure"] = "teacher"
                rows.append(r)
                continue
            ch = jl(choice_path(t, s))
            sel = jl(OUT / ("selection_%s_t%d.json" % (t, s)))
            fs = [jl(student_dir(t, s, k) / "final.json") for k in (0, 1)]
            f = fs[sel["selected_restart"]]
            acc = f["judgment"]["acc"]
            teacher_fl = sum(c["judgment_train_flops"] for c in checks)
            extract_fl = ch["meta"]["teacher"]["extraction_flops"]
            stud_fl = [x["judgment"]["train_flops_cum"] for x in fs]
            total = teacher_fl + extract_fl + sum(stud_fl)
            c1_ = acc[labs[1]] >= 0.90 and acc[labs[2]] >= 0.90
            c2_ = acc[labs[1]] >= B["best"][labs[1]] - 0.01 and acc[labs[2]] >= B["best"][labs[2]] - 0.01
            c3_ = total <= B["budget"]
            teacher_s = sum(c["judgment_wall_train_s"] for c in checks)
            cpu = {"teacher_judgment_train_s": teacher_s, "extraction_cpu_s": ch["meta"]["teacher"]["extraction_cpu_s"],
                   "synthesis_cpu_s": ch["synthesis_cpu_s_total"],
                   "students_judgment_train_s": [x["judgment"]["wall_train_s_cum"] for x in fs]}
            cpu["total"] = cpu["teacher_judgment_train_s"] + cpu["extraction_cpu_s"] + cpu["synthesis_cpu_s"] + sum(cpu["students_judgment_train_s"])
            r.update({"selected_Q": ch["selected_Q"], "dedup_discarded": ch["dedup_discarded"],
                      "coverage_by_Q": {Q: v["coverage"] for Q, v in ch["per_Q"].items()},
                      "solver_by_Q": {Q: v["solver"] for Q, v in ch["per_Q"].items()},
                      "supply_agreement_by_Q": {Q: (v["supply_agreement_all_2000_without_eos"], v["supply_agreement_all_2000_with_eos"])
                                                for Q, v in ch["per_Q"].items()},
                      "hand_coverage": ch["hand_coverage_same_dependency"], "program": ch["program"],
                      "selected_restart": sel["selected_restart"], "selection_accuracy": sel["accuracy"],
                      "acc": acc, "judgment_step": f["judgment"]["step"], "steps": f["steps"],
                      "flops": {"teacher": teacher_fl, "extraction": extract_fl, "students": stud_fl, "total": total,
                                "budget": B["budget"], "fraction": total / B["budget"]},
                      "cpu_s": cpu, "criteria": {"1_ood12_ge_0.90": c1_, "2_ge_baseline_best_minus_0.01": c2_,
                                                 "3_total_flops_le_budget": c3_}, "win": c1_ and c2_ and c3_})
            rows.append(r)
        win = len(rows) == 3 and all(x.get("win") for x in rows)
        wins += win
        out["tasks"][t] = {"baselines": B, "tables": rows, "win": win}
    out["tasks_won"] = wins
    out["answer"] = "yes" if wins >= 3 else "no"
    (OUT / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({t: [(x.get("selected_Q"), x.get("acc"), x.get("win")) for x in v["tables"]] for t, v in out["tasks"].items()}, default=str))
    print("tasks won", wins)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ("synth", "deps"):
        q = sp.add_parser(name)
        q.add_argument("--source", choices=("oracle", "l0", "teacher"), required=True)
        q.add_argument("--task", required=True)
        q.add_argument("--table", type=int)
        q.add_argument("--teacher-run")
        q.add_argument("--Q", type=int, default=1)
        q.add_argument("--stage", choices=("gate", "main"), default="gate")
    for name in ("gate1", "gate2", "gate3"):
        q = sp.add_parser(name)
        q.add_argument("--task", required=True)
    for name in ("teacher_check", "choose", "train", "select"):
        q = sp.add_parser(name)
        q.add_argument("--task", required=True)
        q.add_argument("--seed", type=int, required=True)
        q.add_argument("--restart", type=int, default=0)
        q.add_argument("--resume", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"synth": cmd_synth, "deps": cmd_deps, "gate1": cmd_gate1, "gate2": cmd_gate2, "gate3": cmd_gate3,
     "teacher_check": cmd_teacher_check, "choose": cmd_choose, "train": cmd_train, "select": cmd_select,
     "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
