"""C1-2 task 1 checks before training (CLAUDE.md C1-2):
  a  move-logit gradient, C1-1 (straight-through) vs C1-2 (exact expected immediate loss), same initial weights and
     same batch: mean |gradient| of the move logits at output steps and at prompt steps, share of non-zero
  b  expressiveness unchanged: the PF2 machine driven by the hand-written rules on the harness evaluation sets (1.000)
  c  FLOPs: analytic (controllers + 6-candidate reads + index + 18 counterfactual f forwards) vs measured
  python stage1/pf2_checks.py --parts a,c,b   -> stage1/results/c1_2_checks/*.json
"""
from __future__ import annotations
import argparse
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
from pf_checks import greedy_seq

CFG = M.SCALES["pf2"]["1M"]
DIG = [T.TOK[d] for d in T.DIGITS]


def grad_compare():
    out = {}
    for task in ("addition", "parity", "mqar"):
        ex = T.train_set(task, 64, 1)
        xb, yb = R.make_batch(ex)
        res = {}
        for kind in ("pf", "pf2"):
            torch.manual_seed(0)
            m = M.build(kind, len(T.VOCAB), DIG, CFG)
            if kind == "pf2":
                torch.manual_seed(0)
                ref = M.build("pf", len(T.VOCAB), DIG, CFG)
                m.load_state_dict(ref.state_dict())          # identical initial weights
                m.targets = yb
            m.train()
            m.tau = 1.0
            m.debug = []
            torch.manual_seed(1)
            loss = F.cross_entropy(m(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100)
            if kind == "pf2":
                loss = loss + m.aux
            loss.backward()
            outv, prov = [], []
            for t, (ml, _) in enumerate(m.debug):
                g = ml.grad.abs().mean(-1).mean(-1) if ml.grad is not None else torch.zeros(len(ex))   # [B]
                for b, e in enumerate(ex):
                    p, a = e[0], e[1]
                    if t < len(p) - 1:
                        prov.append(float(g[b]))
                    elif t < len(p) + len(a) - 1:
                        outv.append(float(g[b]))
            gsum = sum(float(p_.grad.abs().sum()) for n, p_ in m.named_parameters() if n.startswith("g.") and p_.grad is not None)
            res[kind] = {"move_logit_grad_mean_abs_output_steps": sum(outv) / len(outv),
                         "move_logit_grad_mean_abs_prompt_steps": sum(prov) / len(prov),
                         "output_steps_nonzero_share": sum(v > 0 for v in outv) / len(outv),
                         "move_controller_g_param_grad_abs_sum": gsum}
        res["ratio_output_steps_c12_over_c11"] = (res["pf2"]["move_logit_grad_mean_abs_output_steps"] /
                                                  max(res["pf"]["move_logit_grad_mean_abs_output_steps"], 1e-30))
        out[task] = res
    return out


def exactness():
    """the move-logit gradient of the C1-2 signal is the exact derivative of sum_m p_j(m) L_j(m) / n_targets:
    autograd on the move logits vs the closed form p (L - sum_m p L) / n_targets, at every step (zero where no
    target), on addition / parity / MQAR batches"""
    out = {}
    for task in ("addition", "parity", "mqar"):
        torch.manual_seed(0)
        m = M.build("pf2", len(T.VOCAB), DIG, CFG)
        m.train()
        xb, yb = R.make_batch(T.train_set(task, 8, 2))
        m.targets = yb
        m.debug, m.debug_L = [], []
        m(xb)
        m.aux.backward()
        n_t = int((yb != -100).sum())
        Ls = dict(m.debug_L)
        worst, checked, zero_ok = 0.0, 0, True
        for t, (ml, _) in enumerate(m.debug):
            if t not in Ls:
                zero_ok &= ml.grad is None or float(ml.grad.abs().sum()) == 0.0
                continue
            p = F.softmax(ml.detach(), -1)
            L = Ls[t]
            expect = p * (L - (p * L).sum(-1, keepdim=True)) / n_t
            worst = max(worst, float((ml.grad - expect).abs().max()))
            checked += 1
        out[task] = {"target_steps_checked": checked, "max_abs_diff_autograd_vs_closed_form": worst,
                     "non_target_steps_zero_gradient": zero_ok}
        m.debug = None
    return out


def expressiveness():
    out = {}
    for task in ("addition", "parity", "mqar"):
        torch.manual_seed(0)
        m = M.build("pf2", len(T.VOCAB), DIG, CFG)
        rm = RuleModel(m, task)
        ev = T.eval_sets(task, 1000, 500)
        res = {}
        for label, ex in ev.items():
            if task == "mqar":
                sc = R.score(rm, ex, "pf2", CFG)
                res[label] = {"query_teacher_forced": sc["query"], "seq_teacher_forced": sc["seq"],
                              "seq_greedy_sample20": greedy_seq(rm, ex[:20]), "n": len(ex)}
            else:
                acc, _ = R.exact_match(rm, ex, "pf2", CFG)
                res[label] = {"seq_teacher_forced": acc, "seq_greedy_sample20": greedy_seq(rm, ex[:20]), "n": len(ex)}
        out[task] = {"bins": res, "all_exact_1.000": all(all(v == 1.0 for k, v in r.items() if k != "n")
                                                          for r in res.values())}
    return out


def flops():
    from torch.utils.flop_counter import FlopCounterMode
    out = {}
    for task in ("addition", "mqar"):
        torch.manual_seed(0)
        m = M.build("pf2", len(T.VOCAB), DIG, CFG)
        m.train()
        xb, yb = R.make_batch(T.train_set(task, 64, 0))
        m.targets = yb
        fc = FlopCounterMode(display=False)
        with fc:
            loss = F.cross_entropy(m(xb).reshape(-1, len(T.VOCAB)), yb.reshape(-1), ignore_index=-100) + m.aux
            loss.backward()
        an = PFM.pf2_train_flops(CFG, xb.shape[0], xb.shape[1], len(T.VOCAB), m.cf_rowsteps)
        extra = PFM.pf2_extra_flops(CFG, len(T.VOCAB), m.cf_rowsteps)
        out[task] = {"batch_shape": list(xb.shape), "counterfactual_row_steps": m.cf_rowsteps,
                     "measured_flop_counter": fc.get_total_flops(),
                     "analytic_matmul": an["matmul"],
                     "matmul_ratio_analytic_over_measured": round(an["matmul"] / fc.get_total_flops(), 4),
                     "analytic_total_with_reads_index_losses": an["total"],
                     "counterfactual_share_of_total": round(extra / an["total"], 4)}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="a,c,b")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results", "c1_2_checks"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    torch.set_num_threads(1)
    fn = {"a": ("a_move_gradient_c11_vs_c12", grad_compare), "b": ("b_expressiveness", expressiveness),
          "x": ("a2_exact_expected_loss_gradient", exactness),
          "c": ("c_flops", flops)}
    for part in a.parts.split(","):
        name, f = fn[part]
        res = {"config": CFG, name: f()}
        with open(os.path.join(a.out, name + ".json"), "w") as fh:
            fh.write(json.dumps(res, indent=1) + "\n")
        print(name, "written", flush=True)
