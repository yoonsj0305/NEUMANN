import json

import pytest

from neumann1 import (
    ATTESTATION_GENESIS_HASH,
    AttestationLedgerIntegrityError,
    AttestationStatus,
    HashChainedAttestationLedger,
    LifecycleAttestation,
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
    PluginManifest,
    PLUGIN_MANIFEST_VERSION,
    Problem,
    RegistryEngine,
    WorkerStateClass,
    builtin_family_registry,
    build_persistent_out_of_process_adapter,
)


def manifest(description="stable"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.durable_attestation_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
        "description": description,
    })


def passing_attestation(m, corpus_digest="1" * 64):
    return LifecycleAttestation(
        attestation_version="neumann.lifecycle-attestation.v1",
        manifest_digest_sha256=m.digest_sha256,
        plugin_id=m.plugin_id,
        worker_state_class=WorkerStateClass.CACHE_ONLY,
        corpus_digest_sha256=corpus_digest,
        case_count=3,
        warm_repetitions=2,
        warm_passed=True,
        recycled_passed=True,
        cross_generation_passed=True,
        semantic_equivalence_rate=1.0,
        warm_generation_count=1,
        recycled_generation_count=3,
        cross_generation_count=9,
        status=AttestationStatus.PASS,
    )


def approved(m):
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    return ledger


def test_durable_attestation_survives_restart_and_grants_exact_manifest(tmp_path):
    m = manifest()
    evidence = passing_attestation(m)
    path = tmp_path / "attestation.jsonl"

    first = HashChainedAttestationLedger(path)
    assert first.head_sha256 == ATTESTATION_GENESIS_HASH
    first.issue(evidence, "initial lifecycle evidence")
    checkpoint = first.checkpoint()

    reloaded = HashChainedAttestationLedger(
        path, expected_head_sha256=checkpoint.head_sha256
    )
    loaded = reloaded.require_manifest(m)
    assert loaded.digest_sha256 == evidence.digest_sha256
    assert reloaded.sequence == 1


def test_use_time_attestation_revocation_stops_next_plugin_rpc(tmp_path):
    m = manifest()
    authorization = approved(m)
    evidence_ledger = HashChainedAttestationLedger(tmp_path / "attestation.jsonl")
    evidence_ledger.issue(passing_attestation(m), "grant persistent evidence")

    adapter = build_persistent_out_of_process_adapter(
        m,
        authorization,
        attestation_registry=evidence_ledger,
        timeout_seconds=8.0,
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), authorization)
    registry.register_plugin(m, adapter)
    engine = RegistryEngine(adapter.compiler, registry)

    first = engine.solve(Problem("probe: before-revoke"))
    assert first.verified
    assert adapter.compiler.dispatcher.is_running
    requests_before_revoke = adapter.compiler.dispatcher.request_count

    evidence_ledger.revoke_manifest(m, "evidence withdrawn")
    with pytest.raises(PermissionError, match="attestation revoked"):
        engine.solve(Problem("probe: after-revoke"))

    assert adapter.compiler.dispatcher.request_count == requests_before_revoke
    assert not adapter.compiler.dispatcher.is_running


def test_revoked_evidence_remains_revoked_after_restart(tmp_path):
    m = manifest()
    path = tmp_path / "attestation.jsonl"
    ledger = HashChainedAttestationLedger(path)
    attestation = passing_attestation(m)
    ledger.issue(attestation)
    ledger.revoke_manifest(m, "regression found")
    checkpoint = ledger.checkpoint()

    reloaded = HashChainedAttestationLedger(
        path, expected_head_sha256=checkpoint.head_sha256
    )
    with pytest.raises(PermissionError, match="attestation revoked"):
        reloaded.require_manifest(m)

    reloaded.issue(attestation, "re-attested after review")
    assert reloaded.require_manifest(m).digest_sha256 == attestation.digest_sha256


def test_changed_manifest_does_not_inherit_old_durable_evidence(tmp_path):
    old = manifest("old")
    ledger = HashChainedAttestationLedger(tmp_path / "attestation.jsonl")
    ledger.issue(passing_attestation(old))

    changed = manifest("changed")
    assert changed.digest_sha256 != old.digest_sha256
    with pytest.raises(
        PermissionError, match="stale or bound to a different manifest digest"
    ):
        ledger.require_manifest(changed)


def test_attestation_ledger_detects_record_mutation(tmp_path):
    m = manifest()
    path = tmp_path / "attestation.jsonl"
    ledger = HashChainedAttestationLedger(path)
    ledger.issue(passing_attestation(m), "original")

    row = json.loads(path.read_text(encoding="utf-8"))
    row["reason"] = "tampered"
    path.write_text(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AttestationLedgerIntegrityError, match="event hash mismatch"):
        HashChainedAttestationLedger(path)


def test_trusted_head_detects_valid_prefix_rollback(tmp_path):
    m = manifest()
    path = tmp_path / "attestation.jsonl"
    ledger = HashChainedAttestationLedger(path)
    ledger.issue(passing_attestation(m), "issue")
    first_prefix = path.read_text(encoding="utf-8")
    ledger.revoke_manifest(m, "revoke")
    trusted_head = ledger.head_sha256

    path.write_text(first_prefix, encoding="utf-8")
    with pytest.raises(
        AttestationLedgerIntegrityError,
        match="possible rollback or truncation",
    ):
        HashChainedAttestationLedger(path, expected_head_sha256=trusted_head)
