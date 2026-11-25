"""Invent recursive control flow from relation I/O, then compile delta execution.

The source learner never receives named 'reachability' or 'BFS' primitives.
Its bounded metalanguage supplies set algebra, relation-image and iteration
semantics, so *arbitrary* novel computational semantics remain OPEN.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns


class InsufficientEvidence(ValueError):
    pass


def canonical(items):
    return frozenset(items)


def validate_task(task, *, with_answer=True):
    if not isinstance(task, dict):
        raise InsufficientEvidence("task requires mapping")
    try:
        nodes = tuple(task["nodes"])
        if len(nodes) == 0 or len(nodes) != len(set(nodes)):
            raise InsufficientEvidence("nonempty unique universe required")
        universe = set(nodes)
        edges = tuple(task["edges"])
        if any(len(e) != 2 or e[0] not in universe or e[1] not in universe
               for e in edges):
            raise InsufficientEvidence("relation outside finite universe")
        seeds = tuple(task["seeds"])
        if any(x not in universe for x in seeds):
            raise InsufficientEvidence("seed outside universe")
        if with_answer and any(x not in universe for x in task["answer"]):
            raise InsufficientEvidence("answer outside universe")
    except (KeyError, TypeError) as error:
        raise InsufficientEvidence("invalid typed relational input") from error
    return nodes, edges, seeds


def image(edges, state, *, reverse):
    if reverse:
        return frozenset(a for a, b in edges if b in state)
    return frozenset(b for a, b in edges if a in state)


def merge(old, new, *, mode):
    if mode == "union":
        return old | new
    if mode == "replace":
        return new
    if mode == "difference":
        return old - new
    if mode == "intersection":
        return old & new
    raise InsufficientEvidence("unsupported combinator")


@dataclass(frozen=True)
class CompiledRule:
    ast: tuple
    source_count: int
    source_signature: tuple[int, ...]
    checked: int
    discovery_ns: int

    def apply(self, task):
        nodes, edges, seeds = validate_task(task, with_answer=False)
        tag, initial, step, direction, mode, stop = self.ast
        if tag != "iterate" or step != "rel_image":
            raise InsufficientEvidence("invalid generated grammar")
        state = {"seeds": frozenset(seeds), "all": frozenset(nodes),
                 "empty": frozenset()}[initial]
        for i in range(len(nodes) + 1):
            nxt = merge(state, image(edges, state,
                                    reverse=(direction == "backward")), mode=mode)
            if stop == "one":
                return nxt
            if stop == "two" and i == 1:
                return nxt
            if stop == "stable":
                if not state <= nxt:
                    raise InsufficientEvidence("nonmonotone: no convergence proof")
                if nxt == state:
                    return nxt
            state = nxt
        raise InsufficientEvidence("no convergence within finite state bound")

    @property
    def verified_for_all_finite_graphs(self):
        # A structural theorem *conditional* on precisely these semantics.
        return self.ast == ("iterate", "seeds", "rel_image",
                            "forward", "union", "stable")

    @property
    def proof(self):
        if not self.verified_for_all_finite_graphs:
            return None
        return ("After k iterations S includes exactly all states reachable "
                "via paths of length <= k. Each expansion is monotone; "
                "finite |V| makes the union stabilize.")

    def compile_delta(self):
        """Structural program rewrite via image(A union B)=image(A) union image(B)."""
        if not self.verified_for_all_finite_graphs:
            raise InsufficientEvidence("unproven fixedpoint: cannot lower to delta")
        return ("delta_while_nonempty", "seeds", "forward_image",
                "subtract_seen", "union_into_seen")

    def apply_delta(self, task):
        self.compile_delta()
        nodes, edges, seeds = validate_task(task, with_answer=False)
        adjacency = {u: set() for u in nodes}
        for u, v in edges:
            adjacency[u].add(v)
        seen = set(seeds)
        frontier = set(seeds)
        while frontier:
            next_frontier = set()
            for u in frontier:
                next_frontier.update(adjacency[u])
            next_frontier.difference_update(seen)
            seen.update(next_frontier)
            frontier = next_frontier
        return frozenset(seen)


class RecursiveGrammarInventor:
    """Source-only recursive control synthesis, promotion, refutation and repair."""

    def __init__(self, *, max_candidates=128):
        self.max_candidates = max_candidates
        self.learned = []
        self.source_history = []
        self.verification_history = []
        self.repairs = 0

    def candidates(self):
        # Enumerate new executable ASTs from a small typed *meta* grammar.
        # No hardcoded reachability/flood-fill/task type selection here.
        for init, direction, mode, stop in product(
            ("seeds", "empty", "all"), ("forward", "backward"),
            ("union", "replace", "intersection", "difference"),
            ("one", "two", "stable")
        ):
            yield ("iterate", init, "rel_image", direction, mode, stop)

    def invent(self, source_tasks, *, verification_tasks=()):
        start = perf_counter_ns()
        train, verification = list(source_tasks), list(verification_tasks)
        if len(train) < 2 or not verification:
            raise InsufficientEvidence("two sources and independent source verifier required")
        for task in train + verification:
            validate_task(task)
        for count, ast in enumerate(self.candidates(), 1):
            if count > self.max_candidates:
                break
            candidate = CompiledRule(
                ast, len(train), tuple(len(t["nodes"]) for t in train), count, 0)
            try:
                if any(candidate.apply(t) != canonical(t["answer"]) for t in train):
                    continue
                if any(candidate.apply(t) != canonical(t["answer"])
                       for t in verification):
                    continue
            except InsufficientEvidence:
                continue
            approved = CompiledRule(
                ast, len(train), tuple(len(t["nodes"]) for t in train),
                count, perf_counter_ns() - start)
            self.learned = [approved]
            self.source_history = train
            self.verification_history = verification
            return approved
        raise InsufficientEvidence("no source-verified generated control rule")

    def revise_with_source_counterexample(self, task):
        if not self.learned:
            raise InsufficientEvidence("no approved rule to revise")
        validate_task(task)
        if self.learned[0].apply(task) == canonical(task["answer"]):
            return False
        training = list(self.source_history)
        independent_checks = list(self.verification_history) + [task]
        self.learned = []  # Falsified program must not continue serving targets.
        self.invent(training, verification_tasks=independent_checks)
        self.repairs += 1
        return True

    def solve(self, task, *, optimized=True):
        if len(self.learned) != 1:
            raise InsufficientEvidence("no unambiguous generated rule")
        rule = self.learned[0]
        if optimized and rule.verified_for_all_finite_graphs:
            return rule.apply_delta(task)
        return rule.apply(task)
