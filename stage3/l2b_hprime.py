"""L2b-0 H' (stage3/DESIGN.md 11.8, 11.9, 11.10): minimal sufficient local-key tables.

A module = (the C-1 compiled routing of table i, a lookup table T_S: key_S -> output token).  No gradient training.

Components at a scored step t (the step whose output is the next answer token or <eos>; stage3/l2b_h.batch_keys):
  x_t, x_{t-1}, and per cell (moving head h of the table x time t, t-1) one of 5 options (11.10):
  none, original read, masked read (the read if the head's segment bit is 1, else the empty symbol), original read +
  bit, bit only.  ("masked + bit" gives the same key as "masked" and is counted once, 11.10-2.)
  Size = atomic components (x_t 1, x_{t-1} 1, original / masked read 1, bit 1).
Enumeration: every configuration (2 x 2 x 5^(2 x heads); 3 heads = 62,500), no size cap.  Order: size, number of
distinct keys on the training data, fewer original reads first ("masked before original", 11.9/11.10), then the
sorted feature-column list lexicographically (11.8-2 "component number order").  S = the first configuration whose
key_S -> output is deterministic (0 conflicts) on the scored steps of the training data.
Training data (11.8-2: N = 100,000, lengths 1-10): the stage-1 training set of the H run of table i with the smallest
seed (230 + i), T.train_set(task, 100000, 230 + i) -- a choice recorded in the result.
Checks (11.8-4 with S): (2) closure: the long random 100,000 of 11.7-2 (stage3/l2b_h.long_random, the same label),
steps whose key_S is not in T_S = 0; (3) K(L) canonical (11.9-3) exhaustive: T_S output = contract at every scored
step (a key missing from T_S counts as wrong), 1.000; all-digit-strings K(L) recorded only; (4) M sets (11.5,
stage3/recomb, the same seeds): every bin 1.000 (teacher-forced; the greedy decoder used by R is run on the same sets
and must agree).  (1) routing: 11.9-1 (path inclusion), from stage3/results/L2b-0/H/closure_<m>_table<i>.json.

  search --module add|mul1 --table i       -> results/L2b-0/Hprime/<module>_table<i>/
"""
from __future__ import annotations
import argparse
import gzip
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

import numpy as np                                                   # noqa: E402

OUT = pathlib.Path(os.environ.get("L2B_HP_OUT", HERE / "results" / "L2b-0" / "Hprime"))
OPTS = ("none", "orig", "masked", "orig+bit", "bit")
OPT_SIZE = (0, 1, 1, 2, 1)
EMPTY = -1                                                           # the masked read of a head with segment bit 0


def data_seed(i):
    return 230 + i


# ---------------------------------------------------------------- features
def features(x, y, table):
    """per scored step: columns [x_t, x_{t-1}] + per cell (head j in moving(table), tau in (t, t-1)):
    [orig read, bit, masked read]; targets; rows; ts"""
    import torch
    import c1a
    mv = c1a.moving(table)
    P = c1a.read_paths(x, table)
    Bt = c1a.segment_bits(x, P)
    rows, ts = (y != -100).nonzero(as_tuple=True)
    assert bool((ts >= 1).all())
    cols = [x[rows, ts], x[rows, ts - 1]]
    for j in mv:
        for tt in (ts, ts - 1):
            r = x[rows, P[rows, j, tt]]
            b = Bt[rows, j, tt]
            cols += [r, b, torch.where(b == 1, r, torch.full_like(r, EMPTY))]
    return torch.stack(cols, 1).numpy(), y[rows, ts].numpy(), rows.numpy(), ts.numpy()


def features_of(exs, table, bs=1024):
    import l2b_h as H
    F, Y, S = [], [], []
    for j in range(0, len(exs), bs):
        x, y = H.encode_batch(exs[j:j + bs])
        f, t, r, _ = features(x, y, table)
        F.append(f)
        Y.append(t)
        S.append(r + j)
    return np.concatenate(F), np.concatenate(Y), np.concatenate(S)


def features_ids(exs, table, bs=1024):
    """the same for examples already in token ids (train_set output)"""
    import torch
    import run as R
    F, Y, S = [], [], []
    for j in range(0, len(exs), bs):
        x, y = R.make_batch(exs[j:j + bs])
        f, t, r, _ = features(x, y, table)
        F.append(f)
        Y.append(t)
        S.append(r + j)
    return np.concatenate(F), np.concatenate(Y), np.concatenate(S)


def cell_names(table):
    import c1a
    return ["h%d@%s" % (j, tau) for j in c1a.moving(table) for tau in ("t", "t-1")]


