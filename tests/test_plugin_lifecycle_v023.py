import sys

import pytest

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.plugin_lifecycle import (
    LifecycleMode, LifecyclePolicyError, build_declared_lifecycle_adapter,
    resolve_plugin_lifecycle,
)
from neumann1.plugin_manifest import PluginStateClass
from neumann1.persistent_plugin_isolation import WorkerStatePolicy


MODULE = "neumann1.isolation_probe_plugin"


def manifest(state_class=None, plugin_id="test.lifecycle_probe"):
    data = {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": plugin_id,
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    }
    if state_class is not None:
        data["state_class"] = state_class
    return PluginManifest.from_dict(data)


def test_legacy_manifest_canonical_digest_shape_is_unchanged_by_optional_extension():
    legacy = manifest()
    assert legacy.state_class is None
    assert "state_class" not in legacy.canonical_dict()


def test_state_declaration_is_digest_bound():
    legacy = manifest()
    declared = manifest("stateless_semantics")
    assert declared.state_class == PluginStateClass.STATELESS_SEMANTICS
    assert declared.canonical_dict()["state_class"] == "stateless_semantics"
    assert declared.digest_sha256 != legacy.digest_sha256



def test_old_approval_does_not_cover_changed_state_declaration():
    legacy = manifest()
    declared = manifest("stateless_semantics")
    ledger = PluginAuthorizationLedger()
    ledger.approve(legacy)
    ledger.require_manifest(legacy)
    with pytest.raises(PermissionError):
        ledger.require_manifest(declared)

def test_stateless_semantics_resolves_to_persistent():
    resolution = resolve_plugin_lifecycle(manifest("stateless_semantics"))
    assert resolution.mode == LifecycleMode.PERSISTENT


def test_cache_only_requires_finite_recycle_limit():
    m = manifest("cache_only")
    with pytest.raises(LifecyclePolicyError, match="finite max_requests"):
        resolve_plugin_lifecycle(m)

    resolution = resolve_plugin_lifecycle(
        m, state_policy=WorkerStatePolicy(max_requests_per_worker=9)
    )
    assert resolution.mode == LifecycleMode.PERSISTENT
    assert resolution.worker_state_policy.max_requests_per_worker == 9


def test_explicit_stateful_rejected_until_session_state_protocol_exists():
    resolution = resolve_plugin_lifecycle(manifest("explicit_stateful"))
    assert resolution.mode == LifecycleMode.REJECT
    with pytest.raises(LifecyclePolicyError, match="session/state protocol"):
        build_declared_lifecycle_adapter(
            manifest("explicit_stateful"), PluginAuthorizationLedger()
        )


def test_non_persistent_only_resolves_to_fresh_process():
    resolution = resolve_plugin_lifecycle(manifest("non_persistent_only"))
    assert resolution.mode == LifecycleMode.FRESH_PROCESS


def test_undeclared_state_fails_safe_to_fresh_process():
    resolution = resolve_plugin_lifecycle(manifest())
    assert resolution.mode == LifecycleMode.FRESH_PROCESS


def _engine_for(m, state_policy=None):
    sys.modules.pop(MODULE, None)
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = build_declared_lifecycle_adapter(
        m, ledger, timeout_seconds=8.0, state_policy=state_policy
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    return adapter, RegistryEngine(adapter.compiler, registry)


def test_stateless_declared_path_reuses_persistent_worker():
    adapter, engine = _engine_for(manifest("stateless_semantics"))
    dispatcher = adapter.compiler.dispatcher
    try:
        assert engine.solve(Problem("probe: ok")).verified
        assert engine.solve(Problem("probe: ok")).verified
        assert dispatcher.start_count == 1
        assert dispatcher.request_count == 6
        assert MODULE not in sys.modules
    finally:
        dispatcher.close()


def test_non_persistent_declared_path_does_not_retain_poison_between_solves():
    adapter, engine = _engine_for(manifest("non_persistent_only"))
    poisoned = engine.solve(Problem("probe: poison"))
    observed = engine.solve(Problem("probe: read_poison"))
    assert poisoned.verified and observed.verified
    assert poisoned.answer["poisoned"] is True
    assert observed.answer["poisoned"] is False
    assert MODULE not in sys.modules


def test_cache_only_declared_path_enforces_configured_recycling():
    adapter, engine = _engine_for(
        manifest("cache_only"),
        state_policy=WorkerStatePolicy(max_requests_per_worker=3),
    )
    dispatcher = adapter.compiler.dispatcher
    try:
        assert engine.solve(Problem("probe: poison")).answer["poisoned"] is True
        observed = engine.solve(Problem("probe: read_poison"))
        assert observed.verified
        assert observed.answer["poisoned"] is False
        assert dispatcher.start_count == 2
        assert any(e.reason == "max_requests_per_worker" for e in dispatcher.recycle_events)
    finally:
        dispatcher.close()