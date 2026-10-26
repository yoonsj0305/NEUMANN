"""RC52 actual pure interface tests; complete ARC external witness in ZIP."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"rc52"))
from disagreement import audit_predictions

def test_real_historical_cell_values_scope():
    a=[[0,0,3,0,0,0,2,0,0,0,2,0,0],
       [0,3,3,3,0,2,2,2,0,2,2,2,0],
       [3,3,3,3,3,3,2,2,2,2,2,2,2]]
    b=[row[:] for row in a]
    b[1][5]=3
    x=audit_predictions({"RC50_first":a,"HINDSIGHT_second":b})
    assert x["status"]=="HOLD_SEMANTIC_AMBIGUITY"
    assert x["disagreement_cells"]==[{"row":1,"col":5,"possible_values":[2,3]}]
    assert x["candidate_identity_bits_ceiling"]==1
    assert x["confident_result"] is None
    assert x["neural_authorized"] is False
    assert x["global_questions_closed"]==[]

def test_consensus_is_only_source_consensus_not_global_proof():
    x=audit_predictions({"a":[[1]],"b":[[1]]})
    assert x["status"]=="SOURCE_CONSENSUS_ONLY"
    assert x["global_questions_closed"]==[]

def test_missing_and_malformed_fail_closed():
    assert audit_predictions({})["status"]=="HOLD_NO_SOURCE_CANDIDATES"
    for bad in ([[1,2],[3]],[[11]],[],[[True]]):
        x=audit_predictions({"bad":bad})
        assert x["status"]=="HOLD_INVALID_PREDICTIONS"

def test_conflicting_dimensions_hold():
    x=audit_predictions({"a":[[1]],"b":[[1,2]]})
    assert x["status"]=="HOLD_SHAPE_DISAGREEMENT"
