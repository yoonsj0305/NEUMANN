import pytest

from neumann1 import IRKind, Problem, Representation, VerificationResult
from neumann1.family_registry import FamilyAdapter
from neumann1.plugin_manifest import (
    ActivationPolicy,
    PLUGIN_MANIFEST_VERSION,
    PluginActivator,
    PluginCatalog,
    PluginManifest,
)


def manifest(capabilities=("compile", "solve", "verify", "cpu")):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "example.scalar_sum_plugin",
        "plugin_version": "0.1.0",
        "family_id": "example.scalar_sum",
        "kind": "example.scalar_sum",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "example_plugin:make_adapter",
        "capabilities": list(capabilities),
        "description": "Example external family",
    })


class C:
    def form(self, problem, ledger):
        return Representation("example.scalar_sum", {"values": [1.0, 2.0]}, 1.0, "ok")


class S:
    name = "external_sum"
    def supports(self, rep):
        return rep.kind == "example.scalar_sum"
    def solve(self, rep, ledger):
        return {"sum": sum(rep.payload["values"])}


class V:
    def verify(self, problem, rep, answer, ledger):
        return VerificationResult(answer["sum"] == 3.0, "verified")


def make_adapter():
    return FamilyAdapter(
        family_id="example.scalar_sum",
        ir_kind="example.scalar_sum",
        compiler=C(),
        solver=S(),
        answer_verifier=V(),
    )


def test_catalog_registration_does_not_resolve_or_execute_code():
    calls = []
    m = manifest()
    catalog = PluginCatalog()
    catalog.register(m)

    assert calls == []
    assert catalog.get(m.plugin_id) == m
    assert len(m.digest_sha256) == 64


def test_manifest_rejects_unnamespaced_kind_and_missing_core_capability():
    data = manifest().canonical_dict()
    data["kind"] = "scalar_sum"
    with pytest.raises(ValueError):
        PluginManifest.from_dict(data)

    data = manifest().canonical_dict()
    data["capabilities"] = ["compile", "solve"]
    with pytest.raises(ValueError):
        PluginManifest.from_dict(data)


def test_default_policy_blocks_risky_declared_capability_before_resolution():
    calls = []
    m = manifest(("compile", "solve", "verify", "network"))

    def resolver(entry):
        calls.append(entry)
        return make_adapter

    with pytest.raises(PermissionError):
        PluginActivator(resolver).activate(m)
    assert calls == []


def test_activation_is_explicit_and_adapter_must_match_manifest():
    calls = []

    def resolver(entry):
        calls.append(entry)
        assert entry == "example_plugin:make_adapter"
        return make_adapter

    m = manifest()
    adapter = PluginActivator(resolver).activate(m)

    assert calls == ["example_plugin:make_adapter"]
    assert adapter.family_id == "example.scalar_sum"
    assert adapter.canonical_kind_id == "example.scalar_sum"


def test_allowlist_can_reject_before_code_load():
    calls = []

    def resolver(entry):
        calls.append(entry)
        return make_adapter

    policy = ActivationPolicy(
        denied_capabilities=frozenset(),
        allowed_plugin_ids=frozenset({"other.plugin"}),
    )
    with pytest.raises(PermissionError):
        PluginActivator(resolver, policy).activate(manifest())
    assert calls == []
