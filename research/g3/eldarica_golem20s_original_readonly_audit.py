"""G3 immutable post-first independent specialist receipt audit: no solver rerun.

Strictly checks the exact first original Z3+2025 benchmark SHA, and actual
Eldarica v2.3/Golem v0.9.0 second original SHA even though original Actions
post-processing shell exited 1 due to an unbound Bash interpolation.
Does not relabel timed-out or unknown as a mathematically unsolvable source.
"""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

FIRST={
 "LIA_MULTIPHASE":"c4529472973dc7e102e3b755ff866ccac5f285a9d7206488d65dd054f5b41535",
 "ARRAY_CHC":"47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8",
}
RECHECK={
 "LIA_MULTIPHASE":"03f8472108478bf0cd6ce6b2620be3b317a5231b3ccb34cca274bae4a9a49a6d",
 "ARRAY_CHC":"5cceacc9e494e0ee75e9b3747a753e37b632b7f64dcecd5afdcf14df282f576a",
}
MANIFEST=Path("docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json")

def sha(x:bytes):return hashlib.sha256(x).hexdigest()
def audit(args):
  p=json.loads(MANIFEST.read_text())
  groups={g["id"]:g for g in p["cohorts"]}
  errors=[];allrows=[];counts={}
  for i,co in enumerate(("LIA_MULTIPHASE","ARRAY_CHC")):
    f=Path(args[1+i]);a=Path(args[3+i])
    fresh=f.read_bytes();later=a.read_bytes()
    if sha(fresh)!=FIRST[co]:errors.append("FROZEN_2025_SOURCE_FIRST_SHA_CHANGED_"+co)
    if sha(later)!=RECHECK[co]:errors.append("FROZEN_POSTFIRST_EXPERT_RESULT_SHA_CHANGED_"+co)
    fr=json.loads(fresh);post=json.loads(later)
    if fr.get("cohort")!=co or len(fr.get("rows",[]))!=8:
      errors.append("PREOPEN_FIRST_EIGHT_ORIGINALS_CHANGED_"+co);continue
    expected=8 if co=="ARRAY_CHC" else 7
    if post.get("postfirst_original_scope")!=co or len(post.get("rows",[]))!=expected:
      errors.append("POSTFIRST_DENOMINATOR_CHANGED_"+co);continue
    if post.get("original_Z3_FIRST_SHA256")!=FIRST[co]:
      errors.append("POSTFIRST_REFERENCES_WRONG_ORIGINAL_SHA_"+co)
    if post.get("extra_training_and_neural_model_calls")!=0:
      errors.append("NEUMANN_ML_WAS_RUN_UNEXPECTEDLY_"+co)
    firstrows=[r for r in fr["rows"] if
       r.get("status")=="NO_NATIVE_GROUNDED_VERDICT_WITHIN_BUDGET"]
    if len(firstrows)!=expected:
      errors.append("NEW_SELECTION_DID_NOT_MATCH_ORIGINAL_FIRST_"+co);continue
    orig_index={r["file"]:r for r in groups[co]["targets"]}
    now=[]
    for source,record in zip(firstrows,post["rows"]):
      if source["file"]!=record["original_file"] or record["first_Z3_status"]!=source["native"][0]["status"]:
        errors.append("POSTFIRST_SOURCE_ORDER_OR_NATIVE_FIRST_DRIFT_"+co);continue
      upstream=orig_index[source["file"]]
      if source.get("git_blob")!=upstream["git_blob"] or record["original_git_blob"]!=upstream["git_blob"]:
        errors.append("GIT_PUBLISHER_SOURCE_BLOB_CHANGED_"+co);continue
      if len(record["natives"])!=(1 if co=="ARRAY_CHC" else 2):
        errors.append("EXPECTED_NEW_NATIVE_EXPERT_MISSING_"+co);continue
      names={x.get("engine") for x in record["natives"]}
      if names!=({"Eldarica"} if co=="ARRAY_CHC" else {"Eldarica","Golem"}):
        errors.append("EXPERT_ENGINE_RIGHTS_CHANGED_"+co)
      outcome=[{"engine":n["engine"],"status":n["status"],"wall_ms":n.get("wall_ms")}
        for n in record["natives"]]
      verified_sat=any(n["status"]=="SAT_CLAIM_ONLY_NOT_INDEPENDENTLY_PROVED"
                  for n in record["natives"])
      unresolved=all(n["status"] in ("TIMEOUT","UNKNOWN_OR_NO_GROUNDED_CLAIM")
               for n in record["natives"])
      if verified_sat and co=="ARRAY_CHC":
        # An original official unlabeled outcome requires extra independent
        # witness before asserting this as science.
        errors.append("ARRAY_SOURCE_NEW_CLAIM_REQUIRES_EXTRA_PROOF")
      row={"cohort":co,"original":record["original_file"],
           "original_git_blob":upstream["git_blob"],
           "first_Z3":"NO_GROUNDED_VERDICT",
           "postfirst_engines":outcome,
           "official_expected":"SAT" if co=="LIA_MULTIPHASE" else "NO_PUBLISHED_VERDICT",
           "source_publisher_corroborated_SAT":verified_sat and co=="LIA_MULTIPHASE",
           "still_unresolved_at_20s":unresolved,
           "cannot_infer_unsolvable":True}
      now.append(row)
      allrows.append(row)
    sat=sum(r["source_publisher_corroborated_SAT"] for r in now)
    still=sum(r["still_unresolved_at_20s"] for r in now)
    if co=="LIA_MULTIPHASE" and (sat!=3 or still!=4):
      errors.append("LIA_POSTFIRST_OBSERVED_3_4_STATUS_CHANGED")
    if co=="ARRAY_CHC" and (sat!=0 or still!=8):
      errors.append("ARRAY_POSTFIRST_OBSERVED_0_8_CHANGED")
    counts[co]={"originals_checked":expected,
      "new_native_SAT_claim_consistent_with_official_label":sat,
      "still_resource_unresolved":still}
  if len(allrows)!=15:errors.append("POSTFIRST_15_EXACT_ORIGINAL_SIZE_CHANGED")
  return {
    "schema":"neumann.g3.postfirst-native-15-immmutable-readonly-v1",
    "audit_pass":not errors,"errors":errors,
    "previous_first_benchmark_SHA256":FIRST,
    "postfirst_20s_expert_receipt_SHA256":RECHECK,
    "first_original_run":42174775254,
    "new_original_postfirst_run_with_shell_epilogue_only_error":42179065682,
    "originals_postfirst_checked":len(allrows),
    "counts":counts,
    "student_neural_calls":0,"original_solver_reexecutions_in_audit":0,
    "new_ARC_eval_original_IDs_consumed":0,
    "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
    "cases":allrows
  }
if __name__=="__main__":
  try:
    v=audit(sys.argv)
    print(json.dumps(v,indent=2,sort_keys=True))
    if not v["audit_pass"]:raise SystemExit(1)
  except Exception as e:
    print("G3_POSTFIRST_READONLY_AUDIT_INFRA_FAIL",repr(e),file=sys.stderr)
    raise SystemExit(2)
