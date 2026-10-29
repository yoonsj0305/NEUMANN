#!/usr/bin/env python3
"""Independent original PBE example semantic Z3 grading, three immutable
CVC5 1.4.2 post-first normalized grammar outputs. No resynthesis.
"""
import collections,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade
from sygus_euphony_four_two_aliases_postfirst_20261029 import normalize_one_source,MAPPING

FREEZE_SHA="f5262b793e1a77a96d6aa316e61be1531047c6b7da930c9f2008ea2ae1287fe0"
FIRST=pathlib.Path("external_euphony4_normalized_frozen")
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_euphony4_source_semantic_Z3")
DATA="G1_EUPHONY4_POSTFIRST_ALIAS_MODERN_CVC5_SOURCE_REPAIR.json"

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    raw=(FIRST/DATA).read_bytes()
    assert sha256(raw)==FREEZE_SHA,"NORMALIZED_C_FIRST_WAS_CHANGED"
    prior=json.loads(raw)
    assert len(prior["rows"])==4
    OUT.mkdir(exist_ok=True)
    graded=[]
    for r in prior["rows"]:
        i=r["index"]
        assert r["original_path"]==FIXED[i]
        original=(ROOT/r["original_path"]).read_bytes()
        assert sha256(original)==r["original_sha256"]
        result={"index":i,"original_path":r["original_path"],
                "source_original_sha256":r["original_sha256"],
                "normalized_C_first_status":r["status"],
                "original_constraint_solver":"Z3 "+z3.get_version_string(),
                "semantic_status":"HOLD"}
        old,_,_,_=normalize_one_source(original)
        data=old.decode()
        for prev,next_name in MAPPING:
            data=data.replace(prev,next_name)
        assert sha256(data.encode())==r["normalized_source_sha256"]
        if r["status"]=="C_POSTFIRST_PROGRAM_UNVERIFIED":
            source=(FIRST/(f"{i:02d}.native.stdout")).read_bytes()
            assert sha256(source)==r["native_cost"]["stdout_sha256"]
            try:
                c=independent_grade(r,original.decode("utf8"),source.decode("utf8","replace"))
                result["grade"]=c
                result["semantic_status"]=(
                    "ORIGINAL_ALL_PBE_EXAMPLES_Z3_VERIFIED"
                    if c["grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS"
                    else "HOLD_COUNTEREXAMPLE_OR_Z3_UNKNOWN"
                )
                assert c["source_original_constraint_count"]>0
            except Exception as e:
                result["semantic_status"]="HOLD_GRADER_EXCEPTION"
                result["error"]=type(e).__name__+":"+str(e)[:320]
        elif r["status"]=="C_POSTFIRST_BUDGET_HOLD":
            result["semantic_status"]="C_POSTFIRST_BUDGET_HOLD_UNCHANGED"
        else:
            result["semantic_status"]="HOLD_PREVIOUS_NATIVE_STATUS_UNCHANGED"
        graded.append(result)
        print("EUPHONY_ORIGINAL_SEMANTIC_GRADE",i,result["semantic_status"],flush=True)
    output={"stage":"POSTFIRST_C_GRAMMAR_NORMALIZED_EXACT_ORIGINAL_PBE_Z3",
       "original_source_git":PIN,
       "normalized_native_FROZEN_receipt_sha256":FREEZE_SHA,
       "source_reuses_all_original_constraints":True,
       "returned_programs_not_mutated":True,
       "original_spec_not_an_arbitrary_target_oracle":True,
       "statuses":dict(collections.Counter(x["semantic_status"] for x in graded)),
       "G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN",
       "rows":graded}
    f=OUT/"G1_EUPHONY4_POSTFIRST_NATIVE_C_ORIGINAL_Z3_FORMAL_GRADE.json"
    f.write_text(json.dumps(output,sort_keys=True,indent=2))
    print("EUPHONY_ORIGINAL_GRADE_SHA256",sha256(f.read_bytes()))
    print("EUPHONY_ORIGINAL_GRADE_SUMMARY",json.dumps(output["statuses"],sort_keys=True))
if __name__=="__main__":main()
