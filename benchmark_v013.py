from __future__ import annotations
import json

from neumann1 import Representation, VerificationResult
from neumann1.family_registry import FamilyAdapter
from neumann1.plugin_manifest import (
    PLUGIN_MANIFEST_VERSION,
    PluginActivator,
    PluginCatalog,
    PluginManifest,
)


class Compiler:
    def form(self, problem, ledger):
        return Representation("example.scalar_sum", {"values":[2.0,3.0]}, 1.0, "demo")


class Solver:
    name = "sum"
    def supports(self, rep):
        return rep.kind == "example.scalar_sum"
    def solve(self, rep, ledger):
        return {"sum": sum(rep.payload["values"])}


class Verifier:
    def verify(self, problem, rep, answer, ledger):
        return VerificationResult(answer["sum"] == 5.0, "verified")


def factory():
    return FamilyAdapter(
        family_id="example.scalar_sum",
        ir_kind="example.scalar_sum",
        compiler=Compiler(),
        solver=Solver(),
        answer_verifier=Verifier(),
    )


def run():
    manifest = PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "example.scalar_sum_plugin",
        "plugin_version": "0.1.0",
        "family_id": "example.scalar_sum",
        "kind": "example.scalar_sum",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "example_plugin:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })

    load_calls = []

    def resolver(entry_point):
        load_calls.append(entry_point)
        return factory

    catalog = PluginCatalog()
    catalog.register(manifest)
    calls_after_discovery = len(load_calls)

    activator = PluginActivator(resolver)
    adapter = activator.activate(manifest)
    calls_after_activation = len(load_calls)

    risky = PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "example.risky_plugin",
        "plugin_version": "0.1.0",
        "family_id": "example.risky_family",
        "kind": "example.risky_family",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "risky_plugin:factory",
        "capabilities": ["compile", "solve", "verify", "network"],
    })

    risky_blocked_before_load = False
    before_risky = len(load_calls)
    try:
        activator.activate(risky)
    except PermissionError:
        risky_blocked_before_load = len(load_calls) == before_risky

    return {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "catalog_count": len(catalog.manifests()),
        "load_calls_after_discovery": calls_after_discovery,
        "load_calls_after_explicit_activation": calls_after_activation,
        "activated_family_id": adapter.family_id,
        "manifest_digest_sha256": manifest.digest_sha256,
        "risky_capability_blocked_before_code_load": risky_blocked_before_load,
        "boundary": (
            "Manifest validation and pre-import policy are metadata controls only. "
            "They do not provide sandboxing, signature authenticity, or dependency isolation."
        ),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
    with open("benchmark_v013_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
