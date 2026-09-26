from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Mapping


@dataclass(frozen=True)
class RuntimeCostAssessment:
    dispatch_count: int
    total_dispatch_seconds: float
    total_service_seconds: float
    total_outside_service_seconds: float
    outside_service_fraction: float
    dispatch_to_service_ratio: float
    median_dispatch_ms: float
    median_service_ms: float
    median_outside_service_ms: float
    performance_diagnosis: str
    next_performance_experiment: str


def assess_dispatch_timings(
    timings: Iterable[Mapping[str, float | str | int]],
) -> RuntimeCostAssessment:
    rows = tuple(timings)
    if not rows:
        raise ValueError("at least one dispatch timing is required")

    dispatch = [float(row["dispatch_seconds"]) for row in rows]
    service = [float(row["service_seconds"]) for row in rows]
    outside = [float(row["outside_service_seconds"]) for row in rows]

    if any(value < 0 for value in dispatch + service + outside):
        raise ValueError("timings must be nonnegative")

    total_dispatch = sum(dispatch)
    total_service = sum(service)
    total_outside = sum(outside)
    outside_fraction = total_outside / total_dispatch if total_dispatch else 0.0
    ratio = (
        total_dispatch / total_service
        if total_service > 0
        else float("inf")
    )

    # Prototype decision gate, frozen before CI measurement:
    # If more than half of dispatch time is outside measured plugin service,
    # fresh-process lifecycle overhead dominates this microbenchmark.
    if outside_fraction >= 0.50:
        diagnosis = "fresh_process_lifecycle_dominated"
        next_experiment = "persistent_worker_lifecycle"
    else:
        diagnosis = "plugin_service_dominated_or_mixed"
        next_experiment = "measure_representative_workloads_before_runtime_change"

    return RuntimeCostAssessment(
        dispatch_count=len(rows),
        total_dispatch_seconds=total_dispatch,
        total_service_seconds=total_service,
        total_outside_service_seconds=total_outside,
        outside_service_fraction=outside_fraction,
        dispatch_to_service_ratio=ratio,
        median_dispatch_ms=median(dispatch) * 1000.0,
        median_service_ms=median(service) * 1000.0,
        median_outside_service_ms=median(outside) * 1000.0,
        performance_diagnosis=diagnosis,
        next_performance_experiment=next_experiment,
    )