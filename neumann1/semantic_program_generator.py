"""Observation-conditioned, autoregressive typed PROGRAM generator.

This is a new experimental proposer, not an extension of discovery_core's
hypothesis scheduling, feature library or program memory. A small trainable
MLP predicts the next primitive/variable/constant from TRAIN observations and
the partially generated typed tree. Grammar masks ensure executable syntax.
The learned object is a conditional distribution over program structures.

The substrate and grammar are human supplied. New emitted trees, not a new
formalism, are the attainable invention scope. No benchmark/task ID is input.
"""
from __future__ import annotations

import hashlib
import json
import math
import time

import numpy as np

from neumann1 import invention_core as ic

TYPES = ("I", "B", "L")
MAX_SCOPE = 8
CONSTS = tuple(range(-2, 10))
LIB = ic.base_library()
TOKENS = tuple(LIB) + tuple("$%d" % i for i in range(MAX_SCOPE)) + tuple("#%d" % k for k in CONSTS)
INDEX = {s: i for i, s in enumerate(TOKENS)}
N = len(TOKENS)
WINDOW = 4


def canonical(ast):
    return json.dumps(ast, separators=(",", ":"))


def _value(v):
    """Bounded numeric observations, no answer-generating operators."""
    a = np.zeros(19, np.float32)
    if type(v) is bool:
        a[1], a[3] = 1, float(v)
        return a
    if type(v) is int:
        a[0], a[3] = 1, math.tanh(v / 8)
        a[4] = math.copysign(min(1, math.log1p(abs(v)) / 20), v)
        return a
    if not isinstance(v, tuple):
        raise TypeError("unsupported observation type")
    a[2], a[3] = 1, min(1, len(v) / 16)
    if not v:
        return a
    a[4:8] = [math.tanh(z / 8) for z in (min(v), max(v), sum(v) / len(v), v[0] - v[-1])]
    a[8] = len(set(v)) / len(v)
    a[9] = sum(z == 0 for z in v) / len(v)
    a[10] = sum(z < 0 for z in v) / len(v)
    for j, z in enumerate(v[:4]):
        a[11 + j] = math.tanh(z / 8)
    for j, z in enumerate(v[-4:]):
        a[15 + j] = math.tanh(z / 8)
    return a


def observations(examples):
    """Permutation-invariant statistics of paired observations only."""
    if not examples:
        raise ValueError("empty TRAIN")
    rows = []
    for inputs, output in examples:
        if len(inputs) != 1:
            raise ValueError("experimental generator accepts one typed input")
        x = inputs[0]
        p = np.zeros(8, np.float32)
        p[0] = float(type(x) is type(output) and x == output)
        if type(x) is int and type(output) is int:
            p[1] = math.tanh((output - x) / 8)
            p[2] = math.tanh(output / (abs(x) + 1) / 4)
        if isinstance(x, tuple) and isinstance(output, tuple):
            p[1] = math.tanh((len(output) - len(x)) / 4)
            p[2] = len(output) / max(1, len(x), len(output))
            p[3] = sum(a == b for a, b in zip(x, output)) / max(1, len(x), len(output))
            p[4] = sum(a == b for a, b in zip(x[::-1], output)) / max(1, len(x), len(output))
            p[5] = math.tanh((sum(output) - sum(x)) / 16)
            p[6] = sum(z in x for z in output) / max(1, len(output))
            p[7] = sum(z in output for z in x) / max(1, len(x))
        rows.append(np.concatenate((_value(x), _value(output), p)))
    r = np.asarray(rows, dtype=np.float32)
    return np.concatenate((r.mean(0), r.std(0), r.min(0), r.max(0))).astype(np.float32)


OBS_DIM = 46 * 4
CTX_DIM = WINDOW * N + 3 + MAX_SCOPE * 3 + 3


def allowed(slot):
    typ, scope = slot
    out = np.zeros(N, dtype=bool)
    for i, token in enumerate(TOKENS):
        if token in LIB:
            p = LIB[token]
            out[i] = p.ret == typ and all(len(scope) + len(bt) <= MAX_SCOPE for _, bt in p.params)
        elif token[0] == "$":
            j = int(token[1:])
            out[i] = j < len(scope) and scope[j] == typ
        else:
            out[i] = typ == "I"
    return out


def advance(stack, token_index):
    stack = list(stack)
    _, scope = stack.pop()
    token = TOKENS[token_index]
    if token in LIB:
        for t, bt in reversed(LIB[token].params):
            stack.append((t, tuple(scope) + tuple(bt)))
    return stack


def context(prefix, stack):
    v = np.zeros(CTX_DIM, np.float32)
    for j, k in enumerate(reversed(prefix[-WINDOW:])):
        v[j * N + k] = 1
    off = WINDOW * N
    typ, scope = stack[-1]
    v[off + TYPES.index(typ)] = 1
    off += 3
    for i, t in enumerate(scope):
        v[off + 3 * i + TYPES.index(t)] = 1
    v[-3:] = (min(len(prefix), 64) / 64, min(len(stack), 16) / 16, len(scope) / MAX_SCOPE)
    return v


