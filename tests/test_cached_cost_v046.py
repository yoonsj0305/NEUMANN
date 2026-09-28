from dataclasses import replace

from neumann1.block_discovery import route_incidence_one_locals
from neumann1.cached_cost_v046 import discover_cached_six, execute_v046
from neumann1.cached_cost_v046_dataset import v046_contract_examples
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.indexed_peeling_v043_dataset import v043_contract_examples
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.mixed_coupled_dataset import generate_mixed_cell
from neumann1.schur_cost_v045 import execute_v045
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def test_cached_high_degree_matches_full_oracle_and_f2():
    scorer = fit_frozen_v033_scorer()
    high, _ = v046_contract_examples()
    reference = materialize_mixed_reference(high.example)
    old = execute_v045(high.example, frozen_scorer=scorer)
    new = execute_v046(high.example, frozen_scorer=scorer)
    assert reference and reference.verified and old.verified and new.verified
    assert new.local_keys == old.local_keys
    assert new.block_keys == old.block_keys
    assert new.answer == old.answer == reference.full_answer
    assert new.retained_dimension == old.retained_dimension == reference.retained_system.dimension
    assert new.solver_ops == old.solver_ops == reference.solver_counts.arithmetic_ops
    assert new.derivations < old.derivations / 2
    assert new.checkers < old.checkers / 2


def test_dense_abstention_matches_frozen_f1():
    scorer = fit_frozen_v033_scorer()
    _, dense = v046_contract_examples()
    baseline = execute_peeling(dense.example, frozen_scorer=scorer, indexed=True)
    new = execute_v046(dense.example, frozen_scorer=scorer)
    assert baseline.verified and new.verified
    assert new.local_keys == baseline.local_keys == ()
    assert new.block_keys == baseline.block_keys == ()
    assert new.answer == baseline.answer
    assert new.retained_dimension == baseline.retained_dimension
    assert new.solver_ops == baseline.solver_ops
    assert new.materialization_attempts == 0


def test_cached_selection_handles_prior_overlap_and_coefficient_fixtures():
    scorer = fit_frozen_v033_scorer()
    for _, example in v043_contract_examples():
        old = execute_v045(example, frozen_scorer=scorer)
        new = execute_v046(example, frozen_scorer=scorer)
        assert old.verified and new.verified
        assert new.local_keys == old.local_keys
        assert new.block_keys == old.block_keys
        assert new.answer == old.answer
        assert new.retained_dimension == old.retained_dimension


def test_cached_discovery_blind_to_oracle_metadata():
    scorer = fit_frozen_v033_scorer()
    high, _ = v046_contract_examples()
    local = route_incidence_one_locals(high.example, frozen_scorer=scorer)
    shadow = replace(high.example, oracle_blocks=(), oracle_easy_leaves=(), core_dimension=1)
    assert discover_cached_six(high.example, local) == discover_cached_six(shadow, local)


def test_controls_remain_unchanged():
    scorer = fit_frozen_v033_scorer()
    for k in (2, 4):
        example = generate_mixed_cell(k, k, count=1, split="v046_control",
                                      seed=2_612_000+k)[0]
        result = execute_v046(example, frozen_scorer=scorer)
        assert result.verified and result.retained_dimension == k
        assert result.local_keys == result.block_keys == ()
        assert result.rejected_materializations == 0
