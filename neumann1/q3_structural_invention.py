"""Q3 unified structural invention: learned operator selection + executable search.

This is ONE task-agnostic discovery policy for the already existing Python
`def transform(x)` substrate, not ARC/string/math family-specific inventors.
An operator prior is fitted from prior independently SOURCE-certified original
model-authored programs. Frozen weights alter the *discovery procedure*
(operator expansion order and expression cost), not a stored target answer.

The compiler composes new executable expressions from small general Python
operations. All intermediate hypotheses are evaluated by a bounded pure
interpreter for search; all accepted programs MUST subsequently pass the
existing independent, no-network Docker original SOURCE verifier. SOURCE
checks and TARGET outputs are never seen by the hypothesis generator.

Scientific status: a new program not in memory is only a *candidate*
invention. Global Q3 requires additional independent-author ORIGINAL exact
wins over identical-budget strong classical + memorization controls in two
unrelated semantic families. This module NEVER declares that global gate.
"""
from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass, field
import json
from time import monotonic
from typing import Any, Iterable

from .open_program_inventor import source_same_value, validate_code
from .q3_structure_factorization import induce_structural_factors
from .q3_object_graph_invention import induce_object_graph_factors
from .q3_source_residual_probes import induce_source_residual_probes

_INVALID = object()

_UNARY = {
    "len": "len({})",
    "bool": "bool({})",
    "str": "str({})",
    "not": "(not ({}))",
    "first": "({})[0]",
    "second": "({})[1]",
    "last": "({})[-1]",
    "reverse": "({})[::-1]",
    "min": "min({})",
    "max": "max({})",
    "sum": "sum({})",
    "strip": "({}).strip()",
    "abs": "abs({})",
    "sorted": "sorted({})",
    "neg": "(-({}))",
}
_BINARY = {
    "in": "({} in {})",
    "eq": "({} == {})",
    "neq": "({} != {})",
    "mod": "({} % {})",
    "add": "({} + {})",
    "mul": "({} * {})",
    "sub": "({} - {})",
    "floordiv": "({} // {})",
    "count": "({}).count({})",
    "lt": "({} < {})",
    "gt": "({} > {})",
    "le": "({} <= {})",
    "ge": "({} >= {})",
}
_BUILTIN_PRIORS = {"root": 0.0, "constant": 0.0}


def _json(v: Any) -> str:
    return json.dumps(
        v, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False)


def _safe_key(v: Any) -> str:
    if v is _INVALID:
        return "<INVALID>"
    try:
        return _json(v)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return "<INVALID>"


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, (list, tuple)):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "other"


def _unary(op: str, x: Any) -> Any:
    try:
        if op == "len":
            return len(x)
        if op == "bool":
            return bool(x)
        if op == "str":
            return str(x)
        if op == "not":
            return not x
        if op == "first":
            return x[0]
        if op == "second":
            return x[1]
        if op == "last":
            return x[-1]
        if op == "reverse":
            return x[::-1]
        if op == "min":
            return min(x)
        if op == "max":
            return max(x)
        if op == "sum":
            return sum(x)
        if op == "strip":
            return x.strip()
        if op == "abs":
            return abs(x)
        if op == "sorted":
            return sorted(x)
        if op == "neg":
            return -x
    except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError,
            OverflowError, AttributeError, RecursionError):
        return _INVALID
    return _INVALID


def _binary(op: str, a: Any, b: Any) -> Any:
    try:
        if op == "in":
            return a in b
        if op == "eq":
            return source_same_value(a, b)
        if op == "neq":
            return not source_same_value(a, b)
        if op == "mod":
            return a % b
        if op == "add":
            return a + b
        if op == "mul":
            return a * b
        if op == "sub":
            return a - b
        if op == "floordiv":
            return a // b
        if op == "count":
            return a.count(b)
        if op == "lt":
            return a < b
        if op == "gt":
            return a > b
        if op == "le":
            return a <= b
        if op == "ge":
            return a >= b
    except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError,
            OverflowError, AttributeError, RecursionError):
        return _INVALID
    return _INVALID


def _program_operations(source: str) -> Counter:
    """Induce general operator support from program STRUCTURE, not task label."""
    tree = ast.parse(validate_code(source))
    result: Counter = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            result.update({
                ast.Mod: "mod", ast.Add: "add", ast.Sub: "sub",
                ast.Mult: "mul", ast.FloorDiv: "floordiv",
            }.get(type(node.op), "") for _ in (0,))
        elif isinstance(node, ast.Compare) and node.ops:
            mapping = {
                ast.Eq: "eq", ast.NotEq: "neq",
                ast.In: "in", ast.Lt: "lt", ast.Gt: "gt",
                ast.LtE: "le", ast.GtE: "ge",
            }
            result.update([mapping.get(type(node.ops[0]), "")])
        elif isinstance(node, ast.Subscript):
            result.update(["first"])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                result.update([node.func.id])
            elif isinstance(node.func, ast.Attribute):
                result.update([node.func.attr])
    result.pop("", None)
    return Counter({op: n for op, n in result.items()
                    if op in _UNARY or op in _BINARY})


