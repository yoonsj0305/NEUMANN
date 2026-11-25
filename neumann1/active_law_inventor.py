"""Active, bounded finite binary-algebra discovery and execution.

The system generates equational hypotheses from a small free term grammar,
asks an external source oracle for discriminating observations, and constructs
new generator-word coordinates when associative structure is supported.
All discovered laws are empirical unless source verification is exhaustive.
The only guaranteed way to resolve arbitrary adversarial black boxes is to
query the entire table or abstain. No target oracle is accessed after freeze.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from random import Random
from typing import Callable, Hashable, Iterable

from .monoid_operator_inventor import EvidenceInsufficient, invent_operator


class BudgetExhausted(EvidenceInsufficient):
    pass


class SourceOracle:
    def __init__(self, universe: Iterable[Hashable], ask: Callable,
                 max_queries: int):
        self.universe = tuple(universe)
        if len(self.universe) < 2 or len(set(self.universe)) != len(self.universe):
            raise EvidenceInsufficient("at least two unique elements required")
        if max_queries < 0:
            raise ValueError("negative budget")
        self.ask_fn = ask
        self.max_queries = max_queries
        self.facts: dict[tuple, Hashable] = {}

    def ask(self, a, b):
        if a not in self.universe or b not in self.universe:
            raise EvidenceInsufficient("query outside declared universe")
        if (a, b) not in self.facts:
            if len(self.facts) >= self.max_queries:
                raise BudgetExhausted("source oracle budget exhausted")
            output = self.ask_fn(a, b)
            if output not in self.universe:
                raise EvidenceInsufficient("operation not closed")
            self.facts[a, b] = output
        return self.facts[a, b]

    def transcript(self):
        return tuple((a,b,c) for (a,b),c in self.facts.items())


# Terms are generated, not supplied as a list of named algebraic laws.
# Trees are ("*", left, right), and leaves are x, y, z.
def _terms():
    terms = ["x", "y", ("*", "x", "x"), ("*", "x", "y"),
             ("*", "y", "x")]
    for perm in permutations(("x", "y", "z")):
        a,b,c = perm
        terms += [("*", ("*", a, b), c),
                  ("*", a, ("*", b, c))]
    return tuple(terms)


def _evaluate(term, env, oracle):
    if isinstance(term, str):
        return env[term]
    return oracle.ask(_evaluate(term[1], env, oracle),
                      _evaluate(term[2], env, oracle))


def _expression(term):
    if isinstance(term, str):
        return term
    return "(" + _expression(term[1]) + "*" + _expression(term[2]) + ")"


@dataclass(frozen=True)
class DiscoveredAlgebra:
    strategy: str
    model: object
    equations: tuple[tuple[str, str], ...]
    source_facts: tuple[tuple, ...]
    validation_queries: int
    validation_correct: int
    law_probe_assignments: int
    verified_exhaustively: bool
    conditional_associativity: bool

    def apply(self, a, b):
        if self.strategy == "generator_word":
            return self.model.apply(a, b)
        if self.strategy == "full_table":
            if (a,b) not in self.model:
                raise EvidenceInsufficient("unknown pair")
            return self.model[a,b]
        raise EvidenceInsufficient("unrecognized strategy")


def _discover_equations(oracle, rng, *, assignments=5):
    terms = _terms()
    vectors = {str(i): [] for i in range(len(terms))}
    for i in range(assignments):
        a,b,c = rng.sample(oracle.universe, 3) if len(oracle.universe)>2 else (
            oracle.universe[i%2], oracle.universe[(i+1)%2], oracle.universe[i%2])
        env = {"x":a,"y":b,"z":c}
        for j, term in enumerate(terms):
            vectors[str(j)].append(_evaluate(term, env, oracle))
    found = []
    for i, a in enumerate(terms):
        for j in range(i+1, len(terms)):
            if vectors[str(i)] == vectors[str(j)]:
                found.append((_expression(a), _expression(terms[j])))
    return tuple(found)


def _find_identity(oracle, rng):
    candidates = list(oracle.universe)
    rng.shuffle(candidates)
    anchors = list(oracle.universe)
    rng.shuffle(anchors)
    for e in candidates:
        if all(oracle.ask(e, x) == x and oracle.ask(x, e) == x
               for x in anchors):
            return e
    raise EvidenceInsufficient("no two-sided identity in available universe")


def _normal_forms(e, generators, rows):
    from collections import deque
    result = {e: ()}
    pending = deque([e])
    while pending:
        x = pending.popleft()
        for g in generators:
            y = rows[g][x]
            if y not in result:
                result[y] = result[x] + (g,)
                pending.append(y)
    return result


def _learn_generators(oracle, e, rng):
    candidates = [x for x in oracle.universe if x != e]
    rng.shuffle(candidates)
    rows = {}
    generators = []
    coverage = {e}
    for g in candidates:
        if g in coverage:
            continue
        rows[g] = {b: oracle.ask(g,b) for b in oracle.universe}
        generators.append(g)
        coverage = set(_normal_forms(e,generators,rows))
        if len(coverage) == len(oracle.universe):
            break
    if len(coverage) != len(oracle.universe):
        raise EvidenceInsufficient("no complete generating action found")
    return tuple(generators)


def _validation_pairs(oracle, model, rng, n):
    unseen = [(a,b) for a in oracle.universe for b in oracle.universe
              if (a,b) not in oracle.facts]
    # Longest words are a stress test for composition errors.
    rng.shuffle(unseen)
    unseen.sort(key=lambda p: -len(model.normal_forms[p[0]]))
    return unseen[:n]


def invent_with_oracle(universe, ask, *, budget, seed=0,
                       law_assignments=5, validation=10,
                       allow_full_table=False):
    """Induce, falsify and compile an operation with a bounded SOURCE oracle.

    Results of non-exhaustive algebraic probes are only empirically supported.
    If no supported structure survives, fail closed or acquire an entire
    table if expressly allowed and affordable. The oracle must be trusted;
    untrusted output still needs independent task-level validation.
    """
    rng = Random(seed)
    oracle = SourceOracle(universe, ask, budget)
    try:
        equations = _discover_equations(oracle, rng, assignments=law_assignments)
        # The compiler currently knows how to use associativity, discovered
        # from generated term equivalences rather than task-family metadata.
        associative = any(set(eq) == {"((x*y)*z)", "(x*(y*z))"}
                          for eq in equations)
        if not associative:
            raise EvidenceInsufficient("associativity not supported by observed law probes")
        e = _find_identity(oracle, rng)
        _learn_generators(oracle,e,rng)
        model = invent_operator(oracle.transcript())
        checks = 0
        for a,b in _validation_pairs(oracle,model,rng,validation):
            checks += 1
            if oracle.ask(a,b) != model.apply(a,b):
                raise EvidenceInsufficient("falsified candidate law on source counterexample")
        observed = oracle.transcript()
        return DiscoveredAlgebra(
            strategy="generator_word",model=model,equations=equations,
            source_facts=observed,validation_queries=checks,
            validation_correct=checks,law_probe_assignments=law_assignments,
            verified_exhaustively=len(observed)==len(oracle.universe)**2,
            conditional_associativity=True)
    except EvidenceInsufficient:
        if not allow_full_table:
            raise
        for a in oracle.universe:
            for b in oracle.universe:
                oracle.ask(a,b)
        observed=oracle.transcript()
        return DiscoveredAlgebra(
            strategy="full_table",model={(a,b):c for a,b,c in observed},
            equations=(),source_facts=observed,validation_queries=0,
            validation_correct=0,law_probe_assignments=law_assignments,
            verified_exhaustively=True,conditional_associativity=False)
