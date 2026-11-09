"""Source-only active hypothesis refutation unit tests.

These are algorithm unit tests, not evidence for unseen Q3/Q6 generalization.
The external original-author reference only exists in the separate evaluator.
"""
from neumann1.active_oracle_challenges import (
    choose_probes,perturb_inputs)


def test_candidate_queries_preserve_generic_numeric_and_string_interfaces():
    number=perturb_inputs(([123,8],[7,3],[11,2]),limit=320)
    assert number and all(isinstance(x,list) and len(x)>=1 for x in number)
    assert [123,123] in number or [7,7] in number
    strings=perturb_inputs(
        (["GROUPA","COMETA"],["GROUPB","COMETB"]),limit=320)
    assert ["GROUPA","GROUPA"] in strings


def test_probe_selection_does_not_use_oracle_labels_or_target_gold():
    source=(
        (["GROUPA","COMETA"],"STAY"),
        (["GROUPB","COMETB"],"STAY"))
    p=choose_probes(source,mode="active",count=4,seed=17)
    q=choose_probes(source,mode="active",count=4,seed=17)
    r=choose_probes(source,mode="random",count=4,seed=17)
    assert p.queries==q.queries
    assert p.selected_sha256==q.selected_sha256
    assert p.queries!=r.queries
    assert all(x not in [s[0] for s in source] for x in p.queries)
    assert len(p.queries)==4
    assert p.pool_count>=4


def test_different_hypotheses_change_probe_disagreement_counts():
    source=(([12,8],12),([30,2],30))
    a=choose_probes(
        source,mode="active",count=4,
        prediction_functions=(
            lambda x: x[0],
            lambda x: x[0]+x[1] if len(x)>1 else x[0]))
    assert a.disagreements>=1
    assert len(a.queries)==4
