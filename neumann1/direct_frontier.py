from __future__ import annotations

from dataclasses import dataclass
import time
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPClassifier, MLPRegressor

from .paired_linear_dataset import PairedLinearExample
from .paired_token_baseline import FixedPositionTokenEncoder


SOLUTION_MIN = -4
SOLUTION_MAX = 4
SOLUTION_CARDINALITY = SOLUTION_MAX - SOLUTION_MIN + 1
PAIR_CLASS_COUNT = SOLUTION_CARDINALITY ** 2


@dataclass(frozen=True)
class DirectFrontierConfig:
    training_size: int
    hidden_units: int


@dataclass(frozen=True)
class DirectFrontierModels:
    config: DirectFrontierConfig
    encoder: FixedPositionTokenEncoder
    regressor: MLPRegressor
    classifier: MLPClassifier
    solution_scale: float
    regression_training_seconds: float
    classifier_training_seconds: float
    regression_convergence_warning: bool
    classifier_convergence_warning: bool


@dataclass(frozen=True)
class DirectModelFootprint:
    parameter_count: int
    layer_shapes: tuple[tuple[int, int], ...]
    dense_weighted_sum_terms_proxy: int


@dataclass(frozen=True)
class DirectPrediction:
    raw_regression: tuple[float, float]
    rounded_regression: tuple[float, float]
    discrete_classification: tuple[float, float]
    regression_wall_seconds: float
    classifier_wall_seconds: float


def frontier_configs() -> tuple[DirectFrontierConfig, ...]:
    return tuple(
        DirectFrontierConfig(training_size=size, hidden_units=width)
        for size in (128, 512, 2048)
        for width in (8, 16, 32, 64)
    )


def solution_pair_to_class(
    solution: tuple[float, float],
) -> int:
    x, y = solution
    xi = int(round(float(x)))
    yi = int(round(float(y)))
    if not (
        SOLUTION_MIN <= xi <= SOLUTION_MAX
        and SOLUTION_MIN <= yi <= SOLUTION_MAX
    ):
        raise ValueError("solution pair outside declared integer support")
    return (
        (xi - SOLUTION_MIN) * SOLUTION_CARDINALITY
        + (yi - SOLUTION_MIN)
    )


def class_to_solution_pair(
    class_id: int,
) -> tuple[float, float]:
    if not 0 <= int(class_id) < PAIR_CLASS_COUNT:
        raise ValueError("class id outside declared solution-pair support")
    class_id = int(class_id)
    x = class_id // SOLUTION_CARDINALITY + SOLUTION_MIN
    y = class_id % SOLUTION_CARDINALITY + SOLUTION_MIN
    return float(x), float(y)


def _new_regressor(
    hidden_units: int,
    *,
    random_state: int,
) -> MLPRegressor:
    return MLPRegressor(
        hidden_layer_sizes=(hidden_units,),
        activation="tanh",
        solver="adam",
        alpha=1e-2,
        max_iter=2000,
        random_state=random_state,
        learning_rate_init=0.003,
        tol=1e-6,
    )


def _new_classifier(
    hidden_units: int,
    *,
    random_state: int,
) -> MLPClassifier:
    return MLPClassifier(
        hidden_layer_sizes=(hidden_units,),
        activation="tanh",
        solver="adam",
        alpha=1e-2,
        max_iter=2000,
        random_state=random_state,
        learning_rate_init=0.003,
        tol=1e-6,
    )


def fit_direct_frontier_models(
    training_pool: tuple[PairedLinearExample, ...],
    config: DirectFrontierConfig,
    *,
    random_state: int = 29,
) -> DirectFrontierModels:
    if config.training_size < 81:
        raise ValueError(
            "frontier training size must cover all 81 solution classes"
        )
    if config.training_size > len(training_pool):
        raise ValueError("training size exceeds provided pool")
    if config.hidden_units < 1:
        raise ValueError("hidden_units must be >= 1")

    training = training_pool[: config.training_size]
    encoder = FixedPositionTokenEncoder()
    x = encoder.encode_many(example.text for example in training)

    solution_scale = 4.0
    regression_targets = np.asarray(
        [example.solution for example in training],
        dtype=float,
    ) / solution_scale

    class_targets = np.asarray(
        [solution_pair_to_class(example.solution) for example in training],
        dtype=int,
    )
    observed_classes = set(map(int, class_targets))
    if len(observed_classes) != PAIR_CLASS_COUNT:
        raise RuntimeError(
            "solution-covered training prefix does not contain all 81 classes"
        )

    regressor = _new_regressor(
        config.hidden_units,
        random_state=random_state,
    )
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        regressor.fit(x, regression_targets)
    regression_training_seconds = time.perf_counter() - start
    regression_convergence_warning = any(
        isinstance(item.message, ConvergenceWarning)
        for item in caught
    )

    classifier = _new_classifier(
        config.hidden_units,
        random_state=random_state,
    )
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        classifier.fit(x, class_targets)
    classifier_training_seconds = time.perf_counter() - start
    classifier_convergence_warning = any(
        isinstance(item.message, ConvergenceWarning)
        for item in caught
    )

    if len(classifier.classes_) != PAIR_CLASS_COUNT:
        raise RuntimeError(
            "classifier did not retain all 81 declared solution classes"
        )

    return DirectFrontierModels(
        config=config,
        encoder=encoder,
        regressor=regressor,
        classifier=classifier,
        solution_scale=solution_scale,
        regression_training_seconds=regression_training_seconds,
        classifier_training_seconds=classifier_training_seconds,
        regression_convergence_warning=regression_convergence_warning,
        classifier_convergence_warning=classifier_convergence_warning,
    )


def model_footprint(model: object) -> DirectModelFootprint:
    weights = getattr(model, "coefs_", None)
    biases = getattr(model, "intercepts_", None)
    if weights is None or biases is None:
        raise RuntimeError("model must be fit before footprint inspection")

    parameter_count = int(
        sum(matrix.size for matrix in weights)
        + sum(vector.size for vector in biases)
    )
    shapes = tuple(
        (int(matrix.shape[0]), int(matrix.shape[1]))
        for matrix in weights
    )
    weighted_terms = int(sum(matrix.size for matrix in weights))
    return DirectModelFootprint(
        parameter_count=parameter_count,
        layer_shapes=shapes,
        dense_weighted_sum_terms_proxy=weighted_terms,
    )


def predict_direct(
    models: DirectFrontierModels,
    text: str,
) -> DirectPrediction:
    encoded = models.encoder.encode(text).reshape(1, -1)

    start = time.perf_counter()
    raw = models.regressor.predict(encoded)[0]
    regression_wall_seconds = time.perf_counter() - start
    raw_solution = (
        float(raw[0] * models.solution_scale),
        float(raw[1] * models.solution_scale),
    )
    rounded_solution = tuple(
        float(
            min(
                SOLUTION_MAX,
                max(SOLUTION_MIN, round(value)),
            )
        )
        for value in raw_solution
    )

    start = time.perf_counter()
    predicted_class = int(models.classifier.predict(encoded)[0])
    classifier_wall_seconds = time.perf_counter() - start
    classified_solution = class_to_solution_pair(predicted_class)

    return DirectPrediction(
        raw_regression=raw_solution,
        rounded_regression=(
            float(rounded_solution[0]),
            float(rounded_solution[1]),
        ),
        discrete_classification=classified_solution,
        regression_wall_seconds=regression_wall_seconds,
        classifier_wall_seconds=classifier_wall_seconds,
    )
