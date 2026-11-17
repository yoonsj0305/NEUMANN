"""Stage 1 baselines (no new architecture):

1. "abacus": decoder-only transformer, pre-LN, NoPE attention + Abacus embeddings (McLeish et al. 2024): every digit
   gets the embedding of its position inside its own number (1, 2, ...), shifted by one random offset per sequence
   during training so that positions beyond the training length have been trained.  Non-digit tokens get index 0.
2. "looped": looped / universal transformer: one shared block of `block_layers` layers applied `recur` times, the
   input embedding injected before every iteration (input injection), Abacus + NoPE as in 1.  At evaluation the
   number of iterations can be raised (recurrence scaled with the input length).
3. "gru": a token-level GRU language model (embedding -> stacked GRU -> output head) over the same prompt + answer
   sequence; no positional embedding (recurrence carries order).  Width chosen so the parameter count matches the
   transformer within 5 %.
"""
from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

ABACUS_MAX = 256          # largest Abacus index (training offsets + longest number)


def abacus_index(tokens, digit_ids):
    """1-based position of each digit inside its contiguous digit run; 0 elsewhere"""
    is_d = torch.isin(tokens, digit_ids)
    idx = torch.zeros_like(tokens)
    run = torch.zeros(tokens.shape[0], dtype=tokens.dtype, device=tokens.device)
    for j in range(tokens.shape[1]):
        run = torch.where(is_d[:, j], run + 1, torch.zeros_like(run))
        idx[:, j] = run
    return idx


class Block(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))
        self.heads = heads

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(self.ln1(x)).view(B, T, 3, self.heads, D // self.heads).permute(2, 0, 3, 1, 4)
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)          # NoPE: no positional term
        x = x + self.proj(a.transpose(1, 2).reshape(B, T, D))
        return x + self.mlp(self.ln2(x))


