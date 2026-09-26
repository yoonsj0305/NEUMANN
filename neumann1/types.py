from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class IRKind(str, Enum):
    BIPARTITE_MATCHING = "bipartite_matching"
    SHORTEST_PATH = "shortest_path"
    LINEAR_SYSTEM = "linear_system"
    ARITHMETIC = "arithmetic"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Problem:
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Representation:
    kind: IRKind
    payload: Dict[str, Any]
    confidence: float
    rationale: str = ""


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str


@dataclass
class CostLedger:
    representation_steps: int = 0
    solver_steps: int = 0
    verification_steps: int = 0
    fallback_steps: int = 0

    @property
    def total_steps(self) -> int:
        return (
            self.representation_steps
            + self.solver_steps
            + self.verification_steps
            + self.fallback_steps
        )


@dataclass
class SolveResult:
    answer: Any
    representation: Representation
    solver_name: str
    verified: bool
    verification_reason: str
    ledger: CostLedger
    trace: List[str] = field(default_factory=list)
