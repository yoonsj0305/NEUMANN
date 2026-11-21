"""H-0a diagnostics (stage2/DESIGN.md 9.4, 9.8) -- no teacher, student or baseline training; no change to the
dependency or compile code (stage1/*.py are imported, not edited).

  bos   1. BOS expressivity (9.4-1).  For the six H-0 tasks (copy, reverse, xor, mul1, prefix_sum, rev_xor) and the
           stage-1 tasks addition and parity, with BOS in front of every prompt (stage2/h_tasks.py): a hand-written move
           table in the PF-search form (3 heads x 7 token kinds -> one of the 6 PF moves) and a hand-written update
           controller drive the stage-1 PF machine itself (stage1/pf.py PF.forward with a controller; moves, reads,
           causality and registers are the PF code), scored with the stage-1 teacher-forced sequence exact match
           (stage1/run.py exact_match).  Representable iff 1.000 on the in-distribution bin and every
           out-of-distribution bin.  reverse and rev_xor have no end-marker head: <eos> exactly when the content head
           (the head that reads the operand backwards) reads BOS.  Also run (same criterion, not required): the
           selection-only set and the first 2,000 training examples of the H-0 seeds 15, 16, 17.
  xor   2. Failed XOR teachers (9.4-2), the kept judgment checkpoints (teacher_best.pt) of G-0 seed 10 and G-0'
           seeds 13, 14, 214, without BOS (their training format), through the token-only adapter
           (stage2/g_adapter.py):
           - token accuracy on "select:xor" (1,000): teacher-forced argmax over the answer tokens (every exact-match
             target: the answer bits and <eos>; the bits alone also recorded), with the sequence accuracy;
           - table_reads of the table compiled by the existing rule (stage1/c3_compile.py --dependency substitution,
             pre-check gate on, unchanged; run separately into results/h0a/xor_failed/<run>_compile): at the step that
             outputs c_k, the share of (example, k) in which head j reads x_k / y_k (stage1/c1_3_table_reads.py
             adapted to the '^' format), on "select:xor";
           - the pre-check ratio (compile_result.json).
  sim   3. Compiled reverse tables on BOS inputs (9.8-1): the G-0 / G-0' reverse tables of seeds 10, 11 (G-0) and
           12, 13, 14 (G-0'), each head column simulated with the PF move code (stage2/g0a.head_path ->
           stage1/pf.candidates) on the BOS reverse sets.  Per head and bin: the share of (example, answer step k = 1..n)
           in which the head reads x_{n-k+1} (the k-th answer digit's source), and the share of examples in which the
           head reads BOS at the <eos> step.  The content head = the head with the highest first share.

  python stage2/h0a.py bos        # stage2/results/h0a/bos/{config,tables,final,env}.json
  python stage2/h0a.py xor        # stage2/results/h0a/xor_failed/diagnosis.json   (after the four compiles)
  python stage2/h0a.py sim        # stage2/results/h0a/reverse_bos_sim.json
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
import h_tasks as HT            # noqa: E402
import g0a                      # noqa: E402  (G-0a: token kinds, head-path simulation, table helper)

OUT = HERE / "results" / "h0a"
STAY, RIGHT, LEFT, NSEP, START, CONTENT = range(6)
TOK, EOS, BOS = HT.TOK, HT.EOS, HT.BOS_ID
DIG = {TOK[str(d)]: d for d in range(10)}
N_ID, N_OOD, N_SEL, N_TRAIN, SEEDS = 1000, 500, 1000, 2000, (15, 16, 17)
T = g0a.table

FWD = {"=": RIGHT, "answer_phase": RIGHT}                    # a head on BOS steps onto the first operand at '='
TWO = {"+": NSEP, "=": RIGHT, "answer_phase": RIGHT}          # the second-operand head (as the G-0a / C1-3 tables)
TABLES = {
    "copy": T({0: FWD}),
    "prefix_sum": T({0: FWD}),
    # head 0 follows the input to s_{n-1}, then walks left; it reads BOS at the <eos> step (no end-marker head)
    "reverse": T({0: {"digit": RIGHT, "answer_phase": LEFT}}),
    "xor": T({0: FWD, 1: TWO}),
    "addition": T({0: FWD, 1: TWO}),
    "mul1": T({0: FWD, 1: {"+": NSEP, "=": RIGHT}}),
    # head 0 follows the input to y_{n-1} and walks left; head 1 jumps to '^', steps left onto x_{n-1} at '=' and walks
    # left; head 1 reads BOS at the <eos> step (no end-marker head)
    "rev_xor": T({0: {"digit": RIGHT, "+": RIGHT, "answer_phase": LEFT}, 1: {"+": NSEP, "=": LEFT, "answer_phase": LEFT}}),
    "parity": T({}),
}
CONTROLLERS = {
    "copy": "stateless: output head 0's digit; <eos> when head 0 reads a non-digit ('=')",
    "prefix_sum": "stateless: at '=' output head 0's digit; afterwards (current token + head 0's digit) mod 10; <eos> "
                  "when head 0 reads a non-digit ('=')",
    "reverse": "stateless: <eos> when head 0 (the content head) reads BOS, otherwise output head 0's digit",
    "xor": "stateless: output head 0 xor head 1; <eos> when head 0 reads a non-digit ('^')",
    "addition": "the C1-3 hand controller (stage1/pf_search_v2_check.TableController): r1 carry, r2 a exhausted, "
                "r3 b exhausted; digit (a_k + b_k + carry) mod 10, the final carry, then <eos>",
    "mul1": "as G-0a: r1 carry 0-8, r2 a exhausted, r3 done; d = head 1's digit",
    "rev_xor": "stateless: <eos> when head 1 (the x content head) reads BOS, otherwise output head 0 xor head 1",
    "parity": "r1 = running xor of the current-token bits in the prompt (BOS and '=' are not bits); output r1 at '=', "
              "then <eos>",
}
NO_END_MARKER = {"reverse": [0], "rev_xor": [1]}        # the content head(s) whose BOS read ends the answer


def rule(task, rd, r, xi):
    a, b = rd[0], rd[1]
    isd = lambda q: q in DIG                                   # noqa: E731
    if task in ("copy", "prefix_sum", "xor", "mul1"):
        return g0a.rule(task, rd, r, xi)
    if task == "reverse":
        return EOS if a == BOS else a
    if task == "rev_xor":
        return EOS if b == BOS else TOK[str(DIG.get(a, 0) ^ DIG.get(b, 0))]
    if task == "addition":
        if not isd(a):
            r[2] = 1
        if not isd(b):
            r[3] = 1
        if r[2] and r[3]:
            o = TOK["1"] if r[1] else EOS
            r[1] = 0
            return o
        s = (0 if r[2] else DIG[a]) + (0 if r[3] else DIG[b]) + r[1]
        r[1] = s // 10
        return TOK[str(s % 10)]
    if task == "parity":
        return TOK[str(r[1])] if xi == TOK["="] else EOS
    raise KeyError(task)


class Controller(g0a.Controller):
    def update(self, x, regs, reads):
        reg = regs.argmax(-1).tolist()
        rd = reads.argmax(-1).tolist()
        newr, outs = [], []
        for b in range(x.shape[0]):
            xi, r = int(x[b]), list(reg[b])
            o = EOS
            if self.task == "parity" and r[0] == 0 and xi in DIG:
                r[1] ^= DIG[xi]
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
        import pf as PFM
        ctl = Controller(self.task, TABLES[self.task], g0a.classes(tokens), self.pf.V, self.pf.K)
        return PFM.PF.forward(self.pf, tokens, controller=ctl)


def env(files):
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--"] + files, cwd=ROOT).strip())
    except Exception:
        commit, dirty = None, None
    cpu = "?"
    try:
        cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    except Exception:
        pass
    return {"code_commit": commit, "code_dirty": dirty, "torch": torch.__version__, "python": platform.python_version(),
            "cpu": cpu, "cores": os.cpu_count(), "threads": torch.get_num_threads()}


def trace(pf, task, ex):
    p, a = ex
    s = p + a
    with torch.no_grad():
        pred = HandModel(pf, task)(torch.tensor([s])).argmax(-1)[0].tolist()
    path = g0a.head_path(s, TABLES[task])
    V = HT.VOCAB
    return {"tokens": " ".join(V[i] for i in p) + " | " + " ".join(V[i] for i in a),
            "answer_steps": [{"step": t, "x_t": V[s[t]], "heads": path[t], "reads": [V[s[q]] for q in path[t]],
                              "output": V[pred[t]], "target": V[s[t + 1]]} for t in range(len(p) - 1, len(s) - 1)]}


def end_reads(task, exs):
    """per head: the share of examples in which it reads BOS at the <eos> step, and at any earlier answer step"""
    at_eos, before = [0, 0, 0], [0, 0, 0]
    for p, a in exs:
        s = p + a
        path = g0a.head_path(s, TABLES[task])
        last = len(s) - 2                                       # the step whose target is <eos>
        for j in range(3):
            at_eos[j] += s[path[last][j]] == BOS
            before[j] += any(s[path[t][j]] == BOS for t in range(len(p) - 1, last))
    return {"head%d" % j: {"reads_bos_at_eos_step": at_eos[j] / len(exs),
                           "reads_bos_at_an_earlier_answer_step": before[j] / len(exs)} for j in range(3)}


def cmd_bos():
    import pf as PFM
    import models as M
    import run as R
    torch.set_num_threads(1)
    out = OUT / "bos"
    out.mkdir(parents=True, exist_ok=True)
    cfg = dict(M.SCALES["pf"]["1M"])
    torch.manual_seed(0)
    pf = PFM.PF(len(HT.VOCAB), sep_ids=g0a.SEP_IDS, **cfg)          # its learned g and f are never used here
    pf.eval()
    tasks = list(HT.SUITE) + list(HT.STAGE1)
    (out / "config.json").write_text(json.dumps({
        "design": "stage2/DESIGN.md 9.1, 9.4-1 (H-0a item 1)", "tasks": tasks, "vocab_size": len(HT.VOCAB),
        "bos": {"token": HT.BOS, "id": BOS, "kind": "other (stage1/pf.py token_classes class 6)",
                "pf_separator": False, "start_move_destination": "position 0 = BOS"},
        "spec": {t: HT.SPEC[t] for t in tasks}, "pf_cfg": cfg, "pf_separators": [HT.VOCAB[i] for i in g0a.SEP_IDS],
        "sets": {"eval": "h_tasks.eval_sets(task, %d, %d)" % (N_ID, N_OOD), "select": "h_tasks.selection_set(task, %d)"
                 % N_SEL, "train": "h_tasks.train_set(task, %d, seed) for seeds %s" % (N_TRAIN, list(SEEDS))},
        "criterion": "representable iff the hand table + hand controller scores 1.000 (stage-1 teacher-forced sequence "
                     "exact match) on the in-distribution bin and every out-of-distribution bin",
        "no_end_marker": "reverse and rev_xor: <eos> exactly when the content head reads BOS (heads %s)" % NO_END_MARKER},
        indent=1))
    res = {}
    for task in tasks:
        t0 = time.time()
        sets = dict(HT.eval_sets(task, N_ID, N_OOD))
        sets["select"] = HT.selection_set(task, N_SEL)
        for s in SEEDS:
            sets["train_s%d_first%d" % (s, N_TRAIN)] = HT.train_set(task, N_TRAIN, s)
        assert all(e[0][0] == BOS and BOS not in e[0][1:] for v in sets.values() for e in v)
        model = HandModel(pf, task)
        with torch.no_grad():
            acc = {lab: R.exact_match(model, exs, "pf_search", cfg)[0] for lab, exs in sets.items()}
        bins = [l for l in sets if l.startswith(("id_", "ood_"))]
        r = {"accuracy": acc, "n": {l: len(e) for l, e in sets.items()},
             "exact_on_all_bins": all(acc[l] == 1.0 for l in bins),
             "exact_on_all_sets": all(v == 1.0 for v in acc.values()),
             "example": {l: " ".join(HT.VOCAB[i] for i in sets[l][0][0]) + "  ->  "
                         + " ".join(HT.VOCAB[i] for i in sets[l][0][1]) for l in bins},
             "trace": trace(pf, task, min(sets[bins[0]][:50], key=lambda e: abs(len(e[0]) - 6))),
             "wall_s": round(time.time() - t0, 1)}
        if task in NO_END_MARKER:
            r["bos_reads"] = {l: end_reads(task, sets[l]) for l in bins}
        res[task] = r
        print("%-11s %s  %ss" % (task, " ".join("%s %.3f" % (l, acc[l]) for l in acc), r["wall_s"]), flush=True)
    (out / "final.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    (out / "tables.json").write_text(json.dumps({t: {
        "table": TABLES[t], "readable": g0a.readable(TABLES[t]),
        "moving_heads": sum(any(m != STAY for m in col) for col in TABLES[t]), "controller": CONTROLLERS[t],
        "registers": "r0 = answer phase (set at '='); r1-r3 as listed", "end_marker_head": None
        if t in NO_END_MARKER else "n/a", "exact_on_all_bins": res[t]["exact_on_all_bins"]} for t in tasks}, indent=1))
    (out / "env.json").write_text(json.dumps(env(["stage2/h0a.py", "stage2/h_tasks.py", "stage2/g0a.py"]), indent=1))
    return all(r["exact_on_all_bins"] for r in res.values())


FAILED = [("g0", "g0_xor__rope__1M__s10__N100000", 10, "g0_s10"),
          ("g0p", "g0p_xor__rope__1M__s13__N100000", 13, "g0p_s13"),
          ("g0p", "g0p_xor__rope__1M__s14__N100000", 14, "g0p_s14"),
          ("g0p", "g0p_xor__rope__1M__s214__N100000", 214, "g0p_s214")]


def xor_reads(table, exs, T):
    """stage1/c1_3_table_reads.reads_share for the '^' format: at the step that outputs c_k (k < n), the share of
    (example, k) in which head j reads x_k / y_k"""
    cnt = {"x": [0, 0, 0], "y": [0, 0, 0]}
    n_all = 0
    for p, a in exs:
        n = p.index(T.TOK["^"])
        path = g0a.head_path(p + a, table)
        eq = len(p) - 1
        for k in range(n):
            n_all += 1
            for j in range(3):
                cnt["x"][j] += path[eq + k][j] == k
                cnt["y"][j] += path[eq + k][j] == n + 1 + k
    return {"head%d" % j: {"reads_x_k": cnt["x"][j] / n_all, "reads_y_k": cnt["y"][j] / n_all} for j in range(3)}


def cmd_xor():
    import g_adapter as A
    A.install()
    import tasks as T
    import models as M
    import run as R
    import c4_select as CS
    torch.set_num_threads(1)
    sel = CS.selection_set("xor")
    rows = {}
    for phase, run, seed, label in FAILED:
        d = HERE / "results" / phase / run
        row = {"run": str(d.relative_to(ROOT)), "run_seed": seed}
        ckp = d / "teacher_best.pt"
        if not ckp.exists():
            rows[label] = dict(row, checkpoint="없음")
            continue
        ck = torch.load(ckp, weights_only=False)
        fin = json.loads((d / "final.json").read_text())
        assert ck["step"] == fin["judgment"]["step"]
        cfg = ck["cfg"]
        m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], cfg)
        m.load_state_dict(ck["model"])
        m.eval()
        ok_tok = ok_bit = n_tok = n_bit = ok_seq = 0
        with torch.no_grad():
            for i in range(0, len(sel), 128):
                x, y = R.make_batch(sel[i:i + 128])
                pred = m(x).argmax(-1)
                msk = y != -100
                bit = msk & (y != T.EOS)
                hit = pred == y
                ok_tok += int((hit & msk).sum())
                n_tok += int(msk.sum())
                ok_bit += int((hit & bit).sum())
                n_bit += int(bit.sum())
                ok_seq += int((hit | ~msk).all(1).sum())
        row.update({"checkpoint": str(ckp.relative_to(ROOT)), "judgment_step": ck["step"], "run_steps": fin["steps"],
                    "selection_set": {"generation_seed": "select:xor", "size": len(sel)},
                    "token_accuracy_answer_and_eos": ok_tok / n_tok, "token_accuracy_answer_bits": ok_bit / n_bit,
                    "sequence_accuracy": ok_seq / len(sel), "answer_tokens": n_tok, "answer_bits": n_bit})
        cr_p = HERE / "results" / "h0a" / "xor_failed" / ("%s_compile" % label) / "compile_result.json"
        if not cr_p.exists():
            row["compile"] = "없음 (compile not run)"
        else:
            cr = json.loads(cr_p.read_text())
            row["precheck"] = {"ratio": cr["precheck"]["dependency"]["ratio"],
                               "correct": cr["precheck"]["dependency"]["correct"],
                               "all_stay": cr["precheck"]["dependency"]["all_stay"], "passed": cr["precheck"]["passed"]}
            row["compile_data_seed"] = cr["data_seed"]
            if "policy" in cr:
                tr = xor_reads(cr["policy"], sel, T)
                row["compiled"] = {"policy": cr["policy"], "policy_named": cr["policy_named"], "table_reads": tr,
                                   "reads_x_k_max": max(v["reads_x_k"] for v in tr.values()),
                                   "reads_y_k_max": max(v["reads_y_k"] for v in tr.values())}
                row["compiled"]["aligned"] = row["compiled"]["reads_x_k_max"] == 1.0 and row["compiled"]["reads_y_k_max"] == 1.0
            else:
                row["compiled"] = "없음 (pre-check gate: no table)"
        rows[label] = row
        print(label, json.dumps({k: row.get(k) for k in ("judgment_step", "token_accuracy_answer_and_eos",
                                                         "token_accuracy_answer_bits", "sequence_accuracy")}), flush=True)
    ref = xor_reads(g0a.TABLES["xor"], sel, T)
    out = {"design": "stage2/DESIGN.md 9.4-2 (H-0a item 2)", "teachers": rows, "correct_table_reads_reference": ref,
           "env": env(["stage2/h0a.py"])}
    p = OUT / "xor_failed" / "diagnosis.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False))


SIM_TABLES = [("g0", 10), ("g0", 11), ("g0p", 12), ("g0p", 13), ("g0p", 14)]


def cmd_sim():
    torch.set_num_threads(1)
    sets = dict(HT.eval_sets("reverse", N_ID, N_OOD))
    sets["select"] = HT.selection_set("reverse", N_SEL)
    res = {"design": "stage2/DESIGN.md 9.8-1 (H-0a item 3)", "inputs": "h_tasks reverse sets with BOS (eval %d / %d, "
           "select %d)" % (N_ID, N_OOD, N_SEL), "tables": {}}
    for phase, s in SIM_TABLES:
        cr = json.loads((HERE / "results" / phase / ("reverse_compile_s%d" % s) / "compile_result.json").read_text())
        tab = cr["policy"]
        per = {}
        for lab, exs in sets.items():
            src, eos, nk = [0, 0, 0], [0, 0, 0], 0
            for p, a in exs:
                q = p + a
                n = len(p) - 2                                  # BOS x_1 .. x_n =
                path = g0a.head_path(q, tab)
                eq = len(p) - 1
                for k in range(1, n + 1):                       # answer step k outputs x_{n-k+1} (position n-k+1)
                    nk += 1
                    for j in range(3):
                        src[j] += path[eq + k - 1][j] == n - k + 1
                for j in range(3):
                    eos[j] += q[path[eq + n][j]] == BOS          # the step whose target is <eos>
            per[lab] = {"head%d" % j: {"reads_x_(n-k+1)_at_step_k": src[j] / nk, "reads_bos_at_eos_step": eos[j] / len(exs)}
                        for j in range(3)}
        content = max(range(3), key=lambda j: per["select"]["head%d" % j]["reads_x_(n-k+1)_at_step_k"])
        res["tables"]["%s_s%d" % (phase, s)] = {
            "policy": tab, "policy_named": cr["policy_named"], "content_head": content, "per_bin": per,
            "content_head_all_1": all(per[l]["head%d" % content]["reads_x_(n-k+1)_at_step_k"] == 1.0
                                      and per[l]["head%d" % content]["reads_bos_at_eos_step"] == 1.0 for l in per)}
        print("%s_s%d content head %d:" % (phase, s, content),
              " ".join("%s %.3f/%.3f" % (l, per[l]["head%d" % content]["reads_x_(n-k+1)_at_step_k"],
                                         per[l]["head%d" % content]["reads_bos_at_eos_step"]) for l in per), flush=True)
    res["env"] = env(["stage2/h0a.py", "stage2/h_tasks.py", "stage2/g0a.py"])
    (OUT / "reverse_bos_sim.json").write_text(json.dumps(res, indent=1))
    return all(t["content_head_all_1"] for t in res["tables"].values())


if __name__ == "__main__":
    cmd = sys.argv[1]
    ok = {"bos": cmd_bos, "xor": cmd_xor, "sim": cmd_sim}[cmd]()
    if ok is not None:
        print("all 1.000:", ok)
