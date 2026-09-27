from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from statistics import mean
from typing import Iterable

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .learned_compression_dataset import (
    AffineDependency,
    LearnedCompressionExample,
)
from .structural_compression import (
    ExactLinearSystem,
    GaussianOperationCounts,
    ReconstructionOperationCounts,
    VerificationOperationCounts,
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


FEATURE_DIMENSION = 16
HIDDEN_UNITS = 16
MODEL_RANDOM_STATE = 33


@dataclass(frozen=True)
class AffineCandidate:
    row_index: int
    target: str
    constant: int
    coefficients: tuple[tuple[str, int], ...]

    @property
    def key(self) -> tuple[int, str]:
        return (self.row_index, self.target)


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: AffineCandidate
    score: float


@dataclass(frozen=True)
class LearnedCompressorFootprint:
    input_feature_dimension: int
    hidden_units: int
    fitted_weight_bias_scalars: int
    scaler_state_scalars: int
    layer_shapes: tuple[tuple[int, int], ...]
    weighted_sum_terms_per_candidate: int


@dataclass(frozen=True)
class MaterializedReduction:
    accepted_candidates: tuple[AffineCandidate, ...]
    retained_system: ExactLinearSystem
    reconstruction_order: tuple[AffineCandidate, ...]
    retained_answer: dict[str, Fraction]
    full_answer: dict[str, Fraction]
    solver_counts: GaussianOperationCounts
    reconstruction_counts: ReconstructionOperationCounts
    verification_counts: VerificationOperationCounts
    verified: bool
    ground_truth_equivalent: bool


@dataclass(frozen=True)
class CheckerResult:
    proposed_candidates: tuple[ScoredCandidate, ...]
    accepted_candidates: tuple[AffineCandidate, ...]
    rejected_candidates: tuple[AffineCandidate, ...]
    materialized: MaterializedReduction


@dataclass(frozen=True)
class LearnedCompressionObservation:
    core_dimension: int
    apparent_dimension: int
    oracle_elimination_count: int
    proposal_budget: int
    candidates_scored: int
    exact_oracle_hits_in_proposals: int
    accepted_eliminations: int
    rejected_proposals: int
    accepted_exact_oracle_eliminations: int
    accepted_non_oracle_valid_eliminations: int
    elimination_count_recovery: float | None
    exact_oracle_rule_recovery: float | None
    baseline_solver_ops: int
    oracle_solver_ops: int
    learned_solver_ops: int
    oracle_solver_savings: int
    learned_solver_savings: int
    oracle_solver_savings_recovery: float | None
    learned_reconstruction_ops: int
    learned_verification_ops: int
    final_verified: bool
    ground_truth_equivalent: bool
    unsafe_accepted_reductions: int
    learned_weighted_sum_proxy: int


def enumerate_affine_candidates(
    system: ExactLinearSystem,
) -> tuple[AffineCandidate, ...]:
    candidates: list[AffineCandidate] = []

    for row_index, (row, rhs) in enumerate(
        zip(system.A, system.b)
    ):
        nonzero = [
            index
            for index, value in enumerate(row)
            if value != 0
        ]
        if len(nonzero) < 2:
            continue

        for target_index in nonzero:
            target_coefficient = int(row[target_index])
            if abs(target_coefficient) != 1:
                continue

            constant = int(rhs // target_coefficient)
            coefficients = []
            for column in nonzero:
                if column == target_index:
                    continue
                value = -int(row[column]) // target_coefficient
                coefficients.append(
                    (system.variables[column], value)
                )

            coefficients.sort(
                key=lambda item: int(item[0][1:])
            )
            candidates.append(
                AffineCandidate(
                    row_index=row_index,
                    target=system.variables[target_index],
                    constant=constant,
                    coefficients=tuple(coefficients),
                )
            )

    candidates.sort(
        key=lambda candidate: (
            candidate.row_index,
            int(candidate.target[1:]),
        )
    )
    return tuple(candidates)


def _oracle_candidate_keys(
    example: LearnedCompressionExample,
) -> frozenset[tuple[int, str]]:
    return frozenset(
        (rule.row_index, rule.target)
        for rule in example.oracle_dependencies
    )


def _column_statistics(
    system: ExactLinearSystem,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    counts: list[int] = []
    masses: list[int] = []

    for column in range(system.dimension):
        column_values = [
            int(row[column])
            for row in system.A
        ]
        counts.append(
            sum(1 for value in column_values if value != 0)
        )
        masses.append(
            sum(abs(value) for value in column_values)
        )

    return tuple(counts), tuple(masses)


def candidate_features(
    system: ExactLinearSystem,
    candidate: AffineCandidate,
) -> tuple[float, ...]:
    n = system.dimension
    row = system.A[candidate.row_index]
    rhs = int(system.b[candidate.row_index])
    target_index = system.variables.index(candidate.target)
    nonzero = [
        value
        for value in row
        if value != 0
    ]
    row_nnz = len(nonzero)
    row_abs_sum = sum(abs(int(value)) for value in nonzero)
    unit_fraction = (
        sum(1 for value in nonzero if abs(int(value)) == 1)
        / row_nnz
    )

    column_counts, column_masses = _column_statistics(system)
    target_count = column_counts[target_index]
    target_mass = column_masses[target_index]

    dependency_indices = [
        system.variables.index(name)
        for name, _ in candidate.coefficients
    ]
    dependency_counts = [
        column_counts[index]
        for index in dependency_indices
    ]
    dependency_masses = [
        column_masses[index]
        for index in dependency_indices
    ]
    dependency_coefficients = [
        abs(coefficient)
        for _, coefficient in candidate.coefficients
    ]

    dep_count_mean = mean(dependency_counts)
    dep_count_max = max(dependency_counts)
    dep_count_min = min(dependency_counts)
    dep_mass_mean = mean(dependency_masses)
    dep_coeff_mean = mean(dependency_coefficients)
    dep_coeff_max = max(dependency_coefficients)

    target_coefficient = int(row[target_index])

    features = (
        math.log2(float(n)) / 5.0,
        row_nnz / n,
        row_abs_sum / max(1.0, 8.0 * n),
        math.log1p(abs(rhs)) / 6.0,
        target_count / n,
        target_mass / max(1.0, 8.0 * n),
        float(target_coefficient),
        unit_fraction,
        len(candidate.coefficients) / n,
        dep_count_mean / n,
        dep_count_max / n,
        dep_count_min / n,
        (target_count - dep_count_mean) / n,
        dep_mass_mean / max(1.0, 8.0 * n),
        dep_coeff_mean / 2.0,
        dep_coeff_max / 2.0,
    )
    if len(features) != FEATURE_DIMENSION:
        raise AssertionError("feature contract dimension drift")
    return tuple(float(value) for value in features)


class LearnedCompressionProposer:
    def __init__(self) -> None:
        self.pipeline = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "mlp",
                    MLPClassifier(
                        hidden_layer_sizes=(HIDDEN_UNITS,),
                        activation="tanh",
                        solver="lbfgs",
                        alpha=1e-3,
                        max_iter=1200,
                        random_state=MODEL_RANDOM_STATE,
                    ),
                ),
            ]
        )

    def fit(
        self,
        examples: Iterable[LearnedCompressionExample],
    ) -> "LearnedCompressionProposer":
        X: list[tuple[float, ...]] = []
        y: list[int] = []

        for example in examples:
            oracle_keys = _oracle_candidate_keys(example)
            for candidate in enumerate_affine_candidates(
                example.full_system
            ):
                X.append(
                    candidate_features(
                        example.full_system,
                        candidate,
                    )
                )
                y.append(1 if candidate.key in oracle_keys else 0)

        if not X or len(set(y)) != 2:
            raise ValueError(
                "training corpus must contain positive and negative candidates"
            )

        # v0.0.34 reproducibility hardening:
        # sklearn's L-BFGS delegates dense linear algebra to BLAS.
        # Different runner thread scheduling produced different fitted
        # weights despite a fixed sklearn random_state. Restrict the
        # numerical backend to one thread so the frozen v0.0.33 scorer
        # is reproducible across CI runners.
        with threadpool_limits(limits=1):
            self.pipeline.fit(
                np.asarray(X, dtype=float),
                np.asarray(y, dtype=int),
            )
        return self

    def score(
        self,
        example: LearnedCompressionExample,
    ) -> tuple[ScoredCandidate, ...]:
        candidates = enumerate_affine_candidates(
            example.full_system
        )
        if not candidates:
            return ()

        X = np.asarray(
            [
                candidate_features(
                    example.full_system,
                    candidate,
                )
                for candidate in candidates
            ],
            dtype=float,
        )
        with threadpool_limits(limits=1):
            probabilities = self.pipeline.predict_proba(X)[:, 1]

        scored = [
            ScoredCandidate(
                candidate=candidate,
                score=float(score),
            )
            for candidate, score in zip(
                candidates,
                probabilities,
            )
        ]
        scored.sort(
            key=lambda item: (
                -item.score,
                item.candidate.row_index,
                int(item.candidate.target[1:]),
            )
        )
        return tuple(scored)


