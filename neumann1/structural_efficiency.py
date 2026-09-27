from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any

from .family_registry import FamilyAdapter
from .types import CostLedger, Problem, Representation, is_unknown_kind, kind_id


@dataclass(frozen=True)
class ExecutionCostSnapshot:
    representation_steps: int
    solver_steps: int
    verification_steps: int
    fallback_steps: int
    wall_seconds: float
    verified_runs: int
    total_runs: int

    @property
    def verified_rate(self) -> float:
        return self.verified_runs / self.total_runs if self.total_runs else 0.0


@dataclass(frozen=True)
class StructuralEfficiencyObservation:
    family_id: str
    repeats: int
    raw_text_bytes: int
    representation_bytes: int
    representation_to_raw_byte_ratio: float
    compile_every_time: ExecutionCostSnapshot
    compile_once_reuse: ExecutionCostSnapshot
    answer_equivalence_rate: float
    representation_identity_stable: bool

    @property
    def representation_step_reduction_factor(self) -> float:
        denom = self.compile_once_reuse.representation_steps
        if denom <= 0:
            return float("inf")
        return self.compile_every_time.representation_steps / denom

    @property
    def compiler_input_byte_reduction_factor(self) -> float:
        # Raw text is presented to the compiler once in reuse mode and once per
        # repetition in compile-every-time mode.
        return float(self.repeats)


def canonical_representation_bytes(representation: Representation) -> bytes:
    """Serialize solver-relevant representation identity deterministically.

    Rationale/confidence are deliberately excluded from this payload proxy because
    the downstream deterministic solver consumes kind + payload semantics.
    """
    data = {
        "kind_id": kind_id(representation.kind),
        "payload": representation.payload,
    }
    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"representation payload must be JSON-serializable for byte accounting: {exc}"
        ) from exc


def _answer_bytes(answer: Any) -> bytes:
    try:
        return json.dumps(
            answer,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"answer must be JSON-serializable for paired comparison: {exc}"
        ) from exc


def _compile_checked(
    problem: Problem,
    adapter: FamilyAdapter,
    ledger: CostLedger,
) -> Representation:
    representation = adapter.compiler.form(problem, ledger)
    if is_unknown_kind(representation.kind):
        raise ValueError("structural-efficiency fixture compiled to UNKNOWN")
    if kind_id(representation.kind) != adapter.canonical_kind_id:
        raise ValueError("compiler emitted representation for the wrong family")
    if not adapter.solver.supports(representation):
        raise ValueError("family solver rejected compiler output")
    return representation


def _execute_representation(
    problem: Problem,
    representation: Representation,
    adapter: FamilyAdapter,
    ledger: CostLedger,
) -> tuple[Any, bool]:
    answer = adapter.solver.solve(representation, ledger)
    verification = adapter.answer_verifier.verify(
        problem, representation, answer, ledger
    )
    return answer, bool(verification.ok)


def _snapshot(
    ledger: CostLedger,
    *,
    wall_seconds: float,
    verified_runs: int,
    total_runs: int,
) -> ExecutionCostSnapshot:
    return ExecutionCostSnapshot(
        representation_steps=ledger.representation_steps,
        solver_steps=ledger.solver_steps,
        verification_steps=ledger.verification_steps,
        fallback_steps=ledger.fallback_steps,
        wall_seconds=wall_seconds,
        verified_runs=verified_runs,
        total_runs=total_runs,
    )


def measure_repeated_structural_reuse(
    problem: Problem,
    adapter: FamilyAdapter,
    *,
    repeats: int = 5,
) -> StructuralEfficiencyObservation:
    """Compare repeated raw recompilation with compile-once structural reuse.

    This benchmark measures the economics of *reusing an already valid
    solver-ready representation*. It does not measure LLM FLOPs, energy, or
    general reasoning quality.
    """
    if repeats < 2:
        raise ValueError("repeats must be >= 2")

    raw_text_bytes = len(problem.raw_text.encode("utf-8"))

    # Mode A: present raw text to the compiler on every repetition.
    every_ledger = CostLedger()
    every_answers: list[bytes] = []
    every_representations: list[bytes] = []
    every_verified = 0
    start = time.perf_counter()
    for _ in range(repeats):
        rep = _compile_checked(problem, adapter, every_ledger)
        rep_bytes = canonical_representation_bytes(rep)
        answer, verified = _execute_representation(
            problem, rep, adapter, every_ledger
        )
        every_representations.append(rep_bytes)
        every_answers.append(_answer_bytes(answer))
        every_verified += int(verified)
    every_wall = time.perf_counter() - start

    # Mode B: compile once, then reuse the exact same representation object.
    reuse_ledger = CostLedger()
    reuse_answers: list[bytes] = []
    reuse_verified = 0
    start = time.perf_counter()
    reusable_rep = _compile_checked(problem, adapter, reuse_ledger)
    reusable_bytes = canonical_representation_bytes(reusable_rep)
    for _ in range(repeats):
        answer, verified = _execute_representation(
            problem, reusable_rep, adapter, reuse_ledger
        )
        reuse_answers.append(_answer_bytes(answer))
        reuse_verified += int(verified)
    reuse_wall = time.perf_counter() - start

    equivalent = sum(
        1
        for left, right in zip(every_answers, reuse_answers)
        if left == right
    )
    representation_identity_stable = all(
        payload == reusable_bytes for payload in every_representations
    )

    return StructuralEfficiencyObservation(
        family_id=adapter.family_id,
        repeats=repeats,
        raw_text_bytes=raw_text_bytes,
        representation_bytes=len(reusable_bytes),
        representation_to_raw_byte_ratio=(
            len(reusable_bytes) / raw_text_bytes if raw_text_bytes else float("inf")
        ),
        compile_every_time=_snapshot(
            every_ledger,
            wall_seconds=every_wall,
            verified_runs=every_verified,
            total_runs=repeats,
        ),
        compile_once_reuse=_snapshot(
            reuse_ledger,
            wall_seconds=reuse_wall,
            verified_runs=reuse_verified,
            total_runs=repeats,
        ),
        answer_equivalence_rate=equivalent / repeats,
        representation_identity_stable=representation_identity_stable,
    )
