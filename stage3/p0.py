"""3-P P0: memory-augmented RNN baselines (Stack-RNN, Tape-RNN), official code (stage3/DESIGN.md 10.3, 10.5).

Official code: github.com/google-deepmind/neural_networks_chomsky_hierarchy commit 2b8eb4b (e_tasks.SOURCE), used
unchanged: experiments/constants.MODEL_BUILDERS ('stack_rnn' = rnn.make_rnn + stack_rnn.StackRNNCore,
'tape_rnn' = rnn.make_rnn + tape_rnn.TapeInputLengthJumpCore, inner core hk.VanillaRNN), the non-autoregressive
wrapper experiments/utils.make_model_with_empty_targets (input tape + one empty token per output position), the
loss of experiments/example.py (mean over examples and positions of the summed pointwise cross-entropy) and the
optimizer of experiments/training.py (optax.clip_by_global_norm(1.0) then optax.adam(lr)), model_init_seed 0.

10.5 decisions:
  1 shape: every example gets as many empty tokens as its true answer length (<eos> excluded); the batch (128) is
    split into groups of the same (prompt length, answer length); one step = the example-weighted mean of the
    group losses (one gradient, one clip, one Adam update).  Only addition and N x 1 have more than one shape.
  2 data: fresh examples every step (official), not our fixed N = 100,000.
  3 lengths: official curriculum, one n per batch, uniform over the task's training lengths (1-10; pairswap: the
    even numbers 2-10).  n is the bin coordinate: for addition the longer operand (the stage-1 out-of-distribution
    draw with lo = hi = n: the other operand uniform 1..n); every other task draws with lo = hi = n.
  4 input: the 8 judged tasks: the judged prompt (BOS and '=' included where the judged format has them); the three
    external tasks: the benchmark's bare input (e_tasks.GEN, no BOS, no '=').
  5 output: the answer tokens without <eos>; accuracy = exact match of every answer token (argmax).
  6 memory: stack size = tape size = 256 (>= the longest evaluation sequence, 163 + answer); hidden 256, cell 8 for
    both models (the official Tape-RNN example values); everything else official (1 stack / tape, VanillaRNN).
  7 evaluation: our sets (in-distribution 1,000, each out-of-distribution bin 500, the stage-1 seeds
    'eval:<task>:id' / 'eval:<task>:<lo>-<hi>' with the judged draw), every 1,000 steps; judgment = the highest
    in-distribution checkpoint (earliest on ties); stop at in-distribution >= 0.99 twice in a row or 100,000 steps.
Learning-rate tuning (10.3): lr x 0.5 and x 2 when the default run has in-distribution < 0.95 or bin 2 >= 0.10.

  python -I stage3/p0.py run --task T --arch stack_rnn|tape_rnn [--lr-mult M] PKG_PARENT
  (PKG_PARENT: a directory holding the official package as neural_networks_chomsky_hierarchy)
"""
from __future__ import annotations
import argparse
import ctypes
import gc
import json
import os
import pathlib
import pickle
import platform
import random
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = pathlib.Path(os.environ.get("P0_OUT", HERE / "results" / "3-P" / "p0"))
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.append(p)

TASKS = ("addition", "copy", "mul1", "prefix_sum", "reverse", "dup", "interleave", "pairswap",
         "even_pairs", "reverse_string", "duplicate_string")
EXTERNAL = ("even_pairs", "reverse_string", "duplicate_string")
ARCHS = ("stack_rnn", "tape_rnn")
ARCH_PARAMS = {"stack_rnn": {"hidden_size": 256, "stack_cell_size": 8, "stack_size": 256},
               "tape_rnn": {"hidden_size": 256, "memory_cell_size": 8, "memory_size": 256}}
BATCH, LR = 128, 1e-3
MAX_STEPS = int(os.environ.get("P0_MAX_STEPS", 100_000))          # smoke runs only (P0_OUT elsewhere)
EVAL_EVERY = int(os.environ.get("P0_EVAL_EVERY", 1000))
RSS_FREE_MB = int(os.environ.get("P0_RSS_FREE_MB", 0))   # >0: after an evaluation, free eval executables above this RSS


def rss_mb():
    return int(open("/proc/self/status").read().split("VmRSS:")[1].split()[0]) // 1024
ID_SIZE, OOD_SIZE = 1000, 500
EVAL_SUB = 250


