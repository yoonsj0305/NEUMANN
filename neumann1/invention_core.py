"""NEUMANN invention core: experience -> invented abstractions -> new capability.

One task-agnostic mechanism over a MINIMAL typed executable substrate
(ints, bools, int lists; cons/head/tail/range, arithmetic, comparison, if,
left/right fold, map, filter: a standard functional core, human given).
No task family, benchmark name or answer-bearing operator appears here.

  wake   bottom-up, cost-ordered program search with observational
         equivalence; only TRAIN input/output examples are visible.
  sleep  second-order anti-unification over the system's OWN verified
         programs proposes new abstractions (possibly higher order: a hole
         may be applied to variables bound inside the abstraction); an
         abstraction is adopted only if it shortens programs of >= 2 tasks
         and every rewritten program still reproduces its examples.
  prior  symbol costs are re-estimated from the rewritten programs, so the
         next search is ordered by description length in the GROWN language.

Arms (issue #745):  A = substrate only, uniform costs.
                    B = A + memory of verified programs (replay + retrieval).
                    C = B + invented abstractions + learned costs.

Scope: the substrate primitives, the fold recursion schemes, the search and
the compression rule are human designed (DreamCoder / Stitch / Probe family
of ideas). What is NOT human supplied is every abstraction in the grown
library and the search order. Budgets are deterministic candidate counts.
"""
from __future__ import annotations
import itertools, math, random, sys, time
sys.setrecursionlimit(20000)
from collections import Counter, defaultdict
from difflib import SequenceMatcher

T_I, T_B, T_L = "I", "B", "L"
INT_CAP = 10 ** 18
LEN_CAP = 40
BASE_CONSTS = tuple(range(10))


class Fail(Exception):
    pass


class Budget(Exception):
    pass


class Found(Exception):
    def __init__(self, entry):
        self.entry = entry


# ------------------------------------------------------------------ executor
# Semantics-preserving executor switches (see docs/research/
# Q3Q6_EXECUTOR_EXACTNESS_2026_11_11.md).  Both default to ON; turning them
# OFF reproduces the frozen 2026-11-11 FIRST executor's evaluation order
# exactly (used only by the equivalence harness).
CALL_BY_NEED = True     # a binder-free abstraction argument is evaluated at
                        # most once per call, on first reference
REUSE_VECTORS = True    # binder-free children of a higher-order candidate are
                        # read from their already computed value vectors
# Work meter: number of substrate evaluation steps (first-order primitive
# applications, `if` vector steps, loop iterations).  The same unit in both
# executor modes; metering only, it never influences search.
WORK = [0]


def _need(f, env):
    """Call-by-need thunk for a binder-free abstraction argument.  The value
    depends only on the call-site scope `env`, which is fixed for the whole
    call; the argument is evaluated on first reference (exactly where
    call-by-name would first evaluate it, so an exception is raised at the
    same point) and the value is reused for later references."""
    cell = []

    def g(_e):
        if cell:
            return cell[0]
        v = f(env)
        cell.append(v)
        return v
    return g


def _need2(g, env, A):
    cell = []

    def h(_e):
        if cell:
            return cell[0]
        v = g(env, A)
        cell.append(v)
        return v
    return h


def _lookup(vec, idx):
    """Binder-free child of a higher-order candidate: its value on env #i is
    vec[i] (None = failure), computed earlier by the same executor."""
    def f(_env):
        v = vec[idx[0]]
        if v is None:
            raise Fail
        return v
    return f


# ----------------------------------------------------------------- substrate
def _add(a, b):
    r = a + b
    return r if -INT_CAP <= r <= INT_CAP else None


def _sub(a, b):
    r = a - b
    return r if -INT_CAP <= r <= INT_CAP else None


def _mul(a, b):
    r = a * b
    return r if -INT_CAP <= r <= INT_CAP else None


def _mod(a, b):
    return a % b if b > 0 else None


def _div(a, b):
    return a // b if b > 0 else None


def _eq(a, b):
    return a == b


def _lt(a, b):
    return a < b


def _not(a):
    return not a


def _nil():
    return ()


def _cons(x, l):
    return (x,) + l if len(l) < LEN_CAP else None


def _head(l):
    return l[0] if l else None


def _tail(l):
    return l[1:] if l else None


def _isnil(l):
    return not l


def _range(n):
    return tuple(range(n)) if 0 <= n <= LEN_CAP else None


def _vec1(f):
    return lambda va: tuple([None if a is None else f(a) for a in va])


def _vec2(f):
    return lambda va, vb: tuple(
        [None if a is None or b is None else f(a, b) for a, b in zip(va, vb)])


