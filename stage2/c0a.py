"""C-0a carrier gate, O arm (stage2/DESIGN.md 11.2-11.4, 11.7, 11.8; 11.8 and 11.7 take precedence).

Student ("coupled"): the stage-1 1M decoder-only transformer shape (models.SCALES["abacus"]["1M"]: d 128, 4 heads,
4 pre-LN layers, NoPE attention, models.Block), token embedding + head-path coupling embeddings; everything else is
stage1/run.py (data, N = 100,000, batch 64, AdamW, lr 1e-3, warm-up + cosine over 20,000 steps, early stop at
in-distribution >= 0.99 twice, exact-match evaluation, FLOPs formula of the transformer).

Head-path coupling (11.7 channels, 11.8 key IDs), from a move table (O arm: the hand tables -- G-0a for addition,
copy, mul1, prefix_sum; H-0a BOS table for reverse) and the stage-1 PF move code (pf.candidates, pf.token_classes, with
the adapter's operators as separators and "+" kind):
  - per example, P = prompt length (through the first '='); the head paths are simulated on the prompt followed by
    P + 2 content-free answer-phase steps (a non-separator token after '=', so of the answer-phase kind);
  - key ID_h^K(i) = the order (1, 2, ...) in which head h's extended path first visits position i, counted over the
    whole extended path, written for the positions of the actual sequence only (0 if never visited);
  - query ID_h^Q(t) = ID_h^K(p_h(t)) at the scored steps t (the logit at t predicts an answer token or <eos>: from the
    '=' step to the step before <eos>), 0 elsewhere; p_h(t) = the extended path's position after the move at t (the
    position the PF head reads at step t);
  - separate embedding tables (256 entries each) for the key and query channel of each head (3 heads x 2 = 6 tables,
    index 0 = "none" has its own learned row as in the Abacus embedding); all added to the token embedding;
  - random offset (training only): per sequence and head one integer 0..100 added to every non-zero key and query ID
    of that head; 0 at test.  IDs + offset must stay < 256 (asserted).
The IDs are computed inside the model from the token tensor (a deterministic function of the prompt and the position);
their computation is an index cost and, as the Abacus index, not counted in the FLOPs.

stage1/run.py is executed from its own source with two textual changes (asserted to apply once each; the file is not
edited): "coupled" is added to the --kind choices, and to the kinds whose FLOPs use cfg["layers"] (the abacus / rope
transformer formula).  models.build / models.SCALES get the "coupled" kind at run time (cfg: the abacus 1M shape + the
move table, recorded in config.json).  run.py's Abacus offsets are not drawn for this kind; the model draws its own
offsets from the torch generator while training.

  python stage2/c0a.py check --task addition  # pre-training checks (a) invariance, (c) query = key of the read position
                                             # on this code, and the IDs against an independent implementation
  python stage2/c0a.py time                  # time estimate
  python stage2/c0a.py train --task addition # one run (seed 21)
  python stage2/c0a.py report
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

OUT = pathlib.Path(os.environ.get("C0A_OUT", HERE / "results" / "c0a"))    # C0A_OUT / C0A_MAX_STEPS: smoke only
SEED = 21
TASKS = ("addition", "copy", "mul1", "prefix_sum", "reverse")
ADAPTER = {"addition": None, "copy": "g_adapter", "mul1": "g_adapter", "prefix_sum": "g_adapter",
           "reverse": "h_adapter"}
ID_MAX, OFF_MAX, H = 256, 100, 3
CONTENT_MOVE = 5


def install(task):
    if ADAPTER[task]:
        __import__(ADAPTER[task]).install()


def hand_table(task):
    import g0a
    import h0a
    if task == "addition":
        return [list(r) for r in g0a.ADDITION_HAND]
    if task == "reverse":
        return [list(r) for r in h0a.TABLES["reverse"]]
    return [list(r) for r in g0a.TABLES[task]]


# ---------------------------------------------------------------- coupling IDs
def coupling_ids(tokens, table):
    """key IDs K [B, H, T] and query IDs Q [B, H, T] (no offset) of a padded batch (prompt + answer + <eos> + pad)"""
    import tasks as T
    import pf as PFM
    B, Tn = tokens.shape
    dev = tokens.device
    eq, eos = T.TOK["="], T.EOS
    has_eq = (tokens == eq).any(1)
    assert bool(has_eq.all()), "every sequence needs '='"
    P = (tokens == eq).float().argmax(1) + 1                                     # prompt length per row
    n = torch.where((tokens == eos).any(1), (tokens == eos).float().argmax(1) + 1, torch.full_like(P, Tn))
    L = int((2 * P + 2).max())
    fill = T.TOK["0"]                                                            # content-free: only its kind is used
    pos = torch.arange(L, device=dev)
    tape = torch.full((B, L), fill, dtype=tokens.dtype, device=dev)
    m = min(L, Tn)
    tape[:, :m] = torch.where(pos[None, :m] < P[:, None], tokens[:, :m], tape[:, :m])
    dig = torch.tensor([T.TOK[d] for d in T.DIGITS], device=dev)
    cls = PFM.token_classes(tape, dig, T.TOK["+"], eq, T.TOK["|"], T.TOK[T.NODES[0]], T.TOK[T.NODES[-1]] + 1)
    issep = torch.isin(tape, torch.tensor([T.TOK["+"], eq, T.TOK["|"]], device=dev))
    tab = torch.tensor(table, device=dev)
    assert not bool((tab == CONTENT_MOVE).any()), "content moves would read the virtual tokens"
    h = torch.zeros(B, H, dtype=torch.long, device=dev)
    K = torch.zeros(B, H, L + 1, dtype=torch.long, device=dev)
    cnt = torch.zeros(B, H, dtype=torch.long, device=dev)
    paths = torch.zeros(B, H, L, dtype=torch.long, device=dev)
    last = 2 * P + 1                                                             # last step of the extended path
    ar = torch.arange(B, device=dev)
    for t in range(L):
        cand = PFM.candidates(tape, t, h, tape[:, t], issep)                     # [B, H, 6]
        mv = tab[:, cls[:, t]].T                                                 # [B, H]
        h = cand.gather(2, mv[:, :, None])[:, :, 0]
        paths[:, :, t] = h
        act = (t <= last)[:, None]                                               # [B, 1]
        new = act & (K.gather(2, h[:, :, None])[:, :, 0] == 0)
        cnt = cnt + new.long()
        K.scatter_(2, h[:, :, None], torch.where(new, cnt, K.gather(2, h[:, :, None])[:, :, 0])[:, :, None])
    K = K[:, :, :Tn] if L >= Tn else torch.cat([K[:, :, :L], torch.zeros(B, H, Tn - L, dtype=torch.long,
                                                                          device=dev)], 2)
    K = torch.where(pos_lt(Tn, n, dev)[:, None, :], K, torch.zeros_like(K))     # actual positions only
    # scored steps: P-1 .. n-2
    tt = torch.arange(Tn, device=dev)
    scored = (tt[None, :] >= (P - 1)[:, None]) & (tt[None, :] <= (n - 2)[:, None])
    pth = paths[:, :, :Tn] if L >= Tn else torch.cat([paths, paths[:, :, -1:].expand(B, H, Tn - L)], 2)
    Q = K.gather(2, pth.clamp(max=Tn - 1))
    Q = torch.where(scored[:, None, :], Q, torch.zeros_like(Q))
    return K, Q, pth, scored


def pos_lt(Tn, n, dev):
    return torch.arange(Tn, device=dev)[None, :] < n[:, None]


class CoupledLM(nn.Module):
    def __init__(self, vocab, d, heads, layers, table, **_):
        super().__init__()
        import models as M
        self.kind = "coupled"
        self.table = [list(r) for r in table]
        self.tok = nn.Embedding(vocab, d)
        self.key = nn.ModuleList([nn.Embedding(ID_MAX, d) for _ in range(H)])
        self.qry = nn.ModuleList([nn.Embedding(ID_MAX, d) for _ in range(H)])
        for e in list(self.key) + list(self.qry):
            nn.init.normal_(e.weight, std=0.02)
        self.blocks = nn.ModuleList([M.Block(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)

    def forward(self, tokens, offset=None, recur=None):
        K, Q, _, _ = coupling_ids(tokens, self.table)
        if self.training:                                                        # one offset per sequence and head
            off = torch.randint(0, OFF_MAX + 1, (tokens.shape[0], H, 1), device=tokens.device)
            K = torch.where(K > 0, K + off, K)
            Q = torch.where(Q > 0, Q + off, Q)
        assert int(K.max()) < ID_MAX and int(Q.max()) < ID_MAX, "coupling ID beyond the table"
        x = self.tok(tokens)
        for j in range(H):
            x = x + self.key[j](K[:, j]) + self.qry[j](Q[:, j])
        for b in self.blocks:
            x = b(x)
        return self.head(self.ln(x))


def register(table):
    import models as M
    M.SCALES["coupled"] = {"1M": dict(M.SCALES["abacus"]["1M"], table=table)}
    inner = M.build

    def build(kind, vocab, digit_ids, cfg):
        if kind == "coupled":
            return CoupledLM(vocab, **cfg)
        return inner(kind, vocab, digit_ids, cfg)
    M.build = build


# ---------------------------------------------------------------- checks
def keys_reference(s, P, table, g0a):
    """independent implementation: g0a.head_path on the prompt + P + 2 answer-phase tokens; first-visit order over the
    whole extended path, written for positions < len(s)"""
    import tasks as T
    ext = s[:P] + [T.TOK["0"]] * (P + 2)
    path = g0a.head_path(ext, table)
    k = [[0] * len(s) for _ in range(H)]
    seen = [set() for _ in range(H)]
    cnt = [0] * H
    for st in path:
        for j in range(H):
            i = st[j]
            if i not in seen[j]:
                seen[j].add(i)
                cnt[j] += 1
                if i < len(s):
                    k[j][i] = cnt[j]
    return k, path


def sets(task, n_id, n_ood):
    import tasks as T
    return T.eval_sets(task, n_id, n_ood)


def cmd_check(a):
    """one task per process (adapters); writes pretraining_check_<task>.json"""
    task = a.task
    install(task)
    import tasks as T
    import run as R
    import g0a
    import h0a
    table = hand_table(task)
    rng = random.Random("c0a:invariance:%s" % task)
    res = {}
    evs = sets(task, a.n, a.n)
    evs["train_s21_first%d" % a.n] = T.train_set(task, 100000, SEED)[:a.n]
    for lab, ex in evs.items():
        inv_ok = q_ok = q_n = ref_ok = 0
        maxid = 0
        for i in range(0, len(ex), 64):
            chunk = ex[i:i + 64]
            x, y = R.make_batch(chunk)
            K, Q, pth, scored = coupling_ids(x, table)
            assert bool((scored == (y != -100)).all()), "scored steps differ from run.py's targets"
            maxid = max(maxid, int(K.max()))
            # (c) on this code: at every scored step with a non-zero query ID, it equals the key ID of the position
            # read, the read position from the independent PF path (g0a.head_path on the actual tokens); and the key
            # IDs equal an independent implementation of the 11.8 definition (g0a.head_path on the extended prompt)
            for b, (p, ans) in enumerate(chunk):
                s = p + ans
                path = g0a.head_path(s, table)
                kr, _ = keys_reference(s, len(p), table, g0a)
                ref_ok += K[b, :, :len(s)].tolist() == kr
                for t in range(len(p) - 1, len(s) - 1):
                    for j in range(H):
                        qv = int(Q[b, j, t])
                        if qv:
                            q_n += 1
                            q_ok += qv == int(K[b, j, path[t][j]])
            # (a) invariance: a random answer of random length 0 .. P + 1 (random digits + <eos>)
            alt = []
            for p, ans in chunk:
                La = rng.randint(0, len(p) + 1)
                alt.append((p, [T.TOK[rng.choice(T.DIGITS)] for _ in range(La)] + [T.EOS]))
            x2, _ = R.make_batch(alt)
            K2, Q2, _, _ = coupling_ids(x2, table)
            for b, ((p, ans), (_, a2)) in enumerate(zip(chunk, alt)):
                c = min(len(p) + len(ans), len(p) + len(a2))
                same = (bool((K[b, :, :c] == K2[b, :, :c]).all())                 # prompt + common answer positions
                        and bool((Q[b, :, :c - 1] == Q2[b, :, :c - 1]).all()))     # common scored steps
                inv_ok += same
        res[lab] = {"examples": len(ex), "invariance": inv_ok / len(ex),
                    "query_equals_key_of_read_position": q_ok / q_n if q_n else None, "query_ids_checked": q_n,
                    "ids_equal_independent_implementation": ref_ok / len(ex), "max_key_id": maxid,
                    "max_key_id_plus_offset_below_256": maxid + OFF_MAX < ID_MAX}
        print(task, lab, json.dumps(res[lab]), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("pretraining_check_%s.json" % task)).write_text(json.dumps(
        {"design": "stage2/DESIGN.md 11.7, 11.8 checks (a) invariance and (c) query = key of the read position, on the "
                   "student code (stage2/c0a.py coupling_ids)", "task": task, "table": table, "results": res,
         "all_1.000": all(v["invariance"] == 1.0 and v["query_equals_key_of_read_position"] == 1.0
                          and v["ids_equal_independent_implementation"] == 1.0 and v["max_key_id_plus_offset_below_256"]
                          for v in res.values()),
         "env": h0a.env(["stage2/c0a.py"])}, indent=1))


# ---------------------------------------------------------------- training
PATCHES = [
    ('"pf_search"), required=True)', '"pf_search", "coupled"), required=True)'),
    ('if kind in ("abacus", "rope") else', 'if kind in ("abacus", "rope", "coupled") else'),
]


def cmd_train(a):
    install(a.task)
    register(hand_table(a.task))
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", "coupled", "--scale", "1M", "--seed", str(SEED), "--N", "100000",
            "--max-steps", os.environ.get("C0A_MAX_STEPS", "20000"), "--phase", "c0a", "--out-root", str(OUT),
            "--threads", "1", "--tag", "oracle"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


def run_dir(task):
    return OUT / ("c0a_%s__coupled__1M__s%d__N100000__oracle" % (task, SEED))


def cmd_time(a):
    """per task: seconds per step (train + eval) measured on a short smoke run (results passed in --smoke-json)"""
    sm = json.loads(pathlib.Path(a.smoke_json).read_text())
    per, cpu = {}, 0.0
    for t, sps in sm.items():
        per[t] = {"s_per_step": sps, "worst_20000_h": sps * 20000 / 3600}
        cpu += sps * 20000
    longest = max(v["worst_20000_h"] for v in per.values())
    res = {"per_task": per, "cpu_hours_worst": cpu / 3600,
           "wall_hours_worst_4_workers_plus_longest": cpu / 3600 / 4 + longest, "limit_hours": 48,
           "note": "worst case: every run 20,000 steps (no early stop); s/step from smoke runs of this code"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "time_estimate.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def cmd_report(a):
    rows, ok = [], 0
    for t in TASKS:
        f = json.loads((run_dir(t) / "final.json").read_text())
        acc = f["judgment"]["acc"]
        labs = list(acc)
        o1, o2 = acc[labs[1]], acc[labs[2]]
        win = o1 >= 0.90 and o2 >= 0.90
        ok += win
        rows.append({"task": t, "judgment_step": f["judgment"]["step"], "acc": acc, "last_acc": f["last"]["acc"],
                     "steps": f["steps"], "stopped": f["stopped"], "judgment_flops": f["judgment"]["train_flops_cum"],
                     "train_flops": f["train_flops"], "wall_train_s": f["wall_train_s"], "wall_eval_s": f["wall_eval_s"],
                     "ood_first_two_ge_0.90": win})
    out = {"design": "stage2/DESIGN.md 11.4 (pass: >= 4 of 5 tasks with OOD bins 1 and 2 >= 0.90)", "tasks": rows,
           "tasks_meeting": ok, "pass": ok >= 4}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1))
    print("| 과제 | 판정 step (멈춤) | 분포 안 · 분포 밖 1 · 2 · 3 | 마지막 체크포인트 | 판정 시점 FLOPs | 학습 FLOPs | 시간 (학습 + 평가) | 밖 1·2 ≥0.90 |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| %s | %d (%d, %s) | %s | %s | %.2e | %.2e | %.0f s | %s |" % (
            r["task"], r["judgment_step"], r["steps"], r["stopped"], " · ".join("%.3f" % v for v in r["acc"].values()),
            " · ".join("%.3f" % v for v in r["last_acc"].values()), r["judgment_flops"], r["train_flops"],
            r["wall_train_s"] + r["wall_eval_s"], "예" if r["ood_first_two_ge_0.90"] else "아니오"))
    print("tasks meeting: %d of 5 -> pass %s" % (ok, ok >= 4))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("check")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--n", type=int, default=200)
    q = sp.add_parser("time")
    q.add_argument("--smoke-json", required=True)
    q = sp.add_parser("train")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--resume", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"check": cmd_check, "time": cmd_time, "train": cmd_train, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
