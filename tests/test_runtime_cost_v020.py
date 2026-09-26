import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.plugin_isolation import build_out_of_process_adapter
from neumann1.runtime_cost import assess_dispatch_timings


MODULE = "neumann1.isolation_probe_plugin"


def manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.runtime_cost_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })


def test_dispatch_timing_separates_total_from_child_service():
    sys.modules.pop(MODULE, None)
    m = manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = build_out_of_process_adapter(m, ledger, timeout_seconds=8.0)
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    result = RegistryEngine(adapter.compiler, registry).solve(Problem("probe: ok"))

    assert result.verified
    timings = adapter.compiler.dispatcher.dispatch_timings
    assert [row["operation"] for row in timings] == ["compile", "solve", "verify"]
    for row in timings:
        assert row["dispatch_seconds"] > 0
        assert row["service_seconds"] >= 0
        assert row["outside_service_seconds"] >= 0
        assert row["dispatch_seconds"] >= row["outside_service_seconds"]


def test_runtime_cost_gate_prefers_persistent_worker_when_lifecycle_dominates():
    rows = [
        {"dispatch_seconds": 1.0, "service_seconds": 0.1, "outside_service_seconds": 0.9},
        {"dispatch_seconds": 1.2, "service_seconds": 0.2, "outside_service_seconds": 1.0},
    ]
    assessment = assess_dispatch_timings(rows)
    assert assessment.outside_service_fraction > 0.5
    assert assessment.performance_diagnosis == "fresh_process_lifecycle_dominated"
    assert assessment.next_performance_experiment == "persistent_worker_lifecycle"


def test_runtime_cost_gate_does_not_force_worker_when_service_dominates():
    rows = [
        {"dispatch_seconds": 1.0, "service_seconds": 0.8, "outside_service_seconds": 0.2},
        {"dispatch_seconds": 1.0, "service_seconds": 0.7, "outside_service_seconds": 0.3},
    ]
    assessment = assess_dispatch_timings(rows)
    assert assessment.outside_service_fraction < 0.5
    assert assessment.next_performance_experiment == "measure_representative_workloads_before_runtime_change"