"""G-0a (stage2/DESIGN.md 7.6): expressivity check and task freeze -- no teacher, student or baseline training, no
change to the pipeline code (stage1/*.py are imported, not edited).

For every candidate task (stage2/g_tasks.py) a hand-written correct move table in the stage-1 PF-search form
(3 heads x 7 token kinds -> one of the 6 PF moves; stage1/pf.py CLASS_NAMES / MOVES) and a hand-written update
controller (finite registers, the R = 4 x K = 16 of the 1M PF) drive the stage-1 PF machine itself (stage1/pf.py
PF.forward with a controller: moves, reads, causality and registers are the PF code).  Scoring is the stage-1
harness's teacher-forced sequence exact match (stage1/run.py exact_match: every answer token and <eos>).
A task is representable iff the table + controller is exact (1.000) on the in-distribution bin and every
out-of-distribution bin.  The table is the "correct table" of the 14-section pre-check (stage1/c3_compile.py).

Token kinds (7.4): the operator tokens '-', '*', '^' are given the "+" kind (classes are computed with stage1's
token_classes after mapping them to '+') and, like '+', are PF separators (the next_sep move): the "+" kind is the
same token kind in the machine as in the table.

Also checked (not required by 7.6, same 1.000 criterion): the selection-only set "select:<task>" and the first
2,000 training examples of the G-0 seeds 9, 10, 11 (the dependency-extraction inputs of the pipeline).

subtraction: no exact table + controller is known (see the report); the aligned-stream controller below (the
padded-answer algorithm) is run on it to measure how often the answer's length is decided by digits not yet read,
and on the reference task subtraction_pad (answer padded to len(a) digits), which is not a candidate.

  python stage2/g0a.py          # writes stage2/results/g0a/{config,tables,final,env}.json
  python stage2/g0a.py --tasks prefix_sum --out stage2/results/g0/a_prefix_sum      # G-0 step 1 (DESIGN 7.10)
"""
from __future__ import annotations
import json
import os
import pathlib
import platform
import subprocess
import sys
import time

import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "stage1"))
import g_tasks as G            # noqa: E402
import pf as PFM               # noqa: E402  (stage-1 PF machine, unchanged)
import models as M             # noqa: E402
import run as R                # noqa: E402  (stage-1 exact-match scoring, unchanged)
from pf_search_v2_check import HAND as ADDITION_HAND     # noqa: E402  (stage-1 addition correct table)

OUT = HERE / "results" / "g0a"
STAY, RIGHT, LEFT, NSEP, START, CONTENT = range(6)
CI = {n: i for i, n in enumerate(PFM.CLASS_NAMES)}
TOK, EOS = G.TOK, G.EOS
DIG = {TOK[str(d)]: d for d in range(10)}
SEP_IDS = [TOK[s] for s in ("+", "=", "|")] + [TOK[s] for s in G.OPS]
N_ID, N_OOD, N_SEL, N_TRAIN, SEEDS = 1000, 500, 1000, 2000, (9, 10, 11)


def table(spec):
    t = [[STAY] * len(CI) for _ in range(3)]
    for h, d in spec.items():
        for c, m in d.items():
            t[h][CI[c]] = m
    return t


