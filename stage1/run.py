"""Stage 1 / week 1: one baseline run = (task, baseline, scale, seed, training-set size, steps).

Trains on lengths 1..L, evaluates exact-match accuracy (greedy decoding to <eos>) at n = L, 2L, 3L, 4L, and records
training / inference FLOPs, wall-clock and hardware.  A result is written once to stage1/results/<name>.json and
never overwritten (rule 5): an existing name is refused; a rerun needs a new --tag.

FLOPs are counted analytically per batch from the executed shapes (dense matmuls 2 * m * n * k; attention QK^T and
AV over the full T x T, as computed by SDPA; training = 3 x forward); checked once against
torch.utils.flop_counter (--check-flops).  Inference FLOPs are those executed by the decoder used here (no KV
cache: every generated token re-runs the full prefix).

  python stage1/run.py --task addition --kind abacus --scale 1M --seed 0 --data 1000 --steps 2000
"""
from __future__ import annotations
import argparse
import json
import math
import os
import pathlib
import platform
import random
import subprocess
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(__file__))
import tasks as T
import models as M

RESULTS = pathlib.Path(__file__).parent / "results"
LR = {"1M": 1e-3, "10M": 5e-4, "50M": 2.5e-4}
OFFSET_MAX = 100          # Abacus training offsets 0..100 (positions up to ~100 + training length are trained)


def hardware():
    cpu = platform.processor()
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    return {"cpu": cpu, "cores": os.cpu_count(), "torch_threads": torch.get_num_threads(), "torch": torch.__version__,
            "cuda": torch.cuda.is_available(), "python": platform.python_version()}


def fwd_flops(cfg, kind, B, Tlen, V):
    d = cfg["d"]
    L = cfg["layers"] if kind == "abacus" else cfg["block_layers"] * cfg["recur_used"]
    return B * Tlen * (2 * 12 * d * d * L + 2 * d * V) + 4 * B * Tlen * Tlen * d * L


def batch(exs, rng, device="cpu"):
    T_ = max(len(p) + len(a) for p, a in exs)
    x = torch.full((len(exs), T_), T.PAD, dtype=torch.long)
    y = torch.full((len(exs), T_), -100, dtype=torch.long)
    for i, (p, a) in enumerate(exs):
        s = p + a
        x[i, :len(s)] = torch.tensor(s)
        # predict the answer tokens (positions len(p)-1 .. len(s)-2 predict s[len(p)] .. s[-1])
        y[i, len(p) - 1:len(s) - 1] = torch.tensor(a)
    return x.to(device), y.to(device)


@torch.no_grad()
def evaluate(model, exs, kind, cfg, recur=None, bs=100):
    """exact match of the greedy continuation (up to and including <eos>); returns (accuracy, executed FLOPs)"""
    model.eval()
    groups = {}
    for p, a in exs:
        groups.setdefault(len(p), []).append((p, a))
    ok = tot = 0
    flops = 0
    c = dict(cfg, recur_used=recur or cfg.get("recur", 1))
    for plen, g in groups.items():
        for i in range(0, len(g), bs):
            chunk = g[i:i + bs]
            x = torch.tensor([p for p, _ in chunk])
            maxa = max(len(a) for _, a in chunk)
            outs = [[] for _ in chunk]
            done = torch.zeros(len(chunk), dtype=torch.bool)
            for _ in range(maxa):
                logits = model(x, recur=recur)
                flops += fwd_flops(c, kind, x.shape[0], x.shape[1], len(T.VOCAB))
                nxt = logits[:, -1].argmax(-1)
                for j in range(len(chunk)):
                    if not done[j]:
                        outs[j].append(int(nxt[j]))
                done |= nxt == T.EOS
                if bool(done.all()):
                    break
                x = torch.cat([x, nxt[:, None]], 1)
            for j, (_, a) in enumerate(chunk):
                tot += 1
                ok += outs[j] == a
    model.train()
    return ok / max(tot, 1), flops


