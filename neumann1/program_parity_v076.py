"""Bounded direct atomic-program interpretation of the existing v031 gate.

No neural inference or training happens here. Head outputs are supplied by
the caller; all original deterministic execution components are reused.
"""

from dataclasses import dataclass
from enum import Enum

from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.solvers import LinearSystemSolver
from neumann1.types import CostLedger, IRKind, Problem
from neumann1.verifier import DeterministicVerifier


class Opcode(str, Enum):
    SOLVE_CONTROLLED_LINEAR = "solve_controlled_linear"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class Outcome:
    status: str
    answer: tuple[tuple[str, float], ...]
    representation_steps: int
    solver_steps: int
    verification_steps: int


def _head(class_id):
    if type(class_id) is not int or not 0 <= class_id < 82:
        raise ValueError("invalid v031 head output")
    return class_id


def decode_tool_program(class_id):
    return Opcode.SOLVE_CONTROLLED_LINEAR if _head(class_id) == 0 else Opcode.ABSTAIN


def _outcome(status, answer, ledger):
    return Outcome(status, tuple(sorted(answer.items())), ledger.representation_steps,
                   ledger.solver_steps, ledger.verification_steps)


def execute_tool_program(text, opcode):
    # Closed vocabulary only: never exec/eval model-produced source code.
    if not isinstance(opcode, Opcode):
        raise ValueError("untrusted opcode")
    ledger = CostLedger()
    if opcode == Opcode.ABSTAIN:
        return _outcome("ABSTAIN", {}, ledger)
    problem = Problem(text)
    representation = ControlledLinearSystemStructureFormer().form(problem, ledger)
    if representation.kind != IRKind.LINEAR_SYSTEM:
        return _outcome("COMPILER_REJECT", {}, ledger)
    answer = LinearSystemSolver().solve(representation, ledger)
    verification = DeterministicVerifier().verify(problem, representation, answer, ledger)
    return _outcome("VERIFIED" if verification.ok else "VERIFICATION_FAILED", answer, ledger)


def structural_route(text, class_id):
    # Exact downstream control flow from benchmark_v031; valid-head domain.
    ledger = CostLedger()
    if _head(class_id) != 0:
        return _outcome("ABSTAIN", {}, ledger)
    problem = Problem(text)
    representation = ControlledLinearSystemStructureFormer().form(problem, ledger)
    if representation.kind != IRKind.LINEAR_SYSTEM:
        return _outcome("COMPILER_REJECT", {}, ledger)
    answer = LinearSystemSolver().solve(representation, ledger)
    verification = DeterministicVerifier().verify(problem, representation, answer, ledger)
    return _outcome("VERIFIED" if verification.ok else "VERIFICATION_FAILED", answer, ledger)


def direct_tool_program_route(text, class_id):
    return execute_tool_program(text, decode_tool_program(class_id))