TWO_POINTER = table({0: {"answer_phase": RIGHT}, 1: {"+": NSEP, "=": RIGHT, "answer_phase": RIGHT}})
assert TWO_POINTER == ADDITION_HAND                      # the stage-1 addition correct table
TABLES = {
    # head 0 sits on s_0 and walks right in the answer phase
    "copy": table({0: {"answer_phase": RIGHT}}),
    # head 0 follows the input to s_{n-1}, then walks left; head 1 walks right from s_0 and reaches '=' after n steps
    "reverse": table({0: {"digit": RIGHT, "answer_phase": LEFT}, 1: {"answer_phase": RIGHT}}),
    # head 0 on x_k, head 1 jumps to '^' then right onto y_0 at '=' (the addition table)
    "xor": TWO_POINTER,
    "subtraction": TWO_POINTER,
    "subtraction_pad": TWO_POINTER,
    # head 0 on a_k; head 1 jumps to '*', right onto d at '=', then stays on d
    "mul1": table({0: {"answer_phase": RIGHT}, 1: {"+": NSEP, "=": RIGHT}}),
    # G-0 (7.10): head 0 sits on x_1 and walks right in the answer phase (the copy table)
    "prefix_sum": table({0: {"answer_phase": RIGHT}}),
}
CONTROLLERS = {
    "copy": "stateless: output head 0's digit; <eos> when head 0 reads a non-digit ('=')",
    "reverse": "stateless: <eos> when head 1 reads a non-digit ('='), otherwise output head 0's digit",
    "xor": "stateless: output head0 xor head1; <eos> when head 0 reads a non-digit ('^')",
    "subtraction": "aligned-stream subtraction (r1 borrow, r2 a exhausted, r3 b exhausted): digit (a_k - b_k - "
                   "borrow) mod 10, b_k = 0 once b is exhausted; <eos> once a is exhausted (always len(a) digits)",
    "subtraction_pad": "same as subtraction",
    "mul1": "r1 carry 0-8, r2 a exhausted, r3 done: d = head 1's digit; d = 0 -> '0' then <eos>; otherwise digit "
            "(a_k d + carry) mod 10; once a is exhausted the carry if non-zero, then <eos>",
    "prefix_sum": "stateless: at '=' output head 0's digit (s_1 = x_1); afterwards (current token s_{k-1} + head 0's "
                  "digit x_k) mod 10; <eos> when head 0 reads a non-digit ('=')",
}
REG_USE = "r0 = answer phase (set at '='), r1-r3 as listed per task; registers are only updated in the answer phase"


def is_d(tok):
    return tok in DIG


def rule(task, rd, r, xi=None):
    """one answer step: reads rd (3 token ids), registers r (mutable list) -> output token id.  Batches are padded,
    so the machine also steps past a row's end (outputs there are not scored); digit look-ups of a read that is not
    a digit there use 0 (as stage1/pf_search_v2_check.TableController)."""
    a, b = rd[0], rd[1]
    if task == "copy":
        return a if is_d(a) else EOS
    if task == "prefix_sum":                              # xi = the current token: '=' or the previous answer s_{k-1}
        if not is_d(a):
            return EOS
        return a if xi == TOK["="] else TOK[str((DIG.get(xi, 0) + DIG[a]) % 10)]
    if task == "reverse":
        return a if is_d(b) else EOS
    if task == "xor":
        return TOK[str(DIG[a] ^ DIG.get(b, 0))] if is_d(a) else EOS
    if task in ("subtraction", "subtraction_pad"):
        if not is_d(a):
            r[2] = 1
        if not is_d(b):
            r[3] = 1
        if r[2]:
            return EOS
        s = DIG[a] - (0 if r[3] else DIG[b]) - r[1]
        r[1] = 1 if s < 0 else 0
        return TOK[str(s % 10)]
    if task == "mul1":
        d = DIG.get(b, 0)
        if r[3]:
            return EOS
        if d == 0:
            r[3] = 1
            return TOK["0"]
        if not is_d(a):
            r[2] = 1
        if r[2]:
            o = TOK[str(r[1])] if r[1] else EOS
            r[1], r[3] = 0, 1
            return o
        p = DIG[a] * d + r[1]
        r[1] = p // 10
        return TOK[str(p % 10)]
    raise KeyError(task)


def classes(tokens):
    """stage-1 token kinds with the 7.4 rule: the infix operators '-', '*', '^' are the "+" kind"""
    t = tokens.clone()
    for s in G.OPS:
        t[t == TOK[s]] = TOK["+"]
    return PFM.token_classes(t, torch.tensor([TOK[d] for d in G.DIGITS]), TOK["+"], TOK["="], TOK["|"],
                             TOK[G.T1.NODES[0]], TOK[G.T1.NODES[-1]] + 1)


