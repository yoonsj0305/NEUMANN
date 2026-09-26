import pytest

from neumann1 import Problem, IRKind
from neumann1.family_registry import (
    FamilyAdapter,
    FamilyRegistry,
    FAMILY_CONTRACT_VERSION,
    builtin_family_registry,
)
from neumann1.registry_engine import RegistryEngine
from neumann1.composite import CompositeStructureFormer
from neumann1.family_conformance import run_family_conformance


def test_builtin_registry_has_two_executable_families():
    registry = builtin_family_registry()
    assert set(registry.kinds()) == {
        IRKind.BIPARTITE_MATCHING,
        IRKind.LINEAR_SYSTEM,
    }
    assert registry.get_by_id("core.bipartite_matching") is not None
    assert registry.get_by_id("core.linear_system") is not None


def test_registry_rejects_duplicate_kind():
    registry = builtin_family_registry()
    existing = registry.get(IRKind.BIPARTITE_MATCHING)
    with pytest.raises(ValueError):
        registry.register(
            FamilyAdapter(
                family_id="duplicate.matching",
                ir_kind=IRKind.BIPARTITE_MATCHING,
                compiler=existing.compiler,
                solver=existing.solver,
                answer_verifier=existing.answer_verifier,
            )
        )


def test_registry_rejects_wrong_contract_version():
    existing = builtin_family_registry().get(IRKind.BIPARTITE_MATCHING)
    with pytest.raises(ValueError):
        FamilyRegistry([
            FamilyAdapter(
                family_id="bad.version",
                ir_kind=IRKind.BIPARTITE_MATCHING,
                compiler=existing.compiler,
                solver=existing.solver,
                answer_verifier=existing.answer_verifier,
                contract_version="neumann.family.v999",
            )
        ])


def test_registry_engine_executes_family_owned_solver_and_verifier():
    registry = builtin_family_registry()
    former = CompositeStructureFormer([a.compiler for a in registry.adapters()])
    engine = RegistryEngine(former, registry)

    matching = engine.solve(Problem("S1 can use A or C; S2 can use B or C"))
    assert matching.verified
    assert "family=core.bipartite_matching" in matching.trace

    linear = engine.solve(Problem("x + y = 5; x - y = 1"))
    assert linear.verified
    assert "family=core.linear_system" in linear.trace


def test_matching_family_conformance():
    adapter = builtin_family_registry().get(IRKind.BIPARTITE_MATCHING)
    result = run_family_conformance(
        adapter,
        valid_texts=[
            "S1 can use A or C; S2 can use B or C",
            "Allowed for R1: X, Y; Allowed for R2: Y, Z",
        ],
        reject_texts=[
            "S1 can use A or C with cost 5; S2 can use B",
            "Find a shortest path.",
        ],
    )
    assert result.valid_compile_rate == 1.0
    assert result.valid_verified_rate == 1.0
    assert result.reject_fail_closed_rate == 1.0


def test_linear_family_conformance():
    adapter = builtin_family_registry().get(IRKind.LINEAR_SYSTEM)
    result = run_family_conformance(
        adapter,
        valid_texts=[
            "x + y = 5; x - y = 1",
            "2*a + b = 7; a - b = 2",
        ],
        reject_texts=[
            "x*x + y = 5; x - y = 1",
            "x + y <= 5; x - y = 1",
        ],
    )
    assert result.valid_compile_rate == 1.0
    assert result.valid_verified_rate == 1.0
    assert result.reject_fail_closed_rate == 1.0
