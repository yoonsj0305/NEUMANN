from __future__ import annotations

import json
from statistics import median
import time

from neumann1 import (
    FamilyRegistry, ManagedPluginRegistry, PluginAuthorizationLedger,
    PluginManifest, PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine,
    builtin_family_registry,
)
from neumann1.plugin_isolation import build_out_of_process_adapter
from neumann1.runtime_cost import assess_dispatch_timings
from neumann1.isolation_probe_plugin import make_adapter as make_in_process_adapter
from neumann1.threat_model import (
    next_security_control_priority_v2, threat_model_v2,
)


def make_manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.runtime_cost_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })


def median_in_process_ms(repetitions=200):
    adapter = make_in_process_adapter()
    engine = RegistryEngine(adapter.compiler, FamilyRegistry([adapter]))
    problem = Problem("probe: ok")
    samples = []
    for _ in range(repetitions):
        start = time.perf_counter()
        result = engine.solve(problem)
        elapsed = time.perf_counter() - start
        if not result.verified:
            raise RuntimeError("in-process baseline failed")
        samples.append(elapsed * 1000.0)
    return median(samples)


def run():
    manifest = make_manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest)
    adapter = build_out_of_process_adapter(manifest, ledger, timeout_seconds=8.0)
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)
    problem = Problem("probe: ok")

    pipeline_ms = []
    for _ in range(3):
        start = time.perf_counter()
        result = engine.solve(problem)
        elapsed = time.perf_counter() - start
        if not result.verified:
            raise RuntimeError("out-of-process benchmark solve failed")
        pipeline_ms.append(elapsed * 1000.0)

    assessment = assess_dispatch_timings(adapter.compiler.dispatcher.dispatch_timings)
    in_process_ms = median_in_process_ms()
    oop_pipeline_median_ms = median(pipeline_ms)

    return {
        "dispatch_count": assessment.dispatch_count,
        "oop_pipeline_median_ms": oop_pipeline_median_ms,
        "in_process_pipeline_median_ms": in_process_ms,
        "oop_to_in_process_latency_ratio": (
            oop_pipeline_median_ms / in_process_ms if in_process_ms > 0 else None
        ),
        "total_dispatch_ms": assessment.total_dispatch_seconds * 1000.0,
        "total_child_service_ms": assessment.total_service_seconds * 1000.0,
        "total_outside_service_ms": assessment.total_outside_service_seconds * 1000.0,
        "outside_service_fraction": assessment.outside_service_fraction,
        "dispatch_to_service_ratio": assessment.dispatch_to_service_ratio,
        "median_dispatch_ms": assessment.median_dispatch_ms,
        "median_child_service_ms": assessment.median_service_ms,
        "median_outside_service_ms": assessment.median_outside_service_ms,
        "performance_diagnosis": assessment.performance_diagnosis,
        "next_performance_experiment": assessment.next_performance_experiment,
        "next_security_control_priority": next_security_control_priority_v2(),
        "threat_model_v2_scenario_count": len(threat_model_v2()),
        "decision": (
            "Performance and security now have different bottlenecks: use a persistent-worker "
            "experiment to reduce fresh-process lifecycle cost, while OS-level capability "
            "sandboxing remains the security gate before hostile plugins can be treated as contained."
        ),
        "boundary": (
            "The in-process baseline is a latency lower bound, not a security-equivalent design. "
            "Child service time starts after Python/module startup, so outside-service time is a "
            "measured lower-bound proxy for startup/import/IPC overhead. The 50% diagnosis gate is "
            "a prototype engineering heuristic, not a universal performance law."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))