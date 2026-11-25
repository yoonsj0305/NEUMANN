"""Stage 2 D1-0 (stage2/DESIGN.md section 4 with 4.1, which takes precedence): training-free attention hardening.

Teachers: the stage-1 baselines rope, abacus, looped_rr (seed 0) at their judgment checkpoints; tasks addition and
MQAR (no parity, 4.1-1).  The weights are never changed; inference only.

* Hardening a head: its attention weights softmax(scores) are replaced by the one-hot of argmax(scores) over the
  causal keys (ties: the leftmost key -- torch.argmax returns the first maximum).  The scores are computed exactly as
  the model does (q k^T / sqrt(head dim), RoPE applied for rope); every other head keeps its softmax.  With no head
  hardened the block runs its original code path (F.scaled_dot_product_attention), so (a) is the stage-1 harness's
  own forward.  looped_rr shares its blocks across iterations: a hardened head is hardened in every iteration; the
  number of iterations is the stage-1 evaluation rule (4 x ceil(bin upper / training upper)).
* Variants: (a) none; (b) every head; (c) selective -- heads in order (layer, then head number), each hardened in
  turn on top of the heads kept so far, kept if the selection accuracy of the resulting set is not more than 0.005
  below (a)'s (cumulative, 4.1-3), otherwise reverted.
* Selection-only validation data: "select:<task>" -- 1,000 new in-distribution examples drawn as the training
  distribution from their own generation seed (the C4 rule; select:addition is C4's set, select:mqar is new, 4.1-5).
  Selection accuracy: exact match (addition) / per-query accuracy (MQAR), the stage-1 primary metrics.
* Choice (pre-fixed): the higher selection accuracy of (b) and (c); a tie goes to (c) (it hardens no more heads than
  (b)).  The choice is written and committed before any out-of-distribution value is computed.
* After the choice: (a), (b), (c) on the existing evaluation sets (in-distribution + every out-of-distribution bin;
  MQAR per-query and whole-sequence), and the diagnostics of 4.1-6 on (a): for every head (and iteration for
  looped_rr) and every bin, the share of target steps where the head's argmax falls on the target position and the
  mean softmax weight on it.  Targets: addition -- at the step emitting answer digit k, the positions of a_k and b_k
  (separately, when k is inside that operand); MQAR -- at a query step, the value position after the prompt key equal
  to the query.

  python stage2/d1_0.py select   --teacher rope --task addition
  python stage2/d1_0.py evaluate --teacher rope --task addition
"""
from __future__ import annotations
import argparse
import json
import math
import os
import pathlib
import random
import subprocess
import sys
import time
import types

import torch
import torch.nn.functional as F

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "stage1"))
import tasks as T          # noqa: E402
import models as M         # noqa: E402
import run as R            # noqa: E402

OUT = HERE / "results" / "d1_0"
S1 = ROOT / "stage1" / "results"
TOL = 0.005
N_SEL = 1000
JUDGE = {"addition": ("ood_11-20", 0.278), "mqar": ("ood_49-64", 0.844)}     # 4.1-2: bin, baseline best
CKPT = {("rope", "addition"): S1 / "c3" / "c3_addition__rope__1M__s0__N100000" / "teacher_best.pt",
        ("rope", "mqar"): S1 / "c3" / "c3_mqar__rope__1M__s0__N100000" / "teacher_best.pt"}
STAGE1_SRC = {("rope", "addition"): ("phaseA4/phaseA4_addition__rope__1M__s0__N100000", None),
              ("abacus", "addition"): ("phaseA/addition__abacus__1M__s0__N100000", 12000),
              ("looped_rr", "addition"): ("phaseA2/phaseA2_addition__looped_rr__1M__s0__N100000", None),
              ("rope", "mqar"): ("phaseA4/phaseA4_mqar__rope__1M__s0__N100000", None),
              ("abacus", "mqar"): ("phaseA4/phaseA4_mqar__abacus__1M__s0__N100000", None),
              ("looped_rr", "mqar"): ("phaseA4/phaseA4_mqar__looped_rr__1M__s0__N100000", None)}


def ckpt_path(teacher, task):
    if (teacher, task) in CKPT:
        return CKPT[(teacher, task)]
    return OUT / ("d1_0_%s__%s__1M__s0__N100000" % (task, teacher)) / "teacher_best.pt"


