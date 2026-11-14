import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"discovery_policy"))
from portfolio_consensus_evidence_gate import bounded_portfolio_probe,active_policy_admission

def test_three_same_predictions_never_certify_version_space():
    # External SGI original PRE_icfp_gen_10.10: authentic bounded agreement
    # appeared at the probe input, but C0 heldout was WRONG and C1 EXACT.
    gate=bounded_portfolio_probe(["#x0000000000000000"]*3)
    assert gate["source_decision"]=="MAY_SKIP_IF_LABEL_COST_JUSTIFIES_RISK"
    assert gate["semantic_uniqueness_certificate"] is False
    assert gate["may_promote_global_Q"] is False

def test_observed_divergence_requests_authentic_label():
    gate=bounded_portfolio_probe(["#x00","#x01","#x00"])
    assert gate["source_decision"]=="REQUEST_ONE_DUE_TO_OBSERVED_DISAGREEMENT"

def test_missing_proposal_not_false_unanimity():
    gate=bounded_portfolio_probe(["#x00",None,"#x00"])
    assert gate["source_decision"]=="REQUEST_ONE_DUE_TO_MISSING_EVIDENCE"
    assert gate["completeness"]=="UNVERIFIED"

def test_real_new_original_sgi12_negative_admission():
    x=active_policy_admission(active_exact=9,strong_exact=10,
        active_cpu=92.905125,strong_cpu=17.138598,
        active_labels=6,strong_labels=12)
    assert x["status"]=="ACCURACY_AND_SOLVER_CPU_INFERIOR_LABEL_COST_TRADEOFF_UNKNOWN"
    assert x["admit_neural"] is False
    assert x["global_neumann_questions"]=="OPEN"

def test_even_scoped_win_cannot_close_global_intelligence():
    x=active_policy_admission(active_exact=11,strong_exact=10,
        active_cpu=8,strong_cpu=17,active_labels=4,strong_labels=12)
    assert x["status"]=="SCOPED_BENCHMARK_ADVANTAGE_NEEDS_COMPLETE_COST_AND_NEW_AUTHOR_TRANSFER"
    assert x["admit_neural"] is False

def test_bad_costs_hold():
    assert active_policy_admission(active_exact=-1,strong_exact=10,active_cpu=2,
        strong_cpu=1,active_labels=4,strong_labels=12)["status"]=="HOLD_INVALID_METRICS"