def inspect_learned_compressor(
    proposer: LearnedCompressionProposer,
) -> LearnedCompressorFootprint:
    scaler: StandardScaler = proposer.pipeline.named_steps["scale"]
    mlp: MLPClassifier = proposer.pipeline.named_steps["mlp"]

    layer_shapes = tuple(
        tuple(int(value) for value in weights.shape)
        for weights in mlp.coefs_
    )
    parameter_count = sum(
        int(weights.size)
        for weights in mlp.coefs_
    ) + sum(
        int(bias.size)
        for bias in mlp.intercepts_
    )
    scaler_state = int(scaler.mean_.size + scaler.scale_.size)
    weighted_sum_terms = sum(
        int(weights.size)
        for weights in mlp.coefs_
    )

    return LearnedCompressorFootprint(
        input_feature_dimension=int(mlp.n_features_in_),
        hidden_units=HIDDEN_UNITS,
        fitted_weight_bias_scalars=parameter_count,
        scaler_state_scalars=scaler_state,
        layer_shapes=layer_shapes,
        weighted_sum_terms_per_candidate=weighted_sum_terms,
    )


def validate_candidate_against_system(
    system: ExactLinearSystem,
    candidate: AffineCandidate,
) -> tuple[bool, str]:
    if candidate.row_index < 0 or candidate.row_index >= system.dimension:
        return False, "row index out of range"
    if candidate.target not in system.variables:
        return False, "unknown target"

    expected = {
        item.key: item
        for item in enumerate_affine_candidates(system)
    }.get(candidate.key)
    if expected is None:
        return False, "row-target pair is not an affine candidate"
    if expected != candidate:
        return False, "candidate algebra does not match original row"
    return True, "candidate algebra verified"


