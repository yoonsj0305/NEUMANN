from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import json
from statistics import mean

import numpy as np
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .learned_compression import (
    AffineCandidate,
    candidate_features,
    enumerate_affine_candidates,
    materialize_reduction,
)
from .learned_compression_dataset import LearnedCompressionExample
from .structural_compression import solve_exact_gauss_jordan
from .utility_compression_dataset import v035_training_examples


V035_FEATURE_DIMENSION = 16
V035_HIDDEN_UNITS = 16
V035_RANDOM_STATE = 35
V035_ALPHA = 1e-3
V035_MAX_ITER = 1200


@dataclass(frozen=True)
class UtilityTrainingRow:
    features: tuple[float, ...]
    reference_label: int
    utility_target: float


@dataclass(frozen=True)
class UtilityTrainingSummary:
    examples: int
    candidates: int
    positive_reference_candidates: int
    positive_utility_candidates: int
    mean_utility_target: float
    max_utility_target: float


def _reference_keys(
    example: LearnedCompressionExample,
) -> frozenset[tuple[int, str]]:
    return frozenset(
        (rule.row_index, rule.target)
        for rule in example.oracle_dependencies
    )


def certified_one_step_solver_utility(
    example: LearnedCompressionExample,
    candidate: AffineCandidate,
    *,
    baseline_solver_ops: int | None = None,
) -> float:
    if baseline_solver_ops is None:
        _, baseline_counts = solve_exact_gauss_jordan(
            example.full_system
        )
        baseline_solver_ops = baseline_counts.arithmetic_ops

    reduction = materialize_reduction(
        example,
        (candidate,),
    )
    if reduction is None:
        return 0.0

    reduced_ops = reduction.solver_counts.arithmetic_ops
    savings = max(0, baseline_solver_ops - reduced_ops)
    if baseline_solver_ops <= 0:
        raise ValueError("baseline solver ops must be positive")

    return float(savings / baseline_solver_ops)


def collect_utility_training_rows(
    examples: tuple[LearnedCompressionExample, ...] | None = None,
) -> tuple[UtilityTrainingRow, ...]:
    examples = (
        examples
        if examples is not None
        else v035_training_examples()
    )
    rows: list[UtilityTrainingRow] = []

    for example in examples:
        reference = _reference_keys(example)
        _, baseline_counts = solve_exact_gauss_jordan(
            example.full_system
        )
        baseline_ops = baseline_counts.arithmetic_ops

        for candidate in enumerate_affine_candidates(
            example.full_system
        ):
            rows.append(
                UtilityTrainingRow(
                    features=candidate_features(
                        example.full_system,
                        candidate,
                    ),
                    reference_label=(
                        1 if candidate.key in reference else 0
                    ),
                    utility_target=certified_one_step_solver_utility(
                        example,
                        candidate,
                        baseline_solver_ops=baseline_ops,
                    ),
                )
            )

    if not rows:
        raise ValueError("utility training corpus is empty")
    return tuple(rows)


def summarize_training_rows(
    rows: tuple[UtilityTrainingRow, ...],
    *,
    examples: int,
) -> UtilityTrainingSummary:
    return UtilityTrainingSummary(
        examples=examples,
        candidates=len(rows),
        positive_reference_candidates=sum(
            row.reference_label
            for row in rows
        ),
        positive_utility_candidates=sum(
            1
            for row in rows
            if row.utility_target > 0.0
        ),
        mean_utility_target=mean(
            row.utility_target
            for row in rows
        ),
        max_utility_target=max(
            row.utility_target
            for row in rows
        ),
    )


def _matched_classifier() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(V035_HIDDEN_UNITS,),
                    activation="tanh",
                    solver="lbfgs",
                    alpha=V035_ALPHA,
                    max_iter=V035_MAX_ITER,
                    random_state=V035_RANDOM_STATE,
                ),
            ),
        ]
    )


def _matched_regressor() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=(V035_HIDDEN_UNITS,),
                    activation="tanh",
                    solver="lbfgs",
                    alpha=V035_ALPHA,
                    max_iter=V035_MAX_ITER,
                    random_state=V035_RANDOM_STATE,
                ),
            ),
        ]
    )


