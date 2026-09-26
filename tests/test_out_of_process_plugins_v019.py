import os
import sys

from neumann1 import (
    ManagedPluginRegistry,
    PluginAuthorizationLedger,
    PluginManifest,
    PLUGIN_MANIFEST_VERSION,
    Problem,
    RegistryEngine,
    builtin_family_registry,
)
from neumann1.plugin_isolation import build_out_of_process_adapter


MODULE = "neumann1.isolation_probe_plugin"


def manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "test.isolation_probe_plugin",
        "plugin_version": "0.1.0",
        "family_id": "test.isolation_probe",
        "kind": "test.isolation_probe",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "neumann1.isolation_probe_plugin:make_adapter",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })


def setup_adapter(timeout=8.0):
    sys.modules.pop(MODULE, None)
    m = manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    adapter = build_out_of_process_adapter(m, ledger, timeout_seconds=timeout)
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(m, adapter)
    engine = RegistryEngine(adapter.compiler, registry)
    return m, ledger, adapter, engine


def test_adapter_creation_does_not_import_plugin_in_core_process():
    sys.modules.pop(MODULE, None)
    m = manifest()
    ledger = PluginAuthorizationLedger()
    ledger.approve(m)
    build_out_of_process_adapter(m, ledger)
    assert MODULE not in sys.modules


def test_compile_solve_verify_execute_only_in_child_processes():
    _, _, adapter, engine = setup_adapter()
    parent_pid = os.getpid()
    result = engine.solve(Problem("probe: ok"))

    assert result.verified
    assert result.answer["pid"] != parent_pid
    assert MODULE not in sys.modules
    dispatcher = adapter.compiler.dispatcher
    assert dispatcher.launch_count == 3
    assert len(dispatcher.worker_pids) == 3
    assert all(pid != parent_pid for pid in dispatcher.worker_pids)


def test_child_environment_mutation_does_not_mutate_parent_environment():
    os.environ.pop("NEUMANN_CHILD_MUTATION", None)
    _, _, adapter, engine = setup_adapter()
    result = engine.solve(Problem("probe: mutate_env"))
    assert result.verified
    assert os.environ.get("NEUMANN_CHILD_MUTATION") is None
    assert MODULE not in sys.modules


def test_compile_timeout_fails_closed():
    _, _, adapter, engine = setup_adapter(timeout=3.0)
    result = engine.solve(Problem("probe: hang_compile"))
    assert not result.verified
    assert result.solver_name == "fallback_required"
    assert "timeout" in result.representation.rationale.lower()
    assert adapter.compiler.dispatcher.launch_count == 1


def test_compile_crash_fails_closed():
    _, _, adapter, engine = setup_adapter(timeout=8.0)
    result = engine.solve(Problem("probe: crash_compile"))
    assert not result.verified
    assert result.solver_name == "fallback_required"
    assert "exited with status" in result.representation.rationale.lower()


def test_revocation_before_next_dispatch_launches_no_child():
    m, ledger, adapter, engine = setup_adapter()
    assert engine.solve(Problem("probe: ok")).verified
    launches = adapter.compiler.dispatcher.launch_count
    ledger.revoke(m.plugin_id)

    blocked = engine.solve(Problem("probe: ok"))
    assert not blocked.verified
    assert adapter.compiler.dispatcher.launch_count == launches
    assert "revoked" in blocked.representation.rationale.lower()


def test_solver_timeout_is_engine_fail_closed():
    _, _, adapter, engine = setup_adapter(timeout=0.2)
    result = engine.solve(Problem("probe: hang_solve"))
    assert not result.verified
    assert result.solver_name == "fallback_required"
    assert "plugin process" in result.verification_reason.lower()


def test_verifier_crash_is_engine_fail_closed():
    _, _, adapter, engine = setup_adapter(timeout=1.0)
    result = engine.solve(Problem("probe: crash_verify"))
    assert not result.verified
    assert result.solver_name == "fallback_required"
    assert "plugin process" in result.verification_reason.lower()