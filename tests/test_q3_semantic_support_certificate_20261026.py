import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"discovery_policy"))
from semantic_support_certificate import semantic_support_certificate as certificate

def test_character_impossibility_on_original_iso_nov_to_dec():
    source=[["2041-11-23T01:17:33Z","Nov 2041"],
            ["2023-11-11T04:17:30Z","Nov 2023"]]
    x=certificate(source,["1974-12-16T02:32:49Z","Dec 1974"])
    assert x["status"]=="PROVEN_NO_PROGRAM_IN_THIS_DSL"
    assert "D" in x["witness"][0]["missing"]
    assert x["global_questions_closed"]==[]

def test_null_totality_barrier():
    x=certificate([["Foo","F"],["A","A"]],[None,"N/A"])
    assert x["status"]=="PROVEN_NO_PROGRAM_IN_THIS_DSL"
    assert x["witness"][0]["type"]=="NULL_TOTALITY_BARRIER"

def test_unknown_does_not_authorize_or_infer_success():
    x=certificate([["18","18"],["27","27"]],["28","28"])
    assert x["status"]=="UNKNOWN"
    assert x["automatically_call_neural"] is False

def test_out_of_scope_is_unknown():
    assert certificate([[["a"],"a"],[["b"],"b"]],[["c"],"c"])["status"]=="UNKNOWN_PREMISE"
    assert certificate([["é","é"],["a","a"]],["b","B"])["status"]=="UNKNOWN_NONASCII"
