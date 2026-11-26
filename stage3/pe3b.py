"""3-B baseline strengthening (stage3/DESIGN.md 8.3 with 8.5): two more stage-1 baselines that change only the position
encoding of the rope baseline (same d / heads / layers / block / optimizer / data / evaluation).

  rel_rand  randomized relative position encoding (Ruoss et al. 2023, the Transformer-XL relative variant):
              score_ij = [ q_i.k_j + q_i.W_R R(pi_i - pi_j) + u.k_j + v.W_R R(pi_i - pi_j) ] / sqrt(d_head), j <= i
            R = sinusoidal encoding (dim d) of the relative distance, W_R one d x d projection per layer, u, v learned
            per head and per layer.  pi: for every sequence, len(sequence) positions drawn from {0, ..., 511} without
            replacement and sorted; len = the sequence's own length (prompt + answer + <eos>, padding excluded; padding
            positions repeat the last real position and are never scored).  Drawn in training (torch global RNG, so
            the run seed and the checkpointed RNG state fix it) and in evaluation (a generator reset to EVAL_SEED
            every time the model is put in eval mode, i.e. at the start of every evaluated bin: the draw depends only
            on the bin and its fixed example order).  Teacher-forced exact match uses one draw for the whole sequence.
  nope      no position encoding (causal mask only; Kazemnejad et al. 2023): the stage-1 NoPE block without Abacus.

No stage-1 or stage-2 file is edited: stage1/run.py is executed with the PATCHES below (kind choices, position
description, FLOPs, an --lr-mult option), through the task adapter of the format the task was judged in:
  stage3 dup / interleave / repeat / pairswap   stage3/l_adapter.py (as 3-0 C)
  copy / mul1 / prefix_sum                      stage2/g_adapter.py (as G-0 / G-0')
  reverse                                       stage2/h_adapter.py (BOS, as H-0)
  addition                                      stage 1 tasks, no adapter (as C4)

  python stage3/pe3b.py check                              implementation checks (i)-(iii) -> results/3-B/checks.json
  python stage3/pe3b.py run --task T --kind K [--lr-mult M] [--resume]
  python stage3/pe3b.py report                             baseline best (old 4 + new 2) per task -> results/3-B/summary.json
"""
from __future__ import annotations
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402
import torch.nn as nn            # noqa: E402
import torch.nn.functional as F  # noqa: E402

OUT = HERE / "results" / "3-B"
PHASE = "3b"
P_MAX = 512                      # positions {0, ..., 511}
EVAL_SEED = 1234                 # evaluation draw: generator reset at every model.eval()
KINDS = ("rel_rand", "nope")
TASKS = ("dup", "interleave", "repeat", "pairswap", "addition", "copy", "mul1", "prefix_sum", "reverse")
ADAPTER = {"dup": "l", "interleave": "l", "repeat": "l", "pairswap": "l", "copy": "g", "mul1": "g", "prefix_sum": "g",
           "reverse": "h", "addition": None}
LR_MULTS = (1.0, 0.5, 2.0)


# ---------------------------------------------------------------- models
def sinusoid(dist, d):
    """Transformer-XL relative position embedding: [sin(dist f), cos(dist f)], f = 10000^(-2i/d)"""
    inv = 1.0 / (10000 ** (torch.arange(0, d, 2, device=dist.device).float() / d))
    ang = dist.float()[..., None] * inv
    return torch.cat([ang.sin(), ang.cos()], dim=-1)


