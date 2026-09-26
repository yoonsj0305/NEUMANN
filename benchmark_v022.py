from __future__ import annotations

import json
from statistics import median
import time

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.persistent_plugin_isolation import (
    WorkerStatePolicy, build_persistent_out_of_process_adapter,
)


def make_manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.state_hygiene_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
    })


def make_engine(max_requests=None):
    m = make_manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = build_persistent_out_of_process_adapter(
        m,
        ledger,
        timeout_seconds=8.0,
        state_policy=WorkerStatePolicy(max_requests_per_worker=max_requests),
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    return m, ledger, adapter, RegistryEngine(adapter.compiler, registry)


def timed_solve(engine, text):
    start = time.perf_counter()
    result = engine.solve(Problem(text))
    return result, (time.perf_counter() - start) * 1000.0


def run():
    _, _, adapter, engine = make_engine()
    dispatcher = adapter.compiler.dispatcher

    poisoned, _ = timed_solve(engine, "probe: poison")
    same_generation, same_ms = timed_solve(engine, "probe: read_poison")
    generation_before_reset = dispatcher.generation_id

    dispatcher.recycle("benchmark_state_reset")
    reset_observation, reset_ms = timed_solve(engine, "probe: read_poison")
    generation_after_reset = dispatcher.generation_id

    clean_samples = []
    for _ in range(5):
        result, elapsed = timed_solve(engine, "probe: ok")
        if not result.verified:
            raise RuntimeError("state hygiene benchmark solve failed")
        clean_samples.append(elapsed)

    # Strong semantic-independence probe: every compile/solve/verify operation
    # gets a different worker generation.
    _, _, strict_adapter, strict_engine = make_engine(max_requests=1)
    strict_result, strict_ms = timed_solve(strict_engine, "probe: ok")
    strict_dispatcher = strict_adapter.compiler.dispatcher
    strict_generations = [row["generation_id"] for row in strict_dispatcher.dispatch_timings]

    keep = (
        poisoned.verified
        and same_generation.answer["poisoned"] is True
        and reset_observation.answer["poisoned"] is False
        and generation_before_reset != generation_after_reset
        and strict_result.verified
        and len(set(strict_generations)) == 3
    )

    result = {
        "poison_visible_same_generation": same_generation.answer["poisoned"],
        "poison_visible_after_recycle": reset_observation.answer["poisoned"],
        "generation_changed_after_recycle": generation_before_reset != generation_after_reset,
        "manual_recycle_events": [
            {
                "reason": e.reason,
                "generation_id": e.generation_id,
                "requests_in_generation": e.requests_in_generation,
            }
            for e in dispatcher.recycle_events
        ],
        "warm_same_generation_pipeline_ms": same_ms,
        "post_recycle_cold_pipeline_ms": reset_ms,
        "warm_clean_pipeline_median_ms": median(clean_samples),
        "strict_cross_generation_pipeline_ms": strict_ms,
        "strict_cross_generation_worker_starts": strict_dispatcher.start_count,
        "strict_cross_generation_unique_generations": len(set(strict_generations)),
        "semantic_result_across_three_generations_verified": strict_result.verified,
        "keep_state_hygiene_contract": keep,
        "claim_boundary": (
            "Process recycle demonstrably clears this test plugin's in-memory global state. "
            "It does not prove that every external side effect is reset; files, network state, "
            "remote services, and other host resources remain outside this state-hygiene contract."
        ),
    }
    dispatcher.close()
    strict_dispatcher.close()
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))