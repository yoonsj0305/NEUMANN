"""Stage 1 / Phase A: one run = (task, baseline, scale, seed, N).

Protocol (CLAUDE.md, Phase A):
* a fixed training set of N i.i.d. examples (N = 100,000), batches of 64 drawn from it with replacement;
* at most 20,000 steps; early stop when the in-distribution validation accuracy is >= 99 % at two consecutive
  evaluations;
* every 1,000 steps: exact-match accuracy on the in-distribution bin and on every out-of-distribution bin, and the
  cumulative training FLOPs, appended to log.jsonl.
Looped transformer: the evaluation recurrence = 4 x (bin upper length / training upper length) is the PRIMARY
result, declared before any run; fixed 4 iterations is recorded as a secondary column.  Neither is chosen after
seeing results.

Exact match is computed with one teacher-forced forward pass: for a causal model, greedy decoding reproduces the
answer (and <eos>) exactly iff the argmax at every answer position, given the correct prefix, is the answer token
(induction over positions), so this equals greedy-decoding exact match at a fraction of the cost.

FLOPs are analytic from the executed (padded) shapes; training = 3 x forward.  Transformer: dense matmuls
2 * 12 d^2 per token per layer + head 2 d V + attention 4 T^2 d per sequence per layer; GRU: 2 * 3 (d_in d + d^2)
per token per layer + head.  Checked against torch.utils.flop_counter with --check-flops.

Results: stage1/results/phaseA/<name>/{log.jsonl, final.json, ckpt.pt}.  A finished run is never overwritten
(rule 5); an unfinished one is continued with --resume from its last checkpoint (every 1,000 steps), and the resume
is written into its log.
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

ROOT = pathlib.Path(__file__).parent / "results" / "phaseA"
LR = {"1M": 1e-3, "10M": 5e-4, "50M": 2.5e-4}
OFFSET_MAX = 100          # Abacus training offsets 0..100


def hardware():
    cpu = platform.processor()
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    return {"cpu": cpu, "cores": os.cpu_count(), "torch_threads": torch.get_num_threads(), "torch": torch.__version__,
            "cuda": torch.cuda.is_available(), "python": platform.python_version()}


def fwd_flops(kind, cfg, B, Tlen, V, recur=None):
    d = cfg["d"]
    if kind == "gru":
        return B * Tlen * (cfg["layers"] * 2 * 3 * (d * d + d * d) + 2 * d * V)
    L = cfg["layers"] if kind == "abacus" else cfg["block_layers"] * (recur or cfg["recur"])
    return B * Tlen * (2 * 12 * d * d * L + 2 * d * V) + 4 * B * Tlen * Tlen * d * L


def make_batch(exs):
    T_ = max(len(p) + len(a) for p, a in exs)
    x = torch.full((len(exs), T_), T.PAD, dtype=torch.long)
    y = torch.full((len(exs), T_), -100, dtype=torch.long)
    for i, (p, a) in enumerate(exs):
        s = p + a
        x[i, :len(s)] = torch.tensor(s)
        y[i, len(p) - 1:len(s) - 1] = torch.tensor(a)      # the logit at position j predicts token j + 1
    return x, y


@torch.no_grad()
def exact_match(model, exs, kind, cfg, recur=None, bs=128):
    model.eval()
    ok, flops = 0, 0
    order = sorted(range(len(exs)), key=lambda i: len(exs[i][0]) + len(exs[i][1]))   # similar lengths per batch
    for i in range(0, len(order), bs):
        chunk = [exs[j] for j in order[i:i + bs]]
        x, y = make_batch(chunk)
        logits = model(x, recur=recur)
        flops += fwd_flops(kind, cfg, x.shape[0], x.shape[1], len(T.VOCAB), recur)
        pred = logits.argmax(-1)
        m = y != -100
        ok += int(((pred == y) | ~m).all(1).sum())
    model.train()
    return ok / len(exs), flops


def ratio(task, label):
    lo, hi = map(int, label.split("_")[1].split("-"))
    return math.ceil(hi / T.SPEC[task]["id"][1])


def main(a):
    name = "%s__%s__%s__s%d__N%d%s" % (a.task, a.kind, a.scale, a.seed, a.N, ("__" + a.tag) if a.tag else "")
    out = (pathlib.Path(a.out_root) if a.out_root else ROOT) / name
    final, logf, ck = out / "final.json", out / "log.jsonl", out / "ckpt.pt"
    if final.exists():
        sys.exit("refusing to overwrite finished run %s (rule 5)" % out)
    if logf.exists() and not a.resume:
        sys.exit("unfinished run exists at %s: continue it with --resume" % out)
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(a.threads)
    cfg = dict(M.SCALES[a.kind][a.scale])
    digit_ids = [T.TOK[d] for d in T.DIGITS]
    torch.manual_seed(a.seed)
    model = M.build(a.kind, len(T.VOCAB), digit_ids, cfg)
    params = M.n_params(model)
    data = T.train_set(a.task, a.N, a.seed)
    evals = T.eval_sets(a.task, a.id_size, a.ood_size)
    lr = LR[a.scale]
    opt = torch.optim.AdamW(model.parameters(), lr=lr, betas=(0.9, 0.98), weight_decay=0.1)
    warm = max(1, a.max_steps // 20)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / a.max_steps)))))
    rng = random.Random("batches:%d" % a.seed)
    st = {"step": 0, "train_flops": 0, "wall_train_s": 0.0, "wall_eval_s": 0.0, "eval_flops": 0, "hits": 0,
          "segments": []}
    if a.resume and ck.exists():
        c = torch.load(ck, weights_only=False)
        model.load_state_dict(c["model"])
        opt.load_state_dict(c["opt"])
        sched.load_state_dict(c["sched"])
        rng.setstate(c["rng"])
        torch.set_rng_state(c["torch_rng"])
        st = c["state"]
        logged = [json.loads(l).get("step", -1) for l in open(logf) if l.strip()]
        if st.get("last_rec") and max(logged) < st["step"]:
            with open(logf, "a") as fh:
                fh.write(json.dumps(dict(st["last_rec"], note="row restored from checkpoint on resume")) + "\n")
    elif a.resume and logf.exists():
        if any("event" not in json.loads(l) for l in open(logf) if l.strip()):
            sys.exit("evaluations logged but no checkpoint in %s: not restarting (rule 5)" % out)
        with open(logf, "a") as fh:                   # killed before the first checkpoint: nothing was recorded
            fh.write(json.dumps({"event": "restart from step 0: stopped before the first checkpoint"}) + "\n")
    seg = {"segment": len(st["segments"]), "start_step": st["step"], "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    st["segments"].append(seg)
    with open(logf, "a") as fh:
        fh.write(json.dumps({"event": "start" if seg["segment"] == 0 else "resume", **seg, "params": params,
                             "config": cfg}) + "\n")
    if a.check_flops:
        from torch.utils.flop_counter import FlopCounterMode
        xb, yb = make_batch(data[:a.batch])
        fc = FlopCounterMode(display=False)
        with fc:
            F.cross_entropy(model(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100).backward()
        opt.zero_grad(set_to_none=True)
        print("flop check: measured %.3e analytic %.3e" % (fc.get_total_flops(),
                                                           3 * fwd_flops(a.kind, cfg, xb.shape[0], xb.shape[1], len(T.VOCAB))))
    stop = None
    window = []
    t_seg = time.time()
    while st["step"] < a.max_steps and stop is None:
        exs = [data[rng.randrange(len(data))] for _ in range(a.batch)]
        xb, yb = make_batch(exs)
        off = torch.randint(0, OFFSET_MAX + 1, (xb.shape[0],)) if a.kind != "gru" else None
        logits = model(xb, offset=off)
        loss = F.cross_entropy(logits.reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        st["step"] += 1
        st["train_flops"] += 3 * fwd_flops(a.kind, cfg, xb.shape[0], xb.shape[1], len(T.VOCAB))
        window.append(loss.item())
        if st["step"] % a.eval_every == 0 or st["step"] == a.max_steps:
            st["wall_train_s"] += time.time() - t_seg
            t_ev = time.time()
            rec = {"step": st["step"], "train_flops_cum": st["train_flops"],
                   "train_loss_mean": round(sum(window) / len(window), 5), "lr": sched.get_last_lr()[0],
                   "acc": {}, "recur": {}}
            window = []
            for label, ex in evals.items():
                r = None if a.kind != "looped" else cfg["recur"] * ratio(a.task, label)
                acc, fl = exact_match(model, ex, a.kind, cfg, recur=r)
                rec["acc"][label] = acc
                st["eval_flops"] += fl
                if a.kind == "looped":
                    rec["recur"][label] = r
                    if label.startswith("ood"):        # secondary: fixed 4 iterations
                        acc4, fl4 = exact_match(model, ex, a.kind, cfg, recur=cfg["recur"])
                        rec.setdefault("acc_fixed4", {})[label] = acc4
                        st["eval_flops"] += fl4
            st["wall_eval_s"] += time.time() - t_ev
            rec.update({"wall_train_s_cum": round(st["wall_train_s"], 2), "wall_eval_s_cum": round(st["wall_eval_s"], 2),
                        "eval_flops_cum": st["eval_flops"], "segment": seg["segment"]})
            id_label = [l for l in evals if l.startswith("id")][0]
            st["hits"] = st["hits"] + 1 if rec["acc"][id_label] >= 0.99 else 0
            if st["hits"] >= 2:
                stop = "early stop: in-distribution >= 99% at two consecutive evaluations"
            st["last_rec"] = rec
            # checkpoint first, atomically (a kill during the write leaves the previous checkpoint intact), then the
            # log row; a resume writes the row again only if the kill fell between the two
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                        "rng": rng.getstate(), "torch_rng": torch.get_rng_state(), "state": st}, str(ck) + ".tmp")
            os.replace(str(ck) + ".tmp", ck)
            with open(logf, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(name, rec["step"], rec["train_loss_mean"], {k: round(v, 3) for k, v in rec["acc"].items()}, flush=True)
            t_seg = time.time()
    if stop is None:
        stop = "max steps"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=os.path.dirname(__file__)).decode().strip()
    except Exception:
        commit = None
    rows = [json.loads(l) for l in open(logf) if l.strip() and "event" not in json.loads(l)]
    last = rows[-1]
    res = {"name": name, "task": a.task, "kind": a.kind, "scale": a.scale, "params": params, "config": cfg,
           "seed": a.seed, "N": a.N, "batch": a.batch, "lr": lr, "max_steps": a.max_steps, "steps": st["step"],
           "stopped": stop, "spec": T.SPEC[a.task], "id_size": a.id_size, "ood_size": a.ood_size,
           "final_acc": last["acc"], "final_acc_fixed4": last.get("acc_fixed4"), "recur": last.get("recur"),
           "train_flops": st["train_flops"], "eval_flops": st["eval_flops"],
           "wall_train_s": round(st["wall_train_s"], 2), "wall_eval_s": round(st["wall_eval_s"], 2),
           "segments": st["segments"], "hardware": hardware(), "commit": commit,
           "primary_eval_rule": "looped: recurrence 4 x ceil(bin upper / training upper) (declared before runs); "
                                "fixed 4 recorded as acc_fixed4"}
    final.write_text(json.dumps(res, indent=1))
    if ck.exists():
        ck.unlink()                                   # the record is the log + final; checkpoints are not kept
    print("FINAL", name, stop, {k: round(v, 3) for k, v in last["acc"].items()}, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=T.TASKS, required=True)
    p.add_argument("--kind", choices=("abacus", "looped", "gru"), required=True)
    p.add_argument("--scale", default="1M")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--N", type=int, default=100000)
    p.add_argument("--max-steps", type=int, default=20000)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--eval-every", type=int, default=1000)
    p.add_argument("--id-size", type=int, default=1000)
    p.add_argument("--ood-size", type=int, default=500)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--tag", default="")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--check-flops", action="store_true")
    p.add_argument("--out-root", default="", help="write elsewhere (harness tests); default stage1/results/phaseA")
    main(p.parse_args())
