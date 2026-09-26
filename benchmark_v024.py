from __future__ import annotations

import json

from neumann1 import (
    AttestationStatus, LifecycleAttestationRegistry, LifecycleConformanceCase,
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
    build_persistent_out_of_process_adapter, run_lifecycle_conformance_attestation,
)


def make_manifest(description="benchmark"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.lifecycle_attestation_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
        "description": description,
    })


def corpus():
    return (
        LifecycleConformanceCase("one", "probe: one", {"value": 42, "mode": "one"}),
        LifecycleConformanceCase("two", "probe: two", {"value": 42, "mode": "two"}),
        LifecycleConformanceCase("three", "probe: three", {"value": 42, "mode": "three"}),
    )


def ledger_for(m):
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    return ledger


def run():
    m = make_manifest()
    ledger = ledger_for(m)

    missing_attestation_blocked = False
    try:
        build_persistent_out_of_process_adapter(m, ledger)
    except PermissionError:
        missing_attestation_blocked = True

    attestation = run_lifecycle_conformance_attestation(
        m, ledger, corpus(), warm_repetitions=2, timeout_seconds=8.0
    )
    registry = LifecycleAttestationRegistry([attestation])
    adapter = build_persistent_out_of_process_adapter(
        m, ledger, attestation_registry=registry, timeout_seconds=8.0
    )
    managed = ManagedPluginRegistry(builtin_family_registry(), ledger)
    managed.register_plugin(m, adapter)
    engine = RegistryEngine(adapter.compiler, managed)
    result = engine.solve(Problem("probe: one"))
    adapter.compiler.dispatcher.close()

    changed = make_manifest("changed after attestation")
    changed_ledger = ledger_for(changed)
    stale_attestation_blocked = False
    try:
        build_persistent_out_of_process_adapter(
            changed, changed_ledger, attestation_registry=registry
        )
    except PermissionError:
        stale_attestation_blocked = True

    return {
        "attestation_version": attestation.attestation_version,
        "attestation_status": attestation.status.value,
        "manifest_digest_sha256": attestation.manifest_digest_sha256,
        "attestation_digest_sha256": attestation.digest_sha256,
        "corpus_digest_sha256": attestation.corpus_digest_sha256,
        "case_count": attestation.case_count,
        "warm_repetitions": attestation.warm_repetitions,
        "warm_passed": attestation.warm_passed,
        "recycled_passed": attestation.recycled_passed,
        "cross_generation_passed": attestation.cross_generation_passed,
        "semantic_equivalence_rate": attestation.semantic_equivalence_rate,
        "warm_generation_count": attestation.warm_generation_count,
        "recycled_generation_count": attestation.recycled_generation_count,
        "cross_generation_count": attestation.cross_generation_count,
        "missing_attestation_blocked": missing_attestation_blocked,
        "persistent_execution_after_attestation_verified": result.verified,
        "stale_attestation_blocked": stale_attestation_blocked,
        "keep_attestation_gate": (
            attestation.status == AttestationStatus.PASS
            and attestation.semantic_equivalence_rate == 1.0
            and missing_attestation_blocked
            and result.verified
            and stale_attestation_blocked
        ),
        "boundary": (
            "This attestation is deterministic behavioral evidence over a small declared corpus, "
            "not a proof of behavior for all inputs. The registry is in-memory in v0.0.24."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))