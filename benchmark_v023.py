from __future__ import annotations

import json
import sys

from neumann1 import (
    ManagedPluginRegistry, PluginAuthorizationLedger, PluginManifest,
    PLUGIN_MANIFEST_VERSION, Problem, RegistryEngine, builtin_family_registry,
)
from neumann1.plugin_lifecycle import (
    LifecycleMode, LifecyclePolicyError, build_declared_lifecycle_adapter,
    resolve_plugin_lifecycle,
)
from neumann1.persistent_plugin_isolation import WorkerStatePolicy


MODULE = "neumann1.isolation_probe_plugin"


def make_manifest(state_class, plugin_id):
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


def make_engine(m, state_policy=None):
    sys.modules.pop(MODULE, None)
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = build_declared_lifecycle_adapter(
        m, ledger, timeout_seconds=8.0, state_policy=state_policy
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    return adapter, RegistryEngine(adapter.compiler, registry)


def run():
    stateless = make_manifest("stateless_semantics", "benchmark.lifecycle.stateless")
    stateless_adapter, stateless_engine = make_engine(stateless)
    stateless_dispatcher = stateless_adapter.compiler.dispatcher
    s1 = stateless_engine.solve(Problem("probe: ok"))
    s2 = stateless_engine.solve(Problem("probe: ok"))
    stateless_reused = (
        s1.verified and s2.verified and stateless_dispatcher.start_count == 1
    )

    cache = make_manifest("cache_only", "benchmark.lifecycle.cache")
    cache_missing_limit_rejected = False
    try:
        resolve_plugin_lifecycle(cache)
    except LifecyclePolicyError:
        cache_missing_limit_rejected = True
    cache_adapter, cache_engine = make_engine(
        cache, WorkerStatePolicy(max_requests_per_worker=3)
    )
    cache_dispatcher = cache_adapter.compiler.dispatcher
    cache_poison = cache_engine.solve(Problem("probe: poison"))
    cache_after_recycle = cache_engine.solve(Problem("probe: read_poison"))

    explicit = make_manifest("explicit_stateful", "benchmark.lifecycle.stateful")
    explicit_resolution = resolve_plugin_lifecycle(explicit)
    explicit_rejected = False
    ledger = PluginAuthorizationLedger()
    ledger.approve(explicit)
    try:
        build_declared_lifecycle_adapter(explicit, ledger)
    except LifecyclePolicyError:
        explicit_rejected = True

    nonpersistent = make_manifest("non_persistent_only", "benchmark.lifecycle.fresh")
    nonpersistent_adapter, nonpersistent_engine = make_engine(nonpersistent)
    np_poison = nonpersistent_engine.solve(Problem("probe: poison"))
    np_observed = nonpersistent_engine.solve(Problem("probe: read_poison"))

    undeclared = make_manifest(None, "benchmark.lifecycle.legacy")
    undeclared_resolution = resolve_plugin_lifecycle(undeclared)

    keep = all([
        stateless_reused,
        cache_missing_limit_rejected,
        cache_poison.verified,
        cache_after_recycle.verified,
        cache_after_recycle.answer["poisoned"] is False,
        explicit_resolution.mode == LifecycleMode.REJECT,
        explicit_rejected,
        np_poison.answer["poisoned"] is True,
        np_observed.answer["poisoned"] is False,
        undeclared_resolution.mode == LifecycleMode.FRESH_PROCESS,
    ])

    result = {
        "stateless_mode": resolve_plugin_lifecycle(stateless).mode.value,
        "stateless_reused_one_worker": stateless_reused,
        "cache_only_missing_limit_rejected": cache_missing_limit_rejected,
        "cache_only_recycled_and_cleared_poison": cache_after_recycle.answer["poisoned"] is False,
        "cache_only_worker_starts": cache_dispatcher.start_count,
        "explicit_stateful_mode": explicit_resolution.mode.value,
        "explicit_stateful_build_rejected": explicit_rejected,
        "non_persistent_mode": resolve_plugin_lifecycle(nonpersistent).mode.value,
        "non_persistent_poison_persisted": np_observed.answer["poisoned"],
        "undeclared_mode": undeclared_resolution.mode.value,
        "keep_lifecycle_class_contract": keep,
        "claim_boundary": (
            "Lifecycle declarations drive enforceable worker-selection policy, but a declaration "
            "is still a plugin claim rather than proof that its implementation obeys the declared semantics."
        ),
    }
    stateless_dispatcher.close()
    cache_dispatcher.close()
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))