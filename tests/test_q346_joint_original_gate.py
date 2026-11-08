"""Real frozen original aggregate verdicts and explicit NON-evidence controls.

These regression fixtures use actual published PR #731 and ARC2 original FIRST
measured totals. The artificial positive cases test the gate only, not Q3.
"""
from dataclasses import replace
import pytest

from neumann1.q346_joint_evidence import (
    OriginalCohort, DiscoveryCost, evaluate_original_joint_gate)


def cohort(**changes):
    base=dict(name="toy",semantic_family="formalism.A",
              author="outside-lab",originals=20,
              learned_correct=12,strongest_matched_correct=10,
              learned_only_originals=2,learned_target_seconds=1.0,
              strongest_matched_target_seconds=100.0,
              upstream_frozen=True,original_verifier=True,
              same_input_rights=True,same_answer_attempts=True,
              new_grammar_witness=True,previously_unopened=True,
              training_domain_adapted=False,
              full_learned_execution_metered=True,
              full_comparator_execution_metered=True,
              independent_semantic_audit=True)
    base.update(changes)
    return OriginalCohort(**base)


def cost(**changes):
    fields=dict(preparation_seconds=0.0,training_seconds=0.0,
                discovery_seconds=0.0,verification_seconds=0.0,
                failed_attempts_seconds=0.0,fallback_seconds=0.0)
    fields.update(changes)
    return DiscoveryCost(**fields)


def test_real_arcagi2_original_first_verdict_stays_negative():
    # Official public ARC2 first: source 61.50174s, 0/120 both.
    evidence=cohort(
        name="ARC-AGI-2-public-FIRST-120",
        semantic_family="arc.2d.object-compositional-reasoning",
        originals=120,learned_correct=0,strongest_matched_correct=0,
        learned_only_originals=0,
        learned_target_seconds=26.34604,
        strongest_matched_target_seconds=26.28608,
        new_grammar_witness=False,
        training_domain_adapted=True,
        full_learned_execution_metered=False,
        full_comparator_execution_metered=False,
        independent_semantic_audit=False)
    result=evaluate_original_joint_gate(
        (evidence,),cost(discovery_seconds=61.50174))
    assert result.original_count==120
    assert result.learned_correct==result.comparator_correct==0
    assert result.source_inclusive_learned_seconds==pytest.approx(87.84778)
    assert result.matched_comparator_seconds==pytest.approx(26.28608)
    assert result.measured_speed_ratio==pytest.approx(0.299223,rel=0.001)
    assert not result.recommend_invention_hotpath
    assert result.q3=="NO_VERIFIED_NEW_RESIDUAL_CAPABILITY"
    assert result.q4=="OPEN_INCOMPLETE_FULL_COST_TELEMETRY"
    assert result.q6=="OPEN_UNRELATED_MATH_TRANSFER"


def test_real_1d_arc_360_originals_failure_of_joint_10x():
    # PR #731: SOURCE 24.76895 seconds; 176 vs strong hybrid 186/360.
    # Baseline is strong matched hybrid, NOT pure classical (classical 58).
    evidence=cohort(
        name="1d-arc-fourth-and-fifth-frozen-360",
        semantic_family="arc.spatial-object-reasoning",
        originals=360,learned_correct=176,strongest_matched_correct=186,
        learned_only_originals=None,
        learned_target_seconds=12.52114,
        strongest_matched_target_seconds=21.81670,
        new_grammar_witness=False,
        training_domain_adapted=True)
    result=evaluate_original_joint_gate(
        (evidence,),cost(discovery_seconds=24.76895))
    assert result.original_count==360
    assert result.source_inclusive_learned_seconds==pytest.approx(37.29009)
    assert result.measured_speed_ratio==pytest.approx(21.8167/37.29009)
    assert result.q3=="OPEN_RESIDUAL_WITNESS_MISSING"
    assert result.q4=="NO_10X_MATCHED_FULL_COST"
    assert result.q6=="OPEN_UNRELATED_MATH_TRANSFER"
    assert "verified original capability regression" in result.reasons
    assert not result.recommend_invention_hotpath


