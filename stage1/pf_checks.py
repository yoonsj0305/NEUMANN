"""C1-1 task 1 checks before training (CLAUDE.md):
  b  expressiveness: the PF machine driven by hand-written rules solves addition (lengths 1-40), parity (1-64) and
     MQAR (n 4-64) exactly (1.000) on the harness's own evaluation sets and scorer; plus real greedy decoding on a
     sample (sequence-level) to confirm teacher-forced == greedy for the machine
  c  gradients: with the straight-through weighted read, move logits and register logits get non-zero gradients
  d  FLOPs: analytic (controllers + 6-candidate reads + position index) vs measured (torch.utils.flop_counter)

  python stage1/pf_checks.py > stage1/results/c1_checks/pf_checks.json
"""
from __future__ import annotations
import json
import os
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(__file__))
import tasks as T
import models as M
import run as R
import pf as PFM
from pf_rules import RuleModel

CFG = M.SCALES["pf"]["1M"]
DIG = [T.TOK[d] for d in T.DIGITS]


@torch.no_grad()
def greedy_seq(model, exs):
    """real autoregressive greedy decoding; sequence-level correctness of every target (MQAR: queries are input)"""
    ok = 0
    for e in exs:
        p, a = e[0], e[1]
        mask = e[2] if len(e) == 3 else [True] * len(a)
        seq = list(p)
        good = True
        for j, (tok, m) in enumerate(zip(a, mask)):
            nx = int(model(torch.tensor([seq]))[0, -1].argmax())
            if m:
                if nx != tok:
                    good = False
                    break
                seq.append(nx)
            else:
                seq.append(tok)                       # an input token (MQAR query / the closing <eos>)
        ok += good
    return ok / len(exs)


def expressiveness():
    out = {}
    for task in ("addition", "parity", "mqar"):
        torch.manual_seed(0)
        pf = M.build("pf", len(T.VOCAB), DIG, CFG)
        rm = RuleModel(pf, task)
        ev = T.eval_sets(task, 1000, 500)
        res = {}
        for label, ex in ev.items():
            if task == "mqar":
                sc = R.score(rm, ex, "pf", CFG)
                res[label] = {"query_teacher_forced": sc["query"], "seq_teacher_forced": sc["seq"],
                              "seq_greedy_sample20": greedy_seq(rm, ex[:20]), "n": len(ex)}
            else:
                acc, _ = R.exact_match(rm, ex, "pf", CFG)
                res[label] = {"seq_teacher_forced": acc, "seq_greedy_sample20": greedy_seq(rm, ex[:20]),
                              "n": len(ex)}
        lens = {l: (min(len(e[0]) for e in ex), max(len(e[0]) + len(e[1]) for e in ex)) for l, ex in ev.items()}
        out[task] = {"bins": res, "token_lengths_min_prompt_max_total": lens,
                     "all_exact_1.000": all(all(v == 1.0 for k, v in r.items() if k != "n") for r in res.values())}
    return out


def gradients():
    out = {}
    for task in ("addition", "parity", "mqar"):
        torch.manual_seed(0)
        pf = M.build("pf", len(T.VOCAB), DIG, CFG)
        pf.train()
        pf.tau = 1.0
        pf.debug = []
        xb, yb = R.make_batch(T.train_set(task, 16, 0))
        loss = F.cross_entropy(pf(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
        loss.backward()
        # a logit with no downstream use has grad None (the last step's register update feeds nothing): counted 0
        mg = [float(m.grad.abs().sum()) if m.grad is not None else 0.0 for m, _ in pf.debug]
        rg = [float(r.grad.abs().sum()) if r.grad is not None else 0.0 for _, r in pf.debug]
        gparams = {n: float(p.grad.abs().sum()) for n, p in pf.named_parameters() if p.grad is not None}
        out[task] = {"steps": len(mg), "move_logit_grad_nonzero_steps": sum(g > 0 for g in mg),
                     "register_logit_grad_zero_at_steps": [i for i, g in enumerate(rg) if g == 0],
                     "move_logit_grad_abs_sum": sum(mg), "register_logit_grad_nonzero_steps": sum(g > 0 for g in rg),
                     "register_logit_grad_abs_sum": sum(rg),
                     "move_controller_g_param_grad_abs_sum": sum(v for n, v in gparams.items() if n.startswith("g.")),
                     "update_controller_f_param_grad_abs_sum": sum(v for n, v in gparams.items() if n.startswith("f.")),
                     "params_without_grad": [n for n, p in pf.named_parameters() if p.grad is None or
                                             float(p.grad.abs().sum()) == 0]}
        pf.debug = None
    return out


def flops():
    from torch.utils.flop_counter import FlopCounterMode
    out = {}
    for task in ("addition", "mqar"):
        torch.manual_seed(0)
        pf = M.build("pf", len(T.VOCAB), DIG, CFG)
        pf.train()
        xb, yb = R.make_batch(T.train_set(task, 64, 0))
        fc = FlopCounterMode(display=False)
        with fc:
            F.cross_entropy(pf(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100).backward()
        an = PFM.pf_flops(CFG, xb.shape[0], xb.shape[1], len(T.VOCAB), train=True)
        out[task] = {"batch_shape": list(xb.shape), "measured_flop_counter": fc.get_total_flops(),
                     "analytic_matmul": an["matmul"], "matmul_ratio_analytic_over_measured":
                         round(an["matmul"] / fc.get_total_flops(), 4),
                     "analytic_reads_6_candidates": an["reads"], "analytic_index": an["index"],
                     "analytic_total": an["total"],
                     "note": "the flop counter counts dense matmuls only; reads (elementwise weighted sum) and the "
                             "position index (comparisons) are analytic"}
    pf = M.build("pf", len(T.VOCAB), DIG, CFG)
    out["params"] = M.n_params(pf)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="c,d,b")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results", "c1_checks"))
    a = ap.parse_args()
    torch.set_num_threads(1)
    fn = {"b": ("b_expressiveness", expressiveness), "c": ("c_gradients", gradients), "d": ("d_flops", flops)}
    for part in a.parts.split(","):
        name, f = fn[part]
        res = {"config": CFG, name: f()}
        with open(os.path.join(a.out, name + ".json"), "w") as fh:
            fh.write(json.dumps(res, indent=1) + "\n")
        print(name, "written", flush=True)