class Prim:
    """A primitive. params = ((type, binder_types), ...).  A parameter with
    binder types is a lambda body evaluated in the scope extended by them."""
    __slots__ = ("name", "ret", "params", "kind", "f", "vf", "comm", "body",
                 "lib", "arity", "tmpl", "vprog", "lazy")

    def __init__(self, name, ret, params, kind, f=None, comm=False, body=None):
        self.name, self.ret, self.params = name, ret, tuple(params)
        self.kind, self.f, self.comm, self.body = kind, f, comm, body
        self.arity = len(self.params)
        # binder-free parameters: their hole is always evaluated on the
        # call-site scope (js == () <=> no binder types, see _au/_to_body)
        self.lazy = tuple(i for i, (_, bt) in enumerate(self.params) if not bt)
        self.vf = None
        self.lib = None
        self.tmpl = {}
        self.vprog = None
        if kind == "fo":
            self.vf = _vec1(f) if self.arity == 1 else _vec2(f) if self.arity == 2 else None

    def first_order(self):
        return self.arity > 0 and not any(bt for _, bt in self.params)

    def value_fn(self):
        """fn(arg_values_tuple) for a first-order abstraction."""
        f = self.vprog
        if f is None:
            n = self.arity

            def conv(b):
                if b[0] == "h":
                    return ("v", b[1])
                if b[0] == "b":
                    return ("v", n + b[1])
                if b[0] == "k":
                    return b
                return (b[0],) + tuple(conv(c) for c in b[1:])
            f = self.vprog = compile_ast(conv(self.body), n, self.lib)
        return f

    def make(self, fns, depth):
        kind = self.kind
        if kind == "fo":
            f = self.f
            if self.arity == 0:
                v = f()
                return lambda env: v
            if self.arity == 1:
                a, = fns

                def fn1(env):
                    WORK[0] += 1
                    r = f(a(env))
                    if r is None:
                        raise Fail
                    return r
                return fn1
            a, b = fns

            def fn2(env):
                WORK[0] += 1
                r = f(a(env), b(env))
                if r is None:
                    raise Fail
                return r
            return fn2
        if kind == "if":
            c, a, b = fns
            return lambda env: a(env) if c(env) else b(env)
        if kind == "foldr":
            body, init, lst = fns

            def foldr(env):
                acc = init(env)
                xs = lst(env)
                WORK[0] += len(xs)
                for x in reversed(xs):
                    acc = body(env + (x, acc))
                return acc
            return foldr
        if kind == "foldl":
            body, init, lst = fns

            def foldl(env):
                acc = init(env)
                xs = lst(env)
                WORK[0] += len(xs)
                for x in xs:
                    acc = body(env + (x, acc))
                return acc
            return foldl
        if kind == "map":
            body, lst = fns

            def map_(env):
                xs = lst(env)
                WORK[0] += len(xs)
                return tuple([body(env + (x,)) for x in xs])
            return map_
        if kind == "filter":
            body, lst = fns

            def filter_(env):
                xs = lst(env)
                WORK[0] += len(xs)
                return tuple([x for x in xs if body(env + (x,))])
            return filter_
        t = self.tmpl.get(depth)
        if t is None:
            t = self.tmpl[depth] = _template(self.body, depth, depth, self.lib)
        lazy = self.lazy
        if not CALL_BY_NEED or not lazy:
            return lambda env: t(env, fns)

        def call(env):
            A = list(fns)
            for k in lazy:
                A[k] = _need(fns[k], env)
            return t(env, A)
        return call


def _native2(p, subs):
    """Same semantics as Prim.make, for closures g(env, A) used inside an
    abstraction template (A = the argument closures of the call)."""
    kind = p.kind
    if kind == "fo":
        f = p.f
        if p.arity == 0:
            v = f()
            return lambda env, A: v
        if p.arity == 1:
            a, = subs

            def g1(env, A):
                WORK[0] += 1
                r = f(a(env, A))
                if r is None:
                    raise Fail
                return r
            return g1
        a, b = subs

        def g2(env, A):
            WORK[0] += 1
            r = f(a(env, A), b(env, A))
            if r is None:
                raise Fail
            return r
        return g2
    if kind == "if":
        c, a, b = subs
        return lambda env, A: a(env, A) if c(env, A) else b(env, A)
    if kind == "foldr":
        body, init, lst = subs

        def gr(env, A):
            acc = init(env, A)
            xs = lst(env, A)
            WORK[0] += len(xs)
            for x in reversed(xs):
                acc = body(env + (x, acc), A)
            return acc
        return gr
    if kind == "foldl":
        body, init, lst = subs

        def gl(env, A):
            acc = init(env, A)
            xs = lst(env, A)
            WORK[0] += len(xs)
            for x in xs:
                acc = body(env + (x, acc), A)
            return acc
        return gl
    if kind == "map":
        body, lst = subs

        def gm(env, A):
            xs = lst(env, A)
            WORK[0] += len(xs)
            return tuple([body(env + (x,), A) for x in xs])
        return gm
    if kind == "filter":
        body, lst = subs

        def gf(env, A):
            xs = lst(env, A)
            WORK[0] += len(xs)
            return tuple([x for x in xs if body(env + (x,), A)])
        return gf
    raise ValueError(kind)


def _template(b, dcur, dcall, lib):
    """Compile an abstraction body ONCE per call depth into g(env, A)."""
    h = b[0]
    if h == "b":
        l = dcall + b[1]
        return lambda env, A: env[l]
    if h == "k":
        v = b[1]
        return lambda env, A: v
    if h == "h":
        k, js = b[1], b[2]
        if not js:
            if dcur == dcall:
                return lambda env, A: A[k](env)
            return lambda env, A: A[k](env[:dcall])
        ls = tuple(dcall + j for j in js)
        if len(ls) == 1:
            l0 = ls[0]
            return lambda env, A: A[k](env[:dcall] + (env[l0],))
        if len(ls) == 2:
            l0, l1 = ls
            return lambda env, A: A[k](env[:dcall] + (env[l0], env[l1]))
        return lambda env, A: A[k](env[:dcall] + tuple(env[l] for l in ls))
    p = lib[h]
    subs = [_template(c, dcur + len(bt), dcall, lib)
            for c, (_, bt) in zip(b[1:], p.params)]
    if p.kind != "inv":
        return _native2(p, subs)
    inner = p.tmpl.get(dcur)
    if inner is None:
        inner = p.tmpl[dcur] = _template(p.body, dcur, dcur, lib)

    lazy = set(p.lazy) if CALL_BY_NEED else ()
    if not lazy:
        def call(env, A):
            return inner(env, [(lambda e, g=g: g(e, A)) for g in subs])
        return call

    def call_need(env, A):
        # binder-free arguments of the nested call depend only on this call's
        # scope `env`: evaluate each at most once, on first reference
        return inner(env, [_need2(g, env, A) if k in lazy else (lambda e, g=g: g(e, A))
                           for k, g in enumerate(subs)])
    return call_need