def stage1_reference(teacher, task):
    """the stage-1 baseline table's value for this teacher and task (judgment checkpoint; Phase A abacus addition: the
    log row the judgment rule picked)"""
    d, step = STAGE1_SRC[(teacher, task)]
    d = S1 / d
    if step is None:
        j = json.loads((d / "final.json").read_text())["judgment"]
        return {"source": str(d.relative_to(ROOT)), "step": j["step"], "acc": j["acc"], "acc_seq": j.get("acc_seq")}
    for l in open(d / "log.jsonl"):
        r = json.loads(l)
        if r.get("step") == step:
            return {"source": str(d.relative_to(ROOT)) + " log step %d" % step, "step": step, "acc": r["acc"],
                    "acc_seq": r.get("acc_seq")}


def selection_set(task, n=N_SEL):
    rng = random.Random("select:%s" % task)
    lo, hi = T.SPEC[task]["id"]
    if task in T.MQAR:
        return [T.encode_mqar(*T.mqar(rng.randint(lo, hi), rng)) for _ in range(n)]
    return [T.encode(*T.draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(n)]


# ------------------------------------------------------------------ hardening
def _forward(self, x, cos=None, sin=None):
    B, Tn, D = x.shape
    H = self.heads
    hd = D // H
    q, k, v = self.qkv(self.ln1(x)).view(B, Tn, 3, H, hd).permute(2, 0, 3, 1, 4)
    if cos is not None:
        q = q * cos + M._rotate_half(q) * sin
        k = k * cos + M._rotate_half(k) * sin
    st = self._d1
    if not st["hard"] and st["diag"] is None:
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)          # the original code path
    else:
        s = (q @ k.transpose(-1, -2)) / math.sqrt(hd)
        s = s.masked_fill(~torch.ones(Tn, Tn, dtype=torch.bool).tril(), float("-inf"))
        w = s.softmax(-1)
        if st["diag"] is not None:
            st["diag"](self, w, st)
        if st["hard"]:
            hh = sorted(st["hard"])
            oh = F.one_hot(s[:, hh].argmax(-1), Tn).to(w.dtype)               # first maximum = leftmost key
            w = w.clone()
            w[:, hh] = oh
        a = w @ v
    x = x + self.proj(a.transpose(1, 2).reshape(B, Tn, D))
    return x + self.mlp(self.ln2(x))


def load(teacher, task):
    ck = torch.load(ckpt_path(teacher, task), weights_only=False)
    cfg = ck["cfg"]
    m = M.build(teacher, len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    m.load_state_dict(ck["model"])
    m.eval()
    for li, b in enumerate(m.blocks):
        b._d1 = {"hard": set(), "diag": None, "layer": li}
        b.forward = types.MethodType(_forward, b)
    return m, cfg, ck


def heads(m):
    return [(li, h) for li, b in enumerate(m.blocks) for h in range(b.heads)]


def set_hard(m, hs):
    for li, b in enumerate(m.blocks):
        b._d1["hard"] = {h for l2, h in hs if l2 == li}


def recur_for(teacher, cfg, task, label):
    return cfg["recur"] * R.ratio(task, label) if teacher in R.LOOPED else None


def accuracy(m, teacher, cfg, task, exs, label):
    r = recur_for(teacher, cfg, task, label)
    with torch.no_grad():
        if task in T.MQAR:
            sc = R.score(m, exs, teacher, cfg, recur=r)
            m.eval()
            return {"acc": sc["query"], "seq": sc["seq"]}
        a, _ = R.exact_match(m, exs, teacher, cfg, recur=r)
        m.eval()
        return {"acc": a}


def env():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "stage2/d1_0.py"], cwd=ROOT).strip())
    except Exception:
        commit, dirty = None, None
    import platform
    return {"code_commit": commit, "code_dirty": dirty, "torch": torch.__version__, "python": platform.python_version(),
            "cores": os.cpu_count(), "threads": torch.get_num_threads()}


