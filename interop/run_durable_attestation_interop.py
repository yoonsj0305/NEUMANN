from __future__ import annotations

import importlib.metadata as md
import json
from pathlib import Path
import sys
import tempfile

from neumann1 import (
    HashChainedAttestationLedger,
    LifecycleConformanceCase,
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
    Problem,
    RegistryEngine,
    builtin_family_registry,
    build_persistent_out_of_process_adapter,
    catalog_from_discovery,
    discover_installed_manifests,
    run_lifecycle_conformance_attestation,
)


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    sys.modules.pop(PLUGIN_MODULE, None)
    manifest = catalog_from_discovery(discover_installed_manifests()).get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("external scalar-sum manifest not discovered")

    authorization = PluginAuthorizationLedger()
    authorization.approve(manifest, "fresh-venv durable lifecycle evidence")

    cases = (
        LifecycleConformanceCase("sum_a", "sum: 1, 2", {"sum": 3.0}),
        LifecycleConformanceCase("sum_b", "sum: -3, 4, 10", {"sum": 11.0}),
        LifecycleConformanceCase("sum_c", "sum: 2.5, 0.5, -1", {"sum": 2.0}),
    )
    attestation = run_lifecycle_conformance_attestation(
        manifest,
        authorization,
        cases,
        warm_repetitions=2,
        timeout_seconds=8.0,
    )
    if attestation.status.value != "PASS":
        raise RuntimeError("external lifecycle conformance attestation did not pass")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("conformance attestation imported plugin into parent")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "attestation.jsonl"
        evidence = HashChainedAttestationLedger(path)
        evidence.issue(attestation, "fresh-venv PASS evidence")
        issued_head = evidence.head_sha256

        reloaded = HashChainedAttestationLedger(
            path, expected_head_sha256=issued_head
        )
        adapter = build_persistent_out_of_process_adapter(
            manifest,
            authorization,
            attestation_registry=reloaded,
            timeout_seconds=8.0,
        )
        registry = ManagedPluginRegistry(builtin_family_registry(), authorization)
        registry.register_plugin(manifest, adapter)
        engine = RegistryEngine(adapter.compiler, registry)

        first = engine.solve(Problem("sum: 2, 3, 4.5"))
        second = engine.solve(Problem("sum: 10, -2, 0.5"))
        if not first.verified or first.answer["sum"] != 9.5:
            raise RuntimeError("durably attested external first execution failed")
        if not second.verified or second.answer["sum"] != 8.5:
            raise RuntimeError("durably attested external reuse failed")
        if adapter.compiler.dispatcher.start_count != 1:
            raise RuntimeError("durably attested external plugin did not reuse worker")

        requests_before_revoke = adapter.compiler.dispatcher.request_count
        reloaded.revoke_manifest(manifest, "fresh-venv evidence revoke")
        revoked_head = reloaded.head_sha256

        revoked_blocked = False
        try:
            engine.solve(Problem("sum: 1, 1"))
        except PermissionError:
            revoked_blocked = True
        if not revoked_blocked:
            raise RuntimeError("revoked evidence did not block next external execution")
        if adapter.compiler.dispatcher.request_count != requests_before_revoke:
            raise RuntimeError("plugin RPC occurred after evidence revocation")
        if adapter.compiler.dispatcher.is_running:
            raise RuntimeError("worker remained alive after evidence revocation")

        after_restart = HashChainedAttestationLedger(
            path, expected_head_sha256=revoked_head
        )
        revoke_survived_restart = False
        try:
            after_restart.require_manifest(manifest)
        except PermissionError:
            revoke_survived_restart = True
        if not revoke_survived_restart:
            raise RuntimeError("evidence revocation did not survive restart")
        if PLUGIN_MODULE in sys.modules:
            raise RuntimeError("durable attestation path imported plugin into parent")

        return {
            "core_distribution_version": md.version("neumann1"),
            "plugin_distribution_version": md.version("neumann-example-scalar-sum"),
            "manifest_digest_sha256": manifest.digest_sha256,
            "attestation_digest_sha256": attestation.digest_sha256,
            "issued_head_sha256": issued_head,
            "revoked_head_sha256": revoked_head,
            "persistent_execution_before_revoke_verified": (
                first.verified and second.verified
            ),
            "same_worker_reused_before_revoke": (
                adapter.compiler.dispatcher.start_count == 1
            ),
            "use_time_revocation_blocked": revoked_blocked,
            "post_revoke_plugin_requests": (
                adapter.compiler.dispatcher.request_count - requests_before_revoke
            ),
            "worker_running_after_revoke": adapter.compiler.dispatcher.is_running,
            "revocation_survived_restart": revoke_survived_restart,
            "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
            "boundary": (
                "Durable evidence remains finite-corpus behavioral evidence. "
                "The local ledger needs a trusted external head to detect valid-prefix rollback."
            ),
        }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