def _comp_body(b, dcur, argfns, dcall, lib):
    """Compile an abstraction body. env[:dcall] is the call-site scope and
    env[dcall:] the variables bound inside the body."""
    h = b[0]
    if h == "b":
        l = dcall + b[1]
        return lambda env: env[l]
    if h == "k":
        v = b[1]
        return lambda env: v
    if h == "h":
        f, js = argfns[b[1]], b[2]
        if not js:
            return f if dcur == dcall else (lambda env: f(env[:dcall]))
        ls = tuple(dcall + j for j in js)
        if len(ls) == 1:
            l0 = ls[0]
            return lambda env: f(env[:dcall] + (env[l0],))
        if len(ls) == 2:
            l0, l1 = ls
            return lambda env: f(env[:dcall] + (env[l0], env[l1]))
        return lambda env: f(env[:dcall] + tuple(env[l] for l in ls))
    p = lib[h]
    sub = [_comp_body(c, dcur + len(bt), argfns, dcall, lib)
           for c, (_, bt) in zip(b[1:], p.params)]
    return p.make(sub, dcur)


def base_library():
    I, B, L = T_I, T_B, T_L
    P = [
        Prim("add", I, [(I, ()), (I, ())], "fo", _add, comm=True),
        Prim("sub", I, [(I, ()), (I, ())], "fo", _sub),
        Prim("mul", I, [(I, ()), (I, ())], "fo", _mul, comm=True),
        Prim("mod", I, [(I, ()), (I, ())], "fo", _mod),
        Prim("div", I, [(I, ()), (I, ())], "fo", _div),
        Prim("head", I, [(L, ())], "fo", _head),
        Prim("ifI", I, [(B, ()), (I, ()), (I, ())], "if"),
        Prim("foldrI", I, [(I, (I, I)), (I, ()), (L, ())], "foldr"),
        Prim("foldlI", I, [(I, (I, I)), (I, ()), (L, ())], "foldl"),
        Prim("eq", B, [(I, ()), (I, ())], "fo", _eq, comm=True),
        Prim("lt", B, [(I, ()), (I, ())], "fo", _lt),
        Prim("isnil", B, [(L, ())], "fo", _isnil),
        Prim("not", B, [(B, ())], "fo", _not),
        Prim("nil", L, [], "fo", _nil),
        Prim("cons", L, [(I, ()), (L, ())], "fo", _cons),
        Prim("tail", L, [(L, ())], "fo", _tail),
        Prim("range", L, [(I, ())], "fo", _range),
        Prim("ifL", L, [(B, ()), (L, ()), (L, ())], "if"),
        Prim("foldrL", L, [(L, (I, L)), (L, ()), (L, ())], "foldr"),
        Prim("foldlL", L, [(L, (I, L)), (L, ()), (L, ())], "foldl"),
        Prim("map", L, [(I, (I,)), (L, ())], "map"),
        Prim("filter", L, [(B, (I,)), (L, ())], "filter"),
    ]
    lib = {p.name: p for p in P}
    for p in P:
        p.lib = lib
    return lib


def add_invention(lib, name, ret, params, body):
    p = Prim(name, ret, [(t, tuple(bt)) for t, bt in params], "inv",
             body=body)
    p.lib = lib
    lib[name] = p
    return p


def library_from_spec(spec):
    """spec = [(name, ret, params, body), ...] in definition order."""
    lib = base_library()
    for name, ret, params, body in spec:
        add_invention(lib, name, ret, params, _tup(body))
    return lib


def _tup(x):
    return tuple(_tup(y) for y in x) if isinstance(x, (list, tuple)) else x


# ----------------------------------------------------------------- programs
def size(ast):
    return 1 if ast[0] in ("v", "k", "b", "h") else 1 + sum(size(c) for c in ast[1:])


def compile_ast(ast, depth, lib):
    h = ast[0]
    if h == "v":
        l = ast[1]
        return lambda env: env[l]
    if h == "k":
        v = ast[1]
        return lambda env: v
    p = lib[h]
    fns = [compile_ast(c, depth + len(bt), lib)
           for c, (_, bt) in zip(ast[1:], p.params)]
    return p.make(fns, depth)


def run_program(ast, lib, inputs):
    """Returns the output or None when the program fails on this input."""
    try:
        return compile_ast(ast, len(inputs), lib)(tuple(inputs))
    except Fail:
        return None


def show(ast, depth=0):
    h = ast[0]
    if h == "v":
        return "$%d" % ast[1]
    if h == "k":
        return str(ast[1])
    if h == "b":
        return "b%d" % ast[1]
    if h == "h":
        return "?%d" % ast[1] + ("(%s)" % ",".join("b%d" % j for j in ast[2]) if ast[2] else "")
    if len(ast) == 1:
        return h
    return "(%s %s)" % (h, " ".join(show(c) for c in ast[1:]))


def expand(ast, lib):
    """Fully expanded size in substrate nodes (execution-cost proxy)."""
    h = ast[0]
    if h in ("v", "k", "b", "h"):
        return 1
    p = lib[h]
    inner = sum(expand(c, lib) for c in ast[1:])
    return inner + (expand(p.body, lib) if p.kind == "inv" else 1)


