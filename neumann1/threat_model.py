from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Assurance(str, Enum):
    ENFORCED = "enforced"
    DETECTED = "detected"
    PARTIAL = "partial"
    OUT_OF_SCOPE = "out_of_scope"


class ThreatActor(str, Enum):
    MALICIOUS_PUBLISHER = "malicious_plugin_publisher"
    PACKAGE_TAMPERER = "installed_package_tamperer"
    LEDGER_TAMPERER = "local_ledger_tamperer"
    HOST_ROLLBACK_ADMIN = "host_rollback_admin"
    COMPROMISED_PLUGIN = "compromised_plugin_after_activation"
    COMPROMISED_NEUMANN_PROCESS = "compromised_neumann_process"
    COMPROMISED_CHECKPOINT_AUTHORITY = "compromised_checkpoint_authority"


class Asset(str, Enum):
    EXECUTION_AUTHORITY = "execution_authority"
    MANIFEST_IDENTITY = "manifest_identity"
    AUTHORIZATION_HISTORY = "authorization_history"
    HOST_INTEGRITY = "host_integrity"
    SOLVER_RESULT_INTEGRITY = "solver_result_integrity"
    CHECKPOINT_INTEGRITY = "checkpoint_integrity"


class TrustBoundary(str, Enum):
    STATIC_DISCOVERY = "static_discovery"
    ACTIVATION = "activation"
    MANAGED_RUNTIME = "managed_runtime"
    LOCAL_LEDGER_FILE = "local_ledger_file"
    TRUSTED_HEAD = "trusted_external_head"
    PYTHON_PROCESS = "python_process"


@dataclass(frozen=True)
class ThreatScenario:
    scenario_id: str
    actor: ThreatActor
    asset: Asset
    boundary: TrustBoundary
    description: str
    prevent: Assurance
    detect: Assurance
    contain: Assurance
    recover: Assurance
    controls: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    residual_risk: str = ""

    def validate(self) -> None:
        if not self.scenario_id or "." not in self.scenario_id:
            raise ValueError("scenario_id must be namespaced")
        for value in (self.description, self.residual_risk):
            if not value.strip():
                raise ValueError(f"{self.scenario_id}: description/residual risk required")
        if any(
            level in {Assurance.ENFORCED, Assurance.DETECTED}
            for level in (self.prevent, self.detect, self.contain, self.recover)
        ) and not self.evidence:
            raise ValueError(
                f"{self.scenario_id}: strong assurance requires explicit evidence"
            )

    @property
    def has_uncontained_execution_risk(self) -> bool:
        return (
            self.asset == Asset.HOST_INTEGRITY
            and self.contain == Assurance.OUT_OF_SCOPE
        )


THREAT_MODEL_VERSION = "neumann.threat-model.v1"


