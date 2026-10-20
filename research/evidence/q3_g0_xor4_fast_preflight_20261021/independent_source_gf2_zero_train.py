"""Pretraining CPU-free GF2 headroom gate for source 4-Boolean XOR program
invariants. Requires authentic original SHA pinned source semantics.
No neural train/forward. Strong synthetic GO and NO_GO controls and
immutable comparison to true PR321 first-negative original experiments.
"""
import argparse,hashlib,itertools,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_learned_xor4_20261021.first_two_frozen_source_four_way_parity import (
 ORIGINS,UPSTREAM,sha,blob,sexprs,compile_typed_original,
 compile_independent_native,dual,elapsed,samples,sample_pairwise_basis,
 gf2_in_span)
FIRST_SHA="5e9c7f5d1e4039d5a7e3b7edd90857684d8d7ac14b3ab10589b76c2102c2e47b"

def exhaustive_gf2(rows,width):
 if not rows or width<4:raise ValueError("NOT_ENOUGH_STATES")
 basis,pairwise=sample_pairwise_basis(rows,width)
 surviving=[]
 sample_witnesses=0
 sample_consistent=0
 reducible=0
 for quad in itertools.combinations(range(width),4):
  obs=[sum(r[i] for i in quad)%2 for r in rows]
  if any(y!=obs[0] for y in obs):
   sample_witnesses+=1
   continue
  sample_consistent+=1
  formula=sum(1<<i for i in quad)|(obs[0]<<width)
  if gf2_in_span(basis,formula):
   reducible+=1
  else:surviving.append((quad,obs[0]))
 total=sum(1 for _ in itertools.combinations(range(width),4))
 if total!=sample_witnesses+sample_consistent:
  raise RuntimeError("NONEXHAUSTIVE_EXACT_G4_COUNT")
 if sample_consistent!=reducible+len(surviving):
  raise RuntimeError("GF2_SPAN_ACCOUNTING_FAIL")
 return {"all_4var_combinations":total,
   "source_observation_disproved_constant_XOR4_count":sample_witnesses,
   "sample_consistent_XOR4_total":sample_consistent,
   "explained_by_conservative_sample_pairwise_span":reducible,
   "independent_four_way_parity_headroom_count":len(surviving),
   "independent_g4_candidates":[{"indices":list(v),"constant_parity":off}
      for v,off in surviving[:64]],
   "candidate_overflow_after_64":max(0,len(surviving)-64),
   "exact_classical_sample_pairwise_GF2":pairwise,
   "decision":"GO_TRAIN_NEW_GRAMMAR_CANDIDATES" if surviving else
       "NO_GO_SKIP_NEURAL_TRAINING_FOR_THIS_XOR4_CLASS"}

def controls():
 even=[[int(bool(j&(1<<k))) for k in range(4)] for j in range(16)
       if j.bit_count()%2==0]
 all_states=[[int(bool(j&(1<<k))) for k in range(4)]
       for j in range(16)]
 positive=exhaustive_gf2(even,4)
 negative=exhaustive_gf2(all_states,4)
 if positive["independent_four_way_parity_headroom_count"]!=1 or \
    positive["independent_g4_candidates"][0]["constant_parity"]!=0:
  raise RuntimeError("SYNTHETIC_POSITIVE_HEADROOM_MISSED")
 if negative["independent_four_way_parity_headroom_count"]!=0:
  raise RuntimeError("SYNTHETIC_NEGATIVE_FALSE_GO")
 return {"nonpairwise_even4_positive":"PASS_GO_1_OF_1",
   "unconstrained_all16_negative":"PASS_NO_GO_0_OF_1",
   "positive_details":positive,"negative_details":negative}