class RelBlock(nn.Module):
    """the stage-1 pre-LN block (same qkv / proj / mlp) with Transformer-XL relative attention"""

    def __init__(self, d, heads):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))
        self.heads = heads
        self.w_r = nn.Linear(d, d, bias=False)
        self.u = nn.Parameter(torch.empty(heads, d // heads))
        self.v = nn.Parameter(torch.empty(heads, d // heads))
        nn.init.normal_(self.u, std=0.02)
        nn.init.normal_(self.v, std=0.02)

    def attend(self, x, pos, naive=False):
        B, T, D = x.shape
        H, hd = self.heads, D // self.heads
        q, k, v = self.qkv(self.ln1(x)).view(B, T, 3, H, hd).permute(2, 0, 3, 1, 4)      # B H T hd
        ac = torch.einsum("bhid,bhjd->bhij", q + self.u[None, :, None, :], k)
        rel = pos[:, :, None] - pos[:, None, :]                                          # B T T: pi_i - pi_j
        causal = torch.ones(T, T, dtype=torch.bool, device=x.device).tril()
        if naive:     # reference: R and W_R evaluated for every pair (standard relative attention, no table)
            r = self.w_r(sinusoid(rel, D)).view(B, T, T, H, hd)                          # B T T H hd
            bd = torch.einsum("bhid,bijhd->bhij", q + self.v[None, :, None, :], r)
        else:         # table of W_R R(delta) for delta in 0..P_MAX-1, gathered at pi_i - pi_j (j <= i)
            table = self.w_r(sinusoid(torch.arange(P_MAX, device=x.device), D)).view(P_MAX, H, hd)
            full = torch.einsum("bhid,phd->bhip", q + self.v[None, :, None, :], table)    # B H T P
            idx = torch.where(causal, rel, torch.zeros_like(rel)).clamp(0, P_MAX - 1)
            bd = full.gather(-1, idx[:, None].expand(B, H, T, T))
        s = (ac + bd) / math.sqrt(hd)
        s = s.masked_fill(~causal, float("-inf"))
        a = torch.softmax(s, -1) @ v
        x = x + self.proj(a.transpose(1, 2).reshape(B, T, D))
        return x + self.mlp(self.ln2(x))


class RelRandLM(nn.Module):
    def __init__(self, vocab, d, heads, layers, pad=0, **_):
        super().__init__()
        self.kind = "rel_rand"
        self.pad = pad
        self.tok = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList([RelBlock(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.eval_gen = torch.Generator()
        self.eval_gen.manual_seed(EVAL_SEED)
        self.fixed_positions = False           # check (iii): pi = 0, 1, ...

    def train(self, mode=True):
        if not mode:                           # every switch to eval mode restarts the evaluation draw
            self.eval_gen.manual_seed(EVAL_SEED)
        return super().train(mode)

    def positions(self, tokens):
        B, T = tokens.shape
        if self.fixed_positions:
            return torch.arange(T)[None].expand(B, T).clone()
        lens = (tokens != self.pad).sum(1).tolist()
        pos = torch.empty(B, T, dtype=torch.long)
        for b, n in enumerate(lens):
            gen = None if self.training else self.eval_gen
            p = torch.randperm(P_MAX, generator=gen)[:n].sort().values
            pos[b, :n] = p
            pos[b, n:] = p[-1] if n else 0
        return pos

    def forward(self, tokens, offset=None, recur=None, positions=None, naive=False):
        pos = self.positions(tokens) if positions is None else positions
        x = self.tok(tokens)
        for b in self.blocks:
            x = b.attend(x, pos.to(tokens.device), naive=naive)
        return self.head(self.ln(x))


class NoPELM(nn.Module):
    """the stage-1 NoPE block (models.Block) without any position embedding"""

    def __init__(self, vocab, d, heads, layers, **_):
        super().__init__()
        import models as M
        self.kind = "nope"
        self.tok = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList([M.Block(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)

    def forward(self, tokens, offset=None, recur=None):
        x = self.tok(tokens)
        for b in self.blocks:
            x = b(x)
        return self.head(self.ln(x))


def install_models():
    import models as M
    if getattr(M, "_pe3b", False):
        return
    for k in KINDS:
        M.SCALES[k] = {s: dict(v) for s, v in M.SCALES["rope"].items()}      # same d / heads / layers as rope
    inner = M.build

    def build(kind, vocab, digit_ids, cfg):
        if kind == "rel_rand":
            import tasks as T
            return RelRandLM(vocab, pad=T.PAD, **cfg)
        if kind == "nope":
            return NoPELM(vocab, **cfg)
        return inner(kind, vocab, digit_ids, cfg)
    M.build = build
    M._pe3b = True


def rel_extra_flops(cfg, B, Tlen):
    """rel_rand beyond the rope formula, per forward: per layer the W_R table (2 P d^2), (q + v) against the table
    (2 B T P d), u added to q (B T d)"""
    d, L = cfg["d"], cfg["layers"]
    return L * (2 * P_MAX * d * d + 2 * B * Tlen * P_MAX * d + B * Tlen * d)


PATCHES = [
    ('"pf_search"), required=True)', '"pf_search", "rel_rand", "nope"), required=True)'),
    ('    L = cfg["layers"] if kind in ("abacus", "rope") else',
     '    if kind == "rel_rand":                                    # 3-B (stage3/pe3b.py)\n'
     '        import pe3b\n'
     '        return fwd_flops("rope", cfg, B, Tlen, V) + pe3b.rel_extra_flops(cfg, B, Tlen)\n'
     '    if kind == "nope":\n'
     '        return fwd_flops("rope", cfg, B, Tlen, V)\n'
     '    L = cfg["layers"] if kind in ("abacus", "rope") else'),
    ('"pf_cont": "none (soft head distributions over the tape; recurrence over steps)"}[a.kind]',
     '"pf_cont": "none (soft head distributions over the tape; recurrence over steps)",\n'
     '                         "rel_rand": "randomized relative position encoding (Ruoss et al. 2023, Transformer-XL '
     'relative attention; positions: per sequence its length drawn from 0..511 without replacement, sorted; '
     'stage3/pe3b.py)",\n'
     '                         "nope": "none: causal mask only (NoPE, stage3/pe3b.py)"}[a.kind]'),
    ('    lr = LR[a.scale]\n', '    lr = LR[a.scale] * a.lr_mult\n'),
    ('    p.add_argument("--tag", default="")\n',
     '    p.add_argument("--tag", default="")\n'
     '    p.add_argument("--lr-mult", type=float, default=1.0, help="3-B: learning rate x (stage3/pe3b.py)")\n'),
]


def install_adapter(task):
    a = ADAPTER[task]
    if a == "l":
        import l_adapter
        l_adapter.install()
    elif a == "g":
        import g_adapter
        g_adapter.install()
    elif a == "h":
        import h_adapter
        h_adapter.install()


def tag(mult):
    return "" if mult == 1.0 else "lrx%g" % mult


def run_dir(task, kind, mult=1.0):
    t = tag(mult)
    return OUT / ("%s_%s__%s__1M__s0__N100000%s" % (PHASE, task, kind, ("__" + t) if t else ""))


def cmd_run(a):
    install_adapter(a.task)
    install_models()
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", a.kind, "--scale", "1M", "--seed", "0", "--N", "100000", "--phase", PHASE,
            "--out-root", os.environ.get("PE3B_OUT", str(OUT)), "--threads", "1", "--lr-mult", str(a.lr_mult)]
    if os.environ.get("PE3B_SMOKE"):                        # smoke test only (scratch out-root): short run, FLOPs check
        argv += ["--max-steps", os.environ["PE3B_SMOKE"], "--eval-every", os.environ["PE3B_SMOKE"], "--check-flops"]
    if tag(a.lr_mult):
        argv += ["--tag", tag(a.lr_mult)]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


# ---------------------------------------------------------------- checks (8.5-1)
def cmd_check(a):
    torch.set_num_threads(1)
    import l_adapter
    l_adapter.install()
    install_models()
    import tasks as T
    import models as M
    torch.manual_seed(0)
    V = len(T.VOCAB)
    cfg = dict(M.SCALES["rel_rand"]["1M"])
    m = M.build("rel_rand", V, [T.TOK[x] for x in T.DIGITS], cfg)
    n0 = M.build("nope", V, [T.TOK[x] for x in T.DIGITS], cfg)
    import run as R
    exs = [e for t in ("interleave", "dup", "pairswap") for ex in T.eval_sets(t, 50, 50).values() for e in ex]
    res = {}
    # (i) sorted, no duplicates, in range: training and evaluation draws, every real position
    ok = tot = 0
    for mode in (True, False):
        m.train(mode)
        for j in range(0, len(exs), 64):
            x, _ = R.make_batch(exs[j:j + 64])
            pos = m.positions(x)
            for b in range(x.shape[0]):
                n = int((x[b] != T.PAD).sum())
                p = pos[b, :n]
                tot += 1
                ok += int(bool((p[1:] > p[:-1]).all()) and int(p.min()) >= 0 and int(p.max()) < P_MAX)
    m.eval()
    x, _ = R.make_batch(exs[:64])
    p1 = m.positions(x)
    m.train()
    m.eval()
    p2 = m.positions(x)
    res["i_sorted_unique_in_range"] = {"fraction": ok / tot, "sequences": tot,
                                       "eval_draw_repeats_after_eval_reset": bool(torch.equal(p1, p2))}
    # (ii) causality: tokens after t replaced (same length, same positions) -> outputs up to t unchanged
    def causal(model, kw):
        model.eval()
        ok = tot = 0
        g = torch.Generator().manual_seed(1)
        with torch.no_grad():
            for j in range(0, 300, 50):
                x, _ = R.make_batch(exs[j:j + 50])
                extra = {}
                if kw:
                    extra["positions"] = model.positions(x)
                base = model(x, **extra)
                for t in (3, 10, 25):
                    if t >= x.shape[1] - 1:
                        continue
                    x2 = x.clone()
                    real = x2[:, t + 1:] != T.PAD
                    rnd = torch.randint(0, V, x2[:, t + 1:].shape, generator=g)
                    rnd = torch.where(rnd == T.PAD, torch.ones_like(rnd), rnd)
                    x2[:, t + 1:] = torch.where(real, rnd, x2[:, t + 1:])
                    out = model(x2, **extra)
                    d = (out[:, :t + 1] - base[:, :t + 1]).abs().amax(dim=(1, 2))
                    ok += int((d <= 1e-5).sum())
                    tot += x.shape[0]
        return {"fraction": ok / tot, "cases": tot, "tolerance": 1e-5}
    res["ii_causal"] = {"rel_rand_same_positions": causal(m, True), "nope": causal(n0, False)}
    # also in eval mode without passing positions: the eval draw depends only on lengths and order
    m.eval()
    x, _ = R.make_batch(exs[:50])
    with torch.no_grad():
        o1 = m(x)
        x2 = x.clone()
        t = 5
        tail = x2[:, t + 1:]
        new = (tail + 1) % V
        new = torch.where(new == T.PAD, (tail + 2) % V, new)
        x2[:, t + 1:] = torch.where(tail != T.PAD, new, tail)
        assert torch.equal(x2 != T.PAD, x != T.PAD)
        m.train()
        m.eval()
        o2 = m(x2)
    d = (o2[:, :t + 1] - o1[:, :t + 1]).abs().amax(dim=(1, 2))
    res["ii_causal"]["rel_rand_eval_draw"] = {"fraction": float((d <= 1e-5).float().mean()), "cases": int(d.numel()),
                                              "tolerance": 1e-5}
    # (iii) randomness off (pi = 0, 1, ...): equals standard relative attention evaluated per pair
    ok = tot = 0
    worst = 0.0
    m.eval()
    m.fixed_positions = True
    with torch.no_grad():
        for j in range(0, 200, 25):
            x, _ = R.make_batch(exs[j:j + 25])
            pos = m.positions(x)
            fast = m(x, positions=pos)
            ref = m(x, positions=pos, naive=True)
            d = (fast - ref).abs().amax(dim=(1, 2))
            worst = max(worst, float(d.max()))
            ok += int((d <= 1e-4).sum())
            tot += x.shape[0]
            assert torch.equal(pos[0], torch.arange(x.shape[1]))
    m.fixed_positions = False
    res["iii_fixed_positions_equal_standard_relative"] = {"fraction": ok / tot, "sequences": tot, "tolerance": 1e-4,
                                                         "max_abs_logit_diff": worst}
    res["params"] = {"rel_rand": M.n_params(m), "nope": M.n_params(n0),
                     "rope": M.n_params(M.build("rope", V, [T.TOK[x] for x in T.DIGITS], dict(M.SCALES["rope"]["1M"])))}
    res["all_1.000"] = all(v["fraction"] == 1.0 for v in (res["i_sorted_unique_in_range"], res["ii_causal"]["rel_rand_same_positions"],
                                                         res["ii_causal"]["nope"], res["ii_causal"]["rel_rand_eval_draw"],
                                                         res["iii_fixed_positions_equal_standard_relative"]))
    import h0a
    res["env"] = {"code": h0a.env(["stage3/pe3b.py"]), "torch": torch.__version__}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checks.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "env"}, indent=1, default=str))


def jl(p):
    return json.loads(p.read_text()) if p.exists() else None


def labels(f):
    return list(f["judgment"]["acc"])


def cmd_tunelist(a):
    """8.5-3: a task / baseline whose default-LR judgment values have in-distribution < 0.95 or bin 2 >= 0.10 gets
    LR x 0.5 and x 2 (printed as 'task kind mult' lines)"""
    for t in TASKS:
        for k in KINDS:
            f = jl(run_dir(t, k) / "final.json")
            assert f is not None, (t, k)
            acc = f["judgment"]["acc"]
            L = labels(f)
            if acc[L[0]] < 0.95 or acc[L[2]] >= 0.10:
                for m in (0.5, 2.0):
                    print(t, k, m)


def main():
    import argparse
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    sp.add_parser("tunelist")
    q = sp.add_parser("run")
    q.add_argument("--task", required=True, choices=TASKS)
    q.add_argument("--kind", required=True, choices=KINDS)
    q.add_argument("--lr-mult", type=float, default=1.0)
    q.add_argument("--resume", action="store_true")
    a = p.parse_args()
    {"check": cmd_check, "run": cmd_run, "tunelist": cmd_tunelist}[a.cmd](a)


if __name__ == "__main__":
    main()
