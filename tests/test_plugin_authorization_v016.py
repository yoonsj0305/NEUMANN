import pytest

from neumann1 import (
    FamilyAdapter,
    IRKind,
    Problem,
    Representation,
    VerificationResult,
    RegistryEngine,
    builtin_family_registry,
)
from neumann1.plugin_authorization import (
    AuthorizedPluginActivator,
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
)
from neumann1.plugin_manifest import PLUGIN_MANIFEST_VERSION, PluginManifest


KIND = "example.counted_sum"


def manifest(description="counted sum"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "example.counted_sum_plugin",
        "plugin_version": "0.1.0",
        "family_id": "example.counted_sum",
        "kind": KIND,
        "family_contract_version": "neumann.family.v1",
        "entry_point": "example_counted:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "description": description,
    })


class Compiler:
    def form(self, problem, ledger):
        ledger.representation_steps += 1
        if not problem.raw_text.startswith("sum:"):
            return Representation(IRKind.UNKNOWN, {}, 0.0, "not sum")
        values = [float(x.strip()) for x in problem.raw_text.split(":", 1)[1].split(",")]
        return Representation(KIND, {"values": values}, 1.0, "counted sum")


class CountingSolver:
    name = "counting_sum"
    def __init__(self):
        self.calls = 0
    def supports(self, rep):
        return rep.kind == KIND
    def solve(self, rep, ledger):
        self.calls += 1
        ledger.solver_steps += 1
        return {"sum": sum(rep.payload["values"])}


class Verifier:
    def verify(self, problem, rep, answer, ledger):
        ledger.verification_steps += 1
        ok = answer["sum"] == sum(rep.payload["values"])
        return VerificationResult(ok, "verified" if ok else "wrong")


def adapter(solver=None):
    return FamilyAdapter(
        family_id="example.counted_sum",
        ir_kind=KIND,
        compiler=Compiler(),
        solver=solver or CountingSolver(),
        answer_verifier=Verifier(),
    )


def test_unapproved_manifest_cannot_trigger_resolver_import():
    calls = []
    ledger = PluginAuthorizationLedger()
    def resolver(entry):
        calls.append(entry)
        return lambda: adapter()

    with pytest.raises(PermissionError):
        AuthorizedPluginActivator(ledger, resolver).activate(manifest())
    assert calls == []


def test_approval_is_bound_to_exact_manifest_digest():
    ledger = PluginAuthorizationLedger()
    approved = manifest("approved")
    changed = manifest("changed")
    ledger.approve(approved)
    ledger.require_manifest(approved)
    with pytest.raises(PermissionError):
        ledger.require_manifest(changed)


def test_revocation_blocks_next_execution_without_calling_solver():
    m = manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    solver = CountingSolver()
    a = adapter(solver)

    managed = ManagedPluginRegistry(builtin_family_registry(), ledger)
    managed.register_plugin(m, a)
    engine = RegistryEngine(a.compiler, managed)

    before = engine.solve(Problem("sum: 2, 3"))
    assert before.verified
    assert solver.calls == 1

    ledger.revoke(m.plugin_id, reason="test revocation")
    after = engine.solve(Problem("sum: 2, 3"))
    assert not after.verified
    assert after.solver_name == "fallback_required"
    assert solver.calls == 1
    assert "authorization" in after.verification_reason.lower()


def test_reapproval_same_manifest_restores_execution():
    m = manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    solver = CountingSolver()
    a = adapter(solver)
    managed = ManagedPluginRegistry(builtin_family_registry(), ledger)
    managed.register_plugin(m, a)
    engine = RegistryEngine(a.compiler, managed)

    assert engine.solve(Problem("sum: 1, 2")).verified
    ledger.revoke(m.plugin_id)
    assert not engine.solve(Problem("sum: 1, 2")).verified
    ledger.approve(m, reason="re-approved")
    assert engine.solve(Problem("sum: 1, 2")).verified
    assert solver.calls == 2


def test_ledger_sequence_is_append_only_and_monotonic():
    m = manifest()
    ledger = PluginAuthorizationLedger()
    e1 = ledger.approve(m, "first")
    e2 = ledger.revoke(m.plugin_id, "stop")
    e3 = ledger.approve(m, "resume")
    assert [e.sequence for e in ledger.events()] == [1, 2, 3]
    assert [e.action for e in ledger.events()] == ["APPROVE", "REVOKE", "APPROVE"]
    assert e1.sequence < e2.sequence < e3.sequence