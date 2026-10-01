import pytest

pytest.importorskip("torch")

from experiments.lp_q34_holdout_register_v098 import protocol as source_protocol, specs
from experiments.lp_q34_holdout_v098 import ROUTES, protocol, summarize


def test_v098_source_specs_are_frozen_without_generation():
    p=source_protocol()
    assert p["seed_base"]==98200
    assert p["cases"]==24
    assert p["groups"]=={"iid64":12,"size_surface_shift128":12}
    assert p["model_access"] is False
    rows=specs()
    assert len(rows)==24
    assert [r["seed"] for r in rows]==list(range(98200,98224))
    assert all(r["rows"]==64 and not r["surface"] for r in rows[:12])
    assert all(r["rows"]==128 and r["surface"] for r in rows[12:])


def test_v098_eval_protocol_freezes_survivor_and_joint_gate():
    p=protocol()
    assert p["routes"]==list(ROUTES)
    assert ROUTES==("DIRECT","ORACLE","B_POINT_s87001","B_POINT_s87002")
    assert p["new_fitting"] is False
    assert p["checkpoint_selection"] is False
    assert p["support_factor"]==2
    assert p["utility_floor"]==0.80
    assert p["discovery_burden_max"]==0.20
    assert p["amortization_queries"]==10000
    assert p["warmups"]==1 and p["repeats"]==3
    assert p["order_seed"]==98991


def fake_sources():
    rows=[]
    for i in range(24):
        rows.append({
            "id":f"fresh{i:02d}",
            "group":"iid64" if i<12 else "size_surface_shift128",
        })
    return rows


def fake_records(candidate_post=2.0,candidate_proposal=0.1,candidate_investment=0.05):
    rows=[]
    for repeat in (-1,0,1,2):
        for source in fake_sources():
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
                    "case_id":source["id"],"group":source["group"],
                    "route":route,"repeat":repeat,"accepted":True,
                    "proposal_ms":proposal_ms,"post_ms":post_ms,
                    "total_ms":proposal_ms+post_ms,
                    "amortized_investment_ms":investment,
                    "fallback_used":False,"subset_accepted":subset,
                })
    return rows


def test_v098_summary_requires_both_seeds_and_both_groups():
    result=summarize(fake_records(),fake_sources())
    assert result["decision"]=="Q34_FRESH_HOLDOUT_PASS_ADVANCE_Q5"
    assert result["advance_q5"] is True
    for route in ("B_POINT_s87001","B_POINT_s87002"):
        assert result["overall"][route]["passed"] is True
        assert all(result["groups"][route][g]["passed"] for g in result["groups"][route])


def test_v098_one_bad_group_blocks_q5():
    rows=fake_records()
    for r in rows:
        if (r["route"]=="B_POINT_s87002"
                and r["group"]=="size_surface_shift128"
                and r["repeat"]>=0):
            r["proposal_ms"]=2.0
            r["post_ms"]=9.5
            r["total_ms"]=11.5
    result=summarize(rows,fake_sources())
    assert result["decision"]=="Q34_FRESH_HOLDOUT_FAIL_NO_Q5"
    assert result["advance_q5"] is False
    assert result["groups"]["B_POINT_s87002"]["size_surface_shift128"]["passed"] is False