def config_cols(cfg):
    """cfg = (use x_t, use x_{t-1}, opt per cell) -> feature column indices"""
    ux, up, opts = cfg
    cols = ([0] if ux else []) + ([1] if up else [])
    for k, o in enumerate(opts):
        base = 2 + 3 * k
        cols += {0: [], 1: [base], 2: [base + 2], 3: [base, base + 1], 4: [base + 1]}[o]
    return cols


def config_size(cfg):
    return cfg[0] + cfg[1] + sum(OPT_SIZE[o] for o in cfg[2])


def config_orig(cfg):
    return sum(o in (1, 3) for o in cfg[2])


def config_str(cfg, names):
    parts = (["x_t"] if cfg[0] else []) + (["x_{t-1}"] if cfg[1] else [])
    parts += ["%s:%s" % (n, OPTS[o]) for n, o in zip(names, cfg[2]) if o]
    return " ".join(parts) if parts else "(empty)"


def all_configs(ncell):
    import itertools
    for ux in (0, 1):
        for up in (0, 1):
            for opts in itertools.product(range(5), repeat=ncell):
                yield (ux, up, tuple(opts))


class Coder:
    """dense codes of every feature column, fitted on the training steps; a value unseen in training -> -1"""

    def __init__(self, F):
        self.vals = [np.unique(F[:, c]) for c in range(F.shape[1])]

    def codes(self, F):
        C = np.empty(F.shape, dtype=np.int64)
        for c, v in enumerate(self.vals):
            i = np.searchsorted(v, F[:, c])
            i = np.clip(i, 0, len(v) - 1)
            C[:, c] = np.where(v[i] == F[:, c], i, -1)
        return C

    def key(self, C, cols):
        """int64 key over the columns (mixed radix); -1 where some column value was unseen in training"""
        k = np.zeros(len(C), dtype=np.int64)
        bad = np.zeros(len(C), dtype=bool)
        rad = 1
        for c in cols:
            n = len(self.vals[c])
            k = k * n + np.maximum(C[:, c], 0)
            bad |= C[:, c] < 0
            rad *= n
        assert rad < 2 ** 62
        return np.where(bad, -1, k)


def build_table(keys, Y):
    """deterministic T_S: sorted unique keys, their outputs (asserts 0 conflicts)"""
    ky, idx = np.unique(keys, return_index=True)
    out = Y[idx]
    # determinism re-check on all steps
    pos = np.searchsorted(ky, keys)
    assert bool((out[pos] == Y).all())
    return ky, out


def lookup(ky, out, keys):
    """outputs of T_S at keys; -2 where the key is not in T_S"""
    pos = np.clip(np.searchsorted(ky, keys), 0, len(ky) - 1)
    hit = (ky[pos] == keys) & (keys >= 0)
    return np.where(hit, out[pos], -2), hit


