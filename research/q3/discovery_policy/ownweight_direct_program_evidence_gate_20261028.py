"""Fail-closed scoped evidence gate for NEUMANN 1 learned structure G1.

No self-reported model scores can alone become a scientific PASS. The gate
is a decision aid, not a substitute for independently checking receipts.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class OwnWeightEvidence:
    test_source: str
    independent_authors_established: bool
    task_family_heldout: bool
    executable_program_generated_directly: bool
    generated_structure_outside_preenumerated_templates: bool
    full_original_formal_proof_checked: bool
    trained_A_better_than_shuffled_B_across_seeds: bool
    stronger_classic_same_rights_checked: bool
    A_exact_solved: int
    classic_exact_solved: int
    A_full_compute_cpu_seconds: Optional[float]
    classic_full_compute_cpu_seconds: Optional[float]
    true_frontier_difficulty_grounded: bool
    independent_replay_passed: bool

def assess_G1(e: OwnWeightEvidence) -> dict:
    """Return HOLD with explicit blockers unless *all* independent conditions.

    Even a positive automated audit has status NEEDS_HUMAN_SCIENTIFIC_REVIEW,
    never automatically promotes Q1-Q7 or merges a research PR.
    """
    blocks=[]
    if e.test_source != "independent_external_original" or not e.independent_authors_established:
        blocks.append("INDEPENDENT_EXTERNAL_AUTHORS_NOT_ESTABLISHED")
    if not e.task_family_heldout:
        blocks.append("UNSEEN_TASK_FAMILY_NOT_DEMONSTRATED")
    if not e.executable_program_generated_directly:
        blocks.append("NO_LEARNED_DIRECT_EXECUTABLE_PROGRAM_GENERATION")
    if not e.generated_structure_outside_preenumerated_templates:
        blocks.append("NO_NOVEL_COMPOSITION_OUTSIDE_PREENUMERATED_TEMPLATES")
    if not e.full_original_formal_proof_checked:
        blocks.append("NO_FULL_ORIGINAL_SEMANTIC_PROOF")
    if not e.trained_A_better_than_shuffled_B_across_seeds:
        blocks.append("NO_REPLICATED_CAUSAL_A_VS_SHUFFLED_B")
    if not e.stronger_classic_same_rights_checked:
        blocks.append("MISSING_STRONGEST_SAME_RIGHT_CLASSICAL_CONTROL")
    if e.A_exact_solved <= e.classic_exact_solved:
        blocks.append("NO_STRONGER_CAPABILITY_THAN_CLASSICAL")
    if e.A_full_compute_cpu_seconds is None or e.classic_full_compute_cpu_seconds is None:
        blocks.append("WHOLE_COMPUTATION_UNKNOWN")
    elif e.A_full_compute_cpu_seconds >= e.classic_full_compute_cpu_seconds:
        blocks.append("NO_FULL_COMPUTE_ADVANTAGE")
    if not e.true_frontier_difficulty_grounded:
        blocks.append("FRONTIER_DIFFICULTY_NOT_GROUNDED")
    if not e.independent_replay_passed:
        blocks.append("INDEPENDENT_REPLAY_MISSING")
    return {
        "G1": "HOLD" if blocks else "NEEDS_HUMAN_SCIENTIFIC_REVIEW",
        "Q1_Q7": "OPEN",
        "auto_promote_to_PASS": False,
        "blocking_findings": blocks,
    }

def actual_synthetic_v1_gate() -> dict:
    """Frozen fact pattern from 2026-10-28 real 6-model direct-AST audit.

    A_seed29 solves 117/145 ID, 3/145 shifted, 0/80 cubic.
    Classic C solves 145/145 +145/145 +80/80 with lower measured CPU.
    A learning positive in-grammar but global G1 cannot be promoted.
    """
    evidence=OwnWeightEvidence(
        test_source="self_generated_synthetic",
        independent_authors_established=False,
        task_family_heldout=False,
        executable_program_generated_directly=True,
        generated_structure_outside_preenumerated_templates=False,
        full_original_formal_proof_checked=True,
        trained_A_better_than_shuffled_B_across_seeds=True,
        stronger_classic_same_rights_checked=True,
        A_exact_solved=117+3+0,
        classic_exact_solved=370,
        A_full_compute_cpu_seconds=20.275874,
        classic_full_compute_cpu_seconds=2.615313,
        true_frontier_difficulty_grounded=False,
        independent_replay_passed=True,
    )
    return assess_G1(evidence)

if __name__ == "__main__":
    import json
    print(json.dumps(actual_synthetic_v1_gate(), sort_keys=True, indent=2))
