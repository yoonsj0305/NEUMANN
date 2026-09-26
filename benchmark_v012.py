from __future__ import annotations
import json

from neumann1.types import (
    Problem,
    Representation,
    VerificationResult,
    CostLedger,
    IRKind,
)
from neumann1.family_registry import FamilyAdapter, builtin_family_registry
from neumann1.registry_engine import RegistryEngine
from neumann1.family_conformance import run_family_conformance


EXTERNAL_KIND = "example.scalar_sum"


class ExternalSumCompiler:
    def form(self, problem, ledger):
        ledger.representation_steps += 1
        if not problem.raw_text.lower().startswith("sum:"):
            return Representation(IRKind.UNKNOWN, {}, 0.0, "not external sum syntax")
        try:
            values = [
                float(x.strip())
                for x in problem.raw_text.split(":", 1)[1].split(",")
            ]
        except ValueError:
            return Representation(IRKind.UNKNOWN, {}, 0.0, "invalid scalar list")
        if len(values) < 2:
            return Representation(IRKind.UNKNOWN, {}, 0.0, "need >=2 scalars")
        return Representation(EXTERNAL_KIND, {"values": values}, 1.0, "external compiler")


class ExternalSumSolver:
    name = "example_sum"

    def supports(self, representation):
        return representation.kind == EXTERNAL_KIND

    def solve(self, representation, ledger):
        ledger.solver_steps += len(representation.payload["values"])
        return {"sum": sum(representation.payload["values"])}


class ExternalSumVerifier:
    def verify(self, problem, representation, answer, ledger):
        ledger.verification_steps += 1
        expected = sum(representation.payload["values"])
        ok = abs(answer["sum"] - expected) < 1e-12
        return VerificationResult(ok, "verified" if ok else "wrong result")


def build_external_adapter():
    return FamilyAdapter(
        family_id="example.scalar_sum",
        ir_kind=EXTERNAL_KIND,
        compiler=ExternalSumCompiler(),
        solver=ExternalSumSolver(),
        answer_verifier=ExternalSumVerifier(),
    )


def run():
    registry = builtin_family_registry()
    enum_members_before = [k.value for k in IRKind]

    external = build_external_adapter()
    registry.register(external)

    engine = RegistryEngine(external.compiler, registry)
    execution = engine.solve(Problem("sum: 2, 3, 4.5"))

    conformance = run_family_conformance(
        external,
        valid_texts=["sum: 1, 2", "sum: -3, 4, 10"],
        reject_texts=["sum: one, two", "compute a minimum spanning tree"],
    )

    enum_members_after = [k.value for k in IRKind]

    return {
        "contract_version": "neumann.family.v1",
        "external_kind": EXTERNAL_KIND,
        "registered_kind_ids": list(registry.kind_ids()),
        "irkind_enum_unchanged": enum_members_before == enum_members_after,
        "external_execution_verified": execution.verified,
        "external_execution_answer": execution.answer,
        "external_trace": execution.trace,
        "external_conformance": {
            "valid_compile_rate": conformance.valid_compile_rate,
            "valid_verified_rate": conformance.valid_verified_rate,
            "reject_fail_closed_rate": conformance.reject_fail_closed_rate,
        },
        "claim_boundary": (
            "This proves an external namespaced kind can use the runtime contract "
            "without editing IRKind. It does not yet provide package discovery, "
            "sandboxing, signatures, dependency isolation, or a public plugin index."
        ),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
    with open("benchmark_v012_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
