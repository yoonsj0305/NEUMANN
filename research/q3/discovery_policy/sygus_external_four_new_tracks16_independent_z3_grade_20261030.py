#!/usr/bin/env python3
"""Post-FIRST independent source semantics, ten original cvc5 candidates.

Reads ORIGINAL frozen 16 native stdout and pinned ORIGINAL third-party SyGuS
files. Does not rerun synthesis, alter tasks, or claim a candidate returned
means correct. Ordinary constraint and inductive 3-VC from established
independent Z3 grader, with strict first JSON/source/stdout SHA checks.
"""
import collections,json,pathlib,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
FIRST=pathlib.Path("external_new16_sealed_FIRST")
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_new16_independent_postfirst")
PATH="NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    original=(FIRST/PATH).read_bytes()
    assert sha256(original)==FIRST_SHA
    first=json.loads(original)
    assert first["task_denominator"]==16
    assert tuple(x["original"] for x in first["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    rows=[]
    for src in first["rows"]:
        i=src["index"];path=src["original"]
        body=(ROOT/path).read_bytes()
        assert sha256(body)==src["source_sha256"]
        item={"index":i,"path":path,"original_native_status":src["status"],
              "source_sha256":src["source_sha256"],
              "independent_result":"HOLD"}
        if src["status"]=="STRONG_C_CANDIDATE_UNVERIFIED":
            raw=(FIRST/(f"{i:02d}_cvc5.stdout")).read_bytes()
            assert sha256(raw)==src["native_cost"]["stdout_sha256"]
            try:
                res=independent_grade(src,body.decode("utf8"),raw.decode("utf8","replace"))
                item["typed_native_return_names"]=res["typed_native_return_names"]
                item["source_original_constraint_count"]=res["source_original_constraint_count"]
                item["source_original_inv_constraint_count"]=res["source_original_inv_constraint_count"]
                item["original_formal_proof_obligations"]=res["original_formal_proof_obligations"]
                item["independent_result"]=res["grade"]
                item["grammar_membership_independently_proved"]=False
            except Exception as exc:
                item["independent_result"]="HOLD_POSTFIRST_SOURCE_PARSER_OR_Z3"
                item["error"]=type(exc).__name__+":"+str(exc)[:300]
        else:
            item["independent_result"]={
                "STRONG_C_BUDGET_HOLD":"ORIGINAL_C_BUDGET_HOLD_UNCHANGED",
                "HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED":"ORIGINAL_C_INFEASIBLE_UNPROVED",
                "HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED":"ORIGINAL_NATIVE_ERROR_UNCHANGED",
            }.get(src["status"],"ORIGINAL_NATIVE_HOLD")
        print("NEW16_SOURCE_Z3_GRADE",i,item["independent_result"],flush=True)
        rows.append(item)
    result={
      "study":"POST_FIRST_INDEPENDENT_GIVEN_PROGRAM_ORIGINAL_SEMANTIC_Z3_4_TRACKS_16",
      "original_source_repo_git":PIN,"immutable_native_first_sha256":FIRST_SHA,
      "exact_original_16_unchanged":True,
      "source_hash_checked_all_originals":True,
      "candidate_native_stdout_hash_checked":True,
      "candidate_grammar_membership_derived_from_source":False,
      "unbounded_variable_semantics":"ALL_FIRST_ORDER_FREE_STATE_TUPLES",
      "n":16,"z3_version":z3.get_version_string(),
      "classification":dict(collections.Counter(x["independent_result"] for x in rows)),
      "n_original_programs_z3_semantics_verified":sum(
         x["independent_result"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS" for x in rows),
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "rows":rows}
    p=OUT/"G1_EXTERNAL_NEW16_FROZEN_CVC5_ORIGINAL_POSTFIRST_Z3_GRADE.json"
    p.write_text(json.dumps(result,sort_keys=True,indent=2))
    print("SOURCE_GRADE_SHA256",sha256(p.read_bytes()))
    print("SOURCE_GRADE_SUMMARY",json.dumps(result["classification"],sort_keys=True))
if __name__=="__main__":main()