def default_threat_model() -> tuple[ThreatScenario, ...]:
    scenarios = (
        ThreatScenario(
            scenario_id="plugin.unapproved_activation",
            actor=ThreatActor.MALICIOUS_PUBLISHER,
            asset=Asset.EXECUTION_AUTHORITY,
            boundary=TrustBoundary.ACTIVATION,
            description="An installed plugin attempts activation without an explicit approval for its exact manifest digest.",
            prevent=Assurance.ENFORCED,
            detect=Assurance.DETECTED,
            contain=Assurance.ENFORCED,
            recover=Assurance.ENFORCED,
            controls=("digest_bound_approval", "authorized_plugin_activator"),
            evidence=("test_unapproved_manifest_cannot_trigger_resolver_import", "fresh_venv_unapproved_activation_block"),
            residual_risk="A compromised NEUMANN process could bypass the managed activation path.",
        ),
        ThreatScenario(
            scenario_id="plugin.manifest_substitution",
            actor=ThreatActor.PACKAGE_TAMPERER,
            asset=Asset.MANIFEST_IDENTITY,
            boundary=TrustBoundary.ACTIVATION,
            description="Plugin metadata changes after approval while keeping the same logical plugin identity.",
            prevent=Assurance.ENFORCED,
            detect=Assurance.DETECTED,
            contain=Assurance.ENFORCED,
            recover=Assurance.PARTIAL,
            controls=("canonical_manifest_sha256", "digest_bound_approval"),
            evidence=("test_approval_is_bound_to_exact_manifest_digest", "benchmark_v016_changed_manifest_digest_blocked"),
            residual_risk="No publisher signature exists, so authenticity before first approval is not established.",
        ),
        ThreatScenario(
            scenario_id="ledger.record_mutation",
            actor=ThreatActor.LEDGER_TAMPERER,
            asset=Asset.AUTHORIZATION_HISTORY,
            boundary=TrustBoundary.LOCAL_LEDGER_FILE,
            description="A persisted authorization event is modified or reordered on disk.",
            prevent=Assurance.OUT_OF_SCOPE,
            detect=Assurance.DETECTED,
            contain=Assurance.ENFORCED,
            recover=Assurance.PARTIAL,
            controls=("sha256_event_chain", "reload_full_chain_verification"),
            evidence=("test_mutating_persisted_event_is_detected", "test_reordering_events_is_detected", "benchmark_v017_mutation_detected"),
            residual_risk="The file is not immutable; detection prevents trusted reload but does not restore the original bytes automatically.",
        ),
        ThreatScenario(
            scenario_id="ledger.valid_prefix_rollback",
            actor=ThreatActor.HOST_ROLLBACK_ADMIN,
            asset=Asset.AUTHORIZATION_HISTORY,
            boundary=TrustBoundary.TRUSTED_HEAD,
            description="The ledger is replaced with a complete older valid prefix to restore stale authorization state.",
            prevent=Assurance.OUT_OF_SCOPE,
            detect=Assurance.PARTIAL,
            contain=Assurance.PARTIAL,
            recover=Assurance.PARTIAL,
            controls=("trusted_expected_head"),
            evidence=("test_valid_prefix_truncation_requires_trusted_head_to_detect", "benchmark_v017_truncation_checkpoint"),
            residual_risk="Rollback is detectable only when an uncompromised external expected head is available.",
        ),
        ThreatScenario(
            scenario_id="plugin.post_activation_arbitrary_code",
            actor=ThreatActor.COMPROMISED_PLUGIN,
            asset=Asset.HOST_INTEGRITY,
            boundary=TrustBoundary.PYTHON_PROCESS,
            description="An approved or compromised plugin executes arbitrary Python inside the NEUMANN process.",
            prevent=Assurance.OUT_OF_SCOPE,
            detect=Assurance.OUT_OF_SCOPE,
            contain=Assurance.OUT_OF_SCOPE,
            recover=Assurance.PARTIAL,
            controls=("use_time_revocation",),
            evidence=("benchmark_v016_post_revocation_solver_actions_zero",),
            residual_risk="Revocation blocks future managed solver dispatch but cannot undo arbitrary side effects or prevent direct in-process actions by imported code.",
        ),
        ThreatScenario(
            scenario_id="core.process_compromise",
            actor=ThreatActor.COMPROMISED_NEUMANN_PROCESS,
            asset=Asset.EXECUTION_AUTHORITY,
            boundary=TrustBoundary.PYTHON_PROCESS,
            description="The NEUMANN process itself is compromised and bypasses registry, policy, or ledger checks.",
            prevent=Assurance.OUT_OF_SCOPE,
            detect=Assurance.OUT_OF_SCOPE,
            contain=Assurance.OUT_OF_SCOPE,
            recover=Assurance.OUT_OF_SCOPE,
            controls=(),
            evidence=(),
            residual_risk="In-process controls cannot defend against an attacker controlling the process that enforces them.",
        ),
        ThreatScenario(
            scenario_id="checkpoint.authority_compromise",
            actor=ThreatActor.COMPROMISED_CHECKPOINT_AUTHORITY,
            asset=Asset.CHECKPOINT_INTEGRITY,
            boundary=TrustBoundary.TRUSTED_HEAD,
            description="The external expected-head authority is modified together with the local ledger rollback.",
            prevent=Assurance.OUT_OF_SCOPE,
            detect=Assurance.OUT_OF_SCOPE,
            contain=Assurance.OUT_OF_SCOPE,
            recover=Assurance.OUT_OF_SCOPE,
            controls=(),
            evidence=(),
            residual_risk="v0.0.17 assumes the expected head is trusted; compromise of both ledger and checkpoint defeats rollback detection.",
        ),
    )
    for scenario in scenarios:
        scenario.validate()
    return scenarios


def assurance_counts(scenarios: Iterable[ThreatScenario] | None = None) -> dict[str, int]:
    scenarios = tuple(default_threat_model() if scenarios is None else scenarios)
    counts = {level.value: 0 for level in Assurance}
    for scenario in scenarios:
        for level in (scenario.prevent, scenario.detect, scenario.contain, scenario.recover):
            counts[level.value] += 1
    return counts


def unresolved_host_integrity_scenarios(
    scenarios: Iterable[ThreatScenario] | None = None,
) -> tuple[ThreatScenario, ...]:
    scenarios = tuple(default_threat_model() if scenarios is None else scenarios)
    return tuple(s for s in scenarios if s.has_uncontained_execution_risk)


def next_control_priority(scenarios: Iterable[ThreatScenario] | None = None) -> str:
    unresolved = unresolved_host_integrity_scenarios(scenarios)
    if unresolved:
        return "out_of_process_plugin_isolation"
    return "publisher_authenticity"