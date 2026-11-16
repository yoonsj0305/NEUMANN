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

    def wellformed(self):
        cons = []

        def walk(n, depth):
            ops = BOOL_OPS if n["kind"] == "bool" else INT_OPS
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

    def __init__(self, depth_u=2, depth_v=1, depth_c=2):
        self.U = Tree("U", depth_u, 2)                 # U(h, x)
        self.V = Tree("V", depth_v, 3)                 # V(h, h', x)
        self.C = Tree("C", depth_c, 3, kind="bool")    # C(h, h', x)
        self.z0 = z3.BitVec("z0", BITS)
        self.h = {}
        self.solver = z3.Solver()
        for t in (self.U, self.V, self.C):
            self.solver.add(*t.wellformed())
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