def _topological_reconstruction_order(
    candidates: tuple[AffineCandidate, ...],
    retained_variables: tuple[str, ...],
) -> tuple[AffineCandidate, ...] | None:
    available = set(retained_variables)
    pending = list(candidates)
    ordered: list[AffineCandidate] = []

    while pending:
        next_pending: list[AffineCandidate] = []
        progress = False

        for candidate in pending:
            dependencies = {
                name
                for name, _ in candidate.coefficients
            }
            if dependencies.issubset(available):
                ordered.append(candidate)
                available.add(candidate.target)
                progress = True
            else:
                next_pending.append(candidate)

        if not progress:
            return None
        pending = next_pending

    return tuple(ordered)


def _reconstruct_affine(
    retained_answer: dict[str, Fraction],
    ordered_candidates: tuple[AffineCandidate, ...],
) -> tuple[
    dict[str, Fraction],
    ReconstructionOperationCounts,
]:
    answer = dict(retained_answer)
    counts = ReconstructionOperationCounts()

    for candidate in ordered_candidates:
        total = Fraction(candidate.constant)
        for index, (dependency, coefficient) in enumerate(
            candidate.coefficients
        ):
            if dependency not in answer:
                raise ValueError(
                    f"missing reconstruction dependency {dependency}"
                )
            product = Fraction(coefficient) * answer[dependency]
            counts.multiplications += 1
            if candidate.constant != 0 or index > 0:
                total += product
                counts.additions += 1
            else:
                total = product
        answer[candidate.target] = total

    return answer, counts


