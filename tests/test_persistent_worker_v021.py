import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.persistent_plugin_isolation import _build_unattested_persistent_adapter_for_conformance as build_persistent_out_of_process_adapter


MODULE = "neumann1.isolation_probe_plugin"


def manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.persistent_probe",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": "CACHE_ONLY",
    })


def setup(timeout=8.0):
    sys.modules.pop(MODULE, None)
    m = manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = build_persistent_out_of_process_adapter(
        m, ledger, timeout_seconds=timeout
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    engine = RegistryEngine(adapter.compiler, registry)
    return m, ledger, adapter, engine


def test_persistent_worker_reuses_one_child_for_compile_solve_verify():
    _, _, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    try:
        result = engine.solve(Problem("probe: ok"))
        assert result.verified
        assert MODULE not in sys.modules
        assert dispatcher.start_count == 1
        assert dispatcher.request_count == 3
        pids = [row["worker_pid"] for row in dispatcher.dispatch_timings]
        assert len(pids) == 3
        assert len(set(pids)) == 1
        assert dispatcher.worker_pid == pids[0]
    finally:
        dispatcher.close()


def test_second_solve_reuses_existing_worker():
    _, _, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    try:
        assert engine.solve(Problem("probe: ok")).verified
        first_pid = dispatcher.worker_pid
        assert engine.solve(Problem("probe: ok")).verified
        assert dispatcher.start_count == 1
        assert dispatcher.request_count == 6
        assert dispatcher.worker_pid == first_pid
        assert len(set(row["worker_pid"] for row in dispatcher.dispatch_timings)) == 1
    finally:
        dispatcher.close()


def test_revocation_kills_worker_without_new_plugin_request():
    m, ledger, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    assert engine.solve(Problem("probe: ok")).verified
    requests_before = dispatcher.request_count
    ledger.revoke(m.plugin_id)

    blocked = engine.solve(Problem("probe: ok"))
    assert not blocked.verified
    assert dispatcher.request_count == requests_before
    assert not dispatcher.is_running
    assert "revoked" in blocked.representation.rationale.lower()


def test_timeout_discards_worker_and_next_request_restarts_cleanly():
    _, _, adapter, engine = setup(timeout=3.0)
    dispatcher = adapter.compiler.dispatcher
    timed_out = engine.solve(Problem("probe: hang_solve"))
    assert not timed_out.verified
    assert not dispatcher.is_running
    assert dispatcher.start_count == 1

    recovered = engine.solve(Problem("probe: ok"))
    assert recovered.verified
    assert dispatcher.start_count == 2
    dispatcher.close()


def test_crash_discards_worker_and_next_request_restarts_cleanly():
    _, _, adapter, engine = setup(timeout=8.0)
    dispatcher = adapter.compiler.dispatcher
    crashed = engine.solve(Problem("probe: crash_verify"))
    assert not crashed.verified
    assert not dispatcher.is_running
    assert dispatcher.start_count == 1

    recovered = engine.solve(Problem("probe: ok"))
    assert recovered.verified
    assert dispatcher.start_count == 2
    dispatcher.close()


def test_close_is_idempotent():
    _, _, adapter, engine = setup()
    dispatcher = adapter.compiler.dispatcher
    assert engine.solve(Problem("probe: ok")).verified
    dispatcher.close()
    dispatcher.close()
    assert not dispatcher.is_running