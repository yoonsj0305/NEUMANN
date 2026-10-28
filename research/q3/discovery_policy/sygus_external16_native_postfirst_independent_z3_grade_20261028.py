#!/usr/bin/env python3
"""Post-FIRST independent semantic grade of 10 actual original CVC5 programs.

Consume EXACT immutable original 16 first artifact; never rerun CVC5 or alter
original authors' constraints. Ordinary source full Z3 universal proofs;
synth-inv original source full 3 verification conditions. A PBE source with
only published finite examples is proven ONLY on those original examples.
"""
import collections,json,pathlib,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_4track16_immutable_first")
OUT=pathlib.Path("external_4track16_independent_z3_grade")
def main():
    import z3
    actual=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    assert actual==PIN
    frozen=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(frozen)==FIRST_SHA, "UNEXPECTED_ORIGINAL_FIRST_RECEIPT_CHANGED"
    first=json.loads(frozen)
    assert first["task_denominator"]==16 and len(first["rows"])==16
    assert tuple(r["original"] for r in first["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    items=[]
    for row in first["rows"]:
        i=row["index"]
        source_path=row["original"]
        raw=(ROOT/source_path).read_bytes()
        assert sha256(raw)==row["source_sha256"]
        record={
            "index":i,"path":source_path,"original_sha256":row["source_sha256"],
            "native_first_status":row["status"],
            "original_feedback_contract":row.get("source_feedback_contract"),
            "independent_grade":"HOLD_OR_NOT_RUN",
        }
        if row["status"]=="STRONG_C_CANDIDATE_UNVERIFIED":
            original_stdout=(FIRST/f"{i:02d}_cvc5.stdout").read_bytes()
            assert sha256(original_stdout)==row["native_cost"]["stdout_sha256"]
            try:
                verdict=independent_grade(row,raw.decode("utf8"),
                                           original_stdout.decode("utf8","replace"))
                record["formal"]=verdict
                record["independent_grade"]=verdict["grade"]
                if record["independent_grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS":
                    if row.get("source_feedback_contract","").startswith("LISTED_PBE"):
                        record["semantic_scope"]="FINITE_LISTED_AUTHORED_PBE_EXAMPLES_ONLY"
                    elif row.get("original_invariant_constraints",0)>0:
                        record["semantic_scope"]="FULL_INDUCTIVE_INIT_CONSECUTION_POST_SAFETY"
                    else:
                        record["semantic_scope"]="ORIGINAL_UNIVERSAL_CONSTRAINTS"
                else:
                    record["semantic_scope"]="UNPROVED"
            except Exception as e:
                record["independent_grade"]="HOLD_PARSER_OR_Z3_UNSUPPORTED"
                record["error"]=type(e).__name__+":"+str(e)[:500]
        else:
            record["independent_grade"]="NATIVE_FIRST_"+row["status"]+"_UNCHANGED"
        items.append(record)
        print("EXTERNAL16_Z3_GRADE",i,record["independent_grade"],flush=True)
    counts=dict(collections.Counter(x["independent_grade"] for x in items))
    report={
        "study":"POSTFIRST_EXTERNAL_ORIGINAL16_INDEPENDENT_NATIVE_C_PROGRAM_GRADE",
        "original_source_git":PIN,"first_immutable_sha256":FIRST_SHA,
        "native_first_10_candidate_preserved":True,
        "original_16_denominator_preserved":True,
        "strict_original_source_full_semantics_checked":True,
        "PBE_scope":"Only supplied finite examples; NOT intended unseen target behavior",
        "inductive_scope":"Three actual original full inductive proof obligations",
        "grammar_membership_independently_proved":False,
        "z3_version":z3.get_version_string(),
        "grade_summary":counts,"items":items,
        "neural_ownweight_results":"NOT_RUN",
        "G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN",
    }
    p=OUT/"EXTERNAL16_FIRST_FROZEN_NATIVE_C_INDEPENDENT_ORIGINAL_Z3_GRADE.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("EXTERNAL16_Z3_GRADE_SHA256",sha256(p.read_bytes()),flush=True)
    print("EXTERNAL16_Z3_SUMMARY",json.dumps(counts,sort_keys=True),flush=True)
if __name__=="__main__":main()
