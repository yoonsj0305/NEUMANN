import pytest

torch=pytest.importorskip("torch")

from experiments.lp_q34_tournament_v097 import (
    CANDIDATES,
    ROUTES,
    learned_investment_per_query,
    proposal,
    protocol,
    summarize,
)
from experiments.lp_shortlist_screen_v089 import raw_source, restore_models
from neumann1.lp_model_study_archive_v088 import load_study


def test_v097_protocol_is_frozen_before_first_timing():
    p=protocol()
    assert p["cases"]==16
    assert p["warmups"]==1 and p["repeats"]==3
    assert p["order_seed"]==97991
    assert p["budget_s"]==5.0
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["amortization_queries"]==10000
    assert p["adaptive_factors"]==[1,2,4]
    assert p["new_fitting"] is False
    assert p["checkpoint_selection"] is False
    assert p["final_evaluation"] is False
    assert ROUTES[:3]==("DIRECT","ORACLE","A_DETERMINISTIC")
    assert len(CANDIDATES)==7


def test_v097_frozen_routes_have_distinct_support_authority_without_labels():
    study=load_study("docs/experiments/results/v088_completed.manifest.json")
    source=study["train_sources"][0]
    raw=raw_source(source)
    models=restore_models(study["training"])
    m,n=raw["A"].shape

    a=proposal(raw,"A_DETERMINISTIC",models)
    b=proposal(raw,"B_POINT_s87001",models)
    c=proposal(raw,"C_FULL_s87001",models)
    d=proposal(raw,"D_ADAPTIVE_s87001",models)

    assert len(a["indices"])==2*m
    assert len(b["indices"])==2*m
    assert len(c["indices"])==2*m
    assert len(d["ranking"])==n
    assert len(set(d["ranking"]))==n
    for out in (a,b,c,d):
        assert out["proposal_ms"]>=0


def test_v097_learned_investment_is_charged_and_classical_is_zero():
    study=load_study("docs/experiments/results/v088_completed.manifest.json")
    setup=study["training_setup_ms"]
    assert learned_investment_per_query(study["training"],setup,"A_DETERMINISTIC")==0
    point=learned_investment_per_query(study["training"],setup,"B_POINT_s87001")
    adaptive=learned_investment_per_query(study["training"],setup,"D_ADAPTIVE_s87001")
    full=learned_investment_per_query(study["training"],setup,"C_FULL_s87001")
    assert point>0 and full>0
    assert adaptive==point


def fake_records(candidate_post=2.0,candidate_proposal=0.1,candidate_investment=0.05):
    sources=[{"id":f"train{i}"} for i in range(16)]
    rows=[]
    for repeat in (-1,0,1,2):
        for source in sources:
            for route in ROUTES:
                if route=="DIRECT":
                    proposal_ms,post_ms,investment=0.0,10.0,0.0
                    subset=False
                elif route=="ORACLE":
                    proposal_ms,post_ms,investment=0.0,1.0,0.0
                    subset=True
                else:
                    proposal_ms,post_ms,investment=(
                        candidate_proposal,candidate_post,candidate_investment)
                    subset=True
                rows.append({
                    "case_id":source["id"],"route":route,"repeat":repeat,
                    "accepted":True,"proposal_ms":proposal_ms,"post_ms":post_ms,
                    "total_ms":proposal_ms+post_ms,
                    "amortized_investment_ms":investment,
                    "fallback_used":False,"subset_accepted":subset,
                })
    return rows,sources


def test_summary_joint_gate_can_admit_efficient_families():
    rows,sources=fake_records()
    result=summarize(rows,sources)
    assert result["decision"]=="ADMIT_FRESH_Q34_HOLDOUT"
    assert result["pareto_q34_survivors"]
    assert all(r["passed"] for r in result["routes"].values())


def test_summary_rejects_discovery_burden_including_amortized_fit():
    rows,sources=fake_records(candidate_post=2.0,candidate_proposal=1.55,candidate_investment=0.10)
    result=summarize(rows,sources)
    # Savings are 8 ms/case; discovery=1.65 ms/case => burden 0.20625.
    assert result["decision"]=="NO_FROZEN_FAMILY_Q34_CANDIDATE"
    assert not any(r["passed"] for r in result["routes"].values())