def tokenize(ast):
    h = ast[0]
    if h == "v":
        return [INDEX["$%d" % ast[1]]]
    if h == "k":
        return [INDEX["#%d" % ast[1]]]
    return [INDEX[h]] + [k for c in ast[1:] for k in tokenize(c)]


def tree(tokens):
    position = 0

    def take():
        nonlocal position
        token = TOKENS[tokens[position]]
        position += 1
        if token[0] == "$":
            return ("v", int(token[1:]))
        if token[0] == "#":
            return ("k", int(token[1:]))
        return (token,) + tuple(take() for _ in LIB[token].params)
    ast = take()
    if position != len(tokens):
        raise ValueError("unused program tokens")
    return ast


class SemanticProgramGenerator:
    """~60k trainable scalar parameters; no pretrained model or code lookup."""

    def __init__(self, hidden=128, seed=9127):
        rng = np.random.default_rng(seed)
        self.W = (rng.standard_normal((OBS_DIM + CTX_DIM, hidden)) / math.sqrt(OBS_DIM + CTX_DIM)).astype(np.float32)
        self.b = np.zeros(hidden, np.float32)
        self.V = (rng.standard_normal((hidden, N)) / math.sqrt(hidden)).astype(np.float32)
        self.c = np.zeros(N, np.float32)

    def parameters(self):
        return [self.W, self.b, self.V, self.c]

    def logits(self, x):
        h = np.tanh(x @ self.W + self.b)
        return h @ self.V + self.c

    def fit(self, tasks, epochs=8, batch=512, seed=31):
        """Teacher programs were generated and execution-verified by selfplay()."""
        xs, ys, masks = [], [], []
        for task in tasks:
            obs = observations(task["train"])
            prefix, stack = [], [(task["out_type"], tuple(task["in_types"]))]
            for token in tokenize(task["ast"]):
                mask = allowed(stack[-1])
                if not mask[token]:
                    raise ValueError("ill-typed teacher")
                xs.append(np.concatenate((obs, context(prefix, stack))))
                ys.append(token)
                masks.append(mask)
                stack = advance(stack, token)
                prefix.append(token)
            assert not stack
        X, Y, M = np.asarray(xs), np.asarray(ys), np.asarray(masks)
        rng = np.random.default_rng(seed)
        params = self.parameters()
        before = [p.copy() for p in params]
        ms, vs = [np.zeros_like(p) for p in params], [np.zeros_like(p) for p in params]
        history, step = [], 0
        c0 = time.process_time()
        for epoch in range(epochs):
            order = rng.permutation(len(Y))
            loss = 0.0
            for start in range(0, len(Y), batch):
                ix = order[start:start + batch]
                x, y, mask = X[ix], Y[ix], M[ix]
                h = np.tanh(x @ self.W + self.b)
                z = h @ self.V + self.c
                z[~mask] = -1e4
                z -= z.max(1, keepdims=True)
                prob = np.exp(z)
                prob /= prob.sum(1, keepdims=True)
                loss -= np.log(np.maximum(prob[np.arange(len(y)), y], 1e-30)).sum()
                prob[np.arange(len(y)), y] -= 1
                dz = prob / len(y)
                dh = (dz @ self.V.T) * (1 - h * h)
                grads = [x.T @ dh, dh.sum(0), h.T @ dz, dz.sum(0)]
                step += 1
                for p, g, m, v in zip(params, grads, ms, vs):
                    np.clip(g, -2, 2, out=g)
                    m *= .9
                    m += .1 * g
                    v *= .999
                    v += .001 * g * g
                    p -= .002 * (m / (1 - .9 ** step)) / (np.sqrt(v / (1 - .999 ** step)) + 1e-8)
            history.append(float(loss / len(Y)))
        delta = math.sqrt(sum(float(np.sum((a - b) ** 2)) for a, b in zip(params, before)))
        return {"examples": len(tasks), "teacher_tokens": len(Y), "epochs": epochs,
                "loss": history, "parameter_l2_delta": delta, "parameters": sum(p.size for p in params),
                "cpu_seconds": time.process_time() - c0}

    def save(self, path):
        np.savez_compressed(path, W=self.W, b=self.b, V=self.V, c=self.c)

    @classmethod
    def load(cls, path):
        d = np.load(path, allow_pickle=False)
        obj = cls(hidden=d["b"].size)
        for name in ("W", "b", "V", "c"):
            setattr(obj, name, d[name])
        return obj

    def invent(self, train, in_types, out_type, cap_s=3, seed=0, max_programs=2048,
               conditioned=True, max_tokens=48):
        """Build new trees token by token; TRAIN-only checks; TEST never accepted."""
        c0 = time.process_time()
        obs = observations(train) if conditioned else np.zeros(OBS_DIM, np.float32)
        # Factor the unchanged observation projection out of all token decisions.
        fixed = obs @ self.W[:OBS_DIM] + self.b
        rng = np.random.default_rng(seed)
        seen, attempted, trace = set(), 0, []
        best, best_fit = None, -1
        while attempted < max_programs and time.process_time() - c0 < cap_s:
            width = min(128, max_programs - attempted)
            prefixes = [[] for _ in range(width)]
            stacks = [[(out_type, tuple(in_types))] for _ in range(width)]
            live = list(range(width))
            for _ in range(max_tokens):
                if not live or time.process_time() - c0 >= cap_s:
                    break
                X = np.asarray([context(prefixes[i], stacks[i]) for i in live])
                z = np.tanh(X @ self.W[OBS_DIM:] + fixed) @ self.V + self.c
                for j, i in enumerate(live):
                    z[j, ~allowed(stacks[i][-1])] = -1e4
                # Same fixed sampling temperature for trained and untrained arms.
                z = z / .8
                z -= z.max(1, keepdims=True)
                p = np.exp(z)
                p /= p.sum(1, keepdims=True)
                u = rng.random(len(live))
                choices = (np.cumsum(p, axis=1) < u[:, None]).sum(1)
                new_live = []
                for i, token in zip(live, choices):
                    token = min(int(token), N - 1)
                    prefixes[i].append(token)
                    stacks[i] = advance(stacks[i], token)
                    if stacks[i]:
                        new_live.append(i)
                        continue
                    ast = tree(prefixes[i])
                    key = canonical(ast)
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        fn = ic.compile_ast(ast, len(in_types), LIB)
                        fit = 0
                        for inputs, output in train:
                            try:
                                v = fn(tuple(inputs))
                            except ic.Fail:
                                v = None
                            fit += type(v) is type(output) and v == output
                    except (OverflowError, RecursionError):
                        fit = -1
                    if fit > best_fit:
                        best, best_fit = ast, fit
                        trace.append({"program": ast, "train_points_fit": fit})
                    if fit == len(train):
                        return {"ast": ast, "fit": True, "proposed": len(seen),
                                "cpu_seconds": time.process_time() - c0, "trace": trace}
                live = new_live
            attempted += width
        return {"ast": None, "fit": False, "proposed": len(seen), "best_partial": best,
                "best_points_fit": best_fit, "cpu_seconds": time.process_time() - c0, "trace": trace}


