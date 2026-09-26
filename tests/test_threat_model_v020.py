from neumann1.threat_model import (
    Assurance, Asset, TrustBoundary,
    next_security_control_priority_v2, threat_model_v2,
)


def by_id():
    return {s.scenario_id: s for s in threat_model_v2()}


def test_v2_preserves_core_runtime_separation_as_explicit_control():
    scenario = by_id()["plugin.direct_core_runtime_mutation"]
    assert scenario.asset == Asset.CORE_RUNTIME_STATE
    assert scenario.boundary == TrustBoundary.CHILD_PROCESS
    assert scenario.prevent == Assurance.ENFORCED
    assert scenario.contain == Assurance.ENFORCED
    assert "out_of_process_execution" in scenario.controls
    assert scenario.evidence


def test_v2_does_not_overclaim_host_sandboxing():
    scenario = by_id()["plugin.host_capability_abuse"]
    assert scenario.asset == Asset.HOST_CAPABILITIES
    assert scenario.boundary == TrustBoundary.CHILD_PROCESS
    assert scenario.prevent == Assurance.OUT_OF_SCOPE
    assert scenario.detect == Assurance.OUT_OF_SCOPE
    assert scenario.contain == Assurance.OUT_OF_SCOPE
    assert "no os-level capability restriction" in scenario.residual_risk.lower()


def test_v2_security_priority_is_os_capability_sandbox():
    assert next_security_control_priority_v2() == "os_level_capability_sandbox"


def test_v2_scenarios_validate_and_are_unique():
    scenarios = threat_model_v2()
    ids = [s.scenario_id for s in scenarios]
    assert len(ids) == len(set(ids))
    assert len(scenarios) >= 8