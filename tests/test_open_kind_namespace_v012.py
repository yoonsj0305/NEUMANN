import pytest

from neumann1.types import (
    Problem,
    Representation,
    VerificationResult,
    CostLedger,
    IRKind,
    kind_id,
)
from neumann1.family_registry import FamilyAdapter, FamilyRegistry, builtin_family_registry
from neumann1.registry_engine import RegistryEngine
from neumann1.family_conformance import run_family_conformance


EXTERNAL_KIND = "example.scalar_sum"


class ExternalSumCompiler:
    def form(self, problem, ledger):
        ledger.representation_steps += 1
        prefix = "sum:"
        if not problem.raw_text.lower().startswith(prefix):
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale="external sum grammar not recognized",
            )
        body = problem.raw_text[len(prefix):].strip()
        try:
            values = [float(x.strip()) for x in body.split(",")]
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
            kind=EXTERNAL_KIND,
            payload={"values": values},
            confidence=1.0,
            rationale="external scalar-sum compiler",
        )


class ExternalSumSolver:
    name = "example_sum"

    def supports(self, representation):
        return representation.kind == EXTERNAL_KIND

    def solve(self, representation, ledger):
        ledger.solver_steps += len(representation.payload["values"])
        return {"sum": sum(representation.payload["values"])}


class ExternalSumVerifier:
    def verify(self, problem, representation, answer, ledger):
        ledger.verification_steps += len(representation.payload["values"])
        expected = sum(representation.payload["values"])
        ok = abs(answer["sum"] - expected) < 1e-12
        return VerificationResult(ok, "external sum verified" if ok else "wrong sum")


def external_adapter():
    return FamilyAdapter(
        family_id="example.scalar_sum",
        ir_kind=EXTERNAL_KIND,
        compiler=ExternalSumCompiler(),
        solver=ExternalSumSolver(),
        answer_verifier=ExternalSumVerifier(),
    )


def test_core_enum_maps_into_reserved_namespace_without_breaking_legacy_enum():
    assert kind_id(IRKind.BIPARTITE_MATCHING) == "core.bipartite_matching"
    assert IRKind.BIPARTITE_MATCHING.value == "bipartite_matching"


def test_external_kind_requires_namespace_and_cannot_claim_core_namespace():
    with pytest.raises(ValueError):
        kind_id("scalar_sum")
    with pytest.raises(ValueError):
        kind_id("core.third_party")
    assert kind_id(EXTERNAL_KIND) == EXTERNAL_KIND


def test_external_family_registers_without_modifying_irkind_enum():
    before = set(IRKind)
    registry = builtin_family_registry()
    registry.register(external_adapter())
    after = set(IRKind)

    assert before == after
    assert EXTERNAL_KIND in registry.kind_ids()
    assert registry.get(EXTERNAL_KIND).family_id == "example.scalar_sum"


def test_external_family_executes_through_registry_engine():
    adapter = external_adapter()
    registry = builtin_family_registry()
    registry.register(adapter)
    engine = RegistryEngine(adapter.compiler, registry)

    result = engine.solve(Problem("sum: 2, 3, 4.5"))
    assert result.verified
    assert result.answer["sum"] == 9.5
    assert result.representation.kind == EXTERNAL_KIND
    assert "kind_id=example.scalar_sum" in result.trace
    assert "family=example.scalar_sum" in result.trace


def test_external_family_conformance_uses_same_contract():
    result = run_family_conformance(
        external_adapter(),
        valid_texts=["sum: 1, 2", "sum: -3, 4, 10"],
        reject_texts=["sum: one, two", "find a shortest path"],
    )
    assert result.valid_compile_rate == 1.0
    assert result.valid_verified_rate == 1.0
    assert result.reject_fail_closed_rate == 1.0