# ---------------------------------------------------------------- data (pure python generators)
def judged_draw(task):
    """the judged format's draw: (rng, lo, hi, train_dist) -> (prompt tokens, answer tokens without <eos>, n)"""
    if task == "addition":
        import tasks as T1
        return T1.draw, T1.SPEC[task]
    if task in ("copy", "mul1", "prefix_sum"):
        import g_tasks as G
        return (lambda rng, lo, hi, train_dist=False: G.draw(task, rng, lo, hi, train_dist=train_dist)), G.SPEC[task]
    if task == "reverse":
        import h_tasks as HT
        import g_tasks as G

        def d(rng, lo, hi, train_dist=False):
            p, a, n = G.draw("reverse", rng, lo, hi, train_dist=train_dist)
            return [HT.BOS] + p, a, n                                   # stage2/h_adapter.h_draw
        return d, HT.SPEC["reverse"]
    if task in ("dup", "interleave", "pairswap"):
        import l_tasks as L
        return (lambda rng, lo, hi, train_dist=False: L.draw(task, rng, lo, hi, train_dist=train_dist)), L.SPEC[task]
    import e_tasks as E

    def d(rng, lo, hi, train_dist=False):
        inp, out, n = E.raw_draw(task, rng, lo, hi)                     # the benchmark's bare input / output
        return [str(v) for v in inp], [str(v) for v in out], n
    return d, E.SPEC[task]


def task_draw(task):
    """(fn(rng, lo, hi, train_dist) -> (prompt, answer, n), spec); addition's draw is the stage-1 one"""
    if task == "addition":
        import tasks as T1
        return (lambda rng, lo, hi, train_dist=False: T1.draw("addition", rng, lo, hi, train_dist=train_dist)), T1.SPEC[task]
    return judged_draw(task)


def train_lengths(task, spec):
    lo, hi = spec["train"]
    return [n for n in range(lo, hi + 1) if task != "pairswap" or n % 2 == 0]


def eval_sets(task):
    """stage1/tasks.eval_sets logic (non-MQAR) with the judged draw, <eos> not appended"""
    draw, spec = task_draw(task)
    out = {}
    lo, hi = spec["id"]
    rng = random.Random("eval:%s:id" % task)
    out["id_%d-%d" % (lo, hi)] = [draw(rng, lo, hi, train_dist=True)[:2] for _ in range(ID_SIZE)]
    for lo, hi in spec["ood"]:
        rng = random.Random("eval:%s:%d-%d" % (task, lo, hi))
        out["ood_%d-%d" % (lo, hi)] = [draw(rng, lo, hi)[:2] for _ in range(OOD_SIZE)]
    return out


def vocabularies(task, evs):
    """input / output symbol lists: from the evaluation sets and 20,000 training draws (every length)"""
    draw, spec = task_draw(task)
    rng = random.Random("p0:vocab:%s" % task)
    ins, outs = set(), set()
    for exs in evs.values():
        for p, a in exs:
            ins.update(p)
            outs.update(a)
    for _ in range(20000):
        n = rng.choice(train_lengths(task, spec))
        p, a, _ = draw(rng, n, n)
        ins.update(p)
        outs.update(a)
    return sorted(ins), sorted(outs)


# ---------------------------------------------------------------- model and training
def env_info(pkg):
    import jax
    import haiku
    import optax
    import numpy
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "stage3/p0.py"], cwd=ROOT).strip())
    except Exception:
        commit, dirty = None, None
    try:
        ocommit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                          cwd=os.path.join(pkg, "neural_networks_chomsky_hierarchy")).decode().strip()
    except Exception:
        ocommit = None
    cpu = "?"
    try:
        cpu = [x.split(":", 1)[1].strip() for x in open("/proc/cpuinfo") if x.startswith("model name")][0]
    except Exception:
        pass
    return {"code_commit": commit, "code_dirty": dirty, "official_commit": ocommit, "jax": jax.__version__,
            "haiku": haiku.__version__, "optax": optax.__version__, "numpy": numpy.__version__,
            "python": platform.python_version(), "cpu": cpu, "cores": os.cpu_count(),
            "xla_flags": os.environ.get("XLA_FLAGS", "")}