def _shift(t, dcall, m, js, q):
    h = t[0]
    if h == "v":
        l = t[1]
        if l < dcall:
            return t
        if l < dcall + m:
            return ("v", dcall + js[l - dcall])
        return ("v", l - m + q)
    if h == "k":
        return t
    return (h,) + tuple(_shift(c, dcall, m, js, q) for c in t[1:])


def _inst(b, dcur, dcall, args, lib):
    h = b[0]
    if h == "b":
        return ("v", dcall + b[1])
    if h == "k":
        return b
    if h == "h":
        return _shift(args[b[1]], dcall, len(b[2]), b[2], dcur - dcall)
    return (h,) + tuple(_inst(c, dcur + len(bt), dcall, args, lib)
                        for c, (_, bt) in zip(b[1:], lib[h].params))


def inline(ast, depth, lib):
    """Expand every invented abstraction back into substrate primitives."""
    h = ast[0]
    if h in ("v", "k"):
        return ast
    p = lib[h]
    kids = tuple(inline(c, depth + len(bt), lib)
                 for c, (_, bt) in zip(ast[1:], p.params))
    if p.kind != "inv":
        return (h,) + kids
    return inline(_inst(p.body, depth, depth, kids, lib), depth, lib)


# ------------------------------------------------------------------- search
class _E:
    __slots__ = ("prim", "kids", "vec", "fn", "depth", "term", "hv", "faith")

    def __init__(self, prim, kids, vec, fn, depth, term, hv, faith=True):
        self.prim, self.kids, self.vec, self.fn = prim, kids, vec, fn
        self.depth, self.term, self.hv = depth, term, hv
        # faith: vec[i] is exactly what getfn() returns on env #i of this
        # context (None <=> Fail).  False for value-mode abstraction calls,
        # which treat a failing argument as failure even when the body would
        # never reference it (strict), whereas closures are lazy.
        self.faith = faith

    def getfn(self):
        f = self.fn
        if f is None:
            if self.prim is None:
                v = self.term[1]
                f = (lambda env: env[v]) if self.term[0] == "v" else (lambda env: v)
            else:
                f = self.prim.make([k.getfn() for k in self.kids], self.depth)
            self.fn = f
        return f

    def ast(self):
        if self.prim is None:
            return self.term
        return (self.prim.name,) + tuple(k.ast() for k in self.kids)


class _Ctx:
    __slots__ = ("types", "envs", "depth", "nb", "lv", "done", "seen", "sub",
                 "terms")

    def __init__(self, types, envs, nb):
        self.types, self.envs, self.nb = tuple(types), envs, nb
        self.depth = len(self.types)
        self.lv = {}
        self.done = {T_I: 0, T_B: 0, T_L: 0}
        self.seen = {T_I: set(), T_B: set(), T_L: set()}
        self.sub = {}
        self.terms = None


_COMPS = {}


def _compositions(n, k):
    key = (n, k)
    if key not in _COMPS:
        if k == 1:
            out = [(n,)]
        else:
            out = [(i,) + rest for i in range(1, n - k + 2)
                   for rest in _compositions(n - i, k - 1)]
        _COMPS[key] = out
    return _COMPS[key]


def uniform_costs():
    return defaultdict(lambda: 1)


