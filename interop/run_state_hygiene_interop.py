from __future__ import annotations

import importlib.metadata as md
import json
import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, Problem, RegistryEngine,
    builtin_family_registry, catalog_from_discovery, discover_installed_manifests,
)
from neumann1.persistent_plugin_isolation import (
    WorkerStatePolicy, _build_unattested_persistent_adapter_for_conformance as build_persistent_out_of_process_adapter,
)


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    sys.modules.pop(PLUGIN_MODULE, None)
    manifest = catalog_from_discovery(discover_installed_manifests()).get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("external scalar-sum manifest not discovered")

    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest, "state hygiene interop approval")
    adapter = build_persistent_out_of_process_adapter(
        manifest,
        ledger,
        timeout_seconds=8.0,
        state_policy=WorkerStatePolicy(max_requests_per_worker=1),
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)
    dispatcher = adapter.compiler.dispatcher

    result = engine.solve(Problem("sum: 2, 3, 4.5"))
    if not result.verified or abs(float(result.answer["sum"]) - 9.5) > 1e-12:
        raise RuntimeError("cross-generation external plugin solve failed")

    generations = [row["generation_id"] for row in dispatcher.dispatch_timings]
    if len(generations) != 3 or len(set(generations)) != 3:
        raise RuntimeError("compile/solve/verify did not use separate generations")
    if dispatcher.start_count != 3:
        raise RuntimeError("expected three worker generations")
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("external plugin imported into parent process")

    recycle_reasons = [event.reason for event in dispatcher.recycle_events]
    if recycle_reasons.count("max_requests_per_worker") < 2:
        raise RuntimeError("automatic recycle events missing")

    first_generation = generations[-1]
    dispatcher.recycle("manual_cross_package_reset")
    second = engine.solve(Problem("sum: 10, -2, 0.5"))
    if not second.verified or abs(float(second.answer["sum"]) - 8.5) > 1e-12:
        raise RuntimeError("external plugin failed after manual recycle")
    if dispatcher.generation_id == first_generation:
        raise RuntimeError("manual recycle did not create a new generation")

    result_data = {
        "core_distribution_version": md.version("neumann1"),
        "plugin_distribution_version": md.version("neumann-example-scalar-sum"),
        "plugin_module_imported_in_parent": PLUGIN_MODULE in sys.modules,
        "first_solve_verified": result.verified,
        "first_answer": result.answer,
        "compile_solve_verify_unique_generations": len(set(generations)),
        "worker_starts_first_solve": 3,
        "automatic_recycle_events": recycle_reasons.count("max_requests_per_worker"),
        "manual_recycle_recorded": any(
            e.reason == "manual_cross_package_reset" for e in dispatcher.recycle_events
        ),
        "second_solve_after_manual_recycle_verified": second.verified,
        "boundary": (
            "Cross-generation correctness proves this external family does not require hidden "
            "in-process worker state for semantics. It does not prove external filesystem/network "
            "side effects are reset by process recycling."
        ),
    }
    dispatcher.close()
    return result_data


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))