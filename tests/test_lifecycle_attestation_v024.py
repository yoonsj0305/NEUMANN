import pytest

from neumann1 import (
    LifecycleAttestationRegistry, LifecycleConformanceCase,
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine,
    AttestationStatus, builtin_family_registry,
    build_persistent_out_of_process_adapter,
    run_lifecycle_conformance_attestation,
)


def manifest(description="stable"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.attestation_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
        "description": description,
    })


def cases():
    return (
        LifecycleConformanceCase("ok", "probe: ok", {"value": 42, "mode": "ok"}),
        LifecycleConformanceCase("alpha", "probe: alpha", {"value": 42, "mode": "alpha"}),
        LifecycleConformanceCase("beta", "probe: beta", {"value": 42, "mode": "beta"}),
    )


def approved(m):
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    return ledger


def test_public_persistent_builder_requires_attestation():
    m = manifest()
    ledger = approved(m)
    with pytest.raises(PermissionError, match="lifecycle attestation required"):
        build_persistent_out_of_process_adapter(m, ledger)


def test_passing_attestation_unlocks_exact_manifest_persistent_execution():
    m = manifest()
    ledger = approved(m)
    attestation = run_lifecycle_conformance_attestation(
        m, ledger, cases(), warm_repetitions=2, timeout_seconds=8.0
    )
    assert attestation.status == AttestationStatus.PASS
    assert attestation.manifest_digest_sha256 == m.digest_sha256
    assert attestation.semantic_equivalence_rate == 1.0
    assert attestation.warm_passed
    assert attestation.recycled_passed
    assert attestation.cross_generation_passed

    registry = LifecycleAttestationRegistry([attestation])
    adapter = build_persistent_out_of_process_adapter(
        m, ledger, attestation_registry=registry, timeout_seconds=8.0
    )
    managed = ManagedPluginRegistry(builtin_family_registry(), ledger)
    managed.register_plugin(m, adapter)
    engine = RegistryEngine(adapter.compiler, managed)
    try:
        result = engine.solve(Problem("probe: ok"))
        assert result.verified
        assert result.answer["value"] == 42
    finally:
        adapter.compiler.dispatcher.close()


def test_attestation_is_bound_to_exact_manifest_digest():
    old = manifest("old")
    old_ledger = approved(old)
    attestation = run_lifecycle_conformance_attestation(old, old_ledger, cases(), timeout_seconds=8.0)
    registry = LifecycleAttestationRegistry([attestation])

    changed = manifest("changed")
    changed_ledger = approved(changed)
    assert changed.digest_sha256 != old.digest_sha256
    with pytest.raises(PermissionError, match="stale or bound to a different manifest digest"):
        build_persistent_out_of_process_adapter(
            changed, changed_ledger, attestation_registry=registry
        )


def test_failed_conformance_does_not_grant_persistent_privilege():
    m = manifest()
    ledger = approved(m)
    bad_cases = (
        LifecycleConformanceCase("ok", "probe: ok", {"value": 999}),
        LifecycleConformanceCase("alpha", "probe: alpha", {"value": 42}),
        LifecycleConformanceCase("beta", "probe: beta", {"value": 42}),
    )
    attestation = run_lifecycle_conformance_attestation(m, ledger, bad_cases, timeout_seconds=8.0)
    assert attestation.status == AttestationStatus.FAIL
    assert attestation.semantic_equivalence_rate < 1.0
    registry = LifecycleAttestationRegistry([attestation])
    with pytest.raises(PermissionError, match="did not pass"):
        build_persistent_out_of_process_adapter(
            m, ledger, attestation_registry=registry
        )


def test_attestation_serialization_detects_digest_tamper():
    m = manifest()
    ledger = approved(m)
    attestation = run_lifecycle_conformance_attestation(m, ledger, cases(), timeout_seconds=8.0)
    data = attestation.to_dict()
    assert data["attestation_digest_sha256"] == attestation.digest_sha256
    data["corpus_digest_sha256"] = "0" * 64
    from neumann1 import LifecycleAttestation
    with pytest.raises(ValueError, match="digest mismatch"):
        LifecycleAttestation.from_dict(data)


def test_attestation_minimum_corpus_and_warm_repetition_gates():
    m = manifest()
    ledger = approved(m)
    with pytest.raises(ValueError, match="at least 3 cases"):
        run_lifecycle_conformance_attestation(m, ledger, cases()[:2])
    with pytest.raises(ValueError, match="warm_repetitions must be >= 2"):
        run_lifecycle_conformance_attestation(m, ledger, cases(), warm_repetitions=1)