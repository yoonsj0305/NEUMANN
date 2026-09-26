from __future__ import annotations

import importlib.metadata as md
import json
import os
import sys

import neumann1
from neumann1 import (
    Problem,
    RegistryEngine,
    builtin_family_registry,
    discover_installed_manifests,
    catalog_from_discovery,
    run_family_conformance,
)
from neumann1.plugin_authorization import (
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
)
from neumann1.plugin_isolation import build_out_of_process_adapter


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("plugin module was imported before discovery began")

    core_distribution_version = md.version("neumann1")
    plugin_distribution_version = md.version("neumann-example-scalar-sum")

    report = discover_installed_manifests()
    matching = [item for item in report.manifests if item.manifest.plugin_id == PLUGIN_ID]
    if len(matching) != 1:
        raise RuntimeError(f"expected exactly one {PLUGIN_ID} manifest, found {len(matching)}")

    discovered = matching[0]
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("static discovery imported plugin code")

    catalog = catalog_from_discovery(report)
    manifest = catalog.get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("discovered plugin missing from catalog")

    ledger = PluginAuthorizationLedger()
    unapproved_adapter_blocked = False
    try:
        build_out_of_process_adapter(manifest, ledger)
    except PermissionError:
        unapproved_adapter_blocked = PLUGIN_MODULE not in sys.modules
    if not unapproved_adapter_blocked:
        raise RuntimeError("unapproved out-of-process adapter creation was not blocked")

    ledger.approve(manifest, reason="cross-package OOP approval")
    adapter = build_out_of_process_adapter(manifest, ledger, timeout_seconds=8.0)
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("proxy construction imported plugin into parent")

    managed_registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    managed_registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, managed_registry)
    dispatcher = adapter.compiler.dispatcher

    parent_pid = os.getpid()
    launches_before = dispatcher.launch_count
    first = engine.solve(Problem("sum: 2, 3, 4.5"))
    if not first.verified or abs(float(first.answer["sum"]) - 9.5) > 1e-12:
        raise RuntimeError("out-of-process external execution failed")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("external plugin leaked into parent sys.modules")
    if dispatcher.launch_count - launches_before != 3:
        raise RuntimeError("expected compile/solve/verify child dispatches")
    if not dispatcher.worker_pids or any(pid == parent_pid for pid in dispatcher.worker_pids):
        raise RuntimeError("plugin operation executed in parent process")

    launches_after_first = dispatcher.launch_count
    ledger.revoke(manifest.plugin_id, reason="cross-package OOP revocation")
    revoked = engine.solve(Problem("sum: 2, 3, 4.5"))
    if revoked.verified:
        raise RuntimeError("revoked plugin still executed successfully")
    launches_after_revoked_attempt = dispatcher.launch_count
    if launches_after_revoked_attempt != launches_after_first:
        raise RuntimeError("revoked request launched a child process")

    ledger.approve(manifest, reason="cross-package OOP re-approval")
    restored = engine.solve(Problem("sum: 2, 3, 4.5"))
    if not restored.verified:
        raise RuntimeError("re-approved plugin did not resume execution")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("plugin imported into parent after restored execution")

    conformance = run_family_conformance(
        adapter,
        valid_texts=["sum: 1, 2", "sum: -3, 4, 10"],
        reject_texts=["sum: one, two", "find a shortest path"],
    )
    if conformance.valid_compile_rate != 1.0:
        raise RuntimeError("external valid compile conformance failed")
    if conformance.valid_verified_rate != 1.0:
        raise RuntimeError("external solve/verify conformance failed")
    if conformance.reject_fail_closed_rate != 1.0:
        raise RuntimeError("external reject conformance failed")

    return {
        "core_distribution_version": core_distribution_version,
        "plugin_distribution_version": plugin_distribution_version,
        "plugin_id": PLUGIN_ID,
        "plugin_manifest_digest_sha256": discovered.manifest_digest_sha256,
        "parent_pid": parent_pid,
        "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
        "unapproved_adapter_blocked": unapproved_adapter_blocked,
        "worker_pids": dispatcher.worker_pids,
        "all_worker_pids_outside_parent": all(pid != parent_pid for pid in dispatcher.worker_pids),
        "first_execution_verified": first.verified,
        "execution_answer": first.answer,
        "child_launches_after_first": launches_after_first,
        "revoked_execution_verified": revoked.verified,
        "child_launches_after_revoked_attempt": launches_after_revoked_attempt,
        "post_revocation_child_launches": launches_after_revoked_attempt - launches_after_first,
        "restored_execution_verified": restored.verified,
        "total_child_launches_after_conformance": dispatcher.launch_count,
        "conformance": {
            "valid_compile_rate": conformance.valid_compile_rate,
            "valid_verified_rate": conformance.valid_verified_rate,
            "reject_fail_closed_rate": conformance.reject_fail_closed_rate,
        },
        "boundary": (
            "Plugin code executes in child Python processes and is absent from parent sys.modules. "
            "This is process separation, not an OS sandbox; child processes still inherit host-user privileges."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))