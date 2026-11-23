"""C-1a gate (stage2/DESIGN.md 11.13, 11.14): a standard transformer with hard reads.  O arm (hand tables: G-0a for
addition, copy, mul1, prefix_sum; H-0a BOS table for reverse), student seed 21.

Student input at position t (11.13):  u_t = E(x_t) + sum_h R_h(E(x[p_h(t)]))   over the MOVING heads h of the table
                                      in_t = u_t + S(u_{t-1})                   (S(u_{-1}) = 0)
  p_h(t): the head position after the move at step t, by the stage-1 PF move code (pf.candidates, pf.token_classes with
  the adapter's operators as "+" kind and separators) on the actual tokens; p_h(t) <= t (causal).  E is the token
  embedding, R_h and S learned linear maps (d x d, no bias).
Arms:
  C-1a (kind "hardread")      body: 4 pre-LN NoPE transformer layers (models.Block), d 128, 4 heads; no coupling IDs
  M    (kind "hardread_mlp")  diagnostic, not a verdict (11.14-2): the same input, 4 pre-LN MLP blocks (x + MLP(LN x),
                              MLP 128 -> 512 -> 128), no attention
Training: stage1/run.py executed from its source with textual changes (asserted once each; the file is not edited):
the two kinds in --kind, in config.json's position description, and a FLOPs branch: the stage-1 transformer formula
(attention + 24 d^2 per token and layer + head) or, for M, 16 d^2 per token and layer + head; both plus the hard-read
maps (2 d^2 per token for each R_h and for S).  --keep-best keeps the judgment checkpoint.

  check --task T   pre-training checks (all must be 1.000): (a) the student's read positions equal the hand-table
                   head path of stage2/g0a.head_path (independent implementation); (b) p_h(t) <= t; (c) invariance: a
                   random answer of random length (0 .. prompt length + 1) leaves the read positions of the common steps
                   unchanged; (d) local determinism and coverage (11.14-1): key = (x_t, x[p_h(t)] for the moving heads,
                   x_{t-1}, x[p_h(t-1)]) -> next token, built from the training data (seed 21, 100,000): conflicts = 0,
                   every scored-step key of the in-distribution and each out-of-distribution evaluation set present in
                   the table, and the table's exact match 1.000 on every set
  train --task T --arm {C,M}
  diag  --task T --arm {C,M}   in-distribution exact match with the hard reads and the shift removed (R_h and S terms 0)
  report
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402
import torch.nn as nn            # noqa: E402
import c0a                       # noqa: E402

OUT = pathlib.Path(os.environ.get("C1A_OUT", HERE / "results" / "c1a"))
SEED = 21
TASKS = c0a.TASKS
ARMS = {"C": "hardread", "M": "hardread_mlp"}
H = 3


def moving(table):
    return [j for j in range(H) if any(m != 0 for m in table[j])]


def read_paths(tokens, table):
    """head positions after the move at every step [B, H, T], on the actual tokens (PF move code, batched)"""
    import tasks as T
    import pf as PFM
    B, Tn = tokens.shape
    dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
    cls = PFM.token_classes(tokens, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]], T.TOK[T.NODES[-1]] + 1)
    issep = torch.isin(tokens, torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]]))
    tab = torch.tensor(table)
    h = torch.zeros(B, H, dtype=torch.long)
    out = torch.zeros(B, H, Tn, dtype=torch.long)
    for t in range(Tn):
        cand = PFM.candidates(tokens, t, h, tokens[:, t], issep)
        h = cand.gather(2, tab[:, cls[:, t]].T[:, :, None])[:, :, 0]
        out[:, :, t] = h
    return out


class HardReadLM(nn.Module):
    def __init__(self, vocab, d, heads, layers, table, mlp_only=False, **_):
        super().__init__()
        import models as M
        self.kind = "hardread_mlp" if mlp_only else "hardread"
        self.table = [list(r) for r in table]
        self.moving = moving(self.table)
        self.tok = nn.Embedding(vocab, d)
        self.R = nn.ModuleList([nn.Linear(d, d, bias=False) for _ in self.moving])
        self.S = nn.Linear(d, d, bias=False)
        if mlp_only:
            self.blocks = nn.ModuleList([MLPBlock(d) for _ in range(layers)])
        else:
            self.blocks = nn.ModuleList([M.Block(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.ablate = False

    def inputs(self, tokens):
        e = self.tok(tokens)
        if self.ablate:
            return e
        P = read_paths(tokens, self.table)
        u = e
        for r, j in zip(self.R, self.moving):
            u = u + r(e.gather(1, P[:, j, :, None].expand(-1, -1, e.shape[-1])))
        sh = torch.zeros_like(u)
        sh[:, 1:] = self.S(u[:, :-1])
        return u + sh

    def forward(self, tokens, offset=None, recur=None):
        x = self.inputs(tokens)
        for b in self.blocks:
            x = b(x)
        return self.head(self.ln(x))


class MLPBlock(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.ln = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, x):
        return x + self.mlp(self.ln(x))


def fwd_flops(kind, cfg, B, Tlen, V):
    d, L = cfg["d"], cfg["layers"]
    nr = len(moving(cfg["table"])) + 1                                   # R_h for the moving heads, and S
    reads = B * Tlen * 2 * d * d * nr
    if kind == "hardread":
        return B * Tlen * (2 * 12 * d * d * L + 2 * d * V) + 4 * B * Tlen * Tlen * d * L + reads
    return B * Tlen * (2 * 8 * d * d * L + 2 * d * V) + reads


def register(table, arm):
    import models as M
    for k in ARMS.values():
        M.SCALES[k] = {"1M": dict(M.SCALES["abacus"]["1M"], table=table)}
    inner = M.build

    def build(kind, vocab, digit_ids, cfg):
        if kind in ARMS.values():
            return HardReadLM(vocab, mlp_only=(kind == "hardread_mlp"), **cfg)
        return inner(kind, vocab, digit_ids, cfg)
    M.build = build


PATCHES = [
    ('"pf_search"), required=True)', '"pf_search", "hardread", "hardread_mlp"), required=True)'),
    ('def fwd_flops(kind, cfg, B, Tlen, V, recur=None):\n',
     'def fwd_flops(kind, cfg, B, Tlen, V, recur=None):\n'
     '    if kind in ("hardread", "hardread_mlp"):                # C-1a (stage2/c1a.py)\n'
     '        import c1a\n'
     '        return c1a.fwd_flops(kind, cfg, B, Tlen, V)\n'),
    ('"pf_cont": "none (soft head distributions over the tape; recurrence over steps)"}[a.kind]',
     '"pf_cont": "none (soft head distributions over the tape; recurrence over steps)",\n'
     '                         "hardread": "NoPE attention; input + hard reads E(x[p_h(t)]) of the hand-table head '
     'paths (R_h) + token shift S (stage2/c1a.py, DESIGN 11.13)",\n'
     '                         "hardread_mlp": "no attention (MLP blocks); input + hard reads + token shift '
     '(stage2/c1a.py, DESIGN 11.14 arm M)"}[a.kind]'),
]


def run_dir(task, arm):
    return OUT / ("c1a_%s__%s__1M__s%d__N100000__oracle" % (task, ARMS[arm], SEED))


# ---------------------------------------------------------------- checks
def cmd_check(a):
    c0a.install(a.task)
    import tasks as T
    import run as R
    import g0a
    import h0a
    table = c0a.hand_table(a.task)
    mv = moving(table)
    rng = random.Random("c1a:invariance:%s" % a.task)
    torch.set_num_threads(1)

    def keys(x, y, P):
        """scored-step keys [(key, next token)] of a batch"""
        out = []
        for b in range(x.shape[0]):
            for t in (y[b] != -100).nonzero()[:, 0].tolist():
                k = (int(x[b, t]),) + tuple(int(x[b, P[b, j, t]]) for j in mv)
                k += (int(x[b, t - 1]),) + tuple(int(x[b, P[b, j, t - 1]]) for j in mv) if t > 0 else (-1,) * (1 + len(mv))
                out.append((b, k, int(y[b, t])))
        return out

    # (d) table from the training data
    train = T.train_set(a.task, 100000, SEED)
    tabk, conflicts = {}, 0
    for i in range(0, len(train), 256):
        x, y = R.make_batch(train[i:i + 256])
        P = read_paths(x, table)
        for _, k, v in keys(x, y, P):
            if k in tabk and tabk[k] != v:
                conflicts += 1
            tabk.setdefault(k, v)
    evs = T.eval_sets(a.task, 1000, 500)
    evs["train_s21_first200"] = train[:200]
    res = {"moving_heads": mv, "train_examples": len(train), "table_keys": len(tabk), "conflicts": conflicts, "sets": {}}
    for lab, ex in evs.items():
        same = caus = inv = 0
        n_keys = covered = 0
        ok_ex = 0
        for i in range(0, len(ex), 128):
            chunk = ex[i:i + 128]
            x, y = R.make_batch(chunk)
            P = read_paths(x, table)
            # (a) against g0a.head_path, (b) causality
            for b, (p, ans) in enumerate(chunk):
                s = p + ans
                ref = g0a.head_path(s, table)
                same += all(int(P[b, j, t]) == ref[t][j] for t in range(len(s)) for j in range(H))
                caus += bool((P[b, :, :len(s)] <= torch.arange(len(s))[None, :]).all())
            # (c) invariance
            alt = []
            for p, ans in chunk:
                La = rng.randint(0, len(p) + 1)
                alt.append((p, [T.TOK[rng.choice(T.DIGITS)] for _ in range(La)] + [T.EOS]))
            x2, _ = R.make_batch(alt)
            P2 = read_paths(x2, table)
            for b, ((p, ans), (_, a2)) in enumerate(zip(chunk, alt)):
                c = min(len(p) + len(ans), len(p) + len(a2))
                inv += bool((P[b, :, :c] == P2[b, :, :c]).all())
            # (d) coverage and table prediction
            wrong = set()
            for b, k, v in keys(x, y, P):
                n_keys += 1
                if k in tabk:
                    covered += 1
                    if tabk[k] != v:
                        wrong.add(b)
                else:
                    wrong.add(b)
            ok_ex += len(chunk) - len(wrong)
        res["sets"][lab] = {"examples": len(ex), "read_positions_equal_hand_table_path": same / len(ex),
                            "causal": caus / len(ex), "invariance": inv / len(ex),
                            "key_coverage": covered / n_keys, "table_exact_match": ok_ex / len(ex)}
        print(a.task, lab, res["sets"][lab], flush=True)
    res["all_1.000"] = conflicts == 0 and all(v == 1.0 for s in res["sets"].values() for k, v in s.items()
                                              if k != "examples")
    res["env"] = h0a.env(["stage2/c1a.py"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("pretraining_check_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print("conflicts", conflicts, "keys", len(tabk), "all 1.000:", res["all_1.000"])


# ---------------------------------------------------------------- train / diag / report
def cmd_train(a):
    c0a.install(a.task)
    register(c0a.hand_table(a.task), a.arm)
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", ARMS[a.arm], "--scale", "1M", "--seed", str(SEED), "--N", "100000",
            "--max-steps", os.environ.get("C1A_MAX_STEPS", "20000"), "--phase", "c1a", "--out-root", str(OUT),
            "--threads", "1", "--tag", "oracle", "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


def cmd_diag(a):
    c0a.install(a.task)
    register(c0a.hand_table(a.task), a.arm)
    import tasks as T
    import models as M
    import run as R
    import h0a
    torch.set_num_threads(1)
    d = run_dir(a.task, a.arm)
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    model = M.build(ARMS[a.arm], len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
    model.load_state_dict(ck["model"])
    model.eval()
    ev = T.eval_sets(a.task, 1000, 500)
    lab = list(ev)[0]
    with torch.no_grad():
        base = R.exact_match(model, ev[lab], ARMS[a.arm], ck["cfg"])[0]
        model.ablate = True
        abl = R.exact_match(model, ev[lab], ARMS[a.arm], ck["cfg"])[0]
    res = {"task": a.task, "arm": a.arm, "judgment_step": ck["step"],
           "in_distribution": {"unchanged": base, "run_judgment_acc": fin["judgment"]["acc"][lab],
                               "reads_and_shift_removed": abl, "drop": base - abl},
           "env": h0a.env(["stage2/c1a.py"])}
    (OUT / ("diag_%s_%s.json" % (a.task, a.arm))).write_text(json.dumps(res, indent=1))
    print(json.dumps(res["in_distribution"]), flush=True)


def curve(d):
    rows = [json.loads(l) for l in open(d / "log.jsonl") if l.strip() and "event" not in json.loads(l)]
    labs = list(rows[0]["acc"])
    out = {}
    for th in (0.5, 0.99):
        r = next((r for r in rows if r["acc"][labs[0]] >= th), None)
        out["id_ge_%s" % th] = None if r is None else {"step": r["step"], "ood_bin1": r["acc"][labs[1]]}
    out["ood_bin1_max"] = max(r["acc"][labs[1]] for r in rows)
    out["ood_bin2_max"] = max(r["acc"][labs[2]] for r in rows)
    out["rows"] = [{"step": r["step"], "acc": r["acc"]} for r in rows]
    return out


def cmd_report(a):
    out = {"design": "stage2/DESIGN.md 11.13 (pass, arm C only: >= 4 of 5 tasks with OOD bins 1 and 2 >= 0.90), 11.14",
           "arms": {}}
    lines = []
    for arm in ARMS:
        rows, ok = [], 0
        for t in TASKS:
            f = json.loads((run_dir(t, arm) / "final.json").read_text())
            dg = json.loads((OUT / ("diag_%s_%s.json" % (t, arm))).read_text())
            acc = f["judgment"]["acc"]
            labs = list(acc)
            win = acc[labs[1]] >= 0.90 and acc[labs[2]] >= 0.90
            ok += win
            rows.append({"task": t, "params": f["params"], "judgment_step": f["judgment"]["step"], "steps": f["steps"],
                         "stopped": f["stopped"], "acc": acc, "last_acc": f["last"]["acc"],
                         "judgment_flops": f["judgment"]["train_flops_cum"], "train_flops": f["train_flops"],
                         "wall_s": f["wall_train_s"] + f["wall_eval_s"], "ood_first_two_ge_0.90": win,
                         "reads_removed": dg["in_distribution"], "curve": curve(run_dir(t, arm))})
        out["arms"][arm] = {"kind": ARMS[arm], "tasks": rows, "tasks_meeting": ok}
        lines.append("\n### arm %s (%s): %d of 5" % (arm, ARMS[arm], ok))
        lines.append("| 과제 | 파라미터 | 판정 step (실행, 멈춤) | 분포 안 · 밖 1 · 2 · 3 | 학습 FLOPs | 시간 | 읽기 제거 하락 | 분포 안 ≥0.5 step (밖 1) | ≥0.99 step (밖 1) | 밖 1·2 ≥0.90 |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            c = r["curve"]
            fmt = lambda x: "—" if x is None else "%d (%.3f)" % (x["step"], x["ood_bin1"])   # noqa: E731
            lines.append("| %s | %d | %d (%d, %s) | %s | %.2e | %.0f s | %.3f | %s | %s | %s |" % (
                r["task"], r["params"], r["judgment_step"], r["steps"], r["stopped"][:10],
                " · ".join("%.3f" % v for v in r["acc"].values()), r["train_flops"], r["wall_s"],
                r["reads_removed"]["drop"], fmt(c["id_ge_0.5"]), fmt(c["id_ge_0.99"]),
                "예" if r["ood_first_two_ge_0.90"] else "아니오"))
    out["pass_arm_C"] = out["arms"]["C"]["tasks_meeting"] >= 4
    (OUT / "summary.json").write_text(json.dumps(out, indent=1))
    print("\n".join(lines))
    print("arm C tasks meeting: %d -> pass %s" % (out["arms"]["C"]["tasks_meeting"], out["pass_arm_C"]))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("check")
    q.add_argument("--task", choices=TASKS, required=True)
    for name in ("train", "diag"):
        q = sp.add_parser(name)
        q.add_argument("--task", choices=TASKS, required=True)
        q.add_argument("--arm", choices=tuple(ARMS), required=True)
        if name == "train":
            q.add_argument("--resume", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"check": cmd_check, "train": cmd_train, "diag": cmd_diag, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
