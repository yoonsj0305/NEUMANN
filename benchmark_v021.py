from __future__ import annotations

import json
from statistics import median
import time

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.plugin_isolation import build_out_of_process_adapter
from neumann1.persistent_plugin_isolation import build_persistent_out_of_process_adapter


def make_manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.persistent_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })


def make_engine(builder, timeout=8.0):
    m = make_manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = builder(m, ledger, timeout_seconds=timeout)
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    return m, ledger, adapter, RegistryEngine(adapter.compiler, registry)


def time_solves(engine, count):
    samples = []
    for _ in range(count):
        start = time.perf_counter()
        result = engine.solve(Problem("probe: ok"))
        elapsed = (time.perf_counter() - start) * 1000.0
        if not result.verified:
            raise RuntimeError("benchmark solve failed")
        samples.append(elapsed)
    return samples


def run():
    _, _, fresh_adapter, fresh_engine = make_engine(build_out_of_process_adapter)
    fresh_samples = time_solves(fresh_engine, 3)

    m, ledger, persistent_adapter, persistent_engine = make_engine(
        build_persistent_out_of_process_adapter
    )
    dispatcher = persistent_adapter.compiler.dispatcher
    persistent_samples = time_solves(persistent_engine, 6)
    cold_ms = persistent_samples[0]
    warm_samples = persistent_samples[1:]
    warm_median_ms = median(warm_samples)
    fresh_median_ms = median(fresh_samples)
    warm_speedup = fresh_median_ms / warm_median_ms

    requests_before_revoke = dispatcher.request_count
    ledger.revoke(m.plugin_id)
    revoked = persistent_engine.solve(Problem("probe: ok"))
    requests_after_revoke = dispatcher.request_count
    worker_running_after_revoke = dispatcher.is_running

    keep = (
        warm_median_ms <= fresh_median_ms * 0.25
        and not revoked.verified
        and requests_after_revoke == requests_before_revoke
        and not worker_running_after_revoke
    )

    return {
        "fresh_process_pipeline_median_ms": fresh_median_ms,
        "persistent_worker_cold_pipeline_ms": cold_ms,
        "persistent_worker_warm_pipeline_median_ms": warm_median_ms,
        "persistent_warm_speedup_vs_fresh": warm_speedup,
        "persistent_worker_start_count": dispatcher.start_count,
        "persistent_worker_startup_ms": [x * 1000.0 for x in dispatcher.startup_timings],
        "persistent_request_count_before_revoke": requests_before_revoke,
        "post_revocation_requests": requests_after_revoke - requests_before_revoke,
        "worker_running_after_revoke": worker_running_after_revoke,
        "revoked_execution_verified": revoked.verified,
        "parent_import_claim": "covered by unit tests; isolated plugin remains absent from parent sys.modules",
        "pre_registered_keep_gate": (
            "warm persistent median <= 25% of fresh-process median, revoke verified false, "
            "post-revocation requests = 0, worker terminated"
        ),
        "keep_persistent_worker_experiment": keep,
        "security_boundary": (
            "Persistent reuse is a performance optimization. It does not add OS-level sandboxing, "
            "and it retains plugin process/global state across requests until worker restart."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))