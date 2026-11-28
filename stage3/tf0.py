"""TF-0: teacher-free structure discovery (stage3/DESIGN.md 12.2, 12.3; 12.5 takes precedence).  No training.

Per task (addition, copy, mul1, prefix_sum, reverse -- the judged formats; reverse = H-0 BOS):
  data       the stage-1 training set (N = 100,000, lengths 1-10), seed 0 (recorded choice: the baseline seed);
             fit = every example of length 1-7, select = every example of length 8-10 (12.5-2); length = the draw's
             bin coordinate (addition: the longer operand).  No teacher, dependency, hand table or longer data.
  space      L0: a head = one move (stay, right, left, next_sep, start, cont) per token class; the classes that occur
             in the task's fit sequences are the cells (others: stay); columns = 6^(classes).
  path       a column's read positions at every scored step t and at t-1 on the fit set; columns with the same path are
             one (12.5-1); representative = fewest non-stay cells, then the column lexicographically.  m = #paths.
  score      key = (x_t, per head the masked read at t and t-1; masked = the read if the head's segment bit is 1, else
             the empty symbol); table from the fit scored steps (conflict -> the most frequent output, ties -> the
             smallest output id); score = fraction of the select scored steps (<eos> included) predicted exactly
             (a key not in the table is wrong).
  selection  best single path; every pair of distinct paths (stop and report before the pairs if m > 2,000); a third
             head added greedily to the best pair while the gain is >= 0.001; the pair is used only if it beats the
             single by >= 0.001.  Ties: fewer non-stay cells in total, then the sorted column tuple.
Then H' (stage3/l2b_hprime.py, 11.8-11.10: minimal sufficient key over the full training set) on the selected routing
and the 11.8 checks: closure on 100,000 long random sequences (addition 4-100, mul1 5-50 = the 11.7 sets; others
lengths 11-40, uniform, seed "TF-0:closure:<task>"); K(L) canonical exhaustive 1.000 (addition L = 3, mul1 L = 4;
copy / prefix_sum / reverse: every digit string of length 1-5, recorded choice); confirmation 1.000 (addition M 1-100,
mul1 M 1-50, others the stage-2 out-of-distribution evaluation bins 11-20 / 21-30 / 31-40).
Records: m, single / pair / triple scores, the hand table's score (same method), hand-path inclusion, equality with the
C-1 compiled tables, CPU seconds.

  python stage3/tf0.py run --task addition|copy|mul1|prefix_sum|reverse   -> results/TF-0/<task>/
"""
from __future__ import annotations
import argparse
import itertools
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

import numpy as np                                                   # noqa: E402

OUT = pathlib.Path(os.environ.get("TF0_OUT", HERE / "results" / "TF-0"))
TASKS = ("addition", "copy", "mul1", "prefix_sum", "reverse")
MODULE = {"addition": "add", "mul1": "mul1"}
SEED = 0
FIT, SEL = (1, 7), (8, 10)
M_LIMIT = 2000
GAIN = 0.001
KL_OTHER = 5
EMPTY = -1


def setup(task):
    import torch
    import c0a
    torch.set_num_threads(1)
    c0a.install(task)
    if task == "addition":                          # c1a.separators / class ids need no adapter; keep stage-1 tokens
        pass


def training(task, n=100000):
    """[(prompt ids, answer ids + <eos>, length)] = T.train_set(task, n, SEED) with the draw's length"""
    import tasks as T
    rng = random.Random("train:%s:%d" % (task, SEED))
    lo, hi = T.SPEC[task]["train"]
    out = []
    for _ in range(n):
        p, a, L = T.draw(task, rng, lo, hi, train_dist=True)
        e = T.encode(p, a)
        out.append((e[0], e[1], L))
    ref = T.train_set(task, min(n, 200), SEED)                       # the same sequences as the stage-1 set
    assert all(list(p) == list(r[0]) and list(a) == list(r[1]) for (p, a, _), r in zip(out, ref))
    return out


# ---------------------------------------------------------------- multi-column paths
def batch_paths(x, tab):
    """head positions after the move at every step for K columns at once: [B, K, T] (c1a.read_paths with K heads)"""
    import torch
    import tasks as T
    import pf as PFM
    B, Tn = x.shape
    dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
    cls = PFM.token_classes(x, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]], T.TOK[T.NODES[-1]] + 1)
    issep = torch.isin(x, torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]]))
    K = tab.shape[0]
    h = torch.zeros(B, K, dtype=torch.long)
    out = torch.zeros(B, K, Tn, dtype=torch.long)
    for t in range(Tn):
        cand = PFM.candidates(x, t, h, x[:, t], issep)
        h = cand.gather(2, tab[:, cls[:, t]].T[:, :, None])[:, :, 0]
        out[:, :, t] = h
    return out