@dataclass(frozen=True)
class LearnedDiscoveryPolicy:
    """Small model of WHICH generic operators help in a source type context.

    Its parameters come exclusively from past certified executable methods.
    Training is independent of current heldout original inputs and target
    outputs. The same frozen policy applies to all semantic families.
    """
    weights: tuple[tuple[str, str, str, int], ...] = ()
    provenance: tuple[str, ...] = ()

    @classmethod
    def fit(cls, certified_episodes: Iterable[Any]) -> "LearnedDiscoveryPolicy":
        counts: Counter = Counter()
        provenance = []
        for episode in certified_episodes:
            pairs = tuple(episode.source_pairs) + tuple(episode.independent_pairs)
            if not pairs:
                continue
            typ = _type_name(pairs[0][0])
            out = _type_name(pairs[0][1])
            for op, n in _program_operations(episode.program).items():
                counts[(typ, out, op)] += min(n, 3)
            provenance.append(episode.program_sha256)
        return cls(tuple(sorted((k[0], k[1], k[2], v)
                                for k, v in counts.items())),
                   tuple(sorted(set(provenance))))

    def weight(self, op: str, input_type: str, output_type: str,
               *, transfer=False) -> int:
        direct=sum(
            value for in_type,out_type,operator,value in self.weights
            if operator==op
            and in_type==input_type and out_type==output_type)
        if not transfer:
            return direct
        # The previous policy silently yielded 0 on every unseen I/O type
        # signature. A representation-changing task is exactly where prior
        # discovery experience must survive. The global method structural
        # prior is learned from old SOURCE-verified ASTs, not old answers.
        others=sum(
            value for in_type,out_type,operator,value in self.weights
            if operator==op and
            (in_type!=input_type or out_type!=output_type))
        return 2*direct+min(3,others)


@dataclass(frozen=True)
class Candidate:
    source: str
    values: tuple
    depth: int
    cost: float
    last_operator: str


@dataclass(frozen=True)
class InventionReceipt:
    candidates: tuple[str, ...]
    evaluated_expressions: int
    unique_semantics: int
    source_constant: bool
    elapsed_seconds: float
    learned_policy: bool
    prior_method_count: int


