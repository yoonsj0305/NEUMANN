"""C-0b diagnostic (stage2/DESIGN.md 11.9, 11.10 first) -- not a verdict.  Four trainings (student seed 21, judgment
checkpoint kept with --keep-best) and diagnostics at the judgment checkpoints.

Arms (tasks addition, copy):
  O  the C-0a student exactly (stage2/c0a.py CoupledLM: per coupling head a key table and a query table, 256 rows
     each; offsets 0..100 per sequence and head; 11.8 prompt-only key IDs) -- retrained to keep the checkpoint;
  D  the same except that the key and the query ID of a coupling head share ONE embedding table (11.10-4).
Training: stage1/run.py executed as in C-0a (stage2/c0a.py PATCHES, the file is not edited) with --keep-best.

Diagnostics per checkpoint (the judgment checkpoint teacher_best.pt; evaluation sets of stage-1 sizes, 1,000 / 500):
  (1) ablation  [reference]: every key and query ID set to 0 -> in-distribution exact match
  (2) shuffle   [primary]: per sequence one random integer 1..50 added to every non-zero query ID (keys unchanged; the
                key-query pairing is broken) -> in-distribution exact match; drop = unchanged accuracy - shuffled
  (3) attention (D1-0 way): attention weights recomputed from the checkpoint (pre-LN blocks of stage1/models.Block, causal
                softmax(q k^T / sqrt(d_head)), checked against the model's own logits); at every scored step t and for
                every coupling channel h, the target position is the one whose key ID equals the query ID Q_h(t) (it is
                p_h(t), unique per channel); per layer and attention head: hit = argmax over positions <= t is the target,
                weight = the attention weight on the target; per bin and channel the best layer-head (highest hit) and its
                hit and mean weight.  Channels whose hand-table head moves are the relevant ones (addition h0, h1; copy
                h0); the others sit on position 0 and are recorded only.
  (4) failure position: out-of-distribution examples that are wrong (teacher-forced exact match): the first wrong answer
                token, as a share of the answer length (answer digits + <eos>): front < 1/3, middle, end >= 2/3; and the
                share whose first error is the <eos> target.
Reading rule (11.10, fixed before the data; reported as numbers, the design chat judges): (a) shuffle drop < 0.1;
(b) drop >= 0.1, OOD argmax right (best layer-head hit >= 0.9) but weight < 0.5; (c) drop >= 0.1, OOD hit < 0.9;
(d) drop >= 0.1, OOD hit >= 0.9 and weight >= 0.5 but the output wrong.  Here "OOD argmax right" requires every moving
channel's best layer-head hit >= 0.9 (and "sharp" every such weight >= 0.5) in that bin.

  python stage2/c0b.py train --task copy --arm O
  python stage2/c0b.py diag --task copy --arm O
  python stage2/c0b.py report
"""
from __future__ import annotations
import argparse
import json
import math
import os
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402
import torch.nn as nn            # noqa: E402
import torch.nn.functional as F  # noqa: E402
import c0a                       # noqa: E402

OUT = pathlib.Path(os.environ.get("C0B_OUT", HERE / "results" / "c0b"))
SEED = 21
TASKS = ("addition", "copy")
ARMS = {"O": "oracle", "D": "shared"}
SHUFFLE_MAX = 50
H = c0a.H


class SharedLM(c0a.CoupledLM):
    """D arm: one embedding table per coupling head, used for both its key and its query ID"""

    def __init__(self, vocab, d, heads, layers, table, **kw):
        super().__init__(vocab, d, heads, layers, table, **kw)
        self.qry = self.key                       # the same modules: one table per head

    def forward(self, tokens, offset=None, recur=None):
        return super().forward(tokens, offset, recur)


def register(table, arm):
    import models as M
    M.SCALES["coupled"] = {"1M": dict(M.SCALES["abacus"]["1M"], table=table, shared=(arm == "D"))}
    inner = M.build

    def build(kind, vocab, digit_ids, cfg):
        if kind == "coupled":
            cfg = dict(cfg)
            shared = cfg.pop("shared", False)
            return (SharedLM if shared else c0a.CoupledLM)(vocab, **cfg)
        return inner(kind, vocab, digit_ids, cfg)
    M.build = build


def run_dir(task, arm):
    return OUT / ("c0b_%s__coupled__1M__s%d__N100000__%s" % (task, SEED, ARMS[arm]))


def cmd_train(a):
    c0a.install(a.task)
    register(c0a.hand_table(a.task), a.arm)
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in c0a.PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", "coupled", "--scale", "1M", "--seed", str(SEED), "--N", "100000",
            "--max-steps", os.environ.get("C0B_MAX_STEPS", "20000"), "--phase", "c0b", "--out-root", str(OUT),
            "--threads", "1", "--tag", ARMS[a.arm], "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


