"""Joint latent invention (section 43) -- opt-in, needs z3 (optional dependency).

A latent-state transducer is synthesised as ONE constraint problem from observed input/output behaviour:
    h_0 = z0,  h_{t+1} = U(h_t, x_t),  output piece_t = [V(h_t, h_{t+1}, x_t)] if C(h_t, h_{t+1}, x_t) else []
The latent values h_t at every observed prefix are UNKNOWNS of the problem: they are never identified first and never
queried.  U, V and C are expression trees of the generic integer substrate (variables, constants, add, sub, min, max,
mod by a small constant; comparisons lt / eq for C); every operator at every node and every constant is a choice of
the solver.  Any solution reproduces every observed output; solutions that predict the same outputs everywhere are not
told apart.  Two solutions that predict differently are separated by an input the solver itself constructs
(`distinguishing_input`), which the caller observes and adds as a constraint.

Nothing names a task or a generator; the operator set is the substrate's integer core.
"""
from __future__ import annotations
import time

try:
    import z3
except Exception:          # optional dependency
    z3 = None

BITS = 8                   # values are bounded signed bit-vectors (bit-blasted solving); Python semantics kept
INT_OPS = ("var0", "var1", "var2", "const", "add", "sub", "min", "max", "mod")   # mod: divisor = the node's constant
BOOL_OPS = ("true", "lt", "eq")
CMAX = 40


class Tree:
    """A symbolic expression tree of fixed depth over `nvars` integer variables."""

    def __init__(self, name, depth, nvars, kind="int"):
        self.name, self.depth, self.nvars, self.kind = name, depth, nvars, kind
        self.ops, self.consts = {}, {}
        self.nodes = self._build(name, depth, kind)

    def _build(self, path, depth, kind):
        op = z3.BitVec("%s_op" % path, 5)
        c = z3.BitVec("%s_c" % path, BITS)
        self.ops[path], self.consts[path] = op, c
        node = {"path": path, "op": op, "c": c, "kind": kind, "kids": []}
        if depth > 0:
            node["kids"] = [self._build(path + "l", depth - 1, "int"), self._build(path + "r", depth - 1, "int")]
        return node

    def wellformed(self, canon=False, ops_allowed=None):
        """canon: children of a node whose operator does not use them are fixed to one canonical form (removes the
        solver's freedom over inactive subtrees); ops_allowed: restrict the integer operators (measurement only)"""
        cons = []

        def canonical(n):
            cons.append(n["op"] == INT_OPS.index("const"))
            cons.append(n["c"] == 0)
            for k in n["kids"]:
                canonical(k)

        def walk(n, depth):
            ops = BOOL_OPS if n["kind"] == "bool" else INT_OPS
            if n["kind"] == "int" and ops_allowed is not None:
                cons.append(z3.Or([n["op"] == INT_OPS.index(o) for o in ops_allowed if o in INT_OPS
                                   and (depth > 0 or o in ("var0", "var1", "var2", "const"))]))
            if canon and n["kids"]:
                leafish = [INT_OPS.index(o) for o in ("var0", "var1", "var2", "const")] if n["kind"] == "int" else [0]
                cons.append(z3.Implies(z3.Or([n["op"] == i for i in leafish]),
                                       z3.And([z3.And(k["op"] == INT_OPS.index("const"), k["c"] == 0) for k in n["kids"]])))
                if n["kind"] == "int":
                    cons.append(z3.Implies(n["op"] == INT_OPS.index("mod"),
                                           z3.And(n["kids"][1]["op"] == INT_OPS.index("const"), n["kids"][1]["c"] == 0)))
            allowed = [i for i, o in enumerate(ops) if depth > 0 or o in ("var0", "var1", "var2", "const", "true")]
            if n["kind"] == "int":
                allowed = [i for i in allowed if not (ops[i].startswith("var") and int(ops[i][3]) >= self.nvars)]
            cons.append(z3.Or([n["op"] == i for i in allowed]))
            cons.append(z3.And(n["c"] >= -CMAX, n["c"] <= CMAX))
            if n["kind"] == "int" and n["kids"]:
                cons.append(z3.Implies(n["op"] == INT_OPS.index("mod"), z3.And(n["c"] >= 2, n["c"] <= 10)))
            for k in n["kids"]:
                walk(k, depth - 1)
        walk(self.nodes, self.depth)
        return cons

    def value(self, args):
        """symbolic value for concrete or symbolic argument list"""
        def ev(n):
            if n["kind"] == "bool":
                a, b = ev(n["kids"][0]), ev(n["kids"][1])
                return z3.If(n["op"] == 0, z3.BoolVal(True), z3.If(n["op"] == 1, a < b, a == b))
            if not n["kids"]:
                leaf = n["c"]
                for i in range(self.nvars):
                    leaf = z3.If(n["op"] == INT_OPS.index("var%d" % i), args[i], leaf)
                return leaf
            a, b = ev(n["kids"][0]), ev(n["kids"][1])
            v = z3.If(n["op"] == INT_OPS.index("const"), n["c"], a)
            for i in range(self.nvars):
                v = z3.If(n["op"] == INT_OPS.index("var%d" % i), args[i], v)
            v = z3.If(n["op"] == INT_OPS.index("add"), a + b, v)
            v = z3.If(n["op"] == INT_OPS.index("sub"), a - b, v)
            v = z3.If(n["op"] == INT_OPS.index("min"), z3.If(a < b, a, b), v)
            v = z3.If(n["op"] == INT_OPS.index("max"), z3.If(a < b, b, a), v)
            r_ = z3.SRem(a, n["c"])
            v = z3.If(n["op"] == INT_OPS.index("mod"), z3.If(r_ < 0, r_ + n["c"], r_), v)
            return v
        return ev(self.nodes)

    def concrete(self, model):
        """an executable Python function and a readable form from a solver model"""
        def get(n):
            op = model.eval(n["op"], model_completion=True).as_long()
            c = model.eval(n["c"], model_completion=True).as_signed_long()
            return op, c, [get(k) for k in n["kids"]]
        t = get(self.nodes)
        kind = self.kind
        nv = self.nvars

        def run(t, args, kind):
            op, c, kids = t
            if kind == "bool":
                a, b = run(kids[0], args, "int"), run(kids[1], args, "int")
                return True if op == 0 else (a < b if op == 1 else a == b)
            name = INT_OPS[op]
            if name.startswith("var"):
                return args[int(name[3])]
            if name == "const":
                return c
            a, b = run(kids[0], args, "int"), run(kids[1], args, "int")
            if name == "add":
                return a + b
            if name == "sub":
                return a - b
            if name == "min":
                return min(a, b)
            if name == "max":
                return max(a, b)
            return a % c

        def show(t, kind):
            op, c, kids = t
            if kind == "bool":
                return "true" if op == 0 else "(%s %s %s)" % ("lt" if op == 1 else "eq", show(kids[0], "int"),
                                                               show(kids[1], "int"))
            name = INT_OPS[op]
            if name.startswith("var"):
                return "$%s" % name[3]
            if name == "const":
                return str(c)
            if name == "mod":
                return "(mod %s %d)" % (show(kids[0], "int"), c)
            return "(%s %s %s)" % (name, show(kids[0], "int"), show(kids[1], "int"))
        return (lambda *args: run(t, args, kind)), show(t, kind), t