class StructuralInventionPolicy:
    """One frozen learned operator policy, no task-type dispatch.

    Only accepted task inputs (training SOURCE) are passed into prepare().
    It cannot ask the source oracle for labels or see independent checks.
    Its proposal API is the same as the neural proposer, which means the
    common GenerativeProgramInventor owns verification and retry policy.
    """

    def __init__(self, learned: LearnedDiscoveryPolicy | None = None,
                 *, max_states=6500, max_evaluations=250000,
                 max_candidates=12, prior_method_count=0,
                 representation_prior=None):
        if not (500 <= max_states <= 50000 and
                1000 <= max_evaluations <= 1000000 and
                1 <= max_candidates <= 64):
            raise ValueError("bounded single-core structural search required")
        self.learned = learned
        # Frozen cross-task preference learned from independently refuted
        # SOURCE candidates, never from TARGET author gold.
        self.representation_prior = representation_prior
        self.max_states = max_states
        self.max_evaluations = max_evaluations
        self.max_candidates = max_candidates
        self.prior_method_count = prior_method_count
        self._candidates: tuple[str, ...] = ()
        self._cursor = 0
        self.receipt: InventionReceipt | None = None

    def prepare(self, source_pairs):
        if not 2 <= len(source_pairs) <= 32:
            raise ValueError("bounded original SOURCE observations required")
        inputs = [x for x, y in source_pairs]
        gold = [y for x, y in source_pairs]
        input_type = _type_name(inputs[0])
        output_type = _type_name(gold[0])
        outputs = {_safe_key(y) for y in gold}
        if "<INVALID>" in outputs:
            raise ValueError("invalid SOURCE outputs")
        source_constant = len(outputs) == 1

        begin = monotonic()
        # Induce the missing intermediate structure from SOURCE before
        # guessing whole-array scalar expressions. One generic JSON-tree
        # factorizer, not a separate ARC/list/string task solver.
        factors=list(induce_structural_factors(
            source_pairs,max_candidates=self.max_candidates))
        # A general graph correspondence representation is attempted on
        # each valid SOURCE topology. It never handles a named benchmark
        # differently and is open to unlearned A on identical terms.
        factors.extend(induce_object_graph_factors(
            source_pairs,max_candidates=self.max_candidates))
        # The earlier policy learned ZERO signal on 50 real ARC2 originals:
        # it admitted only exact-fit representations. Both learned C and
        # unlearned A now share these partially explanatory executable
        # SOURCE proposals; the same independent Docker gate decides truth.
        factors.extend(induce_source_residual_probes(
            source_pairs,max_probes=min(8,self.max_candidates)))
        if self.representation_prior is not None:
            factors.sort(key=self.representation_prior.order_key)
        else:
            factors.sort(key=lambda f:(f.description_length,f.representation))
        pool: list[Candidate] = []
        observed: dict[tuple[str, ...], Candidate] = {}
        exact: list[Candidate] = []
        evaluations = 0

        def preference(op: str) -> int:
            if self.learned is None:
                return 0
            return min(8,self.learned.weight(
                op,input_type,output_type,transfer=True))

        def admit(source: str, values, depth: int, cost: float, op: str):
            if len(pool) >= self.max_states:
                return
            signature = tuple(_safe_key(x) for x in values)
            if all(x == "<INVALID>" for x in signature):
                return
            old = observed.get(signature)
            if old is not None and old.cost <= cost:
                return
            candidate = Candidate(source, tuple(values), depth, cost, op)
            observed[signature] = candidate
            pool.append(candidate)
            if all(source_same_value(y, g) for y, g in zip(values, gold)):
                exact.append(candidate)

        admit("x", inputs, 0, 0.0, "root")
        # Literal hypotheses come ONLY from generic small integers and
        # characters observed in SOURCE inputs. No TARGET-derived constants.
        literal_values: list = [None, True, False, 0, 1, 2, 3, 4, 5, 9, 10]
        characters: Counter = Counter()
        for value in inputs:
            if isinstance(value, str):
                characters.update(value)
        literal_values.extend(c for c, count in characters.most_common(8)
                              if c.strip())
        for constant in literal_values:
            admit(repr(constant), [constant] * len(inputs), 0, 0.5,
                  "constant")

        unary_ops = sorted(_UNARY, key=lambda op: (-preference(op), op))
        binary_ops = sorted(_BINARY, key=lambda op: (-preference(op), op))
        for depth in (1, 2, 3):
            previous = list(pool)
            # Budget and expansion beam apply equally to trained and uniform
            # policies; learned method weights affect ordering, not syntax.
            beam_size = 100 if depth == 3 else 190
            beam = sorted(previous, key=lambda x: (
                x.depth, x.cost, x.source))[:min(beam_size, len(previous))]
            if depth == 3:
                beam = sorted(previous, key=lambda x: (
                    x.cost, x.source))[:beam_size]
            for expression in beam:
                if expression.depth != depth - 1:
                    continue
                for op in unary_ops:
                    if evaluations >= self.max_evaluations:
                        break
                    evaluations += 1
                    values = [_unary(op, v) if v is not _INVALID
                              else _INVALID for v in expression.values]
                    admit(_UNARY[op].format(expression.source), values,
                          depth, expression.cost + 1.0 -
                          0.14 * preference(op), op)
                for rhs in beam:
                    if (evaluations >= self.max_evaluations
                            or len(pool) >= self.max_states):
                        break
                    if max(expression.depth, rhs.depth) != depth - 1:
                        continue
                    for op in binary_ops:
                        evaluations += 1
                        if evaluations >= self.max_evaluations:
                            break
                        values = [
                            _binary(op, v, w)
                            if v is not _INVALID and w is not _INVALID
                            else _INVALID
                            for v, w in zip(expression.values, rhs.values)]
                        admit(_BINARY[op].format(
                            expression.source, rhs.source),
                            values, depth,
                            expression.cost + rhs.cost + 1.2 -
                            0.14 * preference(op), op)
            if exact:
                break
        exact.sort(key=lambda x: (x.cost, x.source))
        candidates = []
        for item in exact:
            text = "def transform(x):\n    return " + item.source
            try:
                text = validate_code(text)
            except (TypeError, ValueError):
                continue
            if text not in candidates:
                candidates.append(text)
            if len(candidates) >= self.max_candidates:
                break
        # Factorized plans are evaluated on current SOURCE already and
        # independently Docker-verified in the one existing discovery core.
        # Both classical A and learned C share these exact same plans and
        # search budget. No retrieval from TARGET or benchmark identity.
        structured=[item.program for item in factors]
        ordered=[]
        for program in structured+candidates:
            if program not in ordered:
                ordered.append(program)
            if len(ordered)>=self.max_candidates:
                break
        self._candidates = tuple(ordered)
        self._cursor = 0
        self.receipt = InventionReceipt(
            candidates=self._candidates,
            evaluated_expressions=evaluations,
            unique_semantics=len(observed)+len(factors),
            source_constant=source_constant,
            elapsed_seconds=monotonic() - begin,
            learned_policy=self.learned is not None,
            prior_method_count=self.prior_method_count)

    def propose(self, prompt: str) -> str:
        # No extra source, output or teacher-gold enters this method.
        if self._cursor >= len(self._candidates):
            raise ValueError("no source-fitting executable hypothesis remains")
        candidate = self._candidates[self._cursor]
        self._cursor += 1
        return candidate
