from __future__ import annotations

import json

from neumann1.learned_compression import LearnedCompressionProposer
from neumann1.learned_compression_dataset import (
    learned_compression_training_examples,
)
from neumann1.stopping_gauntlet import learned_compressor_fingerprint


def run() -> dict[str, object]:
    proposer = LearnedCompressionProposer().fit(
        learned_compression_training_examples()
    )
    scaler = proposer.pipeline.named_steps["scale"]
    mlp = proposer.pipeline.named_steps["mlp"]

    return {
        "format": "neumann-v033-frozen-scorer-v1",
        "selection_rule": (
            "first successful canonicalization CI run after the "
            "v0.0.34 cross-run reproducibility amendment; "
            "not selected by final benchmark performance"
        ),
        "feature_dimension": int(mlp.n_features_in_),
        "hidden_units": int(mlp.hidden_layer_sizes[0]),
        "activation": "tanh",
        "output_activation": "logistic",
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coefs": [array.tolist() for array in mlp.coefs_],
        "intercepts": [array.tolist() for array in mlp.intercepts_],
        "fitted_state_sha256": learned_compressor_fingerprint(
            proposer
        ),
    }


if __name__ == "__main__":
    print("BEGIN_V033_CANONICAL_CHECKPOINT")
    print(json.dumps(run(), sort_keys=True))
    print("END_V033_CANONICAL_CHECKPOINT")
