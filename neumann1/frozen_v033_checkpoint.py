from __future__ import annotations

import base64
import hashlib
import math

import numpy as np

from .learned_compression import (
    AffineCandidate,
    ScoredCandidate,
    candidate_features,
    enumerate_affine_candidates,
)
from .learned_compression_dataset import LearnedCompressionExample


FROZEN_V033_CHECKPOINT_FORMAT = "neumann1_frozen_v033_checkpoint_v1"
FROZEN_V033_STATE_SHA256 = "f9c1dccd0bda28619cb74c6fd6e8a457cde96944cbe5bfa65c9665859da3cc69"

# Canonical checkpoint selected by procedure, not by v0.0.34 final performance:
# this is the exact fitted state observed in the first reproducibility-hardened
# v0.0.34 CI run and independently regenerated from the frozen v0.0.33
# architecture/features/training corpus in the canonical Python environment.
#
# Layout, little-endian float64:
#   scaler_mean[16]
#   scaler_scale[16]
#   hidden_weights[16,16]
#   hidden_bias[16]
#   output_weights[16,1]
#   output_bias[1]
_FROZEN_V033_FLOAT64_B64 = (
    "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"
    "h4w1xu+5279gvKElMq0fwMWCU91mVRnA"
)


def _checkpoint_arrays() -> tuple[np.ndarray, ...]:
    raw = base64.b64decode(_FROZEN_V033_FLOAT64_B64)
    values = np.frombuffer(raw, dtype="<f8")
    if values.size != 321:
        raise AssertionError("frozen v0.0.33 checkpoint length drift")

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
        raise AssertionError("frozen v0.0.33 checkpoint layout drift")
    return (
        scaler_mean,
        scaler_scale,
        hidden_weights,
        hidden_bias,
        output_weights,
        output_bias,
    )


def checkpoint_state_sha256() -> str:
    (
        scaler_mean,
        scaler_scale,
        hidden_weights,
        hidden_bias,
        output_weights,
        output_bias,
    ) = _checkpoint_arrays()

    digest = hashlib.sha256()
    digest.update(b"NEUMANN-v034-frozen-v033-scorer\0")
    for array in (
        scaler_mean,
        scaler_scale,
        hidden_weights,
        output_weights,
        hidden_bias,
        output_bias,
    ):
        normalized = array.astype("<f8", copy=False)
        digest.update(repr(tuple(normalized.shape)).encode("ascii"))
        digest.update(b"\0")
        digest.update(normalized.tobytes(order="C"))
        digest.update(b"\0")
    return digest.hexdigest()


class FrozenV033CheckpointProposer:
    def __init__(self) -> None:
        (
            self.scaler_mean,
            self.scaler_scale,
            self.hidden_weights,
            self.hidden_bias,
            self.output_weights,
            self.output_bias,
        ) = _checkpoint_arrays()

        if checkpoint_state_sha256() != FROZEN_V033_STATE_SHA256:
            raise AssertionError("frozen v0.0.33 checkpoint fingerprint mismatch")

    def _probability(self, features: tuple[float, ...]) -> float:
        scaled = tuple(
            (features[index] - float(self.scaler_mean[index]))
            / float(self.scaler_scale[index])
            for index in range(16)
        )

        hidden = []
        for hidden_index in range(16):
            weighted = math.fsum(
                scaled[input_index]
                * float(self.hidden_weights[input_index, hidden_index])
                for input_index in range(16)
            )
            weighted += float(self.hidden_bias[hidden_index])
            hidden.append(math.tanh(weighted))

        logit = math.fsum(
            hidden[hidden_index]
            * float(self.output_weights[hidden_index, 0])
            for hidden_index in range(16)
        )
        logit += float(self.output_bias[0])

        if logit >= 0.0:
            z = math.exp(-logit)
            return 1.0 / (1.0 + z)
        z = math.exp(logit)
        return z / (1.0 + z)

    def score(
        self,
        example: LearnedCompressionExample,
    ) -> tuple[ScoredCandidate, ...]:
        candidates = enumerate_affine_candidates(example.full_system)
        scored = [
            ScoredCandidate(
                candidate=candidate,
                score=self._probability(
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
