from __future__ import annotations

import json
import os
import sys

from neumann1 import (
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
    PluginManifest,
    PLUGIN_MANIFEST_VERSION,
    Problem,
    RegistryEngine,
    builtin_family_registry,
)
from neumann1.plugin_isolation import build_out_of_process_adapter


MODULE = "neumann1.isolation_probe_plugin"


def make_manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.isolation_probe_plugin",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })


def make_engine(timeout=1.0):
    sys.modules.pop(MODULE, None)
    manifest = make_manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest)
    adapter = build_out_of_process_adapter(manifest, ledger, timeout_seconds=timeout)
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    return manifest, ledger, adapter, RegistryEngine(adapter.compiler, registry)


def run():
    manifest, ledger, adapter, engine = make_engine(timeout=1.0)
    dispatcher = adapter.compiler.dispatcher
    parent_pid = os.getpid()
    imported_before = MODULE in sys.modules

    os.environ.pop("NEUMANN_CHILD_MUTATION", None)
    first = engine.solve(Problem("probe: mutate_env"))
    imported_after = MODULE in sys.modules
    env_mutated_in_parent = os.environ.get("NEUMANN_CHILD_MUTATION") is not None
    first_launches = dispatcher.launch_count

    ledger.revoke(manifest.plugin_id)
    revoked = engine.solve(Problem("probe: ok"))
    launches_after_revoked = dispatcher.launch_count

    _, _, timeout_adapter, timeout_engine = make_engine(timeout=0.2)
    compile_timeout = timeout_engine.solve(Problem("probe: hang_compile"))
    solver_timeout = timeout_engine.solve(Problem("probe: hang_solve"))

    _, _, crash_adapter, crash_engine = make_engine(timeout=1.0)
    compile_crash = crash_engine.solve(Problem("probe: crash_compile"))
    verifier_crash = crash_engine.solve(Problem("probe: crash_verify"))

    return {
        "parent_pid": parent_pid,
        "plugin_imported_in_parent_before": imported_before,
        "plugin_imported_in_parent_after": imported_after,
        "first_execution_verified": first.verified,
        "worker_pids": dispatcher.worker_pids,
        "all_worker_pids_outside_parent": all(pid != parent_pid for pid in dispatcher.worker_pids),
        "parent_environment_mutated_by_child": env_mutated_in_parent,
        "child_launches_first_execution": first_launches,
        "revoked_execution_verified": revoked.verified,
        "post_revocation_child_launches": launches_after_revoked - first_launches,
        "compile_timeout_fail_closed": not compile_timeout.verified,
        "solver_timeout_fail_closed": not solver_timeout.verified,
        "compile_crash_fail_closed": not compile_crash.verified,
        "verifier_crash_fail_closed": not verifier_crash.verified,
        "boundary": (
            "The plugin is process-separated from core Python memory and failures are killable/fail-closed. "
            "The child still runs as the same OS user and is not an OS sandbox."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))