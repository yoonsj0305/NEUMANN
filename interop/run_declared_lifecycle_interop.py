from __future__ import annotations

import importlib.metadata as md
import json
import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, Problem, RegistryEngine,
    builtin_family_registry, catalog_from_discovery, discover_installed_manifests,
)
from neumann1.plugin_lifecycle import (
    LifecycleMode, build_declared_lifecycle_adapter, resolve_plugin_lifecycle,
)


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    sys.modules.pop(PLUGIN_MODULE, None)
    manifest = catalog_from_discovery(discover_installed_manifests()).get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("external scalar-sum manifest not discovered")

    resolution = resolve_plugin_lifecycle(manifest)
    if resolution.mode != LifecycleMode.PERSISTENT:
        raise RuntimeError(f"unexpected lifecycle mode: {resolution.mode}")

    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest, "declared lifecycle interop approval")
    adapter = build_declared_lifecycle_adapter(
        manifest, ledger, timeout_seconds=8.0
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)
    dispatcher = adapter.compiler.dispatcher

    first = engine.solve(Problem("sum: 2, 3, 4.5"))
    second = engine.solve(Problem("sum: 10, -2, 0.5"))
    if not first.verified or not second.verified:
        raise RuntimeError("declared lifecycle external execution failed")
    if first.answer["sum"] != 9.5 or second.answer["sum"] != 8.5:
        raise RuntimeError("unexpected external answer")
    if dispatcher.start_count != 1 or dispatcher.request_count != 6:
        raise RuntimeError("stateless external plugin did not reuse persistent worker")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("external plugin imported into parent")

    result = {
        "core_distribution_version": md.version("neumann1"),
        "plugin_distribution_version": md.version("neumann-example-scalar-sum"),
        "manifest_state_class": manifest.state_class.value if manifest.state_class else None,
        "resolved_lifecycle_mode": resolution.mode.value,
        "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
        "first_execution_verified": first.verified,
        "second_execution_verified": second.verified,
        "persistent_worker_start_count": dispatcher.start_count,
        "persistent_plugin_request_count": dispatcher.request_count,
        "manifest_digest_sha256": manifest.digest_sha256,
        "boundary": (
            "The state declaration is digest-bound and selects runtime lifecycle behavior. "
            "It is a contract declaration, not proof that arbitrary plugin code is truly stateless."
        ),
    }
    dispatcher.close()
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))