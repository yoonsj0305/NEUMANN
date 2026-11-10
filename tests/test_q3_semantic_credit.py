"""Q3 general observation/error-credit tests only, no target benchmarks."""
from types import SimpleNamespace
import pytest
from neumann1.q3_semantic_credit import (
    _raw_distance,source_semantic_credit,preference_from_source)


def test_typed_json_distance_is_structural_not_value_arithmetic():
    assert _raw_distance([[0,1],[1,0]],[[0,2],[1,0]])==1
    assert _raw_distance({"a":[1,2]},{"a":[1,3]})==1
    assert _raw_distance([[1]],[[1],[2]])==1
    assert _raw_distance(5,6)==_raw_distance(5,200)==1
    assert _raw_distance([1,2],[1,2])==0


def test_partial_credit_tracks_source_progress_not_invented_correctness():
    pairs=[([[1,0,0]],[[1,2,0]]),([[1,0,0]],[[1,2,2]])]
    out=SimpleNamespace(status="EXECUTED",outputs=[
        [[1,2,0]],[[1,2,0]]])
    credit=source_semantic_credit(pairs,out)
    assert credit.status=="SOURCE_PARTIAL_ONLY"
    assert credit.exact==1
    assert credit.count==2
    assert credit.gain>0
    assert credit.identity_distance>credit.candidate_distance


def test_semantic_credit_refuses_unexecuted_and_identity_only():
    c=source_semantic_credit(
        [(1,2)],SimpleNamespace(status="TIMEOUT",outputs=[]))
    assert c.status=="ABSTAIN_EXECUTION"
    c=source_semantic_credit(
        [(1,1)],SimpleNamespace(status="EXECUTED",outputs=[1]))
    assert c.status=="ABSTAIN_UNIDENTIFIABLE_IDENTITY"


def test_onpolicy_preference_never_uses_independent_source():
    from neumann1.open_program_inventor import IsolatedPython
    runner=IsolatedPython(max_seconds=8)
    source=[(2,4),(3,9)]
    improved="def transform(x):\n    return x*x"
    worse="def transform(x):\n    return x"
    pair=preference_from_source(source,runner,improved,worse)
    assert pair is not None
    assert pair["positive_program"]==improved
    assert pair["negative_program"]==worse
    assert pair["positive_credit"]["gain"]==1
    assert pair["negative_credit"]["gain"]==0
    assert pair["independent_source_certified"] is False
    assert pair["original_target_gold_read"] is False
    assert preference_from_source(source,runner,improved,improved) is None
