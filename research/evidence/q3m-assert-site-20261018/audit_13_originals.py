"""Q3M historical 13 first-source-proofs fail-closed original C annotation-site audit.

All historical original source file identities remain frozen, all source bodies
read directly from the exact Microsoft Loopy git-blob pinned ZIP.
Zero learned model calls; no Q3F competition benchmark task opened.
"""
from __future__ import annotations
import argparse,hashlib,io,json,sys,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
sys.path.insert(0,str(HERE.parent/"q3k-chc-spacer-20261018"))
sys.path.insert(0,str(HERE.parent/"q3j-polynomial-20261018"))
from original_assert_site import (
    require_original_after_loop_assertion,OriginalAssertionSiteError
)
from replay_real_c_loop_invariants import verify
from source_only_houdini import candidate_proof
from first_source_only_direct_chc import model_semantics,source_fixedpoint,controls
from composed_original_c_certificate import run as compose

BLOB_SHA1="17cac0f6734a39f0fe73558199cc2ad8d5c1a810"
HISTORY={
 "q3i":"cd195fb214e79d1eda9657faa59ac266c4b77969a1ce22dd1eeaa434baec235c",
 "q3k2":"2e17cab004d0057f4418603ae8fa3b4be32c29ff96fd04a0ffcce74dad5af9fd",
 "q3l":"d320796af54efc5fa44f1f5972d34e078e9ac5ef68742508dcfe9d8ae6c53b6c",
}
EXPECTED_CLASSICAL_COUNTS={"q3i":9,"q3k2":1,"q3l":3}

def contents(path,expected):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("PREVIOUS_FIRST_RECEIPT_CHANGED")
    return json.loads(raw)

def classify(original):
    try:
        return {"status":"SOURCE_ASSERTION_SITE_ADMITTED",
                **require_original_after_loop_assertion(original)}
    except Exception as e:
        return {"status":"SOURCE_ASSERTION_SITE_REJECTED",
                "cause":f"{type(e).__name__}: {str(e)[:180]}"}

def controls_test():
    code=lambda ann: "int main(void){\n  int x = 1;\n"+ann
    cases={
      "false_before_loop":code("  //@ assert (x==0);\n  while(x>0){x--;}\n  return 0;\n}\n"),
      "correct_after_loop":code("  while(x>0){x--;}\n  //@ assert (x==0);\n  return 0;\n}\n"),
      "inside_loop":code("  while(x>0){\n    //@ assert (x==0);\n    x--;\n  }\n  return 0;\n}\n"),
      "after_return":code("  while(x>0){x--;}\n  return 0;\n  //@ assert (x==0);\n}\n"),
      "correct_inert_compound_after_loop":code("  while(x>0){x--;}\n  {\n    ;\n    //@ assert (x==0);\n  }\n  return 0;\n}\n"),
      "wrong_effectful_compound_after_loop":code("  while(x>0){x--;}\n  {\n    x++;\n    //@ assert (x==0);\n  }\n  return 0;\n}\n"),
      "wrong_conditional_compound_after_loop":code("  while(x>0){x--;}\n  if(x != 0){\n    //@ assert (x==0);\n  }\n  return 0;\n}\n"),
    }
    result={}
    for key,src in cases.items():
        site=classify(src)
        accepted=site["status"]=="SOURCE_ASSERTION_SITE_ADMITTED"
        expected=key in ("correct_after_loop","correct_inert_compound_after_loop")
        result[key]={"site_accepted":accepted,"expected":expected,
                     "correct_rejection_or_admission":accepted==expected,
                     "status":site}
    # The valid postloop control must still actually prove its original
    # annotated assertion with the existing unchanged C induction logic.
    for key in ("correct_after_loop","correct_inert_compound_after_loop"):
        correct=verify(cases[key],"x>=0")
        result[key]["original_C_full_proof_replayed"]=correct["status"]=="ALL_ORIGINAL_LOOP_OBLIGATIONS_UNSAT"
        result[key]["correct_rejection_or_admission"] &=result[key]["original_C_full_proof_replayed"]
    return result

