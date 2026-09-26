from __future__ import annotations

import importlib.metadata as md
import json
import sys

from neumann1 import (
    LifecycleAttestationRegistry, LifecycleConformanceCase,
    ManagedPluginRegistry, PluginAuthorizationLedger, Problem, RegistryEngine,
    builtin_family_registry, build_persistent_out_of_process_adapter,
    catalog_from_discovery, discover_installed_manifests,
    run_lifecycle_conformance_attestation,
)


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    sys.modules.pop(PLUGIN_MODULE, None)
    manifest = catalog_from_discovery(discover_installed_manifests()).get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("external scalar-sum manifest not discovered")

    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest, "fresh-venv lifecycle attestation")

    missing_attestation_blocked = False
    try:
        build_persistent_out_of_process_adapter(manifest, ledger)
    except PermissionError:
        missing_attestation_blocked = True
    if not missing_attestation_blocked:
        raise RuntimeError("persistent external plugin started without attestation")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("attestation gate imported plugin into parent")

    cases = (
        LifecycleConformanceCase("sum_a", "sum: 1, 2", {"sum": 3.0}),
        LifecycleConformanceCase("sum_b", "sum: -3, 4, 10", {"sum": 11.0}),
        LifecycleConformanceCase("sum_c", "sum: 2.5, 0.5, -1", {"sum": 2.0}),
    )
    attestation = run_lifecycle_conformance_attestation(
        manifest, ledger, cases, warm_repetitions=2, timeout_seconds=8.0
    )
    if attestation.status.value != "PASS" or attestation.semantic_equivalence_rate != 1.0:
        raise RuntimeError("external lifecycle conformance attestation did not pass")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("conformance attestation imported plugin into parent")

    attestation_registry = LifecycleAttestationRegistry([attestation])
    adapter = build_persistent_out_of_process_adapter(
        manifest,
        ledger,
        attestation_registry=attestation_registry,
        timeout_seconds=8.0,
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)

    first = engine.solve(Problem("sum: 2, 3, 4.5"))
    second = engine.solve(Problem("sum: 10, -2, 0.5"))
    if not first.verified or first.answer["sum"] != 9.5:
        raise RuntimeError("attested persistent external first execution failed")
    if not second.verified or second.answer["sum"] != 8.5:
        raise RuntimeError("attested persistent external reuse failed")
    if adapter.compiler.dispatcher.start_count != 1:
        raise RuntimeError("attested external plugin did not reuse worker")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("attested external plugin imported into parent")

    data = {
        "core_distribution_version": md.version("neumann1"),
        "plugin_distribution_version": md.version("neumann-example-scalar-sum"),
        "manifest_digest_sha256": manifest.digest_sha256,
        "attestation_digest_sha256": attestation.digest_sha256,
        "attestation_status": attestation.status.value,
        "attestation_case_count": attestation.case_count,
        "attestation_warm_repetitions": attestation.warm_repetitions,
        "semantic_equivalence_rate": attestation.semantic_equivalence_rate,
        "warm_passed": attestation.warm_passed,
        "recycled_passed": attestation.recycled_passed,
        "cross_generation_passed": attestation.cross_generation_passed,
        "missing_attestation_blocked": missing_attestation_blocked,
        "persistent_execution_after_attestation_verified": first.verified and second.verified,
        "same_worker_reused_after_attestation": adapter.compiler.dispatcher.start_count == 1,
        "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
        "boundary": (
            "The attestation is exact-artifact evidence over three explicit scalar-sum cases. "
            "It is not proof for all inputs and the attestation registry is in-memory in v0.0.24."
        ),
    }
    adapter.compiler.dispatcher.close()
    return data


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))