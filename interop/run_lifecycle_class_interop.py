from __future__ import annotations

import importlib.metadata as md
import json
import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, Problem, RegistryEngine,
    WorkerStateClass, builtin_family_registry, catalog_from_discovery,
    discover_installed_manifests, build_persistent_out_of_process_adapter,
)


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    sys.modules.pop(PLUGIN_MODULE, None)
    manifest = catalog_from_discovery(discover_installed_manifests()).get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("external scalar-sum manifest not discovered")
    if manifest.worker_state_class != WorkerStateClass.CACHE_ONLY:
        raise RuntimeError("external scalar-sum did not declare CACHE_ONLY")

    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest, "lifecycle-class interop approval")
    adapter = build_persistent_out_of_process_adapter(
        manifest, ledger, timeout_seconds=8.0
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)

    first = engine.solve(Problem("sum: 2, 3, 4.5"))
    second = engine.solve(Problem("sum: 10, -2, 0.5"))
    if not first.verified or first.answer["sum"] != 9.5:
        raise RuntimeError("CACHE_ONLY external plugin first execution failed")
    if not second.verified or second.answer["sum"] != 8.5:
        raise RuntimeError("CACHE_ONLY external plugin reuse failed")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("external plugin imported into parent")

    digest_with_class = manifest.digest_sha256
    raw = manifest.canonical_dict()
    del raw["worker_state_class"]
    from neumann1 import PluginManifest
    legacy_view = PluginManifest.from_dict(raw)
    if legacy_view.digest_sha256 == digest_with_class:
        raise RuntimeError("lifecycle declaration did not affect manifest identity")

    data = {
        "core_distribution_version": md.version("neumann1"),
        "plugin_distribution_version": md.version("neumann-example-scalar-sum"),
        "declared_worker_state_class": manifest.worker_state_class.value,
        "persistent_reuse_verified": first.verified and second.verified,
        "same_worker_reused": adapter.compiler.dispatcher.start_count == 1,
        "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
        "lifecycle_declaration_changes_manifest_digest": legacy_view.digest_sha256 != digest_with_class,
        "manifest_digest_sha256": digest_with_class,
        "boundary": (
            "This proves runtime enforcement and identity binding for an independently packaged test plugin. "
            "It does not prove the plugin's CACHE_ONLY declaration is truthful for all possible inputs."
        ),
    }
    adapter.compiler.dispatcher.close()
    return data


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))