def materialize_reduction(
    example: LearnedCompressionExample,
    candidates: tuple[AffineCandidate, ...],
) -> MaterializedReduction | None:
    system = example.full_system

    rows = [candidate.row_index for candidate in candidates]
    targets = [candidate.target for candidate in candidates]
    if len(rows) != len(set(rows)):
        return None
    if len(targets) != len(set(targets)):
        return None

    for candidate in candidates:
        ok, _ = validate_candidate_against_system(
            system,
            candidate,
        )
        if not ok:
            return None

    eliminated = set(targets)
    removed_rows = set(rows)
    retained_variables = tuple(
        variable
        for variable in system.variables
        if variable not in eliminated
    )
    retained_rows = tuple(
        row_index
        for row_index in range(system.dimension)
        if row_index not in removed_rows
    )

    if len(retained_variables) != len(retained_rows):
        return None
    if not retained_variables:
        return None

    reconstruction_order = _topological_reconstruction_order(
        candidates,
        retained_variables,
    )
    if reconstruction_order is None:
        return None

    retained_columns = [
        system.variables.index(variable)
        for variable in retained_variables
    ]
    retained_A = tuple(
        tuple(
            system.A[row_index][column]
            for column in retained_columns
        )
        for row_index in retained_rows
    )
    retained_b = tuple(
        system.b[row_index]
        for row_index in retained_rows
    )

    ground_truth_map = dict(
        zip(system.variables, system.ground_truth)
    )
    retained_ground_truth = tuple(
        ground_truth_map[variable]
        for variable in retained_variables
    )
    retained_system = ExactLinearSystem(
        variables=retained_variables,
        A=retained_A,
        b=retained_b,
        ground_truth=retained_ground_truth,
    )

    try:
        retained_answer, solver_counts = solve_exact_gauss_jordan(
            retained_system
        )
    except ValueError:
        return None

    full_answer, reconstruction_counts = _reconstruct_affine(
        retained_answer,
        reconstruction_order,
    )
    verified, verification_counts = verify_exact_full_system(
        system,
        full_answer,
    )
    ground_truth_equivalent = (
        verified
        and all(
            full_answer[variable] == Fraction(expected)
            for variable, expected in zip(
                system.variables,
                system.ground_truth,
            )
        )
    )
    if not ground_truth_equivalent:
        return None

    return MaterializedReduction(
        accepted_candidates=candidates,
        retained_system=retained_system,
        reconstruction_order=reconstruction_order,
        retained_answer=retained_answer,
        full_answer=full_answer,
        solver_counts=solver_counts,
        reconstruction_counts=reconstruction_counts,
        verification_counts=verification_counts,
        verified=verified,
        ground_truth_equivalent=ground_truth_equivalent,
    )


def _full_system_materialization(
    example: LearnedCompressionExample,
) -> MaterializedReduction:
    answer, solver_counts = solve_exact_gauss_jordan(
        example.full_system
    )
    verified, verification_counts = verify_exact_full_system(
        example.full_system,
        answer,
    )
    equivalent = (
        verified
        and all(
            answer[variable] == Fraction(expected)
            for variable, expected in zip(
                example.full_system.variables,
                example.full_system.ground_truth,
            )
        )
    )
    return MaterializedReduction(
        accepted_candidates=(),
        retained_system=example.full_system,
        reconstruction_order=(),
        retained_answer=answer,
        full_answer=answer,
        solver_counts=solver_counts,
        reconstruction_counts=ReconstructionOperationCounts(),
        verification_counts=verification_counts,
        verified=verified,
        ground_truth_equivalent=equivalent,
    )


def oracle_candidates(
    example: LearnedCompressionExample,
) -> tuple[AffineCandidate, ...]:
    return tuple(
        AffineCandidate(
            row_index=rule.row_index,
            target=rule.target,
            constant=rule.constant,
            coefficients=rule.coefficients,
        )
        for rule in example.oracle_dependencies
    )


