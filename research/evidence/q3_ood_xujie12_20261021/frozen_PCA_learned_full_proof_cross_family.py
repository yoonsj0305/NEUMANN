"""First-source-OOD 12 xujie_code2inv genuine programs; unchanged prior
from_2018 fitted PCA and exact-classical controls. Metadata first frozen at
fffa79f BEFORE program source bodies opened. This wrapper NEVER fits to
cross-family results or changes source parser/learning/verifier.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from research.evidence.q3_v32_posthoc_full_original_20261021.real_trained_PCA_plus_source_Post_3VC import one
LOCK="fffa79f076f8862beb14cbff5bbb7a15619222ce"
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    f=json.loads(Path(a.freeze).read_text())
    assert f["schema"]=="neumann.q3.20261021.unseen_cross_family_xujie_code2inv_12_original_SHA_metadata_only.v1"
    assert f["upstream"].split("@")[-1]==UPSTREAM
    assert f["source_bodies_opened_BEFORE_this_SHA_commit"] is False
    items=f["cases"]
    assert len(items)==12 and len({q["git_blob"] for q in items})==12
    for q in items:
        b=(Path(a.root)/q["path"]).read_bytes()
        if len(b)!=q["bytes"] or blob(b)!=q["git_blob"]:
            raise RuntimeError("XUJIE_FIRST_CROSS_FAMILY_ORIGINAL_SHA_CHANGED:"+q["path"])
    rows=[]
    for q in items:
        r=one(Path(a.root),q)
        r["first_original_body_git_blob_matched_registration"]=True
        rows.append(r)
    def count(key):
        return sum(r.get(key,{}).get("fully_verified_complete_original_3VC",False) for r in rows)
    valid=[r for r in rows if r["status"]=="EXECUTED_POSTHOC_REAL_NATIVE_FULL_3VC_COMPARE"]
    result={
      "schema":"neumann.q3.xujie_12_never_opened_OOD_full_original_trained_PCA_3VC.v1",
      "sha_lock_before_first_body_git_commit":LOCK,
      "new_distinct_source_originals":12,
      "cross_family":"xujie_code2inv",
      "original_native_full_pre_trans_post_parser_parity_count":len(valid),
      "actually_fit_numeric_PCA_count":sum(r.get("actual_CPU_fitted_model",{}).get("real_CPU_PCA_model_fits",0)>0 for r in rows),
      "learned_complete_original_Z3_cvc5_certified":count("TRAINED_PCA_plus_original_POST"),
      "post_only_complete_original_Z3_cvc5_certified":count("POST_only_already_exact_original_dual"),
      "shallow_nofit_complete_original_Z3_cvc5_certified":count("simple_NOLEARN_plus_original_POST"),
      "equal_math_exact_classical_complete_original_Z3_cvc5_certified":count("EXACT_CLASSICAL_plus_original_POST"),
      "learned_only_vs_shallow_nofit":sum(r.get("trained_full_3VC_success_not_no_learn",False) for r in rows),
      "learned_only_vs_exact_classical":sum(r.get("trained_full_3VC_success_not_exact_classical",False) for r in rows),
      "failed_or_unsupported_originals":12-len(valid),
      "existing_frozen_model_unmodified_on_new_family":True,
      "no_heldout_weight_fine_tune_algorithm_changes":True,
      "model_fit_on_each_new_original_execution_data_not_weight_transfer":True,
      "zero_new_mathematical_theorem_claim":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "per_original_case_with_failures":rows
    }
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for k in ("new_distinct_source_originals","original_native_full_pre_trans_post_parser_parity_count",
              "actually_fit_numeric_PCA_count","learned_complete_original_Z3_cvc5_certified",
              "shallow_nofit_complete_original_Z3_cvc5_certified",
              "equal_math_exact_classical_complete_original_Z3_cvc5_certified",
              "learned_only_vs_shallow_nofit","learned_only_vs_exact_classical",
              "failed_or_unsupported_originals"):
        print("NEUMANN_CROSS_FAMILY_SOURCE_FIRST_OOD",k,result[k])
    print("Q3_GLOBAL_OPEN")
if __name__=="__main__":main()
