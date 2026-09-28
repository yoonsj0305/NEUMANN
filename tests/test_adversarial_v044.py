from dataclasses import replace

from neumann1.adversarial_v044 import exact_schur_witness
from neumann1.adversarial_v044_dataset import v044_contract_examples
from neumann1.indexed_peeling_v043 import discover_indexed, execute_peeling
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan
from neumann1.block_discovery import route_incidence_one_locals


def test_high_incidence_fixture_has_verified_missed_elimination():
    high, _ = v044_contract_examples()
    example = high.example
    for name in high.high_targets:
        assert sum(row[example.full_system.variables.index(name)] != 0
                   for row in example.full_system.A) == 6
    oracle = materialize_mixed_reference(example)
    assert oracle is not None and oracle.verified and oracle.ground_truth_equivalent
    scorer = fit_frozen_v033_scorer()
    result = execute_peeling(example, frozen_scorer=scorer, indexed=True)
    assert result.verified
    assert result.retained_dimension > oracle.retained_system.dimension
    assert all(name not in (target for _, targets in result.block_keys for target in targets)
               for name in high.high_targets)
    local = route_incidence_one_locals(example, frozen_scorer=scorer)
    shadow = replace(example, oracle_blocks=(), oracle_easy_leaves=(), core_dimension=1)
    assert discover_indexed(example, local) == discover_indexed(shadow, local)


def test_dense_fixture_has_two_independent_exact_witnesses():
    _, dense = v044_contract_examples()
    example = dense.example
    _, baseline = solve_exact_gauss_jordan(example.full_system)
    witnesses = [exact_schur_witness(example.full_system, dense.witness.row_pair, pair)
                 for pair in dense.witness.target_pairs]
    assert dense.witness.target_pairs[0] != dense.witness.target_pairs[1]
    assert all(w is not None and w.verified and w.retained_dimension == example.apparent_dimension-2
               and w.retained_solver_ops < baseline.arithmetic_ops for w in witnesses)
    scorer = fit_frozen_v033_scorer()
    result = execute_peeling(example, frozen_scorer=scorer, indexed=True)
    assert result.verified and result.block_keys == () and result.local_keys == ()
    assert result.solver_ops == baseline.arithmetic_ops
