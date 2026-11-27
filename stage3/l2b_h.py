"""L2b-0 H (stage3/DESIGN.md 11.6-1, 11.6-2; admission by 11.7, which replaces 11.6-3 and 11.6-4).

Students: the C-1 MLP student (kind "hardread_mlp", stage2/c1a.HardReadLM with mlp_only: 4 pre-LN MLP blocks, the C-1
input -- hard reads of the moving heads + segment bits + token shift), tables = the C-1 add / mul1 tables 1-3
(stage2/c1.compiled).  Training: stage1/run.py executed from its source exactly as stage2/c1.py cmd_train does (the
c1a.PATCHES, asserted once each), plus two textual changes for H (asserted once each; no file is edited):
  - early stop disabled (the "two consecutive in-distribution >= 0.99" stop never fires; 20,000 steps always);
  - config.json's "early_stop" field says so.
Learning lengths 1-10, N = 100,000, seeds 230 + i, 330 + i, 430 + i for table i, 20,000 steps, last checkpoint
(ckpt.pt at step 20,000; run.py with --keep-best keeps it locally, not committed).  The run's data seed = its seed.

  train --module add|mul1 --table i --seed s [--resume]
"""
from __future__ import annotations
import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

OUT = pathlib.Path(os.environ.get("L2B_H_OUT", HERE / "results" / "L2b-0" / "H"))
MODULE_TASK = {"add": "addition", "mul1": "mul1"}
H_PATCHES = [
    ('            if st["hits"] >= 2:\n                stop = "early stop',
     '            if st["hits"] >= 2 and False:              # L2b-0 H (stage3/l2b_h.py): no early stop\n'
     '                stop = "early stop'),
    ('"early_stop": "in-distribution >= 0.99 at two consecutive evaluations",',
     '"early_stop": "none (L2b-0 H, stage3/DESIGN.md 11.6-2: 20,000 steps, last checkpoint)",'),
]


def seeds(i):
    return [230 + i, 330 + i, 430 + i]


def run_dir(module, i, s):
    return OUT / ("H_%s__hardread_mlp__1M__s%d__N100000__table%d" % (MODULE_TASK[module], s, i))


def cmd_train(a):
    import c0a
    import c1
    import c1a
    task = MODULE_TASK[a.module]
    assert a.seed in seeds(a.table), (a.seed, a.table)
    c0a.install(task)                               # as stage2/c1.py: the G-0 adapter for mul1 only
    table = c1.compiled(task, a.table)["policy"]
    c1a.register(table, "M")
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in list(c1a.PATCHES) + H_PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", task, "--kind", "hardread_mlp", "--scale", "1M", "--seed", str(a.seed), "--N", "100000",
            "--max-steps", os.environ.get("L2B_H_MAX_STEPS", "20000"), "--phase", "H", "--out-root", str(OUT),
            "--threads", "1", "--tag", "table%d" % a.table, "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


# ================================================================ admission by proof (11.7)
# local key at a scored step t (the logit at t predicts an answer token or <eos>):
#   (x_t, (x[p_h(t)], b_h(t)) for the moving heads h of the module's table, x_{t-1}, (x[p_h(t-1)], b_h(t-1)))
# -- exactly the input of the MLP student at t (stage2/c1a.HardReadLM: u_t from x_t and the reads and bits at t,
# in_t = u_t + S(u_{t-1}); per-position MLP blocks; no position term), and the key of stage2/c1.py check (d).
# Encoded in one int64: 7 bits per token (vocabulary <= 128), 1 bit per segment bit.
KL = {"add": 3, "mul1": 4}
LONG = {"add": (4, 100), "mul1": (5, 50)}
CACHE = pathlib.Path(os.environ.get("L2B_CACHE", "/tmp/claude-0/-home-user-NEUMANN/87d05f95-27a9-535f-9293-"
                                    "4221906025b2/scratchpad/l2b_cache"))


def _setup(module):
    import torch
    import c0a
    torch.set_num_threads(1)
    import g_adapter                                # '*' (mul1); stage-1 token ids unchanged
    g_adapter.install()


def _num(rng, ndig):
    return rng.randrange(10) if ndig == 1 else rng.randrange(10 ** (ndig - 1), 10 ** ndig)


def _seq(v):
    return list(str(v)[::-1])


def numbers(d, canonical):
    """all numbers written with exactly d digits (least significant first): canonical = no leading zero (one-digit 0
    allowed), else every digit string"""
    if not canonical:
        import itertools
        return [list(s) for s in itertools.product("0123456789", repeat=d)]
    lo = 0 if d == 1 else 10 ** (d - 1)
    return [_seq(v) for v in range(lo, 10 ** d)]


