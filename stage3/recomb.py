"""L2b-0 (stage3/DESIGN.md 11.2, 11.3; 11.5 takes precedence): the recombination language, the hand-composed programs
multi_add and mulNM, the implementation check, and M (module reliability).

Language (11.2, fixed before any task):
  values       token sequences (list of str) and lists of token sequences
  modules      compiled library programs, prompt -> answer, run greedily (autoregressive, until <eos>); a call uses the
               module's judgment format: add(x, y) = prompt `x + y =`, mul1(a, d) = prompt `a * d =`
  combinators  split(seq, sep) -> list; tokens(seq) -> list of one-token sequences; rev_list(list); fold(f, init, list);
               map(f, list); concat(seq, seq); const(tokens...); rstrip(seq, tok): delete trailing `tok` tokens but
               keep one (leading-zero clean-up of a least-significant-digit-first number)
  combinators act on whole sequences (not autoregressive).
Programs (11.3):
  multi_add(x) = fold(lambda acc, a. add(acc, a), const("0"), split(x, "+"))
  mulNM(x)     = fold(lambda acc, b. add(rstrip(concat(const("0"), acc), "0"), mul1(A, b)), const("0"),
                      rev_list(tokens(B)))   with [A, B] = split(x, "*")
  Interface convention (recorded): a program receives the task prompt without its final "=" (the judgment format's
  query marker); multi_add's operands are the "+" segments, mulNM's A and B the two "*" segments.
Execution: every example's program is a Python generator that yields module requests (name, args); a scheduler runs
the pending requests of all examples batched per module and sends the answers back.  Calls are counted per example.

Modules for M: the C-1 students (stage2/results/c1, arm C, the selected restart of each table -- restart 0 for every
add and mul1 table, seeds 31, 32, 33), judgment checkpoint teacher_best.pt, stage2/c1a.HardReadLM unchanged.  The model
is causal (causal attention; hard-read paths and segment bits use positions <= t only), so "every teacher-forced argmax
equals the answer token and <eos>" is the same event as "greedy decoding returns the answer"; M uses the teacher-forced
pass for the correct / wrong flag and decodes greedily the examples on which some table is wrong (their outputs are
recorded, and the equivalence is checked on them).

  check            implementation check (11.3): exact integer modules; multi_add and mulNM on every bin must be 1.000
  repro            the six modules reproduce their C-1 judgment accuracies on the C-1 evaluation sets
  measure --module add|mul1   M (11.5-2): per length bin (width 10; add: longer operand 1-100, the other uniform in
                   1..longer, which one is longer at random -- the stage-1 evaluation draw; mul1: length 1-100.. 1-50,
                   multiplier 0-9) 2,000 examples: per-table exact match, strict majority of 3 (>= 2 tables right),
                   ties (exactly one right and the two wrong outputs differ), wrong majorities, pairwise co-error
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

OUT = pathlib.Path(os.environ.get("L2B_OUT", HERE / "results" / "L2b-0"))
C1 = ROOT / "stage2" / "results" / "c1"
MODULE_TASK = {"add": "addition", "mul1": "mul1"}
SEEDS = (31, 32, 33)                                   # C-1 selected restart (0) of tables 1, 2, 3


# ================================================================ language
def split(seq, sep):
    out, cur = [], []
    for t in seq:
        if t == sep:
            out.append(cur)
            cur = []
        else:
            cur.append(t)
    out.append(cur)
    return out


def tokens(seq):
    return [[t] for t in seq]


def rev_list(lst):
    return list(reversed(lst))


def concat(a, b):
    return list(a) + list(b)


def const(*toks):
    return list(toks)


def rstrip(seq, tok):
    s = list(seq)
    while len(s) > 1 and s[-1] == tok:
        s.pop()
    return s


def fold(f, init, lst):
    acc = init
    for e in lst:
        acc = yield from f(acc, e)
    return acc


def map_(f, lst):
    out = []
    for e in lst:
        out.append((yield from f(e)))
    return out


def call(module, *args):
    return (yield (module, tuple(args)))


FORMAT = {"add": lambda x, y: list(x) + ["+"] + list(y) + ["="],
          "mul1": lambda a, d: list(a) + ["*"] + list(d) + ["="]}


# ================================================================ programs (11.3)
def multi_add(x):
    return (yield from fold(lambda acc, a: call("add", acc, a), const("0"), split(x, "+")))


def mulNM(x):
    A, B = split(x, "*")

    def step(acc, b):
        shifted = rstrip(concat(const("0"), acc), "0")
        prod = yield from call("mul1", A, b)
        return (yield from call("add", shifted, prod))
    return (yield from fold(step, const("0"), rev_list(tokens(B))))


PROGRAMS = {"multi_add": multi_add, "mulNM": mulNM}


def execute(program, prompts, backends):
    """run `program` on every prompt (token lists ending with '='); backends: {module: f(list of prompts) -> list of
    answers}.  Returns (outputs, calls per example as {module: count})."""
    n = len(prompts)
    gens, req, out = [], {}, [None] * n
    calls = [{m: 0 for m in backends} for _ in range(n)]

    def advance(i, value):
        try:
            r = gens[i].send(value)
            req[i] = r
        except StopIteration as e:
            out[i] = e.value
    for i, p in enumerate(prompts):
        assert p[-1] == "=", p
        gens.append(program(p[:-1]))
        advance(i, None)
    while req:
        by = {}
        for i, (m, args) in req.items():
            by.setdefault(m, []).append((i, FORMAT[m](*args)))
        req = {}
        for m, items in by.items():
            ans = backends[m]([q for _, q in items])
            for (i, _), a in zip(items, ans):
                calls[i][m] += 1
                advance(i, a)
    return out, calls


# ================================================================ exact modules (implementation check only)
def _int(seq):
    return int("".join(reversed(seq)))


def _seq(v):
    return list(str(v)[::-1])


def exact_add(prompts):
    out = []
    for p in prompts:
        x, y = split(p[:-1], "+")
        out.append(_seq(_int(x) + _int(y)))
    return out


def exact_mul1(prompts):
    out = []
    for p in prompts:
        a, d = split(p[:-1], "*")
        assert len(d) == 1
        out.append(_seq(_int(a) * _int(d)))
    return out


EXACT = {"add": exact_add, "mul1": exact_mul1}


# ================================================================ composite task data (R bins, 11.5-3)
R_BINS = {"mulNM": [("id", 1, 10, None), ("ood1", 11, 20, None), ("ood2", 21, 30, None), ("ood3", 31, 50, None)],
          "multi_add": [("id", 1, 10, (2, 5)), ("ood1", 11, 20, (6, 10)), ("ood2", 21, 30, (11, 20)),
                        ("ood3", 31, 50, (21, 40))]}


def _num(rng, ndig):
    return rng.randrange(10) if ndig == 1 else rng.randrange(10 ** (ndig - 1), 10 ** ndig)


def composite_example(task, rng, lo, hi, k):
    """check data only: n, m (mulNM) and every operand's digit count (multi_add) independent uniform in lo..hi, k
    uniform in its range.  (How R draws these is a question for the design chat before R.)"""
    if task == "mulNM":
        a, b = _num(rng, rng.randint(lo, hi)), _num(rng, rng.randint(lo, hi))
        return _seq(a) + ["*"] + _seq(b) + ["="], _seq(a * b)
    nums = [_num(rng, rng.randint(lo, hi)) for _ in range(rng.randint(*k))]
    p = []
    for j, v in enumerate(nums):
        p += (["+"] if j else []) + _seq(v)
    return p + ["="], _seq(sum(nums))


def cmd_check(a):
    import h0a
    res = {"design": "stage3/DESIGN.md 11.3 implementation check (exact integer modules; not used for the verdict)",
           "note": "check data: n, m and operand digit counts independent uniform in the bin, k uniform", "tasks": {}}
    ok_all = True
    for task, bins in R_BINS.items():
        res["tasks"][task] = {}
        for lab, lo, hi, k in bins:
            rng = random.Random("L2b-0:check:%s:%s" % (task, lab))
            n = 1000 if lab == "id" else (200 if lab == "ood3" else 500)
            exs = [composite_example(task, rng, lo, hi, k) for _ in range(n)]
            if lab == "id":                                         # edge cases: zeros, one-digit operands
                if task == "mulNM":
                    exs += [(["0", "*", "0", "="], ["0"]), (["5", "*", "0", "="], ["0"]),
                            (["0", "*", "1", "2", "="], ["0"]), (["0", "0", "1", "*", "0", "1", "="],
                                                                     _seq(100 * 10))]   # 100 x 10 (attempt 1 had 100 x 100 here)
                else:
                    exs += [(["0", "+", "0", "="], ["0"]), (["9", "+", "1", "+", "0", "="], ["0", "1"])]
            t0 = time.time()
            outs, calls = execute(PROGRAMS[task], [p for p, _ in exs], EXACT)
            acc = sum(o == ans for o, (_, ans) in zip(outs, exs)) / len(exs)
            ok_all &= acc == 1.0
            c = [sum(x.values()) for x in calls]
            res["tasks"][task][lab] = {"lengths": [lo, hi], "k": k, "examples": len(exs), "accuracy": acc,
                                       "calls_mean": sum(c) / len(c), "calls_max": max(c),
                                       "calls_by_module_max": {m: max(x[m] for x in calls) for m in EXACT},
                                       "seconds": round(time.time() - t0, 2)}
            print(task, lab, res["tasks"][task][lab], flush=True)
    res["all_1.000"] = ok_all
    res["env"] = h0a.env(["stage3/recomb.py"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "impl_check.json").write_text(json.dumps(res, indent=1))
    print("implementation check all 1.000:", ok_all)
    if not ok_all:
        sys.exit(1)


# ================================================================ neural modules
_SETUP = False


def setup():
    global _SETUP
    if _SETUP:
        return
    import torch
    import g_adapter                                       # '*' token (ids of the stage-1 tokens unchanged)
    import c1a
    g_adapter.install()
    torch.set_num_threads(1)
    _SETUP = True


def run_dir(module, i):
    return C1 / ("c1_%s__hardread__1M__s%d__N100000__table%d" % (MODULE_TASK[module], SEEDS[i - 1], i))


def load_module(module, i):
    import torch
    import c1a
    setup()
    d = run_dir(module, i)
    sel = json.loads((C1 / ("selection_%s_table%d.json" % (MODULE_TASK[module], i))).read_text())
    assert sel["selected_restart"] == 0 and sel["selected_seed"] == SEEDS[i - 1], sel
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"] and ck["kind"] == "hardread"
    vocab = ck["model"]["tok.weight"].shape[0]
    m = c1a.HardReadLM(vocab, **ck["cfg"])
    m.load_state_dict(ck["model"])
    m.eval()
    return m, {"dir": str(d.relative_to(ROOT)), "step": ck["step"], "vocab": vocab, "table": ck["cfg"]["table"],
               "judgment_acc": fin["judgment"]["acc"]}


def ids(seq):
    import tasks as T
    return [T.TOK[t] for t in seq]


def teacher_forced_ok(model, exs, bs=128):
    """exs: [(prompt ids, answer ids + [EOS])] -> list of bools (every scored argmax right)"""
    import torch
    import run as R
    ok = []
    with torch.no_grad():
        for j in range(0, len(exs), bs):
            x, y = R.make_batch(exs[j:j + bs])
            pred = model(x).argmax(-1)
            m = y != -100
            ok += ((pred == y) | ~m).all(1).tolist()
    return ok


def greedy(model, prompts, extra=2, bs=64):
    """prompts: token-string lists ending with '='; greedy decoding until <eos> or len(prompt) + extra tokens.
    Returns the answers (token strings, <eos> excluded; a missing <eos> is recorded by '<noeos>' at the end)."""
    import torch
    import tasks as T
    out = [None] * len(prompts)
    order = sorted(range(len(prompts)), key=lambda i: len(prompts[i]))
    with torch.no_grad():
        for j in range(0, len(order), bs):
            idx = order[j:j + bs]
            P = [ids(prompts[i]) for i in idx]
            cap = [len(p) + extra for p in P]
            Tn = max(len(p) + c for p, c in zip(P, cap))
            x = torch.full((len(idx), Tn), T.PAD, dtype=torch.long)
            for r, p in enumerate(P):
                x[r, :len(p)] = torch.tensor(p)
            pos = [len(p) - 1 for p in P]                         # logit at pos predicts token pos + 1
            done = [False] * len(idx)
            gen = [[] for _ in idx]
            while not all(done):
                hi = max(pos[r] for r in range(len(idx)) if not done[r]) + 1
                logits = model(x[:, :hi])
                for r in range(len(idx)):
                    if done[r]:
                        continue
                    tok = int(logits[r, pos[r]].argmax())
                    if tok == T.EOS:
                        done[r] = True
                        continue
                    gen[r].append(T.VOCAB[tok])
                    pos[r] += 1
                    x[r, pos[r]] = tok
                    if len(gen[r]) >= cap[r]:
                        gen[r].append("<noeos>")
                        done[r] = True
            for r, i in enumerate(idx):
                out[i] = gen[r]
    return out


def cmd_repro(a):
    import tasks as T
    import h0a
    setup()
    res = {"design": "the C-1 modules reproduce their C-1 judgment accuracies (teacher-forced exact match on the C-1 "
                     "evaluation sets, tasks.eval_sets(task, 1000, 500))", "modules": {}}
    for mod in ("add", "mul1"):
        ev = T.eval_sets(MODULE_TASK[mod], 1000, 500)
        for i in (1, 2, 3):
            m, info = load_module(mod, i)
            acc = {lab: sum(teacher_forced_ok(m, ex)) / len(ex) for lab, ex in ev.items()}
            info["reproduced_acc"] = acc
            info["equal"] = all(abs(acc[l] - info["judgment_acc"][l]) < 1e-9 for l in acc)
            res["modules"]["%s_table%d" % (mod, i)] = info
            print(mod, i, acc, info["equal"], flush=True)
    res["all_equal"] = all(v["equal"] for v in res["modules"].values())
    res["env"] = h0a.env(["stage3/recomb.py"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "module_repro.json").write_text(json.dumps(res, indent=1))


# ================================================================ M (11.5-2)
M_BINS = {"add": [(lo, lo + 9) for lo in range(1, 100, 10)], "mul1": [(lo, lo + 9) for lo in range(1, 50, 10)]}
M_N = 2000


def module_example(mod, rng, lo, hi):
    if mod == "add":                                    # stage-1 evaluation draw (tasks.draw, train_dist=False)
        mx = rng.randint(lo, hi)
        o = rng.randint(1, mx)
        da, db = (mx, o) if rng.random() < 0.5 else (o, mx)
        x, y = _num(rng, da), _num(rng, db)
        return _seq(x) + ["+"] + _seq(y) + ["="], _seq(x + y)
    n = rng.randint(lo, hi)                             # g_tasks.mul1
    x, d = _num(rng, n), rng.randrange(10)
    return _seq(x) + ["*", str(d), "="], _seq(x * d)


def cmd_measure(a):
    import tasks as T
    import h0a
    setup()
    mod = a.module
    d = OUT / ("M_%s" % mod)
    d.mkdir(parents=True, exist_ok=True)
    models, infos = [], []
    for i in (1, 2, 3):
        m, info = load_module(mod, i)
        models.append(m)
        infos.append(info)
    done = set()
    if (d / "log.jsonl").exists():
        done = {json.loads(l)["bin"] for l in (d / "log.jsonl").read_text().splitlines() if l.strip()}
    else:
        (d / "config.json").write_text(json.dumps({
            "design": "stage3/DESIGN.md 11.5-2 M", "module": mod, "modules": infos, "bins": M_BINS[mod],
            "examples_per_bin": M_N, "generation_seed": "L2b-0:M:%s:<lo>-<hi>" % mod,
            "draw": ("longer operand uniform in the bin, the other uniform in 1..longer, which one is longer at random"
                     if mod == "add" else "multiplicand length uniform in the bin, multiplier digit uniform 0-9"),
            "correct": "teacher-forced exact match of the answer and <eos> (= greedy decoding exact, causal model)",
            "majority3": "strict: >= 2 of the 3 tables right; ties (exactly one right, the two wrong outputs "
                         "different) counted separately; wrong majority = >= 2 identical wrong outputs"}, indent=1))
        (d / "env.json").write_text(json.dumps(h0a.env(["stage3/recomb.py"]), indent=1))
    for lo, hi in M_BINS[mod]:
        lab = "%d-%d" % (lo, hi)
        if lab in done:
            continue
        t0 = time.time()
        rng = random.Random("L2b-0:M:%s:%s" % (mod, lab))
        exs = [module_example(mod, rng, lo, hi) for _ in range(M_N)]
        enc = [(ids(p), ids(ans) + [T.EOS]) for p, ans in exs]
        flags = [teacher_forced_ok(m, enc) for m in models]
        t_tf = time.time() - t0
        bad = [j for j in range(M_N) if not all(f[j] for f in flags)]
        outs = [greedy(m, [exs[j][0] for j in bad]) for m in models]
        mismatch = 0
        maj = ties = wrong_maj = 0
        for j in range(M_N):
            r = [f[j] for f in flags]
            maj += sum(r) >= 2
        for q, j in enumerate(bad):
            o = [tuple(outs[i][q]) for i in range(3)]
            r = [flags[i][j] for i in range(3)]
            mismatch += sum((o[i] == tuple(exs[j][1])) != r[i] for i in range(3))
            wrong = [o[i] for i in range(3) if not r[i]]
            if sum(r) == 1 and wrong[0] != wrong[1]:
                ties += 1
            if len(wrong) >= 2 and max(wrong.count(w) for w in wrong) >= 2:
                wrong_maj += 1
        err = [[not f[j] for j in range(M_N)] for f in flags]
        co = {"%d,%d" % (i + 1, k + 1): sum(err[i][j] and err[k][j] for j in range(M_N)) for i in range(3)
              for k in range(i + 1, 3)}
        row = {"bin": lab, "examples": M_N, "single_acc": [sum(f) / M_N for f in flags],
               "single_wrong": [M_N - sum(f) for f in flags], "maj3_strict_acc": maj / M_N,
               "maj3_wrong": M_N - maj, "ties_one_right_two_different_wrong": ties,
               "wrong_majorities": wrong_maj, "co_error_pairs": co,
               "all_three_wrong": sum(all(e[j] for e in err) for j in range(M_N)),
               "examples_any_wrong": len(bad), "greedy_vs_teacher_forced_mismatches": mismatch,
               "seconds": round(time.time() - t0, 1), "seconds_teacher_forced": round(t_tf, 1)}
        with open(d / "log.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")
        with open(d / "errors.jsonl", "a") as f:
            for q, j in enumerate(bad):
                f.write(json.dumps({"bin": lab, "prompt": " ".join(exs[j][0]), "answer": " ".join(exs[j][1]),
                                    "right": [flags[i][j] for i in range(3)],
                                    "outputs": [" ".join(outs[i][q]) for i in range(3)]}) + "\n")
        print(json.dumps(row), flush=True)
    rows = [json.loads(l) for l in (d / "log.jsonl").read_text().splitlines() if l.strip()]
    if len(rows) == len(M_BINS[mod]):
        fin = {"module": mod, "bins": rows,
               "min_single_acc": [min(r["single_acc"][i] for r in rows) for i in range(3)],
               "min_maj3_strict_acc": min(r["maj3_strict_acc"] for r in rows),
               "admission_threshold": 0.999,
               "admitted_single": [min(r["single_acc"][i] for r in rows) >= 0.999 for i in range(3)],
               "admitted_maj3": min(r["maj3_strict_acc"] for r in rows) >= 0.999,
               "admission_rule": "every length bin >= 0.999 (the composition receives every length)",
               "env": h0a.env(["stage3/recomb.py"])}
        (d / "final.json").write_text(json.dumps(fin, indent=1))
        print("final", json.dumps({k: fin[k] for k in ("min_single_acc", "min_maj3_strict_acc")}))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    sp.add_parser("repro")
    q = sp.add_parser("measure")
    q.add_argument("--module", choices=("add", "mul1"), required=True)
    a = p.parse_args()
    {"check": cmd_check, "repro": cmd_repro, "measure": cmd_measure}[a.cmd](a)


if __name__ == "__main__":
    main()
