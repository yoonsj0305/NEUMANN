"""Stage 2-0 (stage2/DESIGN.md section 2): synthesis feasibility gate -- no training, CPU only.

For one case (task, routing table): the routing is the FIXED table (C4 seeds 6-8: the selected table; the control:
the C3-2 table compiled from the untrained teacher).  The PF machine's own move code (stage1/pf.py candidates, the
token classes of the table) gives every head's position at every step; only MOVING heads (a column that is not all
"stay") are read.

* Step structure (checked against stage1/pf.py PF.forward before implementing): step t takes the input-stream token
  at position t (teacher forced), moves the heads by the table entry of that token's class, reads the heads, and
  emits the prediction of token t+1; only answer positions (answer tokens and <eos>) are scored.  So the step input
  is x_t = (code(token_t), code(read of each moving head)) and the step's output piece is (code(next token),) at an
  answer step and () otherwise.  Steps run from position 0 to the step that emits <eos>.
* Integer code: a digit token is its value (bits are the digits 0 / 1); every other token is a fixed integer >= 10
  (10 + its index among the non-digit tokens in vocabulary order: <pad> 10, <eos> 11, + 12, = 13, ...).  Output
  pieces use the same code.
* Observations: the first <= 200 sequences of the case's training data (T.train_set(task, 100000, seed); all of
  them in-distribution lengths).
* Synthesis: stage2/k_ext.factored_synthesis (the section 44 core K, inputs generalised to 1 + moving heads), driven
  counterexample-guided as the joint core's own solvers do: start from the 4 shortest sequences (their steps are the
  observations, the sequences the full examples), run the synthesis, check its first machine on every training
  sequence, add the (at most 2) shortest it gets wrong, rerun; stop when a machine reproduces every training sequence
  or at 60 CPU seconds (time.process_time) for the case.  The machine reported is the first machine of the last
  synthesis round (if any), with whether it reproduces all training sequences.
* Evaluation only after the machine is written (fixed): the existing evaluation sets (T.eval_sets(task, 1000, 500):
  in-distribution and every out-of-distribution bin), exact match of the emitted output codes.

  python stage2/s2_0.py synth --case addition_s6
  python stage2/s2_0.py eval  --case addition_s6
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import platform
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "stage1"))
sys.path.insert(0, str(HERE))
import tasks as T          # noqa: E402
import k_ext as K          # noqa: E402

N_SEQ = 200
CPU_CAP = 60.0
START = 4
ADD_PER_ROUND = 2
OUT = HERE / "results" / "s2_0"
S1 = ROOT / "stage1" / "results"
SEPS = {T.TOK["+"], T.TOK["="], T.TOK["|"]}
NONDIGIT = [i for i, v in enumerate(T.VOCAB) if v not in T.DIGITS]
CODE = {T.TOK[d]: int(d) for d in T.DIGITS}
CODE.update({tid: 10 + k for k, tid in enumerate(NONDIGIT)})


def cases():
    out = {}
    for task in ("addition", "parity"):
        for sd in (6, 7, 8):
            sel = json.loads((S1 / "c4" / ("selection_%s_s%d.json" % (task, sd))).read_text())
            tag = sel["selected"]
            pol = sel["students"][tag]["policy"]
            out["%s_s%d" % (task, sd)] = {"task": task, "data_seed": sd, "table": tag, "policy": pol,
                                          "table_source": "stage1/results/c4/selection_%s_s%d.json (selected: %s)"
                                                          % (task, sd, tag)}
    cr = json.loads((S1 / "c3" / "addition_compile_s0_ctrl_untrained" / "compile_result.json").read_text())
    out["addition_ctrl_untrained"] = {"task": "addition", "data_seed": 0, "table": "control (untrained teacher)",
                                      "policy": cr["policy"],
                                      "table_source": "stage1/results/c3/addition_compile_s0_ctrl_untrained/"
                                                      "compile_result.json (C3-2 control)"}
    return out


def token_class(tokens):
    """the 7 token classes of stage1/pf.py token_classes, per position"""
    out, after = [], False
    for x in tokens:
        if after:
            c = 5
        elif T.VOCAB[x] in T.DIGITS:
            c = 0
        elif x == T.TOK["+"]:
            c = 1
        elif x == T.TOK["="]:
            c = 2
        elif x == T.TOK["|"]:
            c = 3
        elif T.VOCAB[x] in T.NODES:
            c = 4
        else:
            c = 6
        out.append(c)
        if x in (T.TOK["="], T.TOK["|"]):
            after = True
    return out


def head_positions(tokens, policy):
    """positions of every head after the move at every step: stage1/pf.py candidates for one sequence"""
    cls = token_class(tokens)
    H = len(policy)
    h = [0] * H
    out = []
    for t, xt in enumerate(tokens):
        new = []
        for j in range(H):
            mv = policy[j][cls[t]]
            p = h[j]
            if mv == 0:
                q = p
            elif mv == 1:
                q = min(p + 1, t)
            elif mv == 2:
                q = max(p - 1, 0)
            elif mv == 3:
                q = next((i for i in range(p + 1, t + 1) if tokens[i] in SEPS), p)
            elif mv == 4:
                q = 0
            else:
                q = next((i + 1 for i in range(p, t) if tokens[i] == xt), p)
            new.append(q)
        h = new
        out.append(tuple(h))
    return out


def moving(policy):
    return [j for j, col in enumerate(policy) if any(mv != 0 for mv in col)]


def to_io(ex, policy):
    """one sequence -> (inputs: tuple of int tuples, outputs: tuple of codes, per-step pieces)"""
    p, a = ex
    tokens = list(p) + list(a)
    last = len(tokens) - 2                                  # the step that emits <eos>
    pos = head_positions(tokens[:last + 1], policy)
    mv = moving(policy)
    xs, pieces = [], []
    for t in range(last + 1):
        xs.append((CODE[tokens[t]],) + tuple(CODE[tokens[pos[t][j]]] for j in mv))
        pieces.append((CODE[tokens[t + 1]],) if t >= len(p) - 1 else ())
    return tuple(xs), tuple(CODE[v] for v in a), tuple(pieces)


def env():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "stage2"], cwd=ROOT).strip())
    except Exception:
        commit, dirty = None, None
    cpu = "?"
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    return {"code_commit": commit, "code_dirty": dirty, "python": platform.python_version(), "cpu": cpu,
            "cores": os.cpu_count(), "k_ext_source": "neumann1/joint.py @ 080541c (Q3 branch), see stage2/k_ext.py"}


def synth(a):
    cs = cases()[a.case]
    name = "s2_0_%s" % a.case
    d = OUT / name
    if (d / "final.json").exists():
        sys.exit("refusing to overwrite %s (rule 5)" % d)
    d.mkdir(parents=True, exist_ok=True)
    exs = T.train_set(cs["task"], 100000, cs["data_seed"])[:N_SEQ]
    seqs = [to_io(e, cs["policy"]) for e in exs]
    order = sorted(range(len(seqs)), key=lambda i: (len(seqs[i][0]), seqs[i][0]))
    n_in = 1 + len(moving(cs["policy"]))
    cfg = {"name": name, "case": a.case, **cs, "moving_heads": moving(cs["policy"]), "n_in": n_in,
           "code": {T.VOCAB[k]: v for k, v in CODE.items()}, "n_sequences": len(seqs), "cpu_cap_s": CPU_CAP,
           "start_sequences": START, "add_per_round": ADD_PER_ROUND,
           "k_ext": {"max_ops_u": 2, "max_holes_u": 1, "crange": [-20, 40], "z0range": [-20, 40], "want": 3,
                     "output_terms_max_ops": 1, "latent_range": [-200, 200]}}
    (d / "config.json").write_text(json.dumps(cfg, indent=1))
    (d / "env.json").write_text(json.dumps(env(), indent=1))
    logf = open(d / "log.jsonl", "w")
    t0 = time.process_time()
    deadline = t0 + CPU_CAP
    used = order[:START]
    m, rnd, stop, info = None, 0, None, {}
    while True:
        rnd += 1
        steps = []
        for i in used:
            xs, ys, pieces = seqs[i]
            steps += [(xs[:t], xs[t], pieces[t]) for t in range(len(xs))]
        examples = [(seqs[i][0], seqs[i][1]) for i in used]
        found, info = K.factored_synthesis(steps, examples, deadline, n_in=n_in, want=3)
        m = found[0] if found else None
        bad = [] if m is None else [i for i in order if K.run_factored(m, seqs[i][0]) != seqs[i][1]]
        logf.write(json.dumps({"round": rnd, "sequences_used": len(used), "steps_used": len(steps),
                               "machines": [f["show"] for f in found], "wrong_training_sequences": len(bad),
                               "cpu_s": round(time.process_time() - t0, 2),
                               "info": {k: v for k, v in info.items() if k != "regularities"}}) + "\n")
        logf.flush()
        if m is None:
            stop = "no machine (%s)" % info.get("stop", "search exhausted")
            break
        if not bad:
            stop = "machine reproduces every training sequence"
            break
        if time.process_time() >= deadline:
            stop = "cpu cap"
            break
        used = used + [i for i in bad if i not in used][:ADD_PER_ROUND]
    cpu = time.process_time() - t0
    machine = None
    if m is not None:
        machine = {"U": m["show"]["U"], "z0": m["z0"], "V": m["show"]["V"], "C": m["show"]["C"],
                   "size_U_ops": m["size"], "bits": m["bits"], "U_tree": m["U"], "ucs": list(m["ucs"]),
                   "rule": m["rule"],
                   "variables": "U: $0 = h, $1.. = inputs; V, C: $0 = h, $1 = h', $2.. = inputs; inputs = "
                                "(current token, %s)" % ", ".join("head %d read" % j for j in moving(cs["policy"]))}
    fin = {"name": name, "stopped": stop, "rounds": rnd, "cpu_s": round(cpu, 2),
           "sequences_used": len(used), "steps_used": sum(len(seqs[i][0]) for i in used),
           "training_sequences": len(seqs),
           "training_sequences_reproduced": None if m is None else len(seqs) - len(bad),
           "machine": machine, "last_info": {k: v for k, v in info.items() if k != "regularities"},
           "regularities": info.get("regularities"), "eval": None}
    (d / "final.json").write_text(json.dumps(fin, indent=1, default=list))
    print(json.dumps({k: v for k, v in fin.items() if k not in ("last_info",)}, default=list))


def run_machine(fin, x):
    mm = fin["machine"]
    m = {"U": _tup(mm["U_tree"]), "ucs": tuple(mm["ucs"]), "z0": mm["z0"], "rule": _rule(mm["rule"]),
         "terms": K._hole_free_terms(2 + fin["_n_in"], 1)}
    return K.run_factored(m, x)


def _tup(t):
    return tuple(_tup(v) if isinstance(v, list) else v for v in t)


def _rule(r):
    return tuple(tuple(v) for v in r)


def evaluate(a):
    """only after the machine is fixed (final.json written by synth)"""
    d = OUT / ("s2_0_%s" % a.case)
    fin = json.loads((d / "final.json").read_text())
    cfg = json.loads((d / "config.json").read_text())
    if fin.get("eval") is not None:
        sys.exit("already evaluated")
    res = {}
    if fin["machine"] is not None:
        fin["_n_in"] = cfg["n_in"]
        for label, exs in T.eval_sets(cfg["task"], 1000, 500).items():
            ok = 0
            for e in exs:
                xs, ys, _ = to_io(e, cfg["policy"])
                ok += run_machine(fin, xs) == ys
            res[label] = ok / len(exs)
        fin.pop("_n_in")
    fin["eval"] = res or "no machine"
    fin["eval_rule"] = "exact match of the emitted output codes (answer digits and <eos>) on T.eval_sets(task, 1000, 500)"
    (d / "final.json").write_text(json.dumps(fin, indent=1, default=list))
    print(a.case, res or "no machine")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("synth", "eval", "list"))
    p.add_argument("--case", default="")
    a = p.parse_args()
    if a.cmd == "list":
        for k, v in cases().items():
            print(k, v["table"], v["policy"], "moving", moving(v["policy"]))
    elif a.cmd == "synth":
        synth(a)
    else:
        evaluate(a)
