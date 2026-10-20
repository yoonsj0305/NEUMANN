"""NEUMANN Q3: externally authored SOURCE-first original transfer without retuning.
All three target Git blob IDs preregistered (commit 2d2a6c4). Test source
contents only after commit. Hard fail on changed fixed pretrained 42 weights.
Origin provenance is collection-level; unsupported != neural reasoning failure.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import train_frozen_operator
from research.evidence.q3_coclock_fixed42_20261020.posthoc_genuine_source_affine_controller import (
 one as frozen_one,FROZEN_WEIGHTS_SHA)
from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import blob

UPSTREAM="SyGuS-Org/benchmarks"
REV="13c8deb68a873635879c9a69bc78caebd340f646"
COHORT=(
 ("andrew_lustre","lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl",
  "8490b3e25ff7d462a7405e68e742be1abb35b8f8"),
 ("xujie_code2inv","lib/Inv_Track/xujie_code2inv/1.c.sl",
  "859bae24a9f26044a40a3c97f1d2e5fc08504f06"),
 ("sygus_comp_2017","comp/2017/Inv_Track/sum1.sl",
  "5fd2e4f7841aea6ebab96d30d394819b0d2b17d6")
)
def ms(t):return round((time.perf_counter_ns()-t)/1e6,3)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();start=time.perf_counter_ns()
 # Existing weights unchanged. This call is the SAME training on SAME 384
 # synthetic samples, performed BEFORE touching any heldout original source.
 weights,training=train_frozen_operator()
 if training["frozen_trained_weights_sha256"]!=FROZEN_WEIGHTS_SHA:
  raise RuntimeError("FROZEN_MODEL_WEIGHT_IDENTITY_VIOLATED")
 assert training["heldout_64_full_integer_coefficient_predictions_exact"]==64
 print("FROZEN_PRETRAINED_WEIGHTS_SHA",FROZEN_WEIGHTS_SHA,flush=True)
 rows=[]
 for origin,path,frozen_git_blob in COHORT:
  t=time.perf_counter_ns()
  row={"collection":origin,"original_path":path,
   "expected_frozen_git_blob":frozen_git_blob,
   "conservative_source_dialect":"PENDING",
   "frozen_learned_independent_original_3VC":False,
   "same_input_exact_classical_original_3VC":False}
  try:
   raw=(a.root/path).read_bytes()
   actual=blob(raw)
   if actual!=frozen_git_blob:raise RuntimeError("PRE_CONTENT_SOURCE_BLOB_MISMATCH")
   row["actual_git_blob_verified"]=True
   row["original_sha256"]=hashlib.sha256(raw).hexdigest()
   # Identify characteristics only; do not adapt or rewrite grammar.
   row["published_contains_synth_inv"]=b"(synth-inv" in raw
   row["published_contains_inv_constraint"]=b"(inv-constraint" in raw
   row["published_has_explicit_Bool_state"]=b" Bool)" in raw
   row["source_bytes"]=len(raw)
   full=frozen_one(a.root,path,frozen_git_blob,weights)
   row["raw_unchanged_frozen_model_attempt"]=full
   row["frozen_learned_independent_original_3VC"]=bool(
       full.get("learned_full_original_dual_3VC",False))
   row["same_input_exact_classical_original_3VC"]=bool(
       full.get("classical_full_original_dual_3VC",False))
   row["conservative_source_dialect"]=(
      "ORIGINAL_3VC_DUAL_VERIFIED" if
       row["frozen_learned_independent_original_3VC"] and
       row["same_input_exact_classical_original_3VC"]
      else "UNSUPPORTED_OR_NOT_PROVEN_WITH_FROZEN_ADAPTER")
  except Exception as exc:
   row["conservative_source_dialect"]="ABSTAIN_SOURCE_IDENTITY_OR_EXECUTION_ERROR"
   row["error"]=type(exc).__name__+":"+str(exc)[:240]
  row["wall_ms"]=ms(t)
  rows.append(row)
  print("EXTERNAL_FIRST_ORIGINAL",origin,path,
    "LEARNED",row["frozen_learned_independent_original_3VC"],
    "STRONG_CLASSICAL",row["same_input_exact_classical_original_3VC"],
    "DIALECT",row["conservative_source_dialect"],
    "ERROR",row.get("raw_unchanged_frozen_model_attempt",{}).get("error",""),
    flush=True)
 report={"schema":"neumann.q3.cross_research_collections.frozen42.first.20261020.v1",
   "original_remote_repo":UPSTREAM,"original_sha_frozen_upstream_rev":REV,
   "preregistered_content_blind_commit":"2d2a6c44424bf5f1e641321b4b748c59ed26a428",
   "cross_upstream_to_previous_LoopInvGen":True,
   "collection_count":len(rows),
   "separate_author_authorship_independently_verified":False,
   "three_sources_pinned_before_source_body_read":True,
   "model_training_data_contains_external_target_source":False,
   "trained_model_unchanged_original_weights":training,
   "first_frozen_cross_corpus_learned_original_passes":sum(
     bool(x["frozen_learned_independent_original_3VC"]) for x in rows),
   "equal_input_exact_classical_original_passes":sum(
     bool(x["same_input_exact_classical_original_3VC"]) for x in rows),
   "all_three_rows_retained":len(rows)==3,
   "first_attempt_without_target_specific_adapter_tuning":True,
   "same_fixed_degree_learned_operator_no_new_mathematical_primitive":True,
   "no_superiority_over_complete_classical":True,
   "original_unsupported_dialect_never_counted_reasoning_fail":True,
   "GPU_calls":0,"paid_API_calls":0,
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "whole_study_wall_ms":ms(start),"sources":rows}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print("FIRST_CROSS_CORPUS_LEARNED_ORIGINAL",
  report["first_frozen_cross_corpus_learned_original_passes"],"/3",
  "CLASSICAL",report["equal_input_exact_classical_original_passes"],"/3",
  "GLOBAL_Q3 OPEN",flush=True)
if __name__=="__main__":main()
