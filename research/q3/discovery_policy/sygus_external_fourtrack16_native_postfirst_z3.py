#!/usr/bin/env python3
"""POST-FIRST independent verifier of native CVC5 1.4.2 ORIGINAL 16 tasks.

Reads immutable prior FIRST archive raw stdout, SHA256 first JSON, official
third-party exact source Git. Full original Z3 semantic original constraints;
full 3-VC initialization/consecution/safety for true synth-inv tasks.
Unsupported original SLIA, first native timeout and declared infeasible are
held unchanged. NO retraining and NO resynthesizing native C outputs.
"""
import collections,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_fourtrack16_frozen_first")
OUT=pathlib.Path("external_fourtrack16_independent_z3")
NAME="NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"

def main():
    import z3
    assert subprocess.check_output(
        ["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    data=(FIRST/NAME).read_bytes()
    assert sha256(data)==FIRST_SHA, "MUTATED_ORIGINAL_FIRST"
    original=json.loads(data)
    assert original["task_denominator"]==16
    assert tuple(original["prereg_paths"])==FIXED
    assert [x["original"] for x in original["rows"]]==list(FIXED)
    OUT.mkdir(exist_ok=True)
    rows=[]
    for r in original["rows"]:
        i=r["index"]
        path=r["original"]
        raw=(ROOT/path).read_bytes()
        assert sha256(raw)==r["source_sha256"],("SOURCE_DRIFT",path)
        entry={"index":i,"original_path":path,"original_source_sha256":r["source_sha256"],
               "original_native_status":r["status"],
               "native_candidate_returned_unmodified":True,
               "independent_full_source_status":"HOLD"}
        if r["status"]=="STRONG_C_CANDIDATE_UNVERIFIED":
            stdout=(FIRST/(f"{i:02d}_cvc5.stdout")).read_bytes()
            assert sha256(stdout)==r["native_cost"]["stdout_sha256"],"MUTATED_ORIGINAL_NATIVE_OUTPUT"
            try:
                grade=independent_grade(r,raw.decode("utf8"),stdout.decode("utf8","replace"))
                entry.update(grade)
                if grade["grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS":
                    entry["independent_full_source_status"]="VALID_FULL_SOURCE_Z3_PROVED"
                else:
                    entry["independent_full_source_status"]="HOLD_COUNTEREXAMPLE_OR_UNKNOWN"
            except Exception as e:
                entry["independent_full_source_status"]="HOLD_PARSER_OR_GRADER_UNSUPPORTED"
                entry["grader_error"]=type(e).__name__+":"+str(e)[:320]
        elif r["status"]=="STRONG_C_BUDGET_HOLD":
            entry["independent_full_source_status"]="C_BUDGET_HOLD_UNCHANGED"
        elif r["status"]=="HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED":
            entry["independent_full_source_status"]="INFEASIBLE_CLAIM_UNPROVED_UNCHANGED"
        elif r["status"]=="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED":
            entry["independent_full_source_status"]="NATIVE_FORMAT_UNSUPPORTED_UNCHANGED"
        else:
            entry["independent_full_source_status"]="HOLD_NATIVE_OR_EXECUTOR_UNCHANGED"
        rows.append(entry)
        obligations=entry.get("original_formal_proof_obligations",[])
        print("EXTERNAL16_INDEPENDENT_GRADE",i,path,
              entry["independent_full_source_status"],
              "VCs",[q.get("z3_answer") for q in obligations],flush=True)
    assert len(rows)==16
    result={
       "stage":"POSTFIRST_UNMODIFIED_CVC5_142_CANDIDATES_FULL_ORIGINAL_Z3",
       "original_source_git_sha":PIN,
       "original_first_receipt_sha256":FIRST_SHA,
       "first_native_sha256_verified_for_every_candidate":True,
       "distinct_original_source_count":16,
       "actual_independent_solver":"z3 "+z3.get_version_string(),
       "source_candidate_proof_unmodified":"yes",
       "candidate_grammar_derivation_independent":"NOT_PROVED",
       "statuses":dict(collections.Counter(r["independent_full_source_status"] for r in rows)),
       "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
       "rows":rows}
    f=OUT/"G1_EXTERNAL16_ORIGINAL_CVC5_FULL_INDEPENDENT_Z3_GRADE.json"
    f.write_text(json.dumps(result,sort_keys=True,indent=2))
    print("EXTERNAL16_GRADE_SHA256",sha256(f.read_bytes()))
    print("EXTERNAL16_GRADE_SUMMARY",json.dumps(result["statuses"],sort_keys=True))
if __name__=="__main__":main()