class Controller:
    def __init__(self, task, tab, cls, V, K):
        self.task, self.tab, self.cls, self.V, self.K, self.t = task, torch.tensor(tab), cls, V, K, 0

    def move(self, x, regs, prev):
        mv = self.tab[:, self.cls[:, self.t]].T                                   # [B, H]
        self.t += 1
        return F.one_hot(mv, len(PFM.MOVES)).float()

    def update(self, x, regs, reads):
        reg = regs.argmax(-1).tolist()
        rd = reads.argmax(-1).tolist()
        newr, outs = [], []
        for b in range(x.shape[0]):
            xi, r = int(x[b]), list(reg[b])
            o = EOS
            if xi == TOK["="] or r[0] == 1:
                r[0] = 1
                o = rule(self.task, rd[b], r, xi)
            newr.append(r)
            outs.append(o)
        return F.one_hot(torch.tensor(newr), self.K).float(), F.one_hot(torch.tensor(outs), self.V).float() * 100.0


class HandModel(nn.Module):
    def __init__(self, pf, task):
        super().__init__()
        self.pf, self.task = pf, task

    def forward(self, tokens, offset=None, recur=None):
        ctl = Controller(self.task, TABLES[self.task], classes(tokens), self.pf.V, self.pf.K)
        return PFM.PF.forward(self.pf, tokens, controller=ctl)


def head_path(tokens, tab):
    """head positions after the move at every step for one example (the PF move code, pf.candidates)"""
    x = torch.tensor([tokens])
    cls = classes(x)
    issep = torch.isin(x, torch.tensor(SEP_IDS))
    h = torch.zeros(1, 3, dtype=torch.long)
    tt = torch.tensor(tab)
    out = []
    for t in range(x.shape[1]):
        cand = PFM.candidates(x, t, h, x[:, t], issep)
        mv = tt[:, cls[0, t]]
        h = cand[0, torch.arange(3), mv][None]
        out.append(h[0].tolist())
    return out


def trace(pf, task, ex):
    """the answer steps of one example: step, current token, head positions and reads, output, target"""
    p, a = ex
    s = p + a
    with torch.no_grad():
        pred = HandModel(pf, task)(torch.tensor([s])).argmax(-1)[0].tolist()
    path = head_path(s, TABLES[task])
    V = G.VOCAB
    rows = []
    for t in range(len(p) - 1, len(s) - 1):
        rows.append({"step": t, "x_t": V[s[t]], "heads": path[t], "reads": [V[s[q]] for q in path[t]],
                     "output": V[pred[t]], "target": V[s[t + 1]]})
    return {"tokens": " ".join(V[i] for i in p) + " | " + " ".join(V[i] for i in a), "answer_steps": rows}


def env():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "stage2/g0a.py",
                                              "stage2/g_tasks.py"], cwd=ROOT).strip())
    except Exception:
        commit, dirty = None, None
    cpu = "?"
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    return {"code_commit": commit, "code_dirty": dirty, "torch": torch.__version__, "python": platform.python_version(),
            "cpu": cpu, "cores": os.cpu_count(), "threads": torch.get_num_threads()}


def readable(tab):
    return {"head%d" % h: {PFM.CLASS_NAMES[c]: PFM.MOVES[tab[h][c]] for c in range(len(CI))} for h in range(3)}