# ---------------------------------------------------------------- greedy decoding with a table module (used by R)
def table_decode(prompts, table, coder, cols, ky, out, max_new, bs=512):
    """greedy decoding of a table module, incremental.  Valid because paths, token classes, separators and segment
    bits at a position use positions <= it only, and answer-phase tokens (digits, <eos>) have the same class (5,
    answer phase) and separator flag (no) as the pad written there before decoding.  prompts: token-id lists ending
    with '='.  Returns [(answer ids without <eos>, status)], status 'ok' (<eos> produced), 'missing' (a key not in
    T_S; decoding of that row stops), 'length' (max_new tokens without <eos>)."""
    import torch
    import tasks as T
    import pf as PFM
    import c1a
    mv = c1a.moving(table)
    tab = torch.tensor(table)
    dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
    res = []
    for j0 in range(0, len(prompts), bs):
        chunk = prompts[j0:j0 + bs]
        B = len(chunk)
        plen = torch.tensor([len(p) for p in chunk])
        Tn = int(plen.max()) + max_new + 1
        buf = torch.full((B, Tn), T.PAD, dtype=torch.long)
        for i, p in enumerate(chunk):
            buf[i, :len(p)] = torch.tensor(p)
        assert bool((buf[torch.arange(B), plen - 1] == T.TOK["="]).all())
        cls = PFM.token_classes(buf, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]], T.TOK[T.NODES[-1]] + 1)
        issep = torch.isin(buf, torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]]))
        g = torch.cumsum(c1a.separators(buf).long(), 1)
        t0 = (buf == T.TOK["="]).float().argmax(1)                 # first '=' (the prompt's last token)
        h = torch.zeros(B, c1a.H, dtype=torch.long)
        G0 = torch.zeros(B, c1a.H, dtype=torch.long)
        hist = []                                                  # (x_t, reads [B,H], g(p_h(t)) [B,H]) per t
        done = torch.zeros(B, dtype=torch.bool)
        status = ["length"] * B
        for t in range(Tn - 1):
            cand = PFM.candidates(buf, t, h, buf[:, t], issep)
            h = cand.gather(2, tab[:, cls[:, t]].T[:, :, None])[:, :, 0]
            gp = g.gather(1, h)
            G0 = torch.where((t0 == t)[:, None], gp, G0)
            hist.append((buf[:, t].clone(), buf.gather(1, h), gp))
            active = (t >= plen - 1) & ~done
            if t < 1 or not bool(active.any()):
                continue
            (xc, rc, gc), (xq, rq, gq) = hist[t], hist[t - 1]
            bc, bq = (gc == G0).long(), (gq == G0).long()
            cv = [xc, xq]
            for j in mv:
                for rr, bb in ((rc, bc), (rq, bq)):
                    r, b = rr[:, j], bb[:, j]
                    cv += [r, b, torch.where(b == 1, r, torch.full_like(r, EMPTY))]
            Fv = torch.stack(cv, 1).numpy()
            o, hit = lookup(ky, out, coder.key(coder.codes(Fv), cols))
            for i in active.nonzero()[:, 0].tolist():
                if not hit[i]:
                    done[i] = True
                    status[i] = "missing"
                elif o[i] == T.EOS:
                    done[i] = True
                    status[i] = "ok"
                else:
                    buf[i, t + 1] = int(o[i])
            if bool(done.all()):
                break
        for i, p in enumerate(chunk):
            a = buf[i, len(p):].tolist()
            n = 0
            while n < len(a) and a[n] != T.PAD:
                n += 1
            res.append((a[:n], status[i]))
    return res


# ---------------------------------------------------------------- search and checks
def _ids(seq):
    import tasks as T
    return [T.TOK[t] for t in seq]


def tf_check(exs, table, coder, cols, ky, out):
    """teacher-forced T_S on string examples: per-step correctness, missing keys; per-example all-correct"""
    F, Y, S = features_of(exs, table)
    k = coder.key(coder.codes(F), cols)
    o, hit = lookup(ky, out, k)
    ok = o == Y
    bad_seq = np.unique(S[~ok])
    ex_ok = np.ones(len(exs), dtype=bool)
    ex_ok[bad_seq] = False
    return {"F": F, "Y": Y, "S": S, "k": k, "o": o, "hit": hit, "ok": ok, "ex_ok": ex_ok}


def decode_cfg_key(Frow, cfg, names):
    import tasks as T

    def tok(v):
        return "∅" if v == EMPTY else T.VOCAB[int(v)]
    parts = []
    if cfg[0]:
        parts.append("x_t=%s" % tok(Frow[0]))
    if cfg[1]:
        parts.append("x_{t-1}=%s" % tok(Frow[1]))
    for kk, (n, o) in enumerate(zip(names, cfg[2])):
        base = 2 + 3 * kk
        if o == 1:
            parts.append("%s=%s" % (n, tok(Frow[base])))
        elif o == 2:
            parts.append("%s=%s" % (n, tok(Frow[base + 2])))
        elif o == 3:
            parts.append("%s=%s,b%d" % (n, tok(Frow[base]), Frow[base + 1]))
        elif o == 4:
            parts.append("%s:b%d" % (n, Frow[base + 1]))
    return " ".join(parts)


