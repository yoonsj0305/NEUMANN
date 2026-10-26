"""Compact reference invariants. Full original source-only receipts in RC47 ZIP."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"rc47"))
from schema_induction import induce_schemata,bounded_instantiate,source_gate

def test_new_schema_without_target_template_named():
    source=[
       {"domain":"strings","code":["rotate_left","tail","sort"],"source_verified":True},
       {"domain":"ints","code":["rotate_left","tail","unique"],"source_verified":True},
       {"domain":"symbols","code":["rotate_left","tail","reverse"],"source_verified":True},
       {"domain":"bad","code":["rotate_left","tail","fake"],"source_verified":False},
    ]
    found=induce_schemata(source)
    assert len(found)==1 and found[0]["schema"]==["rotate_left","tail","SLOT"]
    assert found[0]["mdl_token_proxy_gain"]==3
    assert bounded_instantiate(found[0]["schema"],"rotate_right",
        {"rotate_left","tail","sort","unique","reverse","rotate_right"})==[
         "rotate_left","tail","rotate_right"]

def test_second_distinct_synthetic_schema():
    source=[{"domain":str(i),"code":["sort","init",last],"source_verified":True}
        for i,last in enumerate(["rotate_left","unique","reverse"])]
    found=induce_schemata(source)
    assert len(found)==1 and found[0]["schema"]==["sort","init","SLOT"]

def test_fail_closed_and_unknown_authority():
    assert source_gate(["reverse"],[{"input":"ab","output":"ba"}],
        lambda p,x:x[::-1])["status"]=="SOURCE_FIT_ONLY"
    assert not source_gate(["reverse"],[{"input":"ab","output":"ba"}],
        lambda p,x:x[::-1])["authorized_to_deploy"]
    assert source_gate(["reverse"],[{"input":"ab","output":"ab"}],
        lambda p,x:x[::-1])["status"]=="UNKNOWN_SOURCE_MISMATCH"
    assert source_gate([],[],lambda p,x:x)["status"]=="UNKNOWN_NO_SOURCE"
    try:
        bounded_instantiate(["SLOT","SLOT"],"reverse",{"reverse"})
    except ValueError:pass
    else:raise AssertionError("multiple slots unauthorized")
