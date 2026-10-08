"""Typed exact-integer representation programs and original-goal verification.

Compiler/canonicalization are infrastructure, not learned perspective discovery.
Polynomial equality is universal under declared Z semantics, not sampled I/O.
Unknown/budget-exceeding verification is never an accepted transformation.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


class ProgramError(ValueError):
    pass


def validate(program, max_nodes=8192):
    if not isinstance(program, dict) or set(program) != {"semantics", "inputs", "nodes", "outputs"}:
        raise ProgramError("Public representation schema only; no Oracle/metadata fields")
    if program["semantics"] != "exact_integer":
        raise ProgramError("Exact-integer semantics required")
    names, nodes, outputs = program["inputs"], program["nodes"], program["outputs"]
    if not isinstance(names, list) or not 1 <= len(names) <= 64 or any(not isinstance(x, str) or not x.isidentifier() for x in names) or len(set(names)) != len(names):
        raise ProgramError("Unique declared input names required")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= max_nodes:
        raise ProgramError("Program node budget exceeded")
    for i, node in enumerate(nodes):
        if not isinstance(node, list) or not node:
            raise ProgramError("Malformed node")
        if node[0] == "input" and len(node) == 2 and node[1] in names:
            continue
        if node[0] == "const" and len(node) == 2 and type(node[1]) is int and -(2**63) <= node[1] < 2**63:
            continue
        if node[0] in ("add", "mul") and len(node) == 3 and all(type(k) is int and 0 <= k < i for k in node[1:]):
            continue
        raise ProgramError("Unregistered constructor or non-topological reference")
    if not isinstance(outputs, list) or not 1 <= len(outputs) <= 8 or any(type(i) is not int or not 0 <= i < len(nodes) for i in outputs):
        raise ProgramError("Original ordered outputs required")
    return program


class Builder:
    """Hash-consed public term construction; no algebraic search or Oracle."""
    def __init__(self, inputs):
        self.inputs = list(inputs)
        self.nodes = []
        self.memo = {}

    def node(self, kind, *args):
        key = (kind, *args)
        if key not in self.memo:
            self.memo[key] = len(self.nodes)
            self.nodes.append(list(key))
        return self.memo[key]

    def input(self, name):
        return self.node("input", name)

    def const(self, n):
        return self.node("const", n)

    def add(self, a, b):
        return self.node("add", a, b)

    def mul(self, a, b):
        return self.node("mul", a, b)

    def combine(self, kind, terms):
        terms = list(terms)
        if not terms:
            return self.const(0 if kind == "add" else 1)
        # Balanced construction avoids arbitrary deep parser/compiler artifacts.
        while len(terms) > 1:
            terms = [self.node(kind, terms[i], terms[i + 1]) if i + 1 < len(terms) else terms[i]
                     for i in range(0, len(terms), 2)]
        return terms[0]

    def finish(self, outputs):
        return validate({"semantics": "exact_integer", "inputs": self.inputs,
                         "nodes": self.nodes, "outputs": list(outputs)})


def reachable_nodes(program):
    live = set(program["outputs"])
    for i in range(len(program["nodes"]) - 1, -1, -1):
        node = program["nodes"][i]
        if i in live and node[0] in ("add", "mul"):
            live.update(node[1:])
    return live


def polynomial_forms(program, max_terms=8192, max_product_work=2_000_000):
    validate(program)
    dim = len(program["inputs"])
    zero = (0,) * dim
    positions = {name: i for i, name in enumerate(program["inputs"])}
    forms = []
    work = 0
    live = reachable_nodes(program)
    for index, node in enumerate(program["nodes"]):
        if index not in live:
            forms.append(None)
            continue
        kind = node[0]
        if kind == "input":
            exponent = list(zero)
            exponent[positions[node[1]]] = 1
            poly = {tuple(exponent): 1}
        elif kind == "const":
            poly = {zero: node[1]} if node[1] else {}
        elif kind == "add":
            poly = forms[node[1]].copy()
            for exponent, coefficient in forms[node[2]].items():
                poly[exponent] = poly.get(exponent, 0) + coefficient
                if poly[exponent] == 0:
                    del poly[exponent]
        else:
            a, b = forms[node[1]], forms[node[2]]
            work += len(a) * len(b)
            if work > max_product_work:
                raise ProgramError("Polynomial verification work budget exceeded: UNKNOWN")
            poly = {}
            for p, ap in a.items():
                for q, bq in b.items():
                    exponent = tuple(i + j for i, j in zip(p, q))
                    poly[exponent] = poly.get(exponent, 0) + ap * bq
            poly = {p: c for p, c in poly.items() if c}
        if len(poly) > max_terms:
            raise ProgramError("Polynomial verification term budget exceeded: UNKNOWN")
        forms.append(poly)
    return [forms[i] for i in program["outputs"]]


def verify_original(original, candidate):
    begin = perf_counter()
    try:
        validate(original); validate(candidate)
        if original["inputs"] != candidate["inputs"] or len(original["outputs"]) != len(candidate["outputs"]):
            raise ProgramError("Original input/output interface changed")
        if original == candidate:
            accepted, authority = True, "IDENTICAL_ORIGINAL_PROGRAM"
        else:
            accepted = polynomial_forms(original) == polynomial_forms(candidate)
            authority = "EXACT_ORDERED_INTEGER_POLYNOMIAL_IDENTITY"
        return {"accepted": accepted, "authority": authority, "error": None,
                "verification_seconds": perf_counter() - begin}
    except ProgramError as exc:
        return {"accepted": False, "authority": "NOT_VERIFIED", "error": str(exc),
                "verification_seconds": perf_counter() - begin}


@dataclass
class CompiledProgram:
    function: object
    input_count: int
    add_calls: int
    mul_calls: int
    source: str

    def run(self, bindings):
        for row in bindings:
            if len(row) != self.input_count or any(type(x) is not int for x in row):
                raise ProgramError("Complete exact-integer input tuple required")
        return [self.function(row) for row in bindings]


def compile_program(program):
    """All arms share DCE, commutative hash-consing and constant identities.

    Source uses only generated temporary identifiers, integer literals and row
    positions. Public names/text are never interpolated into executable code.
    """
    validate(program)
    live = reachable_nodes(program)
    positions = {v: i for i, v in enumerate(program["inputs"])}
    remap, canonical, exprs = {}, {}, []
    lines = ["def execute(row):"]
    adds = muls = 0
    constants = {}
    for i, node in enumerate(program["nodes"]):
        if i not in live:
            continue
        kind = node[0]
        if kind in ("add", "mul"):
            a, b = sorted(remap[j] for j in node[1:])
            if kind == "add" and (constants.get(a) == 0 or constants.get(b) == 0):
                remap[i] = b if constants.get(a) == 0 else a
                continue
            if kind == "mul" and (constants.get(a) == 1 or constants.get(b) == 1):
                remap[i] = b if constants.get(a) == 1 else a
                continue
            if kind == "mul" and (constants.get(a) == 0 or constants.get(b) == 0):
                remap[i] = a if constants.get(a) == 0 else b
                continue
            key = (kind, a, b)
        else:
            key = tuple(node)
        if key in canonical:
            remap[i] = canonical[key]
            continue
        index = len(exprs)
        canonical[key] = remap[i] = index
        if kind == "input":
            expression = f"row[{positions[node[1]]}]"
        elif kind == "const":
            expression = str(node[1])
            constants[index] = node[1]
        else:
            expression = f"t{a} {'+' if kind == 'add' else '*'} t{b}"
            adds += kind == "add"
            muls += kind == "mul"
        exprs.append(expression)
        lines.append(f"    t{index} = {expression}")
    lines.append("    return (" + ",".join(f"t{remap[i]}" for i in program["outputs"]) + ",)")
    source = "\n".join(lines) + "\n"
    namespace = {"__builtins__": {}}
    exec(compile(source, "<validated_integer_program>", "exec"), namespace)
    return CompiledProgram(namespace["execute"], len(positions), adds, muls, source)


def sympy_transform(program, method):
    """Reuse strong CAS factor/collect/Horner and cross-output CSE."""
    import sympy as sp
    if sp.__version__ != "1.14.0" or method not in {"CSE", "FACTOR_CSE", "FACTOR_TERMS_CSE", "HORNER_CSE"}:
        raise ProgramError("Pinned CAS and declared transformation required")
    validate(program)
    symbols = {name: sp.Symbol(name) for name in program["inputs"]}
    values = []
    live = reachable_nodes(program)
    for index, n in enumerate(program["nodes"]):
        if index not in live:
            values.append(None)
            continue
        if n[0] == "input":
            e = symbols[n[1]]
        elif n[0] == "const":
            e = sp.Integer(n[1])
        elif n[0] == "add":
            e = values[n[1]] + values[n[2]]
        else:
            e = values[n[1]] * values[n[2]]
        values.append(e)
    outputs = [values[i] for i in program["outputs"]]
    if method == "FACTOR_CSE":
        outputs = [sp.factor(e) for e in outputs]
    elif method == "FACTOR_TERMS_CSE":
        outputs = [sp.factor_terms(e) for e in outputs]
    elif method == "HORNER_CSE":
        outputs = [sp.horner(e, *symbols.values()) for e in outputs]
    replacements, outputs = sp.cse(outputs, symbols=sp.numbered_symbols("_generated", cls=sp.Dummy), order="none")
    builder = Builder(program["inputs"])
    mapping = {s: builder.input(name) for name, s in symbols.items()}

    def convert(e):
        if e in mapping:
            return mapping[e]
        if e.is_Integer:
            value = builder.const(int(e))
        elif e.is_Add:
            value = builder.combine("add", [convert(a) for a in e.args])
        elif e.is_Mul:
            value = builder.combine("mul", [convert(a) for a in e.args])
        elif e.is_Pow and e.exp.is_Integer and 0 <= int(e.exp) <= 16:
            value = builder.combine("mul", [convert(e.base)] * int(e.exp))
        else:
            raise ProgramError("CAS output is outside exact-integer polynomial DSL")
        mapping[e] = value
        return value

    for symbol, expression in replacements:
        mapping[symbol] = convert(expression)
    return builder.finish([convert(e) for e in outputs])
