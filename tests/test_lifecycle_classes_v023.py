import pytest

from neumann1 import (
    PluginAuthorizationLedger, PluginManifest, PLUGIN_MANIFEST_VERSION,
    WorkerStateClass, build_out_of_process_adapter,
    build_persistent_out_of_process_adapter,
)


def manifest(state_class=None):
    data = {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.lifecycle_class_plugin",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    }
    if state_class is not None:
        data["worker_state_class"] = state_class
    return PluginManifest.from_dict(data)


def approved(m):
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    return ledger


@pytest.mark.parametrize("state_class", ["STATELESS", "CACHE_ONLY"])
def test_persistent_builder_accepts_reusable_classes(state_class):
    m = manifest(state_class)
    adapter = build_persistent_out_of_process_adapter(m, approved(m), timeout_seconds=8.0)
    try:
        assert adapter.compiler.dispatcher.manifest.worker_state_class == WorkerStateClass(state_class)
    finally:
        adapter.compiler.dispatcher.close()


def test_persistent_builder_rejects_undeclared_legacy_manifest():
    m = manifest()
    with pytest.raises(PermissionError, match="requires explicit worker_state_class"):
        build_persistent_out_of_process_adapter(m, approved(m))


def test_non_persistent_class_rejects_persistent_but_allows_fresh():
    m = manifest("NON_PERSISTENT")
    ledger = approved(m)
    with pytest.raises(PermissionError, match="NON_PERSISTENT"):
        build_persistent_out_of_process_adapter(m, ledger)
    adapter = build_out_of_process_adapter(m, ledger, timeout_seconds=8.0)
    assert adapter.family_id == m.family_id


def test_stateful_explicit_is_fail_closed_until_state_protocol_exists():
    m = manifest("STATEFUL_EXPLICIT")
    ledger = approved(m)
    with pytest.raises(PermissionError, match="state-transfer protocol"):
        build_persistent_out_of_process_adapter(m, ledger)
    with pytest.raises(PermissionError, match="state-transfer protocol"):
        build_out_of_process_adapter(m, ledger)


def test_legacy_undeclared_manifest_remains_fresh_process_compatible():
    m = manifest()
    adapter = build_out_of_process_adapter(m, approved(m), timeout_seconds=8.0)
    assert adapter.family_id == m.family_id


def test_state_class_is_part_of_manifest_identity_digest():
    stateless = manifest("STATELESS")
    cache_only = manifest("CACHE_ONLY")
    assert stateless.digest_sha256 != cache_only.digest_sha256
    assert stateless.canonical_dict()["worker_state_class"] == "STATELESS"


def test_invalid_state_class_is_rejected_at_manifest_parse():
    with pytest.raises(ValueError, match="unknown worker_state_class"):
        manifest("MAGIC_MEMORY")