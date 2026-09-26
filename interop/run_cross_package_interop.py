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
from neumann1.plugin_authorization import (
    AuthorizedPluginActivator,
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
)
from neumann1.plugin_loading import resolve_python_entry_point


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

    ledger = PluginAuthorizationLedger()
    resolver_calls = []

    def resolver(entry_point):
        resolver_calls.append(entry_point)
        return resolve_python_entry_point(entry_point)

    authorized_activator = AuthorizedPluginActivator(ledger, resolver)

    unapproved_blocked_before_import = False
    try:
        authorized_activator.activate(manifest)
    except PermissionError:
        unapproved_blocked_before_import = (
            PLUGIN_MODULE not in sys.modules and len(resolver_calls) == 0
        )
    if not unapproved_blocked_before_import:
        raise RuntimeError("unapproved plugin reached import/resolver boundary")

    ledger.approve(manifest, reason="cross-package CI approval")
    adapter = authorized_activator.activate(manifest)
    imported_after_activation = PLUGIN_MODULE in sys.modules
    if not imported_after_activation:
        raise RuntimeError("approved explicit activation did not import plugin module")

    managed_registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    managed_registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, managed_registry)

    import example_scalar_sum.plugin as plugin_module
    calls_before_execution = plugin_module.SOLVE_CALLS

    first = engine.solve(Problem("sum: 2, 3, 4.5"))
    if not first.verified or abs(float(first.answer["sum"]) - 9.5) > 1e-12:
        raise RuntimeError("authorized external execution failed")
    calls_after_first = plugin_module.SOLVE_CALLS

    ledger.revoke(manifest.plugin_id, reason="cross-package CI revocation")
    revoked = engine.solve(Problem("sum: 2, 3, 4.5"))
    calls_after_revoked_attempt = plugin_module.SOLVE_CALLS
    if revoked.verified:
        raise RuntimeError("revoked plugin still executed successfully")
    if calls_after_revoked_attempt != calls_after_first:
        raise RuntimeError("solver was called after revocation")

    ledger.approve(manifest, reason="cross-package CI re-approval")
    restored = engine.solve(Problem("sum: 2, 3, 4.5"))
    calls_after_restore = plugin_module.SOLVE_CALLS
    if not restored.verified:
        raise RuntimeError("re-approved plugin did not resume execution")
    if calls_after_restore != calls_after_first + 1:
        raise RuntimeError("re-approved solver call count unexpected")

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
        "unapproved_activation_blocked_before_import": unapproved_blocked_before_import,
        "plugin_imported_after_activation": imported_after_activation,
        "resolver_calls_after_authorized_activation": len(resolver_calls),
        "registered_kind_ids": list(managed_registry.kind_ids()),
        "first_execution_verified": first.verified,
        "execution_answer": first.answer,
        "solver_calls_before_execution": calls_before_execution,
        "solver_calls_after_first": calls_after_first,
        "revoked_execution_verified": revoked.verified,
        "revoked_verification_reason": revoked.verification_reason,
        "post_revocation_solver_calls": calls_after_revoked_attempt - calls_after_first,
        "restored_execution_verified": restored.verified,
        "solver_calls_after_restore": calls_after_restore,
        "authorization_events": [
            {"sequence": e.sequence, "action": e.action, "reason": e.reason}
            for e in ledger.events()
        ],
        "conformance": {
            "valid_compile_rate": conformance.valid_compile_rate,
            "valid_verified_rate": conformance.valid_verified_rate,
            "reject_fail_closed_rate": conformance.reject_fail_closed_rate,
        },
        "boundary": (
            "Authorization is an in-memory managed-runtime control. Core and plugin are "
            "separate wheels in a fresh venv, but source still lives in one Git repository. "
            "Revocation prevents managed NEUMANN execution; it does not unload imported code."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))