"""Exact information-loss certificate for this new proposer's observation map.

This is NOT a capability experiment, and says nothing about other NEUMANN
representations. It proves why more weights cannot fix this particular map.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from neumann1 import semantic_program_generator as gen, invention_core as ic


def certificate():
    examples, functions, encoded = [], [], []
    xs = [10 ** 16 + 17 * j for j in range(8)]
    for j in range(20):
        delta = ("mul", ("k", 8), ("mul", ("k", 4), ("k", 5)))
        for _ in range(j):
            delta = ("mul", ("k", 2), delta)
        ast = ("add", ("v", 0), delta)
        ex = [((x,), ic.run_program(ast, gen.LIB, (x,))) for x in xs]
        assert len(gen.tokenize(ast)) <= 48
        assert all(y == i[0] + 160 * 2 ** j for i, y in ex)
        examples.append(ex)
        encoded.append(gen.observations(ex))
        functions.append({"offset": 160 * 2 ** j, "ast": ast, "tokens": len(gen.tokenize(ast))})
    same = all(np.array_equal(encoded[0], x) for x in encoded)
    model = gen.SemanticProgramGenerator.load(ROOT / "docs/experiments/results/semantic_program_generator_20261112/model.npz")
    ctx = gen.context([], [("I", ("I",))])
    logits = [model.logits(np.concatenate((e, ctx))[None])[0] for e in encoded]
    return {"schema": "neumann.semantic-generator.lossy-observation-certificate.v1",
            "functions": functions, "all_functions_expressible_in_frozen_token_limit": True,
            "shared_exact_inputs": xs, "raw_observations_all_distinct": len({json.dumps(x) for x in examples}) == 20,
            "encoded_observations_byte_identical": same,
            "max_feature_difference": max(float(np.max(np.abs(encoded[0] - x))) for x in encoded),
            "frozen_model_initial_logits_byte_identical": all(np.array_equal(logits[0], x) for x in logits),
            "feature_sha256": hashlib.sha256(encoded[0].tobytes()).hexdigest(),
            "identification_information_lost_bits": math.log2(20),
            "balanced_one_proposal_success_upper_bound": 1 / 20,
            "theorem_scope": "Any proposer conditioned only on this encoded vector and program prefix has the same conditional distribution for all 20 tasks. The tasks have identical TRAIN inputs and pairwise different required outputs; a single program cannot satisfy two. Hence average one-proposal success is at most 1/20 under a uniform task choice independent of its random seed. Raw-TRAIN checking can still reject wrong proposals, so this is NOT a bound on exhaustive search or the full NEUMANN architecture.",
            "decision": "Delete this fixed lossy observation map as a sufficient invention representation; do not scale its model to repair information already discarded.",
            "original_24_failure_causation": "Not established by this constructed certificate. Curriculum mismatch, conditional modeling and syntax/semantic credit still need separate causal attribution."}


if __name__ == "__main__":
    result = certificate()
    out = ROOT / "docs/experiments/results/semantic_program_generator_20261112/capacity_certificate.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("functions", "shared_exact_inputs")}, indent=2))