def test_aggregate_unrelated_positive_is_only_scoped_unit_fixture():
    # Purely a unit contract; numbers are invented, NOT empirical evidence.
    different=cohort(name="frozen-B",semantic_family="mathematics.B",
                     author="different-outside-author",
                     learned_target_seconds=1.0,
                     strongest_matched_target_seconds=100.0)
    a=cohort()
    result=evaluate_original_joint_gate(
        (a,different),
        cost(discovery_seconds=1,
                      preparation_seconds=.25,
                      training_seconds=.25,
                      verification_seconds=.25,
                      failed_attempts_seconds=.25,
                      fallback_seconds=.25))
    assert result.q3=="SCOPED_NEW_ORIGINAL_CAPABILITY"
    assert result.q4=="SCOPED_10X_FULL_COST_AND_EQUAL_ACCURACY"
    assert result.q6=="SCOPED_DIFFERENT_SEMANTIC_TRANSFER"
    assert result.recommend_invention_hotpath
    assert "GLOBAL" not in result.q3+result.q4+result.q6


def test_one_family_two_formats_is_not_cross_semantic_transfer():
    evidence=(cohort(name="grid1",semantic_family="same.graph.closure"),
              cohort(name="grid2",semantic_family="same.graph.closure"))
    r=evaluate_original_joint_gate(evidence,cost())
    assert r.q6=="OPEN_UNRELATED_MATH_TRANSFER"


def test_training_domain_adaptation_does_not_count_as_unadapted_q6():
    evidence=(cohort(name="a"),
              cohort(name="b",semantic_family="mathematics.B",
                     training_domain_adapted=True))
    r=evaluate_original_joint_gate(evidence,cost())
    assert r.q6=="OPEN_UNRELATED_MATH_TRANSFER"


def test_strong_baseline_saturates_all_originals_no_new_q3():
    evidence=cohort(learned_correct=20,strongest_matched_correct=20,
                    learned_only_originals=0)
    r=evaluate_original_joint_gate((evidence,),cost())
    assert r.q3=="NO_VERIFIED_NEW_RESIDUAL_CAPABILITY"


def test_original_provenance_or_rights_missing_always_hold():
    for key in ("upstream_frozen","original_verifier","same_input_rights",
                "same_answer_attempts","previously_unopened"):
        e=cohort(**{key:False})
        r=evaluate_original_joint_gate((e,),cost())
        assert r.q3==r.q4==r.q6=="HOLD_PROVENANCE"
        assert not r.recommend_invention_hotpath


def test_missing_witness_cannot_be_assumed_zero_or_positive():
    e=cohort(learned_only_originals=None)
    r=evaluate_original_joint_gate((e,),cost())
    assert r.q3=="OPEN_RESIDUAL_WITNESS_MISSING"


def test_better_cost_with_worse_accuracy_does_not_pass_q4():
    e=cohort(learned_correct=8,strongest_matched_correct=12,
             learned_only_originals=0,
             learned_target_seconds=.0001,
             strongest_matched_target_seconds=1000)
    r=evaluate_original_joint_gate((e,),cost())
    assert r.q4=="NO_10X_MATCHED_FULL_COST"


def test_all_source_costs_count_before_claiming_10x():
    e=cohort(learned_target_seconds=.1,
             strongest_matched_target_seconds=100)
    high=cost(preparation_seconds=40,training_seconds=40,
              discovery_seconds=10,verification_seconds=10,
              failed_attempts_seconds=4,fallback_seconds=1)
    r=evaluate_original_joint_gate((e,),high)
    assert r.q4=="NO_10X_MATCHED_FULL_COST"


def test_invalid_denominator_nan_forged_or_duplicate_rejected():
    with pytest.raises(ValueError):
        cohort(originals=0)
    with pytest.raises(ValueError):
        cohort(learned_only_originals=21)
    with pytest.raises(ValueError):
        cohort(learned_target_seconds=float('nan'))
    with pytest.raises(ValueError):
        cohort(author="")
    with pytest.raises(ValueError):
        cost(training_seconds=-1)
    with pytest.raises(ValueError):
        evaluate_original_joint_gate(
            (cohort(name="x"),cohort(name="x")),cost())


def test_unmeasured_target_cost_cannot_claim_tenfold_q4():
    e=cohort(full_learned_execution_metered=False,
             learned_target_seconds=.001,
             strongest_matched_target_seconds=10000)
    r=evaluate_original_joint_gate((e,),cost())
    assert r.q4=="OPEN_INCOMPLETE_FULL_COST_TELEMETRY"


def test_uncertified_unrelated_semantics_cannot_claim_q6():
    e1=cohort()
    e2=cohort(name="mathematics-b",semantic_family="unrelated.math.b",
              independent_semantic_audit=False)
    r=evaluate_original_joint_gate((e1,e2),cost())
    assert r.q6=="OPEN_UNRELATED_MATH_TRANSFER"
