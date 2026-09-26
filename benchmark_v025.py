from __future__ import annotations

import json
import tempfile
from pathlib import Path

from neumann1 import (
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


def make_manifest(description="benchmark"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.durable_attestation_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
        "description": description,
    })


def passing_attestation(m):
    return LifecycleAttestation(
        attestation_version="neumann.lifecycle-attestation.v1",
        manifest_digest_sha256=m.digest_sha256,
        plugin_id=m.plugin_id,
        worker_state_class=WorkerStateClass.CACHE_ONLY,
        corpus_digest_sha256="2" * 64,
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


def run():
    m = make_manifest()
    authorization = PluginAuthorizationLedger()
    authorization.approve(m, "benchmark approval")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "attestation.jsonl"
        evidence = HashChainedAttestationLedger(path)
        attestation = passing_attestation(m)
        evidence.issue(attestation, "benchmark evidence")
        issued_head = evidence.head_sha256

        reloaded = HashChainedAttestationLedger(
            path, expected_head_sha256=issued_head
        )
        restart_preserved = (
            reloaded.require_manifest(m).digest_sha256 == attestation.digest_sha256
        )

        adapter = build_persistent_out_of_process_adapter(
            m,
            authorization,
            attestation_registry=reloaded,
            timeout_seconds=8.0,
        )
        registry = ManagedPluginRegistry(builtin_family_registry(), authorization)
        registry.register_plugin(m, adapter)
        engine = RegistryEngine(adapter.compiler, registry)

        first = engine.solve(Problem("probe: before-revoke"))
        requests_before_revoke = adapter.compiler.dispatcher.request_count
        running_before_revoke = adapter.compiler.dispatcher.is_running

        reloaded.revoke_manifest(m, "benchmark revoke")
        revoked_head = reloaded.head_sha256
        revoked_blocked = False
        try:
            engine.solve(Problem("probe: after-revoke"))
        except PermissionError:
            revoked_blocked = True

        no_post_revoke_rpc = (
            adapter.compiler.dispatcher.request_count == requests_before_revoke
        )
        worker_terminated = not adapter.compiler.dispatcher.is_running

        after_restart = HashChainedAttestationLedger(
            path, expected_head_sha256=revoked_head
        )
        revoke_survived_restart = False
        try:
            after_restart.require_manifest(m)
        except PermissionError:
            revoke_survived_restart = True

        return {
            "ledger_version": after_restart.checkpoint().ledger_version,
            "manifest_digest_sha256": m.digest_sha256,
            "attestation_digest_sha256": attestation.digest_sha256,
            "issued_head_sha256": issued_head,
            "revoked_head_sha256": revoked_head,
            "restart_preserved_active_evidence": restart_preserved,
            "persistent_execution_before_revoke_verified": first.verified,
            "worker_running_before_revoke": running_before_revoke,
            "use_time_revocation_blocked_next_execution": revoked_blocked,
            "post_revoke_plugin_requests": (
                adapter.compiler.dispatcher.request_count - requests_before_revoke
            ),
            "no_post_revoke_rpc": no_post_revoke_rpc,
            "worker_terminated_after_evidence_revoke": worker_terminated,
            "revocation_survived_restart": revoke_survived_restart,
            "keep_durable_attestation_gate": (
                restart_preserved
                and first.verified
                and running_before_revoke
                and revoked_blocked
                and no_post_revoke_rpc
                and worker_terminated
                and revoke_survived_restart
            ),
            "boundary": (
                "The local hash chain is tamper-evident, not rollback-proof by itself. "
                "Valid-prefix rollback detection still requires a trusted external head."
            ),
        }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