class LM(nn.Module):
    def __init__(self, vocab, d, heads, layers, kind="abacus", block_layers=2, recur=4, digit_ids=()):
        super().__init__()
        self.kind, self.recur = kind, recur
        self.tok = nn.Embedding(vocab, d)
        self.aba = nn.Embedding(ABACUS_MAX + 1, d)
        nn.init.normal_(self.aba.weight, std=0.02)
        n = layers if kind == "abacus" else block_layers
        self.blocks = nn.ModuleList([Block(d, heads) for _ in range(n)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.register_buffer("digit_ids", torch.tensor(list(digit_ids), dtype=torch.long), persistent=False)

    def embed(self, tokens, offset=None):
        idx = abacus_index(tokens, self.digit_ids)
        if offset is not None:                              # training: one random shift per sequence
            idx = torch.where(idx > 0, idx + offset[:, None], idx)
        idx = idx.clamp(max=ABACUS_MAX)
        return self.tok(tokens) + self.aba(idx)

    def iterate(self, x, e, n):
        """n iterations of the shared block with input injection, from state x"""
        for _ in range(n):
            x = x + e
            for b in self.blocks:
                x = b(x)
        return x

    def readout(self, x):
        return self.head(self.ln(x))

    def forward(self, tokens, offset=None, recur=None):
        e = self.embed(tokens, offset)
        if self.kind == "abacus":
            x = e
            for b in self.blocks:
                x = b(x)
        else:
            x = torch.zeros_like(e)
            for _ in range(recur or self.recur):
                x = x + e                                   # input injection
                for b in self.blocks:
                    x = b(x)
        return self.head(self.ln(x))


def rope_tables(T, hd, base=10000.0, device=None):
    """cos / sin tables of rotary position embedding (Su et al. 2021) for positions 0..T-1, head dim hd"""
    inv = 1.0 / (base ** (torch.arange(0, hd, 2, device=device).float() / hd))
    ang = torch.arange(T, device=device).float()[:, None] * inv[None, :]          # T x hd/2
    ang = torch.cat([ang, ang], dim=-1)                                           # T x hd
    return ang.cos(), ang.sin()


def _rotate_half(x):
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat([-x2, x1], dim=-1)


class RopeBlock(Block):
    """the same pre-LN block (same parameters); RoPE applied to queries and keys of every head"""

    def forward(self, x, cos=None, sin=None):
        B, T, D = x.shape
        q, k, v = self.qkv(self.ln1(x)).view(B, T, 3, self.heads, D // self.heads).permute(2, 0, 3, 1, 4)
        q = q * cos + _rotate_half(q) * sin
        k = k * cos + _rotate_half(k) * sin
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(a.transpose(1, 2).reshape(B, T, D))
        return x + self.mlp(self.ln2(x))


class RopeLM(nn.Module):
    """4. "rope" (Phase A''): a standard decoder-only transformer with rotary position embedding in every attention
    layer and no other position embedding; layers / width / heads as the Abacus 1M model."""

    def __init__(self, vocab, d, heads, layers, **_):
        super().__init__()
        self.kind = "rope"
        self.heads = heads
        self.tok = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList([RopeBlock(d, heads) for _ in range(layers)])
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)

    def forward(self, tokens, offset=None, recur=None):
        x = self.tok(tokens)
        cos, sin = rope_tables(tokens.shape[1], x.shape[-1] // self.heads, device=tokens.device)
        for b in self.blocks:
            x = b(x, cos, sin)
        return self.head(self.ln(x))


class GRULM(nn.Module):
    def __init__(self, vocab, d, layers, **_):
        super().__init__()
        self.kind = "gru"
        self.tok = nn.Embedding(vocab, d)
        self.rnn = nn.GRU(d, d, num_layers=layers, batch_first=True)
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)

    def forward(self, tokens, offset=None, recur=None):
        x, _ = self.rnn(self.tok(tokens))
        return self.head(self.ln(x))


def build(kind, vocab, digit_ids, cfg):
    if kind == "gru":
        return GRULM(vocab, **cfg)
    if kind == "rope":
        return RopeLM(vocab, **cfg)
    if kind == "pf":                        # C1 Pointer Fold (stage1/pf.py); separators +, =, |
        import pf as PFM
        import tasks as TT
        return PFM.PF(vocab, sep_ids=[TT.TOK["+"], TT.TOK["="], TT.TOK["|"]], **cfg)
    if kind == "pf2":                       # C1-2: PF with the exact expected immediate loss for the head moves
        import pf as PFM
        import tasks as TT
        return PFM.PF2(vocab, sep_ids=[TT.TOK["+"], TT.TOK["="], TT.TOK["|"]], **cfg)
    if kind == "pf_cont":                   # PF-cont: the same machine without discretisation (branch step 2)
        import pf as PFM
        import tasks as TT
        return PFM.PFCont(vocab, sep_ids=[TT.TOK["+"], TT.TOK["="], TT.TOK["|"]], **cfg)
    if kind == "looped_rr":                 # the same looped network; only its training procedure differs
        return LM(vocab, digit_ids=digit_ids, kind="looped", **cfg)
    return LM(vocab, digit_ids=digit_ids, kind=kind, **cfg)


def n_params(m):
    return sum(p.numel() for p in m.parameters())


# parameter scales (~1M / ~10M / ~50M non-embedding + embedding); looped: a 2-layer shared block, width chosen so the
# parameter count matches the same scale
SCALES = {
    "abacus": {"1M": dict(d=128, heads=4, layers=4), "10M": dict(d=320, heads=8, layers=8),
               "50M": dict(d=576, heads=8, layers=12)},
    "looped": {"1M": dict(d=176, heads=4, layers=0, block_layers=2, recur=4),
               "10M": dict(d=640, heads=8, layers=0, block_layers=2, recur=4),
               "50M": dict(d=1408, heads=16, layers=0, block_layers=2, recur=4)},
    "gru": {"1M": dict(d=256, layers=2)},
}
SCALES["looped_rr"] = SCALES["looped"]
SCALES["rope"] = {k: dict(v) for k, v in SCALES["abacus"].items()}    # same layers / width / heads as Abacus
# C1 Pointer Fold: pre-declared size (CANDIDATE_DESIGN.md 3); not parameter-matched, compared by training FLOPs
SCALES["pf"] = {"1M": dict(R=4, K=16, H=3, hidden=256, emb=64)}
SCALES["pf_cont"] = SCALES["pf"]
SCALES["pf2"] = SCALES["pf"]
