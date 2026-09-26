import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.persistent_plugin_isolation import (
    WorkerStatePolicy, _build_unattested_persistent_adapter_for_conformance as build_persistent_out_of_process_adapter,
)


MODULE = "neumann1.isolation_probe_plugin"


def manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.state_hygiene_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
    })


def setup(max_requests=None):
    sys.modules.pop(MODULE, None)
    m = manifest()
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
    engine = RegistryEngine(adapter.compiler, registry)
    return m, ledger, adapter, engine


def test_poison_fixture_persists_inside_same_generation():
    _, _, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    try:
        poisoned = engine.solve(Problem("probe: poison"))
        assert poisoned.verified
        assert poisoned.answer["poisoned"] is True
        generation = dispatcher.generation_id

        observed = engine.solve(Problem("probe: read_poison"))
        assert observed.verified
        assert observed.answer["poisoned"] is True
        assert dispatcher.generation_id == generation
    finally:
        dispatcher.close()


def test_manual_recycle_clears_hidden_plugin_state():
    _, _, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    try:
        poisoned = engine.solve(Problem("probe: poison"))
        assert poisoned.answer["poisoned"] is True
        old_generation = dispatcher.generation_id

        dispatcher.recycle("manual_state_reset")
        assert not dispatcher.is_running
        assert dispatcher.recycle_events[-1].reason == "manual_state_reset"
        assert dispatcher.recycle_events[-1].generation_id == old_generation

        observed = engine.solve(Problem("probe: read_poison"))
        assert observed.verified
        assert observed.answer["poisoned"] is False
        assert dispatcher.generation_id != old_generation
    finally:
        dispatcher.close()


def test_request_limit_recycles_before_next_pipeline_and_clears_state():
    _, _, adapter, engine = setup(max_requests=3)
    dispatcher = adapter.compiler.dispatcher
    try:
        poisoned = engine.solve(Problem("probe: poison"))
        assert poisoned.verified
        assert poisoned.answer["poisoned"] is True
        old_generation = dispatcher.generation_id
        assert dispatcher.requests_in_generation == 3

        observed = engine.solve(Problem("probe: read_poison"))
        assert observed.verified
        assert observed.answer["poisoned"] is False
        assert dispatcher.generation_id != old_generation
        assert dispatcher.start_count == 2
        assert any(e.reason == "max_requests_per_worker" for e in dispatcher.recycle_events)
    finally:
        dispatcher.close()


def test_semantics_survive_generation_change_between_every_operation():
    _, _, adapter, engine = setup(max_requests=1)
    dispatcher = adapter.compiler.dispatcher
    try:
        result = engine.solve(Problem("probe: ok"))
        assert result.verified
        assert result.answer["value"] == 42
        generations = [row["generation_id"] for row in dispatcher.dispatch_timings]
        assert len(generations) == 3
        assert len(set(generations)) == 3
        assert dispatcher.start_count == 3
    finally:
        dispatcher.close()


def test_repeated_normal_request_is_semantically_stable_across_recycle():
    _, _, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    try:
        first = engine.solve(Problem("probe: ok"))
        first_generation = dispatcher.generation_id
        dispatcher.recycle("equivalence_check")
        second = engine.solve(Problem("probe: ok"))

        assert first.verified and second.verified
        assert first.answer["value"] == second.answer["value"] == 42
        assert first.answer["mode"] == second.answer["mode"] == "ok"
        assert dispatcher.generation_id != first_generation
        assert MODULE not in sys.modules
    finally:
        dispatcher.close()


def test_state_policy_rejects_nonpositive_request_limit():
    for invalid in (0, -1):
        try:
            WorkerStatePolicy(max_requests_per_worker=invalid).validate()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid max_requests_per_worker accepted")