def _random_ast(rng, typ, scope, depth):
    leaves = [("v", i) for i, t in enumerate(scope) if t == typ]
    if typ == "I":
        leaves += [("k", int(k)) for k in range(5)]
    if typ == "L":
        leaves += [("nil",)]
    ps = [p for p in LIB.values() if p.ret == typ and p.arity and
          all(len(scope) + len(bt) <= MAX_SCOPE for _, bt in p.params)]
    if leaves and (depth <= 0 or rng.random() < .38):
        return leaves[int(rng.integers(len(leaves)))]
    if depth <= -1:
        return ("eq", ("k", 0), ("k", 0)) if typ == "B" else leaves[0]
    p = ps[int(rng.integers(len(ps)))]
    return (p.name,) + tuple(_random_ast(rng, t, scope + bt, depth - 1) for t, bt in p.params)


def selfplay(n=3500, seed=917, max_tries=150000, log=None):
    """Generate typed programs, execute them, deduplicate finite behaviours.

    No benchmark data, teacher model or handwritten complete solution program.
    The random grammar sampler is human designed and is explicitly not learned.
    """
    rng = np.random.default_rng(seed)
    inputs = {"L": [((tuple(int(z) for z in rng.integers(-3, 10, size=int(rng.integers(3, 9))))),)
                    for _ in range(16)], "I": [(int(z),) for z in rng.integers(0, 13, size=16)]}
    seen, tasks = set(), []
    c0 = time.process_time()
    for attempt in range(max_tries):
        ti = "L" if rng.random() < .8 else "I"
        to = TYPES[int(rng.integers(3))]
        ast = _random_ast(rng, to, (ti,), int(rng.integers(2, 5)))
        if ic.size(ast) < 4 or ic.size(ast) > 28:
            continue
        try:
            toks = tokenize(ast)
            fn = ic.compile_ast(ast, 1, LIB)
            outputs = [fn(x) for x in inputs[ti]]
        except (ic.Fail, OverflowError, RecursionError):
            continue
        if len(set(outputs)) < (2 if to == "B" else 3) or outputs == [x[0] for x in inputs[ti]]:
            continue
        key = canonical((ti, to, outputs))
        if key in seen:
            continue
        seen.add(key)
        # All original output values come from actual execution of this AST.
        pairs = list(zip(inputs[ti], outputs))
        tasks.append({"id": "selfplay/%05d" % len(tasks), "in_types": [ti], "out_type": to,
                      "train": pairs[:8], "test": pairs[8:], "ast": ast,
                      "behaviour_sha256": hashlib.sha256(key.encode()).hexdigest()})
        if log and len(tasks) % 500 == 0:
            log({"accepted": len(tasks), "attempts": attempt + 1, "cpu": time.process_time() - c0})
        if len(tasks) >= n:
            break
    return tasks, {"accepted": len(tasks), "attempts": attempt + 1, "cpu_seconds": time.process_time() - c0,
                   "root_counts": {k: sum(t["ast"][0] == k for t in tasks) for k in LIB}}