def present_classes(exs):
    import torch
    import tasks as T
    import pf as PFM
    import run as R
    seen = set()
    for j in range(0, len(exs), 4096):
        x, y = R.make_batch([(p, a) for p, a, _ in exs[j:j + 4096]])
        dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
        cls = PFM.token_classes(x, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]], T.TOK[T.NODES[-1]] + 1)
        last = (y != -100).long().cumsum(1).argmax(1)               # last scored step per row
        valid = torch.arange(x.shape[1])[None, :] <= last[:, None]
        seen |= set(cls[valid].unique().tolist())
    return sorted(seen)


def columns(classes):
    out = []
    for mv in itertools.product(range(6), repeat=len(classes)):
        row = [0] * 7
        for c, m in zip(classes, mv):
            row[c] = m
        out.append(tuple(row))
    return out


def nonstay(col):
    return sum(m != 0 for m in col)


class Steps:
    """scored steps of a set of examples, with per-column positions computed on demand"""

    def __init__(self, exs, bs=2048):
        import run as R
        self.batches = []
        X, Y = [], []
        for j in range(0, len(exs), bs):
            x, y = R.make_batch([(p, a) for p, a, _ in exs[j:j + bs]])
            rows, ts = (y != -100).nonzero(as_tuple=True)
            self.batches.append((x, rows, ts))
            X.append(x[rows, ts].numpy())
            Y.append(y[rows, ts].numpy())
        self.x, self.y = np.concatenate(X), np.concatenate(Y)
        self.n = len(self.y)

    def positions(self, cols):
        """[K, n, 2] positions at (t, t-1), and masked reads [K, n, 2]"""
        import torch
        import c1a
        tab = torch.tensor(cols)
        P, Mr = [], []
        for x, rows, ts in self.batches:
            pa = batch_paths(x, tab)                                  # [B, K, T]
            g = torch.cumsum(c1a.separators(x).long(), 1)
            import tasks as T
            t0 = (x == T.TOK["="]).float().argmax(1)
            gp = g[:, None, :].expand(-1, pa.shape[1], -1).gather(2, pa)          # [B, K, T]
            ref = gp.gather(2, t0[:, None, None].expand(-1, pa.shape[1], 1))
            bits = gp == ref
            ps, ms = [], []
            for tt in (ts, ts - 1):
                pos = pa[rows, :, tt]                                 # [n, K]
                rd = x[rows[:, None], pos]
                b = bits[rows, :, tt]
                ps.append(pos)
                ms.append(torch.where(b, rd, torch.full_like(rd, EMPTY)))
            P.append(torch.stack(ps, -1))
            Mr.append(torch.stack(ms, -1))
        P = torch.cat(P).permute(1, 0, 2).to(torch.int16).numpy()    # [K, n, 2]
        Mr = torch.cat(Mr).permute(1, 0, 2).to(torch.int16).numpy()
        return P, Mr


def dense(v):
    u, inv = np.unique(v, return_inverse=True)
    return inv.astype(np.int64), len(u)


# ---------------------------------------------------------------- scoring
class Scorer:
    def __init__(self, fit, sel):
        allx = np.concatenate([fit.x, sel.x])
        xu = np.unique(allx)
        self.fx, self.sx = np.searchsorted(xu, fit.x), np.searchsorted(xu, sel.x)
        self.nx = len(xu)
        yu = np.unique(np.concatenate([fit.y, sel.y]))
        self.fy, self.sy = np.searchsorted(yu, fit.y), np.searchsorted(yu, sel.y)
        self.ny = len(yu)
        self.nfit, self.nsel = fit.n, sel.n

    def score(self, fkey, skey, nk):
        """fkey/skey dense keys in [0, nk); majority table from fit; accuracy on sel"""
        ny = self.ny
        if nk * ny <= 30_000_000:
            cnt = np.bincount(fkey * ny + self.fy, minlength=nk * ny).reshape(nk, ny)
            best = cnt.argmax(1)
            seen = cnt.max(1) > 0
            return float(((best[skey] == self.sy) & seen[skey]).mean())
        u, c = np.unique(fkey * ny + self.fy, return_counts=True)
        k, yv = u // ny, u % ny
        order = np.lexsort((yv, -c, k))                              # per key: most frequent, then smallest output
        k, yv = k[order], yv[order]
        first = np.ones(len(k), dtype=bool)
        first[1:] = k[1:] != k[:-1]
        tk, ty = k[first], yv[first]
        pos = np.clip(np.searchsorted(tk, skey), 0, len(tk) - 1)
        hit = tk[pos] == skey
        return float((hit & (ty[pos] == self.sy)).mean())


