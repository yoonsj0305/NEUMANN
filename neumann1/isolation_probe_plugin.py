from __future__ import annotations

import os
import time

from .family_registry import FamilyAdapter
from .types import CostLedger, IRKind, Problem, Representation, VerificationResult


KIND = "test.isolation_probe"
POISONED = False


class ProbeCompiler:
    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        ledger.representation_steps += 1
        if not problem.raw_text.startswith("probe:"):
            return Representation(IRKind.UNKNOWN, {}, 0.0, "not probe")
        mode = problem.raw_text.split(":", 1)[1].strip()
        if mode == "hang_compile":
            time.sleep(5)
        if mode == "crash_compile":
            os._exit(17)
        return Representation(KIND, {"mode": mode}, 1.0, "isolation probe")


class ProbeSolver:
    name = "isolation_probe_solver"

    def supports(self, rep: Representation) -> bool:
        return rep.kind == KIND

    def solve(self, rep: Representation, ledger: CostLedger):
        global POISONED
        ledger.solver_steps += 1
        mode = str(rep.payload["mode"])
        if mode == "hang_solve":
            time.sleep(5)
        if mode == "crash_solve":
            os._exit(18)
        if mode == "mutate_env":
            os.environ["NEUMANN_CHILD_MUTATION"] = "child-only"
        if mode == "poison":
            POISONED = True
        return {
            "mode": mode,
            "pid": os.getpid(),
            "value": 42,
            "poisoned": POISONED,
        }


class ProbeVerifier:
    def verify(self, problem, rep, answer, ledger):
        ledger.verification_steps += 1
        mode = str(rep.payload["mode"])
        if mode == "hang_verify":
            time.sleep(5)
        if mode == "crash_verify":
            os._exit(19)
        ok = bool(answer and answer.get("value") == 42)
        return VerificationResult(ok, "probe verified" if ok else "probe mismatch")


def make_adapter() -> FamilyAdapter:
    return FamilyAdapter(
        family_id="test.isolation_probe",
        ir_kind=KIND,
        compiler=ProbeCompiler(),
        solver=ProbeSolver(),
        answer_verifier=ProbeVerifier(),
    )