def select(a):
    torch.set_num_threads(a.threads)
    t0 = time.time()
    name = "%s_%s" % (a.teacher, a.task)
    d = OUT / name
    if (d / "selection.json").exists():
        sys.exit("selection exists for %s (rule 5)" % name)
    d.mkdir(parents=True, exist_ok=True)
    m, cfg, ck = load(a.teacher, a.task)
    sel = selection_set(a.task)
    id_label = [l for l in T.eval_sets(a.task, 1, 1) if l.startswith("id")][0]
    log = open(d / "log.jsonl", "w")
    # (a) and the reproducibility check on the in-distribution evaluation set (stage-1 recorded value)
    set_hard(m, [])
    acc_a = accuracy(m, a.teacher, cfg, a.task, sel, id_label)["acc"]
    ev_id = T.eval_sets(a.task, 1000, 500)[id_label]
    id_a = accuracy(m, a.teacher, cfg, a.task, ev_id, id_label)
    ref = stage1_reference(a.teacher, a.task)
    log.write(json.dumps({"variant": "a", "selection_acc": acc_a, "id_eval": id_a, "stage1_id": ref["acc"][id_label]}) + "\n")
    # (b)
    set_hard(m, heads(m))
    acc_b = accuracy(m, a.teacher, cfg, a.task, sel, id_label)["acc"]
    log.write(json.dumps({"variant": "b", "selection_acc": acc_b}) + "\n")
    # (c)
    kept = []
    trace = []
    acc_c = acc_a
    for hd in heads(m):
        trial = kept + [hd]
        set_hard(m, trial)
        acc = accuracy(m, a.teacher, cfg, a.task, sel, id_label)["acc"]
        keep = acc >= acc_a - TOL
        trace.append({"head": list(hd), "selection_acc_with_head": acc, "kept": keep})
        log.write(json.dumps({"variant": "c", "try": list(hd), "selection_acc": acc, "kept": keep}) + "\n")
        log.flush()
        if keep:
            kept = trial
            acc_c = acc
    choice = "c" if acc_c >= acc_b else "b"
    out = {"teacher": a.teacher, "task": a.task, "checkpoint": str(ckpt_path(a.teacher, a.task).relative_to(ROOT)),
           "checkpoint_step": ck.get("step"), "heads_total": len(heads(m)),
           "selection_set": {"generation_seed": "select:%s" % a.task, "size": N_SEL, "lengths": list(T.SPEC[a.task]["id"]),
                             "metric": "per-query accuracy" if a.task in T.MQAR else "exact match"},
           "selection_acc": {"a": acc_a, "b": acc_b, "c": acc_c},
           "c_kept_heads": [list(h) for h in kept], "c_trace": trace,
           "rule": "(c): keep a head if the selection accuracy with it (on top of the kept heads) >= (a) - 0.005; choice: "
                   "higher selection accuracy of (b) and (c), tie -> (c)",
           "choice": choice,
           "a_id_eval": id_a, "stage1_reference": ref,
           "a_id_equals_stage1": id_a["acc"] == ref["acc"][id_label],
           "wall_s": round(time.time() - t0, 1)}
    (d / "selection.json").write_text(json.dumps(out, indent=1))
    (d / "env.json").write_text(json.dumps(env(), indent=1))
    (d / "config.json").write_text(json.dumps({"teacher": a.teacher, "task": a.task, "cfg": cfg,
                                               "tolerance": TOL, "judgment_bin": JUDGE[a.task][0],
                                               "baseline_best_judgment_bin": JUDGE[a.task][1],
                                               "recurrence": "4 x ceil(bin upper / training upper)"
                                               if a.teacher in R.LOOPED else None}, indent=1))
    print(json.dumps({k: out[k] for k in ("teacher", "task", "selection_acc", "c_kept_heads", "choice", "a_id_eval",
                                          "a_id_equals_stage1", "wall_s")}))


