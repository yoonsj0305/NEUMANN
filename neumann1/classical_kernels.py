"""Strong conventional solutions. Never re-invent a solved exact obligation.

A semantics contract is supplied by the trusted caller, NOT inferred from
task shape or a few I/O examples.  A matching name without a real contract
would not constitute proof of the problem's mathematical meaning.
"""
from __future__ import annotations

from collections import deque
from .induced_fixpoint_grammar import validate_task, InsufficientEvidence

DIRECTED_REACHABILITY = "finite_directed_reachability"


def classical_directed_reachability(task):
    """Exact O(|V|+|E|) BFS for a finite directed relation."""
    nodes, edges, seeds = validate_task(task, with_answer=False)
    neighbors = {v: [] for v in nodes}
    for a, b in edges:
        neighbors[a].append(b)
    seen = set(seeds)
    pending = deque(seeds)
    while pending:
        for b in neighbors[pending.popleft()]:
            if b not in seen:
                seen.add(b)
                pending.append(b)
    return frozenset(seen)


def solve_with_semantic_contract(task, *, semantics):
    """Execute a known classical algorithm without initiating discovery.

    This is an *interface guarantee*, not automatic recognition of arbitrary
    problem statements. The caller is responsible for declaring semantics
    accurately and independent verification of any novel application.
    """
    if semantics == DIRECTED_REACHABILITY:
        return classical_directed_reachability(task)
    raise InsufficientEvidence("no certified classical semantic adapter")