def main(a):
    RESULTS.mkdir(parents=True, exist_ok=True)
    name = "%s__%s__%s__s%d__d%d__st%d%s" % (a.task, a.kind, a.scale, a.seed, a.data, a.steps,
                                             ("__" + a.tag) if a.tag else "")
    out = RESULTS / (name + ".json")
    if out.exists():
        sys.exit("refusing to overwrite %s (rule 5): use --tag" % out)
    torch.manual_seed(a.seed)
    random.seed(a.seed)
    torch.set_num_threads(a.threads)
    L = T.TRAIN_LEN[a.task]
    cfg = dict(M.SCALES[a.kind][a.scale])
    digit_ids = [T.TOK[d] for d in T.DIGITS]
    model = M.LM(len(T.VOCAB), digit_ids=digit_ids, kind=a.kind, **cfg)
    params = M.n_params(model)
    data = T.dataset(a.task, a.data, L, a.seed)
    rng = random.Random(a.seed)
    lr = LR[a.scale]
    opt = torch.optim.AdamW(model.parameters(), lr=lr, betas=(0.9, 0.98), weight_decay=0.1)
    warm = max(1, a.steps // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / a.steps)))))
    tcfg = dict(cfg, recur_used=cfg.get("recur", 1))
    train_flops, losses = 0, []
    if a.check_flops:
        from torch.utils.flop_counter import FlopCounterMode
        xb, yb = batch(rng.sample(data, min(a.batch, len(data))), rng)
        fc = FlopCounterMode(display=False)
        with fc:
            lo = F.cross_entropy(model(xb, offset=torch.zeros(xb.shape[0], dtype=torch.long)).reshape(-1, len(T.VOCAB)),
                                 yb.reshape(-1), ignore_index=-100)
            lo.backward()
        opt.zero_grad()
        measured = fc.get_total_flops()
        analytic = 3 * fwd_flops(tcfg, a.kind, xb.shape[0], xb.shape[1], len(T.VOCAB))
        print("flop check: measured %.3e analytic %.3e ratio %.3f" % (measured, analytic, analytic / measured))
    t0 = time.time()
    model.train()
    for step in range(a.steps):
        exs = [data[rng.randrange(len(data))] for _ in range(a.batch)]
        xb, yb = batch(exs, rng)
        off = torch.randint(0, OFFSET_MAX + 1, (xb.shape[0],))
        logits = model(xb, offset=off)
        loss = F.cross_entropy(logits.reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        train_flops += 3 * fwd_flops(tcfg, a.kind, xb.shape[0], xb.shape[1], len(T.VOCAB))
        if step % 100 == 0 or step == a.steps - 1:
            losses.append([step, round(loss.item(), 4)])
    wall_train = time.time() - t0
    t1 = time.time()
    evals = {}
    for k in (1, 2, 3, 4):
        n = k * L
        ex = T.evalset(a.task, n, a.eval_size)
        acc, fl = evaluate(model, ex, a.kind, cfg)
        evals[str(n)] = {"x_train_len": k, "accuracy": acc, "infer_flops": fl}
        if a.kind == "looped" and k > 1:            # recurrence scaled with the length ratio (pre-declared rule)
            r = cfg["recur"] * k
            acc2, fl2 = evaluate(model, ex, a.kind, cfg, recur=r)
            evals[str(n)].update({"accuracy_recur_scaled": acc2, "recur_scaled": r, "infer_flops_recur_scaled": fl2})
    wall_eval = time.time() - t1
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=os.path.dirname(__file__)).decode().strip()
    except Exception:
        commit = None
    res = {"name": name, "task": a.task, "kind": a.kind, "scale": a.scale, "params": params, "config": cfg,
           "seed": a.seed, "data_size": len(data), "data_requested": a.data, "steps": a.steps, "batch": a.batch,
           "lr": lr, "abacus_offset_max": OFFSET_MAX, "train_len": L, "eval_size": a.eval_size, "eval": evals,
           "train_flops": train_flops, "wall_train_s": round(wall_train, 2), "wall_eval_s": round(wall_eval, 2),
           "final_loss": losses[-1][1], "loss_curve": losses, "hardware": hardware(), "commit": commit,
           "flops_note": "analytic from executed shapes; training = 3 x forward; inference without KV cache"}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("name", "params", "final_loss", "wall_train_s", "wall_eval_s")}),
          {n: round(v["accuracy"], 3) for n, v in evals.items()})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=T.TASKS, required=True)
    p.add_argument("--kind", choices=("abacus", "looped"), required=True)
    p.add_argument("--scale", choices=("1M", "10M", "50M"), required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--data", type=int, default=1000)
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--eval-size", type=int, default=200)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--tag", default="")
    p.add_argument("--check-flops", action="store_true")
    main(p.parse_args())
