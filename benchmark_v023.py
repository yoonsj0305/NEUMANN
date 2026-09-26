from __future__ import annotations

import json

from neumann1 import (
    PluginAuthorizationLedger, PluginManifest, PLUGIN_MANIFEST_VERSION,
    WorkerStateClass, build_out_of_process_adapter,
)
from neumann1.persistent_plugin_isolation import _build_unattested_persistent_adapter_for_conformance as build_persistent_out_of_process_adapter


def make_manifest(state_class=None, suffix="base"):
    data = {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": f"benchmark.lifecycle_{suffix}",
        "plugin_version": "0.1.0",
        "family_id": f"benchmark.lifecycle_{suffix}",
        "kind": f"benchmark.lifecycle_{suffix}",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    }
    # For policy-only construction tests, adapter activation is not reached when
    # the lifecycle decision rejects before child launch. Accepted cases use the
    # test isolation family below instead of these policy-only manifests.
    if state_class is not None:
        data["worker_state_class"] = state_class
    return PluginManifest.from_dict(data)


def probe_manifest(state_class, suffix):
    data = {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": f"benchmark.probe_{suffix}",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "worker_state_class": state_class,
    }
    return PluginManifest.from_dict(data)


def ledger_for(manifest):
    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest)
    return ledger


def blocked(builder, manifest):
    ledger = ledger_for(manifest)
    try:
        adapter = builder(manifest, ledger, timeout_seconds=8.0)
    except PermissionError as exc:
        return True, str(exc)
    else:
        dispatcher = getattr(adapter.compiler, "dispatcher", None)
        if dispatcher is not None and hasattr(dispatcher, "close"):
            dispatcher.close()
        return False, ""


def run():
    stateless = probe_manifest("STATELESS", "stateless")
    cache_only = probe_manifest("CACHE_ONLY", "cache")
    non_persistent = probe_manifest("NON_PERSISTENT", "fresh")
    stateful = probe_manifest("STATEFUL_EXPLICIT", "stateful")
    legacy = PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.legacy_plugin",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })

    allowed_persistent = {}
    for name, manifest in (("STATELESS", stateless), ("CACHE_ONLY", cache_only)):
        adapter = build_persistent_out_of_process_adapter(
            manifest, ledger_for(manifest), timeout_seconds=8.0
        )
        allowed_persistent[name] = (
            adapter.compiler.dispatcher.manifest.worker_state_class.value
        )
        adapter.compiler.dispatcher.close()

    nonpersistent_blocked, nonpersistent_reason = blocked(
        build_persistent_out_of_process_adapter, non_persistent
    )
    stateful_persistent_blocked, stateful_persistent_reason = blocked(
        build_persistent_out_of_process_adapter, stateful
    )
    stateful_fresh_blocked, stateful_fresh_reason = blocked(
        build_out_of_process_adapter, stateful
    )
    legacy_persistent_blocked, legacy_reason = blocked(
        build_persistent_out_of_process_adapter, legacy
    )

    fresh_nonpersistent = build_out_of_process_adapter(
        non_persistent, ledger_for(non_persistent), timeout_seconds=8.0
    )
    fresh_legacy = build_out_of_process_adapter(
        legacy, ledger_for(legacy), timeout_seconds=8.0
    )

    same_identity_cache_data = stateless.canonical_dict()
    same_identity_cache_data["worker_state_class"] = "CACHE_ONLY"
    same_identity_cache = PluginManifest.from_dict(same_identity_cache_data)
    digest_changes_with_class = (
        stateless.digest_sha256 != same_identity_cache.digest_sha256
    )

    return {
        "persistent_allowed_classes": allowed_persistent,
        "non_persistent_rejected_from_persistent": nonpersistent_blocked,
        "non_persistent_reason": nonpersistent_reason,
        "non_persistent_fresh_allowed": fresh_nonpersistent.family_id == non_persistent.family_id,
        "stateful_explicit_persistent_rejected": stateful_persistent_blocked,
        "stateful_explicit_fresh_rejected": stateful_fresh_blocked,
        "stateful_persistent_reason": stateful_persistent_reason,
        "stateful_fresh_reason": stateful_fresh_reason,
        "legacy_undeclared_persistent_rejected": legacy_persistent_blocked,
        "legacy_undeclared_reason": legacy_reason,
        "legacy_undeclared_fresh_allowed": fresh_legacy.family_id == legacy.family_id,
        "state_class_changes_manifest_digest": digest_changes_with_class,
        "supported_declared_classes": [x.value for x in WorkerStateClass],
        "decision": (
            "Persistent reuse is now an explicit privilege granted only to STATELESS and CACHE_ONLY. "
            "NON_PERSISTENT is fresh-only; STATEFUL_EXPLICIT remains fail-closed until a real state protocol exists."
        ),
        "boundary": (
            "Lifecycle declarations are policy inputs, not proof of honest plugin behavior. "
            "CACHE_ONLY/STATELESS claims still need behavioral conformance evidence."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))