def cmd_run(a):
    sys.path.insert(0, a.pkg)
    import numpy as np
    import jax
    import jax.numpy as jnp
    import haiku as hk
    import optax
    from neural_networks_chomsky_hierarchy.experiments import constants, utils

    tag = "" if a.lr_mult == 1.0 else "__lrx%g" % a.lr_mult
    name = "p0_%s__%s__s0%s" % (a.task, a.arch, tag)
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    import fcntl                                      # one process per run directory (exit 75 if already running)
    lock = open(d / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(name, "already running", flush=True)
        sys.exit(75)
    draw, spec = task_draw(a.task)
    evs = eval_sets(a.task)
    ivoc, ovoc = vocabularies(a.task, evs)
    iix, oix = {s: i for i, s in enumerate(ivoc)}, {s: i for i, s in enumerate(ovoc)}
    lens = train_lengths(a.task, spec)
    lr = LR * a.lr_mult
    cfg = {"name": name, "task": a.task, "arch": a.arch, "arch_params": ARCH_PARAMS[a.arch], "seed": 0,
           "model_init_seed": 0, "batch": BATCH, "lr": lr, "lr_mult": a.lr_mult, "max_steps": MAX_STEPS,
           "eval_every": EVAL_EVERY, "optimizer": "clip_by_global_norm(1.0) + adam(lr)",
           "loss": "mean over examples (weighted by group size) and positions of summed pointwise cross-entropy",
           "data": "fresh examples every step; one n per batch uniform over %s" % lens,
           "input": "bare benchmark input" if a.task in EXTERNAL else "judged prompt (BOS, '=' as judged)",
           "output": "answer tokens without <eos>, one empty token per answer position",
           "input_vocab": ivoc, "output_vocab": ovoc, "id_size": ID_SIZE, "ood_size": OOD_SIZE,
           "spec": spec, "design": "stage3/DESIGN.md 10.3, 10.5"}
    ck_path = d / "ckpt.pt"                           # resume state (pickle; *.pt is git-ignored)
    resume = ck_path.exists() and (d / "log.jsonl").exists() and not (d / "final.json").exists()
    if not resume:
        (d / "config.json").write_text(json.dumps(cfg, indent=1))
        (d / "env.json").write_text(json.dumps(env_info(a.pkg), indent=1))

    core_model = constants.MODEL_BUILDERS[a.arch](output_size=len(ovoc), return_all_outputs=True,
                                                  **ARCH_PARAMS[a.arch])

    class _Len:                                       # utils.make_model_with_empty_targets reads output_length
        def __init__(self, k):
            self.k = k

        def output_length(self, input_length):
            return self.k
    models = {}

    def model_for(k):
        if k not in models:
            models[k] = hk.transform(utils.make_model_with_empty_targets(core_model, _Len(k), 0, False))
        return models[k]

    def onehot(exs):
        x = np.zeros((len(exs), len(exs[0][0]), len(ivoc)), np.float32)
        y = np.zeros((len(exs), len(exs[0][1]), len(ovoc)), np.float32)
        for i, (p, ans) in enumerate(exs):
            x[i, np.arange(len(p)), [iix[s] for s in p]] = 1
            y[i, np.arange(len(ans)), [oix[s] for s in ans]] = 1
        return jnp.asarray(x), jnp.asarray(y)

    def group(exs):
        g = {}
        for e in exs:
            g.setdefault((len(e[0]), len(e[1])), []).append(e)
        return g

    def loss_k(k):
        m = model_for(k)

        def f(params, x, y):
            out = m.apply(params, None, x)
            return jnp.mean(jnp.sum(-y * jax.nn.log_softmax(out), axis=-1))
        return f
    grad_fns, pred_fns = {}, {}

    def grad_fn(k):
        if k not in grad_fns:
            grad_fns[k] = jax.jit(jax.value_and_grad(loss_k(k)))
        return grad_fns[k]

    def pred_fn(k):
        if k not in pred_fns:
            m = model_for(k)
            pred_fns[k] = jax.jit(lambda params, x: jnp.argmax(m.apply(params, None, x), -1))
        return pred_fns[k]

    opt = optax.chain(optax.clip_by_global_norm(1.0), optax.adam(lr))
    rng = random.Random("p0:train:%s:%s:%g" % (a.task, a.arch, a.lr_mult))
    first = [draw(rng, lens[0], lens[0])[:2]]
    init_model = model_for(len(first[0][1]))
    params = init_model.init(jax.random.PRNGKey(0), onehot(first)[0])
    opt_state = opt.init(params)
    upd = jax.jit(lambda g, s, p: opt.update(g, s, p))

    frees = [0]

    def evaluate(params):
        acc = {}
        for lab, exs in evs.items():
            ok = 0
            for shape, ex in group(exs).items():
                for j in range(0, len(ex), EVAL_SUB):
                    chunk = ex[j:j + EVAL_SUB]
                    x, y = onehot(chunk)
                    pr = np.asarray(pred_fn(shape[1])(params, x))
                    ok += int((pr == np.asarray(y).argmax(-1)).all(-1).sum())
            acc[lab] = ok / len(exs)
        if RSS_FREE_MB and rss_mb() > RSS_FREE_MB:     # drop evaluation-only executables (recompiled next time;
            pred_fns.clear()                            # same function and shapes, so the same predictions)
            models.clear()
            gc.collect()
            try:
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            except OSError:
                pass
            frees[0] += 1
        return acc

    labels = list(evs)
    best = None
    hits = 0
    t_train = t_eval = 0.0
    stopped = "max steps"
    last = None
    start = 1
    resumes = []
    if resume:                                        # continue exactly where the last checkpoint left off
        with open(ck_path, "rb") as f:
            ck = pickle.load(f)
        params = jax.tree_util.tree_map(jnp.asarray, ck["params"])
        opt_state = jax.tree_util.tree_map(jnp.asarray, ck["opt_state"])
        rng.setstate(ck["rng"])
        best, hits, last, t_train, t_eval, resumes = (ck["best"], ck["hits"], ck["last"], ck["t_train"],
                                                      ck["t_eval"], ck["resumes"])
        frees[0] = ck.get("eval_cache_frees", 0)
        start = ck["step"] + 1
        kept = [x for x in (d / "log.jsonl").read_text().splitlines() if json.loads(x)["step"] <= ck["step"]]
        (d / "log.jsonl").write_text("".join(x + "\n" for x in kept))
        resumes = resumes + [{"from_step": ck["step"], "time_utc": time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                 time.gmtime()),
                              "env": env_info(a.pkg)}]
        (d / "resumes.json").write_text(json.dumps(resumes, indent=1))
        print(name, "resumed from step", ck["step"], flush=True)
    log = open(d / "log.jsonl", "a" if resume else "w")
    for step in range(start, MAX_STEPS + 1):
        t0 = time.time()
        n = rng.choice(lens)
        exs = [draw(rng, n, n)[:2] for _ in range(BATCH)]
        tot_g, tot_l = None, 0.0
        for shape, ex in group(exs).items():
            x, y = onehot(ex)
            lv, g = grad_fn(shape[1])(params, x, y)
            w = len(ex) / BATCH
            g = jax.tree_util.tree_map(lambda v: v * w, g)
            tot_g = g if tot_g is None else jax.tree_util.tree_map(jnp.add, tot_g, g)
            tot_l += float(lv) * w
        updates, opt_state = upd(tot_g, opt_state, params)
        params = optax.apply_updates(params, updates)
        t_train += time.time() - t0
        if step % EVAL_EVERY == 0:
            t1 = time.time()
            acc = evaluate(params)
            t_eval += time.time() - t1
            rec = {"step": step, "train_loss_last_batch": tot_l, "acc": acc, "wall_train_s": round(t_train, 1),
                   "wall_eval_s": round(t_eval, 1)}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(name, json.dumps(rec), flush=True)
            last = rec
            if best is None or acc[labels[0]] > best["acc"][labels[0]]:
                best = rec
            hits = hits + 1 if acc[labels[0]] >= 0.99 else 0
            if hits >= 2:
                stopped = "early stop: in-distribution >= 0.99 at two consecutive evaluations"
                break
            ck = {"step": step, "params": jax.device_get(params), "opt_state": jax.device_get(opt_state),
                  "rng": rng.getstate(), "best": best, "hits": hits, "last": last, "t_train": t_train,
                  "t_eval": t_eval, "resumes": resumes, "eval_cache_frees": frees[0]}
            with open(str(ck_path) + ".tmp", "wb") as f:
                pickle.dump(ck, f)
            os.replace(str(ck_path) + ".tmp", ck_path)
    fin = {"name": name, "steps": last["step"], "stopped": stopped, "judgment_rule": "highest in-distribution "
           "accuracy, earliest on ties", "judgment": {"step": best["step"], "acc": best["acc"]},
           "last": {"step": last["step"], "acc": last["acc"]}, "wall_train_s": round(t_train, 1),
           "wall_eval_s": round(t_eval, 1), "params": int(sum(v.size for v in jax.tree_util.tree_leaves(params))),
           "resumed_from_steps": [r["from_step"] for r in resumes], "eval_cache_frees": frees[0]}
    (d / "final.json").write_text(json.dumps(fin, indent=1))
    if ck_path.exists():
        ck_path.unlink()
    print(name, "final", json.dumps(fin), flush=True)


def needs_tuning(task, arch):
    f = OUT / ("p0_%s__%s__s0" % (task, arch)) / "final.json"
    j = json.loads(f.read_text())["judgment"]["acc"]
    labs = list(j)
    return j[labs[0]] < 0.95 or j[labs[2]] >= 0.10


def cmd_tunelist(a):
    for t in TASKS:
        for ar in ARCHS:
            if needs_tuning(t, ar):
                for m in (0.5, 2.0):
                    print(t, ar, m)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--task", required=True, choices=TASKS)
    r.add_argument("--arch", required=True, choices=ARCHS)
    r.add_argument("--lr-mult", type=float, default=1.0)
    r.add_argument("pkg")
    sub.add_parser("tunelist")
    a = ap.parse_args()
    {"run": cmd_run, "tunelist": cmd_tunelist}[a.cmd](a)


if __name__ == "__main__":
    main()
