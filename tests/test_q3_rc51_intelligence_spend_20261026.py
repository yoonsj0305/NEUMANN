import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"research"/"q3"/"rc51"))
from intelligence_spend import (
    Evidence, Resource, neural_spend_gate, batch_cpu_break_even,
    resource_dominance, finite_source_nonidentifiability
)

def test_no_neural_when_classical_verified_even_under_adversarial_flags():
    for classic_budget in (False,True):
        for verifier in (False,True):
            e=Evidence(baseline_correct=True,baseline_proof=True,
                       classical_budget_limit_proven=classic_budget,
                       independent_verifier=verifier,
                       allowed_bounded_research_budget=True)
            r=neural_spend_gate(e)
            assert r["state"]=="EXECUTE_CLASSICAL"
            assert r["neural_forwards_authorized"]==0

def test_limited_dsl_exhaustion_does_not_buy_neural():
    e=Evidence(baseline_correct=False,bounded_baselines_checked=1,
               independent_verifier=True)
    r=neural_spend_gate(e)
    assert r["state"]=="HOLD_UNKNOWN"
    assert r["neural_forwards_authorized"]==0

def test_neural_can_only_be_research_admitted():
    e=Evidence(baseline_correct=False,bounded_baselines_checked=3,
               classical_budget_limit_proven=True,
               independent_verifier=True,same_rights_baseline=True,
               allowed_bounded_research_budget=True)
    r=neural_spend_gate(e)
    assert r["state"]=="NEURAL_RESEARCH_ONLY"
    assert r["global_questions_closed"]==[]

def test_historical_exact_cpu_reanalysis_not_global_success():
    r=batch_cpu_break_even(23195692,94139943,43815534,30)
    assert r["learning_and_reuse_cpu_ns"]==67011226
    assert r["conditional_future_break_even_n"]==14
    assert 1.404 < r["observed_cpu_subtotal_gain"] < 1.406
    assert not r["is_full_iso_capability_10x_pass"]

def test_missing_resource_forbids_global_comparison():
    a=Resource(task_set_sha256="A",tool_rights_sha256="R",
               verified=True,cpu_ns=100)
    b=Resource(task_set_sha256="A",tool_rights_sha256="R",
               verified=True,cpu_ns=200)
    assert resource_dominance(a,b).startswith("UNKNOWN_RESOURCE")
    assert resource_dominance(a,b,("cpu_ns",))=="PARETO_DOMINATES"
    c=Resource(task_set_sha256="B",tool_rights_sha256="R",
               verified=True,cpu_ns=200)
    assert resource_dominance(a,c,("cpu_ns",))=="NOT_COMPARABLE_TASK_RIGHTS_OR_SCOPE"

def test_unseen_input_is_underidentified_without_priors():
    assert finite_source_nonidentifiability({"a","b"},"unseen").startswith("PROVED")