def codes_of(Mf, Ms):
    """per column: dense code of (masked read t, masked read t-1) on fit and sel (shared dictionary)"""
    a = np.concatenate([Mf, Ms]).astype(np.int64)
    c = (a[:, 0] + 2) * 512 + (a[:, 1] + 2)
    d, n = dense(c)
    dt = np.uint8 if n <= 256 else np.int32
    return d[:len(Mf)].astype(dt), d[len(Mf):].astype(dt), n


# ---------------------------------------------------------------- H' on a routing (generic over the five tasks)
def exhaustive_other(task, L):
    """every digit string of length 1..L in the judged format (prompt, answer) -- copy / prefix_sum / reverse"""
    import g_tasks as G
    out = []
    for n in range(1, L + 1):
        for s in itertools.product("0123456789", repeat=n):
            s = list(s)
            if task == "copy":
                out.append((s + ["="], list(s)))
            elif task == "reverse":
                import h_tasks as HT
                out.append(([HT.BOS] + s + ["="], s[::-1]))
            else:
                acc, a = 0, []
                for v in s:
                    acc = (acc + int(v)) % 10
                    a.append(str(acc))
                out.append((s + ["="], a))
    return out


def long_other(task, n):
    import tasks as T
    rng = random.Random("TF-0:closure:%s" % task)
    return [T.draw(task, rng, 11, 40)[:2] for _ in range(n)]


