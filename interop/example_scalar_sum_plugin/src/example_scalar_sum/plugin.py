from __future__ import annotations

from neumann1 import (
    CostLedger,
    FamilyAdapter,
    IRKind,
    Problem,
    Representation,
    VerificationResult,
)


KIND = "example.scalar_sum"
SOLVE_CALLS = 0


class ScalarSumCompiler:
    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        if not problem.raw_text.lower().startswith("sum:"):
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="external scalar-sum grammar not recognized",
            )

        body = problem.raw_text.split(":", 1)[1]
        try:
            values = [float(piece.strip()) for piece in body.split(",")]
        except ValueError:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="invalid scalar list",
            )

        if len(values) < 2:
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="at least two scalars required",
            )

        return Representation(
            kind=KIND,
            payload={"values": values},
            confidence=1.0,
            rationale="external scalar-sum compiler",
        )


class ScalarSumSolver:
    name = "external_scalar_sum"

    def supports(self, representation: Representation) -> bool:
        return representation.kind == KIND

    def solve(self, representation: Representation, ledger: CostLedger):
        global SOLVE_CALLS
        SOLVE_CALLS += 1
        values = list(map(float, representation.payload["values"]))
        ledger.solver_steps += len(values)
        return {"sum": sum(values)}


class ScalarSumVerifier:
    def verify(self, problem, representation, answer, ledger):
        values = list(map(float, representation.payload["values"]))
        ledger.verification_steps += len(values)
        expected = sum(values)
        ok = abs(float(answer["sum"]) - expected) < 1e-12
        return VerificationResult(
            ok=ok,
            reason="external scalar sum verified" if ok else "external scalar sum mismatch",
        )


def make_adapter() -> FamilyAdapter:
    return FamilyAdapter(
        family_id="example.scalar_sum",
        ir_kind=KIND,
        compiler=ScalarSumCompiler(),
        solver=ScalarSumSolver(),
        answer_verifier=ScalarSumVerifier(),
    )