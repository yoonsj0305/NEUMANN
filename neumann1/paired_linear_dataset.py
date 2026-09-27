from __future__ import annotations

from dataclasses import dataclass
import random


_COEFFICIENTS = (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)
_SOLUTIONS = tuple(range(-4, 5))
_VARIABLE_PAIRS = (
    ("x", "y"),
    ("a", "b"),
    ("p", "q"),
    ("u", "v"),
    ("m", "n"),
    ("r", "s"),
    ("c", "d"),
    ("h", "k"),
    ("z", "t"),
)
_PREFIXES = ("", "Solve: ", "Equation: ")


@dataclass(frozen=True)
class PairedLinearExample:
    text: str
    solution: tuple[float, float]
    variables: tuple[str, str]


def _term(coefficient: int, variable: str, *, first: bool) -> str:
    if coefficient == 0:
        return ""
    magnitude = abs(coefficient)
    body = variable if magnitude == 1 else f"{magnitude}*{variable}"
    if first:
        return body if coefficient > 0 else f"-{body}"
    sign = "+" if coefficient > 0 else "-"
    return f" {sign} {body}"


def _expression(
    c1: int,
    v1: str,
    c2: int,
    v2: str,
) -> str:
    return _term(c1, v1, first=True) + _term(
        c2,
        v2,
        first=False,
    )


def generate_paired_linear_examples(
    count: int,
    *,
    seed: int,
) -> tuple[PairedLinearExample, ...]:
    """Generate deterministic nonsingular 2x2 integer systems.

    The hidden solution is sampled first. Right-hand sides are then generated
    exactly from an invertible integer coefficient matrix. This gives the direct
    learned baseline exact supervised targets without using the production
    compiler or solver to create labels.
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    rng = random.Random(seed)
    seen: set[str] = set()
    out: list[PairedLinearExample] = []

    for _ in range(200_000):
        if len(out) >= count:
            break

        a, b, c, d = (
            rng.choice(_COEFFICIENTS)
            for _ in range(4)
        )
        if a * d - b * c == 0:
            continue

        x = rng.choice(_SOLUTIONS)
        y = rng.choice(_SOLUTIONS)
        rhs1 = a * x + b * y
        rhs2 = c * x + d * y
        if abs(rhs1) > 30 or abs(rhs2) > 30:
            continue

        v1, v2 = rng.choice(_VARIABLE_PAIRS)
        prefix = rng.choice(_PREFIXES)
        text = (
            f"{prefix}{_expression(a, v1, b, v2)} = {rhs1}; "
            f"{_expression(c, v1, d, v2)} = {rhs2}"
        )
        if text in seen:
            continue
        seen.add(text)
        out.append(
            PairedLinearExample(
                text=text,
                solution=(float(x), float(y)),
                variables=(v1, v2),
            )
        )

    if len(out) != count:
        raise RuntimeError(
            f"could not generate {count} unique examples"
        )
    return tuple(out)


def make_near_negative(
    example: PairedLinearExample,
    index: int,
) -> str:
    """Create a deterministic unsupported near-neighbor.

    The three transformations exercise distinct fail-closed compiler paths:
    inequality, nonlinear variable multiplication, and an underspecified
    one-equation system.
    """
    mode = index % 3
    if mode == 0:
        return example.text.replace(" = ", " <= ", 1)
    if mode == 1:
        left, rest = example.text.split(" = ", 1)
        v1, v2 = example.variables
        return f"{left} + {v1}*{v2} = {rest}"
    return example.text.split(";", 1)[0]


def paired_linear_training_examples() -> tuple[PairedLinearExample, ...]:
    return generate_paired_linear_examples(128, seed=2901)


def paired_linear_validation_examples() -> tuple[PairedLinearExample, ...]:
    return generate_paired_linear_examples(32, seed=2902)


def paired_linear_final_examples() -> tuple[PairedLinearExample, ...]:
    return generate_paired_linear_examples(64, seed=2903)



def generate_solution_covered_linear_examples(
    count: int,
    *,
    seed: int,
) -> tuple[PairedLinearExample, ...]:
    """Generate a deterministic pool that covers all 81 integer solution pairs.

    For count >= 81, the first 81 examples contain every ordered solution pair
    in [-4, 4] x [-4, 4] exactly once in a seed-shuffled order. Larger prefixes
    continue cycling through reshuffled solution pairs. This prevents the
    discrete Direct challenger from being handicapped by missing output classes
    at the smallest v0.0.30 training size.
    """
    all_solutions = [
        (x, y)
        for x in _SOLUTIONS
        for y in _SOLUTIONS
    ]
    if count < len(all_solutions):
        raise ValueError(
            "solution-covered corpus requires count >= 81"
        )

    rng = random.Random(seed)
    schedule: list[tuple[int, int]] = []
    while len(schedule) < count:
        cycle = list(all_solutions)
        rng.shuffle(cycle)
        schedule.extend(cycle)
    schedule = schedule[:count]

    seen: set[str] = set()
    out: list[PairedLinearExample] = []

    for x, y in schedule:
        for _ in range(20_000):
            a, b, c, d = (
                rng.choice(_COEFFICIENTS)
                for _ in range(4)
            )
            if a * d - b * c == 0:
                continue

            rhs1 = a * x + b * y
            rhs2 = c * x + d * y
            if abs(rhs1) > 30 or abs(rhs2) > 30:
                continue

            v1, v2 = rng.choice(_VARIABLE_PAIRS)
            prefix = rng.choice(_PREFIXES)
            text = (
                f"{prefix}{_expression(a, v1, b, v2)} = {rhs1}; "
                f"{_expression(c, v1, d, v2)} = {rhs2}"
            )
            if text in seen:
                continue

            seen.add(text)
            out.append(
                PairedLinearExample(
                    text=text,
                    solution=(float(x), float(y)),
                    variables=(v1, v2),
                )
            )
            break
        else:
            raise RuntimeError(
                "could not generate a unique example for scheduled solution"
            )

    return tuple(out)


def direct_frontier_training_pool() -> tuple[PairedLinearExample, ...]:
    return generate_solution_covered_linear_examples(
        2048,
        seed=3001,
    )


def direct_frontier_validation_examples() -> tuple[PairedLinearExample, ...]:
    return generate_solution_covered_linear_examples(
        243,
        seed=3002,
    )


def direct_frontier_final_examples() -> tuple[PairedLinearExample, ...]:
    return generate_solution_covered_linear_examples(
        243,
        seed=3003,
    )



def sequence_challenger_training_pool() -> tuple[PairedLinearExample, ...]:
    """v0.0.31 positive pool for the sequence-model challenger."""
    return generate_solution_covered_linear_examples(
        8192,
        seed=3101,
    )


def sequence_challenger_validation_examples() -> tuple[PairedLinearExample, ...]:
    return generate_solution_covered_linear_examples(
        243,
        seed=3102,
    )


def sequence_challenger_final_examples() -> tuple[PairedLinearExample, ...]:
    return generate_solution_covered_linear_examples(
        243,
        seed=3103,
    )
