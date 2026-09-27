from __future__ import annotations

import json
import math

from neumann1.structural_compression import (
    APPARENT_DIMENSIONS,
    CORE_DIMENSIONS,
    EXAMPLES_PER_CELL,
    aggregate_observations,
    generate_benchmark_corpus,
    generate_cell,
    observe_example,
    scale_grid,
)


def run() -> dict[str, object]:
    corpus = generate_benchmark_corpus()
    observations = tuple(
        observe_example(example)
        for example in corpus
    )
    aggregate = aggregate_observations(observations)

    expected_count = (
        len(scale_grid()) * EXAMPLES_PER_CELL
    )
    cell_counts = {
        (int(cell["core_dimension"]), int(cell["apparent_dimension"])): (
            int(cell["count"])
        )
        for cell in aggregate["cells"]
    }

    deterministic_replay = True
    for k, n in scale_grid():
        example = generate_cell(k, n, count=1)[0]
        if observe_example(example) != observe_example(example):
            deterministic_replay = False
            break

    all_verified = all(
        observation.baseline_verified
        and observation.compressed_verified
        for observation in observations
    )
    all_equivalent = all(
        observation.full_solution_equivalent
        for observation in observations
    )
    all_certificates_valid = all(
        observation.certificate_valid
        for observation in observations
    )
    all_operation_counts_positive = all(
        observation.baseline_solver.arithmetic_ops > 0
        and observation.compressed_solver.arithmetic_ops > 0
        and observation.baseline_verification.arithmetic_ops > 0
        and observation.compressed_verification.arithmetic_ops > 0
        for observation in observations
    )
    verification_cost_parity = all(
        observation.baseline_verification
        == observation.compressed_verification
        for observation in observations
    )

    scale_cells_complete = (
        len(cell_counts) == len(scale_grid())
        and all(
            cell_counts.get((k, n)) == EXAMPLES_PER_CELL
            for k, n in scale_grid()
        )
    )

    finite_scaling = all(
        math.isfinite(
            float(metrics["baseline_solver_log_log_slope"])
        )
        and math.isfinite(
            float(metrics["compressed_solver_log_log_slope"])
        )
        for metrics in aggregate["scaling"].values()
    )

    keep = (
        len(corpus) == expected_count
        and scale_cells_complete
        and deterministic_replay
        and all_verified
        and all_equivalent
        and all_certificates_valid
        and all_operation_counts_positive
        and verification_cost_parity
        and finite_scaling
    )

    solver_reduction_cells = []
    for cell in aggregate["cells"]:
        solver_reduction_cells.append(
            {
                "core_dimension": cell["core_dimension"],
                "apparent_dimension": cell["apparent_dimension"],
                "mean_solver_work_ratio": (
                    cell["mean_solver_work_ratio"]
                ),
                "solver_work_reduction_observed": (
                    float(cell["mean_solver_work_ratio"]) > 1.0
                ),
            }
        )

    return {
        "experiment": (
            "v0.0.32 Structural Compression Contract "
            "+ Oracle Lower Bound"
        ),
        "pre_registered_grid": {
            "core_dimensions": list(CORE_DIMENSIONS),
            "apparent_dimensions": list(APPARENT_DIMENSIONS),
            "scale_cells": [
                {"core_dimension": k, "apparent_dimension": n}
                for k, n in scale_grid()
            ],
            "examples_per_cell": EXAMPLES_PER_CELL,
            "total_examples": len(corpus),
        },
        "contract_checks": {
            "all_full_and_compressed_paths_verified": all_verified,
            "full_solution_equivalence_rate": (
                sum(
                    1
                    for observation in observations
                    if observation.full_solution_equivalent
                )
                / len(observations)
            ),
            "compression_certificate_valid_rate": (
                sum(
                    1
                    for observation in observations
                    if observation.certificate_valid
                )
                / len(observations)
            ),
            "deterministic_operation_replay": deterministic_replay,
            "verification_cost_parity": verification_cost_parity,
            "scale_cells_complete": scale_cells_complete,
        },
        "cells": aggregate["cells"],
        "scaling": aggregate["scaling"],
        "descriptive_solver_reduction": solver_reduction_cells,
        "keep_oracle_structural_compression_contract": keep,
        "boundary": (
            "v0.0.32 uses generator-provided oracle dependency "
            "information that is unavailable to a real learned system. "
            "It can establish benchmark validity, an oracle compression "
            "opportunity, solver-work reduction potential, and a controlled "
            "scaling opportunity only. It does not establish that an AI "
            "can discover the compression or that end-to-end NEUMANN total "
            "compute is lower. Exact solver, reconstruction, and original-"
            "problem verification operation vectors remain separate. "
            "Representation and certificate bytes are reported without "
            "requiring them to shrink."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
