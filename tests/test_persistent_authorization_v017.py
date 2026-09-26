import json

import pytest

from neumann1.plugin_manifest import PLUGIN_MANIFEST_VERSION, PluginManifest
from neumann1.persistent_authorization import (
    GENESIS_HASH,
    HashChainedAuthorizationLedger,
    LedgerIntegrityError,
)


def manifest(description="stable"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "example.persisted_plugin",
        "plugin_version": "0.1.0",
        "family_id": "example.persisted",
        "kind": "example.persisted",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "example_persisted:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "description": description,
    })


def test_state_and_head_survive_ledger_restart(tmp_path):
    path = tmp_path / "auth.jsonl"
    m = manifest()
    first = HashChainedAuthorizationLedger(path)
    first.approve(m, "initial")
    first.revoke(m.plugin_id, "pause")
    first.approve(m, "resume")
    checkpoint = first.checkpoint()

    second = HashChainedAuthorizationLedger(
        path, expected_head_sha256=checkpoint.head_sha256
    )
    assert second.sequence == 3
    assert second.head_sha256 == checkpoint.head_sha256
    assert second.current(m.plugin_id).active is True
    second.require_manifest(m)


def test_mutating_persisted_event_is_detected(tmp_path):
    path = tmp_path / "auth.jsonl"
    ledger = HashChainedAuthorizationLedger(path)
    ledger.approve(manifest(), "original reason")

    record = json.loads(path.read_text(encoding="utf-8").strip())
    record["reason"] = "mutated reason"
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityError, match="hash mismatch"):
        HashChainedAuthorizationLedger(path)


def test_reordering_events_is_detected(tmp_path):
    path = tmp_path / "auth.jsonl"
    m = manifest()
    ledger = HashChainedAuthorizationLedger(path)
    ledger.approve(m)
    ledger.revoke(m.plugin_id)

    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(lines[1] + "\n" + lines[0] + "\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityError):
        HashChainedAuthorizationLedger(path)


def test_valid_prefix_truncation_requires_trusted_head_to_detect(tmp_path):
    path = tmp_path / "auth.jsonl"
    m = manifest()
    ledger = HashChainedAuthorizationLedger(path)
    ledger.approve(m, "one")
    ledger.revoke(m.plugin_id, "two")
    ledger.approve(m, "three")
    trusted = ledger.checkpoint()

    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")

    # A complete older prefix is internally valid by itself.
    older = HashChainedAuthorizationLedger(path)
    assert older.sequence == 2
    assert older.head_sha256 != trusted.head_sha256

    # A trusted head from outside the ledger reveals the rollback/truncation.
    with pytest.raises(LedgerIntegrityError, match="trusted expected head"):
        HashChainedAuthorizationLedger(
            path, expected_head_sha256=trusted.head_sha256
        )


def test_missing_ledger_with_non_genesis_expected_head_is_rejected(tmp_path):
    path = tmp_path / "missing.jsonl"
    with pytest.raises(LedgerIntegrityError):
        HashChainedAuthorizationLedger(path, expected_head_sha256="a" * 64)

    empty = HashChainedAuthorizationLedger(path, expected_head_sha256=GENESIS_HASH)
    assert empty.sequence == 0


def test_append_after_reload_extends_verified_chain(tmp_path):
    path = tmp_path / "auth.jsonl"
    m = manifest()
    first = HashChainedAuthorizationLedger(path)
    first.approve(m)
    old_head = first.head_sha256

    second = HashChainedAuthorizationLedger(path, expected_head_sha256=old_head)
    second.revoke(m.plugin_id)
    assert second.sequence == 2
    assert second.head_sha256 != old_head

    third = HashChainedAuthorizationLedger(
        path, expected_head_sha256=second.head_sha256
    )
    assert third.current(m.plugin_id).active is False
    with pytest.raises(PermissionError):
        third.require_manifest(m)

def test_reloaded_persistent_ledger_drives_managed_runtime(tmp_path):
    from neumann1 import (
        FamilyAdapter, IRKind, Problem, Representation, RegistryEngine,
        VerificationResult, builtin_family_registry,
    )
    from neumann1.plugin_authorization import ManagedPluginRegistry

    kind = "example.persisted_runtime"
    runtime_manifest = PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "example.persisted_runtime_plugin",
        "plugin_version": "0.1.0",
        "family_id": "example.persisted_runtime",
        "kind": kind,
        "family_contract_version": "neumann.family.v1",
        "entry_point": "example_runtime:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })

    class Compiler:
        def form(self, problem, ledger):
            ledger.representation_steps += 1
            if problem.raw_text != "ping":
                return Representation(IRKind.UNKNOWN, {}, 0.0, "not ping")
            return Representation(kind, {"value": 7}, 1.0, "persisted runtime")

    class Solver:
        name = "persisted_runtime_solver"
        def supports(self, rep):
            return rep.kind == kind
        def solve(self, rep, ledger):
            ledger.solver_steps += 1
            return {"value": rep.payload["value"]}

    class Verifier:
        def verify(self, problem, rep, answer, ledger):
            ledger.verification_steps += 1
            ok = answer["value"] == 7
            return VerificationResult(ok, "verified" if ok else "wrong")

    path = tmp_path / "runtime-auth.jsonl"
    first = HashChainedAuthorizationLedger(path)
    first.approve(runtime_manifest, "persist across restart")
    trusted_head = first.head_sha256

    # Simulate process restart by constructing a new ledger object from disk.
    reloaded = HashChainedAuthorizationLedger(
        path, expected_head_sha256=trusted_head
    )
    adapter = FamilyAdapter(
        family_id=runtime_manifest.family_id,
        ir_kind=kind,
        compiler=Compiler(),
        solver=Solver(),
        answer_verifier=Verifier(),
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), reloaded)
    registry.register_plugin(runtime_manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)

    assert engine.solve(Problem("ping")).verified

    reloaded.revoke(runtime_manifest.plugin_id, "stop after restart")
    blocked = engine.solve(Problem("ping"))
    assert not blocked.verified
    assert blocked.solver_name == "fallback_required"