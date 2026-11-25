"""3-1 with the last revision (stage3/DESIGN.md 6.12 together with 6.13; these take precedence over 6.10-6.11).
The 3-1a (stage3/l31.py) and 3-1a2 (stage3/l31b.py) runs are kept unchanged; this module reuses their helpers.

Changes against stage3/l31b.py:
  6.12-1 + 6.13-1/3  output state q' = value-free supply selection.  Per scored step t (including <eos>):
      E_t = {EOS} if y_t = <eos>, else {heads h whose read token = y_t} + {"cur" if x_t = y_t} + {"prev" if x_{t-1} = y_t};
      structure key s_t = (q_t, kind(x_t), kinds read by every head, segment bit of every head) - no values.
      CP-SAT over delta'(q', q, kind(x_t), kinds read) and c(s, q') in {head0, head1, head2, cur, prev, EOS}:
      minimise the synthesis-sample steps that are not explained (E_t empty, or c(s_t, q'_t) not in E_t); ties: fewer
      q'-changing delta' cells; unused delta' cells keep q'.  Q' = 1 .. floor(4 / Q).
  6.13-2  explained step: (s_t, q'_t) is in the synthesis-sample table, E_t is not empty and c(s_t, q'_t) in E_t.
      The table holds the keys met in the synthesis sample at steps with a non-empty E_t (a key met only at steps
      with an empty E_t has no c fixed by the data and is not in the table).
  6.13-4  selection over every (Q, Q') with Q = 1-4 (the 6.10 monotone routing candidates) and Q' = 1..floor(4/Q):
      length 8-10 explanation rate (0.005 ties) -> length 8-10 coverage (0.005 ties) -> Q x Q' -> Q.
  6.12-2  check 1 criterion unchanged (6.6-1 + value-key (d) conflicts 0 everywhere).
  6.12-3  A2' (record): Q = 1 CP-SAT maximising the covered scored steps when every position whose token equals
      the output counts (free positions t, t-1 included); <eos> steps left out of the main value.
  6.13-5  check 3' (record): the selection applied to the 3-1a2 check 3 routing candidates (rope seed 0 teacher).

The routing candidates are not solved again: the routing synthesis did not change (6.12-4), so the 3-1a2 files
(results/3-1/3-1a2/<oracle|teacher>_<task>_route_Q<k>.json) are read as they are.

  gate1 --task T        check 1 (oracle routing candidates of 3-1a2, new output state and selection, A1)
  a2p --task T          A2' (record)
  gate3p --task T       check 3' (record)
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402

import l1                        # noqa: E402
import l31                       # noqa: E402
import l31b                      # noqa: E402

RES = HERE / "results" / "3-1"
ROUTE_DIR = RES / "3-1a2"
GATE = RES / os.environ.get("L31C_GATE_DIR", "3-1a3")
H, KINDS, MOVES = l1.H, l1.KINDS, l1.MOVES
TIME_S = float(os.environ.get("L31_TIME", "600"))
SRC = ("head0", "head1", "head2", "cur", "prev", "EOS")
EOS_SRC = 5
TIE = 0.005
cpu_s = l31.cpu_s


def env_info():
    e = l31b.env_info()
    e["module"] = "stage3/l31c.py"
    e["cp_sat"]["max_time_in_seconds"] = TIME_S
    import h0a
    e["code"] = h0a.env(["stage3/l31c.py", "stage3/l31b.py", "stage3/l31.py", "stage3/l1.py"])
    return e


# ---------------------------------------------------------------- supply sets and structure keys
def steps_of(exs, ids, tens, Qp=1):
    """{i: (ctx [t -> (q, kind x_t, kinds read)], steps [(t, s, E, is_eos, q')], n)} under the program tens whose
    state index is q * Qp + q'"""
    import tasks as T
    import run as R
    out = {}
    for j in range(0, len(ids), 128):
        bid = ids[j:j + 128]
        x, y = R.make_batch([exs[i] for i in bid])
        P, Qt = l1.l1_paths(x, None, tens)
        Bt = l1.segment_bits(x, P)
        cls = l1.kinds_of(x)
        for b, i in enumerate(bid):
            n = len(exs[i][0]) + len(exs[i][1])
            q, qp = Qt[b] // Qp, Qt[b] % Qp
            rk = [[int(cls[b, int(P[b, h, t])]) for h in range(H)] for t in range(n)]
            ctx = [(int(q[t]), int(cls[b, t])) + tuple(rk[t]) for t in range(n)]
            st = []
            for t in (y[b] != -100).nonzero()[:, 0].tolist():
                yt = int(y[b, t])
                if yt == T.EOS:
                    E = frozenset({EOS_SRC})
                else:
                    E = {h for h in range(H) if int(x[b, int(P[b, h, t])]) == yt}
                    if int(x[b, t]) == yt:
                        E.add(3)
                    if t >= 1 and int(x[b, t - 1]) == yt:
                        E.add(4)
                    E = frozenset(E)
                s = ctx[t] + tuple(int(Bt[b, h, t]) for h in range(H))
                st.append((t, s, E, yt == T.EOS, int(qp[t])))
            out[i] = (ctx, st, n)
    return out


def explain(exs, ids, tens, Qp, table):
    """6.13-2 explanation rate (with <eos>), the <eos>-step rate and the shares behind the misses"""
    data = steps_of(exs, ids, tens, Qp)
    n = ok = ne = oke = miss = empty = 0
    for i in ids:
        for (t, s, E, ise, qp) in data[i][1]:
            k = (s, qp)
            good = bool(E) and k in table and table[k] in E
            n += 1
            ok += good
            miss += k not in table
            empty += not E
            if ise:
                ne += 1
                oke += good
    return {"rate": ok / n, "eos_rate": (oke / ne) if ne else None, "steps": n, "eos_steps": ne,
            "key_not_in_table": miss / n, "empty_E": empty / n}


def synth_supply(exs, syn, MU, DEL, Qp, time_s=TIME_S):
    """CP-SAT for delta' and c with the routing (MU, DEL) fixed; returns combined program, table, info"""
    from ortools.sat.python import cp_model
    t_start, c_start = time.time(), cpu_s()
    Q = MU.shape[1]
    data = steps_of(exs, syn, (MU, DEL), 1)
    m = cp_model.CpModel()
    ctx_ids, DP, qv, trans = {}, {}, {}, []
    for i in syn:
        ctx, st, n = data[i]
        tl = max(t for (t, *_) in st)
        qv[(i, 0)] = m.NewConstant(0)
        for t in range(tl):
            c = ctx[t]
            if Qp > 1:
                if c not in ctx_ids:
                    ctx_ids[c] = len(ctx_ids)
                    for a in range(Qp):
                        DP[(a, ctx_ids[c])] = m.NewIntVar(0, Qp - 1, "")
                qn = m.NewIntVar(0, Qp - 1, "")
                m.AddElement(qv[(i, t)], [DP[(a, ctx_ids[c])] for a in range(Qp)], qn)
            else:
                qn = m.NewConstant(0)
            qv[(i, t + 1)] = qn
            trans.append((i, t, c))
    lit = {}

    def lits(i, t):
        if (i, t) not in lit:
            v = qv[(i, t)]
            bs = [m.NewBoolVar("") for _ in range(Qp)]
            for a, b in enumerate(bs):
                m.Add(v == a).OnlyEnforceIf(b)
                m.Add(v != a).OnlyEnforceIf(b.Not())
            lit[(i, t)] = bs
        return lit[(i, t)]

    cb, ex, n_steps, n_empty = {}, [], 0, 0
    for i in syn:
        for (t, s, E, ise, _) in data[i][1]:
            n_steps += 1
            if not E:
                n_empty += 1
                continue
            e = m.NewBoolVar("")
            ex.append(e)
            for a in range(Qp):
                if (s, a) not in cb:
                    cb[(s, a)] = [m.NewBoolVar("") for _ in SRC]
                    m.AddExactlyOne(cb[(s, a)])
                cl = [cb[(s, a)][o] for o in sorted(E)] + [e.Not()]
                if Qp > 1:
                    cl.append(lits(i, t)[a].Not())
                m.AddBoolOr(cl)
    ch = []
    for (a, cid), v in DP.items():
        b = m.NewBoolVar("")
        m.Add(v == a).OnlyEnforceIf(b.Not())
        ch.append(b)
        m.AddHint(v, a)
    m.Maximize((len(ch) + 1) * sum(ex) - sum(ch))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_s
    s.parameters.num_workers = 1
    s.parameters.random_seed = 0
    st_ = s.Solve(m)
    status = s.StatusName(st_)
    assert status in ("OPTIMAL", "FEASIBLE"), status
    qsol = {key: s.Value(v) for key, v in qv.items()}
    used = {(qsol[(i, t)], c) for (i, t, c) in trans}
    DPt = torch.arange(Qp)[:, None, None, None, None, None].expand(Qp, Q, 7, 7, 7, 7).clone()
    inv = {j: c for c, j in ctx_ids.items()}
    for (a, cid), v in DP.items():
        if (a, inv[cid]) in used:
            DPt[(a,) + inv[cid]] = s.Value(v)
    table = {}
    for i in syn:
        for (t, sk, E, ise, _) in data[i][1]:
            if E:
                k = (sk, qsol[(i, t)])
                table[k] = next(o for o in range(len(SRC)) if s.Value(cb[k][o]))
    MUc, DELc = l31b.combine(MU, DEL, Qp, DPt)
    pp = l31.batch_paths(exs, syn, (MU, DEL))                     # execution check: positions and q' as solved
    pc = l31.batch_paths(exs, syn, (MUc, DELc))
    same = 0
    for i in syn:
        tl = max(t for (ii, t) in qsol if ii == i)
        same += bool((pc[i][2] == pp[i][2]).all()) and all(
            int(pc[i][3][t]) == int(pp[i][3][t]) * Qp + qsol[(i, t)] for t in range(tl + 1))
    info = {"Qp": Qp, "status": status, "proved_optimal": status == "OPTIMAL",
            "synthesis_sample_unexplained_solver": n_steps - int(sum(s.Value(e) for e in ex)),
            "synthesis_sample_steps": n_steps, "synthesis_sample_empty_E": n_empty,
            "changing_delta_p_cells": int(sum(s.Value(b) for b in ch)), "contexts": len(ctx_ids),
            "table_keys": len(table), "wall_s": time.time() - t_start, "cpu_s": cpu_s() - c_start,
            "time_limit_s": time_s, "workers": 1, "random_seed": 0, "exec_check_examples_equal": same / len(syn)}
    return MUc, DELc, table, info


def table_json(table):
    return [{"q": k[0][0], "kind_x": KINDS[k[0][1]], "reads": [KINDS[r] for r in k[0][2:2 + H]],
             "bits": list(k[0][2 + H:]), "qp": k[1], "c": SRC[v]} for k, v in sorted(table.items())]


def table_load(rows):
    return {((r["q"], KINDS.index(r["kind_x"])) + tuple(KINDS.index(x) for x in r["reads"]) + tuple(r["bits"]), r["qp"]):
            SRC.index(r["c"]) for r in rows}


def load_routes(prefix):
    out = {}
    for Q in (1, 2, 3, 4):
        MU, DEL, rec = l31.load_prog(ROUTE_DIR / ("%s_route_Q%d.json" % (prefix, Q)))
        assert MU.shape[1] == Q
        out[Q] = (MU, DEL, rec)
    return out


def supply_candidates(exs, syn, sel, ids_all, routes, prefix):
    """every (Q, Q'); files <prefix>_sup_Q<Q>_Qp<Qp>.json in GATE"""
    res = {}
    for Q, (MU, DEL, rrec) in routes.items():
        for Qp in range(1, 4 // Q + 1):
            f = GATE / ("%s_sup_Q%d_Qp%d.json" % (prefix, Q, Qp))
            if f.exists():
                MUc, DELc, rec = l31.load_prog(f)
                table = table_load(rec["table"])
            else:
                MUc, DELc, table, info = synth_supply(exs, syn, MU, DEL, Qp)
                assert info["exec_check_examples_equal"] == 1.0, "q' execution check failed: stop"
                rec = {"Q": Q, "Qp": Qp, "states": Q * Qp, "solver": info,
                       "routing_file": str((ROUTE_DIR / ("%s_route_Q%d.json" % (prefix, Q))).relative_to(ROOT)),
                       "routing_candidate": rrec["candidate"], "coverage": rrec["coverage"],
                       "coverage_without_free": rrec["coverage_without_free"],
                       "explanation": {"synthesis_sample": explain(exs, syn, (MUc, DELc), Qp, table),
                                       "selection_8_10": explain(exs, sel, (MUc, DELc), Qp, table),
                                       "all": explain(exs, ids_all, (MUc, DELc), Qp, table)},
                       "table": table_json(table)}
                l31.save_prog(f, MUc, DELc, rec)
                rec = json.loads(f.read_text())
                print(prefix, "Q", Q, "Qp", Qp, "expl", {k: round(v["rate"], 4) for k, v in rec["explanation"].items()},
                      "cov sel %.4f" % rec["coverage"]["selection_8_10"], "cpu %.1f" % info["cpu_s"], flush=True)
            res[(Q, Qp)] = (MUc, DELc, rec)
    return res


def select(res):
    """6.13-4: explanation rate 8-10 (0.005) -> coverage 8-10 (0.005) -> Q x Q' -> Q"""
    keys = list(res)
    ex = {k: res[k][2]["explanation"]["selection_8_10"]["rate"] for k in keys}
    b = max(ex.values())
    keys = [k for k in keys if ex[k] >= b - TIE]
    cv = {k: res[k][2]["coverage"]["selection_8_10"] for k in keys}
    b = max(cv.values())
    keys = [k for k in keys if cv[k] >= b - TIE]
    return min(keys, key=lambda k: (k[0] * k[1], k[0])), keys


def cand_summary(res):
    return {"Q%d_Qp%d" % k: {"explanation": {s: v["rate"] for s, v in r[2]["explanation"].items()},
                             "eos_explanation": {s: v["eos_rate"] for s, v in r[2]["explanation"].items()},
                             "key_not_in_table": {s: v["key_not_in_table"] for s, v in r[2]["explanation"].items()},
                             "empty_E": {s: v["empty_E"] for s, v in r[2]["explanation"].items()},
                             "coverage": r[2]["coverage"],
                             "solver": {x: r[2]["solver"].get(x) for x in
                                        ("status", "proved_optimal", "synthesis_sample_unexplained_solver",
                                         "changing_delta_p_cells", "cpu_s")}}
            for k, r in sorted(res.items())}


# ---------------------------------------------------------------- check 1
def cmd_gate1(a):
    torch.set_num_threads(1)
    l31b.setup(a.task)
    GATE.mkdir(parents=True, exist_ok=True)
    exs, ns = l31.train_with_n(a.task, l1.SEED_DATA_A2, l31.N_ALL)
    syn, sel = l31.pick_sets(a.task, ns)
    ids_all = list(range(l31.N_ALL))
    rows = l31.rows_oracle(a.task, exs, ids_all)
    prefix = "oracle_%s" % a.task
    res = supply_candidates(exs, syn, sel, ids_all, load_routes(prefix), prefix)
    pick, tied = select(res)
    MUc, DELc, rec = res[pick]
    pc = l31b.paths_of(exs, ids_all, (MUc, DELc))
    cov = l31b.covs(rows, syn, sel, ids_all, pc)
    r1 = l31b.a1(a.task, (MUc, DELc), l31.moving_t(MUc))
    ok_cov = cov["synthesis_sample"] == 1.0
    out = {"check": "6.6-1 oracle recovery (6.12, 6.13 selection)", "task": a.task,
           "candidates": cand_summary(res), "selected": {"Q": pick[0], "Qp": pick[1]},
           "tied_after_explanation_and_coverage": ["Q%d_Qp%d" % k for k in tied],
           "combined_states": int(MUc.shape[1]), "program": l31.prog_table(MUc, DELc), "table": rec["table"],
           "explanation_selected": rec["explanation"], "oracle_coverage_free": cov,
           "coverage_1.000_on_synthesis_sample": ok_cov, "a1": r1,
           "pass_strict": bool(ok_cov and r1["a1_all_strict"]), "pass_free": bool(ok_cov and r1["a1_all_free"]),
           "t0_rule": "first query step (6.10-6)" if a.task == "mqar" else "first '='", "env": env_info()}
    out["pass"] = out["pass_strict"] if out["pass_strict"] == out["pass_free"] else None
    (GATE / ("gate1_%s.json" % a.task)).write_text(json.dumps(out, indent=1, default=str))
    print(a.task, "gate1 pick", pick, "expl", rec["explanation"]["selection_8_10"], "pass", out["pass_strict"],
          out["pass_free"], flush=True)


# ---------------------------------------------------------------- A2' (record)
def value_sets(exs, ids):
    """{i: [(t, O_t positions j <= t with x_j = y_t, is_eos)]} over the scored steps"""
    import tasks as T
    import run as R
    out = {}
    for j in range(0, len(ids), 200):
        bid = ids[j:j + 200]
        x, y = R.make_batch([exs[i] for i in bid])
        for b, i in enumerate(bid):
            out[i] = []
            for t in (y[b] != -100).nonzero()[:, 0].tolist():
                yt = int(y[b, t])
                O = {p for p in range(t + 1) if int(x[b, p]) == yt}
                out[i].append((t, O, yt == T.EOS))
    return out


def a2p_cov(vs, ids, paths):
    n = ok = n_all = 0
    for i in ids:
        for (t, O, ise) in vs[i]:
            n_all += 1
            if ise:
                continue
            n += 1
            ok += bool(O & ({int(paths[i][h, t]) for h in range(H)} | {t, t - 1}))
    return {"without_eos": ok / n, "with_eos": ok / n_all, "steps_without_eos": n, "steps_with_eos": n_all}


def synth_a2p(exs, syn, vs, time_s=TIME_S):
    """Q = 1 CP-SAT: maximise the covered scored steps (no <eos>), free positions t, t-1 constant; ties: fewer
    non-stay mu cells"""
    import tasks as T
    import pf as PFM
    import run as R
    from ortools.sat.python import cp_model
    t_start, c_start = time.time(), cpu_s()
    seps = torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]])
    m = cp_model.CpModel()
    data, kset = [], set()
    for i in syn:
        tl = max(t for (t, _, _) in vs[i])
        xb, _ = R.make_batch([exs[i]])
        x = xb[:, :tl + 1]
        cls = l1.kinds_of(x)[0].tolist()
        issep = torch.isin(x, seps)
        cand = [PFM.candidates(x, t, torch.arange(max(t, 1))[None, :], x[:, t], issep)[0].tolist() for t in range(tl + 1)]
        data.append((i, tl, cls, cand))
        kset |= set(cls)
    MU = {(h, k): m.NewIntVar(0, len(MOVES) - 1, "") for h in range(H) for k in sorted(kset)}
    terms, var, const = [], {}, 0
    for (i, tl, cls, cand) in data:
        prev = [None] * H
        goal = {t: (O, ise) for (t, O, ise) in vs[i]}
        for t in range(tl + 1):
            ps = []
            for h in range(H):
                mv = MU[(h, cls[t])]
                p = m.NewIntVar(0, t, "")
                if t == 0:
                    m.AddElement(mv, cand[0][0], p)
                else:
                    m.AddAllowedAssignments([prev[h], mv, p], [(pp, k, cand[t][pp][k]) for pp in range(len(cand[t]))
                                                               for k in range(len(MOVES))])
                ps.append(p)
                prev[h] = p
            var[(i, t)] = ps
            if t in goal and not goal[t][1]:
                O = goal[t][0]
                if O & {t, t - 1}:
                    const += 1
                    continue
                if not O:
                    continue
                bs = []
                for h in range(H):
                    for j in sorted(O):
                        b = m.NewBoolVar("")
                        m.Add(ps[h] == j).OnlyEnforceIf(b)
                        bs.append(b)
                c = m.NewBoolVar("")
                m.AddBoolOr(bs).OnlyEnforceIf(c)
                terms.append(c)
    ns = []
    for v in MU.values():
        b = m.NewBoolVar("")
        m.Add(v == 0).OnlyEnforceIf(b.Not())
        ns.append(b)
        m.AddHint(v, 0)
    m.Maximize((len(ns) + 1) * sum(terms) - sum(ns))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_s
    s.parameters.num_workers = 1
    s.parameters.random_seed = 0
    st = s.Solve(m)
    status = s.StatusName(st)
    assert status in ("OPTIMAL", "FEASIBLE"), status
    MU_t = torch.zeros(H, 1, 7, dtype=torch.long)
    for (h, k), v in MU.items():
        MU_t[h, 0, k] = s.Value(v)
    DEL_t = torch.zeros(1, 7, 7, 7, 7, dtype=torch.long)
    pp = l31.batch_paths(exs, syn, (MU_t, DEL_t))
    same = sum(all(int(pp[i][2][h, t]) == s.Value(var[(i, t)][h]) for t in range(tl + 1) for h in range(H))
               for (i, tl, cls, cand) in data)
    info = {"status": status, "proved_optimal": status == "OPTIMAL", "objective": s.ObjectiveValue(),
            "bound": s.BestObjectiveBound(),
            "gap_relative": (s.BestObjectiveBound() - s.ObjectiveValue()) / max(1.0, abs(s.ObjectiveValue())),
            "free_covered_steps": const, "wall_s": time.time() - t_start, "cpu_s": cpu_s() - c_start,
            "time_limit_s": time_s, "workers": 1, "random_seed": 0, "exec_check_examples_equal": same / len(data)}
    return MU_t, DEL_t, info


def cmd_a2p(a):
    torch.set_num_threads(1)
    l31b.setup(a.task)
    GATE.mkdir(parents=True, exist_ok=True)
    exs, ns = l31.train_with_n(a.task, l1.SEED_DATA_A2, l31.N_ALL)
    syn, sel = l31.pick_sets(a.task, ns)
    ids_all = list(range(l31.N_ALL))
    vs = value_sets(exs, ids_all)
    MU, DEL, info = synth_a2p(exs, syn, vs)
    pa = l31b.paths_of(exs, ids_all, (MU, DEL))
    stay = l31b.paths_of(exs, ids_all, l31b.all_stay(1))
    out = {"check": "A2' path-free L0 coverage (6.12-3, record)", "task": a.task, "solver": info,
           "program": l31.prog_table(MU, DEL),
           "covered": {"synthesis_sample": a2p_cov(vs, syn, pa), "selection_8_10": a2p_cov(vs, sel, pa),
                       "all": a2p_cov(vs, ids_all, pa)},
           "all_stay": {"synthesis_sample": a2p_cov(vs, syn, stay), "all": a2p_cov(vs, ids_all, stay)},
           "data": "train_set seed %d, the first 2,000 (synthesis sample as 6.9-1)" % l1.SEED_DATA_A2, "env": env_info()}
    (GATE / ("a2p_%s.json" % a.task)).write_text(json.dumps(out, indent=1, default=str))
    print(a.task, "a2p", out["covered"], info["status"], flush=True)


# ---------------------------------------------------------------- check 3' (record)
def cmd_gate3p(a):
    torch.set_num_threads(1)
    l31b.setup(a.task)
    GATE.mkdir(parents=True, exist_ok=True)
    exs, ns = l31.train_with_n(a.task, 0, l31.N_ALL)
    syn, sel = l31.pick_sets(a.task, ns)
    ids_all = list(range(l31.N_ALL))
    prefix = "teacher_%s" % a.task
    res = supply_candidates(exs, syn, sel, ids_all, load_routes(prefix), prefix)
    pick, tied = select(res)
    g3 = json.loads((ROUTE_DIR / ("gate3_%s.json" % a.task)).read_text())
    rec = res[pick][2]
    sel_rate = rec["explanation"]["selection_8_10"]["rate"]
    out = {"check": "check 3' (6.13-5, record): new selection on the 3-1a2 check 3 routing candidates", "task": a.task,
           "teacher_run": g3["teacher"]["teacher_run"], "candidates": cand_summary(res),
           "selected": {"Q": pick[0], "Qp": pick[1]}, "tied_after_explanation_and_coverage": ["Q%d_Qp%d" % k for k in tied],
           "explanation_selected": rec["explanation"], "coverage_selected": rec["coverage"],
           "supply_agreement_selected_routing": {k: g3["per_Q"][str(pick[0])][k] for k in
                                                 ("supply_agreement_without_eos", "supply_agreement_with_eos")},
           "program": rec["program"], "table": rec["table"],
           "explanation_8_10_below_0.99": bool(sel_rate < 0.99), "env": env_info()}
    (GATE / ("gate3p_%s.json" % a.task)).write_text(json.dumps(out, indent=1, default=str))
    print(a.task, "gate3p pick", pick, "expl", {k: round(v["rate"], 4) for k, v in rec["explanation"].items()}, flush=True)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ("gate1", "a2p", "gate3p"):
        q = sp.add_parser(name)
        q.add_argument("--task", required=True)
    a = p.parse_args()
    {"gate1": cmd_gate1, "a2p": cmd_a2p, "gate3p": cmd_gate3p}[a.cmd](a)


if __name__ == "__main__":
    main()
