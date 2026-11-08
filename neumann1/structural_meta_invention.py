"""Live NEUMANN structural meta-invention.

Mine *new executable program generators* from two source-certified ASTs.
The two recurrence directions are GENERIC tree operations, not named
max/fold/scan templates. Newly learned contexts immediately become runtime
candidate generators, ranked by independently verified outcomes.

Syntactic recurrence is only a hypothesis. No target is accepted without
the injected original-semantics verifier. The meta-search language itself
remains human-implemented; universal autonomous Q3 is NOT implied.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
import hashlib
import json
from .meta_utility_policy import MetaUtilityEvidence, decide_meta_method, source_evidence_dict

Expr = tuple[Any, ...]


def _validate(ast: Any) -> Expr:
    memo = {}

    def check(x):
        if not isinstance(x, (list, tuple)) or not x:
            raise TypeError("nonempty expression AST required")
        if id(x) in memo:
            return memo[id(x)]
        op = x[0]
        if type(op) is not str or not op:
            raise TypeError("operation must be a string")
        if op == "arg":
            if len(x) != 2 or type(x[1]) is not int or x[1] < 0:
                raise ValueError("arg requires nonnegative index")
            node = ("arg", x[1])
        elif op == "lit":
            if len(x) != 2 or type(x[1]) not in (int, str, bool):
                raise ValueError("unsupported literal")
            node = ("lit", x[1])
        else:
            if op.startswith("_meta_") or len(x) < 2:
                raise ValueError("reserved or zero-arity operator")
            node = (op, *(check(y) for y in x[1:]))
        memo[id(x)] = node
        return node

    return check(ast)


def _nodes(ast):
    seen = set()
    stack = [ast]
    while stack:
        item = stack.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        yield item
        stack.extend(x for x in item[1:] if isinstance(x, tuple))


def _size(ast):
    return sum(1 for _ in _nodes(ast))


def _expanded_size(ast, cap):
    """Bound cost for target adapters that serialize a shared DAG as a tree."""
    memo = {}

    def count(node):
        ident = id(node)
        if ident in memo:
            return memo[ident]
        size = 1
        for child in node[1:]:
            if isinstance(child, tuple):
                size = min(cap + 1, size + count(child))
            if size > cap:
                break
        memo[ident] = size
        return size

    return count(ast)


def _args(ast):
    return {x[1] for x in _nodes(ast) if x[0] == "arg"}


def _hash(data):
    return hashlib.sha256(json.dumps(
        data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _map_constants(ast, constants):
    if ast[0] == "lit" and ast[1] in constants:
        return ("_meta_param", constants[ast[1]])
    if ast[0] in ("arg", "lit", "_meta_param"):
        return ast
    return (ast[0], *(_map_constants(x, constants) for x in ast[1:]))


def _shift(ast, delta, memo=None):
    if memo is None:
        memo = {}
    if id(ast) in memo:
        return memo[id(ast)]
    if ast[0] == "arg":
        idx = ast[1] + delta
        if idx < 0:
            raise ValueError("negative shifted argument")
        out = ("arg", idx)
    elif ast[0] in ("lit", "_meta_param", "_meta_hole", "_meta_new"):
        out = ast
    else:
        out = (ast[0], *(_shift(x, delta, memo) for x in ast[1:]))
    memo[id(ast)] = out
    return out


def _reindex_with_fresh(ast, old_arity, insertion_index, reverse=False, memo=None):
    """Execute an automatically inferred argument-alignment PROGRAM.

    Old argument positions are embedded in an enlarged arity by inserting
    one fresh argument at any index, with optional reversal. This transforms
    a whole prior solution, not a named task-specific algorithm.
    """
    if type(insertion_index) is not int or not 0 <= insertion_index <= old_arity:
        raise ValueError("insertion index out of range")
    if memo is None:
        memo = {}
    if id(ast) in memo:
        return memo[id(ast)]
    if ast[0] == "arg":
        index = ast[1]
        if not 0 <= index < old_arity:
            raise ValueError("source argument outside old arity")
        index = old_arity - 1 - index if reverse else index
        out = ("arg", index + int(index >= insertion_index))
    elif ast[0] in ("lit", "_meta_param", "_meta_hole", "_meta_new"):
        out = ast
    else:
        out = (ast[0], *(_reindex_with_fresh(
            child, old_arity, insertion_index, reverse, memo)
            for child in ast[1:]))
    memo[id(ast)] = out
    return out


def _extract(outer, repeated):
    if outer == repeated:
        return ("_meta_hole",), 1
    if outer[0] in ("arg", "lit", "_meta_param"):
        return outer, 0
    children = [_extract(x, repeated) for x in outer[1:]]
    return (outer[0], *(x[0] for x in children)), sum(x[1] for x in children)


def _fresh_to_marker(ast, fresh):
    if ast == ("arg", fresh):
        return ("_meta_new",)
    if ast[0] in ("arg", "lit", "_meta_param", "_meta_hole"):
        return ast
    return (ast[0], *(_fresh_to_marker(x, fresh) for x in ast[1:]))


def _materialize(ast, previous, fresh, parameters, memo=None):
    if memo is None:
        memo = {}
    if id(ast) in memo:
        return memo[id(ast)]
    op = ast[0]
    if op == "_meta_hole":
        result = previous
    elif op == "_meta_new":
        result = ("arg", fresh)
    elif op == "_meta_param":
        if ast[1] >= len(parameters):
            raise ValueError("missing target method parameter")
        result = ("lit", parameters[ast[1]])
    elif op in ("arg", "lit"):
        result = ast
    else:
        result = (op, *(_materialize(x, previous, fresh, parameters, memo)
                        for x in ast[1:]))
    memo[id(ast)] = result
    return result


@dataclass(frozen=True)
class CertifiedProgram:
    family: str
    arity: int
    expr: Expr
    certificate: str
    params: tuple = ()

    def __post_init__(self):
        if not self.family or type(self.arity) is not int or self.arity < 1:
            raise ValueError("valid family and arity required")
        if type(self.certificate) is not str or not self.certificate:
            raise ValueError("real original-source certificate required")
        cleaned = _validate(self.expr)
        if any(i >= self.arity for i in _args(cleaned)):
            raise ValueError("source expression references nonexistent argument")
        object.__setattr__(self, "expr", cleaned)


@dataclass
class InventedMethod:
    family: str
    source_arity: int
    direction: str
    base: Expr
    context: Expr
    parameters: int
    source_hash: str
    insertion_index: int = -1
    reverse: bool = False
    successes: int = 0
    failures: int = 0
    verifier_queries: int = 0

    @property
    def identity(self):
        # Keep historical append/prepend identities stable for checkpoints.
        identity = (self.family, self.direction, self.base, self.context,
                    self.parameters, self.source_hash)
        if self.direction in ("insert", "permuted_insert"):
            identity = (*identity, self.insertion_index, self.reverse)
        return _hash(identity)

    def generate(self, arity: int, params: tuple = ()) -> Expr:
        if type(arity) is not int or arity < self.source_arity:
            raise ValueError("arity below source program")
        if len(params) != self.parameters:
            raise ValueError("parameter binding count mismatch")
        out = _materialize(self.base, self.base, 0, params)
        for n in range(self.source_arity, arity):
            if self.direction == "append":
                out = _materialize(self.context, out, n, params)
            elif self.direction == "prepend":
                out = _materialize(self.context, _shift(out, 1), 0, params)
            elif self.direction in ("insert", "permuted_insert"):
                if self.insertion_index >= n + 1:
                    raise ValueError("insertion index invalid for arity")
                previous = _reindex_with_fresh(
                    out, n, self.insertion_index, self.reverse)
                out = _materialize(
                    self.context, previous, self.insertion_index, params)
            else:
                raise AssertionError("unknown learned method direction")
        if any(i >= arity for i in _args(out)):
            raise AssertionError("generated argument index escaped arity")
        return out


class StructuralMetaInventor:
    """Mutable LIVE inventory of new program-constructor methods.

    Source and target verification are callbacks owned by the user's actual
    problem checker. No syntactic matching is treated as correctness proof.
    """

    def __init__(self, max_nodes=20000, max_arity=128):
        if type(max_nodes) is not int or max_nodes < 1:
            raise ValueError("positive node budget required")
        if type(max_arity) is not int or max_arity < 2:
            raise ValueError("arity cap must be >=2")
        self.max_nodes = max_nodes
        self.max_arity = max_arity
        self.methods: dict[str, InventedMethod] = {}
        self.observations: dict[str, dict[int, CertifiedProgram]] = defaultdict(dict)
        self.meta_utility_evidence: dict[str, dict] = {}

    def learn(self, smaller: CertifiedProgram, larger: CertifiedProgram, *,
              verify: Callable[[CertifiedProgram], bool]) -> list[InventedMethod]:
        if smaller.family != larger.family or larger.arity != smaller.arity + 1:
            raise ValueError("certified adjacent source programs required")
        if larger.arity > self.max_arity:
            raise ValueError("source exceeds arity cap")
        if verify(smaller) is not True or verify(larger) is not True:
            return []
        if (_expanded_size(smaller.expr, self.max_nodes) > self.max_nodes or
                _expanded_size(larger.expr, self.max_nodes) > self.max_nodes):
            return []  # DAG is compact, but naive target serialization may not be.
        a = {x[1] for x in _nodes(smaller.expr) if
             x[0] == "lit" and type(x[1]) is int and x[1] not in (0, 1)}
        b = {x[1] for x in _nodes(larger.expr) if
             x[0] == "lit" and type(x[1]) is int and x[1] not in (0, 1)}
        constants = tuple(sorted(a & b))
        # Parameter identity is structural; its observed numeric value may
        # change from one certified program to the next. Preserve the slot,
        # not the observed source value (e.g. threshold 5 -> threshold 15).
        if smaller.params or larger.params:
            if len(smaller.params) != len(larger.params):
                return []
            if any(v in (0, 1) for v in smaller.params + larger.params):
                return []  # avoid abstracting structural literal 0/1
            old_slots = {v: i for i, v in enumerate(smaller.params)}
            new_slots = {v: i for i, v in enumerate(larger.params)}
            parameter_count = len(smaller.params)
            reconstruction_parameters = larger.params
        else:
            old_slots = new_slots = {v: i for i, v in enumerate(constants)}
            parameter_count = len(constants)
            reconstruction_parameters = constants
        base = _map_constants(smaller.expr, old_slots)
        extended = _map_constants(larger.expr, new_slots)
        invented = []
        # Search over EDIT OPERATORS themselves: the expanded program
        # determines WHERE an old argument sequence is embedded and whether
        # its order is reversed. Previously only the two endpoints were
        # representable, so genuine interior insertion was impossible.
        #
        # The discovered reindexing program is persisted with its context.
        for reverse in (False, True):
            for insertion_index in range(smaller.arity + 1):
                previous = _reindex_with_fresh(
                    base, smaller.arity, insertion_index, reverse)
                context, count = _extract(extended, previous)
                if not count or insertion_index not in _args(context):
                    continue
                skeleton = _fresh_to_marker(context, insertion_index)
                if reverse:
                    direction = "permuted_insert"
                elif insertion_index == 0:
                    direction = "prepend"
                elif insertion_index == smaller.arity:
                    direction = "append"
                else:
                    direction = "insert"
                method = InventedMethod(
                    family=smaller.family, source_arity=smaller.arity,
                    direction=direction, base=base, context=skeleton,
                    parameters=parameter_count,
                    source_hash=_hash((smaller.certificate, larger.certificate)),
                    insertion_index=insertion_index,
                    reverse=reverse)
                if _size(base) + _size(skeleton) > self.max_nodes:
                    continue
                try:
                    if method.generate(
                            larger.arity, reconstruction_parameters) != larger.expr:
                        continue
                except (ValueError, AssertionError):
                    continue
                if method.identity not in self.methods:
                    self.methods[method.identity] = method
                    invented.append(method)
        # Store source evidence whether or not the bounded grammar can
        # represent its recurrence: future source solutions may extend it.
        self.observations[smaller.family][smaller.arity] = smaller
        self.observations[larger.family][larger.arity] = larger
        return invented

    def observe(self, source: CertifiedProgram, *,
                verify: Callable[[CertifiedProgram], bool]) -> list[InventedMethod]:
        if verify(source) is not True:
            return []
        known = self.observations[source.family]
        neighbors = [known[n] for n in (source.arity-1, source.arity+1)
                     if n in known]
        known[source.arity] = source
        new_methods = []
        for other in neighbors:
            low, high = sorted((source, other), key=lambda item: item.arity)
            new_methods.extend(self.learn(low, high, verify=verify))
        return new_methods

    def candidates(self, family, arity, *, params=()):
        if type(arity) is not int or not 1 <= arity <= self.max_arity:
            raise ValueError("invalid target arity")
        eligible = (m for m in self.methods.values()
                    if m.family == family and m.source_arity <= arity and
                    m.parameters == len(params))
        # This policy improves from verified outcome feedback, not fixed
        # family-specific operator names or a hardcoded fold/scan dispatch.
        order = sorted(eligible, key=lambda m:(
            -m.successes, m.failures, _size(m.context), m.identity))
        for method in order:
            try:
                expr = method.generate(arity, params)
                if (_size(expr) <= self.max_nodes and
                        _expanded_size(expr, self.max_nodes) <= self.max_nodes):
                    yield method, expr
            except (ValueError, AssertionError):
                continue

    def solve(self, family, arity, *, params=(), verify=None, promote=False):
        if verify is None:
            return None  # No original checker -> no unverified "success".
        for method, candidate in self.candidates(family, arity, params=params):
            method.verifier_queries += 1
            if verify(candidate) is True:
                method.successes += 1
                grown = []
                if promote:
                    evidence = CertifiedProgram(
                        family=family, arity=arity, expr=candidate,
                        params=params, certificate="verified:"+method.identity)
                    grown = self.observe(
                        evidence, verify=lambda item: item == evidence or
                        item in self.observations[family].values())
                return {"program": candidate, "method_id": method.identity,
                        "source_certificate_digest": method.source_hash,
                        "verified": True,
                        "new_method_ids": [m.identity for m in grown]}
            method.failures += 1
        return None

    def admit_meta_method_utility(self, family, evidence: MetaUtilityEvidence):
        """Record source-only capability + amortized compute admission.

        The discovery engine itself now learns when to DELETE a nonproductive
        method from an affected family's inference hot path. It never deletes
        retained source proof evidence; the policy can be updated when a
        new independent source study has better evidence.
        """
        if type(family) is not str or not family:
            raise ValueError("valid method family required")
        if not isinstance(evidence, MetaUtilityEvidence):
            raise TypeError("MetaUtilityEvidence required")
        verdict=decide_meta_method(evidence)
        self.meta_utility_evidence[family]=source_evidence_dict(evidence)
        return verdict

    def meta_utility_decision(self, family):
        evidence=self.meta_utility_evidence.get(family)
        return decide_meta_method(
            MetaUtilityEvidence(**evidence)) if evidence is not None else None

    def solve_or_discover(self, family, arity, *, params=(), verify=None,
                          classical=None):
        """Original-verified CLASSICAL FIRST; invention only for measured gains or gaps.

        The default prior is economical: do not invoke an uncalibrated
        method inventer before an available trusted classic solver.
        A source-verified positive-utility policy may explicitly admit
        INVENTED_FIRST.  If cold fails and there is no negative utility
        policy, a learned constructor is permitted to attempt the gap.
        All success must pass the actual target original verifier.
        """
        if verify is None or not callable(verify):
            return None
        if type(arity) is not int or not 1 <= arity <= self.max_arity:
            raise ValueError("invalid synthesis arity")
        if type(family) is not str or not family:
            raise ValueError("valid synthesis family required")
        if classical is not None and not callable(classical):
            raise TypeError("classical baseline must be a callable")
        params = tuple(params)
        decision = self.meta_utility_decision(family)
        invented_first = bool(decision and decision.use_invented_first)
        classical_attempted = False
        invented_attempts = 0

        def try_classical():
            nonlocal classical_attempted
            if classical is None or classical_attempted:
                return None
            classical_attempted = True
            proposed = classical(arity, params)
            if proposed is None:
                return None
            try:
                program = _validate(proposed)
            except (TypeError, ValueError):
                return None
            if (any(i >= arity for i in _args(program)) or
                    _size(program) > self.max_nodes or
                    _expanded_size(program, self.max_nodes) > self.max_nodes):
                return None
            if verify(program) is not True:
                return None
            source = CertifiedProgram(
                family=family, arity=arity, expr=program, params=params,
                certificate="original-verifier:" +
                            _hash((family, arity, params, program)))
            discovered = self.observe(
                source, verify=lambda p:
                    p == source or p in self.observations[p.family].values())
            return {"program": program, "verified": True,
                    "origin": "classical_verified_then_learned",
                    "method_id": None,
                    "source_certificate_digest": source.certificate,
                    "method_queries": invented_attempts,
                    "classical_invocations": 1,
                    "new_method_ids": [m.identity for m in discovered]}

        # A known solver with an original-semantic checker is tried first
        # unless an independent source-only cost/capability gate admits
        # invented-first search.
        if not invented_first:
            result = try_classical()
            if result is not None:
                return result

        # A source study with negative amortized utility deletes the
        # inventor from the hot path, even if the classical algorithm
        # fails on a different problem instance.
        inventor_allowed = decision is None or decision.use_invented_first
        if inventor_allowed:
            before = sum(m.verifier_queries for m in self.methods.values())
            learned = self.solve(
                family, arity, params=params, verify=verify, promote=True)
            method_queries = (
                sum(m.verifier_queries for m in self.methods.values()) - before)
            invented_attempts += method_queries
            if learned is not None:
                return {**learned, "origin": "self_invented_method",
                        "method_queries": method_queries,
                        "classical_invocations": int(classical_attempted)}
        if invented_first:
            return try_classical()
        return None

    def checkpoint(self):
        """Serialize learned method PROGRAMS, not cached target solutions.

        The SHA detects accidental state drift. It does not authenticate an
        untrusted writer; all restored proposals still need target proof.
        """
        rows = []
        for m in sorted(self.methods.values(), key=lambda x: x.identity):
            rows.append({
                "family": m.family, "source_arity": m.source_arity,
                "direction": m.direction, "base": m.base,
                "context": m.context, "parameters": m.parameters,
                "source_hash": m.source_hash,
                "insertion_index": m.insertion_index,
                "reverse": m.reverse,
                "successes": m.successes, "failures": m.failures,
                "verifier_queries": m.verifier_queries,
            })
        # Keep certified observations, not only methods: after a restart a
        # new verified n+1 program must still be able to grow the discovery
        # language from the stored n program. Version 1 lost that ability.
        observed = []
        for family, family_observations in sorted(self.observations.items()):
            for arity, p in sorted(family_observations.items()):
                observed.append({
                    "family": p.family, "arity": arity, "expr": p.expr,
                    "params": p.params, "certificate": p.certificate,
                })
        state = {"schema": "neumann.structural-meta-methods.v2",
                 "max_nodes": self.max_nodes, "max_arity": self.max_arity,
                 "methods": rows, "observations": observed,
                 "source_only_meta_utility": self.meta_utility_evidence}
        state["sha256"] = _hash(state)
        return state

    @classmethod
    def from_checkpoint(cls, checkpoint):
        """Restore verified-USE-ONLY method grammar; never deserialize code."""
        if (type(checkpoint) is not dict or checkpoint.get("schema") not in (
                "neumann.structural-meta-methods.v1",
                "neumann.structural-meta-methods.v2")):
            raise ValueError("unsupported method checkpoint")
        payload = {k:v for k,v in checkpoint.items() if k != "sha256"}
        if _hash(payload) != checkpoint.get("sha256"):
            raise ValueError("method checkpoint checksum failure")
        inventory = cls(max_nodes=payload["max_nodes"],
                        max_arity=payload["max_arity"])
        if type(payload["methods"]) is not list or len(payload["methods"]) > 256:
            raise ValueError("invalid method count")

        def ast(value):
            if not isinstance(value, (tuple, list)) or not value or type(value[0]) is not str:
                raise ValueError("invalid method AST")
            op = value[0]
            if op in ("_meta_hole", "_meta_new"):
                if len(value) != 1:
                    raise ValueError("malformed method hole")
                return (op,)
            if op == "_meta_param":
                if len(value) != 2 or type(value[1]) is not int or value[1] < 0:
                    raise ValueError("malformed method parameter")
                return (op, value[1])
            if op == "arg":
                if len(value) != 2 or type(value[1]) is not int or value[1] < 0:
                    raise ValueError("invalid argument")
                return ("arg", value[1])
            if op == "lit":
                if len(value) != 2 or type(value[1]) not in (int, bool, str):
                    raise ValueError("invalid literal")
                return ("lit", value[1])
            if op.startswith("_meta_") or len(value) < 2:
                raise ValueError("unsupported method expression")
            return (op, *(ast(x) for x in value[1:]))

        for row in payload["methods"]:
            if type(row) is not dict:
                raise ValueError("invalid method record")
            m = InventedMethod(
                family=row["family"], source_arity=row["source_arity"],
                direction=row["direction"], base=ast(row["base"]),
                context=ast(row["context"]), parameters=row["parameters"],
                source_hash=row["source_hash"],
                insertion_index=row.get("insertion_index", -1),
                reverse=row.get("reverse", False),
                successes=row["successes"],
                failures=row["failures"],
                verifier_queries=row["verifier_queries"])
            if m.direction not in (
                    "append", "prepend", "insert", "permuted_insert"
            ) or m.source_arity < 1:
                raise ValueError("invalid learned method")
            if m.direction in ("insert", "permuted_insert"):
                if (type(m.insertion_index) is not int or
                        not 0 <= m.insertion_index <= m.source_arity or
                        type(m.reverse) is not bool or
                        m.reverse != (m.direction == "permuted_insert")):
                    raise ValueError("invalid learned alignment")
            if type(m.parameters) is not int or m.parameters < 0:
                raise ValueError("invalid method parameters")
            if _size(m.base) + _size(m.context) > inventory.max_nodes:
                raise ValueError("oversized method")
            if any(type(x) is not int or x < 0 for x in
                   (m.successes, m.failures, m.verifier_queries)):
                raise ValueError("invalid method costs")
            inventory.methods[m.identity] = m
        if checkpoint["schema"] == "neumann.structural-meta-methods.v2":
            records = payload.get("observations")
            if type(records) is not list or len(records) > 512:
                raise ValueError("invalid certified observation count")
            for record in records:
                if type(record) is not dict or set(record) != {
                        "family", "arity", "expr", "params", "certificate"}:
                    raise ValueError("invalid certified source record")
                if type(record["params"]) not in (list, tuple):
                    raise ValueError("bad source parameter slots")
                source = CertifiedProgram(
                    family=record["family"], arity=record["arity"],
                    expr=ast(record["expr"]),
                    params=tuple(record["params"]),
                    certificate=record["certificate"])
                if (source.arity > inventory.max_arity or
                        _expanded_size(source.expr, inventory.max_nodes) >
                        inventory.max_nodes):
                    raise ValueError("unsafe stored source AST size")
                if source.arity in inventory.observations[source.family]:
                    raise ValueError("duplicate source observation")
                inventory.observations[source.family][source.arity] = source
        evidence=payload.get("source_only_meta_utility", {})
        if type(evidence) is not dict or len(evidence)>256:
            raise ValueError("invalid utility evidence inventory")
        for family, rec in evidence.items():
            if type(family) is not str or not family or type(rec) is not dict:
                raise ValueError("invalid utility family or source record")
            # Recompute, never trust an unverified stored admission flag.
            typed=MetaUtilityEvidence(**rec)
            inventory.admit_meta_method_utility(family,typed)
        return inventory
