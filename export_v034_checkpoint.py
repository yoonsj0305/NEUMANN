from __future__ import annotations

import hashlib
import json

from neumann1.learned_compression import LearnedCompressionProposer
from neumann1.learned_compression_dataset import (
    learned_compression_training_examples,
)


def _state() -> dict[str, object]:
    proposer = LearnedCompressionProposer().fit(
        learned_compression_training_examples()
    )
    scaler = proposer.pipeline.named_steps["scale"]
    mlp = proposer.pipeline.named_steps["mlp"]

    state = {
        "format": "neumann-v034-frozen-v033-mlp-v1",
        "feature_dimension": 16,
        "hidden_units": 16,
        "activation": "tanh",
        "output": "binary-logistic",
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coefs": [
            weights.tolist()
            for weights in mlp.coefs_
        ],
        "intercepts": [
            bias.tolist()
            for bias in mlp.intercepts_
        ],
    }

    canonical = json.dumps(
        state,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    state["checkpoint_json_sha256"] = hashlib.sha256(
        canonical
    ).hexdigest()
    return state


if __name__ == "__main__":
    print("V034_CHECKPOINT_BEGIN")
    print(
        json.dumps(
            _state(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    print("V034_CHECKPOINT_END")