def contract(module, a, b):
    ia, ib = int("".join(reversed(a))), int("".join(reversed(b)))
    return _seq(ia + ib if module == "add" else ia * ib)


def exhaustive(module, canonical=True):
    """K(L) sequences: add = every ordered pair of operands of 1..3 digits; mul1 = every multiplicand of 1..4 digits x
    multiplier 0-9.  Returns [(prompt tokens, answer tokens)] (the answer = the contract's, <eos> added at encoding)"""
    L = KL[module]
    pool = [n for d in range(1, L + 1) for n in numbers(d, canonical)]
    out = []
    if module == "add":
        for a in pool:
            for b in pool:
                out.append((a + ["+"] + b + ["="], contract("add", a, b)))
    else:
        for a in pool:
            for d in "0123456789":
                out.append((a + ["*", d, "="], contract("mul1", a, [d])))
    return out


def long_random(module, n, seed_label):
    import random
    rng = random.Random(seed_label)
    lo, hi = LONG[module]
    out = []
    for _ in range(n):
        if module == "add":                         # the M draw (11.5): longer operand uniform, other 1..longer
            mx = rng.randint(lo, hi)
            o = rng.randint(1, mx)
            da, db = (mx, o) if rng.random() < 0.5 else (o, mx)
            a, b = _seq(_num(rng, da)), _seq(_num(rng, db))
            out.append((a + ["+"] + b + ["="], contract("add", a, b)))
        else:
            a, d = _seq(_num(rng, rng.randint(lo, hi))), str(rng.randrange(10))
            out.append((a + ["*", d, "="], contract("mul1", a, [d])))
    return out


def encode_batch(exs):
    import tasks as T
    import run as R
    return R.make_batch([([T.TOK[t] for t in p], [T.TOK[t] for t in a] + [T.EOS]) for p, a in exs])


def batch_keys(x, y, table):
    """int64 keys, targets, (row, t) of every scored step of a padded batch"""
    import torch
    import c1a
    mv = c1a.moving(table)
    P = c1a.read_paths(x, table)
    Bt = c1a.segment_bits(x, P)
    rows, ts = (y != -100).nonzero(as_tuple=True)
    assert bool((ts >= 1).all())
    key = torch.zeros(len(rows), dtype=torch.long)

    def push(k, v, bits):
        return (k << bits) | v
    for tt in (ts, ts - 1):
        key = push(key, x[rows, tt], 7)
        for j in mv:
            p = P[rows, j, tt]
            key = push(key, x[rows, p], 7)
            key = push(key, Bt[rows, j, tt], 1)
    return key, y[rows, ts], rows, ts


def decode_key(k, nh):
    import tasks as T
    f = []
    for _ in range(2):
        part = []
        for _ in range(nh):
            b = k & 1
            k >>= 1
            tok = k & 127
            k >>= 7
            part.append("(%s,%d)" % (T.VOCAB[tok], b))
        xt = k & 127
        k >>= 7
        f.append("x=%s reads=%s" % (T.VOCAB[xt], " ".join(reversed(part))))
    return "t: %s | t-1: %s" % (f[1], f[0])


def keys_of(exs, table, bs=2048):
    import torch
    K, Y, S = [], [], []
    for j in range(0, len(exs), bs):
        x, y = encode_batch(exs[j:j + bs])
        k, tgt, rows, _ = batch_keys(x, y, table)
        K.append(k)
        Y.append(tgt)
        S.append(rows + j)
    return torch.cat(K), torch.cat(Y), torch.cat(S)


def table_of(module, i):
    """i = 1, 2, 3: the C-1 compiled table; i = 0: the C-1a hand table (diagnostic only, not an admission table)"""
    import c0a
    import c1
    if i == 0:
        return c0a.hand_table(MODULE_TASK[module])
    return c1.compiled(MODULE_TASK[module], i)["policy"]


