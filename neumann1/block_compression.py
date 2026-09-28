from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json

from .block_compression_dataset import (
    CoupledBlockExample,
)
from .structural_compression import (
    ExactLinearSystem,
    GaussianOperationCounts,
    ReconstructionOperationCounts,
    VerificationOperationCounts,
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


@dataclass(frozen=True)
class BlockAffineCandidate:
    row_indices: tuple[int, int]
    targets: tuple[str, str]


@dataclass(frozen=True)
class BlockReconstructionRule:
    target: str
    constant: int
    coefficients: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ValidatedBlockCandidate:
    candidate: BlockAffineCandidate
    determinant: int
    rules: tuple[
        BlockReconstructionRule,
        BlockReconstructionRule,
    ]


@dataclass(frozen=True)
class BlockMaterializedReduction:
    accepted_blocks: tuple[BlockAffineCandidate, ...]
    reconstruction_rules: tuple[BlockReconstructionRule, ...]
    retained_system: ExactLinearSystem
    retained_answer: dict[str, Fraction]
    full_answer: dict[str, Fraction]
    solver_counts: GaussianOperationCounts
    reconstruction_counts: ReconstructionOperationCounts
    verification_counts: VerificationOperationCounts
    verified: bool
    ground_truth_equivalent: bool
    certificate_integer_scalars: int
    certificate_bytes: int


def _variable_index(
    system: ExactLinearSystem,
    name: str,
) -> int:
    try:
        return system.variables.index(name)
    except ValueError as exc:
        raise ValueError(
            f"unknown variable: {name}"
        ) from exc


def _derive_rules(
    system: ExactLinearSystem,
    candidate: BlockAffineCandidate,
) -> tuple[
    int,
    tuple[
        BlockReconstructionRule,
        BlockReconstructionRule,
    ],
]:
    rows = candidate.row_indices
    targets = candidate.targets

    if len(set(rows)) != 2:
        raise ValueError(
            "block rows must be distinct"
        )
    if len(set(targets)) != 2:
        raise ValueError(
            "block targets must be distinct"
        )
    if any(
        row_index < 0
        or row_index >= system.dimension
        for row_index in rows
    ):
        raise ValueError(
            "block row index out of range"
        )

    t0 = _variable_index(
        system,
        targets[0],
    )
    t1 = _variable_index(
        system,
        targets[1],
    )

    row0 = system.A[rows[0]]
    row1 = system.A[rows[1]]
    rhs0 = int(system.b[rows[0]])
    rhs1 = int(system.b[rows[1]])

    a = int(row0[t0])
    b = int(row0[t1])
    c = int(row1[t0])
    d = int(row1[t1])
    determinant = a * d - b * c

    if abs(determinant) != 1:
        raise ValueError(
            "target block is not unimodular"
        )

    constant0 = (
        d * rhs0 - b * rhs1
    ) // determinant
    constant1 = (
        -c * rhs0 + a * rhs1
    ) // determinant

    coefficients0: list[tuple[str, int]] = []
    coefficients1: list[tuple[str, int]] = []

    for column, variable in enumerate(
        system.variables
    ):
        if column in {t0, t1}:
            continue

        r0 = int(row0[column])
        r1 = int(row1[column])

        coefficient0 = -(
            d * r0 - b * r1
        ) // determinant
        coefficient1 = -(
            -c * r0 + a * r1
        ) // determinant

        if coefficient0:
            coefficients0.append(
                (
                    variable,
                    int(coefficient0),
                )
            )
        if coefficient1:
            coefficients1.append(
                (
                    variable,
                    int(coefficient1),
                )
            )

    rules = (
        BlockReconstructionRule(
            target=targets[0],
            constant=int(constant0),
            coefficients=tuple(coefficients0),
        ),
        BlockReconstructionRule(
            target=targets[1],
            constant=int(constant1),
            coefficients=tuple(coefficients1),
        ),
    )
    return determinant, rules


def _rule_map(
    rule: BlockReconstructionRule,
) -> dict[str, int]:
    return dict(rule.coefficients)


def _validate_derived_algebra(
    system: ExactLinearSystem,
    candidate: BlockAffineCandidate,
    rules: tuple[
        BlockReconstructionRule,
        BlockReconstructionRule,
    ],
) -> tuple[bool, str]:
    target_indices = [
        _variable_index(
            system,
            target,
        )
        for target in candidate.targets
    ]
    maps = [
        _rule_map(rule)
        for rule in rules
    ]

    for row_index in candidate.row_indices:
        row = system.A[row_index]
        rhs = int(system.b[row_index])

        constant = sum(
            int(row[target_index])
            * int(rule.constant)
            for target_index, rule in zip(
                target_indices,
                rules,
            )
        )
        if constant != rhs:
            return (
                False,
                "derived block constants do not reproduce rhs",
            )

        for column, variable in enumerate(
            system.variables
        ):
            if column in target_indices:
                continue

            coefficient = int(row[column])
            coefficient += sum(
                int(row[target_index])
                * maps[rule_index].get(
                    variable,
                    0,
                )
                for rule_index, target_index in enumerate(
                    target_indices
                )
            )
            if coefficient != 0:
                return (
                    False,
                    "derived block coefficients do not cancel",
                )

    return True, "block algebra verified"


def validate_block_candidate(
    system: ExactLinearSystem,
    candidate: BlockAffineCandidate,
) -> tuple[
    bool,
    str,
    ValidatedBlockCandidate | None,
]:
    try:
        determinant, rules = _derive_rules(
            system,
            candidate,
        )
    except ValueError as exc:
        return False, str(exc), None

    ok, message = _validate_derived_algebra(
        system,
        candidate,
        rules,
    )
    if not ok:
        return False, message, None

    return (
        True,
        "block candidate verified",
        ValidatedBlockCandidate(
            candidate=candidate,
            determinant=determinant,
            rules=rules,
        ),
    )


def _topological_rule_order(
    rules: tuple[BlockReconstructionRule, ...],
    retained_variables: tuple[str, ...],
) -> tuple[BlockReconstructionRule, ...] | None:
    available = set(retained_variables)
    pending = list(rules)
    ordered: list[BlockReconstructionRule] = []

    while pending:
        next_pending: list[
            BlockReconstructionRule
        ] = []
        progress = False

        for rule in pending:
            dependencies = {
                name
                for name, _ in rule.coefficients
            }
            if dependencies.issubset(available):
                ordered.append(rule)
                available.add(rule.target)
                progress = True
            else:
                next_pending.append(rule)

        if not progress:
            return None
        pending = next_pending

    return tuple(ordered)


def _reconstruct(
    retained_answer: dict[str, Fraction],
    rules: tuple[BlockReconstructionRule, ...],
) -> tuple[
    dict[str, Fraction],
    ReconstructionOperationCounts,
]:
    answer = dict(retained_answer)
    counts = ReconstructionOperationCounts()

    for rule in rules:
        total = Fraction(rule.constant)

        for index, (dependency, coefficient) in enumerate(
            rule.coefficients
        ):
            if dependency not in answer:
                raise ValueError(
                    f"missing reconstruction dependency: {dependency}"
                )
            product = (
                Fraction(coefficient)
                * answer[dependency]
            )
            counts.multiplications += 1

            if rule.constant != 0 or index > 0:
                total += product
                counts.additions += 1
            else:
                total = product

        answer[rule.target] = total

    return answer, counts


def _certificate_payload(
    validated: tuple[ValidatedBlockCandidate, ...],
) -> dict[str, object]:
    return {
        "blocks": [
            {
                "rows": list(
                    item.candidate.row_indices
                ),
                "targets": list(
                    item.candidate.targets
                ),
                "determinant": (
                    item.determinant
                ),
                "rules": [
                    {
                        "target": rule.target,
                        "constant": rule.constant,
                        "coefficients": [
                            [name, coefficient]
                            for name, coefficient
                            in rule.coefficients
                        ],
                    }
                    for rule in item.rules
                ],
            }
            for item in validated
        ]
    }


def _certificate_integer_scalars(
    validated: tuple[ValidatedBlockCandidate, ...],
) -> int:
    total = 0
    for item in validated:
        total += 2  # row indices
        total += 2  # target indices / identities
        total += 1  # determinant
        for rule in item.rules:
            total += 1  # constant
            total += 2 * len(
                rule.coefficients
            )
    return total


def materialize_block_reduction(
    example: CoupledBlockExample,
    candidates: tuple[BlockAffineCandidate, ...],
) -> BlockMaterializedReduction | None:
    system = example.full_system

    row_indices = [
        row_index
        for candidate in candidates
        for row_index in candidate.row_indices
    ]
    targets = [
        target
        for candidate in candidates
        for target in candidate.targets
    ]

    if len(row_indices) != len(set(row_indices)):
        return None
    if len(targets) != len(set(targets)):
        return None

    validated: list[ValidatedBlockCandidate] = []
    rules: list[BlockReconstructionRule] = []

    for candidate in candidates:
        ok, _, item = validate_block_candidate(
            system,
            candidate,
        )
        if not ok or item is None:
            return None
        validated.append(item)
        rules.extend(item.rules)

    eliminated = set(targets)
    removed_rows = set(row_indices)

    retained_variables = tuple(
        variable
        for variable in system.variables
        if variable not in eliminated
    )
    retained_rows = tuple(
        row_index
        for row_index in range(
            system.dimension
        )
        if row_index not in removed_rows
    )

    if len(retained_variables) != len(retained_rows):
        return None
    if not retained_variables:
        return None

    ordered_rules = _topological_rule_order(
        tuple(rules),
        retained_variables,
    )
    if ordered_rules is None:
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
        zip(
            system.variables,
            system.ground_truth,
        )
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
        retained_answer, solver_counts = (
            solve_exact_gauss_jordan(
                retained_system
            )
        )
    except ValueError:
        return None

    full_answer, reconstruction_counts = (
        _reconstruct(
            retained_answer,
            ordered_rules,
        )
    )
    verified, verification_counts = (
        verify_exact_full_system(
            system,
            full_answer,
        )
    )
    equivalent = (
        verified
        and all(
            full_answer[variable]
            == Fraction(expected)
            for variable, expected in zip(
                system.variables,
                system.ground_truth,
            )
        )
    )
    if not equivalent:
        return None

    payload = _certificate_payload(
        tuple(validated)
    )
    certificate_bytes = len(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )

    return BlockMaterializedReduction(
        accepted_blocks=tuple(candidates),
        reconstruction_rules=ordered_rules,
        retained_system=retained_system,
        retained_answer=retained_answer,
        full_answer=full_answer,
        solver_counts=solver_counts,
        reconstruction_counts=(
            reconstruction_counts
        ),
        verification_counts=(
            verification_counts
        ),
        verified=verified,
        ground_truth_equivalent=equivalent,
        certificate_integer_scalars=(
            _certificate_integer_scalars(
                tuple(validated)
            )
        ),
        certificate_bytes=certificate_bytes,
    )


def oracle_block_candidates(
    example: CoupledBlockExample,
) -> tuple[BlockAffineCandidate, ...]:
    return tuple(
        BlockAffineCandidate(
            row_indices=proposal.row_indices,
            targets=proposal.targets,
        )
        for proposal in example.oracle_blocks
    )
