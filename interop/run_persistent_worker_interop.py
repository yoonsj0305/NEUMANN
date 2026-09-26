from __future__ import annotations

import importlib.metadata as md
import json
import os
import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, Problem, RegistryEngine,
    builtin_family_registry, catalog_from_discovery, discover_installed_manifests,
)
from neumann1.persistent_plugin_isolation import _build_unattested_persistent_adapter_for_conformance as build_persistent_out_of_process_adapter


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    sys.modules.pop(PLUGIN_MODULE, None)
    report = discover_installed_manifests()
    manifest = catalog_from_discovery(report).get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("external scalar-sum manifest not discovered")

    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest, "persistent interop approval")
    adapter = build_persistent_out_of_process_adapter(
        manifest, ledger, timeout_seconds=8.0
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)
    dispatcher = adapter.compiler.dispatcher
    parent_pid = os.getpid()

    first = engine.solve(Problem("sum: 2, 3, 4.5"))
    if not first.verified or abs(float(first.answer["sum"]) - 9.5) > 1e-12:
        raise RuntimeError("persistent external first execution failed")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("external plugin imported into parent")
    first_pid = dispatcher.worker_pid
    if first_pid is None or first_pid == parent_pid:
        raise RuntimeError("persistent plugin did not execute in child")
    if dispatcher.start_count != 1 or dispatcher.request_count != 3:
        raise RuntimeError("unexpected persistent lifecycle after first solve")

    second = engine.solve(Problem("sum: 10, -2, 0.5"))
    if not second.verified or abs(float(second.answer["sum"]) - 8.5) > 1e-12:
        raise RuntimeError("persistent external second execution failed")
    if dispatcher.worker_pid != first_pid or dispatcher.start_count != 1:
        raise RuntimeError("persistent worker was not reused")
    requests_before_revoke = dispatcher.request_count

    ledger.revoke(manifest.plugin_id, "persistent interop revoke")
    revoked = engine.solve(Problem("sum: 1, 2"))
    if revoked.verified:
        raise RuntimeError("revoked persistent external plugin verified")
    if dispatcher.request_count != requests_before_revoke:
        raise RuntimeError("request sent after revocation")
    if dispatcher.is_running:
        raise RuntimeError("persistent worker survived revocation")

    ledger.approve(manifest, "persistent interop reapprove")
    restored = engine.solve(Problem("sum: 1, 2"))
    if not restored.verified or restored.answer["sum"] != 3.0:
        raise RuntimeError("reapproved persistent plugin did not recover")
    second_pid = dispatcher.worker_pid
    if dispatcher.start_count != 2 or second_pid is None:
        raise RuntimeError("reapproval did not create a replacement worker")

    result = {
        "core_distribution_version": md.version("neumann1"),
        "plugin_distribution_version": md.version("neumann-example-scalar-sum"),
        "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
        "parent_pid": parent_pid,
        "first_worker_pid": first_pid,
        "replacement_worker_pid": second_pid,
        "first_two_solves_reused_same_worker": True,
        "start_count_after_reapproval": dispatcher.start_count,
        "requests_before_revoke": requests_before_revoke,
        "post_revocation_requests": 0,
        "worker_running_after_revoke": False,
        "restored_execution_verified": restored.verified,
        "boundary": (
            "Persistent external plugin execution preserves process separation and revocation, "
            "but retained child-process state and same-user host privileges remain explicit boundaries."
        ),
    }
    dispatcher.close()
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))