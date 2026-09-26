from __future__ import annotations

import importlib.metadata as md
import json
import sys

import neumann1
from neumann1 import (
    Problem,
    RegistryEngine,
    builtin_family_registry,
    discover_installed_manifests,
    catalog_from_discovery,
    run_family_conformance,
)
from neumann1.plugin_loading import activate_python_plugin


PLUGIN_ID = "example.scalar_sum_plugin"
PLUGIN_MODULE = "example_scalar_sum.plugin"


def run():
    if PLUGIN_MODULE in sys.modules:
        raise RuntimeError("plugin module was imported before discovery began")

    core_distribution_version = md.version("neumann1")
    plugin_distribution_version = md.version("neumann-example-scalar-sum")

    report = discover_installed_manifests()
    matching = [
        item for item in report.manifests
        if item.manifest.plugin_id == PLUGIN_ID
    ]
    if len(matching) != 1:
        raise RuntimeError(
            f"expected exactly one {PLUGIN_ID} manifest, found {len(matching)}"
        )

    discovered = matching[0]
    imported_after_discovery = PLUGIN_MODULE in sys.modules
    if imported_after_discovery:
        raise RuntimeError("static discovery imported plugin code")

    catalog = catalog_from_discovery(report)
    manifest = catalog.get(PLUGIN_ID)
    if manifest is None:
        raise RuntimeError("discovered plugin missing from catalog")

    adapter = activate_python_plugin(manifest)
    imported_after_activation = PLUGIN_MODULE in sys.modules
    if not imported_after_activation:
        raise RuntimeError("explicit activation did not import plugin module")

    registry = builtin_family_registry()
    registry.register(adapter)

    engine = RegistryEngine(adapter.compiler, registry)
    result = engine.solve(Problem("sum: 2, 3, 4.5"))
    if not result.verified:
        raise RuntimeError(result.verification_reason)
    if abs(float(result.answer["sum"]) - 9.5) > 1e-12:
        raise RuntimeError("unexpected external plugin result")

    conformance = run_family_conformance(
        adapter,
        valid_texts=["sum: 1, 2", "sum: -3, 4, 10"],
        reject_texts=["sum: one, two", "find a shortest path"],
    )
    if conformance.valid_compile_rate != 1.0:
        raise RuntimeError("external valid compile conformance failed")
    if conformance.valid_verified_rate != 1.0:
        raise RuntimeError("external solve/verify conformance failed")
    if conformance.reject_fail_closed_rate != 1.0:
        raise RuntimeError("external reject conformance failed")

    return {
        "core_distribution_version": core_distribution_version,
        "plugin_distribution_version": plugin_distribution_version,
        "core_import_path": neumann1.__file__,
        "plugin_id": PLUGIN_ID,
        "plugin_distribution_name": discovered.distribution_name,
        "plugin_distribution_manifest_path": discovered.relative_path,
        "plugin_manifest_digest_sha256": discovered.manifest_digest_sha256,
        "plugin_imported_after_discovery": imported_after_discovery,
        "plugin_imported_after_activation": imported_after_activation,
        "registered_kind_ids": list(registry.kind_ids()),
        "execution_verified": result.verified,
        "execution_answer": result.answer,
        "execution_trace": result.trace,
        "conformance": {
            "valid_compile_rate": conformance.valid_compile_rate,
            "valid_verified_rate": conformance.valid_verified_rate,
            "reject_fail_closed_rate": conformance.reject_fail_closed_rate,
        },
        "boundary": (
            "Core and plugin are separate Python wheel distributions installed into "
            "a fresh venv, but their source currently lives in the same Git repository. "
            "This is cross-distribution interoperability evidence, not yet a separate-"
            "repository or independently published third-party proof."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))