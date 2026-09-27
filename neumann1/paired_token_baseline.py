from __future__ import annotations

from dataclasses import dataclass
import re
import time
from typing import Iterable

import numpy as np
from sklearn.neural_network import MLPRegressor

from .paired_linear_dataset import (
    PairedLinearExample,
    make_near_negative,
)


_TOKEN_RE = re.compile(
    r"<=|>=|!=|[A-Za-z_][A-Za-z0-9_]*|"
    r"\d+(?:\.\d+)?|[+\-*/=;:,().]"
)
_TOKEN_CATEGORIES = (
    "PAD",
    "NUM",
    "VAR0",
    "VAR1",
    "VARX",
    "ENTITY",
    "+",
    "-",
    "*",
    "/",
    "=",
    ";",
    "<=",
    ">=",
    "!=",
    "SOLVE",
    "EQUATION",
    "WORD",
    "PUNCT",
)


@dataclass(frozen=True)
class TokenEncodingObservation:
    token_count: int
    active_input_scalars: int


class FixedPositionTokenEncoder:
    """Sequence-sensitive token encoder with no learned state.

    Each token position receives a categorical one-hot feature. Numeric tokens
    additionally carry a scaled scalar value. Single-letter variables are
    canonicalized by first occurrence so variable spelling does not leak across
    train/final splits.

    This is intentionally much smaller and more auditable than a language-model
    tokenizer/embedding stack. It is still a hand-designed research encoder.
    """

    def __init__(
        self,
        *,
        max_tokens: int = 32,
        numeric_scale: float = 32.0,
    ):
        if max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if numeric_scale <= 0:
            raise ValueError("numeric_scale must be positive")
        self.max_tokens = int(max_tokens)
        self.numeric_scale = float(numeric_scale)
        self.category_to_index = {
            category: index
            for index, category in enumerate(_TOKEN_CATEGORIES)
        }

    @property
    def features_per_token(self) -> int:
        return len(_TOKEN_CATEGORIES) + 1

    @property
    def input_dimension(self) -> int:
        return self.max_tokens * self.features_per_token

    def _canonical_tokens(
        self,
        text: str,
    ) -> list[tuple[str, float]]:
        variables: dict[str, int] = {}
        out: list[tuple[str, float]] = []

        for token in _TOKEN_RE.findall(text):
            lower = token.lower()

            if re.fullmatch(r"\d+(?:\.\d+)?", token):
                out.append(("NUM", float(token)))
                continue

            if lower == "solve":
                out.append(("SOLVE", 0.0))
                continue
            if lower == "equation":
                out.append(("EQUATION", 0.0))
                continue

            if re.fullmatch(r"[A-Za-z]", token):
                if lower not in variables:
                    variables[lower] = len(variables)
                ordinal = variables[lower]
                if ordinal == 0:
                    category = "VAR0"
                elif ordinal == 1:
                    category = "VAR1"
                else:
                    category = "VARX"
                out.append((category, 0.0))
                continue

            if re.search(r"[A-Za-z]", token) and re.search(
                r"\d",
                token,
            ):
                out.append(("ENTITY", 0.0))
                continue

            if token in {
                "+",
                "-",
                "*",
                "/",
                "=",
                ";",
                "<=",
                ">=",
                "!=",
            }:
                out.append((token, 0.0))
                continue

            if re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*",
                token,
            ):
                out.append(("WORD", 0.0))
                continue

            out.append(("PUNCT", 0.0))

        return out

    def observe(self, text: str) -> TokenEncodingObservation:
        tokens = self._canonical_tokens(text)
        if len(tokens) > self.max_tokens:
            raise ValueError(
                f"token sequence length {len(tokens)} exceeds "
                f"max_tokens={self.max_tokens}"
            )
        active = self.max_tokens
        active += sum(
            1
            for category, value in tokens
            if category == "NUM" and value != 0.0
        )
        return TokenEncodingObservation(
            token_count=len(tokens),
            active_input_scalars=active,
        )

    def encode(self, text: str) -> np.ndarray:
        tokens = self._canonical_tokens(text)
        if len(tokens) > self.max_tokens:
            raise ValueError(
                f"token sequence length {len(tokens)} exceeds "
                f"max_tokens={self.max_tokens}"
            )

        matrix = np.zeros(
            (self.max_tokens, self.features_per_token),
            dtype=float,
        )
        for index, (category, numeric_value) in enumerate(tokens):
            matrix[index, self.category_to_index[category]] = 1.0
            if category == "NUM":
                matrix[index, -1] = (
                    numeric_value / self.numeric_scale
                )

        pad_index = self.category_to_index["PAD"]
        for index in range(len(tokens), self.max_tokens):
            matrix[index, pad_index] = 1.0

        return matrix.reshape(-1)

    def encode_many(self, texts: Iterable[str]) -> np.ndarray:
        return np.vstack([self.encode(text) for text in texts])


@dataclass(frozen=True)
class MatchedTokenModels:
    encoder: FixedPositionTokenEncoder
    structural_model: MLPRegressor
    direct_model: MLPRegressor
    structural_margin_threshold: float
    solution_scale: float
    hidden_units: int


@dataclass(frozen=True)
class MatchedMLPFootprint:
    structural_parameter_count: int
    direct_parameter_count: int
    structural_layer_shapes: tuple[tuple[int, int], ...]
    direct_layer_shapes: tuple[tuple[int, int], ...]
    structural_dense_weighted_sum_terms_proxy: int
    direct_dense_weighted_sum_terms_proxy: int