# ---------------------------------------------------------------- diagnostics
def embed(model, tokens, K, Q):
    x = model.tok(tokens)
    for j in range(H):
        x = x + model.key[j](K[:, j]) + model.qry[j](Q[:, j])
    return x


def forward_with_attention(model, x):
    """the model's blocks with the attention weights returned ([layers] x [B, heads, T, T])"""
    atts = []
    for b in model.blocks:
        B, T, D = x.shape
        q, k, v = b.qkv(b.ln1(x)).view(B, T, 3, b.heads, D // b.heads).permute(2, 0, 3, 1, 4)
        s = q @ k.transpose(-1, -2) / math.sqrt(D // b.heads)
        s = s.masked_fill(torch.triu(torch.ones(T, T, dtype=torch.bool), 1), float("-inf"))
        w = s.softmax(-1)
        atts.append(w)
        a = w @ v
        x = x + b.proj(a.transpose(1, 2).reshape(B, T, D))
        x = x + b.mlp(b.ln2(x))
    return model.head(model.ln(x)), atts


def exact(model, exs, mode, rng, bs=128):
    import run as R
    ok = 0
    for i in range(0, len(exs), bs):
        x, y = R.make_batch(exs[i:i + bs])
        K, Q, _, _ = c0a.coupling_ids(x, model.table)
        if mode == "ablate":
            K, Q = torch.zeros_like(K), torch.zeros_like(Q)
        elif mode == "shuffle":
            off = torch.tensor([rng.randint(1, SHUFFLE_MAX) for _ in range(x.shape[0])])[:, None, None]
            Q = torch.where(Q > 0, Q + off, Q)
        assert int(K.max()) < c0a.ID_MAX and int(Q.max()) < c0a.ID_MAX
        h = embed(model, x, K, Q)
        for b in model.blocks:
            h = b(h)
        pred = model.head(model.ln(h)).argmax(-1)
        m = y != -100
        ok += int(((pred == y) | ~m).all(1).sum())
    return ok / len(exs)


def cmd_diag(a):
    c0a.install(a.task)
    register(c0a.hand_table(a.task), a.arm)
    import tasks as T
    import models as M
    import run as R
    import h0a
    torch.set_num_threads(1)
    d = run_dir(a.task, a.arm)
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    model = M.build("coupled", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
    model.load_state_dict(ck["model"])
    model.eval()
    table = model.table
    moving = [j for j in range(H) if any(mv != 0 for mv in table[j])]
    evs = T.eval_sets(a.task, 1000, 500)
    labs = list(evs)
    rng = random.Random("c0b:shuffle:%s:%s" % (a.task, a.arm))
    res = {"task": a.task, "arm": a.arm, "judgment_step": ck["step"], "moving_channels": moving}
    with torch.no_grad():
        base = exact(model, evs[labs[0]], "none", rng)
        abl = exact(model, evs[labs[0]], "ablate", rng)
        shf = exact(model, evs[labs[0]], "shuffle", rng)
        res["in_distribution"] = {"unchanged": base, "run_judgment_acc": fin["judgment"]["acc"][labs[0]],
                                  "ablation_all_ids_0": abl, "ablation_drop": base - abl,
                                  "shuffle_query_plus_1_50": shf, "shuffle_drop": base - shf}
        att, fail, maxdiff = {}, {}, 0.0
        for lab in labs:
            ex = evs[lab]
            nL, nA = len(model.blocks), model.blocks[0].heads
            hit = torch.zeros(H, nL, nA, dtype=torch.float64)
            wsum = torch.zeros(H, nL, nA, dtype=torch.float64)
            nsteps = 0
            pos_counts = {"front": 0, "middle": 0, "end": 0, "eos_target": 0}
            nwrong = ncorrect = 0
            for i in range(0, len(ex), 64):
                chunk = ex[i:i + 64]
                x, y = R.make_batch(chunk)
                K, Q, pth, scored = c0a.coupling_ids(x, table)
                logits, atts = forward_with_attention(model, embed(model, x, K, Q))
                maxdiff = max(maxdiff, float((logits - model(x)).abs().max()))
                bi, ti = scored.nonzero(as_tuple=True)                       # scored steps
                nsteps += len(bi)
                for j in range(H):
                    tgt = pth[bi, j, ti]                                      # the position whose key ID = Q_j(t)
                    assert bool((K[bi, j, :].gather(1, tgt[:, None])[:, 0] == Q[bi, j, ti]).all())
                    for li, w in enumerate(atts):
                        wt = w[bi, :, ti, :]                                  # [S, heads, T]
                        am = wt.argmax(-1)                                    # [S, heads]
                        hit[j, li] += (am == tgt[:, None]).double().sum(0)
                        wsum[j, li] += wt.gather(2, tgt[:, None, None].expand(-1, nA, 1))[:, :, 0].double().sum(0)
                if lab != labs[0]:
                    pred = logits.argmax(-1)
                    for b, (p, ans) in enumerate(chunk):
                        ts = list(range(len(p) - 1, len(p) + len(ans) - 1))
                        wrong = [k for k, t in enumerate(ts) if int(pred[b, t]) != int(y[b, t])]
                        if not wrong:
                            ncorrect += 1
                            continue
                        nwrong += 1
                        k, La = wrong[0], len(ans)
                        pos_counts["front" if k < La / 3 else ("middle" if k < 2 * La / 3 else "end")] += 1
                        pos_counts["eos_target"] += k == La - 1
            hr, wm = hit / nsteps, wsum / nsteps
            ch = {}
            for j in range(H):
                flat = hr[j].flatten()
                best = int(flat.argmax())
                ch["h%d" % j] = {"moving": j in moving, "best_layer": best // nA, "best_head": best % nA,
                                 "best_hit": float(flat[best]), "best_weight": float(wm[j].flatten()[best]),
                                 "hit_by_layer_head": [[round(float(v), 4) for v in row] for row in hr[j]],
                                 "weight_by_layer_head": [[round(float(v), 4) for v in row] for row in wm[j]]}
            att[lab] = {"scored_steps": nsteps, "channels": ch}
            if lab != labs[0]:
                fail[lab] = {"wrong": nwrong, "correct": ncorrect,
                             **{k: (v / nwrong if nwrong else None) for k, v in pos_counts.items()}}
            print(a.task, a.arm, lab, {k: (v["best_hit"], v["best_weight"]) for k, v in ch.items() if v["moving"]},
                  fail.get(lab), flush=True)
        res["attention"] = att
        res["failure_position_ood"] = fail
        res["max_abs_logit_diff_recomputed_vs_model"] = maxdiff
    # reading rule (11.10), per OOD bin
    drop = res["in_distribution"]["shuffle_drop"]
    branch = {}
    for lab in labs[1:]:
        ch = [att[lab]["channels"]["h%d" % j] for j in moving]
        right = all(c["best_hit"] >= 0.9 for c in ch)
        sharp = all(c["best_weight"] >= 0.5 for c in ch)
        branch[lab] = ("a" if drop < 0.1 else ("c" if not right else ("d" if sharp else "b")))
    res["reading_rule_by_ood_bin"] = branch
    res["ood_acc"] = {l: fin["judgment"]["acc"][l] for l in labs}
    res["env"] = h0a.env(["stage2/c0b.py", "stage2/c0a.py"])
    (OUT / ("diag_%s_%s.json" % (a.task, a.arm))).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("in_distribution", "reading_rule_by_ood_bin", "ood_acc",
                                          "max_abs_logit_diff_recomputed_vs_model")}, indent=1))


