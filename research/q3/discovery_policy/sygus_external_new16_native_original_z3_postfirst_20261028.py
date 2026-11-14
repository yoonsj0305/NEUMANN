#!/usr/bin/env python3
"""POST-FIRST NEW external SyGuS16: grade immutable real native candidates.

Native original C FIRST is never modified. Formal unbounded source correctness:
ordinary constraints via negation UNSAT; synth-inv via all three original VCs.
All 16 original paths retained, unsupported and timeout count as HOLD. Fully
separate source grammar membership from independently proved semantics.
"""
import collections,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_new16_frozen_FIRST")
OUT=pathlib.Path("external_new16_z3_postfirst")
FIRST_NAME="NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    data=(FIRST/FIRST_NAME).read_bytes()
    assert sha256(data)==FIRST_SHA
    original_first=json.loads(data)
    assert original_first["task_denominator"]==16
    assert [r["original"] for r in original_first["rows"]]==list(FIXED)
    OUT.mkdir(exist_ok=True)
    results=[]
    for row in original_first["rows"]:
        i=row["index"]
        path=row["original"]
        source=(ROOT/path).read_bytes()
        assert sha256(source)==row["source_sha256"]
        record={"index":i,"path":path,"original_source_sha256":row["source_sha256"],
                "native_first_status":row["status"],"independent_grade":"HOLD",
                "native_source_grammar_membership_independently_proved":False}
        if row["status"]=="STRONG_C_CANDIDATE_UNVERIFIED":
            candidate_bytes=(FIRST/(f"{i:02d}_cvc5.stdout")).read_bytes()
            assert sha256(candidate_bytes)==row["native_cost"]["stdout_sha256"]
            try:
                proof=independent_grade({},source.decode("utf8"),candidate_bytes.decode("utf8"))
                record["original_full_proofs"]=proof["original_formal_proof_obligations"]
                record["independent_grade"]=proof["grade"]
                record["proof_obligation_count"]=len(proof["original_formal_proof_obligations"])
                record["native_definition_names"]=proof["typed_native_return_names"]
            except Exception as ex:
                record["independent_grade"]="HOLD_ORIGINAL_CHECKER_UNSUPPORTED"
                record["checker_error"]=type(ex).__name__+":"+str(ex)[:280]
        elif row["status"]=="STRONG_C_BUDGET_HOLD":
            record["independent_grade"]="ORIGINAL_NATIVE_BUDGET_HOLD_UNCHANGED"
        elif row["status"]=="HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED":
            record["independent_grade"]="ORIGINAL_NATIVE_UNREALIZABILITY_NOT_PROVEN"
        else:
            record["independent_grade"]="ORIGINAL_NATIVE_ERROR_NOT_GRADED"
            p=(FIRST/(f"{i:02d}_cvc5.stderr")).read_text(errors="replace")
            record["native_stderr_excerpt"]=p[-550:]
        results.append(record)
        print("NEW16_ORIGINAL_SOURCE_GRADE",i,record["independent_grade"],
              record.get("proof_obligation_count"),flush=True)
    counts=dict(collections.Counter(r["independent_grade"] for r in results))
    out={"source_commit":PIN,"first_frozen_original_sha256":FIRST_SHA,
         "independent_checker_version":z3.get_version_string(),
         "native_candidates_returned":10,"original_task_denominator":16,
         "actual_independently_verified":counts.get("VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS",0),
         "counts":counts,"native_grammar_derivation_certificate":"NOT_CHECKED",
         "old_original_first_bytes_never_modified":True,
         "neural_model_trained_on_new16":False,
         "G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN",
         "rows":results}
    file=OUT/"NEW16_ORIGINAL_CVC5_NATIVE_CANDIDATES_INDEPENDENT_Z3_GRADE.json"
    file.write_text(json.dumps(out,sort_keys=True,indent=2))
    print("NEW16_POSTFIRST_RESULT_SHA256",sha256(file.read_bytes()))
    print("NEW16_POSTFIRST_COUNTS",json.dumps(counts,sort_keys=True),flush=True)
if __name__=="__main__":main()
