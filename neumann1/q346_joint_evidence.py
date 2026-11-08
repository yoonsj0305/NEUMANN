"""Evidence-based Q3/Q4/Q6 joint decision, using ORIGINAL cohorts and full cost.

This is deliberately a falsification gate, not a new invention algorithm.
A positive on a finite benchmark is never 'universal general intelligence'.
Original verifiers, task authorship, and authentic source model freezes
remain independent responsibilities; this evaluator cannot authenticate them
from self-reported strings.
"""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class OriginalCohort:
    name: str
    semantic_family: str
    author: str
    originals: int
    learned_correct: int
    strongest_matched_correct: int
    learned_only_originals: int | None
    learned_target_seconds: float
    strongest_matched_target_seconds: float
    upstream_frozen: bool
    original_verifier: bool
    same_input_rights: bool
    same_answer_attempts: bool
    new_grammar_witness: bool
    previously_unopened: bool
    training_domain_adapted: bool = False

    def __post_init__(self):
        if not self.name or not self.semantic_family or not self.author:
            raise ValueError("source labels and author required")
        if type(self.originals) is not int or self.originals < 1:
            raise ValueError("positive original denominator")
        for count in (self.learned_correct, self.strongest_matched_correct):
            if type(count) is not int or count < 0 or count > self.originals:
                raise ValueError("invalid number of correct originals")
        if self.learned_only_originals is not None:
            if (type(self.learned_only_originals) is not int or
                    self.learned_only_originals < 0 or
                    self.learned_only_originals > self.learned_correct):
                raise ValueError("invalid exact residual witness count")
        for cost in (self.learned_target_seconds,
                     self.strongest_matched_target_seconds):
            if type(cost) not in (float, int) or not math.isfinite(cost) or cost < 0:
                raise ValueError("missing/invalid nonnegative full candidate runtime")
        for flag in (self.upstream_frozen, self.original_verifier,
                     self.same_input_rights, self.same_answer_attempts,
                     self.new_grammar_witness, self.previously_unopened,
                     self.training_domain_adapted):
            if type(flag) is not bool:
                raise ValueError("real boolean evidence fields required")

    @property
    def original_authority(self):
        return (self.upstream_frozen and self.original_verifier
                and self.same_input_rights and self.same_answer_attempts
                and self.previously_unopened)


@dataclass(frozen=True)
class DiscoveryCost:
    preparation_seconds: float = 0.0
    training_seconds: float = 0.0
    discovery_seconds: float = 0.0
    verification_seconds: float = 0.0
    failed_attempts_seconds: float = 0.0
    fallback_seconds: float = 0.0

    def __post_init__(self):
        for v in self.__dict__.values():
            if type(v) not in (float, int) or not math.isfinite(v) or v < 0:
                raise ValueError("complete finite nonnegative time meters required")

    @property
    def total_seconds(self):
        return sum(self.__dict__.values())


@dataclass(frozen=True)
class JointFinding:
    q3: str
    q4: str
    q6: str
    recommend_invention_hotpath: bool
    original_count: int
    learned_correct: int
    comparator_correct: int
    source_inclusive_learned_seconds: float
    matched_comparator_seconds: float
    measured_speed_ratio: float | None
    reasons: tuple[str, ...]


def evaluate_original_joint_gate(cohorts: tuple[OriginalCohort, ...],
                                  discovery: DiscoveryCost,
                                  *, requested_speedup=10.0):
    """Compare matched originals, new generated witnesses and amortized total time.

    Q3 scoped positive requires independent original verified NEW executable
    program that solves a gap the strongest classical comparator did not.
    Q6 scoped cross-semantic transfer requires >=2 separate semantic families
    with those positive witnesses; simply changing data encoding never counts.
    Q4 requires equal-or-greater verified correctness AND total discovery +
    failed attempts + target inference cost to be <=1/target_speedup of the
    strongest matched classical TOTAL cost. Explicit recorded costs are not
    a claim to model FLOPs, electricity or frontier cloud-equivalence.

    Returns only scoped evidence decisions. Never 'global universal PASS'.
    """
    if not cohorts or not isinstance(discovery, DiscoveryCost):
        raise ValueError("cohorts and complete discovery cost required")
    if (type(requested_speedup) not in (int, float)
            or not math.isfinite(requested_speedup) or requested_speedup <= 0):
        raise ValueError("positive speedup target required")
    if len(set(c.name for c in cohorts)) != len(cohorts):
        raise ValueError("duplicate original cohort")
    if any(not c.original_authority for c in cohorts):
        return JointFinding("HOLD_PROVENANCE","HOLD_PROVENANCE","HOLD_PROVENANCE",
                            False, 0,0,0,0,0,None,
                            ("unverified original/author/source rights",))
    n=sum(c.originals for c in cohorts)
    learned=sum(c.learned_correct for c in cohorts)
    comparator=sum(c.strongest_matched_correct for c in cohorts)
    learn_time=(discovery.total_seconds
                +sum(c.learned_target_seconds for c in cohorts))
    comparator_time=sum(c.strongest_matched_target_seconds for c in cohorts)
    ratio=(comparator_time/learn_time) if learn_time>0 else None
    observed_residual=any((c.learned_only_originals or 0)>0
                          and c.new_grammar_witness for c in cohorts)
    residual_unknown=any(c.learned_only_originals is None for c in cohorts)
    transfer_domains={c.semantic_family for c in cohorts
                      if c.new_grammar_witness
                      and (c.learned_only_originals or 0)>0
                      and not c.training_domain_adapted}
    q3=("SCOPED_NEW_ORIGINAL_CAPABILITY" if observed_residual else
        "OPEN_RESIDUAL_WITNESS_MISSING" if residual_unknown else
        "NO_VERIFIED_NEW_RESIDUAL_CAPABILITY")
    q6=("SCOPED_DIFFERENT_SEMANTIC_TRANSFER"
        if len(transfer_domains)>=2 else
        "OPEN_UNRELATED_MATH_TRANSFER")
    capability_ok=learned>=classic
    q4=("SCOPED_10X_FULL_COST_AND_EQUAL_ACCURACY"
        if capability_ok and learn_time>0 and comparator_time>=learn_time*requested_speedup
        else "NO_10X_MATCHED_FULL_COST")
    reasons=[]
    if learned<comparator:
        reasons.append("verified original capability regression")
    if discovery.total_seconds>0:
        reasons.append("includes source preparation/training/discovery/verification costs")
    if q3!="SCOPED_NEW_ORIGINAL_CAPABILITY":
        reasons.append("no independently verified generated-only residual witness")
    if len(transfer_domains)<2:
        reasons.append("no independent new-capability transfer to two unrelated semantic families")
    if q4!="SCOPED_10X_FULL_COST_AND_EQUAL_ACCURACY":
        reasons.append("10x end-to-end equal-accuracy evidence absent")
    # Only source-proven novelty + multi-semantic transfer + full cost gate
    # would even warrant a broader external scientific audit.
    return JointFinding(
        q3,q4,q6,
        all((q3=="SCOPED_NEW_ORIGINAL_CAPABILITY",
             q4=="SCOPED_10X_FULL_COST_AND_EQUAL_ACCURACY",
             q6=="SCOPED_DIFFERENT_SEMANTIC_TRANSFER")),
        n,learned,comparator,learn_time,comparator_time,ratio,tuple(reasons))
