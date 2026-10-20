"""Immutable first 0/18 audit + ONE full-source verification of original 110
neural generated Bool relational ASTs, without changing trained parameters
or original Pre/Trans/Post. Authentic original 2VC Z3 and pinned cvc5.
NOT first blind, NOT novel operator, classical complete 21/570 known.
"""
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_gateR_learned_bool_20261021.first_cpu_trained_bool_implication_source_only import (
 TRAIN,HOLDOUT,FILE,GIT_SHA,SEED,train,original_samples,
 model_candidates,sha,blob,sexprs,compile_typed_original,
 compile_independent_native,dual,elapsed)

FIRST_SHA="c3ca5345ca0de3ec9644206fe109150e71448232f400659cda3d67bdecc6bb78"
TRAINED_SHA="d00ebe239e23fe86e6ace2fe2d7a69ea380f0fb6fc4dbc096cc3bb3d2baf07d0"
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--first",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 t=time.perf_counter_ns()
 raw=a.first.read_bytes()
 if sha(raw)!=FIRST_SHA:raise RuntimeError("FIRST_HISTORICAL_RECEIPT_TAMPERED")
 first=json.loads(raw)
 baseline=first["real_original"]
 assert baseline["frozen_first_network_proposals_checked"]==18
 assert baseline["first_network_source_only_inductive_count"]==0
 assert baseline["matched_complete_classical_bool_grammar"]["inductive_candidates_Z3_found"]==21
 weights,study=train()
 if study["trained_network_weight_sha256"]!=TRAINED_SHA:
  raise RuntimeError("FROZEN_268_PARAMETER_MODEL_CHANGED")
 if study["learned_heldout_correct"]!=418:
  raise RuntimeError("UNREPRODUCIBLE_SYNTHETIC_HOLDOUT")
 raw_source=(a.root/FILE).read_bytes()
 if blob(raw_source)!=GIT_SHA:raise RuntimeError("SOURCE_GIT_ID_CHANGED")
 fs=sexprs(raw_source)
 typed=compile_typed_original(fs)
 native=compile_independent_native(fs,typed)
 parity={name:dual(z3.Xor(typed[name],native[name]),"unsat",9)
   for name in ["pre","trans","post"]}
 if not all(x["dual_pass"] for x in parity.values()):
  raise RuntimeError("SOURCE_PRE_TRANS_POST_PARITY_UNPROVEN")
 index,models,sampling=original_samples(typed)
 preds=model_candidates(typed,index,models,weights)
 if len(preds)!=baseline["candidate_count_from_trained_network"]:
  raise RuntimeError("FIRST_SOURCE_PROPOSAL_SET_IS_DIFFERENT")
 for previous,current in zip(baseline["first_network_candidates"],preds[:18]):
  for attr in ("bool_state_index_pair","class","original_candidate_SMT"):
   if previous[attr]!=current[attr]:
    raise RuntimeError("FIRST_18_CHANGING_AFTER_ORIGINAL_OBSERVATION_"+attr)
  if abs(previous["model_probability"]-current["model_probability"])>1e-6:
   raise RuntimeError("FIRST_18_NETWORK_SCORE_CHANGED")
 printed=[]
 accepted=[]
 for ix,item in enumerate(preds):
  q=item.pop("clause")
  badpre=z3.And(native["pre"],z3.Not(q))
  pre=dual(badpre,"unsat",8)
  if pre["dual_pass"]:
   future=z3.substitute(q,*list(zip(typed["now"],typed["next"])))
   step=dual(z3.And(q,native["trans"],z3.Not(future)),"unsat",9)
  else:
   step={"status":"NOT_RUN_PRE_BAD_OR_UNKNOWN"}
  okay=pre["dual_pass"] and step.get("dual_pass",False)
  row={**item,"frozen_candidate_rank":ix+1,
     "original_Pre_implies_rel_Z3_cvc5":pre,
     "rel_and_original_Trans_implies_rel_next_Z3_cvc5":step,
     "source_genuine_inductive_original_2VC":okay}
  printed.append(row)
  if okay:accepted.append(row)
 print("FULL_FROZEN_NETWORK_BOOL_CANDIDATES",len(preds),
  "PROVEN",len(accepted),
  "FIRST_PROVEN_RANK",accepted[0]["frozen_candidate_rank"] if accepted else None,flush=True)
 decision={
  "schema":"neumann.q3.gateR.neural_Bool_all110_posthoc_original_2VC.v1",
  "first_original_actions_run":39512051313,
  "immutable_first_JSON_SHA256":FIRST_SHA,
  "immutable_first_model_real_source_pass":"0/18",
  "matched_complete_exact_classical_Bool_grammar":"21/570",
  "original_Git_blob":GIT_SHA,
  "real_source_sha256":sha(raw_source),
  "frozen_268_neural_weights_SHA256":TRAINED_SHA,
  "synthetic_holdout_correct_replay":study["learned_heldout_correct"],
  "synthetic_training_label_permutation_correct":study["permuted_label_heldout_correct"],
  "same_source_samples_proposals_first18_identical":True,
  "original_source_native_custom_semantic_parity":parity,
  "source_sampling":sampling,
  "neural_boolean_source_proposal_count":len(preds),
  "neural_boolean_actual_original_inductive_2VC_dual_proved":len(accepted),
  "one_source_posthoc_full_verifier_budget_expansion_only":True,
  "first_safety_original_3VC_not_claimed":True,
  "fixed_boolean_grammar_exact_classical_stronger":"YES",
  "new_operator_outside_fixed_boolean_grammar":"NOT_DEMONSTRATED",
  "global_Q3":"OPEN","gate_R_full":"OPEN","gate_V":"OPEN","global_Q1_Q7":"OPEN",
  "GPU_calls":0,"paid_API_calls":0,
  "whole_wall_ms":elapsed(t),
  "all_immutable_order_candidate_receipts":printed}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(decision,sort_keys=True,indent=2)+"\n")
 print("NEUMANN_FIRST_UNSEEN_G1",decision["gate_V"],
  "GLOBAL_Q3",decision["global_Q3"])
if __name__=="__main__":main()