def cmd_search(a):
    import random
    import torch
    import c0a
    import c1a
    import h0a
    import l2b_h as H
    import recomb as RC
    import tasks as T
    task = H.MODULE_TASK[a.module]
    H._setup(a.module)
    c0a.install(task)
    d = OUT / ("%s_table%d" % (a.module, a.table))
    d.mkdir(parents=True, exist_ok=True)
    t00 = time.time()
    table = H.table_of(a.module, a.table)
    names = cell_names(table)
    hand_route = json.loads((H.OUT / ("closure_%s_table%d.json" % (a.module, a.table))).read_text())["routing"]
    res = {"design": "stage3/DESIGN.md 11.8, 11.9, 11.10", "module": a.module, "table": a.table,
           "compiled_table": table, "moving_heads": c1a.moving(table), "cells": names,
           "training_data": "T.train_set(%r, 100000, %d) (the H run of table %d with the smallest seed)"
                            % (task, data_seed(a.table), a.table),
           "order": "size, distinct keys on the training steps, fewer original reads, sorted feature columns",
           "routing_11.9-1": {k: hand_route[k] for k in
                              ("every_hand_moving_head_has_a_compiled_head_with_the_same_path_1.000",
                               "hand_head_path_equal_fraction_by_compiled_head",
                               "compiled_heads_without_hand_counterpart")}}
    (d / "config.json").write_text(json.dumps({k: v for k, v in res.items()}, indent=1))
    (d / "env.json").write_text(json.dumps(h0a.env(["stage3/l2b_hprime.py", "stage3/l2b_h.py"]), indent=1))
    # training steps
    train = T.train_set(task, int(os.environ.get("L2B_HP_N", "100000")), data_seed(a.table))   # env: smoke test only
    F, Y, _ = features_ids(train, table)
    coder = Coder(F)
    U = np.unique(np.column_stack([F, Y]), axis=0)
    C, Yu = coder.codes(U[:, :-1]), U[:, -1]
    yv, yd = np.unique(Yu, return_inverse=True)
    ny = len(yv)
    res["training_steps"] = int(len(F))
    res["training_distinct_rows"] = int(len(U))
    print("train steps", len(F), "distinct rows", len(U), round(time.time() - t00), flush=True)
    # enumeration
    t1 = time.time()
    cat = []
    for cfg in all_configs(len(names)):
        cols = config_cols(cfg)
        if cols:
            kk = coder.key(C, cols)
            s = np.unique(kk * ny + yd)
            kp = s // ny
            nk = 1 + int(np.count_nonzero(np.diff(kp)))
            det = nk == len(s)
        else:
            nk, det = 1, ny == 1
        cat.append((config_size(cfg), nk, config_orig(cfg), cols, cfg, det))
    cat.sort(key=lambda z: (z[0], z[1], z[2], z[3]))
    res["enumeration"] = {"configurations": len(cat), "seconds": round(time.time() - t1, 1),
                          "deterministic": sum(z[5] for z in cat),
                          "by_size": {}}
    for sz in sorted({z[0] for z in cat}):
        zs = [z for z in cat if z[0] == sz]
        dz = [z for z in zs if z[5]]
        res["enumeration"]["by_size"][str(sz)] = {
            "configurations": len(zs), "deterministic": len(dz),
            "first_deterministic": [{"config": config_str(z[4], names), "distinct_keys": z[1]} for z in dz[:10]],
            "fewest_keys_nondeterministic": [{"config": config_str(z[4], names), "distinct_keys": z[1]}
                                             for z in [z for z in zs if not z[5]][:3]]}
    with gzip.open(d / "catalog.csv.gz", "wt") as fh:
        fh.write("rank,size,distinct_keys,orig_reads,deterministic,config\n")
        for r, z in enumerate(cat):
            fh.write("%d,%d,%d,%d,%d,%s\n" % (r, z[0], z[1], z[2], int(z[5]), config_str(z[4], names)))
    dets = [z for z in cat if z[5]]
    print("enumeration", len(cat), "deterministic", len(dets), round(time.time() - t1), flush=True)
    if not dets:
        res["S"] = None
        res["admission_checks_pass"] = False
        res["seconds"] = round(time.time() - t00, 1)
        (d / "final.json").write_text(json.dumps(res, indent=1))
        return
    S = dets[0]
    cfg, cols = S[4], S[3]
    kfull = coder.key(coder.codes(F), cols)
    ky, out = build_table(kfull, Y)
    space = 1
    for c in cols:
        space *= len(coder.vals[c])
    res["S"] = {"config": config_str(cfg, names), "cfg": [cfg[0], cfg[1], list(cfg[2])], "size": S[0],
                "feature_columns": cols, "T_S_size": int(len(ky)), "distinct_keys": S[1],
                "product_space_of_observed_component_values": space,
                "T_S_over_product_space": len(ky) / space,
                "uses_heads_without_hand_counterpart":
                    sorted({int(names[k].split("@")[0][1:]) for k, o in enumerate(cfg[2]) if o}
                           & set(hand_route["compiled_heads_without_hand_counterpart"]))}
    print("S", res["S"], flush=True)
    np.savez_compressed(d / "T_S.npz", keys=ky, out=out, cols=np.array(cols))
    # (2) closure on the long random 100,000
    t1 = time.time()
    exL = H.long_random(a.module, int(os.environ.get("L2B_HP_NLONG", "100000")), "L2b-0:closure:%s" % a.module)
    r = tf_check(exL, table, coder, cols, ky, out)
    miss = ~r["hit"]
    mk = np.unique(r["k"][miss]) if miss.any() else np.array([], dtype=np.int64)
    ex_first = {}
    for i in np.nonzero(miss)[0]:
        kv = int(r["k"][i])
        if kv not in ex_first and len(ex_first) < 50:
            ex_first[kv] = i
    res["closure"] = {"sequences": len(exL), "lengths": H.LONG[a.module], "scored_steps": int(len(r["k"])),
                      "steps_with_key_not_in_T_S": int(miss.sum()), "distinct_keys_not_in_T_S": int(len(mk)),
                      "sequences_with_a_missing_key": int(len(np.unique(r["S"][miss]))),
                      "wrong_steps_on_present_keys": int((r["hit"] & ~r["ok"]).sum()),
                      "sequence_accuracy_teacher_forced": float(r["ex_ok"].mean()),
                      "missing_keys": [decode_cfg_key(r["F"][i], cfg, names) for i in ex_first.values()],
                      "seconds": round(time.time() - t1, 1)}
    print("closure", {k: v for k, v in res["closure"].items() if k != "missing_keys"}, flush=True)
    # (3) K(L) exhaustive
    res["KL"] = {}
    for canon in (True, False):
        lab = "canonical" if canon else "all_digit_strings (record only, 11.9-3)"
        t1 = time.time()
        exK = H.exhaustive(a.module, canon)
        r = tf_check(exK, table, coder, cols, ky, out)
        bad = ~r["ok"]
        first = {}
        for i in np.nonzero(bad)[0]:
            kv = int(r["k"][i])
            if kv not in first and len(first) < 50:
                first[kv] = i
        res["KL"][lab] = {"L": H.KL[a.module], "sequences": len(exK), "scored_steps": int(len(r["k"])),
                          "wrong_steps": int(bad.sum()), "missing_key_steps": int((~r["hit"]).sum()),
                          "step_accuracy": float(r["ok"].mean()), "sequence_accuracy": float(r["ex_ok"].mean()),
                          "wrong_keys": [{"key": decode_cfg_key(r["F"][i], cfg, names),
                                          "T_S": ("missing" if not r["hit"][i] else T.VOCAB[int(r["o"][i])]),
                                          "contract": T.VOCAB[int(r["Y"][i])]} for i in first.values()],
                          "seconds": round(time.time() - t1, 1)}
        print("KL", lab, {k: v for k, v in res["KL"][lab].items() if k != "wrong_keys"}, flush=True)
    res["admission_checks_pass"] = bool(res["closure"]["steps_with_key_not_in_T_S"] == 0
                                        and res["KL"]["canonical"]["wrong_steps"] == 0
                                        and hand_route["every_hand_moving_head_has_a_compiled_head_with_the_same_path_1.000"])
    # (4) M sets (confirmation), teacher-forced and greedy
    res["M"] = {}
    for lo, hi in RC.M_BINS[a.module]:
        lab = "%d-%d" % (lo, hi)
        t1 = time.time()
        rng = random.Random("L2b-0:M:%s:%s" % (a.module, lab))
        exs = [RC.module_example(a.module, rng, lo, hi) for _ in range(int(os.environ.get("L2B_HP_NM", RC.M_N)))]
        r = tf_check(exs, table, coder, cols, ky, out)
        dec = table_decode([_ids(p) for p, _ in exs], table, coder, cols, ky, out, max_new=hi + 3)
        g_ok = np.array([st == "ok" and o == _ids(ans) for (o, st), (_, ans) in zip(dec, exs)])
        res["M"][lab] = {"examples": len(exs), "accuracy_teacher_forced": float(r["ex_ok"].mean()),
                         "accuracy_greedy": float(g_ok.mean()),
                         "greedy_equals_teacher_forced": bool((g_ok == r["ex_ok"]).all()),
                         "missing_key_steps": int((~r["hit"]).sum()),
                         "greedy_status": {s: sum(st == s for _, st in dec) for s in ("ok", "missing", "length")},
                         "seconds": round(time.time() - t1, 1)}
        print("M", lab, res["M"][lab], flush=True)
    res["M_all_1.000"] = all(v["accuracy_teacher_forced"] == 1.0 and v["accuracy_greedy"] == 1.0
                             for v in res["M"].values())
    res["seconds"] = round(time.time() - t00, 1)
    (d / "final.json").write_text(json.dumps(res, indent=1))
    print("done", res["admission_checks_pass"], res["M_all_1.000"], res["seconds"], flush=True)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("search")
    q.add_argument("--module", choices=("add", "mul1"), required=True)
    q.add_argument("--table", type=int, choices=(0, 1, 2, 3), required=True, help="0 = hand table (diagnostic)")
    a = p.parse_args()
    {"search": cmd_search}[a.cmd](a)


if __name__ == "__main__":
    main()
