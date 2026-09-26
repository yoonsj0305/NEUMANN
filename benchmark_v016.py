from __future__ import annotations

import json

from neumann1 import (
    FamilyAdapter,
    IRKind,
    Problem,
    Representation,
    RegistryEngine,
    VerificationResult,
    builtin_family_registry,
)
from neumann1.plugin_authorization import ManagedPluginRegistry, PluginAuthorizationLedger
from neumann1.plugin_manifest import PLUGIN_MANIFEST_VERSION, PluginManifest


KIND = "benchmark.revocable_sum"


class Compiler:
    def form(self, problem, ledger):
        ledger.representation_steps += 1
        if not problem.raw_text.startswith("sum:"):
            return Representation(IRKind.UNKNOWN, {}, 0.0, "not sum")
        values = [float(x.strip()) for x in problem.raw_text.split(":", 1)[1].split(",")]
        return Representation(KIND, {"values": values}, 1.0, "sum")


class Solver:
    name = "revocable_sum"
    def __init__(self):
        self.calls = 0
    def supports(self, rep):
        return rep.kind == KIND
    def solve(self, rep, ledger):
        self.calls += 1
        ledger.solver_steps += 1
        return {"sum": sum(rep.payload["values"])}


class Verifier:
    def verify(self, problem, rep, answer, ledger):
        ledger.verification_steps += 1
        ok = answer["sum"] == sum(rep.payload["values"])
        return VerificationResult(ok, "verified" if ok else "wrong")


def make_manifest(description="stable"):
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.revocable_sum_plugin",
        "plugin_version": "0.1.0",
        "family_id": "benchmark.revocable_sum",
        "kind": KIND,
        "family_contract_version": "neumann.family.v1",
        "entry_point": "benchmark_plugin:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
        "description": description,
    })


def run():
    manifest = make_manifest()
    changed_manifest = make_manifest("changed manifest")
    ledger = PluginAuthorizationLedger()
    ledger.approve(manifest, "benchmark approval")

    solver = Solver()
    adapter = FamilyAdapter(
        family_id=manifest.family_id,
        ir_kind=manifest.kind,
        compiler=Compiler(),
        solver=solver,
        answer_verifier=Verifier(),
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), ledger)
    registry.register_plugin(manifest, adapter)
    engine = RegistryEngine(adapter.compiler, registry)

    first = engine.solve(Problem("sum: 2, 3"))
    calls_after_first = solver.calls

    ledger.revoke(manifest.plugin_id, "benchmark revoke")
    revoked = engine.solve(Problem("sum: 2, 3"))
    calls_after_revoked_attempt = solver.calls

    changed_digest_blocked = False
    ledger.approve(manifest, "approve original again")
    try:
        ledger.require_manifest(changed_manifest)
    except PermissionError:
        changed_digest_blocked = True

    restored = engine.solve(Problem("sum: 2, 3"))

    return {
        "first_execution_verified": first.verified,
        "solver_calls_after_first": calls_after_first,
        "revoked_execution_verified": revoked.verified,
        "revoked_solver_name": revoked.solver_name,
        "solver_calls_after_revoked_attempt": calls_after_revoked_attempt,
        "post_revocation_solver_calls": calls_after_revoked_attempt - calls_after_first,
        "changed_manifest_digest_blocked": changed_digest_blocked,
        "restored_execution_verified": restored.verified,
        "ledger_events": [
            {
                "sequence": e.sequence,
                "action": e.action,
                "plugin_id": e.plugin_id,
                "digest": e.manifest_digest_sha256,
                "reason": e.reason,
            }
            for e in ledger.events()
        ],
        "boundary": (
            "The ledger is in-memory and unauthenticated. It proves use-time digest-bound "
            "authorization semantics, not durable policy storage or tamper resistance."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))