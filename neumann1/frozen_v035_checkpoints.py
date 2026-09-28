from __future__ import annotations

import base64
import hashlib
import math

import numpy as np

from .learned_compression import (
    ScoredCandidate,
    candidate_features,
    enumerate_affine_candidates,
)
from .learned_compression_dataset import LearnedCompressionExample


V035_CHECKPOINT_FORMAT = "neumann1_v035_matched_checkpoint_bundle_v1"
V035_CANONICAL_EXPORT_RUN_ID = 36379107563
V035_CANONICAL_EXPORT_JOB_ID = 108790948414
V035_CANONICAL_EXPORT_COMMIT = "a21bfc0c6af50945ac309385109fef167b311c4f"

V035_REFERENCE_STATE_SHA256 = "598867fcc9981cb3c51c9ca6c8756f38d861cc00dae01d96b02649dc59a426a9"
V035_UTILITY_STATE_SHA256 = "ced59cd328a63cbeac9936cf44ce0f4e9f87a1d66d775652f6a4285cd5de4d49"

# Canonical checkpoints selected chronologically from the first successful
# training-only v0.0.35 exporter job. Calibration/final data were not read
# during checkpoint generation.
_REFERENCE_FLOAT64_B64 = (
    "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"
    "HBvA"
)

_UTILITY_FLOAT64_B64 = (
    "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"
    "Rec/"
)


def _decode_checkpoint(
    encoded: str,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    bytes,
]:
    raw = base64.b64decode(encoded)
    values = np.frombuffer(raw, dtype="<f8")
    if values.size != 321:
        raise AssertionError("v0.0.35 checkpoint length drift")

    index = 0
    scaler_mean = values[index:index + 16].copy()
    index += 16
    scaler_scale = values[index:index + 16].copy()
    index += 16
    hidden_weights = values[index:index + 256].reshape(16, 16).copy()
    index += 256
    hidden_bias = values[index:index + 16].copy()
    index += 16
    output_weights = values[index:index + 16].reshape(16, 1).copy()
    index += 16
    output_bias = values[index:index + 1].copy()
    index += 1

    if index != values.size:
        raise AssertionError("v0.0.35 checkpoint layout drift")

    return (
        scaler_mean,
        scaler_scale,
        hidden_weights,
        hidden_bias,
        output_weights,
        output_bias,
        raw,
    )


def _state_sha256(
    raw: bytes,
    *,
    model_kind: str,
) -> str:
    return hashlib.sha256(
        (
            f"NEUMANN-v035-{model_kind}-checkpoint\0"
        ).encode("ascii")
        + raw
    ).hexdigest()


class _FrozenMatchedBase:
    def __init__(
        self,
        encoded: str,
        *,
        expected_sha256: str,
        model_kind: str,
    ) -> None:
        (
            self.scaler_mean,
            self.scaler_scale,
            self.hidden_weights,
            self.hidden_bias,
            self.output_weights,
            self.output_bias,
            raw,
        ) = _decode_checkpoint(encoded)
        self.model_kind = model_kind
        self.state_sha256 = _state_sha256(
            raw,
            model_kind=model_kind,
        )
        if self.state_sha256 != expected_sha256:
            raise AssertionError(
                f"v0.0.35 {model_kind} checkpoint fingerprint mismatch"
            )

    def _logit(
        self,
        features: tuple[float, ...],
    ) -> float:
        if len(features) != 16:
            raise ValueError("v0.0.35 feature dimension drift")

        scaled = tuple(
            (
                features[index]
                - float(self.scaler_mean[index])
            )
            / float(self.scaler_scale[index])
            for index in range(16)
        )

        hidden = []
        for hidden_index in range(16):
            weighted = math.fsum(
                scaled[input_index]
                * float(
                    self.hidden_weights[
                        input_index,
                        hidden_index,
                    ]
                )
                for input_index in range(16)
            )
            weighted += float(self.hidden_bias[hidden_index])
            hidden.append(math.tanh(weighted))

        output = math.fsum(
            hidden[hidden_index]
            * float(self.output_weights[hidden_index, 0])
            for hidden_index in range(16)
        )
        output += float(self.output_bias[0])
        return output

    def score(
        self,
        example: LearnedCompressionExample,
    ) -> tuple[ScoredCandidate, ...]:
        candidates = enumerate_affine_candidates(
            example.full_system
        )
        scored = [
            ScoredCandidate(
                candidate=candidate,
                score=self._score_value(
                    candidate_features(
                        example.full_system,
                        candidate,
                    )
                ),
            )
            for candidate in candidates
        ]
        scored.sort(
            key=lambda item: (
                -item.score,
                item.candidate.row_index,
                int(item.candidate.target[1:]),
            )
        )
        return tuple(scored)

    def _score_value(
        self,
        features: tuple[float, ...],
    ) -> float:
        raise NotImplementedError


class FrozenV035ReferenceClassifier(_FrozenMatchedBase):
    def __init__(self) -> None:
        super().__init__(
            _REFERENCE_FLOAT64_B64,
            expected_sha256=V035_REFERENCE_STATE_SHA256,
            model_kind="matched-reference-classifier",
        )

    def _score_value(
        self,
        features: tuple[float, ...],
    ) -> float:
        logit = self._logit(features)
        if logit >= 0.0:
            z = math.exp(-logit)
            return 1.0 / (1.0 + z)
        z = math.exp(logit)
        return z / (1.0 + z)


class FrozenV035UtilityRegressor(_FrozenMatchedBase):
    def __init__(self) -> None:
        super().__init__(
            _UTILITY_FLOAT64_B64,
            expected_sha256=V035_UTILITY_STATE_SHA256,
            model_kind="matched-utility-regressor",
        )

    def _score_value(
        self,
        features: tuple[float, ...],
    ) -> float:
        raw = self._logit(features)
        return max(0.0, min(1.0, raw))


def checkpoint_fingerprints() -> dict[str, str]:
    reference = FrozenV035ReferenceClassifier()
    utility = FrozenV035UtilityRegressor()
    return {
        "reference": reference.state_sha256,
        "utility": utility.state_sha256,
    }
