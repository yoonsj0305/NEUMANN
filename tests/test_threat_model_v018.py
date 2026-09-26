from neumann1.threat_model import (
    Assurance,
    Asset,
    ThreatActor,
    default_threat_model,
    next_control_priority,
    unresolved_host_integrity_scenarios,
)


def by_id():
    return {s.scenario_id: s for s in default_threat_model()}


def test_threat_model_has_unique_namespaced_scenarios():
    scenarios = default_threat_model()
    ids = [s.scenario_id for s in scenarios]
    assert len(ids) == len(set(ids))
    assert all("." in scenario_id for scenario_id in ids)


def test_strong_assurance_claims_have_explicit_evidence():
    for scenario in default_threat_model():
        strong = any(
            level in {Assurance.ENFORCED, Assurance.DETECTED}
            for level in (scenario.prevent, scenario.detect, scenario.contain, scenario.recover)
        )
        if strong:
            assert scenario.evidence


def test_manifest_substitution_claim_matches_existing_digest_boundary():
    scenario = by_id()["plugin.manifest_substitution"]
    assert scenario.prevent == Assurance.ENFORCED
    assert scenario.detect == Assurance.DETECTED
    assert "digest_bound_approval" in scenario.controls
    assert "publisher signature" in scenario.residual_risk.lower()


def test_valid_prefix_rollback_is_not_overclaimed():
    scenario = by_id()["ledger.valid_prefix_rollback"]
    assert scenario.prevent == Assurance.OUT_OF_SCOPE
    assert scenario.detect == Assurance.PARTIAL
    assert "external expected head" in scenario.residual_risk.lower()


def test_compromised_plugin_is_explicitly_uncontained():
    scenario = by_id()["plugin.post_activation_arbitrary_code"]
    assert scenario.actor == ThreatActor.COMPROMISED_PLUGIN
    assert scenario.asset == Asset.HOST_INTEGRITY
    assert scenario.contain == Assurance.OUT_OF_SCOPE
    assert "cannot undo arbitrary side effects" in scenario.residual_risk.lower()


def test_compromised_core_process_is_not_claimed_defended():
    scenario = by_id()["core.process_compromise"]
    assert scenario.prevent == Assurance.OUT_OF_SCOPE
    assert scenario.detect == Assurance.OUT_OF_SCOPE
    assert scenario.contain == Assurance.OUT_OF_SCOPE
    assert scenario.recover == Assurance.OUT_OF_SCOPE


def test_model_points_to_process_isolation_before_more_identity_crypto():
    unresolved = unresolved_host_integrity_scenarios()
    assert any(s.scenario_id == "plugin.post_activation_arbitrary_code" for s in unresolved)
    assert next_control_priority() == "out_of_process_plugin_isolation"