from neumann1.cached_cost_v046 import execute_v046
from neumann1.cost_gate_v048 import prechoice_features, run_static_gate
from neumann1.cost_gate_v048_dataset import contract_examples
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def test_matched_dimension_and_route_contract():
    scorer = fit_frozen_v033_scorer()
    items = contract_examples()
    assert all(item.example.apparent_dimension == 16 for item in items)
    for item, expected_route in zip(items, ("F3", "F1", "F1")):
        features = prechoice_features(item.example)
        assert (6 in features[2]) == (expected_route == "F3")
        gated = run_static_gate(item.example, frozen_scorer=scorer)
        f1 = execute_peeling(item.example, frozen_scorer=scorer, indexed=True)
        f3 = execute_v046(item.example, frozen_scorer=scorer)
        assert gated.route == expected_route and not gated.fallback
        assert gated.verified and f1.verified and f3.verified
        assert gated.answer == f1.answer == f3.answer


def test_features_do_not_read_metadata():
    from dataclasses import replace

    item = contract_examples()[0].example
    shadow = replace(item, core_dimension=1, split="shadow", oracle_blocks=(),
                     oracle_easy_leaves=())
    assert prechoice_features(item) == prechoice_features(shadow)
