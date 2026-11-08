"""NEUMANN cost-aware meta-discovery admission, implemented in the CORE.

Q3 methodology: inventing a program-generating algorithm is only useful if
(1) it preserves/improves original capability and (2) discovery + future
repeated use beats the strongest matched cold classical strategy on cost.
Never celebrate candidate-count savings while ignoring source learning time.

This policy explicitly carries the accounting provenance of a measured
source run and a disjoint SOURCE validation run. Candidate unit-cost is
a source-derived Estimate, NOT a claim about target GPU FLOPs or cloud $.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import math

@dataclass(frozen=True)
class MetaUtilityEvidence:
    discovery_wall_seconds: float
    discovery_candidate_checks: int
    validation_tasks: int
    validation_cold_candidate_checks: int
    validation_learned_candidate_checks: int
    validation_cold_solved: int
    validation_learned_solved: int
    intended_future_tasks: int
    source_only: bool = True

    def __post_init__(self):
        if type(self.source_only) is not bool or not self.source_only:
            raise ValueError("non-source or target-peeking data cannot admit a method")
        for key in ("discovery_candidate_checks","validation_tasks",
                    "validation_cold_candidate_checks","validation_learned_candidate_checks",
                    "validation_cold_solved","validation_learned_solved",
                    "intended_future_tasks"):
            val=getattr(self,key)
            if type(val) is not int or val<0:
                raise ValueError("invalid source utility integer "+key)
        if not (math.isfinite(self.discovery_wall_seconds)
                and self.discovery_wall_seconds>=0):
            raise ValueError("invalid source discovery wall time")
        if not self.discovery_candidate_checks or not self.validation_tasks:
            raise ValueError("source cost calibration and validation tasks required")
        if self.intended_future_tasks<1:
            raise ValueError("positive target deployment horizon required")
        if (self.validation_cold_solved>self.validation_tasks or
                self.validation_learned_solved>self.validation_tasks):
            raise ValueError("source correct totals exceed task count")


@dataclass(frozen=True)
class MetaUtilityDecision:
    route: str
    reason: str
    estimate_unit_cost_seconds_per_candidate: float
    estimate_future_savings_seconds: float
    source_discovery_cost_seconds: float
    estimate_net_benefit_seconds: float
    estimate_break_even_tasks: float | None
    capability_comparison: str
    evidence_level: str

    @property
    def use_invented_first(self):
        return self.route=="INVENTED_FIRST"


def decide_meta_method(evidence: MetaUtilityEvidence) -> MetaUtilityDecision:
    """Conservative inequality, not a trained task-specific heuristic.

    Benefit = expected number of future saved candidate checks × observed
    source wall-time-per-check proxy. Because source wall time may include
    unrelated overhead, all resulting extrapolations are explicitly
    labelled Estimate. When no net savings or capability gain exists,
    delete the learned method from this family's target hot path.
    """
    unit=evidence.discovery_wall_seconds/evidence.discovery_candidate_checks
    d=(evidence.validation_cold_candidate_checks -
       evidence.validation_learned_candidate_checks)
    checks_per_task=d/evidence.validation_tasks
    seconds_per_task=checks_per_task*unit
    projected=seconds_per_task*evidence.intended_future_tasks
    net=projected-evidence.discovery_wall_seconds
    if seconds_per_task>0:
        breakeven=evidence.discovery_wall_seconds/seconds_per_task
    else:
        breakeven=None
    if evidence.validation_learned_solved<evidence.validation_cold_solved:
        route,reason,quality="CLASSICAL_FIRST","CAPABILITY_REGRESSION","BELOW_COLD"
    elif evidence.validation_learned_solved>evidence.validation_cold_solved:
        # Capability improvement has precedence but does NOT imply a cost
        # saving, 10x efficiency, or global Q3. Respect external budget caps.
        route,reason,quality="INVENTED_FIRST","VERIFIED_SOURCE_CAPABILITY_GAIN","ABOVE_COLD"
    elif net>0 and d>0:
        route,reason,quality="INVENTED_FIRST","POSITIVE_AMORTIZED_SOURCE_UTILITY","EQUAL_COLD"
    else:
        route,reason,quality="CLASSICAL_FIRST","NO_POSITIVE_SOURCE_NET_UTILITY","EQUAL_COLD"
    return MetaUtilityDecision(
        route=route,reason=reason,
        estimate_unit_cost_seconds_per_candidate=unit,
        estimate_future_savings_seconds=projected,
        source_discovery_cost_seconds=evidence.discovery_wall_seconds,
        estimate_net_benefit_seconds=net,
        estimate_break_even_tasks=breakeven,
        capability_comparison=quality,
        evidence_level="SOURCE_WALL_TIME_PER_CHECK_EXTRAPOLATION_ESTIMATE")


def source_evidence_dict(evidence: MetaUtilityEvidence):
    return asdict(evidence)
