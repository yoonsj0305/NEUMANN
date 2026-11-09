"""ONE task-agnostic Q3 discovery loop: certified method memory + learned proposer.

The inference policy, not the developer, creates new executable Python programs.
There is no ARC/string/graph/CA/SyGuS dispatch and no domain-specific operator
synthesis here. Verified source episodes are reusable principles/teaching traces,
not accepted answers on unrelated tasks.

Two causal controls intentionally use this SAME implementation:
  B: frozen policy with certified memory
  C: identically scoped memory with SOURCE-trained policy weights

An independent original problem scorer (not this module) owns TARGET labels.
No model result is accepted from mere SOURCE fit as universal correctness.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .open_program_inventor import (
    Discovery, GenerativeProgramInventor, IsolatedPython,
    UnsafeProposal, validate_code,
)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _source_key(pairs) -> str:
    return sha256(_canonical(pairs).encode()).hexdigest()


def _check_pairs(train, checks):
    if (not 1 <= len(train) <= 32 or not 1 <= len(checks) <= 32):
        raise ValueError("bounded SOURCE train and check are required")
    tr = [_canonical(x) for x, _ in train]
    ck = [_canonical(x) for x, _ in checks]
    if len(tr) != len(set(tr)) or len(ck) != len(set(ck)) or set(tr) & set(ck):
        raise ValueError("independent SOURCE labels need disjoint unique inputs")
    for x, y in (*train, *checks):
        _canonical(x)
        _canonical(y)


@dataclass(frozen=True)
class CertifiedMethodEpisode:
    """Past program code plus source-only proof inputs; never TARGET gold."""
    source_id: str
    source_pairs: tuple
    independent_pairs: tuple
    program: str
    program_sha256: str
    observation_sha256: str

    @property
    def identity(self):
        return sha256((self.source_id + ":" + self.observation_sha256
                       + ":" + self.program_sha256).encode()).hexdigest()


class SourceMethodMemory:
    """Small immutable-proof method library; no task family or oracle routing."""

    def __init__(self, runner, *, max_episodes=128):
        if not 1 <= max_episodes <= 4096:
            raise ValueError("bounded method library required")
        self.runner = runner
        self.max_episodes = max_episodes
        self.episodes: list[CertifiedMethodEpisode] = []
        self._frozen = False

    def freeze(self):
        self._frozen = True

    def admit(self, source_id, train, checks, program):
        """Recertify both SOURCE partitions in locked executor, fail closed."""
        if self._frozen:
            raise ValueError("method memory frozen for heldout evaluation")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source provenance required")
        if any(e.source_id == source_id for e in self.episodes):
            raise ValueError("duplicate source ID; no cross-split contamination")
        if len(self.episodes) >= self.max_episodes:
            raise ValueError("method memory budget exhausted")
        train = tuple((x, y) for x, y in train)
        checks = tuple((x, y) for x, y in checks)
        _check_pairs(train, checks)
        code = validate_code(program)
        if len(code) > 6000:
            raise ValueError("bounded executable method size")
        outcome = self.runner.evaluate(code, [x for x, _ in (*train, *checks)])
        if (outcome.status != "EXECUTED" or
                len(outcome.outputs) != len(train) + len(checks) or
                any(a != b for a, (_, b) in zip(
                    outcome.outputs, (*train, *checks)))):
            raise UnsafeProposal("prior method not independently SOURCE-certified")
        row = CertifiedMethodEpisode(
            source_id=source_id, source_pairs=train,
            independent_pairs=checks, program=code,
            program_sha256=sha256(code.encode()).hexdigest(),
            observation_sha256=_source_key((*train, *checks)))
        self.episodes.append(row)
        return row

    def import_source_teachers(self, rows, *, prefix="source-teacher"):
        """Reuse previously frozen ORIGINAL_SOURCE_ONLY teacher receipts.

        A teacher is NOT trusted on metadata alone. Code and all SOURCE
        witnesses must be re-executed on the same independent executor.
        """
        inserted = []
        for idx, row in enumerate(rows):
            if (row.get("schema") !=
                    "NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1" or
                    row.get("provenance") != "ORIGINAL_SOURCE_ONLY" or
                    row.get("independent_checks", 0) < 1 or
                    not isinstance(row.get("pairs"), list) or
                    len(row["pairs"]) <= row["independent_checks"]):
                raise ValueError("not a certified SOURCE method record")
            program = row.get("program")
            if (not isinstance(program, str) or
                    sha256(program.encode()).hexdigest() != row.get("sha256")):
                raise ValueError("teacher code SHA mismatch")
            source_id = str(row.get("original_id", idx))
            items = row["pairs"]
            k = row["independent_checks"]
            inserted.append(self.admit(
                prefix + "/" + source_id, items[:-k], items[-k:], program))
        return inserted

    def context(self, *, excluded_ids=(), max_methods=2,
                max_chars_per_method=1000):
        """Bounded SOURCE-only method episodes shared by B and C controls."""
        if not 0 <= max_methods <= 8 or not 100 <= max_chars_per_method <= 3000:
            raise ValueError("bounded method conditioning required")
        forbidden = set(excluded_ids)
        candidates = [e for e in self.episodes
                      if e.source_id not in forbidden]
        # Deterministic frozen order; never select by hidden TARGET outcome.
        candidates.sort(key=lambda e: e.identity)
        parts = []
        for e in candidates[:max_methods]:
            parts.append(
                "Past SOURCE-certified general method (" +
                e.program_sha256[:12] + "); source example: " +
                _canonical(e.source_pairs[0])[:240] + "\n" +
                e.program[:max_chars_per_method])
        return "\n\n".join(parts)

    def teacher_rows(self):
        """Teacher forcing for the SAME generator, no labels from heldout."""
        return [
            {
                "schema": "NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
                "provenance": "ORIGINAL_SOURCE_ONLY",
                "source_id": e.source_id,
                "independent_checks": len(e.independent_pairs),
                "pairs": list(e.source_pairs + e.independent_pairs),
                "program": e.program,
                "sha256": e.program_sha256,
            }
            for e in self.episodes]


@dataclass(frozen=True)
class CoreOutcome:
    discovery: Discovery
    method_memory_count: int
    source_context_sha256: str
    status: str


class SingleDiscoveryCore:
    """Single learned policy and method memory, no family-labeled routes.

    An optional already-trusted classical procedure can be invoked by the
    caller outside this core. Its original-semantic verification is the
    caller's responsibility; this loop never treats a SOURCE fit as TARGET
    correctness. To avoid polluting frozen evaluation, do not admit new
    episodes after freeze().
    """

    def __init__(self, policy, runner=None, *, memory=None, max_proposals=8):
        self.policy = policy
        self.runner = runner if runner is not None else IsolatedPython()
        self.memory = (memory if memory is not None
                       else SourceMethodMemory(self.runner))
        if not 1 <= max_proposals <= 64:
            raise ValueError("finite proposal budget required")
        self.max_proposals = max_proposals

    def discover(self, source_pairs, independent_source_checks, *,
                 excluded_source_ids=(), reuse_memory=True):
        train = tuple((x, y) for x, y in source_pairs)
        checks = tuple((x, y) for x, y in independent_source_checks)
        _check_pairs(train, checks)
        context = (self.memory.context(excluded_ids=excluded_source_ids)
                   if reuse_memory else "")
        proposal = GenerativeProgramInventor(
            self.policy, self.runner,
            max_proposals=self.max_proposals).discover(
                train, independent_source_checks=checks,
                method_context=context)
        return CoreOutcome(
            discovery=proposal,
            method_memory_count=(len(self.memory.episodes) if reuse_memory else 0),
            source_context_sha256=sha256(context.encode()).hexdigest(),
            status=proposal.status,
        )

    def learn_from_verified_source(self, source_id, train, checks, outcome):
        """Admit actual independent SOURCE verified discoveries, never misses."""
        if not isinstance(outcome, CoreOutcome) or not outcome.discovery.verified:
            raise UnsafeProposal("cannot learn from unverified candidate")
        return self.memory.admit(
            source_id, train, checks, outcome.discovery.program)
