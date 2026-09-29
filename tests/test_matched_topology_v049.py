from neumann1.cached_cost_v046 import execute_v046
from neumann1.cost_gate_v048 import prechoice_features, run_static_gate
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.matched_topology_v049_dataset import contract_pair
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.structural_compression import solve_exact_gauss_jordan, verify_exact_full_system


def test_matched_cheap_features_but_different_support():
    pair = contract_pair()
    positive, negative = pair.recoverable, pair.retained_support
    assert prechoice_features(positive) == prechoice_features(negative)
    assert 6 in prechoice_features(positive)[2]
    assert positive.signature != negative.signature
    for example in (positive, negative):
        answer, _ = solve_exact_gauss_jordan(example.full_system)
        ok, _ = verify_exact_full_system(example.full_system, answer)
        assert ok and all(answer[name] == value for name, value in
                          zip(example.full_system.variables, example.full_system.ground_truth))


def test_frozen_paths_and_gate_remain_exact():
    pair = contract_pair()
    scorer = fit_frozen_v033_scorer()
    for example in (pair.recoverable, pair.retained_support):
        f1 = execute_peeling(example, frozen_scorer=scorer, indexed=True)
        f3 = execute_v046(example, frozen_scorer=scorer)
        gate = run_static_gate(example, frozen_scorer=scorer)
        assert f1.verified and f3.verified and gate.verified
        assert f1.answer == f3.answer == gate.answer
        assert gate.route == "F3"
        assert not gate.fallback
    positive = execute_v046(pair.recoverable, frozen_scorer=scorer)
    negative = execute_v046(pair.retained_support, frozen_scorer=scorer)
    assert positive.retained_dimension + 2 == negative.retained_dimension