def cmd_closure(a):
    """(1) routing and (2) key closure for one table (model-independent); caches K(L) keys"""
    import json
    import time
    import torch
    import c0a
    import c1a
    import h0a
    import tasks as T
    _setup(a.module)
    t0 = time.time()
    table, hand = table_of(a.module, a.table), c0a.hand_table(MODULE_TASK[a.module])
    res = {"design": "stage3/DESIGN.md 11.7-1, 11.7-2", "module": a.module, "table": a.table, "compiled_table": table,
           "hand_table": hand, "moving_compiled": c1a.moving(table), "moving_hand": c1a.moving(hand)}
    # (1) routing: 2,000 random sequences, longer operand / multiplicand length 1-100
    import random
    rng = random.Random("L2b-0:route:%s" % a.module)
    exs = []
    for _ in range(2000):
        if a.module == "add":
            mx = rng.randint(1, 100)
            o = rng.randint(1, mx)
            da, db = (mx, o) if rng.random() < 0.5 else (o, mx)
            p, q = _seq(_num(rng, da)), _seq(_num(rng, db))
            exs.append((p + ["+"] + q + ["="], contract("add", p, q)))
        else:
            p, d = _seq(_num(rng, rng.randint(1, 100))), str(rng.randrange(10))
            exs.append((p + ["*", d, "="], contract("mul1", p, [d])))
    match = {h: {} for h in c1a.moving(hand)}          # hand head -> compiled head -> sequences with equal path
    cells = {"compiled": set(), "hand": set()}
    for j in range(0, len(exs), 256):
        chunk = exs[j:j + 256]
        x, y = encode_batch(chunk)
        n = torch.tensor([len(p) + len(q) + 1 for p, q in chunk])
        valid = torch.arange(x.shape[1])[None, :] < n[:, None]
        Pc, Ph = c1a.read_paths(x, table), c1a.read_paths(x, hand)
        import pf as PFM
        dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
        cls = PFM.token_classes(x, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]], T.TOK[T.NODES[-1]] + 1)
        for c in cls[valid].unique().tolist():
            cells["compiled"].add(c)
        for h in c1a.moving(hand):
            for g in range(len(table)):
                eq = ((Pc[:, g] == Ph[:, h]) | ~valid).all(1)
                match[h][g] = match[h].get(g, 0) + int(eq.sum())
    reached = sorted(cells["compiled"])
    res["routing"] = {
        "sequences": len(exs), "token_classes_reached": reached,
        "literal_equal_on_reached_cells": all(table[h][c] == hand[h][c] for h in range(len(table)) for c in reached),
        "hand_head_path_equal_fraction_by_compiled_head": {str(h): {str(g): v / len(exs) for g, v in m.items()}
                                                           for h, m in match.items()},
        "every_hand_moving_head_has_a_compiled_head_with_the_same_path_1.000":
            all(max(m.values()) == len(exs) for m in match.values()),
        "compiled_heads_without_hand_counterpart": [g for g in c1a.moving(table)
                                                    if not any(m.get(g) == len(exs) for m in match.values())]}
    print("routing", json.dumps(res["routing"]), flush=True)
    # (2) key closure
    CACHE.mkdir(parents=True, exist_ok=True)
    out_clo = {}
    for canon in (True, False):
        lab = "canonical" if canon else "all_digit_strings"
        exK = exhaustive(a.module, canon)
        K, Y, S = keys_of(exK, table)
        uk, inv = torch.unique(K, return_inverse=True)
        # conflicts: a key whose contract next token differs between sequences
        tmin = torch.full((len(uk),), 10 ** 6, dtype=torch.long).scatter_reduce(0, inv, Y, "amin")
        tmax = torch.full((len(uk),), -1, dtype=torch.long).scatter_reduce(0, inv, Y, "amax")
        conf = (tmin != tmax).nonzero()[:, 0]
        torch.save({"keys": uk, "sequences": len(exK)}, CACHE / ("KL_%s_table%d_%s.pt" % (a.module, a.table, lab)))
        out_clo[lab] = {"sequences": len(exK), "scored_steps": len(K), "distinct_keys": len(uk),
                        "keys_with_conflicting_contract_targets": len(conf),
                        "conflict_examples": [decode_key(int(uk[c]), len(c1a.moving(table))) for c in conf[:20]]}
        print(lab, out_clo[lab], round(time.time() - t0), flush=True)
    exL = long_random(a.module, 100000, "L2b-0:closure:%s" % a.module)
    KLg, _, SL = keys_of(exL, table, bs=256)
    for lab in ("canonical", "all_digit_strings"):
        uk = torch.load(CACHE / ("KL_%s_table%d_%s.pt" % (a.module, a.table, lab)))["keys"]
        miss = ~torch.isin(KLg, uk)
        um = KLg[miss].unique()
        out_clo[lab]["long"] = {"sequences": len(exL), "lengths": LONG[a.module], "scored_steps": len(KLg),
                                "steps_with_key_not_in_KL": int(miss.sum()), "distinct_keys_not_in_KL": len(um),
                                "sequences_with_a_new_key": len(SL[miss].unique()),
                                "new_keys": [decode_key(int(k), len(c1a.moving(table))) for k in um[:50]]}
        print(lab, "long", {k: v for k, v in out_clo[lab]["long"].items() if k != "new_keys"}, flush=True)
    res["closure"] = out_clo
    res["seconds"] = round(time.time() - t0, 1)
    res["env"] = h0a.env(["stage3/l2b_h.py"])
    (OUT / ("closure_%s_table%d.json" % (a.module, a.table))).write_text(json.dumps(res, indent=1))