def check_case(root,path,githash,first):
 st=time.perf_counter_ns()
 row={"source":path,"expected_git_blob":githash}
 try:
  raw=(root/path).read_bytes()
  if blob(raw)!=githash:raise RuntimeError("SOURCE_GIT_BLOB_CHANGED")
  row["original_sha256"]=sha(raw)
  sex=sexprs(raw)
  typed=compile_typed_original(sex)
  native=compile_independent_native(sex,typed)
  parity={k:dual(z3.Xor(typed[k],native[k]),"unsat",10)
       for k in ("pre","trans","post")}
  row["native_vs_custom_original_parity"]=parity
  if not all(v["dual_pass"] for v in parity.values()):
   raise RuntimeError("SOURCE_SEMANTIC_PARITY_DUAL_FAILED")
  original={**typed,**native}
  goal_vars={str(v) for v in z3.z3util.get_vars(native["post"])}
  positions=[i for i,(name,typ) in enumerate(typed["states"])
    if typ=="Bool" and str(typed["now"][i]) not in goal_vars]
  row["eligible_source_bool_indices"]=positions
  sample,receipts=samples(original,positions)
  row["sample_reachability_construction"]=receipts
  row["actual_source_observation_count"]=len(sample)
  row["observation_rows_sha256"]=sha(json.dumps(sample,separators=(",",":")).encode())
  analysis=exhaustive_gf2(sample,len(positions))
  row["complete_nonlearned_GF2_enumeration"]=analysis
  if len(positions)!=len(first["eligible_source_boolean_state_indices"]):
   raise RuntimeError("FIRST_SOURCE_ELIGIBLE_WIDTH_REGRESSION")
  if len(sample)!=first["original_source_only_64_or_fewer_observed_models"]:
   raise RuntimeError("FIRST_SOURCE_SAMPLING_REGRESSION")
  if analysis["exact_classical_sample_pairwise_GF2"]["GF2_pairwise_span_rank"]!=\
    first["source_sample_pairwise_upper_bound_on_inductive_span"]["GF2_pairwise_span_rank"]:
   raise RuntimeError("FIRST_SOURCE_PAIRWISE_GF2_REGRESSION")
  if analysis["independent_four_way_parity_headroom_count"]!=\
     first["classical_exact_full_sample_consistent_higher_order_count"]:
   raise RuntimeError("FIRST_REAL_XOR4_CLASSICAL_HEADROOM_REGRESSION")
  row["first_real_original_2VC_learned_inductives_preserved"]=\
      first["learned_first_source_original_dual_2VC_count"]
  row["first_real_original_2VC_classical_inductives_preserved"]=\
      first["strong_classical_first_source_original_dual_2VC_count"]
  row["status"]="ORIGINAL_REPLAY_VALID_G0_HEADROOM_PROVED"
 except Exception as exc:
  row["status"]="ABSTAIN_ORIGINAL_HEADROOM_REPLAY"
  row["error"]=type(exc).__name__+":"+str(exc)[:280]
 row["wall_ms_no_neural_learning_or_inference"]=elapsed(st)
 print("REAL_SOURCE_ZERO_NEURAL_HEADROOM",path,row["status"],
   "G0",row.get("complete_nonlearned_GF2_enumeration",{}).get("decision"),
   "ERROR",row.get("error"),flush=True)
 return row

def main():
 a=argparse.ArgumentParser()
 a.add_argument("--root",type=Path,required=True)
 a.add_argument("--first",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 opts=a.parse_args()
 t=time.perf_counter_ns()
 source=opts.first.read_bytes()
 if sha(source)!=FIRST_SHA:raise RuntimeError("FIRST_RUN_IMMUTABLE_SHA_MISMATCH")
 historic=json.loads(source)
 assert len(historic["cases"])==len(ORIGINS)==2
 verification_controls=controls() # No real source, no neural
 rows=[check_case(opts.root,*data,historic["cases"][i])
       for i,data in enumerate(ORIGINS)]
 result={"schema":"neumann.q3.G0.exact_pretraining_GF2_headroom.v1",
   "upstream_revision":UPSTREAM,
   "first_original_full_run":39514997383,
   "immutable_first_real_JSON_sha256":FIRST_SHA,
   "all_first_original_two_git_ids_preserved":all(
      "original_sha256" in r for r in rows),
   "replayed_original_positive_and_negative_source_count":len(rows),
   "independent_positive_negative_synthetic_preflight_controls":verification_controls,
   "G0_original_replay_certified":all(
      r["status"]=="ORIGINAL_REPLAY_VALID_G0_HEADROOM_PROVED" for r in rows),
   "exact_classical_full_independent_G4_headroom":sum(
      r.get("complete_nonlearned_GF2_enumeration",{}).get(
         "independent_four_way_parity_headroom_count",0) for r in rows),
   "zero_neural_forward_calls":True,"zero_neural_train_updates":True,
   "first_historical_training_wall_ms":historic["model"]["source_free_synthetic_generation_and_training_ms"],
   "trained_new_xor4_math_operator":"NO_GO_IN_THIS_TWO_SOURCE_SAMPLE_INDEPENDENT_GRAMMAR",
   "NOT_full_program_absence_of_new_operator_theorem":True,
   "global_Q3":"OPEN","gate_R_full":"OPEN","gate_V":"OPEN","global_Q1_Q7":"OPEN",
   "GPU_calls":0,"paid_API_calls":0,"whole_preflight_wall_ms":elapsed(t),
   "actual_original_sources":rows}
 opts.out.parent.mkdir(parents=True,exist_ok=True)
 opts.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print("Q3_G0_STOP_XOR4_TRAINING",result["exact_classical_full_independent_G4_headroom"],
   "HEADROOM; NO_NEURAL_TRAINING",result["zero_neural_train_updates"])
 print("GLOBAL_Q3",result["global_Q3"])
if __name__=="__main__":main()