def cmd_report(a):
    rows = {}
    for t in TASKS:
        for arm in ARMS:
            f = json.loads((run_dir(t, arm) / "final.json").read_text())
            dg = json.loads((OUT / ("diag_%s_%s.json" % (t, arm))).read_text())
            rows["%s_%s" % (t, arm)] = {"final": {"judgment_step": f["judgment"]["step"], "steps": f["steps"],
                                                  "stopped": f["stopped"], "acc": f["judgment"]["acc"],
                                                  "train_flops": f["train_flops"],
                                                  "wall_s": f["wall_train_s"] + f["wall_eval_s"]},
                                        "diag": {k: dg[k] for k in ("in_distribution", "reading_rule_by_ood_bin",
                                                                    "failure_position_ood")},
                                        "attention_best": {l: {c: (v["best_hit"], v["best_weight"], v["best_layer"],
                                                                   v["best_head"]) for c, v in x["channels"].items()
                                                               if v["moving"]} for l, x in dg["attention"].items()}}
    # O-arm reproduction of C-0a
    rep = {}
    for t in TASKS:
        a0 = [json.loads(l) for l in open(c0a.OUT / ("c0a_%s__coupled__1M__s21__N100000__oracle" % t) / "log.jsonl")
              if l.strip() and "event" not in json.loads(l)]
        b0 = [json.loads(l) for l in open(run_dir(t, "O") / "log.jsonl") if l.strip() and "event" not in json.loads(l)]
        rep[t] = {"same_acc_and_loss_every_row": [(r["acc"], r["train_loss_mean"]) for r in a0] ==
                  [(r["acc"], r["train_loss_mean"]) for r in b0], "rows_c0a": len(a0), "rows_c0b": len(b0)}
    out = {"design": "stage2/DESIGN.md 11.9, 11.10", "runs": rows, "o_arm_reproduces_c0a": rep}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ("train", "diag"):
        q = sp.add_parser(name)
        q.add_argument("--task", choices=TASKS, required=True)
        q.add_argument("--arm", choices=tuple(ARMS), required=True)
        if name == "train":
            q.add_argument("--resume", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"train": cmd_train, "diag": cmd_diag, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