def hprime(task, table, train, d, res):
    """stage3/l2b_hprime.cmd_search on (task, routing table) with the 11.8 checks of TF-0"""
    import torch
    import tasks as T
    import c1a
    import l2b_h as H
    import l2b_hprime as HP
    import recomb as RC
    t1 = time.time()
    names = HP.cell_names(table)
    F, Y, _ = HP.features_ids([(p, a) for p, a, _ in train], table)
    coder = HP.Coder(F)
    U = np.unique(np.column_stack([F, Y]), axis=0)
    C, Yu = coder.codes(U[:, :-1]), U[:, -1]
    yv, yd = np.unique(Yu, return_inverse=True)
    ny = len(yv)
    cat = []
    for cfg in HP.all_configs(len(names)):
        cols = HP.config_cols(cfg)
        if cols:
            s = np.unique(coder.key(C, cols) * ny + yd)
            kp = s // ny
            nk = 1 + int(np.count_nonzero(np.diff(kp)))
            det = nk == len(s)
        else:
            nk, det = 1, ny == 1
        cat.append((HP.config_size(cfg), nk, HP.config_orig(cfg), cols, cfg, det))
    cat.sort(key=lambda z: (z[0], z[1], z[2], z[3]))
    dets = [z for z in cat if z[5]]
    hp = {"training_steps": int(len(F)), "configurations": len(cat), "deterministic": len(dets),
          "enumeration_seconds": round(time.time() - t1, 1)}
    res["Hprime"] = hp
    if not dets:
        hp["S"] = None
        return False
    S = dets[0]
    cfg, cols = S[4], S[3]
    ky, out = HP.build_table(coder.key(coder.codes(F), cols), Y)
    space = 1
    for c in cols:
        space *= len(coder.vals[c])
    hp["S"] = {"config": HP.config_str(cfg, names), "size": S[0], "T_S_size": int(len(ky)),
               "T_S_over_product_space": len(ky) / space, "feature_columns": cols}
    np.savez_compressed(d / "T_S.npz", keys=ky, out=out, cols=np.array(cols))
    print("H' S", hp["S"], round(time.time() - t1), flush=True)
    # closure
    t1 = time.time()
    exL = (H.long_random(MODULE[task], 100000, "L2b-0:closure:%s" % MODULE[task]) if task in MODULE
           else long_other(task, 100000))
    r = HP.tf_check(exL, table, coder, cols, ky, out)
    miss = ~r["hit"]
    first = {}
    for i in np.nonzero(miss)[0]:
        if int(r["k"][i]) not in first and len(first) < 50:
            first[int(r["k"][i])] = i
    hp["closure"] = {"sequences": len(exL), "lengths": (list(H.LONG[MODULE[task]]) if task in MODULE else [11, 40]),
                     "scored_steps": int(len(r["k"])), "steps_with_key_not_in_T_S": int(miss.sum()),
                     "distinct_keys_not_in_T_S": int(len(np.unique(r["k"][miss]))),
                     "sequences_with_a_missing_key": int(len(np.unique(r["S"][miss]))),
                     "wrong_steps_on_present_keys": int((r["hit"] & ~r["ok"]).sum()),
                     "missing_keys": [HP.decode_cfg_key(r["F"][i], cfg, names) for i in first.values()],
                     "seconds": round(time.time() - t1, 1)}
    print("closure", {k: v for k, v in hp["closure"].items() if k != "missing_keys"}, flush=True)
    # K(L)
    t1 = time.time()
    if task in MODULE:
        exK, L = H.exhaustive(MODULE[task], True), H.KL[MODULE[task]]
    else:
        exK, L = exhaustive_other(task, KL_OTHER), KL_OTHER
    r = tf = HP.tf_check(exK, table, coder, cols, ky, out)
    bad = ~r["ok"]
    first = {}
    for i in np.nonzero(bad)[0]:
        if int(r["k"][i]) not in first and len(first) < 50:
            first[int(r["k"][i])] = i
    hp["KL"] = {"L": L, "sequences": len(exK), "scored_steps": int(len(r["k"])), "wrong_steps": int(bad.sum()),
                "missing_key_steps": int((~r["hit"]).sum()), "step_accuracy": float(r["ok"].mean()),
                "wrong_keys": [{"key": HP.decode_cfg_key(r["F"][i], cfg, names),
                                "T_S": ("missing" if not r["hit"][i] else T.VOCAB[int(r["o"][i])]),
                                "contract": T.VOCAB[int(r["Y"][i])]} for i in first.values()],
                "seconds": round(time.time() - t1, 1)}
    print("KL", {k: v for k, v in hp["KL"].items() if k != "wrong_keys"}, flush=True)
    # confirmation
    hp["confirm"] = {}
    if task in MODULE:
        sets = {}
        for lo, hi in RC.M_BINS[MODULE[task]]:
            rng = random.Random("L2b-0:M:%s:%d-%d" % (MODULE[task], lo, hi))
            sets["%d-%d" % (lo, hi)] = [RC.module_example(MODULE[task], rng, lo, hi) for _ in range(RC.M_N)]
    else:
        ev = T.eval_sets(task, 10, 500)
        sets = {k: [([T.VOCAB[i] for i in p], [T.VOCAB[i] for i in a[:-1]]) for p, a in v]
                for k, v in ev.items() if k.startswith("ood")}
    for lab, exs in sets.items():
        r = HP.tf_check(exs, table, coder, cols, ky, out)
        dec = HP.table_decode([HP._ids(p) for p, _ in exs], table, coder, cols, ky, out,
                              max_new=max(len(a) for _, a in exs) + 3)
        g_ok = np.array([st == "ok" and o == HP._ids(a) for (o, st), (_, a) in zip(dec, exs)])
        hp["confirm"][lab] = {"examples": len(exs), "accuracy_teacher_forced": float(r["ex_ok"].mean()),
                              "accuracy_greedy": float(g_ok.mean()),
                              "greedy_equals_teacher_forced": bool((g_ok == r["ex_ok"]).all())}
        print("confirm", lab, hp["confirm"][lab], flush=True)
    return (hp["closure"]["steps_with_key_not_in_T_S"] == 0 and hp["KL"]["wrong_steps"] == 0
            and all(v["accuracy_teacher_forced"] == 1.0 and v["accuracy_greedy"] == 1.0
                    for v in hp["confirm"].values()))