@dataclass(frozen=True)
class TokenInferenceObservation:
    output: tuple[float, float]
    active_input_scalars: int
    dense_weighted_sum_terms_proxy: int
    wall_seconds: float


def _new_model(
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


def fit_matched_token_models(
    training: tuple[PairedLinearExample, ...],
    validation: tuple[PairedLinearExample, ...],
    *,
    hidden_units: int = 8,
    validation_negative_margin: float = 0.10,
) -> MatchedTokenModels:
    """Fit matched-capacity direct and structural neural paths.

    Both models use the exact same encoder, one hidden layer width, two-output
    regression head, optimizer family, and inference architecture.

    Supervision is intentionally not identical:
    - direct model: positive linear systems -> exact (x0, x1) targets
    - structural model: same positives plus paired unsupported near-negatives ->
      LINEAR / ABSTAIN target scores

    Therefore this experiment matches inference capacity, not training-set
    cardinality.
    """
    if hidden_units < 1:
        raise ValueError("hidden_units must be >= 1")
    if validation_negative_margin <= 0:
        raise ValueError(
            "validation_negative_margin must be positive"
        )

    encoder = FixedPositionTokenEncoder()
    positive_texts = [example.text for example in training]
    negative_texts = [
        make_near_negative(example, index)
        for index, example in enumerate(training)
    ]

    positive_x = encoder.encode_many(positive_texts)
    negative_x = encoder.encode_many(negative_texts)

    structural_x = np.vstack([positive_x, negative_x])
    structural_y = np.vstack(
        [
            np.tile([1.0, 0.0], (len(training), 1)),
            np.tile([0.0, 1.0], (len(training), 1)),
        ]
    )

    structural_model = _new_model(
        hidden_units,
        random_state=29,
    )
    structural_model.fit(structural_x, structural_y)

    solution_scale = 4.0
    direct_y = np.asarray(
        [example.solution for example in training],
        dtype=float,
    ) / solution_scale
    direct_model = _new_model(
        hidden_units,
        random_state=29,
    )
    direct_model.fit(positive_x, direct_y)

    validation_positive = structural_model.predict(
        encoder.encode_many(
            example.text for example in validation
        )
    )
    validation_negative = structural_model.predict(
        encoder.encode_many(
            make_near_negative(example, index)
            for index, example in enumerate(validation)
        )
    )
    positive_margins = (
        validation_positive[:, 0] - validation_positive[:, 1]
    )
    negative_margins = (
        validation_negative[:, 0] - validation_negative[:, 1]
    )

    threshold = float(
        np.max(negative_margins) + validation_negative_margin
    )
    if not bool(np.all(positive_margins >= threshold)):
        raise RuntimeError(
            "validation cannot separate positive systems from paired "
            "near-negatives with the declared safety margin"
        )

    return MatchedTokenModels(
        encoder=encoder,
        structural_model=structural_model,
        direct_model=direct_model,
        structural_margin_threshold=threshold,
        solution_scale=solution_scale,
        hidden_units=hidden_units,
    )


def _parameter_count(model: MLPRegressor) -> int:
    return int(
        sum(matrix.size for matrix in model.coefs_)
        + sum(vector.size for vector in model.intercepts_)
    )


def _layer_shapes(
    model: MLPRegressor,
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (int(matrix.shape[0]), int(matrix.shape[1]))
        for matrix in model.coefs_
    )


def _dense_weighted_sum_terms(model: MLPRegressor) -> int:
    return int(sum(matrix.size for matrix in model.coefs_))


def inspect_matched_token_models(
    models: MatchedTokenModels,
) -> MatchedMLPFootprint:
    return MatchedMLPFootprint(
        structural_parameter_count=_parameter_count(
            models.structural_model
        ),
        direct_parameter_count=_parameter_count(
            models.direct_model
        ),
        structural_layer_shapes=_layer_shapes(
            models.structural_model
        ),
        direct_layer_shapes=_layer_shapes(
            models.direct_model
        ),
        structural_dense_weighted_sum_terms_proxy=(
            _dense_weighted_sum_terms(
                models.structural_model
            )
        ),
        direct_dense_weighted_sum_terms_proxy=(
            _dense_weighted_sum_terms(models.direct_model)
        ),
    )


def measure_token_model(
    model: MLPRegressor,
    encoder: FixedPositionTokenEncoder,
    text: str,
) -> TokenInferenceObservation:
    encoding = encoder.observe(text)
    encoded = encoder.encode(text).reshape(1, -1)
    start = time.perf_counter()
    raw = model.predict(encoded)[0]
    wall_seconds = time.perf_counter() - start
    return TokenInferenceObservation(
        output=(float(raw[0]), float(raw[1])),
        active_input_scalars=encoding.active_input_scalars,
        dense_weighted_sum_terms_proxy=(
            _dense_weighted_sum_terms(model)
        ),
        wall_seconds=wall_seconds,
    )


def structural_accepts_linear(
    models: MatchedTokenModels,
    observation: TokenInferenceObservation,
) -> bool:
    margin = observation.output[0] - observation.output[1]
    return margin >= models.structural_margin_threshold


def direct_solution(
    models: MatchedTokenModels,
    observation: TokenInferenceObservation,
) -> tuple[float, float]:
    return (
        observation.output[0] * models.solution_scale,
        observation.output[1] * models.solution_scale,
    )
