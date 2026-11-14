"""G1 direct-program semantic novelty gate regression tests. No result fabrication."""
from dataclasses import replace
from research.q3.discovery_policy.ownweight_direct_program_evidence_gate_20261028 import (
    OwnWeightEvidence,assess_G1,actual_synthetic_v1_gate
)

def ideal():
    return OwnWeightEvidence(
        test_source="independent_external_original",
        independent_authors_established=True,
        task_family_heldout=True,
        executable_program_generated_directly=True,
        generated_structure_outside_preenumerated_templates=True,
        full_original_formal_proof_checked=True,
        trained_A_better_than_shuffled_B_across_seeds=True,
        stronger_classic_same_rights_checked=True,
        A_exact_solved=11,classic_exact_solved=6,
        A_full_compute_cpu_seconds=3.0,
        classic_full_compute_cpu_seconds=8.0,
        true_frontier_difficulty_grounded=True,
        independent_replay_passed=True
    )

def test_real_synthetic_neural_positive_does_not_close_G1():
    x=actual_synthetic_v1_gate()
    assert x['G1']=='HOLD' and x['Q1_Q7']=='OPEN'
    assert not x['auto_promote_to_PASS']
    assert 'NO_NOVEL_COMPOSITION_OUTSIDE_PREENUMERATED_TEMPLATES' in x['blocking_findings']
    assert 'NO_STRONGER_CAPABILITY_THAN_CLASSICAL' in x['blocking_findings']

def test_ideal_evidence_still_requires_human_review():
    x=assess_G1(ideal())
    assert x['G1']=='NEEDS_HUMAN_SCIENTIFIC_REVIEW'
    assert x['Q1_Q7']=='OPEN'
    assert not x['auto_promote_to_PASS']
    assert x['blocking_findings']==[]

def test_shuffled_label_control_missing_forces_hold():
    assert 'NO_REPLICATED_CAUSAL_A_VS_SHUFFLED_B' in assess_G1(
        replace(ideal(),trained_A_better_than_shuffled_B_across_seeds=False))['blocking_findings']

def test_generated_program_requires_new_structure():
    x=assess_G1(replace(ideal(),generated_structure_outside_preenumerated_templates=False))
    assert x['G1']=='HOLD'

def test_external_author_independence_cannot_be_synthetic():
    x=assess_G1(replace(ideal(),test_source='self_generated_synthetic'))
    assert 'INDEPENDENT_EXTERNAL_AUTHORS_NOT_ESTABLISHED' in x['blocking_findings']

def test_unknown_training_cost_does_not_pass():
    assert 'WHOLE_COMPUTATION_UNKNOWN' in assess_G1(
        replace(ideal(),A_full_compute_cpu_seconds=None))['blocking_findings']

def test_strong_classic_overmatches_training():
    x=assess_G1(replace(ideal(),A_exact_solved=6,classic_exact_solved=11))
    assert 'NO_STRONGER_CAPABILITY_THAN_CLASSICAL' in x['blocking_findings']

def test_semantic_proof_must_be_full():
    x=assess_G1(replace(ideal(),full_original_formal_proof_checked=False))
    assert 'NO_FULL_ORIGINAL_SEMANTIC_PROOF' in x['blocking_findings']

def test_frontier_difficulty_without_evidence_is_hold():
    x=assess_G1(replace(ideal(),true_frontier_difficulty_grounded=False))
    assert x['G1']=='HOLD'

def test_independent_replay_mandatory():
    x=assess_G1(replace(ideal(),independent_replay_passed=False))
    assert 'INDEPENDENT_REPLAY_MISSING' in x['blocking_findings']