def load_last(module, i, s):
    import torch
    import c1a
    d = run_dir(module, i, s)
    fin = __import__("json").loads((d / "final.json").read_text())
    ck = torch.load(d / "ckpt.pt", weights_only=False)
    assert ck["state"]["step"] == fin["steps"] == 20000, (ck["state"]["step"], fin["steps"])
    sd = ck["model"]
    cfg = fin["config"]
    m = c1a.HardReadLM(sd["tok.weight"].shape[0], mlp_only=True, **cfg)
    m.load_state_dict(sd)
    m.eval()
    return m, fin


def cmd_keycheck(a):
    """(3) key correctness: teacher-forced argmax at every scored step of every K(L) sequence == the contract"""
    import json
    import time
    import torch
    import c1a
    import h0a
    _setup(a.module)
    t0 = time.time()
    table = table_of(a.module, a.table)
    m, fin = load_last(a.module, a.table, a.seed)
    res = {"design": "stage3/DESIGN.md 11.7-3", "module": a.module, "table": a.table, "seed": a.seed,
           "checkpoint": "last (step %d)" % fin["steps"], "run_last_acc": fin["last"]["acc"]}
    for canon in (True, False):
        lab = "canonical" if canon else "all_digit_strings"
        exK = exhaustive(a.module, canon)
        wrong_k, wrong_s, steps = [], [], 0
        with torch.no_grad():
            for j in range(0, len(exK), 2048):
                x, y = encode_batch(exK[j:j + 2048])
                k, tgt, rows, ts = batch_keys(x, y, table)
                pred = m(x).argmax(-1)[rows, ts]
                bad = pred != tgt
                steps += len(k)
                wrong_k.append(k[bad])
                wrong_s.append(rows[bad] + j)
        wk, ws = torch.cat(wrong_k), torch.cat(wrong_s)
        uk, cnt = wk.unique(return_counts=True)
        res[lab] = {"sequences": len(exK), "scored_steps": steps, "wrong_steps": len(wk),
                    "sequences_with_a_wrong_step": len(ws.unique()), "distinct_wrong_keys": len(uk),
                    "step_accuracy": 1 - len(wk) / steps, "sequence_accuracy": 1 - len(ws.unique()) / len(exK),
                    "wrong_keys": [{"key": decode_key(int(k), len(c1a.moving(table))), "steps": int(c)}
                                   for k, c in sorted(zip(uk.tolist(), cnt.tolist()), key=lambda z: -z[1])][:200],
                    "wrong_sequence_indices": ws.unique().tolist()[:100000]}
        print(lab, {k: v for k, v in res[lab].items() if k not in ("wrong_keys", "wrong_sequence_indices")},
              round(time.time() - t0), flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    res["env"] = h0a.env(["stage3/l2b_h.py"])
    (OUT / ("keycheck_%s_table%d_s%d.json" % (a.module, a.table, a.seed))).write_text(json.dumps(res, indent=1))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("train")
    q.add_argument("--module", choices=tuple(MODULE_TASK), required=True)
    q.add_argument("--table", type=int, choices=(1, 2, 3), required=True)
    q.add_argument("--seed", type=int, required=True)
    q.add_argument("--resume", action="store_true")
    q = sp.add_parser("closure")
    q.add_argument("--module", choices=tuple(MODULE_TASK), required=True)
    q.add_argument("--table", type=int, choices=(0, 1, 2, 3), required=True, help="0 = hand table (diagnostic)")
    q = sp.add_parser("keycheck")
    q.add_argument("--module", choices=tuple(MODULE_TASK), required=True)
    q.add_argument("--table", type=int, choices=(1, 2, 3), required=True)
    q.add_argument("--seed", type=int, required=True)
    a = p.parse_args()
    {"train": cmd_train, "closure": cmd_closure, "keycheck": cmd_keycheck}[a.cmd](a)


if __name__ == "__main__":
    main()
