from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import scipy
import sklearn

from neumann1.learned_compression_dataset import (
    learned_compression_training_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer_once,
)


FORMAT_VERSION = "neumann1-v034-frozen-scorer-v1"


def _hex_array(array: np.ndarray) -> dict[str, object]:
    normalized = np.asarray(array, dtype=np.float64)
    return {
        "shape": list(normalized.shape),
        "values_hex": [
            float(value).hex()
            for value in normalized.ravel(order="C")
        ],
    }


def _training_signature() -> str:
    digest = hashlib.sha256()
    digest.update(b"NEUMANN-v033-training-corpus\0")
    for example in learned_compression_training_examples():
        digest.update(repr(example.signature).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def export(path: Path) -> dict[str, object]:
    frozen = fit_frozen_v033_scorer_once()
    scaler = frozen.proposer.pipeline.named_steps["scale"]
    mlp = frozen.proposer.pipeline.named_steps["mlp"]

    payload = {
        "format_version": FORMAT_VERSION,
        "selection_rule": (
            "first successful canonical export after the v0.0.34 "
            "reproducibility amendment; not selected by final metrics"
        ),
        "training_corpus_sha256": _training_signature(),
        "fitted_state_sha256": frozen.fitted_state_sha256,
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "scaler": {
            "mean": _hex_array(scaler.mean_),
            "scale": _hex_array(scaler.scale_),
            "var": _hex_array(scaler.var_),
            "n_features_in": int(scaler.n_features_in_),
            "n_samples_seen": int(scaler.n_samples_seen_),
        },
        "mlp": {
            "coefs": [
                _hex_array(array)
                for array in mlp.coefs_
            ],
            "intercepts": [
                _hex_array(array)
                for array in mlp.intercepts_
            ],
            "classes": [int(value) for value in mlp.classes_],
            "n_features_in": int(mlp.n_features_in_),
            "n_outputs": int(mlp.n_outputs_),
            "n_layers": int(mlp.n_layers_),
            "out_activation": str(mlp.out_activation_),
        },
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    output = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "artifacts/v034_frozen_scorer.json"
    )
    payload = export(output)
    print(
        json.dumps(
            {
                "path": str(output),
                "format_version": payload["format_version"],
                "training_corpus_sha256": (
                    payload["training_corpus_sha256"]
                ),
                "fitted_state_sha256": (
                    payload["fitted_state_sha256"]
                ),
                "selection_rule": payload["selection_rule"],
            },
            indent=2,
        )
    )
