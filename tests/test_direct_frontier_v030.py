from __future__ import annotations

from functools import lru_cache

from neumann1.direct_frontier import (
    PAIR_CLASS_COUNT,
    DirectFrontierConfig,
    class_to_solution_pair,
    fit_direct_frontier_models,
    frontier_configs,
    model_footprint,
    predict_direct,
    solution_pair_to_class,
)
from neumann1.paired_linear_dataset import (
    direct_frontier_final_examples,
    direct_frontier_training_pool,
    direct_frontier_validation_examples,
    paired_linear_final_examples,
    paired_linear_training_examples,
    paired_linear_validation_examples,
)


@lru_cache(maxsize=1)
def _small_models():
    return fit_direct_frontier_models(
        direct_frontier_training_pool(),
        DirectFrontierConfig(
            training_size=128,
            hidden_units=8,
        ),
        random_state=29,
    )


def test_v030_solution_pair_class_round_trip_is_complete():
    observed = set()

    for x in range(-4, 5):
        for y in range(-4, 5):
            class_id = solution_pair_to_class((x, y))
            observed.add(class_id)
            assert class_to_solution_pair(class_id) == (
                float(x),
                float(y),
            )

    assert observed == set(range(PAIR_CLASS_COUNT))
    assert PAIR_CLASS_COUNT == 81


def test_v030_training_prefixes_cover_all_solution_classes():
    pool = direct_frontier_training_pool()
    assert len(pool) == 2048

    expected = set(range(81))
    for size in (128, 512, 2048):
        observed = {
            solution_pair_to_class(example.solution)
            for example in pool[:size]
        }
        assert observed == expected


def test_v030_frontier_splits_are_disjoint_from_each_other_and_v029():
    train = {
        example.text
        for example in direct_frontier_training_pool()
    }
    validation = {
        example.text
        for example in direct_frontier_validation_examples()
    }
    final = {
        example.text
        for example in direct_frontier_final_examples()
    }
    old = {
        example.text
        for dataset in (
            paired_linear_training_examples(),
            paired_linear_validation_examples(),
            paired_linear_final_examples(),
        )
        for example in dataset
    }

    assert train.isdisjoint(validation)
    assert train.isdisjoint(final)
    assert validation.isdisjoint(final)
    assert train.isdisjoint(old)
    assert validation.isdisjoint(old)
    assert final.isdisjoint(old)


def test_v030_frontier_grid_is_pre_registered():
    configs = frontier_configs()

    assert len(configs) == 12
    assert {
        config.training_size for config in configs
    } == {128, 512, 2048}
    assert {
        config.hidden_units for config in configs
    } == {8, 16, 32, 64}


def test_v030_small_direct_challengers_fit_and_have_positive_cost():
    models = _small_models()
    reg = model_footprint(models.regressor)
    clf = model_footprint(models.classifier)

    assert reg.parameter_count > 0
    assert clf.parameter_count > reg.parameter_count
    assert reg.dense_weighted_sum_terms_proxy > 0
    assert clf.dense_weighted_sum_terms_proxy > 0
    assert reg.layer_shapes[0] == (640, 8)
    assert reg.layer_shapes[-1] == (8, 2)
    assert clf.layer_shapes[0] == (640, 8)
    assert clf.layer_shapes[-1] == (8, 81)
    assert isinstance(models.regression_convergence_warning, bool)
    assert isinstance(models.classifier_convergence_warning, bool)


def test_v030_direct_prediction_exposes_all_three_challengers():
    models = _small_models()
    example = direct_frontier_validation_examples()[0]
    prediction = predict_direct(models, example.text)

    assert len(prediction.raw_regression) == 2
    assert len(prediction.rounded_regression) == 2
    assert len(prediction.discrete_classification) == 2
    assert all(
        value.is_integer()
        for value in prediction.rounded_regression
    )
    assert all(
        -4.0 <= value <= 4.0
        for value in prediction.rounded_regression
    )
    assert all(
        value.is_integer()
        for value in prediction.discrete_classification
    )