# ------------------------------------------------------------------ diagnostics (on (a))
def targets(task, chunk, x):
    """[(type, batch index, query position, key position)]"""
    out = []
    for b, e in enumerate(chunk):
        p = e[0]
        if task in T.MQAR:
            cont, mask = e[1], e[2]
            keys = {p[2 * i]: 2 * i + 1 for i in range(len(p) // 2)}
            for j, mk in enumerate(mask):
                if mk:
                    t = len(p) + j - 1                        # the query step (its token is the query key)
                    out.append(("value", b, t, keys[cont[j - 1]]))
        else:
            la = p.index(T.TOK["+"])
            lb = len(p) - la - 2
            for kk in range(len(e[1])):
                t = len(p) - 1 + kk
                if kk < la:
                    out.append(("a_k", b, t, kk))
                if kk < lb:
                    out.append(("b_k", b, t, la + 1 + kk))
    return out


def diag_hook(blk, w, st):
    """w [B, H, T, T] softmax weights; accumulate per (iteration, layer, head, target type)"""
    it = st["calls"]
    st["calls"] += 1
    for typ, (bi, ti, ki) in st["tg"].items():
        ww = w[bi, :, ti, :]                                   # [n, H, T]
        am = ww.argmax(-1)                                     # [n, H]
        hit = (am == ki[:, None]).sum(0)
        wt = ww.gather(2, ki[:, None, None].expand(-1, w.shape[1], 1)).squeeze(-1).sum(0)
        acc = st["acc"]
        for h in range(w.shape[1]):
            key = (it, st["layer"], h, typ)
            c = acc.setdefault(key, [0, 0.0, 0])
            c[0] += int(hit[h])
            c[1] += float(wt[h])
            c[2] += len(bi)


def diagnostics(m, teacher, cfg, task, exs, label, bs=64):
    r = recur_for(teacher, cfg, task, label)
    acc = {}
    order = sorted(range(len(exs)), key=lambda i: len(exs[i][0]) + len(exs[i][1]))
    with torch.no_grad():
        for i in range(0, len(order), bs):
            chunk = [exs[j] for j in order[i:i + bs]]
            x, _ = R.make_batch(chunk)
            tg = {}
            for typ, b, t, k in targets(task, chunk, x):
                tg.setdefault(typ, ([], [], []))
                tg[typ][0].append(b)
                tg[typ][1].append(t)
                tg[typ][2].append(k)
            tg = {k: tuple(torch.tensor(v) for v in vv) for k, vv in tg.items()}
            calls = {"n": 0}
            for b in m.blocks:
                b._d1["diag"] = diag_hook
                b._d1["tg"] = tg
                b._d1["acc"] = acc
                b._d1["calls"] = 0
            m(x, recur=r)
    for b in m.blocks:
        b._d1["diag"] = None
    rows = []
    for (it, li, h, typ), (hit, ws, n) in sorted(acc.items()):
        rows.append({"iteration": it, "layer": li, "head": h, "target": typ, "argmax_hit": hit / n,
                     "mean_weight": ws / n, "n": n})
    return rows


def evaluate(a):
    torch.set_num_threads(a.threads)
    t0 = time.time()
    d = OUT / ("%s_%s" % (a.teacher, a.task))
    sel = json.loads((d / "selection.json").read_text())
    if (d / "final.json").exists():
        sys.exit("already evaluated (rule 5)")
    m, cfg, _ = load(a.teacher, a.task)
    ev = T.eval_sets(a.task, 1000, 500)
    variants = {"a": [], "b": heads(m), "c": [tuple(h) for h in sel["c_kept_heads"]]}
    res = {}
    for vname, hs in variants.items():
        set_hard(m, hs)
        res[vname] = {label: accuracy(m, a.teacher, cfg, a.task, exs, label) for label, exs in ev.items()}
    set_hard(m, [])
    diag = {label: diagnostics(m, a.teacher, cfg, a.task, exs, label) for label, exs in ev.items()}
    id_label = [l for l in ev if l.startswith("id")][0]
    jb, best = JUDGE[a.task]
    ch = sel["choice"]
    up = res[ch][jb]["acc"] - res["a"][jb]["acc"]
    drop = res["a"][id_label]["acc"] - res[ch][id_label]["acc"]
    ref = sel["stage1_reference"]
    fin = {"teacher": a.teacher, "task": a.task, "choice": ch, "accuracy": res,
           "stage1_reference": ref,
           "a_equals_stage1": {l: res["a"][l]["acc"] == ref["acc"].get(l) for l in ev},
           "a_minus_stage1": {l: res["a"][l]["acc"] - ref["acc"][l] for l in ev if l in ref["acc"]},
           "judgment": {"bin": jb, "baseline_best": best, "chosen_minus_a": up,
                        "chosen_value": res[ch][jb]["acc"], "id_drop": drop,
                        "cond1_up_ge_0.2": up >= 0.2, "cond2_above_baseline_best": res[ch][jb]["acc"] > best,
                        "cond3_id_drop_le_0.01": drop <= 0.01},
           "diagnostics_a": diag, "wall_s": round(time.time() - t0, 1)}
    fin["judgment"]["all_three"] = all(fin["judgment"][k] for k in ("cond1_up_ge_0.2", "cond2_above_baseline_best",
                                                                     "cond3_id_drop_le_0.01"))
    (d / "final.json").write_text(json.dumps(fin, indent=1))
    print(json.dumps({k: fin[k] for k in ("teacher", "task", "choice", "accuracy", "a_equals_stage1", "judgment")}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("select", "evaluate"))
    p.add_argument("--teacher", required=True, choices=("rope", "abacus", "looped_rr"))
    p.add_argument("--task", required=True, choices=("addition", "mqar"))
    p.add_argument("--threads", type=int, default=1)
    a = p.parse_args()
    select(a) if a.cmd == "select" else evaluate(a)