def _size(t, kind):
    op, c, kids = t
    if kind == "bool":
        return 1 if op == 0 else 1 + _size(kids[0], "int") + _size(kids[1], "int")
    name = INT_OPS[op]
    if name.startswith("var") or name == "const":
        return 1
    return 1 + _size(kids[0], "int") + _size(kids[1], "int")


class JointModel:
    """The constraint problem over a prefix tree of observations."""

    def __init__(self, depth_u=2, depth_v=1, depth_c=2, canon=False, ops_allowed=None):
        self.U = Tree("U", depth_u, 2)                 # U(h, x)
        self.V = Tree("V", depth_v, 3)                 # V(h, h', x)
        self.C = Tree("C", depth_c, 3, kind="bool")    # C(h, h', x)
        self.z0 = z3.BitVec("z0", BITS)
        self.h = {}
        self.solver = z3.Solver()
        for t in (self.U, self.V, self.C):
            self.solver.add(*t.wellformed(canon=canon, ops_allowed=ops_allowed))
        self.solver.add(self.z0 >= -CMAX, self.z0 <= CMAX)
        self.h[()] = self.z0
        self.n_obs = 0

    def hvar(self, u):
        if u not in self.h:
            parent = u[:-1]
            hp = self.hvar(parent)
            hv = z3.BitVec("h_%d" % len(self.h), BITS)
            self.solver.add(hv == self.U.value([hp, z3.BitVecVal(u[-1], BITS)]))
            self.h[u] = hv
        return self.h[u]

    def observe_step(self, u, e, piece):
        """the answer after u.e extends the answer after u by `piece` (a tuple of 0 or 1 integers)"""
        h, h2 = self.hvar(u), self.hvar(u + (e,))
        ev = z3.BitVecVal(e, BITS)
        cond = self.C.value([h, h2, ev])
        if len(piece) == 0:
            self.solver.add(z3.Not(cond))
        elif len(piece) == 1:
            self.solver.add(cond, self.V.value([h, h2, ev]) == z3.BitVecVal(piece[0], BITS))
        else:
            self.solver.add(z3.BoolVal(False))
        self.n_obs += 1

    def solve(self, timeout_ms):
        self.solver.set("timeout", max(1, int(timeout_ms)))
        r = self.solver.check()
        if r != z3.sat:
            return None, str(r)
        m = self.solver.model()
        u, us, ut = self.U.concrete(m)
        v, vs, vt = self.V.concrete(m)
        c, cs, ct = self.C.concrete(m)
        z0 = m.eval(self.z0, model_completion=True).as_signed_long()
        sol = {"U": u, "V": v, "C": c, "z0": z0, "show": {"U": us, "V": vs, "C": cs, "z0": z0},
               "size": _size(ut, "int") + _size(vt, "int") + _size(ct, "bool"), "trees": (ut, vt, ct)}
        return sol, "sat"


