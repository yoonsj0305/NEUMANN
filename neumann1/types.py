from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, TypeAlias


class IRKind(str, Enum):
    """Legacy/core representation kinds.

    Core families keep this enum for backward compatibility. External families
    should use a namespaced string such as "acme.min_cost_flow".
    """

    BIPARTITE_MATCHING = "bipartite_matching"
    SHORTEST_PATH = "shortest_path"
    LINEAR_SYSTEM = "linear_system"
    ARITHMETIC = "arithmetic"
    UNKNOWN = "unknown"


KindLike: TypeAlias = IRKind | str
_CUSTOM_KIND_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)+$")


def kind_id(kind: KindLike) -> str:
    """Return the stable runtime identifier for a representation kind."""
    if isinstance(kind, IRKind):
        return f"core.{kind.value}"
    if not isinstance(kind, str) or not kind:
        raise TypeError("representation kind must be IRKind or nonempty string")
    if kind in {"unknown", "core.unknown"}:
        return "core.unknown"
    if not _CUSTOM_KIND_RE.fullmatch(kind):
        raise ValueError(
            "external representation kinds must be namespaced, e.g. 'vendor.family'"
        )
    if kind.startswith("core."):
        raise ValueError("the 'core.' kind namespace is reserved for NEUMANN core")
    return kind


def is_unknown_kind(kind: KindLike) -> bool:
    try:
        return kind_id(kind) == "core.unknown"
    except (TypeError, ValueError):
        return False


def display_kind(kind: KindLike) -> str:
    if isinstance(kind, IRKind):
        return kind.value
    return str(kind)


@dataclass(frozen=True)
class Problem:
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Representation:
    kind: KindLike
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
