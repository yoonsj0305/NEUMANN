"""Stage 2 E-0 (stage2/DESIGN.md section 5 with 5.1, which takes precedence): baseline efficiency curve on addition.

How many training FLOPs does the strongest known method need to reach C3's addition out-of-distribution level
(11-20 and 21-30 both >= 0.95)?  Runs (seed 0, budget 1.79e15 FLOPs = 10 x C3's largest total, stopped at the first
evaluation where 11-20 and 21-30 are both >= 0.95 -- an oracle checkpoint, the most favourable to the baseline):

  abacus_ii      1M   general method: the stage-1 abacus model + input injection (the input embedding added to the
                      input of every decoder layer, McLeish et al. 2024); stage-1 Abacus offsets (0..100 per sequence)
  abacus_looped  1M   general method, the Abacus paper's best: Abacus embeddings with offset beta ~ U[1, 100] shared
                      by the batch (beta = 1 at test), a recurrent block of 8 decoder layers x 2 recurrences, input
                      injection before every layer, progressive loss (Bansal et al. 2022) with alpha = 1.0
  abacus_looped  10M  the same at 10M
  position_coupling 1M  task-knowledge reference (Cho et al. 2024): 1 decoder layer, 4 heads; learned absolute
                      position embedding indexed by COUPLED position IDs -- digits of the same significance share an
                      ID, '+' and '=' get units-ID + 1, special tokens 0; random start in training, start 1 at test;
                      max_pos = 42 (the longest test operand is 40 digits)

Common (5 / 5.1): training data drawn fresh for every batch (operand lengths independent uniform 1..10, the stage-1
training distribution); the stage-1 evaluation sets and scoring (exact match of answer digits and <eos>); stage-1
optimiser (AdamW, betas (0.9, 0.98), weight decay 0.1, clip 1.0, batch 64, lr 1e-3 at 1M / 5e-4 at 10M); the learning
rate follows the training FLOPs: linear warm-up over the first 5 % of the 10 x budget, cosine to 10 % at the 10 x
budget, then constant at 10 % (only used by the 30 x extension).  Training FLOPs: stage-1 analytic formula
(run.fwd_flops / iter_flops), training = 3 x forward; progressive loss: the no-grad iterations count once.
Evaluation every 1,000 steps on every bin; checkpoint (atomic) at every evaluation; --resume continues.

  python stage2/e0.py --run abacus_looped_1M [--budget 1.79e15] [--resume]
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
import torch.nn as nn
import torch.nn.functional as F

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "stage1"))
import tasks as T          # noqa: E402
import models as M         # noqa: E402
import run as R            # noqa: E402

OUT = HERE / "results" / "e0"
C3_FLOPS = 1.79e14
BUDGET_10X = 10 * C3_FLOPS
TARGET = 0.95
BATCH = 64
EVAL_EVERY = 1000
PROG_ALPHA = 1.0
PC_MAX_POS = 42

RUNS = {
    "abacus_ii_1M": dict(kind="abacus_ii", scale="1M", d=128, heads=4, layers=4),
    "abacus_looped_1M": dict(kind="abacus_looped", scale="1M", d=92, heads=4, layers=8, recur=2),
    "abacus_looped_10M": dict(kind="abacus_looped", scale="10M", d=320, heads=8, layers=8, recur=2),
    "position_coupling_1M": dict(kind="position_coupling", scale="1M", d=256, heads=4, layers=1),
}


class E0LM(nn.Module):
    def __init__(self, vocab, kind, d, heads, layers, recur=1, **_):
        super().__init__()
        self.kind, self.recur, self.V = kind, recur, vocab
        self.tok = nn.Embedding(vocab, d)
        if kind == "position_coupling":
            self.pe = nn.Embedding(PC_MAX_POS + 1, d)
            nn.init.normal_(self.pe.weight, std=0.02)       # as the stage-1 Abacus table
        else:
            self.aba = nn.Embedding(M.ABACUS_MAX + 1, d)
            nn.init.normal_(self.aba.weight, std=0.02)
        self.blocks = nn.ModuleList([M.Block(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.register_buffer("digit_ids", torch.tensor([T.TOK[c] for c in T.DIGITS]), persistent=False)

    def pc_ids(self, tokens, start):
        """coupled position IDs: significance j -> C - j with C = start + max(la, lb); '+' and '=' -> C + 1; <eos>,
        <pad> -> 0"""
        B, Tn = tokens.shape
        pos = torch.arange(Tn)[None, :].expand(B, Tn)
        pp = (tokens == T.TOK["+"]).float().argmax(1)[:, None]
        pe = (tokens == T.TOK["="]).float().argmax(1)[:, None]
        la, lb = pp, pe - pp - 1
        C = start[:, None] + torch.maximum(la, lb)
        sig = torch.where(pos < pp, pos, torch.where(pos < pe, pos - pp - 1, pos - pe - 1))
        ids = C - sig
        ids = torch.where((pos == pp) | (pos == pe), C + 1, ids)
        ids = torch.where(torch.isin(tokens, self.digit_ids) | (pos == pp) | (pos == pe), ids, torch.zeros_like(ids))
        return ids.clamp(min=0, max=PC_MAX_POS)

    def embed(self, tokens, offset=None, start=None):
        if self.kind == "position_coupling":
            if start is None:
                start = torch.ones(tokens.shape[0], dtype=torch.long)
            return self.tok(tokens) + self.pe(self.pc_ids(tokens, start))
        idx = M.abacus_index(tokens, self.digit_ids)
        if offset is not None:
            idx = torch.where(idx > 0, idx + offset[:, None], idx)
        return self.tok(tokens) + self.aba(idx.clamp(max=M.ABACUS_MAX))

    def iterate(self, x, e, n):
        for _ in range(n):
            for b in self.blocks:
                x = b(x + e)                                # input injection before every layer
        return x

    def forward(self, tokens, offset=None, recur=None, start=None):
        e = self.embed(tokens, offset, start)
        if self.kind == "position_coupling":
            x = e
            for b in self.blocks:
                x = b(x)
        else:
            x = self.iterate(torch.zeros_like(e), e, recur or self.recur)
        return self.head(self.ln(x))


def fwd_flops(cfg, B, Tn, iters=None):
    """stage-1 analytic forward FLOPs (run.fwd_flops): 24 d^2 per token per layer, 2 d V readout, 4 T d attention"""
    d, L = cfg["d"], cfg["layers"] * (iters if iters is not None else cfg.get("recur", 1))
    return B * Tn * (2 * 12 * d * d * L + 2 * d * len(T.VOCAB)) + 4 * B * Tn * Tn * d * L


def iter_only(cfg, B, Tn):
    d, L = cfg["d"], cfg["layers"]
    return B * Tn * 2 * 12 * d * d * L + 4 * B * Tn * Tn * d * L


def lr_at(flops, base):
    w = 0.05 * BUDGET_10X
    if flops < w:
        return base * max(flops, 1.0) / w
    f = min(1.0, flops / BUDGET_10X)
    return base * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * (f - 0.05) / 0.95)))


def env():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "stage2/e0.py"], cwd=ROOT).strip())
    except Exception:
        commit, dirty = None, None
    cpu = "?"
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    return {"code_commit": commit, "code_dirty": dirty, "torch": torch.__version__, "python": platform.python_version(),
            "cpu": cpu, "cores": os.cpu_count(), "threads": torch.get_num_threads()}


def evaluate(model, cfg, evals):
    """exact match on every bin; abacus_looped is primarily scored with its training recurrences (2, as the paper);
    the stage-1 looped rule (recurrences x ceil(bin upper / 10)) is recorded alongside as acc_scaled"""
    rc = {"d": cfg["d"], "layers": cfg["layers"], "block_layers": cfg["layers"], "recur": cfg.get("recur", 1)}
    out, scaled = {}, {}
    for label, ex in evals.items():
        out[label], _ = R.exact_match(model, ex, cfg["kind"], rc)
        if cfg["kind"] == "abacus_looped" and R.ratio("addition", label) > 1:
            scaled[label], _ = R.exact_match(model, ex, cfg["kind"], rc, recur=cfg["recur"] * R.ratio("addition", label))
    return out, scaled


def main(a):
    torch.set_num_threads(a.threads)
    cfg = dict(RUNS[a.run])
    d = OUT / ("e0_%s" % a.run)
    final, logf, ck = d / "final.json", d / "log.jsonl", d / "ckpt.pt"
    if a.extend:                                         # the 10 x final.json is kept (rule 5)
        if not final.exists():
            sys.exit("--extend needs a finished 10 x run")
        final = d / ("final_extend_%.3g.json" % a.budget)
    if final.exists():
        sys.exit("finished run exists (rule 5)")
    d.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    model = E0LM(len(T.VOCAB), **cfg)
    params = sum(p.numel() for p in model.parameters())
    base_lr = R.LR[cfg["scale"]]
    opt = torch.optim.AdamW(model.parameters(), lr=base_lr, betas=(0.9, 0.98), weight_decay=0.1)
    rng = random.Random("e0:train:%s:0" % a.run)
    prog_rng = random.Random("e0:prog:%s:0" % a.run)
    st = {"step": 0, "flops": 0, "wall_train": 0.0, "wall_eval": 0.0, "segments": [], "reached": None}
    if (a.resume or a.extend) and ck.exists():
        c = torch.load(ck, weights_only=False)
        model.load_state_dict(c["model"])
        opt.load_state_dict(c["opt"])
        rng.setstate(c["rng"])
        prog_rng.setstate(c["prog_rng"])
        torch.set_rng_state(c["torch_rng"])
        st = c["state"]
    elif logf.exists():
        sys.exit("unfinished run exists: --resume")
    budget = a.budget
    if st["step"] == 0:
        (d / "config.json").write_text(json.dumps({
            "run": a.run, **cfg, "params": params, "seed": 0, "batch": BATCH, "base_lr": base_lr,
            "optimizer": "AdamW betas (0.9, 0.98) wd 0.1 clip 1.0",
            "lr_schedule": "by training FLOPs: linear warm-up 5 % of 1.79e15, cosine to 10 % at 1.79e15, then constant",
            "budget": budget, "target": "first evaluation with ood_11-20 >= 0.95 and ood_21-30 >= 0.95",
            "data": "fresh every batch: T.draw(addition, 1..10, train_dist=True)", "eval": "T.eval_sets(addition, 1000, 500)",
            "abacus_offset": {"abacus_ii": "per sequence uniform 0..100 (stage 1)",
                              "abacus_looped": "per batch shift beta - 1, beta ~ U[1, 100]; test beta = 1"}.get(cfg["kind"]),
            "position_coupling": {"max_pos": PC_MAX_POS, "train_start": "per sequence uniform 1 .. max_pos - max(la,lb) - 1",
                                  "test_start": 1} if cfg["kind"] == "position_coupling" else None,
            "progressive_loss_alpha": PROG_ALPHA if cfg["kind"] == "abacus_looped" else None,
            "test_recurrence": {"primary": "training recurrences (2), as the paper",
                                "acc_scaled": "stage-1 looped rule: 2 x ceil(bin upper / 10) for the ood bins (recorded only)"}
            if cfg["kind"] == "abacus_looped" else None}, indent=1))
        (d / "env.json").write_text(json.dumps(env(), indent=1))
    if st.get("last_rec") and logf.exists():            # a cut between checkpoint and log line: restore the line
        logged = [json.loads(l).get("step", -1) for l in open(logf)]
        if max(logged) < st["last_rec"]["step"]:
            with open(logf, "a") as fh:
                fh.write(json.dumps({**st["last_rec"], "restored_from_checkpoint": True}) + "\n")
    seg = {"segment": len(st["segments"]), "start_step": st["step"], "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "budget": budget, "max_wall_s": a.max_wall, "threads": a.threads}
    ev = "start" if seg["segment"] == 0 else ("extend" if st["segments"][-1]["budget"] < budget else "resume")
    st["segments"].append(seg)
    with open(logf, "a") as fh:
        fh.write(json.dumps({"event": ev, **seg, "params": params}) + "\n")
    evals = T.eval_sets("addition", 1000, 500)
    window = st.pop("window", [])                      # losses since the last evaluation, kept across a cut
    t_seg = t0 = time.time()

    def save():
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "rng": rng.getstate(),
                    "prog_rng": prog_rng.getstate(), "torch_rng": torch.get_rng_state(), "state": st}, str(ck) + ".tmp")
        os.replace(str(ck) + ".tmp", ck)
    while st["flops"] < budget and st["reached"] is None:
        exs = [T.encode(*T.draw("addition", rng, 1, 10, train_dist=True)[:2]) for _ in range(BATCH)]
        xb, yb = R.make_batch(exs)
        B, Tn = xb.shape
        for g in opt.param_groups:
            g["lr"] = lr_at(st["flops"], base_lr)
        model.train()
        if cfg["kind"] == "abacus_looped":
            beta = prog_rng.randint(1, 100)                      # one offset for the batch (paper)
            off = torch.full((B,), beta - 1, dtype=torch.long)
            m_ = cfg["recur"]
            n = prog_rng.randint(0, m_ - 1)
            k = prog_rng.randint(1, m_ - n)
            e = model.embed(xb, off)
            with torch.no_grad():
                x0 = model.iterate(torch.zeros_like(e), e.detach(), n)
            logits = model.head(model.ln(model.iterate(x0.detach(), e, k)))
            loss = F.cross_entropy(logits.reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
            if PROG_ALPHA < 1.0:
                raise SystemExit("alpha < 1 not used")
            step_flops = n * iter_only(cfg, B, Tn) + 3 * (k * iter_only(cfg, B, Tn) + B * Tn * 2 * cfg["d"] * len(T.VOCAB))
        elif cfg["kind"] == "abacus_ii":
            off = torch.randint(0, R.OFFSET_MAX + 1, (B,))
            loss = F.cross_entropy(model(xb, offset=off).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
            step_flops = 3 * fwd_flops(cfg, B, Tn)
        else:
            mx = torch.tensor([max(e[0].index(T.TOK["+"]), len(e[0]) - e[0].index(T.TOK["+"]) - 2) for e in exs])
            start = (torch.rand(B) * (PC_MAX_POS - mx - 1).float()).long() + 1    # uniform 1 .. max_pos - mx - 1
            loss = F.cross_entropy(model(xb, start=start).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
            step_flops = 3 * fwd_flops(cfg, B, Tn)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        st["step"] += 1
        st["flops"] += step_flops
        window.append(loss.item())
        if st["step"] % EVAL_EVERY == 0 or st["flops"] >= budget:
            st["wall_train"] += time.time() - t_seg
            t_ev = time.time()
            model.eval()
            acc, acc_scaled = evaluate(model, cfg, evals)
            st["wall_eval"] += time.time() - t_ev
            rec = {"step": st["step"], "train_flops_cum": st["flops"], "train_loss_mean": round(sum(window) / len(window), 5),
                   "lr": opt.param_groups[0]["lr"], "acc": acc, "wall_train_s_cum": round(st["wall_train"], 1),
                   "wall_eval_s_cum": round(st["wall_eval"], 1), "segment": seg["segment"]}
            if acc_scaled:
                rec["acc_scaled"] = acc_scaled
                rec["recur_scaled"] = {k: cfg["recur"] * R.ratio("addition", k) for k in acc_scaled}
            window = []
            if acc["ood_11-20"] >= TARGET and acc["ood_21-30"] >= TARGET:
                st["reached"] = {"step": st["step"], "train_flops_cum": st["flops"], "acc": acc}
            st["last_rec"] = rec
            save()
            with open(logf, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(a.run, rec["step"], "%.3e" % st["flops"], rec["train_loss_mean"], {k: round(v, 3) for k, v in acc.items()},
                  flush=True)
            t_seg = time.time()
        if a.max_wall and time.time() - t0 > a.max_wall and st["reached"] is None and st["flops"] < budget:
            st["wall_train"] += time.time() - t_seg       # planned cut: checkpoint between evaluations, then exit
            st["window"] = window
            save()
            st.pop("window")
            with open(logf, "a") as fh:
                fh.write(json.dumps({"event": "cut", "at_step": st["step"], "train_flops_cum": st["flops"],
                                     "time": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
            print(a.run, "cut at step", st["step"], flush=True)
            sys.exit(3)
    rows = [json.loads(l) for l in open(logf) if "step" in json.loads(l)]
    fin = {"run": a.run, "params": params, "steps": st["step"], "train_flops": st["flops"], "budget": budget,
           "reached": st["reached"], "stopped": "reached target" if st["reached"] else "budget",
           "multiple_of_C3": (st["reached"]["train_flops_cum"] / C3_FLOPS) if st["reached"] else None,
           "best_ood_11_20": max(r["acc"]["ood_11-20"] for r in rows),
           "best_ood_21_30": max(r["acc"]["ood_21-30"] for r in rows),
           "last": rows[-1], "wall_train_s": round(st["wall_train"], 1), "wall_eval_s": round(st["wall_eval"], 1),
           "segments": st["segments"]}
    final.write_text(json.dumps(fin, indent=1))
    print("FINAL", json.dumps({k: fin[k] for k in ("run", "steps", "train_flops", "reached", "stopped")}), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, choices=sorted(RUNS))
    p.add_argument("--budget", type=float, default=BUDGET_10X)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--extend", action="store_true", help="continue a finished run to a larger --budget (30 x)")
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--max-wall", type=float, default=0, help="checkpoint and exit (code 3) after this many seconds")
    main(p.parse_args())