def check_scored_proposals(
    example: LearnedCompressionExample,
    scored_candidates: tuple[ScoredCandidate, ...],
    *,
    proposal_budget: int,
) -> CheckerResult:
    if proposal_budget < 0:
        raise ValueError("proposal budget must be >= 0")

    proposals = scored_candidates[:proposal_budget]
    accepted: list[AffineCandidate] = []
    rejected: list[AffineCandidate] = []

    for scored in proposals:
        candidate = scored.candidate

        if any(
            candidate.row_index == item.row_index
            or candidate.target == item.target
            for item in accepted
        ):
            rejected.append(candidate)
            continue

        tentative = tuple(accepted + [candidate])
        materialized = materialize_reduction(
            example,
            tentative,
        )
        if materialized is None:
            rejected.append(candidate)
            continue

        accepted.append(candidate)

    final_materialized = (
        materialize_reduction(
            example,
            tuple(accepted),
        )
        if accepted
        else _full_system_materialization(example)
    )
    if final_materialized is None:
        raise AssertionError(
            "checker accepted a set that cannot be materialized"
        )

    return CheckerResult(
        proposed_candidates=proposals,
        accepted_candidates=tuple(accepted),
        rejected_candidates=tuple(rejected),
        materialized=final_materialized,
    )


def observe_learned_compression(
    example: LearnedCompressionExample,
    proposer: LearnedCompressionProposer,
    footprint: LearnedCompressorFootprint,
) -> LearnedCompressionObservation:
    baseline = _full_system_materialization(example)

    oracle = materialize_reduction(
        example,
        oracle_candidates(example),
    )
    if oracle is None:
        raise AssertionError("oracle reduction failed materialization")

    scored = proposer.score(example)
    budget = example.oracle_elimination_count
    checked = check_scored_proposals(
        example,
        scored,
        proposal_budget=budget,
    )

    oracle_keys = _oracle_candidate_keys(example)
    proposal_hits = sum(
        1
        for item in checked.proposed_candidates
        if item.candidate.key in oracle_keys
    )
    accepted_oracle = sum(
        1
        for candidate in checked.accepted_candidates
        if candidate.key in oracle_keys
    )
    accepted_total = len(checked.accepted_candidates)
    accepted_non_oracle = accepted_total - accepted_oracle

    if budget > 0:
        elimination_recovery: float | None = (
            accepted_total / budget
        )
        exact_recovery: float | None = (
            accepted_oracle / budget
        )
    else:
        elimination_recovery = None
        exact_recovery = None

    baseline_ops = baseline.solver_counts.arithmetic_ops
    oracle_ops = oracle.solver_counts.arithmetic_ops
    learned_ops = checked.materialized.solver_counts.arithmetic_ops
    oracle_savings = baseline_ops - oracle_ops
    learned_savings = baseline_ops - learned_ops

    if oracle_savings > 0:
        solver_savings_recovery: float | None = (
            learned_savings / oracle_savings
        )
    else:
        solver_savings_recovery = None

    final_verified = (
        checked.materialized.verified
        and checked.materialized.ground_truth_equivalent
    )

    return LearnedCompressionObservation(
        core_dimension=example.core_dimension,
        apparent_dimension=example.apparent_dimension,
        oracle_elimination_count=budget,
        proposal_budget=budget,
        candidates_scored=len(scored),
        exact_oracle_hits_in_proposals=proposal_hits,
        accepted_eliminations=accepted_total,
        rejected_proposals=len(checked.rejected_candidates),
        accepted_exact_oracle_eliminations=accepted_oracle,
        accepted_non_oracle_valid_eliminations=accepted_non_oracle,
        elimination_count_recovery=elimination_recovery,
        exact_oracle_rule_recovery=exact_recovery,
        baseline_solver_ops=baseline_ops,
        oracle_solver_ops=oracle_ops,
        learned_solver_ops=learned_ops,
        oracle_solver_savings=oracle_savings,
        learned_solver_savings=learned_savings,
        oracle_solver_savings_recovery=solver_savings_recovery,
        learned_reconstruction_ops=(
            checked.materialized.reconstruction_counts.arithmetic_ops
        ),
        learned_verification_ops=(
            checked.materialized.verification_counts.arithmetic_ops
        ),
        final_verified=final_verified,
        ground_truth_equivalent=(
            checked.materialized.ground_truth_equivalent
        ),
        unsafe_accepted_reductions=(
            0 if final_verified else accepted_total
        ),
        learned_weighted_sum_proxy=(
            len(scored)
            * footprint.weighted_sum_terms_per_candidate
        ),
    )


