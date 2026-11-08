"""Finite operator and representation induction from binary source facts.

The inference algorithm uses only observed triples (a,b,result).
It discovers a two-sided identity candidate, complete left-action rows,
a generating set and a shortest-word normal form for every observed symbol.

Guarantee is CONDITIONAL on the true operator being associative with a
two-sided identity; sparse source facts alone cannot certify those axioms.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import perf_counter_ns
from typing import Hashable, Iterable


class EvidenceInsufficient(ValueError):
    """Abort rather than pretend that missing examples imply a law."""


def stable_key(value):
    return type(value).__name__, repr(value)


@dataclass(frozen=True)
class InventedOperator:
    identity: Hashable
    generators: tuple[Hashable, ...]
    normal_forms: dict[Hashable, tuple[Hashable, ...]]
    actions: dict[Hashable, dict[Hashable, Hashable]]
    source_observations: int
    candidate_identity_count: int
    elapsed_ms: float
    premise: str = "conditional on finite associative identity algebra"

    def apply(self, a: Hashable, b: Hashable) -> Hashable:
        if a not in self.normal_forms or b not in self.normal_forms:
            raise EvidenceInsufficient("unknown element: refuse extrapolation")
        value = b
        for generator in self.normal_forms[a]:
            value = self.actions[generator][value]
        return value

    def representation(self, a: Hashable) -> tuple[Hashable, ...]:
        if a not in self.normal_forms:
            raise EvidenceInsufficient("unknown element")
        return self.normal_forms[a]

    @property
    def universe_size(self):
        return len(self.normal_forms)

    @property
    def total_inferred_cells(self):
        return self.universe_size ** 2

    @property
    def unobserved_predictions(self):
        return self.total_inferred_cells - self.source_observations


def _normal_forms(identity, generators, actions):
    # Discover each observed symbol's coordinate in generator-word space.
    words = {identity: ()}
    pending = deque([identity])
    while pending:
        a = pending.popleft()
        for g in generators:
            b = actions[g][a]
            if b not in words:
                words[b] = words[a] + (g,)
                pending.append(b)
    return words


def invent_operator(source: Iterable[tuple[Hashable, Hashable, Hashable]]):
    start = perf_counter_ns()
    facts = {}
    universe = set()
    for triple in source:
        if not isinstance(triple, (tuple, list)) or len(triple) != 3:
            raise EvidenceInsufficient("binary source triple required")
        a, b, c = triple
        try:
            hash(a); hash(b); hash(c)
            universe.update((a, b, c))
        except TypeError as err:
            raise EvidenceInsufficient("unhashable element") from err
        if (a, b) in facts and facts[a, b] != c:
            raise EvidenceInsufficient("contradictory source")
        facts[a, b] = c
    if len(universe) < 2:
        raise EvidenceInsufficient("at least two elements required")
    universe = tuple(sorted(universe, key=stable_key))

    full_rows = {}
    for a in universe:
        if all((a, b) in facts for b in universe):
            full_rows[a] = {b: facts[a, b] for b in universe}
    identities = [
        a for a, row in full_rows.items()
        if all(row[b] == b for b in universe)
        and all(facts.get((b, a), b) == b for b in universe)
    ]
    if len(identities) != 1:
        raise EvidenceInsufficient("no unique identity supported by source")
    identity = identities[0]

    actions = {g: row for g, row in full_rows.items() if g != identity}
    if not actions:
        raise EvidenceInsufficient("no complete nontrivial generator rows")
    generators = tuple(sorted(actions, key=stable_key))
    if len(_normal_forms(identity, generators, actions)) != len(universe):
        raise EvidenceInsufficient("unreachable elements")

    # Delete surplus complete action rows while retaining coverage.
    for g in tuple(generators):
        trial = tuple(x for x in generators if x != g)
        if len(_normal_forms(identity, trial, actions)) == len(universe):
            generators = trial
    words = _normal_forms(identity, generators, actions)
    model = InventedOperator(
        identity=identity,
        generators=generators,
        normal_forms=words,
        actions={g: actions[g] for g in generators},
        source_observations=len(facts),
        candidate_identity_count=1,
        elapsed_ms=(perf_counter_ns() - start) / 1e6,
    )
    for (a, b), c in facts.items():
        if model.apply(a, b) != c:
            raise EvidenceInsufficient("generated operator contradicts source")
    return model
