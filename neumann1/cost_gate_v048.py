from __future__ import annotations

from dataclasses import dataclass

from .cached_cost_v046 import execute_v046
from .indexed_peeling_v043 import execute_peeling
from .mixed_coupled_dataset import MixedCoupledExample
from .stopping_gauntlet import FrozenV033Scorer


@dataclass(frozen=True)
class RouteResult:
    route: str
    answer: dict
    verified: bool
    fallback: bool


def prechoice_features(example: MixedCoupledExample) -> tuple[int, int, tuple[int, ...]]:
    matrix = example.full_system.A
    n = example.full_system.dimension
    incidences = tuple(sum(matrix[row][col] != 0 for row in range(n))
                       for col in range(n))
    return n, sum(incidences), tuple(sorted(incidences))


def run_static_gate(example: MixedCoupledExample, *, frozen_scorer: FrozenV033Scorer) -> RouteResult:
    _, _, incidences = prechoice_features(example)
    if 6 not in incidences:
        result = execute_peeling(example, frozen_scorer=frozen_scorer, indexed=True)
        return RouteResult("F1", result.answer, result.verified, False)
    proposed = execute_v046(example, frozen_scorer=frozen_scorer)
    if proposed.verified:
        return RouteResult("F3", proposed.answer, True, False)
    fallback = execute_peeling(example, frozen_scorer=frozen_scorer, indexed=True)
    return RouteResult("F1", fallback.answer, fallback.verified, True)