class Search:
    """Cost-ordered bottom-up enumeration with observational equivalence.

    examples: list of (inputs_tuple, output).  Only these are visible.
    budget:   maximum number of candidate programs evaluated (deterministic).
    """

    def __init__(self, lib, cost, in_types, out_type, examples, budget,
                 consts=(), max_nb=2, max_level=80, seed=0):
        self.lib = lib
        self.by_ret = {T_I: [], T_B: [], T_L: []}
        for p in lib.values():
            self.by_ret[p.ret].append(p)
        self.cost = cost
        self.in_types, self.out_type = tuple(in_types), out_type
        self.examples = examples
        self.budget, self.n = budget, 0
        self.consts = tuple(sorted(set(BASE_CONSTS) | set(consts)))
        self.max_nb, self.max_level, self.seed = max_nb, max_level, seed
        self.target = tuple(o for _, o in examples)
        self.nprobe = max(1, 32 // max(1, len(examples)))
        self.top = _Ctx(self.in_types, [tuple(i) for i, _ in examples], 0)
        self.top.terms = self._terms(self.top)
        self._argctx_cache = {}

    # probes: plausible values for lambda-bound variables, used ONLY to
    # merge behaviourally identical sub-expressions (never as answers).
    def _probe_envs(self, binders):
        envs = []
        for i, (inp, out) in enumerate(self.examples):
            ints = [0, 1, 2, 3]
            lists = [()]
            for v in tuple(inp) + (out,):
                if isinstance(v, tuple):
                    ints.extend(v)
                    ints.append(len(v))
                    lists.append(v)
                elif isinstance(v, bool):
                    pass
                elif isinstance(v, int):
                    ints.append(v)
                    if 0 <= v <= 12:
                        lists.append(tuple(range(v)))
            for q in range(self.nprobe):
                rng = random.Random(self.seed * 1000003 + i * 7919 + q * 104729
                                    + len(binders) * 31)
                vals = []
                for t in binders:
                    if t == T_I:
                        vals.append(rng.choice(ints))
                    elif t == T_B:
                        vals.append(rng.random() < 0.5)
                    else:
                        base = rng.choice(lists)
                        a = rng.randint(0, len(base))
                        vals.append(base[a:] if rng.random() < 0.6 else base[:a])
                envs.append(tuple(inp) + tuple(vals))
        return envs

    def _terms(self, ctx):
        terms = []
        n_in = len(self.in_types)
        for l, t in enumerate(ctx.types):
            sym = ("$in:" if l < n_in else "$bv:") + t
            terms.append((("v", l), t, tuple(e[l] for e in ctx.envs), sym, True))
        npos = len(ctx.envs)
        for v in self.consts:
            sym = "k%d" % v if v in BASE_CONSTS else "$kd"
            terms.append((("k", v), T_I, (v,) * npos, sym, False))
        return terms

    def _subctx(self, ctx, bt):
        if ctx.nb + 1 > self.max_nb:
            return None
        sub = ctx.sub.get(bt)
        if sub is None:
            binders = ctx.types[len(self.in_types):] + bt
            sub = _Ctx(ctx.types + bt, self._probe_envs(binders), ctx.nb + 1)
            sub.terms = self._terms(sub)
            ctx.sub[bt] = sub
        return sub

    def _pool(self, ctx, t, c):
        """Entries of type t and exact cost c, generated on demand.  Only
        types and levels that some parent can still use are ever built; all
        cheaper levels of the same type are built first so that the kept
        representative of a behaviour is a minimum-cost one."""
        done = ctx.done[t]
        while done < c:
            done += 1
            ctx.lv[(t, done)] = self._level(ctx, t, done)
            ctx.done[t] = done
        return ctx.lv[(t, c)]

    def _level(self, ctx, t, c):
        out = []
        cost = self.cost
        for term, tt, vec, sym, hv in ctx.terms:
            if tt == t and cost[sym] == c:
                self._keep(ctx, out, _E(None, (), vec, None, ctx.depth, term, hv), t)
        for p in self.by_ret[t]:
            cp = cost[p.name]
            k = p.arity
            if k == 0:
                if cp == c:
                    self._cand(ctx, p, (), out)
                continue
            rem = c - cp
            if rem < k:
                continue
            acs = []
            for _, bt in p.params:
                ac = ctx if not bt else self._subctx(ctx, bt)
                if ac is None:
                    break
                acs.append(ac)
            if len(acs) != k:
                continue
            comm = p.comm
            for split in _compositions(rem, k):
                if comm and split[0] > split[1]:
                    continue
                pools = []
                for (pt, _), ac, ci in zip(p.params, acs, split):
                    pool = self._pool(ac, pt, ci)
                    if not pool:
                        break
                    pools.append(pool)
                if len(pools) != k:
                    continue
                if k == 1:
                    for a in pools[0]:
                        self._cand(ctx, p, (a,), out)
                elif k == 2:
                    if comm and split[0] == split[1]:
                        pa = pools[0]
                        for i, a in enumerate(pa):
                            for b in pa[i:]:
                                self._cand(ctx, p, (a, b), out)
                    else:
                        pb = pools[1]
                        for a in pools[0]:
                            for b in pb:
                                self._cand(ctx, p, (a, b), out)
                else:
                    for kids in itertools.product(*pools):
                        self._cand(ctx, p, kids, out)
        return out

    def _cand(self, ctx, p, kids, out):
        kind = p.kind
        hv = False
        for k in kids:
            if k.hv:
                hv = True
                break
        if not hv and p.ret != T_L:
            return                      # closed int/bool compounds are constants
        self.n += 1
        if self.n > self.budget:
            raise Budget()
        fn = None
        faith = True
        if kind == "fo":
            WORK[0] += len(ctx.envs)
            if p.arity == 0:
                vec = (p.f(),) * len(ctx.envs)
            else:
                vec = p.vf(*[k.vec for k in kids])
            for k in kids:
                if not k.faith:
                    faith = False
                    break
        elif kind == "if":
            c, a, b = kids
            if a is b:
                return
            WORK[0] += len(ctx.envs)
            vec = tuple([None if x is None else (y if x else z)
                         for x, y, z in zip(c.vec, a.vec, b.vec)])
            faith = c.faith and a.faith and b.faith
        elif kind == "inv" and p.first_order():
            faith = False
            # A first-order abstraction is a function of its argument VALUES:
            # reuse the children's value vectors instead of re-running them.
            vp = p.value_fn()
            res = []
            for args in zip(*[k.vec for k in kids]):
                if None in args:
                    res.append(None)
                    continue
                try:
                    res.append(vp(args))
                except Fail:
                    res.append(None)
            vec = tuple(res)
        elif REUSE_VECTORS:
            # Higher-order candidate.  Binder-free children whose vector is
            # faithful are read from it instead of being re-executed; the
            # general closure (needed by parents in other scopes) is built
            # later by getfn() from the same children.
            idx = [0]
            fast = [_lookup(k.vec, idx) if not bt and k.faith else k.getfn()
                    for k, (_, bt) in zip(kids, p.params)]
            fe = p.make(fast, ctx.depth)
            res = []
            for i, env in enumerate(ctx.envs):
                idx[0] = i
                try:
                    res.append(fe(env))
                except Fail:
                    res.append(None)
            vec = tuple(res)
        else:
            fn = p.make([k.getfn() for k in kids], ctx.depth)
            res = []
            for env in ctx.envs:
                try:
                    res.append(fn(env))
                except Fail:
                    res.append(None)
            vec = tuple(res)
        if vec.count(None) == len(vec):
            return
        self._keep(ctx, out, _E(p, kids, vec, fn, ctx.depth, None, hv, faith), p.ret)

    def _keep(self, ctx, out, e, t):
        seen = ctx.seen[t]
        if e.vec in seen:
            return
        seen.add(e.vec)
        out.append(e)
        if ctx is self.top and t == self.out_type and e.vec == self.target:
            raise Found(e)

    def run(self):
        """Returns the minimum-cost TRAIN-consistent program AST or None."""
        try:
            for c in range(1, self.max_level + 1):
                self._pool(self.top, self.out_type, c)
        except Found as f:
            return f.entry.ast()
        except Budget:
            return None
        return None


# -------------------------------------------------------------------- sleep
def _typeof(ast, scope, lib):
    h = ast[0]
    if h == "v":
        return scope[ast[1]]
    if h == "k":
        return T_I
    return lib[h].ret


def _free_internal(t, d, q, acc):
    if t[0] == "v":
        j = t[1] - d
        if 0 <= j < q:
            acc.add(j)
    elif t[0] != "k":
        for c in t[1:]:
            _free_internal(c, d, q, acc)
    return acc


def _rel(t, d):
    if t[0] == "v":
        return ("v", t[1] - d)
    if t[0] == "k":
        return t
    return (t[0],) + tuple(_rel(c, d) for c in t[1:])


def _au(a, da, sa, b, db, sb, q, btypes, holes, lib):
    """Second-order anti-unification of two typed subtrees.  A mismatch
    becomes a hole applied to the pattern-bound variables it mentions."""
    ha, hb = a[0], b[0]
    if ha == "v" and hb == "v":
        ja, jb = a[1] - da, b[1] - db
        if 0 <= ja < q and ja == jb:
            return ("b", ja)
    elif ha == hb:
        if ha == "k":
            if a[1] == b[1]:
                return a
        else:
            p = lib[ha]
            out = [ha]
            for ca, cb, (_, bt) in zip(a[1:], b[1:], p.params):
                out.append(_au(ca, da, sa + bt, cb, db, sb + bt, q + len(bt),
                               btypes + bt, holes, lib))
            return tuple(out)
    js = tuple(sorted(_free_internal(a, da, q, set()) | _free_internal(b, db, q, set())))
    key = (_rel(a, da), _rel(b, db), js)
    if key not in holes:
        holes[key] = (len(holes), _typeof(a, sa, lib), tuple(btypes[j] for j in js))
    return ("h", holes[key][0], js)


def _solid(p):
    """Non-hole, non-variable nodes of a pattern."""
    if p[0] in ("h", "b"):
        return 0
    if p[0] == "k":
        return 1
    return 1 + sum(_solid(c) for c in p[1:])


def _rename(t, d, q, js, m):
    h = t[0]
    if h == "v":
        l = t[1]
        if l < d:
            return t
        j = l - d
        if j < q:
            if j not in js:
                return None
            return ("v", d + js.index(j))
        return ("v", l - q + m)
    if h == "k":
        return t
    out = [h]
    for c in t[1:]:
        r = _rename(c, d, q, js, m)
        if r is None:
            return None
        out.append(r)
    return tuple(out)


def _match(p, t, d, q, bind, lib):
    h = p[0]
    if h == "b":
        return t[0] == "v" and t[1] == d + p[1]
    if h == "h":
        arg = _rename(t, d, q, p[2], len(p[2]))
        if arg is None:
            return False
        k = p[1]
        if k in bind:
            return bind[k] == arg
        bind[k] = arg
        return True
    if h == "k":
        return t[0] == "k" and t[1] == p[1]
    if t[0] != h:
        return False
    for cp, ct, (_, bt) in zip(p[1:], t[1:], lib[h].params):
        if not _match(cp, ct, d, q + len(bt), bind, lib):
            return False
    return True


def rewrite(t, d, name, pat, lib):
    h = t[0]
    if h in ("v", "k"):
        return t
    bind = {}
    if _match(pat, t, d, 0, bind, lib):
        params = lib[name].params
        return (name,) + tuple(
            rewrite(bind[k], d + len(params[k][1]), name, pat, lib)
            for k in range(len(params)))
    return (h,) + tuple(rewrite(c, d + len(bt), name, pat, lib)
                        for c, (_, bt) in zip(t[1:], lib[h].params))


def _subtrees(t, d, scope, lib, out, tag):
    if t[0] in ("v", "k"):
        return
    out.append((t, d, scope, tag))
    for c, (_, bt) in zip(t[1:], lib[t[0]].params):
        _subtrees(c, d + len(bt), scope + bt, lib, out, tag)


def propose(corpus, lib, top_k=120, max_pairs=400000):
    """corpus: {task_id: (ast, in_types)}.  Returns candidate patterns
    [(pattern, ret, params)] ranked by a cheap upper bound of their gain."""
    subs = []
    for tid, (ast, in_types) in corpus.items():
        _subtrees(ast, len(in_types), tuple(in_types), lib, subs, tid)
    by_root = defaultdict(list)
    for s in subs:
        by_root[s[0][0]].append(s)
    votes, sigs = Counter(), {}
    pairs = 0
    for root, group in sorted(by_root.items()):
        for x, y in itertools.combinations(group, 2):
            if x[3] == y[3]:
                continue
            pairs += 1
            if pairs > max_pairs:
                break
            holes = {}
            pat = _au(x[0], x[1], x[2], y[0], y[1], y[2], 0, (), holes, lib)
            s = _solid(pat)
            if pat[0] == "h" or s < 2:
                continue
            votes[pat] += s
            if pat not in sigs:
                params = [None] * len(holes)
                for k, t, bt in holes.values():
                    params[k] = (t, bt)
                sigs[pat] = (lib[root].ret, tuple(params))
    return [(pat,) + sigs[pat] for pat, _ in votes.most_common(top_k)]


def compress(corpus, lib, examples, next_id, max_new=8, min_gain=3,
             min_tasks=2, log=None):
    """Greedy MDL abstraction.  `lib` is extended in place; returns
    (new corpus, [spec of adopted inventions]).  `examples[tid]` holds the
    task's (inputs, output) pairs used to verify every rewritten program."""
    adopted = []
    for _ in range(max_new):
        best = None
        for pat, ret, params in propose(corpus, lib):
            name = "f%d" % next_id
            add_invention(lib, name, ret, params, pat)
            gain, tasks, new = -_solid(pat), 0, {}
            for tid, (ast, in_types) in corpus.items():
                r = rewrite(ast, len(in_types), name, pat, lib)
                new[tid] = (r, in_types)
                d = size(ast) - size(r)
                if d > 0:
                    gain += d
                    tasks += 1
            del lib[name]
            if tasks >= min_tasks and gain >= min_gain and (best is None or gain > best[0]):
                best = (gain, pat, ret, params, new, tasks)
        if best is None:
            break
        gain, pat, ret, params, new, tasks = best
        name = "f%d" % next_id
        add_invention(lib, name, ret, params, pat)
        ok = True                       # independent semantic re-verification
        for tid, (ast, in_types) in new.items():
            if ast != corpus[tid][0]:
                for inp, out in examples[tid]:
                    if run_program(ast, lib, inp) != out:
                        ok = False
                        break
            if not ok:
                break
        if not ok:
            del lib[name]
            if log:
                log("rejected unsound rewrite for %s" % show(pat))
            break
        corpus = new
        adopted.append((name, ret, [(t, list(bt)) for t, bt in params], pat))
        if log:
            log("invented %s : %s  gain=%d tasks=%d" % (name, show(pat), gain, tasks))
        next_id += 1
    return corpus, adopted


# -------------------------------------------------------------------- prior
def _count(ast, d_in, scope, lib, counts):
    h = ast[0]
    if h == "v":
        t = scope[ast[1]]
        counts[t][("$in:" if ast[1] < d_in else "$bv:") + t] += 1
    elif h == "k":
        counts[T_I]["k%d" % ast[1] if ast[1] in BASE_CONSTS else "$kd"] += 1
    else:
        p = lib[h]
        counts[p.ret][h] += 1
        for c, (_, bt) in zip(ast[1:], p.params):
            _count(c, d_in, scope + bt, lib, counts)


def learn_costs(programs, lib, alpha=0.5, explore=0.35):
    """programs: [(ast, in_types)].  Per-type unigram description lengths
    (bits, integer >= 1) estimated from the system's own programs, mixed
    with the uniform prior so that rarely used substrate symbols stay
    reachable (otherwise the prior collapses onto early easy programs)."""
    counts = {T_I: Counter(), T_B: Counter(), T_L: Counter()}
    for ast, in_types in programs:
        _count(ast, len(in_types), tuple(in_types), lib, counts)
    symbols = {T_I: ["$in:I", "$bv:I", "$kd"] + ["k%d" % v for v in BASE_CONSTS],
               T_B: ["$in:B", "$bv:B"], T_L: ["$in:L", "$bv:L"]}
    for p in lib.values():
        symbols[p.ret].append(p.name)
    cost = {}
    for t, syms in symbols.items():
        total = sum(counts[t].values()) + alpha * len(syms)
        for s in syms:
            p = ((1 - explore) * (counts[t][s] + alpha) / total
                 + explore / len(syms))
            cost[s] = max(1, int(round(-math.log2(p))))
    return cost


def _as_cost(cost):
    if cost is None:
        return uniform_costs()
    d = defaultdict(lambda: 8)
    d.update(cost)
    return d


# ------------------------------------------------------------------- memory
def _similarity(a, b):
    if a == b:
        return 1.0
    if isinstance(a, tuple) and isinstance(b, tuple):
        return 0.9 * SequenceMatcher(None, a, b, autojunk=False).ratio()
    return 0.0


def memory_prims(lib, memory, task, k=8):
    """Episodic memory.  Returns (exact replay ast or None, #replays, names
    of the k retrieved whole programs added to `lib` as unary primitives).
    Retrieval is behavioural: similarity of each stored program's outputs on
    this task's TRAIN inputs to the TRAIN outputs."""
    sig = (tuple(task["in_types"]), task["out_type"])
    scored, replays, exact = [], 0, None
    for mid, (ast, in_types, out_type) in enumerate(memory):
        if (tuple(in_types), out_type) != sig:
            continue
        replays += 1
        fn = compile_ast(ast, len(in_types), lib)
        score, good = 0.0, True
        for inp, out in task["train"]:
            try:
                got = fn(tuple(inp))
            except Fail:
                got = None
            if got != out:
                good = False
            score += _similarity(got, out) if got is not None else 0.0
        if good and (exact is None or size(ast) < size(exact)):
            exact = ast
        scored.append((-score, size(ast), mid))
    names = []
    if len(task["in_types"]) == 1:
        for _, _, mid in sorted(scored)[:k]:
            ast, in_types, out_type = memory[mid]
            name = "m%d" % mid
            add_invention(lib, name, out_type, [(in_types[0], ())],
                          _to_body(ast, 1))
            names.append(name)
    return exact, replays, names


def _to_body(ast, d_in):
    h = ast[0]
    if h == "v":
        return ("h", ast[1], ()) if ast[1] < d_in else ("b", ast[1] - d_in)
    if h == "k":
        return ast
    return (h,) + tuple(_to_body(c, d_in) for c in ast[1:])


# -------------------------------------------------------------------- solve
def data_constants(train):
    """Integers that appear in >= half of the TRAIN outputs without being in
    the corresponding input (generic constant seeding, no task knowledge)."""
    hits = Counter()
    for inp, out in train:
        seen = set()
        for v in inp:
            seen.update(v if isinstance(v, tuple) else (v,))
        vals = out if isinstance(out, tuple) else (out,)
        for v in set(vals):
            if isinstance(v, int) and not isinstance(v, bool) and v not in seen:
                hits[v] += 1
    need = (len(train) + 1) // 2
    return tuple(sorted(v for v, n in hits.items() if n >= need and v not in BASE_CONSTS))[:6]


def solve(task, spec=(), cost=None, budget=100000, memory=None, k_retrieve=8):
    """One task, one arm.  task: {in_types, out_type, train, test}.
    Only `train` reaches the search; `test` is scored afterwards."""
    t0 = time.perf_counter()
    c0, w0 = time.process_time(), WORK[0]
    lib = library_from_spec(spec)
    cost = _as_cost(cost)
    used, via, ast = 0, None, None
    if memory:
        ast, used, names = memory_prims(lib, memory, task, k_retrieve)
        via = "replay" if ast is not None else None
        for nm in names:
            cost[nm] = cost.get("$mem", 1)
    if ast is None and used < budget:
        s = Search(lib, cost, task["in_types"], task["out_type"], task["train"],
                   budget - used, consts=data_constants(task["train"]))
        ast = s.run()
        used += s.n
        via = "search" if ast is not None else None
    ok = False
    if ast is not None:
        ok = all(run_program(ast, lib, inp) == out for inp, out in task["test"])
    return {"fit": ast is not None, "solved": bool(ok), "via": via,
            "candidates": used, "ast": ast,
            "size": size(ast) if ast is not None else None,
            "seconds": round(time.perf_counter() - t0, 4),
            "cpu_seconds": round(time.process_time() - c0, 4),
            "work": WORK[0] - w0}


# ----------------------------------------------------------------- training
def sig_key(task):
    return "".join(task["in_types"]) + ">" + task["out_type"]


def cost_for(costs, task):
    """costs = {"*": global, "<sig>": per-signature}.  The task signature is
    observable; an unseen signature falls back to the global prior."""
    if costs is None:
        return None
    return costs.get(sig_key(task), costs["*"])


def _job(args):
    task, spec, cost, budget, memory = args
    r = solve(task, spec, cost, budget, memory)
    r["id"] = task["id"]
    return r


def run_arm(tasks, spec, costs, budget, memory, pool):
    jobs = [(t, spec, cost_for(costs, t), budget, memory) for t in tasks]
    return (pool.map(_job, jobs, chunksize=1) if pool is not None
            else [_job(j) for j in jobs])


def untrained_costs():
    """The same prior mechanism with zero experience: uniform per type."""
    c = learn_costs([], base_library())
    c["$mem"] = 3                       # a retrieved memory costs like a primitive
    return {"*": c}


def train(tasks, rounds=3, budget=1000000, pool=None, log=print, max_new=8,
          min_sig=8):
    """Wake-sleep on SOURCE tasks.  Each task: {id, in_types, out_type,
    train, test}; here `test` is only a verification split of SOURCE data.
    No reference program is ever read.  Returns the frozen core state."""
    spec, costs = [], untrained_costs()
    lib = base_library()
    solved, history = {}, []
    by_id = {t["id"]: t for t in tasks}
    for r in range(rounds):
        t0 = time.perf_counter()
        results = run_arm(tasks, spec, costs, budget, None, pool)
        cands = sum(x["candidates"] for x in results)
        for x in results:
            if x["fit"] and x["solved"]:
                old = solved.get(x["id"])
                if old is None or size(x["ast"]) <= size(old):
                    solved[x["id"]] = _tup(x["ast"])
        corpus = {tid: (ast, tuple(by_id[tid]["in_types"]))
                  for tid, ast in sorted(solved.items())}
        examples = {tid: by_id[tid]["train"] + by_id[tid]["test"] for tid in corpus}
        corpus, adopted = compress(corpus, lib, examples, len(spec),
                                   max_new=max_new, log=log)
        spec = spec + adopted
        solved = {tid: ast for tid, (ast, _) in corpus.items()}
        costs = {"*": learn_costs(list(corpus.values()), lib)}
        groups = defaultdict(list)
        for tid, prog in corpus.items():
            groups[sig_key(by_id[tid])].append(prog)
        for key, progs in groups.items():
            if len(progs) >= min_sig:
                costs[key] = learn_costs(progs, lib)
        for c in costs.values():
            c["$mem"] = 3
        history.append({"round": r, "wake_fit_and_verified": len(solved),
                        "wake_candidates": cands, "inventions": len(spec),
                        "seconds": round(time.perf_counter() - t0, 2)})
        log("round %d: %d/%d source tasks solved, %d inventions, %.0fs"
            % (r, len(solved), len(tasks), len(spec), history[-1]["seconds"]))
    memory = [(inline(ast, len(by_id[tid]["in_types"]), lib),
               tuple(by_id[tid]["in_types"]), by_id[tid]["out_type"])
              for tid, ast in sorted(solved.items())]
    return {"spec": spec, "costs": costs, "memory": memory,
            "solved": {tid: ast for tid, ast in sorted(solved.items())},
            "history": history}