def aggregate_learned_observations(
    observations: Iterable[LearnedCompressionObservation],
) -> dict[str, object]:
    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one observation is required")

    compression_rows = tuple(
        row
        for row in rows
        if row.oracle_elimination_count > 0
    )

    grouped: dict[
        tuple[int, int],
        list[LearnedCompressionObservation],
    ] = {}
    for row in rows:
        grouped.setdefault(
            (row.core_dimension, row.apparent_dimension),
            [],
        ).append(row)

    cells: list[dict[str, object]] = []
    for key in sorted(grouped):
        cell_rows = grouped[key]
        active = [
            row
            for row in cell_rows
            if row.oracle_elimination_count > 0
        ]

        cell: dict[str, object] = {
            "core_dimension": key[0],
            "apparent_dimension": key[1],
            "count": len(cell_rows),
            "verified_retention": mean(
                1.0 if row.final_verified else 0.0
                for row in cell_rows
            ),
            "unsafe_accepted_reductions": sum(
                row.unsafe_accepted_reductions
                for row in cell_rows
            ),
            "mean_candidates_scored": mean(
                row.candidates_scored
                for row in cell_rows
            ),
            "mean_accepted_eliminations": mean(
                row.accepted_eliminations
                for row in cell_rows
            ),
            "mean_rejected_proposals": mean(
                row.rejected_proposals
                for row in cell_rows
            ),
            "mean_learned_solver_ops": mean(
                row.learned_solver_ops
                for row in cell_rows
            ),
            "mean_learned_weighted_sum_proxy": mean(
                row.learned_weighted_sum_proxy
                for row in cell_rows
            ),
        }

        if active:
            cell.update(
                {
                    "mean_elimination_count_recovery": mean(
                        float(row.elimination_count_recovery)
                        for row in active
                        if row.elimination_count_recovery is not None
                    ),
                    "mean_exact_oracle_rule_recovery": mean(
                        float(row.exact_oracle_rule_recovery)
                        for row in active
                        if row.exact_oracle_rule_recovery is not None
                    ),
                    "mean_oracle_solver_savings_recovery": mean(
                        float(row.oracle_solver_savings_recovery)
                        for row in active
                        if row.oracle_solver_savings_recovery is not None
                    ),
                    "mean_baseline_solver_ops": mean(
                        row.baseline_solver_ops
                        for row in active
                    ),
                    "mean_oracle_solver_ops": mean(
                        row.oracle_solver_ops
                        for row in active
                    ),
                    "mean_oracle_exact_hits_in_proposals": mean(
                        row.exact_oracle_hits_in_proposals
                        for row in active
                    ),
                    "mean_accepted_non_oracle_valid_eliminations": mean(
                        row.accepted_non_oracle_valid_eliminations
                        for row in active
                    ),
                }
            )
        else:
            cell.update(
                {
                    "mean_elimination_count_recovery": None,
                    "mean_exact_oracle_rule_recovery": None,
                    "mean_oracle_solver_savings_recovery": None,
                }
            )

        cells.append(cell)

    return {
        "count": len(rows),
        "compression_opportunity_count": len(compression_rows),
        "verified_retention": mean(
            1.0 if row.final_verified else 0.0
            for row in rows
        ),
        "unsafe_accepted_reduction_count": sum(
            row.unsafe_accepted_reductions
            for row in rows
        ),
        "examples_with_any_accepted_compression": sum(
            1
            for row in compression_rows
            if row.accepted_eliminations > 0
        ),
        "mean_elimination_count_recovery": mean(
            float(row.elimination_count_recovery)
            for row in compression_rows
            if row.elimination_count_recovery is not None
        ),
        "mean_exact_oracle_rule_recovery": mean(
            float(row.exact_oracle_rule_recovery)
            for row in compression_rows
            if row.exact_oracle_rule_recovery is not None
        ),
        "mean_oracle_solver_savings_recovery": mean(
            float(row.oracle_solver_savings_recovery)
            for row in compression_rows
            if row.oracle_solver_savings_recovery is not None
        ),
        "total_fail_closed_rejections": sum(
            row.rejected_proposals
            for row in rows
        ),
        "cells": cells,
    }