def short_len(task, exs):
    """examples whose answer has fewer digits than the first operand (subtraction: the answer length is decided by
    the upper digits)"""
    n = 0
    for p, a in exs:
        la = next(i for i, tok in enumerate(p) if not is_d(tok))
        n += (len(a) - 1) < la
    return n


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=",".join(list(G.TASKS) + list(G.REFERENCE)),
                    help="comma list (default: the G-0a candidates and the reference)")
    ap.add_argument("--out", default=str(OUT), help="results directory (default stage2/results/g0a)")
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    torch.set_num_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    cfg = dict(M.SCALES["pf"]["1M"])
    torch.manual_seed(0)
    pf = PFM.PF(len(G.VOCAB), sep_ids=SEP_IDS, **cfg)        # its learned g and f are never used here
    pf.eval()
    tasks = args.tasks.split(",")
    config = {"design": "stage2/DESIGN.md 7.4-7.6 (G-0a); 7.10 (prefix_sum, G-0 step 1)", "tasks": tasks,
              "g0a_candidates": list(G.TASKS), "g0_suite": list(G.SUITE), "reference_only": list(G.REFERENCE),
              "spec": {t: G.SPEC[t] for t in tasks}, "vocab_added": G.OPS, "vocab_size": len(G.VOCAB),
              "token_kinds": "digits and bits = digit; infix operators + - * ^ = '+' kind; '=', '|', answer phase "
                             "(strictly after the first '=' or '|'), others as stage 1 (stage1/pf.py token_classes)",
              "pf_separators": ["+", "=", "|"] + G.OPS, "pf_cfg": cfg, "class_names": list(PFM.CLASS_NAMES),
              "moves": list(PFM.MOVES), "sets": {"eval": "g_tasks.eval_sets(task, %d, %d)" % (N_ID, N_OOD),
                                                 "select": "g_tasks.selection_set(task, %d)" % N_SEL,
                                                 "train": "g_tasks.train_set(task, %d, seed) for seeds %s"
                                                          % (N_TRAIN, list(SEEDS))},
              "criterion": "representable iff the hand table + hand controller scores 1.000 (stage-1 teacher-forced "
                           "sequence exact match) on the in-distribution bin and every out-of-distribution bin"}
    (out / "config.json").write_text(json.dumps(config, indent=1))
    res = {}
    for task in tasks:
        t0 = time.time()
        sets = dict(G.eval_sets(task, N_ID, N_OOD))
        sets["select"] = G.selection_set(task, N_SEL)
        for s in SEEDS:
            sets["train_s%d_first%d" % (s, N_TRAIN)] = G.train_set(task, N_TRAIN, s)
        model = HandModel(pf, task)
        acc = {}
        with torch.no_grad():
            for lab, exs in sets.items():
                acc[lab] = R.exact_match(model, exs, "pf_search", cfg)[0]
        bins = [l for l in sets if l.startswith(("id_", "ood_"))]
        r = {"accuracy": acc, "n": {l: len(e) for l, e in sets.items()},
             "max_tokens": {l: max(len(p) + len(a) for p, a in e) for l, e in sets.items()},
             "exact_on_all_bins": all(acc[l] == 1.0 for l in bins),
             "exact_on_all_sets": all(v == 1.0 for v in acc.values()),
             "example": {l: " ".join(G.VOCAB[i] for i in sets[l][0][0]) + "  ->  "
                         + " ".join(G.VOCAB[i] for i in sets[l][0][1]) for l in bins},
             "trace_shortest_id": trace(pf, task, min(sets[bins[0]][:50], key=lambda e: abs(len(e[0]) - 6))),
             "wall_s": round(time.time() - t0, 1)}
        if task.startswith("subtraction"):
            r["answer_shorter_than_a"] = {l: short_len(task, sets[l]) for l in sets}
        res[task] = r
        print("%-16s %s  %s" % (task, " ".join("%s %.3f" % (l, acc[l]) for l in acc), r["wall_s"]), flush=True)
    (out / "final.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    # the 14-section pre-check's "correct table" is a table that is exact here; subtraction's is not (see report)
    tables = {t: {"table": TABLES[t], "readable": readable(TABLES[t]),
                  "moving_heads": sum(any(m != STAY for m in col) for col in TABLES[t]),
                  "controller": CONTROLLERS[t], "registers": REG_USE,
                  "exact_on_all_bins": res[t]["exact_on_all_bins"],
                  "correct_table_for_precheck": res[t]["exact_on_all_bins"] and t in G.SUITE} for t in tasks}
    (out / "tables.json").write_text(json.dumps(tables, indent=1))
    (out / "env.json").write_text(json.dumps(env(), indent=1))


if __name__ == "__main__":
    main()