def run(dataset,historical):
    prior={k:contents(historical[k],v) for k,v in HISTORY.items()}
    prior_q3i=prior["q3i"]
    nine=[r for r in prior_q3i["first_originals"] if r["proof"]["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED"]
    one=prior["q3k2"]
    three=[r for r in prior["q3l"]["cases"]
           if r["status"]=="CLASSICAL_SPECIALISTS_COMPOSED_ORIGINAL_C_PROVEN"]
    if [len(nine),int(one["status"]=="ONE_AUTHENTIC_ORIGINAL_C_SAFETY_PROVEN_BY_CLASSICAL_COMPOSITION"),len(three)] != [9,1,3]:
        raise ValueError("HISTORICAL_PROOF_COUNTS_CHANGED")
    registry=[]
    for r in nine: registry.append(("q3i",r["source_path"],r["source_sha256"]))
    registry.append(("q3k2",one["exact_original_path"],one["exact_original_sha256"]))
    for r in three:registry.append(("q3l",r["source_path"],r["source_sha256"]))
    if len(registry)!=13 or len({k for _,k,_ in registry})!=13:
        raise ValueError("REPEAT_OR_MISSING_HISTORICAL_PROVEN_ORIGINAL")
    source=dataset.read_bytes()
    git_blob=b"blob "+str(len(source)).encode()+b"\x00"+source
    if hashlib.sha1(git_blob).hexdigest()!=BLOB_SHA1:
        raise ValueError("THIRD_PARTY_ORIGINAL_SOURCE_ARCHIVE_CHANGED")
    adversarial=controls_test()
    if not all(v["correct_rejection_or_admission"] for v in adversarial.values()):
        raise ValueError("ADVERSARIAL_SOURCE_ANNOTATION_GUARD_FAILED")
    if not all(v["pass"] for v in controls().values()):
        raise ValueError("EXISTING_SAFE_UNSAFE_OVERFLOW_CONTROLS_REGRESSED")
    outcome=[]
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        for group,path,sha in registry:
            raw=z.read(path)
            if hashlib.sha256(raw).hexdigest()!=sha:
                raise ValueError("HISTORICAL_AUTHENTIC_SOURCE_HASH_CHANGED")
            site=classify(raw.decode("utf-8",errors="strict"))
            result={
                "study":group,"original_path":path,"original_sha256":sha,
                "annotation_site":site,
                "original_source_modified":False,
                "reproof_status":"NO_REPROOF_IF_ANNOTATION_INVALID",
            }
            if site["status"]=="SOURCE_ASSERTION_SITE_ADMITTED":
                source_text=raw.decode("utf-8")
                try:
                    if group=="q3i":
                        proof=candidate_proof(source_text)
                        result["reproof_status"]=proof["status"]
                        result["original_proof_checks"]=proof.get("full_original_check")
                    elif group=="q3l":
                        model,names,base,prestatus,arith=model_semantics(source_text)
                        fp=source_fixedpoint(model,names,base,arith,timeout_ms=3500)
                        good=prestatus=="unsat" and all(
                           fp[x]["bad_state_query"]=="unsat"
                           for x in ("exit_safety","signed_step_overflow"))
                        result["reproof_status"]="FULL_SPACER_ORIGINAL_PROVEN" if good else "NO_REPROOF"
                        result["original_proof_checks"]={
                           "prelude":prestatus,
                           "exit":fp["exit_safety"]["bad_state_query"],
                           "overflow":fp["signed_step_overflow"]["bad_state_query"]
                        }
                    else:
                        # Original Q3J algorithm and original CHC are executed
                        # independently, and composing still requires every gate.
                        result["reproof_status"]="COMPOSITION_REPROOF_PENDING_SEPARATE_JOB"
                except Exception as ex:
                    result["reproof_status"]="UNPROVEN_OR_ENGINEERING_ERROR"
                    result["error"]=f"{type(ex).__name__}: {str(ex)[:180]}"
            outcome.append(result)
    # Separate full Q3K-2 reuse of the exact upstream ZIP, only after all
    # three original category location checks have been evaluated.
    for r in outcome:
        if r["study"]=="q3k2" and r["annotation_site"]["status"]=="SOURCE_ASSERTION_SITE_ADMITTED":
            try:
                composed=compose(dataset)
                r["reproof_status"]=composed["status"]
                r["composition_obligations"]=composed.get("composition_lemma_contract")
            except Exception as ex:
                r["reproof_status"]="UNPROVEN_OR_COMPOSITION_ERROR"
                r["error"]=f"{type(ex).__name__}: {str(ex)[:180]}"
    passed=lambda r:(r["study"]=="q3i" and r["reproof_status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED" or
                     r["study"]=="q3l" and r["reproof_status"]=="FULL_SPACER_ORIGINAL_PROVEN" or
                     r["study"]=="q3k2" and r["reproof_status"]=="ONE_AUTHENTIC_ORIGINAL_C_SAFETY_PROVEN_BY_CLASSICAL_COMPOSITION")
    reproof=[r for r in outcome if passed(r)]
    return {
      "status":"ANNOTATION_SITE_AND_ORIGINAL_PROOF_AUDIT_COMPLETE",
      "historical_13_exact_originals":13,
      "original_C_strict_assert_site_admitted":sum(r["annotation_site"]["status"]=="SOURCE_ASSERTION_SITE_ADMITTED" for r in outcome),
      "historical_full_original_certificates_reverified_with_site_gate":len(reproof),
      "disallowed_pre_loop_or_nontop_level_original_claims":sum(r["annotation_site"]["status"]!="SOURCE_ASSERTION_SITE_ADMITTED" for r in outcome),
      "adversarial_controls":adversarial,
      "global_q1_q7":"OPEN",
      "no_published_target_invariants_used":True,
      "no_q3f_holdout_source_read":True,
      "neural_model_calls":0,
      "records":outcome
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--q3i",type=Path,required=True)
    p.add_argument("--q3k2",type=Path,required=True)
    p.add_argument("--q3l",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=run(a.dataset,{"q3i":a.q3i,"q3k2":a.q3k2,"q3l":a.q3l})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3M_ASSERT_SITE_REPROVEN",r["historical_full_original_certificates_reverified_with_site_gate"],
         "OF",r["historical_13_exact_originals"])
    print("Q3M_SOURCE_REJECTIONS",r["disallowed_pre_loop_or_nontop_level_original_claims"])
    print("Q3M_PER_ORIGINAL",[(r["study"],r["original_path"],r["annotation_site"]["status"],r["reproof_status"])
                              for r in r["records"]])
    print("Q3M_GLOBAL",r["global_q1_q7"])
