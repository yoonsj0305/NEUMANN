from __future__ import annotations

from dataclasses import replace
import math

from neumann1.structural_compression import (
    EXAMPLES_PER_CELL,
    CompressionCertificate,
    ReconstructionRule,
    aggregate_observations,
    check_compression_certificate,
    generate_benchmark_corpus,
    generate_cell,
    observe_example,
    scale_grid,
)


def test_v032_pre_registered_grid_and_corpus_size():
    assert scale_grid() == (
        (2, 4),
        (2, 8),
        (2, 16),
        (2, 32),
        (4, 4),
        (4, 8),
        (4, 16),
        (4, 32),
    )

    corpus = generate_benchmark_corpus()
    assert len(corpus) == len(scale_grid()) * EXAMPLES_PER_CELL


def test_v032_generator_is_deterministic_and_dimensions_are_exact():
    first = generate_cell(2, 8, count=3)
    second = generate_cell(2, 8, count=3)

    assert first == second
    assert len(first) == 3

    for example in first:
        assert example.core_dimension == 2
        assert example.apparent_dimension == 8
        assert example.core_system.dimension == 2
        assert example.full_system.dimension == 8
        assert len(example.certificate.eliminated_variables) == 6
        assert len(example.certificate.reconstruction_rules) == 6


def test_v032_certificate_checker_accepts_valid_and_rejects_tamper():
    example = generate_cell(2, 8, count=1)[0]
    ok, reason = check_compression_certificate(example)

    assert ok, reason

    first_rule = example.certificate.reconstruction_rules[0]
    dependency, coefficient = first_rule.coefficients[0]
    tampered_rule = replace(
        first_rule,
        coefficients=(
            (dependency, coefficient + 1),
            *first_rule.coefficients[1:],
        ),
    )
    tampered_certificate = replace(
        example.certificate,
        reconstruction_rules=(
            tampered_rule,
            *example.certificate.reconstruction_rules[1:],
        ),
    )
    tampered_example = replace(
        example,
        certificate=tampered_certificate,
    )

    ok, _ = check_compression_certificate(tampered_example)
    assert not ok


def test_v032_oracle_path_reconstructs_and_verifies_original_problem():
    for k, n in scale_grid():
        example = generate_cell(k, n, count=1)[0]
        observation = observe_example(example)

        assert observation.certificate_valid
        assert observation.baseline_verified
        assert observation.compressed_verified
        assert observation.full_solution_equivalent
        assert (
            observation.baseline_verification
            == observation.compressed_verification
        )


def test_v032_operation_counters_are_deterministic():
    example = generate_cell(4, 16, count=1)[0]

    first = observe_example(example)
    second = observe_example(example)

    assert first == second
    assert first.baseline_solver.arithmetic_ops > 0
    assert first.compressed_solver.arithmetic_ops > 0
    assert first.baseline_verification.arithmetic_ops > 0
    assert first.reconstruction.arithmetic_ops >= 0


def test_v032_aggregate_reports_every_cell_without_outcome_gate():
    observations = [
        observe_example(generate_cell(k, n, count=1)[0])
        for k, n in scale_grid()
    ]
    aggregate = aggregate_observations(observations)

    assert len(aggregate["cells"]) == len(scale_grid())
    assert set(aggregate["scaling"]) == {"2", "4"}

    for metrics in aggregate["scaling"].values():
        assert math.isfinite(
            metrics["baseline_solver_log_log_slope"]
        )
        assert math.isfinite(
            metrics["compressed_solver_log_log_slope"]
        )

    for cell in aggregate["cells"]:
        assert cell["verified_equivalence_rate"] == 1.0
        assert cell["certificate_valid_rate"] == 1.0
        assert cell["mean_raw_representation_bytes"] > 0
        assert cell["mean_compressed_representation_bytes"] > 0
        assert cell["mean_certificate_bytes"] > 0
