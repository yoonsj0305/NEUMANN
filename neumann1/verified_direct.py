"""Numerical proposals with exact original-system authority and fallback."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from .structural_compression import (
    ExactLinearSystem,
    solve_exact_gauss_jordan,
    verify_exact_full_system,
)


@dataclass(frozen=True)
class VerifiedDirectResult:
    answer: dict[str, Fraction]
    used_exact_fallback: bool
    proposal_status: str


def solve_verified_numeric_or_exact(
    system: ExactLinearSystem,
) -> VerifiedDirectResult:
    """Return only exactly verified answers; numeric output is never trusted.

    No generator ground truth is read. The integer gate is only an accelerator:
    rational answers or failed/ambiguous proposals go through exact solving.
    """
    n = system.dimension
    if (n == 0 or len(system.A) != n or len(system.b) != n
            or any(len(row) != n for row in system.A)):
        raise ValueError("expected a nonempty square system")

    status = "numeric_exception"
    try:
        numeric = np.linalg.solve(
            np.asarray(system.A, dtype=np.float64),
            np.asarray(system.b, dtype=np.float64),
        )
        if (not np.isfinite(numeric).all()
                or np.any(np.abs(numeric) >= 2**53)):
            status = "nonfinite_or_out_of_range"
        else:
            rounded = np.rint(numeric)
            if np.any(np.abs(numeric - rounded) > 1e-6):
                status = "nonintegral_proposal"
            else:
                proposed = tuple(int(value) for value in rounded)
                # Use Python integers for every product and sum. Float residuals
                # are not a sufficient correctness certificate.
                if all(
                    sum(int(a) * x for a, x in zip(row, proposed)) == int(b)
                    for row, b in zip(system.A, system.b)
                ):
                    return VerifiedDirectResult(
                        answer={name: Fraction(x) for name, x in zip(
                            system.variables, proposed
                        )},
                        used_exact_fallback=False,
                        proposal_status="exact_integer_verified",
                    )
                status = "exact_equation_rejected"
    except (np.linalg.LinAlgError, ValueError, OverflowError):
        pass

    answer, _ = solve_exact_gauss_jordan(system)
    verified, _ = verify_exact_full_system(system, answer)
    if not verified:
        raise AssertionError("exact direct fallback failed verification")
    return VerifiedDirectResult(
        answer=answer,
        used_exact_fallback=True,
        proposal_status=status,
    )