def fit_matched_v035_models(
    rows: tuple[UtilityTrainingRow, ...] | None = None,
) -> tuple[Pipeline, Pipeline, UtilityTrainingSummary]:
    training_examples = v035_training_examples()
    rows = (
        rows
        if rows is not None
        else collect_utility_training_rows(training_examples)
    )

    X = np.asarray(
        [row.features for row in rows],
        dtype=float,
    )
    y_reference = np.asarray(
        [row.reference_label for row in rows],
        dtype=int,
    )
    y_utility = np.asarray(
        [row.utility_target for row in rows],
        dtype=float,
    )

    if X.shape[1] != V035_FEATURE_DIMENSION:
        raise AssertionError("v0.0.35 feature dimension drift")
    if set(y_reference.tolist()) != {0, 1}:
        raise ValueError(
            "reference training labels require both classes"
        )

    reference_model = _matched_classifier()
    utility_model = _matched_regressor()

    with threadpool_limits(limits=1):
        reference_model.fit(X, y_reference)
        utility_model.fit(X, y_utility)

    ref_scaler = reference_model.named_steps["scale"]
    utility_scaler = utility_model.named_steps["scale"]
    if not np.array_equal(
        ref_scaler.mean_,
        utility_scaler.mean_,
    ):
        raise AssertionError("matched scaler mean drift")
    if not np.array_equal(
        ref_scaler.scale_,
        utility_scaler.scale_,
    ):
        raise AssertionError("matched scaler scale drift")

    summary = summarize_training_rows(
        rows,
        examples=len(training_examples),
    )
    return reference_model, utility_model, summary


def _pipeline_state(
    pipeline: Pipeline,
    *,
    model_kind: str,
) -> dict[str, object]:
    scaler = pipeline.named_steps["scale"]
    mlp = pipeline.named_steps["mlp"]

    arrays = (
        scaler.mean_.astype("<f8", copy=False),
        scaler.scale_.astype("<f8", copy=False),
        mlp.coefs_[0].astype("<f8", copy=False),
        mlp.intercepts_[0].astype("<f8", copy=False),
        mlp.coefs_[1].astype("<f8", copy=False),
        mlp.intercepts_[1].astype("<f8", copy=False),
    )
    values = np.concatenate(
        [
            array.reshape(-1)
            for array in arrays
        ]
    )
    if values.size != 321:
        raise AssertionError("v0.0.35 checkpoint layout drift")

    raw = values.astype("<f8", copy=False).tobytes(order="C")
    sha = hashlib.sha256(
        (
            f"NEUMANN-v035-{model_kind}-checkpoint\0"
        ).encode("ascii")
        + raw
    ).hexdigest()

    return {
        "model_kind": model_kind,
        "feature_dimension": V035_FEATURE_DIMENSION,
        "hidden_units": V035_HIDDEN_UNITS,
        "fitted_weight_bias_scalars": 289,
        "scaler_state_scalars": 32,
        "float64_value_count": 321,
        "state_sha256": sha,
        "float64_b64": base64.b64encode(raw).decode("ascii"),
    }


def export_matched_v035_checkpoint_bundle() -> dict[str, object]:
    reference, utility, summary = fit_matched_v035_models()

    return {
        "format": "neumann1_v035_matched_checkpoint_bundle_v1",
        "training_contract": {
            "feature_dimension": V035_FEATURE_DIMENSION,
            "hidden_units": V035_HIDDEN_UNITS,
            "random_state": V035_RANDOM_STATE,
            "alpha": V035_ALPHA,
            "max_iter": V035_MAX_ITER,
            "training_examples": summary.examples,
            "training_candidates": summary.candidates,
            "positive_reference_candidates": (
                summary.positive_reference_candidates
            ),
            "positive_utility_candidates": (
                summary.positive_utility_candidates
            ),
            "mean_utility_target": summary.mean_utility_target,
            "max_utility_target": summary.max_utility_target,
        },
        "reference_classifier": _pipeline_state(
            reference,
            model_kind="matched-reference-classifier",
        ),
        "utility_regressor": _pipeline_state(
            utility,
            model_kind="matched-utility-regressor",
        ),
    }


def canonical_bundle_json(
    bundle: dict[str, object],
) -> str:
    return json.dumps(
        bundle,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