def run_solution(sol, x):
    h, out = sol["z0"], []
    for e in x:
        h2 = sol["U"](h, e)
        if sol["C"](h, h2, e):
            out.append(sol["V"](h, h2, e))
        h = h2
    return tuple(out)


def solve_cegis(observations, deadline, depth_u=2, depth_v=1, depth_c=2, start=6):
    """Counterexample-guided joint synthesis: the constraint problem grows only by the observations the current
    candidate gets wrong.  observations: [(u, e, piece)].  Returns (solution or None, info)."""
    obs = sorted(observations, key=lambda o: (len(o[0]), o[0], o[1]))
    M = JointModel(depth_u, depth_v, depth_c)
    used = set()

    def add(i):
        if i not in used:
            used.add(i)
            u, e, piece = obs[i]
            M.observe_step(u, e, piece)
    step = max(1, len(obs) // start)
    for i in range(0, len(obs), step):
        add(i)
    rounds = 0
    while time.process_time() < deadline:
        rounds += 1
        sol, st = M.solve((deadline - time.process_time()) * 1000)
        if sol is None:
            return None, {"status": st, "rounds": rounds, "constraints": len(used)}
        bad = []
        for i, (u, e, piece) in enumerate(obs):
            try:
                ok = run_solution(sol, tuple(u) + (e,))[len(run_solution(sol, tuple(u))):] == tuple(piece)
            except Exception:
                ok = False
            if not ok:
                bad.append(i)
        if not bad:
            return sol, {"status": "sat", "rounds": rounds, "constraints": len(used)}
        for i in bad[:3]:
            add(i)
    return None, {"status": "time", "rounds": rounds, "constraints": len(used)}


def observe_sequence(M, x, y, key):
    """Whole-output constraint (no prefix answer needed): running the machine over x emits exactly y.  A symbolic
    emission counter aligns the pieces with the observed list."""
    h = M.z0
    pos = z3.BitVecVal(0, BITS)
    cons = []
    for t, e in enumerate(x):
        ev = z3.BitVecVal(e, BITS)
        h2 = z3.BitVec("s%s_h%d" % (key, t), BITS)
        cons.append(h2 == M.U.value([h, ev]))
        c = M.C.value([h, h2, ev])
        v = M.V.value([h, h2, ev])
        hit = z3.BoolVal(False)
        for j, yj in enumerate(y):
            hit = z3.Or(hit, z3.And(pos == j, v == z3.BitVecVal(yj, BITS)))
        cons.append(z3.Implies(c, hit))
        pos = pos + z3.If(c, z3.BitVecVal(1, BITS), z3.BitVecVal(0, BITS))
        h = h2
    cons.append(pos == len(y))
    M.solver.add(*cons)
    M.n_obs += 1


def synthesise(sequences, deadline, depth_u=2, depth_v=1, depth_c=2, case_timeout=3.0):
    """Joint synthesis of (z0, U, V, C) from whole input/output sequences [(x, y)] -- the latent values are solver
    unknowns.  The structure's top operators are split into cases (smallest first); each case is solved by
    counterexample-guided growth of the constraint set.  Returns (solution, info)."""
    seqs = sorted(dict.fromkeys((tuple(x), tuple(y)) for x, y in sequences), key=lambda s: (len(s[0]), s))
    info = {"cases": 0, "status": []}
    cases = [(u, c) for c in (0, 1, 2) for u in INT_OPS if u not in ("var2",)]
    for uroot, croot in cases:
        if time.process_time() > deadline:
            info["stop"] = "deadline"
            break
        info["cases"] += 1
        M = JointModel(depth_u, depth_v, depth_c)
        M.solver.add(M.U.nodes["op"] == INT_OPS.index(uroot), M.C.nodes["op"] == croot)
        used = set()
        for i in range(0, len(seqs), max(1, len(seqs) // 3)):
            used.add(i)
            observe_sequence(M, seqs[i][0], seqs[i][1], i)
        end = min(deadline, time.process_time() + case_timeout)
        sol = None
        while time.process_time() < end:
            M.solver.set("timeout", max(1, int((end - time.process_time()) * 1000)))
            r = M.solver.check()
            if r != z3.sat:
                info["status"].append((uroot, croot, str(r)))
                break
            m = M.solver.model()
            cand = {}
            for nm, tree in (("U", M.U), ("V", M.V), ("C", M.C)):
                fn, sh, tr = tree.concrete(m)
                cand[nm], cand[nm + "_show"], cand[nm + "_t"] = fn, sh, tr
            cand["z0"] = m.eval(M.z0, model_completion=True).as_signed_long()
            sol_ = {"U": cand["U"], "V": cand["V"], "C": cand["C"], "z0": cand["z0"],
                    "show": {"U": cand["U_show"], "V": cand["V_show"], "C": cand["C_show"], "z0": cand["z0"]},
                    "size": _size(cand["U_t"], "int") + _size(cand["V_t"], "int") + _size(cand["C_t"], "bool")}
            bad = [i for i, (x, y) in enumerate(seqs) if i not in used and _safe_run(sol_, x) != y]
            if not bad:
                sol = sol_
                break
            for i in bad[:2]:
                used.add(i)
                observe_sequence(M, seqs[i][0], seqs[i][1], i)
        if sol is not None:
            info["case"] = (uroot, ["true", "lt", "eq"][croot])
            return sol, info
    return None, info


def _safe_run(sol, x):
    try:
        return run_solution(sol, x)
    except Exception:
        return None


def _internal_count(tree):
    """symbolic number of internal operator nodes (add, sub, min, max, mod for integers; lt, eq for conditions)"""
    total = []

    def walk(n):
        if n["kind"] == "bool":
            total.append(z3.If(n["op"] == 0, z3.IntVal(0), z3.IntVal(1)))
        elif n["kids"]:
            total.append(z3.If(z3.Or([n["op"] == INT_OPS.index(o) for o in ("add", "sub", "min", "max", "mod")]),
                               z3.IntVal(1), z3.IntVal(0)))
        for k in n["kids"]:
            walk(k)
    walk(tree.nodes)
    return z3.Sum(total) if total else z3.IntVal(0)


def synthesise_by_size(sequences, deadline, max_ops=6, depth_u=2, depth_v=1, depth_c=2, size_timeout=4.0):
    """Joint synthesis in increasing total size (number of internal operators of U, V and C together): the smallest
    machine that reproduces every observed input/output sequence (counterexample-guided).  Returns (solution, info)."""
    seqs = sorted(dict.fromkeys((tuple(x), tuple(y)) for x, y in sequences), key=lambda s: (len(s[0]), s))
    info = {"sizes": []}
    for k in range(0, max_ops + 1):
        if time.process_time() > deadline:
            info["stop"] = "deadline"
            break
        M = JointModel(depth_u, depth_v, depth_c)
        M.solver.add(_internal_count(M.U) + _internal_count(M.V) + _internal_count(M.C) <= k)
        used = set()
        for i in range(0, len(seqs), max(1, len(seqs) // 3)):
            used.add(i)
            observe_sequence(M, seqs[i][0], seqs[i][1], i)
        end = min(deadline, time.process_time() + size_timeout)
        sol, st = None, "time"
        while time.process_time() < end:
            M.solver.set("timeout", max(1, int((end - time.process_time()) * 1000)))
            r = M.solver.check()
            if r != z3.sat:
                st = str(r)
                break
            m = M.solver.model()
            parts = {}
            for nm, tree in (("U", M.U), ("V", M.V), ("C", M.C)):
                parts[nm] = tree.concrete(m)
            sol_ = {"U": parts["U"][0], "V": parts["V"][0], "C": parts["C"][0],
                    "z0": m.eval(M.z0, model_completion=True).as_signed_long(),
                    "show": {nm: parts[nm][1] for nm in parts}, "size": k}
            sol_["show"]["z0"] = sol_["z0"]
            bad = [i for i, (x, y) in enumerate(seqs) if i not in used and _safe_run(sol_, x) != y]
            if not bad:
                sol, st = sol_, "sat"
                break
            for i in bad[:2]:
                used.add(i)
                observe_sequence(M, seqs[i][0], seqs[i][1], i)
        info["sizes"].append((k, st))
        if sol is not None:
            return sol, info
    return None, info


def synthesise_steps_by_size(steps, deadline, max_ops=6, depth_u=2, depth_v=1, depth_c=2, size_timeout=4.0,
                             start=6, regularities=True):
    """As synthesise_by_size, but from per-step observations [(u, e, piece)] (answers of observed prefixes): no
    alignment of emitted pieces is needed.  Counterexample-guided within each size."""
    obs = sorted(dict.fromkeys(steps), key=lambda o: (len(o[0]), o[0], o[1]))
    info = {"sizes": []}
    for k in range(0, max_ops + 1):
        if time.process_time() > deadline:
            info["stop"] = "deadline"
            break
        M = JointModel(depth_u, depth_v, depth_c)
        M.solver.add(_internal_count(M.U) + _internal_count(M.V) + _internal_count(M.C) <= k)
        if regularities:
            reg = output_regularities(obs)
            info["regularities"] = reg
            fix_regularities(M, reg)
        used = set(range(0, len(obs), max(1, len(obs) // start)))
        for i in sorted(used):
            M.observe_step(*obs[i])
        end = min(deadline, time.process_time() + size_timeout)
        sol, st = None, "time"
        while time.process_time() < end:
            M.solver.set("timeout", max(1, int((end - time.process_time()) * 1000)))
            r = M.solver.check()
            if r != z3.sat:
                st = str(r)
                break
            m = M.solver.model()
            parts = {nm: tree.concrete(m) for nm, tree in (("U", M.U), ("V", M.V), ("C", M.C))}
            sol_ = {"U": parts["U"][0], "V": parts["V"][0], "C": parts["C"][0],
                    "z0": m.eval(M.z0, model_completion=True).as_signed_long(),
                    "show": {nm: parts[nm][1] for nm in parts}, "size": k}
            sol_["show"]["z0"] = sol_["z0"]
            bad = []
            for i, (u, e, piece) in enumerate(obs):
                a, b = _safe_run(sol_, tuple(u)), _safe_run(sol_, tuple(u) + (e,))
                if a is None or b is None or b[len(a):] != tuple(piece) or b[:len(a)] != a:
                    bad.append(i)
            if not bad:
                sol, st = sol_, "sat"
                break
            for i in bad[:3]:
                if i not in used:
                    used.add(i)
                    M.observe_step(*obs[i])
        info["sizes"].append((k, st))
        if sol is not None:
            return sol, info
    return None, info


def output_regularities(steps):
    """Parts of the output rule the observations already fix (no query): every step emits one value -> the emit
    condition is constantly true; every emitted value is the element just read -> the emitted value is x."""
    pieces = [(e, p) for _, e, p in steps]
    always = bool(pieces) and all(len(p) == 1 for _, p in pieces)
    echo = any(len(p) == 1 for _, p in pieces) and all(p[0] == e for e, p in pieces if len(p) == 1)
    return {"always_emit": always, "emits_element": echo}


def fix_regularities(M, reg):
    if reg.get("always_emit"):
        M.solver.add(M.C.nodes["op"] == 0)
    if reg.get("emits_element"):
        M.solver.add(M.V.nodes["op"] == INT_OPS.index("var2"))


# ------------------------------------------------------------------ section 44: factored joint synthesis
# The same joint problem and the same operator range as above, decided without symbolic operator choice:
# * the STRUCTURE of the update U is enumerated once, in canonical form (commutative operands ordered, no constant-only
#   or self-cancelling subterms), smallest first -- equivalent structures are generated once;
# * for a structure and its constants, the latent trace of every observed prefix is computed (the latent values are
#   never given or queried); the JOINT constraint is that every observed output piece is a function of
#   (h, h', x) along those traces -- a structure failing it is refuted for every output rule at once;
# * only then the output rule (emit condition C, emitted value V) is constructed from the induced table, smallest
#   first, with its constants solved exactly from the table;
# * observed output regularities (always emits / emits the element) narrow V and C as HYPOTHESES: they are retracted
#   when no machine is found under them.
F_OPS = ("add", "sub", "min", "max", "mod")
COMM = ("add", "min", "max")


def _leaves(nv):
    return [("v", i) for i in range(nv)] + [("c",)]


def _canon_key(t):
    return repr(t)


def skeletons(nv, max_ops):
    """canonical integer expression structures over nv variables with <= max_ops operators ('c' = constant hole;
    mod's divisor is a hole of its own)"""
    by_size = {0: _leaves(nv)}
    for k in range(1, max_ops + 1):
        out = []
        for op in F_OPS:
            if op == "mod":
                for a in by_size[k - 1]:
                    if a != ("c",):
                        out.append(("mod", a))
                continue
            for i in range(0, k):
                for a in by_size[i]:
                    for b in by_size[k - 1 - i]:
                        if a == ("c",) and b == ("c",):
                            continue
                        if a == b and op in ("sub", "min", "max"):
                            continue
                        if op in COMM and _canon_key(a) > _canon_key(b):
                            continue
                        out.append((op, a, b))
        by_size[k] = list(dict.fromkeys(out))
    return by_size


def holes(t):
    if t[0] == "c":
        return 1
    if t[0] == "v":
        return 0
    if t[0] == "mod":
        return 1 + holes(t[1])
    return holes(t[1]) + holes(t[2])


def evaluate(t, args, consts):
    """Python semantics (unbounded integers; mod as Python's floored mod by a positive divisor)"""
    it = iter(consts)

    def ev(t):
        k = t[0]
        if k == "v":
            return args[t[1]]
        if k == "c":
            return next(it)
        if k == "mod":
            a = ev(t[1])
            return a % next(it)
        a, b = ev(t[1]), ev(t[2])
        if k == "add":
            return a + b
        if k == "sub":
            return a - b
        if k == "min":
            return min(a, b)
        return max(a, b)
    return ev(t)


def show_t(t, consts):
    it = iter(consts)

    def sh(t):
        k = t[0]
        if k == "v":
            return "$%d" % t[1]
        if k == "c":
            return str(next(it))
        if k == "mod":
            a = sh(t[1])
            return "(mod %s %d)" % (a, next(it))
        return "(%s %s %s)" % (k, sh(t[1]), sh(t[2]))
    return sh(t)


def _const_choices(t, crange):
    """constant assignments for the holes of t in order (mod divisors 2..10)"""
    import itertools
    kinds = []

    def walk(t):
        k = t[0]
        if k == "c":
            kinds.append(crange)
        elif k == "mod":
            walk(t[1])
            kinds.append(range(2, 11))
        elif k != "v":
            walk(t[1])
            walk(t[2])
    walk(t)
    return itertools.product(*kinds) if kinds else [()]


def compile_t(t, consts, nargs=2):
    """the expression as a Python function with the SAME semantics as evaluate() (unbounded integers, floored mod by
    a positive divisor) -- one closure call per step instead of a tree walk"""
    it = iter(consts)

    def src(t):
        k = t[0]
        if k == "v":
            return "a%d" % t[1]
        if k == "c":
            return "(%d)" % next(it)
        if k == "mod":
            a = src(t[1])
            return "((%s) %% %d)" % (a, next(it))
        a, b = src(t[1]), src(t[2])
        if k == "add":
            return "(%s + %s)" % (a, b)
        if k == "sub":
            return "(%s - %s)" % (a, b)
        return "%s(%s, %s)" % (k, a, b)
    return eval("lambda %s: %s" % (", ".join("a%d" % i for i in range(nargs)), src(t)))


def latent_trace(fn, z0, prefixes, hcap=200):
    """latent value after every observed prefix (prefixes sorted so that a prefix's parent comes first); None when a
    value leaves the bounded range"""
    hv = {(): z0}
    for u in prefixes:
        if u in hv:
            continue
        p = hv.get(u[:-1])
        if p is None:
            return None
        v = fn(p, u[-1])
        if not -hcap <= v <= hcap:
            return None
        hv[u] = v
    return hv


def latent_table(U, ucs, z0, steps, hcap=200):
    """the latent trace along every observed prefix and the induced table (h, h', x) -> piece; None on a conflict
    (the outputs are not a function of the latent: U is refuted for every output rule)"""
    hv = {(): z0}

    def h(u):
        if u in hv:
            return hv[u]
        p = h(u[:-1])
        if p is None:
            hv[u] = None
            return None
        v = evaluate(U, (p, u[-1]), ucs)
        hv[u] = v if -hcap <= v <= hcap else None
        return hv[u]
    tab = {}
    for u, e, piece in steps:
        a, b = h(u), h(u + (e,))
        if a is None or b is None:
            return None
        k = (a, b, e)
        if tab.setdefault(k, piece) != piece:
            return None
    return tab


def _hole_free_terms(nv, max_ops, divisors=range(2, 11)):
    """terms with no constant hole (mod divisors enumerated): [(show, fn)]"""
    out = []
    sk = skeletons(nv, max_ops)
    for k in range(max_ops + 1):
        for t in sk[k]:
            nh = holes(t)
            if t == ("c",):
                continue
            # only mod-divisor holes are allowed here
            def only_mod(t):
                if t[0] == "c":
                    return False
                if t[0] == "v":
                    return True
                if t[0] == "mod":
                    return only_mod(t[1])
                return only_mod(t[1]) and only_mod(t[2])
            if not only_mod(t):
                continue
            for cs in _const_choices(t, [0]):
                out.append((t, cs))
    return out


def output_rules(tab, reg, max_ops=1):
    """The output rules over (h, h', x) that reproduce the table, smallest first: emitted value V and emit condition
    C.  A term carries at most one additive constant, solved EXACTLY from the table (never enumerated): V = t + c
    needs y - t constant over emitting rows; C = (t > c) / (t < c) / (t == c) needs c inside the interval the rows
    allow.  Mod divisors 2..10 are enumerated.  Yields (C, V) = ((kind, term, c), (term, c)); several rules can fit
    the same table, the full examples decide."""
    rows = list(tab.items())
    if any(len(p) > 1 for _, p in rows):
        return
    emit = [(k, p[0]) for k, p in rows if len(p) == 1]
    silent = [k for k, p in rows if len(p) == 0]
    terms = _hole_free_terms(3, max_ops)
    vals = {}

    def tv(i, k):
        key = (i, k)
        if key not in vals:
            t, cs = terms[i]
            vals[key] = evaluate(t, k, cs)
        return vals[key]
    Vs = []
    order = [i for i, (t, cs) in enumerate(terms) if t == ("v", 2)] if reg.get("emits_element") else range(len(terms))
    for i in order:
        if not emit:
            Vs.append((i, 0))
            break
        d = {y - tv(i, k) for k, y in emit}
        if len(d) == 1:
            Vs.append((i, d.pop()))
    if not Vs:
        return
    Cs = []
    if not silent:
        Cs.append(("true", None, None))
    elif not reg.get("always_emit"):
        for i in range(len(terms)):
            te = [tv(i, k) for k, _ in emit]
            ts = [tv(i, k) for k in silent]
            if not te:                           # nothing emitted on the observed steps: never emit
                Cs.append(("ceq", i, max(ts) + 1))
                break
            lo, hi = max(ts), min(te)            # t > c on emitting rows, t <= c on silent rows
            if lo <= hi - 1:
                Cs.append(("cgt", i, lo))
            lo2, hi2 = max(te), min(ts)           # t < c on emitting rows, t >= c on silent rows
            if lo2 + 1 <= hi2:
                Cs.append(("clt", i, lo2 + 1))
            if len(set(te)) == 1 and te[0] not in ts:
                Cs.append(("ceq", i, te[0]))
    for C in Cs:
        for V in Vs:
            yield C, V


def output_rule(tab, reg, max_ops=1, crange=None):
    """the first rule of output_rules (kept for the section 44 measurements)"""
    return next(output_rules(tab, reg, max_ops), None)


def _apply_rule(rule, terms, args):
    (ck, ci, cc), (vi, vc) = rule
    t, cs = terms[vi]
    v = evaluate(t, args, cs) + vc
    if ck == "true":
        return True, v
    t2, cs2 = terms[ci]
    a = evaluate(t2, args, cs2)
    return (a > cc if ck == "cgt" else (a < cc if ck == "clt" else a == cc)), v


def _occam(r):
    """small magnitudes first (0, 1, -1, 2, -2, ...): a generic order, not a task constant"""
    return sorted(r, key=lambda v: (abs(v), -v))


def cbits(v):
    """description length of an integer constant (a generic Elias-style code: 0 is free, small magnitudes cheap)"""
    return 0 if v == 0 else 2 * abs(v).bit_length() + (1 if v < 0 else 0)


OP_BITS, HOLE_BITS = 4, 2


def _hole_kinds(t):
    out = []

    def walk(t):
        k = t[0]
        if k == "c":
            out.append("c")
        elif k == "mod":
            walk(t[1])
            out.append("d")
        elif k != "v":
            walk(t[1])
            walk(t[2])
    walk(t)
    return tuple(out)


def compile_param(t):
    """the update structure as lambda a0, a1, k0, k1, ...: the hole values are arguments (one compile per
    structure); same semantics as evaluate()"""
    n = [0]

    def src(t):
        k = t[0]
        if k == "v":
            return "a%d" % t[1]
        if k == "c":
            n[0] += 1
            return "k%d" % (n[0] - 1)
        if k == "mod":
            a = src(t[1])
            n[0] += 1
            return "((%s) %% k%d)" % (a, n[0] - 1)
        a, b = src(t[1]), src(t[2])
        if k == "add":
            return "(%s + %s)" % (a, b)
        if k == "sub":
            return "(%s - %s)" % (a, b)
        return "%s(%s, %s)" % (k, a, b)
    body = src(t)
    return eval("lambda a0, a1%s: %s" % ("".join(", k%d" % i for i in range(n[0])), body))


_COMBOS = {}


def _combos(kinds, crange, z0range):
    """every (hole values..., start) sorted by description length"""
    key = (kinds, tuple(crange), tuple(z0range))
    if key not in _COMBOS:
        import itertools
        lists = [list(crange) if k == "c" else list(range(2, 11)) for k in kinds] + [list(z0range)]
        _COMBOS[key] = sorted(((sum(cbits(v) for v in c), c) for c in itertools.product(*lists)),
                              key=lambda e: (e[0], [(abs(v), -v) for v in e[1]]))
    return _COMBOS[key]


def _check(fnU, ks, z0, rule, tfn, examples):
    (ck, ci, cc), (vi, vc) = rule
    fv = tfn[vi]
    fc = tfn[ci] if ck != "true" else None
    for x, y in examples:
        h, out = z0, []
        for e in x:
            h2 = fnU(h, e, *ks)
            if fc is None:
                out.append(fv(h, h2, e) + vc)
            else:
                a = fc(h, h2, e)
                if (a > cc) if ck == "cgt" else ((a < cc) if ck == "clt" else a == cc):
                    out.append(fv(h, h2, e) + vc)
            h = h2
        if tuple(out) != tuple(y):
            return False
    return True


def factored_synthesis(steps, examples, deadline, max_ops_u=2, crange=range(-20, 41), z0range=range(-20, 41),
                       want=3, max_holes_u=1, rule_cap=24, margin=2):
    """Joint synthesis, factored.  steps: [(u, e, piece)] observed (no latent value); examples: [(x, y)] checked in
    full.  Every (update structure, its constants, start value) is enumerated ONCE, in order of description length
    (operators, holes and constants priced together: OP_BITS per operator, HOLE_BITS per hole, cbits per value).
    Each fixes the latent trace; latents equal on every checked input are not searched again; the observed output
    pieces must be a function of (h, h', x) (one table check refutes the update for every output rule); the output
    rule's constants are solved exactly (output_rules) and the full examples decide.  Returns (machines, info):
    machines within `margin` bits of the shortest found, at most `want`."""
    import heapq
    obs = list(dict.fromkeys(steps))
    reg_all = output_regularities(obs)
    terms = _hole_free_terms(3, 1)
    tfn = [compile_t(t, cs, 3) for t, cs in terms]
    info = {"regularities": reg_all, "structures_tried": 0, "traces": 0, "tables_functional": 0,
            "equivalent_skipped": 0, "rules_checked": 0}
    found = []
    allp = set()
    for u in [u for u, e, _ in obs] + [u + (e,) for u, e, _ in obs] + [tuple(x) for x, _ in examples]:
        allp.update(u[:i] for i in range(len(u) + 1))
    prefixes = sorted(allp, key=lambda u: (len(u), u))     # the key covers every input checked: dedup is exact
    index = {u: n for n, u in enumerate(prefixes)}
    parent = [index[u[:-1]] if u else -1 for u in prefixes]
    elem = [u[-1] if u else None for u in prefixes]
    obs_ix = [(index[u], index[u + (e,)], e, piece) for u, e, piece in obs]
    sk = skeletons(2, max_ops_u)
    structs = []
    for k in range(max_ops_u + 1):
        for U in sk[k]:
            if U[0] == "c" or U == ("v", 0) or holes(U) > max_holes_u:
                continue
            kinds = _hole_kinds(U)
            structs.append((U, kinds, OP_BITS * k + HOLE_BITS * len(kinds), k))
    fns = {}
    for reg in (reg_all, {}):                       # observed regularities first; retracted if nothing fits
        seen = set()
        heap = []
        for si, (U, kinds, base, k) in enumerate(structs):
            lo = sum(cbits(2) if kd == "d" else 0 for kd in kinds)
            heapq.heappush(heap, (base + lo, si, -1))          # -1: combos not built yet
        best = None
        while heap:
            cost, si, pos = heapq.heappop(heap)
            if best is not None and cost > best + margin:
                break
            U, kinds, base, k = structs[si]
            combos = _combos(kinds, crange, z0range)
            if pos < 0:
                info["structures_tried"] += 1
                heapq.heappush(heap, (base + combos[0][0], si, 0))
                continue
            if pos + 1 < len(combos):
                heapq.heappush(heap, (base + combos[pos + 1][0], si, pos + 1))
            if time.process_time() > deadline:
                info["stop"] = "deadline"
                return found, info
            vals_ = combos[pos][1]
            ks, z0 = vals_[:-1], vals_[-1]
            if si not in fns:
                fns[si] = compile_param(U)
            fnU = fns[si]
            info["traces"] += 1
            hv = [z0] * len(prefixes)
            bad = False
            for n in range(1, len(prefixes)):
                v = fnU(hv[parent[n]], elem[n], *ks)
                if not -200 <= v <= 200:
                    bad = True
                    break
                hv[n] = v
            if bad:
                continue
            key = tuple(hv)
            if key in seen:                         # an equivalent latent on every checked input: not searched again
                info["equivalent_skipped"] += 1
                continue
            seen.add(key)
            tab = {}
            for a, b, e, piece in obs_ix:
                if tab.setdefault((hv[a], hv[b], e), piece) != piece:
                    tab = None
                    break
            if tab is None:
                continue
            info["tables_functional"] += 1
            for n_r, rule in enumerate(output_rules(tab, reg)):
                if n_r >= rule_cap:
                    break
                info["rules_checked"] += 1
                if _check(fnU, ks, z0, rule, tfn, examples):
                    m = {"U": U, "ucs": tuple(ks), "z0": z0, "rule": rule, "terms": terms, "size": k,
                         "bits": cost}
                    (ck, ci, cc), (vi, vc) = rule
                    vt, vcs = terms[vi]
                    vs = show_t(vt, vcs) + ("" if vc == 0 else " + %d" % vc)
                    if ck == "true":
                        cs_ = "true"
                    else:
                        ct, ccs = terms[ci]
                        cs_ = "(%s %s %d)" % ({"cgt": ">", "clt": "<", "ceq": "=="}[ck], show_t(ct, ccs), cc)
                    m["show"] = {"U": show_t(U, ks), "z0": z0, "V": vs, "C": cs_}
                    found.append(m)
                    best = cost if best is None else best
                    if len(found) >= want:
                        return found, info
                    break
        if found or not (reg_all.get("always_emit") or reg_all.get("emits_element")):
            break
        info["regularities_retracted"] = True
    return found, info


def run_factored(m, x):
    h, out = m["z0"], []
    for e in x:
        h2 = evaluate(m["U"], (h, e), m["ucs"])
        c, v = _apply_rule(m["rule"], m["terms"], (h, h2, e))
        if c:
            out.append(v)
        h = h2
    return tuple(out)


def distinguishing_inputs(machines, vals, rng, n=400, maxlen=8):
    """inputs on which the candidate machines predict different outputs (the experiment that tells them apart);
    drawn from the observed value range, shortest first"""
    xs = []
    for _ in range(n):
        x = tuple(rng.choice(vals) for _ in range(rng.randrange(1, maxlen)))
        outs = {run_factored(m, x) for m in machines}
        if len(outs) > 1:
            xs.append(x)
    return sorted(set(xs), key=lambda x: (len(x), x))