# ---------------------------------------------------------------- main
def cmd_run(a):
    import torch
    import c0a
    import c1
    import c1a
    import h0a
    task = a.task
    setup(task)
    T0, C0 = time.time(), time.process_time()
    d = OUT / task
    d.mkdir(parents=True, exist_ok=True)
    (d / "env.json").write_text(json.dumps(h0a.env(["stage3/tf0.py", "stage3/l2b_hprime.py"]), indent=1))
    train = training(task, int(os.environ.get("TF0_N", "100000")))   # env: smoke only
    fit = [e for e in train if FIT[0] <= e[2] <= FIT[1]]
    sel = [e for e in train if SEL[0] <= e[2] <= SEL[1]]
    classes = present_classes(fit)
    cols = columns(classes)
    res = {"design": "stage3/DESIGN.md 12.3 with 12.5", "task": task, "training": "T.train_set(%r, 100000, %d)" %
           (task, SEED), "fit_examples": len(fit), "select_examples": len(sel), "classes": classes,
           "columns": len(cols)}
    (d / "config.json").write_text(json.dumps({k: res[k] for k in ("design", "task", "training", "classes", "columns")}
                                              | {"fit_lengths": FIT, "select_lengths": SEL, "m_limit": M_LIMIT,
                                                 "gain": GAIN}, indent=1))
    Fs, Ss = Steps(fit), Steps(sel)
    res["fit_scored_steps"], res["select_scored_steps"] = Fs.n, Ss.n
    print(task, "classes", classes, "columns", len(cols), "fit", len(fit), Fs.n, "sel", len(sel), Ss.n, flush=True)
    # (a) paths on the fit set -> equivalence classes
    rs = np.random.default_rng(12345)
    W1 = rs.integers(1, 2 ** 31, size=(Fs.n, 2), dtype=np.int64)
    W2 = rs.integers(1, 2 ** 31, size=(Fs.n, 2), dtype=np.int64)
    sig = {}
    CH = 16
    for j in range(0, len(cols), CH):
        P, _ = Fs.positions(cols[j:j + CH])
        P = P.astype(np.int64)
        h1 = (P * W1[None]).sum((1, 2))
        h2 = (P * W2[None]).sum((1, 2))
        for k in range(P.shape[0]):
            sig.setdefault((int(h1[k]), int(h2[k])), []).append(cols[j + k])
    reps = sorted(min(v, key=lambda c: (nonstay(c), c)) for v in sig.values())
    reps.sort(key=lambda c: (nonstay(c), c))
    m = len(reps)
    res["m_distinct_paths"] = m
    res["path_seconds"] = round(time.time() - T0, 1)
    print("m", m, round(time.time() - T0), flush=True)
    if m > M_LIMIT:
        res["stopped"] = "m > %d: report before the pair enumeration (12.5-1)" % M_LIMIT
        (d / "final.json").write_text(json.dumps(res, indent=1))
        return
    # codes of every representative on fit and select
    sc = Scorer(Fs, Ss)
    codes = []
    for j in range(0, m, CH):
        _, Mf = Fs.positions(reps[j:j + CH])
        _, Ms = Ss.positions(reps[j:j + CH])
        for k in range(Mf.shape[0]):
            codes.append(codes_of(Mf[k], Ms[k]))

    def score_set(idx):
        fk = sc.fx.copy()
        sk = sc.sx.copy()
        nk = sc.nx
        for i in idx:
            cf, cs, n = codes[i]
            fk, sk, nk = fk * n + cf.astype(np.int64), sk * n + cs.astype(np.int64), nk * n
        return sc.score(fk, sk, nk)

    def tie(idx):
        return (sum(nonstay(reps[i]) for i in idx), tuple(sorted(reps[i] for i in idx)))
    t1 = time.time()
    singles = [(score_set([i]), i) for i in range(m)]
    best1 = max(z[0] for z in singles)
    s1 = min([z for z in singles if z[0] == best1], key=lambda z: tie([z[1]]))
    res["single"] = {"score": s1[0], "column": reps[s1[1]], "seconds": round(time.time() - t1, 1),
                     "top": [{"score": s, "column": reps[i]} for s, i in sorted(singles, key=lambda z: -z[0])[:10]]}
    print("single", res["single"]["score"], res["single"]["column"], flush=True)
    t1 = time.time()
    bestp, bp = -1.0, None
    allp = []
    for i in range(m):
        for j in range(i + 1, m):
            s = score_set([i, j])
            allp.append((s, i, j))
            if s > bestp or (s == bestp and tie([i, j]) < tie(list(bp))):
                bestp, bp = s, (i, j)
    allp.sort(key=lambda z: -z[0])
    res["pair"] = {"score": bestp, "columns": [reps[i] for i in bp], "pairs": len(allp),
                   "seconds": round(time.time() - t1, 1),
                   "top": [{"score": s, "columns": [reps[i], reps[j]]} for s, i, j in allp[:10]]}
    print("pair", bestp, res["pair"]["columns"], round(time.time() - t1), flush=True)
    t1 = time.time()
    chosen, cur = list(bp), bestp
    trip = None
    best3, b3 = -1.0, None
    for k in range(m):
        if k in chosen:
            continue
        s = score_set(chosen + [k])
        if s > best3 or (s == best3 and tie(chosen + [k]) < tie(chosen + [b3])):
            best3, b3 = s, k
    res["triple"] = {"score": best3, "added_column": reps[b3] if b3 is not None else None,
                     "gain": best3 - cur, "seconds": round(time.time() - t1, 1)}
    print("triple", best3, best3 - cur, flush=True)
    if best3 - cur >= GAIN:
        chosen, cur = chosen + [b3], best3
        trip = True
    if bestp - s1[0] >= GAIN:
        sel_idx, sel_score = chosen, cur
    else:
        sel_idx, sel_score = [s1[1]], s1[0]
    routing = [list(reps[i]) for i in sel_idx]
    table = routing + [[0] * 7 for _ in range(c1a.H - len(routing))]
    res["selected"] = {"heads": len(routing), "routing": routing, "score": sel_score,
                       "rule": "pair if pair - single >= %g, triple if gain >= %g" % (GAIN, GAIN)}
    res["search_cpu_seconds"] = round(time.process_time() - C0, 1)
    res["search_wall_seconds"] = round(time.time() - T0, 1)
    # records: the hand table and the C-1 compiled tables
    hand = c0a.hand_table(task)
    hmv = c1a.moving(hand)
    hcols = [tuple(hand[j]) for j in hmv]
    _, Mfh = Fs.positions(hcols)
    _, Msh = Ss.positions(hcols)
    hc = [codes_of(Mfh[k], Msh[k]) for k in range(len(hcols))]
    fk, sk, nk = sc.fx.copy(), sc.sx.copy(), sc.nx
    for cf, cs, n in hc:
        fk, sk, nk = fk * n + cf.astype(np.int64), sk * n + cs.astype(np.int64), nk * n
    res["hand"] = {"moving_heads": [list(c) for c in hcols], "score": sc.score(fk, sk, nk)}
    Pf_sel, _ = Fs.positions([tuple(r) for r in routing])
    Ps_sel, _ = Ss.positions([tuple(r) for r in routing])
    Pf_h, _ = Fs.positions(hcols)
    Ps_h, _ = Ss.positions(hcols)
    res["hand"]["every_hand_path_in_selected_fit_and_select"] = all(
        any(np.array_equal(Pf_h[k], Pf_sel[g]) and np.array_equal(Ps_h[k], Ps_sel[g]) for g in range(len(routing)))
        for k in range(len(hcols)))
    comp = {}
    for i in (1, 2, 3):
        try:
            ct = c1.compiled(task, i)["policy"]
        except Exception as e:                                       # noqa
            comp[str(i)] = {"error": repr(e)}
            continue
        cmv = [tuple(ct[j]) for j in c1a.moving(ct)]
        Pc, _ = Fs.positions(cmv)
        Pcs, _ = Ss.positions(cmv)
        same_paths = sorted(
            [any(np.array_equal(Pc[g], Pf_sel[k]) and np.array_equal(Pcs[g], Ps_sel[k]) for g in range(len(cmv)))
             for k in range(len(routing))])
        comp[str(i)] = {"compiled_moving": [list(c) for c in cmv],
                        "literal_equal_on_present_classes_as_sets": sorted(
                            tuple(r[c] for c in classes) for r in routing) == sorted(
                            tuple(r[c] for c in classes) for r in cmv),
                        "every_selected_path_in_compiled": all(same_paths)}
    res["C1_compiled"] = comp
    print("hand", res["hand"], "C1", comp, flush=True)
    (d / "final.json").write_text(json.dumps(res, indent=1))
    # H' + checks on the full training set
    ok = hprime(task, table, train, d, res)
    res["Hprime_checks_pass"] = bool(ok)
    res["cpu_seconds_total"] = round(time.process_time() - C0, 1)
    res["wall_seconds_total"] = round(time.time() - T0, 1)
    (d / "final.json").write_text(json.dumps(res, indent=1))
    print("done", task, ok, res["cpu_seconds_total"], flush=True)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("run")
    q.add_argument("--task", choices=TASKS, required=True)
    a = p.parse_args()
    cmd_run(a)


if __name__ == "__main__":
    main()
