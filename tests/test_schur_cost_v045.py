from dataclasses import replace

from neumann1.adversarial_v044 import exact_schur_witness
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.mixed_coupled_dataset import generate_mixed_cell
from neumann1.schur_cost_v045 import discover_incidence_six, execute_v045
from neumann1.schur_cost_v045_dataset import v045_contract_examples
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.block_discovery import route_incidence_one_locals


def test_high_incidence_recovers_frozen_oracle_with_exact_answer():
    scorer = fit_frozen_v033_scorer()
    high, _ = v045_contract_examples()
    oracle = materialize_mixed_reference(high.example)
    old = execute_peeling(high.example, frozen_scorer=scorer, indexed=True)
    new = execute_v045(high.example, frozen_scorer=scorer)
    assert oracle and oracle.verified
    assert old.verified and new.verified and new.mode == "sparse"
    assert old.retained_dimension > oracle.retained_system.dimension
    assert new.retained_dimension == oracle.retained_system.dimension
    assert new.answer == old.answer == oracle.full_answer
    assert new.solver_ops == oracle.solver_counts.arithmetic_ops


def test_dense_fallback_exactly_substitutes_and_verifies():
    scorer = fit_frozen_v033_scorer()
    _, alt = v045_contract_examples()
    old = execute_peeling(alt.example, frozen_scorer=scorer, indexed=True)
    new = execute_v045(alt.example, frozen_scorer=scorer)
    witnesses = [exact_schur_witness(alt.example.full_system, alt.witness.row_pair, pair)
                 for pair in alt.witness.target_pairs]
    assert old.verified and old.retained_dimension == alt.example.apparent_dimension
    assert new.verified and new.mode == "schur"
    assert new.retained_dimension == alt.example.apparent_dimension - 2
    assert new.answer == old.answer == witnesses[0].answer == witnesses[1].answer
    assert new.solver_ops < old.solver_ops
    assert new.schur_construction_ops > 0


def test_high_degree_discovery_ignores_labels_and_core_dimension():
    scorer = fit_frozen_v033_scorer()
    high, _ = v045_contract_examples()
    local = route_incidence_one_locals(high.example, frozen_scorer=scorer)
    shadow = replace(high.example, oracle_blocks=(), oracle_easy_leaves=(), core_dimension=1)
    assert discover_incidence_six(high.example, local) == discover_incidence_six(shadow, local)


def test_controls_remain_full_without_proposals():
    scorer = fit_frozen_v033_scorer()
    for k in (2, 4):
        example = generate_mixed_cell(k, k, count=1, split="v045_control",
                                      seed=2_312_000+k)[0]
        result = execute_v045(example, frozen_scorer=scorer)
        assert result.verified and result.mode == "full"
        assert result.retained_dimension == k
        assert result.materialization_attempts == result.rejected_materializations == 0
