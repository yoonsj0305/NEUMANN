"""3-0: the L1 gate (stage3/DESIGN.md 3, 5).  L1 = multi-head finite-automaton control (Q <= 4, H = 3 heads).

Machine (3): control state q in {0..Q-1}, q_0 = 0, shared by all heads.  At step t (one step per token x_t):
  move   head h: mu_h(q_t, kappa(x_t)), the six PF moves of stage1/pf.py (candidates; causal, every read <= t)
  read   r_h(t) = tape[p_h(t)]
  next   q_{t+1} = delta(q_t, kappa(x_t), kappa(r_1(t)), kappa(r_2(t)), kappa(r_3(t)))
kappa = the seven stage-1 token kinds (pf.token_classes with the G-0 adapter rule), applied to the tape: kappa(x_t) is
the kind at position t and kappa(r_h(t)) the kind at position p_h(t) (answer-phase positions are "answer_phase").
Separators of next_sep: '+', '=', '|' and the G-0 infix operators (as C-1).  Q = 1 is L0 (A0 checks this).
Student input (3, as C-1 plus q): u_t = E(x_t) + sum_h R_h(E(x[p_h(t)]) + F_h b_h(t)) + W_q onehot(q_t) over the
moving heads; in_t = u_t + S(u_{t-1}).  Segment bit b_h(t) = [g(p_h(t)) == g(p_h(t0))], g(i) = separators at
positions <= i, t0 = the first scored step (the first '=' position; MQAR, which has no '=': the step after the
first '|', the first query).

Hand programs (Claude Code, within 3; reported as tables): PROGRAMS below.  "supply" = the output-supplying head
per state (5.2 A1 correct read).  No program needs the left end, so no task uses BOS (A1 records this).

  a0                          regression: Q = 1 on the 15 C-1 compiled tables == stage2/c1a.read_paths (one process
                              per task: --task)
  a1 --task T                 (b), (c') (t >= t0: positions, bits, q), correct read, (d) local determinism
  a2 --task T                 oracle dependency (supply head's read position) -> L0 exhaustive compile (c3 method,
                              3 heads, greedy cover); coverage and (d) without q of the best L0 table
  train --task T --arm {q,q0} the D student (seed 30) or its control with q = 0
  b --task T                  teacher dependency (rope seed 0 judgment checkpoint, gradient, first 2,000) coverage of
                              the hand program's reads vs the all-stay table
  report                      the per-task table and the verdict (5.3)
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
import os
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np               # noqa: E402
import torch                     # noqa: E402
import torch.nn as nn            # noqa: E402

OUT = pathlib.Path(os.environ.get("L30_OUT", HERE / "results" / "3-0"))
H = 3
SEED_STUDENT = 30
SEED_DATA_A2 = 0                    # A2 / B: the teacher's (rope seed 0) training data, first 2,000 (c3 method)
VERDICT_TASKS = ("dup", "interleave", "repeat", "pairswap")
ALL_TASKS = VERDICT_TASKS + ("mqar",)
C1_TASKS = ("addition", "copy", "mul1", "prefix_sum", "reverse")
MOVES = ("stay", "right", "left", "next_sep", "start", "content")
KINDS = ("digit", "+", "=", "|", "node", "answer_phase", "other")
ARMS = {"q": "l1read", "q0": "l1read_q0"}

# ---------------------------------------------------------------- hand programs (3: Q <= 4, mu, delta)
# mu: {head: {(q, kind): move}}; every other (q, kind) of a head is "stay".
# delta: rules (q, kind of x_t, {head: kind of its read}, next q) in order, first match; "*" = any; next "same" = q.
PROGRAMS = {
    "dup": {
        "Q": 2,
        "mu": {0: {(1, "answer_phase"): "right"}},
        "delta": [("*", "=", {}, 0), (0, "answer_phase", {}, 1), (1, "answer_phase", {}, 0), ("*", "*", {}, "same")],
        "supply": {0: 0, 1: 0},
        "note": "head 0 reads s_floor(k/2) at answer step k: it waits on q = 0 and moves right on q = 1; q alternates "
                "on answer-phase steps from 0 at the '=' step"},
    "interleave": {
        "Q": 2,
        "mu": {0: {(0, "answer_phase"): "right"},
               1: {(0, "+"): "next_sep", (1, "+"): "next_sep", (1, "answer_phase"): "right"}},
        "delta": [("*", "=", {}, 1), (0, "answer_phase", {}, 1), (1, "answer_phase", {}, 0), ("*", "*", {}, "same")],
        "supply": {0: 0, 1: 1},
        "note": "head 0 (A) at a_0, head 1 (B) jumps to '+' and waits; q = 1 on odd answer steps: B moves right and "
                "supplies b; q = 0 on even steps: A moves right (from step 2) and supplies a"},
    "repeat": {
        "Q": 3,
        "mu": {0: {(0, "answer_phase"): "right"},
               1: {(0, "="): "right", (0, "answer_phase"): "right"},
               2: {(2, "answer_phase"): "right"}},
        "delta": [(0, "*", {1: "="}, 1), (1, "*", {}, 2), (2, "*", {}, 2), ("*", "*", {}, "same")],
        "supply": {0: 0, 1: 2, 2: 2},
        "note": "head 0 copies s (q = 0); head 1 runs one position ahead of head 0 and reads '=' at answer step n-1, "
                "so q = 1 at step n (head 2 reads s_0 at position 0) and q = 2 after (head 2 moves right): the state "
                "changes on the KIND READ (5.1).  The extra look-ahead head makes the switch happen at step n, not "
                "one step late (the design sketch's 'A reads = then q 0 -> 1', with A one ahead)"},
    "pairswap": {
        "Q": 3,
        "mu": {0: {(0, "="): "right", (0, "answer_phase"): "right", (1, "answer_phase"): "right",
                   (2, "answer_phase"): "right"},
               1: {(0, "answer_phase"): "right", (2, "answer_phase"): "right"}},
        "delta": [(0, "=", {}, 1), (1, "answer_phase", {}, 0), (0, "answer_phase", {}, 2), (2, "answer_phase", {}, 0),
                  ("*", "*", {}, "same")],
        "supply": {0: 0, 1: 1, 2: 1},
        "note": "head 0 reads position k+1 at answer step k (supplies even k: s_{k+1}); head 1 reads position k-1 "
                "(supplies odd k: s_{k-1}), starting one step late: q = 1 marks answer step 1 (head 1 stays at 0), "
                "then q alternates 0 (even k) / 2 (odd k >= 3)"},
    "mqar": {
        "Q": 2,
        "mu": {0: {(0, "|"): "start", (0, "answer_phase"): "content", (1, "answer_phase"): "start"}},
        "delta": [("*", "|", {}, 0), (0, "answer_phase", {}, 1), (1, "answer_phase", {}, 0), ("*", "*", {}, "same")],
        "supply": {0: 0},
        "note": "the design sketch: start at '|', content on query steps (q = 0), start on answer steps (q = 1)"},
}


def program_tensors(prog):
    """MU [H, Q, 7] move ids, DEL [Q, 7, 7, 7, 7] next state"""
    Q = prog["Q"]
    assert 1 <= Q <= 4
    MU = torch.zeros(H, Q, len(KINDS), dtype=torch.long)
    for h, m in prog["mu"].items():
        for (q, k), mv in m.items():
            assert 0 <= q < Q
            MU[h, q, KINDS.index(k)] = MOVES.index(mv)
    DEL = torch.full((Q, 7, 7, 7, 7), -1, dtype=torch.long)
    for q in range(Q):
        for kx in range(7):
            for r in itertools.product(range(7), repeat=H):
                for (rq, rk, rr, nxt) in prog["delta"]:
                    if rq != "*" and rq != q:
                        continue
                    if rk != "*" and KINDS.index(rk) != kx:
                        continue
                    if any(KINDS.index(v) != r[h] for h, v in rr.items()):
                        continue
                    DEL[(q, kx) + r] = q if nxt == "same" else nxt
                    break
    assert int(DEL.min()) >= 0 and int(DEL.max()) < Q
    return MU, DEL


def table_program(table):
    """an L0 table [H][7] as an L1 program with Q = 1 (A0)"""
    return {"Q": 1, "mu": {h: {(0, KINDS[c]): MOVES[table[h][c]] for c in range(7)} for h in range(H)},
            "delta": [("*", "*", {}, "same")], "supply": {0: 0}}


def moving(prog):
    return [h for h in range(H) if any(mv != "stay" for mv in prog["mu"].get(h, {}).values())]


def kinds_of(tokens):
    import tasks as T
    import pf as PFM
    dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
    return PFM.token_classes(tokens, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]],
                             T.TOK[T.NODES[-1]] + 1)


def l1_paths(tokens, prog, tensors=None):
    """head positions after the move [B, H, T] and the state q_t used at each step [B, T]"""
    import tasks as T
    import pf as PFM
    MU, DEL = tensors if tensors is not None else program_tensors(prog)
    B, Tn = tokens.shape
    cls = kinds_of(tokens)
    issep = torch.isin(tokens, torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]]))   # + adapter operators (pf patch)
    h = torch.zeros(B, H, dtype=torch.long)
    q = torch.zeros(B, dtype=torch.long)
    P = torch.zeros(B, H, Tn, dtype=torch.long)
    Qt = torch.zeros(B, Tn, dtype=torch.long)
    hs = torch.arange(H)
    for t in range(Tn):
        Qt[:, t] = q
        mv = MU[hs[None, :], q[:, None], cls[:, t][:, None]]                     # [B, H]
        cand = PFM.candidates(tokens, t, h, tokens[:, t], issep)
        h = cand.gather(2, mv[:, :, None])[:, :, 0]
        P[:, :, t] = h
        rc = cls.gather(1, h)                                                    # kinds of the reads [B, H]
        q = DEL[q, cls[:, t], rc[:, 0], rc[:, 1], rc[:, 2]]
    return P, Qt


def first_scored(tokens):
    """t0 per row: the first '=' position; rows without '=' (MQAR): the first '|' position + 1"""
    import tasks as T
    eq = tokens == T.TOK["="]
    bar = tokens == T.TOK["|"]
    has_eq = eq.any(1)
    assert bool((has_eq | bar.any(1)).all())
    return torch.where(has_eq, eq.float().argmax(1), bar.float().argmax(1) + 1)


def segment_bits(tokens, P):
    import c1a
    g = torch.cumsum(c1a.separators(tokens).long(), 1)
    t0 = first_scored(tokens)
    gp = g[:, None, :].expand(-1, P.shape[1], -1).gather(2, P)
    ref = gp.gather(2, t0[:, None, None].expand(-1, P.shape[1], 1))
    return (gp == ref).long()


def install(task):
    import l_adapter
    l_adapter.install()


# ---------------------------------------------------------------- A0
def cmd_a0(a):
    import c0a
    import c1
    import c1a
    import h0a
    c0a.install(a.task)
    import tasks as T
    import run as R
    torch.set_num_threads(1)
    res = {"task": a.task, "tables": {}}
    for i in (1, 2, 3):
        table = c1.compiled(a.task, i)["policy"]
        prog = table_program(table)
        tens = program_tensors(prog)
        evs = T.eval_sets(a.task, 1000, 500)
        evs["train_first200"] = T.train_set(a.task, 100000, c1.seed_of(i))[:200]
        sets = {}
        for lab, ex in evs.items():
            same_p = same_b = steps = 0
            for j in range(0, len(ex), 128):
                chunk = ex[j:j + 128]
                x, _ = R.make_batch(chunk)
                P0 = c1a.read_paths(x, table)
                P1, Qt = l1_paths(x, prog, tens)
                assert int(Qt.max()) == 0
                B0, B1 = c1a.segment_bits(x, P0), segment_bits(x, P1)
                for b, e in enumerate(chunk):
                    n = len(e[0]) + len(e[1])
                    steps += n
                    same_p += int((P0[b, :, :n] == P1[b, :, :n]).all(0).sum())
                    same_b += int((B0[b, :, :n] == B1[b, :, :n]).all(0).sum())
            sets[lab] = {"steps": steps, "read_positions_equal": same_p / steps, "segment_bits_equal": same_b / steps}
            print(a.task, i, lab, sets[lab], flush=True)
        res["tables"]["table%d" % i] = {"source": str(c1.SRC[a.task][i - 1].relative_to(ROOT)), "policy": table,
                                        "sets": sets}
    res["all_1.000"] = all(s["read_positions_equal"] == 1.0 for v in res["tables"].values() for s in v["sets"].values())
    res["env"] = h0a.env(["stage3/l1.py"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("a0_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(a.task, "A0 all 1.000:", res["all_1.000"])


# ---------------------------------------------------------------- A1
def dkeys(x, y, P, Bt, Qt, mv, use_q=True):
    """scored-step (d) keys: (x_t, (x[p_h(t)], b_h(t)) moving heads, q_t, and the same of step t-1) -> next token"""
    out = []
    for b in range(x.shape[0]):
        for t in (y[b] != -100).nonzero()[:, 0].tolist():
            k = (int(x[b, t]),) + tuple((int(x[b, P[b, j, t]]), int(Bt[b, j, t])) for j in mv)
            k += ((int(Qt[b, t]),) if use_q else ())
            k += (int(x[b, t - 1]),) + tuple((int(x[b, P[b, j, t - 1]]), int(Bt[b, j, t - 1])) for j in mv)
            k += ((int(Qt[b, t - 1]),) if use_q else ())
            out.append((b, k, int(y[b, t])))
    return out


def d_check(task, paths_fn, mv, evs, use_q, train_seed=SEED_STUDENT):
    """(d): table from the training data (seed 30, 100,000); per set: conflicts inside the set, steps whose key is in
    the training table and gets a different next token, key coverage (recorded)"""
    import tasks as T
    import run as R
    train = T.train_set(task, 100000, train_seed)
    tabk, conflicts = {}, 0
    for j in range(0, len(train), 256):
        x, y = R.make_batch(train[j:j + 256])
        P, Qt = paths_fn(x)
        for _, k, v in dkeys(x, y, P, segment_bits(x, P), Qt, mv, use_q):
            if k in tabk and tabk[k] != v:
                conflicts += 1
            tabk.setdefault(k, v)
    sets = {}
    for lab, ex in evs.items():
        own, own_conf, n, cov, cov_wrong = {}, 0, 0, 0, 0
        for j in range(0, len(ex), 128):
            x, y = R.make_batch(ex[j:j + 128])
            P, Qt = paths_fn(x)
            for _, k, v in dkeys(x, y, P, segment_bits(x, P), Qt, mv, use_q):
                n += 1
                if k in own and own[k] != v:
                    own_conf += 1
                own.setdefault(k, v)
                if k in tabk:
                    cov += 1
                    cov_wrong += tabk[k] != v
        sets[lab] = {"scored_steps": n, "conflicts_within_set": own_conf, "covered_steps_vs_train_table_wrong": cov_wrong,
                     "key_coverage_recorded": cov / n}
    return {"train_seed": train_seed, "train_examples": len(train), "train_table_keys": len(tabk),
            "train_conflicts": conflicts, "sets": sets,
            "conflicts_0_everywhere": conflicts == 0 and all(s["conflicts_within_set"] == 0 and
                                                             s["covered_steps_vs_train_table_wrong"] == 0
                                                             for s in sets.values())}


def cmd_a1(a):
    install(a.task)
    import tasks as T
    import run as R
    import h0a
    torch.set_num_threads(1)
    prog = PROGRAMS[a.task]
    tens = program_tensors(prog)
    mv = moving(prog)
    rng = random.Random("l30:causal:%s" % a.task)
    pool = sorted({T.TOK[d] for d in T.DIGITS} | {T.TOK[s] for s in ("+", "=", "|", "-", "*", "^")} | {T.EOS}
                  | ({T.TOK[v] for v in T.NODES} if a.task == "mqar" else set()))
    evs = T.eval_sets(a.task, 2000, 500)
    sets = {}
    for lab, ex in evs.items():
        caus = inv = inv_any_pq = n_sc = n_ok = 0
        for j in range(0, len(ex), 128):
            chunk = ex[j:j + 128]
            x, y = R.make_batch(chunk)
            P, Qt = l1_paths(x, prog, tens)
            Bt = segment_bits(x, P)
            t0 = first_scored(x)
            x2 = x.clone()
            ts = []
            for b, e in enumerate(chunk):
                n = len(e[0]) + len(e[1])
                caus += bool((P[b, :, :n] <= torch.arange(n)[None, :]).all())
                t = rng.randint(int(t0[b]), n - 1)                                  # a step t >= t0
                ts.append(t)
                for p in range(t + 1, n):
                    x2[b, p] = rng.choice(pool)
            P2, Q2 = l1_paths(x2, prog, tens)
            B2 = segment_bits(x2, P2)
            for b, t in enumerate(ts):
                same = (bool((P[b, :, :t + 1] == P2[b, :, :t + 1]).all()) and bool((Bt[b, :, :t + 1] == B2[b, :, :t + 1]).all())
                        and bool((Qt[b, :t + 1] == Q2[b, :t + 1]).all()))
                inv += same
            # correct read: scored steps except <eos>
            for b in range(x.shape[0]):
                for t in (y[b] != -100).nonzero()[:, 0].tolist():
                    if int(y[b, t]) == T.EOS:
                        continue
                    h = prog["supply"].get(int(Qt[b, t]))
                    n_sc += 1
                    n_ok += h is not None and int(x[b, P[b, h, t]]) == int(y[b, t])
        sets[lab] = {"examples": len(ex), "b_causal_p_le_t": caus / len(ex),
                     "c_prime_invariance_t_ge_t0_positions_bits_q": inv / len(ex),
                     "correct_read_scored_steps_without_eos": n_ok / n_sc, "scored_steps_without_eos": n_sc}
        print(a.task, lab, sets[lab], flush=True)
    d = d_check(a.task, lambda x: l1_paths(x, prog, tens), mv, evs, use_q=True)
    print(a.task, "(d)", json.dumps({k: v for k, v in d.items() if k != "sets"}), flush=True)
    for lab, s in d["sets"].items():
        print("   ", lab, s, flush=True)
    ok = all(s["b_causal_p_le_t"] == 1.0 and s["c_prime_invariance_t_ge_t0_positions_bits_q"] == 1.0
             and s["correct_read_scored_steps_without_eos"] == 1.0 for s in sets.values()) and d["conflicts_0_everywhere"]
    res = {"task": a.task, "program": prog_json(prog), "moving_heads": mv, "bos": False,
           "bos_reason": "no head needs the left end: every head starts at position 0 and reads it directly; no "
                         "head moves left (H-0 BOS convention not used)",
           "kind_of_read": "kappa at the read position (pf.token_classes on the tape)",
           "sets": sets, "d": d, "a1_all": ok, "env": h0a.env(["stage3/l1.py", "stage3/l_tasks.py", "stage3/l_adapter.py"])}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("a1_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(a.task, "A1:", ok)


def prog_json(prog):
    return {"Q": prog["Q"],
            "mu": {"head%d" % h: {"q%d %s" % (q, k): mv for (q, k), mv in sorted(m.items())} for h, m in prog["mu"].items()},
            "mu_default": "stay",
            "delta_rules_first_match": [{"q": q, "kind_x": k, "kind_reads": {"head%d" % h: v for h, v in r.items()},
                                         "next": nx} for q, k, r, nx in prog["delta"]],
            "supply_head_by_q": {"q%d" % q: h for q, h in prog["supply"].items()}, "note": prog.get("note", "")}


# ---------------------------------------------------------------- A2
def oracle_rows(task, exs, prog, with_eos):
    """rows (example, t, one-hot dependency on the supply head's read position) on the scored steps"""
    import tasks as T
    import run as R
    tens = program_tensors(prog)
    rows = []
    for j in range(0, len(exs), 100):
        x, y = R.make_batch(exs[j:j + 100])
        P, Qt = l1_paths(x, prog, tens)
        for b in range(x.shape[0]):
            for t in (y[b] != -100).nonzero()[:, 0].tolist():
                if not with_eos and int(y[b, t]) == T.EOS:
                    continue
                h = prog["supply"][int(Qt[b, t])]
                s = np.zeros(t + 1)
                s[int(P[b, h, t])] = 1.0
                rows.append((j + b, t, s, s))
    return rows


def l0_compile(exs, rows):
    """stage1/c3_compile.py steps 3 (13.1-3) on given dependency rows: best table, greedy cover over 3 heads"""
    import c3_compile as CC
    NM, NC = len(MOVES), len(KINDS)
    S = CC.dense(rows, 2)
    ar = np.arange(len(rows))
    pres = CC.present_classes(exs, rows)
    combos = list(itertools.product(range(NM), repeat=len(pres)))
    cols = []
    for cmb in combos:
        col = [0] * NC
        for c, m in zip(pres, cmb):
            col[c] = m
        cols.append(col)
    P, n_moves = CC.simulate(exs, rows, cols)
    P = P.numpy()
    allcols = list(itertools.product(range(NM), repeat=NC))
    weights = [NM ** (len(pres) - 1 - k) for k in range(len(pres))]
    to_combo = np.array([sum(col[c] * w for c, w in zip(pres, weights)) for col in allcols])
    Sg = S.copy()
    chosen, per = [], []
    for j in range(H):
        full = Sg[ar[None, :], P].mean(1)[to_combo]
        best = int(np.argmax(full))
        col = list(allcols[best])
        chosen.append(col)
        per.append({"column": {KINDS[c]: MOVES[col[c]] for c in range(NC)}, "score_after_cover": float(full[best]),
                    "columns_tied_at_best": int((full == full[best]).sum())})
        Sg[ar, P[int(to_combo[best])]] = 0.0
    pcomp = [P[int(to_combo[allcols.index(tuple(c))])] for c in chosen]
    tot, _ = CC.table_score(S, pcomp)
    return chosen, per, tot, {"present_classes": [KINDS[c] for c in pres], "distinct_paths_simulated": len(cols)}


def cmd_a2(a):
    install(a.task)
    import tasks as T
    import c1a
    import h0a
    torch.set_num_threads(1)
    prog = PROGRAMS[a.task]
    exs = T.train_set(a.task, 100000, SEED_DATA_A2)[:2000]
    evs = T.eval_sets(a.task, 2000, 500)
    res = {"task": a.task, "data": "train_set(seed %d)[:2000] (c3 method)" % SEED_DATA_A2, "variants": {}}
    for with_eos in (False, True):
        rows = oracle_rows(a.task, exs, prog, with_eos)
        table, per, cover, info = l0_compile(exs, rows)
        mv = c1a.moving(table)
        d = d_check(a.task, lambda x: (c1a.read_paths(x, table), torch.zeros(x.shape[0], x.shape[1], dtype=torch.long)),
                    mv, evs, use_q=False)
        any_conf = not d["conflicts_0_everywhere"]
        lab = "with_eos_step" if with_eos else "without_eos_step"
        res["variants"][lab] = {"output_steps": len(rows), "best_l0_table": table, "per_head": per,
                                "coverage": cover, "moving_heads": mv, "d_without_q": d,
                                "l0_outside": bool(cover < 0.99 or any_conf),
                                "why": {"coverage_lt_0.99": bool(cover < 0.99), "d_conflict_gt_0": any_conf}, **info}
        print(a.task, lab, "coverage %.4f" % cover, "d conflicts any:", any_conf, "table", table, flush=True)
        for s, v in d["sets"].items():
            print("   ", s, v, flush=True)
    v = [x["l0_outside"] for x in res["variants"].values()]
    res["l0_outside_same_in_both_variants"] = v[0] == v[1]
    res["a2_l0_outside"] = v[0] if v[0] == v[1] else None
    res["env"] = h0a.env(["stage3/l1.py", "stage3/l_tasks.py", "stage3/l_adapter.py"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("a2_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(a.task, "A2 L0 outside:", res["a2_l0_outside"], "(both variants agree: %s)" % res["l0_outside_same_in_both_variants"])


# ---------------------------------------------------------------- D student
class L1Student(nn.Module):
    def __init__(self, vocab, d, heads, layers, program, q_zero=False, **_):
        super().__init__()
        import models as M
        self.kind = "l1read_q0" if q_zero else "l1read"
        self.program, self.q_zero = program, q_zero
        self.prog = PROGRAMS[program]
        self.tens = program_tensors(self.prog)
        self.moving = moving(self.prog)
        self.tok = nn.Embedding(vocab, d)
        self.R = nn.ModuleList([nn.Linear(d, d, bias=False) for _ in self.moving])
        self.S = nn.Linear(d, d, bias=False)
        self.F = nn.Parameter(torch.randn(len(self.moving), d) * 0.02)
        self.Wq = nn.Embedding(self.prog["Q"], d)                               # onehot(q_t) -> d
        self.blocks = nn.ModuleList([M.Block(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)

    def inputs(self, tokens):
        e = self.tok(tokens)
        P, Qt = l1_paths(tokens, self.prog, self.tens)
        if self.q_zero:
            Qt = torch.zeros_like(Qt)
        bits = segment_bits(tokens, P).to(e.dtype)
        u = e + self.Wq(Qt)
        for k, (r, j) in enumerate(zip(self.R, self.moving)):
            u = u + r(e.gather(1, P[:, j, :, None].expand(-1, -1, e.shape[-1])) + bits[:, j, :, None] * self.F[k])
        sh = torch.zeros_like(u)
        sh[:, 1:] = self.S(u[:, :-1])
        return u + sh

    def forward(self, tokens, offset=None, recur=None):
        x = self.inputs(tokens)
        for b in self.blocks:
            x = b(x)
        return self.head(self.ln(x))


def fwd_flops(kind, cfg, B, Tlen, V):
    """C-1 transformer formula (stage2/c1a.fwd_flops, kind hardread): attention + 24 d^2 per token and layer + head,
    plus 2 d^2 per token for each R_h of a moving head and for S; the q embedding is a look-up (no FLOPs)"""
    d, L = cfg["d"], cfg["layers"]
    nr = len(moving(PROGRAMS[cfg["program"]])) + 1
    return B * Tlen * (2 * 12 * d * d * L + 2 * d * V) + 4 * B * Tlen * Tlen * d * L + B * Tlen * 2 * d * d * nr


def register(program):
    import models as M
    for arm, k in ARMS.items():
        M.SCALES[k] = {"1M": dict(M.SCALES["abacus"]["1M"], program=program, q_zero=(arm == "q0"))}
    inner = M.build

    def build(kind, vocab, digit_ids, cfg):
        if kind in ARMS.values():
            return L1Student(vocab, **cfg)
        return inner(kind, vocab, digit_ids, cfg)
    M.build = build


PATCHES = [
    ('"pf_search"), required=True)', '"pf_search", "l1read", "l1read_q0"), required=True)'),
    ('def fwd_flops(kind, cfg, B, Tlen, V, recur=None):\n',
     'def fwd_flops(kind, cfg, B, Tlen, V, recur=None):\n'
     '    if kind in ("l1read", "l1read_q0"):                     # 3-0 D (stage3/l1.py)\n'
     '        import l1\n'
     '        return l1.fwd_flops(kind, cfg, B, Tlen, V)\n'),
    ('"pf_cont": "none (soft head distributions over the tape; recurrence over steps)"}[a.kind]',
     '"pf_cont": "none (soft head distributions over the tape; recurrence over steps)",\n'
     '                         "l1read": "NoPE attention; input + hard reads of the hand L1 program (R_h, segment '
     'bits) + onehot(q_t) + token shift S (stage3/l1.py, DESIGN 3)",\n'
     '                         "l1read_q0": "as l1read with q_t = 0 at every step (D control)"}[a.kind]'),
]


def run_dir(task, arm):
    return OUT / ("l30_%s__%s__1M__s%d__N100000__hand" % (task, ARMS[arm], SEED_STUDENT))


def cmd_train(a):
    install(a.task)
    register(a.task)
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", ARMS[a.arm], "--scale", "1M", "--seed", str(SEED_STUDENT), "--N", "100000",
            "--max-steps", os.environ.get("L30_MAX_STEPS", "20000"), "--phase", "l30", "--out-root", str(OUT),
            "--threads", "1", "--tag", "hand", "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


# ---------------------------------------------------------------- B
def base_dir(task, kind):
    return OUT / ("l30_%s__%s__1M__s0__N100000" % (task, kind))


def cmd_b(a):
    install(a.task)
    import tasks as T
    import models as M
    import c3_compile as CC
    import h0a
    torch.set_num_threads(1)
    d = base_dir(a.task, "rope")
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    cfg = ck["cfg"]
    m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], cfg)
    m.load_state_dict(ck["model"])
    m.eval()
    exs = T.train_set(a.task, 100000, 0)[:CC.N_EX]
    rows, flops, n_bwd, maxdiff = CC.extract(m, cfg, exs)
    S = CC.dense(rows, 2)
    prog = PROGRAMS[a.task]
    tens = program_tensors(prog)
    import run as R
    want = {}
    for r, (i, t, _, _) in enumerate(rows):
        want.setdefault(i, []).append((t, r))
    ph = np.zeros((H, len(rows)), dtype=np.int64)
    ids = sorted(want)
    for c0 in range(0, len(ids), 100):
        bid = ids[c0:c0 + 100]
        x, _ = R.make_batch([exs[i] for i in bid])
        P, _ = l1_paths(x, prog, tens)
        for bi, i in enumerate(bid):
            for t, r in want[i]:
                ph[:, r] = P[bi, :, t].numpy()
    stay = np.zeros((H, len(rows)), dtype=np.int64)
    c_dep, c_per = CC.table_score(S, list(ph))
    s_dep, s_per = CC.table_score(S, list(stay))
    res = {"task": a.task, "teacher": {"run": d.name, "step": ck["step"], "acc": fin["judgment"]["acc"],
                                       "train_flops_to_judgment": ck["train_flops_cum"]},
           "examples": len(exs), "output_steps": len(rows), "dependency": "input gradient (c3 design 13)",
           "extraction": {"flops": flops, "backward_passes": n_bwd, "manual_forward_max_abs_logit_diff": maxdiff},
           "hand_program": {"coverage": c_dep, "per_head": c_per},
           "all_stay": {"coverage": s_dep, "per_head": s_per},
           "ratio": c_dep / s_dep if s_dep > 0 else None, "b_pass": bool(c_dep >= 2 * s_dep),
           "env": h0a.env(["stage3/l1.py"])}
    (OUT / ("b_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("hand_program", "all_stay", "ratio", "b_pass")}))


# ---------------------------------------------------------------- report
def jload(p):
    return json.loads(p.read_text()) if p.exists() else None


def cmd_report(a):
    rows, passed = [], 0
    for t in ALL_TASKS:
        a1, a2 = jload(OUT / ("a1_%s.json" % t)), jload(OUT / ("a2_%s.json" % t))
        fq, fq0 = jload(run_dir(t, "q") / "final.json"), jload(run_dir(t, "q0") / "final.json")
        b = jload(OUT / ("b_%s.json" % t))
        base = {k: jload(base_dir(t, k) / "final.json") for k in ("abacus", "rope", "looped_rr", "gru")}
        r = {"task": t, "verdict_task": t in VERDICT_TASKS}
        r["A1"] = a1 and a1["a1_all"]
        r["A2"] = a2 and a2["a2_l0_outside"]
        if fq:
            acc = fq["judgment"]["acc"]
            labs = list(acc)
            r["D_acc"], r["D_q0_acc"] = acc, fq0 and fq0["judgment"]["acc"]
            r["D"] = acc[labs[1]] >= 0.90 and acc[labs[2]] >= 0.90
            r["D_steps"] = (fq["judgment"]["step"], fq["steps"])
        if all(base.values()):
            import baseline_table as BT
            accs = {k: BT.judged(base_dir(t, k))[1] for k in base}
            labs = list(accs["rope"])
            best = {l: max(v[l] for v in accs.values()) for l in labs}
            r["C_best"] = best
            r["C_by_kind"] = accs
            r["C"] = best[labs[2]] <= 0.60
            r["budget_20000"] = max(f["train_flops"] / f["steps"] * 20000 for f in base.values())
        if b:
            r["B_ratio"], r["B"] = b["ratio"], b["b_pass"]
        if t in VERDICT_TASKS:
            r["pass"] = all(r.get(k) is True for k in ("A1", "A2", "D", "C", "B"))
            passed += bool(r["pass"])
        rows.append(r)
    out = {"design": "stage3/DESIGN.md 5.3", "tasks": rows, "verdict_tasks_passed": passed, "answer_yes": passed >= 3}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("a0")
    q.add_argument("--task", choices=C1_TASKS, required=True)
    for name in ("a1", "a2", "b"):
        q = sp.add_parser(name)
        q.add_argument("--task", choices=ALL_TASKS if name == "a1" else VERDICT_TASKS, required=True)
    q = sp.add_parser("train")
    q.add_argument("--task", choices=ALL_TASKS, required=True)
    q.add_argument("--arm", choices=tuple(ARMS), required=True)
    q.add_argument("--resume", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"a0": cmd_a0, "a1": cmd_a1, "a2": cmd_a2, "train": cmd_train, "b": cmd_b, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
