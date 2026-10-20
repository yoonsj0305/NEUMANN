"""NEUMANN Q3 first unopened original learned four-way Boolean XOR AST.
Frozen source SHA + hypothesis in PRIOR COMMIT c9cf02b11 before targets read.
Neural is real trainable 16->32->3 MLP; no real source training labels.
Source full native semantics and 2VC require Z3 AND independent cvc5.
Exact GF2 source-only pairwise span and full classical four-way XOR baseline.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math,time
from pathlib import Path
import numpy as np
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
 sha,blob,sexprs,compile_typed_original,compile_independent_native,dual,elapsed)

ORIGINS=(
 ("lib/Inv_Track/andrew_lustre/FIREFLY_1.lus.sl","e23218d41372a350467aba1386897cb0311247ff"),
 ("lib/Inv_Track/andrew_lustre/DRAGON_2.lus.sl","17f0cea250008e9e3575d38181f7e40804501dde"),
)
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
SYNTH_TRAIN=3600
SYNTH_TEST=600
SAMPLE_SIZE=32
SEED=20261021
N_STEPS=220
MAX_SOURCE_MODELS=32
FIRST_PROPOSALS=48
CLASSES=("NONE","XOR4_ZERO","XOR4_ONE")
PRESOURCE_COMMIT="c9cf02b11d6bb8fdd4ffe10a7b6aecc36e0ca0cb"

def synthetic(seed,count):
 rng=np.random.default_rng(seed)
 X=np.empty((count,16),dtype=np.float64)
 Y=rng.integers(0,3,size=count)
 parity=np.array([int(k).bit_count()%2 for k in range(16)],dtype=np.int64)
 for idx,label in enumerate(Y):
  valid=np.flatnonzero(parity==label-1) if label else np.arange(16)
  weights=rng.dirichlet(np.ones(len(valid))*rng.uniform(0.7,2.8))
  draws=rng.choice(valid,size=SAMPLE_SIZE,p=weights)
  X[idx]=np.bincount(draws,minlength=16)/float(SAMPLE_SIZE)
 return X,Y

def forward(X,p):
 W1,b1,W2,b2=p
 hidden=np.tanh(X@W1+b1)
 logits=hidden@W2+b2
 probs=np.exp(logits-logits.max(axis=1,keepdims=True))
 probs/=probs.sum(axis=1,keepdims=True)
 return probs,hidden

def learn():
 st=time.perf_counter_ns()
 X,y=synthetic(SEED,SYNTH_TRAIN)
 T,yt=synthetic(SEED+1,SYNTH_TEST)
 rng=np.random.default_rng(SEED+2)
 def fresh():
  return [rng.normal(0,0.5,(16,32)),np.zeros(32),
    rng.normal(0,0.3,(32,3)),np.zeros(3)]
 def fit(labels):
  W1,b1,W2,b2=fresh()
  n=len(X);ix=np.arange(n)
  loss=[]
  for step in range(N_STEPS+1):
   p,h=forward(X,(W1,b1,W2,b2))
   ce=-np.log(np.maximum(1e-12,p[ix,labels])).mean()
   if step%55==0:loss.append(round(float(ce),6))
   dz=p.copy();dz[ix,labels]-=1;dz/=n
   gw2=h.T@dz+0.00005*W2;gb2=dz.sum(0)
   dh=(dz@W2.T)*(1-h*h)
   gw1=X.T@dh+0.00005*W1;gb1=dh.sum(0)
   rate=0.75/(1+step/75)
   W1-=rate*gw1;b1-=rate*gb1;W2-=rate*gw2;b2-=rate*gb2
  return (W1,b1,W2,b2),loss
 true_model,loss=fit(y)
 negative_model,negative_loss=fit(rng.permutation(y))
 prediction,_=forward(T,true_model)
 neg,_=forward(T,negative_model)
 # Classical nonlinear exact parity-count classifier: unlearned.
 even=np.array([(int(k).bit_count()%2)==0 for k in range(16)])
 known_even=np.sum(T[:,~even],axis=1)<1e-12
 known_odd=np.sum(T[:,even],axis=1)<1e-12
 exact=np.where(known_even,1,np.where(known_odd,2,0))
 audit={"synthetic_training_programs":SYNTH_TRAIN,
  "synthetic_independent_test_programs":SYNTH_TEST,
  "model_trainable_parameters":sum(int(x.size) for x in true_model),
  "network_architecture":"16→32 tanh→3 softmax",
  "synthetic_train_loss_every55":loss,
  "learned_test_correct":int((prediction.argmax(1)==yt).sum()),
  "shuffled_train_labels_test_correct":int((neg.argmax(1)==yt).sum()),
  "unlearned_exact_contingency_test_correct":int((exact==yt).sum()),
  "first_model_weight_sha256":hashlib.sha256(b"".join(
    np.asarray(x,dtype=">f8").tobytes() for x in true_model)).hexdigest(),
  "source_free_synthetic_generation_and_training_ms":elapsed(st),
  "no_actual_original_source_or_post_used_for_training":True}
 return true_model,audit

def gf2_add(basis,vector):
 while vector:
  high=vector.bit_length()-1
  if high not in basis:
   basis[high]=vector
   return True
  vector^=basis[high]
 return False
def gf2_in_span(basis,vector):
 while vector:
  pivot=vector.bit_length()-1
  if pivot not in basis:return False
  vector^=basis[pivot]
 return True

def samples(original,mask):
 indices=mask
 sample=[]
 receipt=[]
 for label,pred,states in (
   ("source_Pre",original["pre"],original["now"]),
   ("genuine_source_Pre_Trans_successor",z3.And(original["pre"],original["trans"]),original["next"])):
  solver=z3.Solver();solver.set(timeout=9000);solver.add(pred)
  count=0
  for _ in range(MAX_SOURCE_MODELS):
   verdict=solver.check()
   if verdict!=z3.sat:
    receipt.append({"phase":label,"terminal":str(verdict)})
    break
   model=solver.model()
   values=tuple(int(z3.is_true(model.eval(states[i],model_completion=True))) for i in indices)
   sample.append(values)
   count+=1
   solver.add(z3.Or(*[states[i]!=z3.BoolVal(bool(bit)) for i,bit in zip(indices,values)]))
  receipt.append({"phase":label,"distinct_observed_bool_models":count})
 return sample,receipt

def preproved_and_source_inductive(original,expr,small_timeout=7):
 step=z3.substitute(expr,*list(zip(original["now"],original["next"])))
 initial=dual(z3.And(original["pre"],z3.Not(expr)),"unsat",small_timeout)
 if not initial["dual_pass"]:
  return {"initial":initial,"step":{"not_run":"initial_not_dual_unsat"},"dual_2vc":False}
 consequence=dual(z3.And(expr,original["trans"],z3.Not(step)),"unsat",small_timeout)
 return {"initial":initial,"step":consequence,
   "dual_2vc":bool(consequence["dual_pass"])}

def xor4(original,index,vec,offset):
 bits=[original["now"][index[k]] for k in vec]
 p=z3.BoolVal(False)
 for expr in bits:p=z3.Xor(p,expr)
 return p==z3.BoolVal(bool(offset))

def sample_pairwise_basis(rows,count):
 basis={}
 singles=0;pairs=0
 for width in (1,2):
  for cols in itertools.combinations(range(count),width):
   parity=[sum(r[i] for i in cols)%2 for r in rows]
   if not parity or any(p!=parity[0] for p in parity):continue
   vector=sum(1<<j for j in cols)|(parity[0]<<count)
   gf2_add(basis,vector)
   if width==1:singles+=1
   else:pairs+=1
 return basis,{"all_source_sample_consistent_singletons":singles,
    "all_source_sample_consistent_pairs":pairs,
    "GF2_pairwise_span_rank":len(basis)}

def features_of_quad(rows,inds):
 counter=np.zeros(16,dtype=np.float64)
 for row in rows:
  bits=(row[inds[0]]<<3)|(row[inds[1]]<<2)|(row[inds[2]]<<1)|(row[inds[3]])
  counter[bits]+=1
 return counter/len(rows)

def evaluate(root,path,expected,net):
 st=time.perf_counter_ns()
 result={"original":path,"frozen_git_blob_sha1":expected,
    "status":"NOT_STARTED","learned_first_source_original_dual_2VC_count":0,
    "strong_classical_first_source_original_dual_2VC_count":0}
 try:
  b=(root/path).read_bytes()
  if blob(b)!=expected:raise RuntimeError("PRESOURCE_BLOB_ID_MISMATCH")
  result["actual_original_bytes_sha256"]=sha(b)
  sex=sexprs(b)
  parsed=compile_typed_original(sex)
  native=compile_independent_native(sex,parsed)
  typed_native={key:dual(z3.Xor(parsed[key],native[key]),"unsat",10)
    for key in ("pre","trans","post")}
  result["original_source_semantic_parity_3VC"]=typed_native
  if not all(q["dual_pass"] for q in typed_native.values()):
   raise RuntimeError("INDEPENDENT_SOURCE_SEMANTIC_PARITY_FAILURE")
  original={**parsed,**native}
  post_uses={str(v) for v in z3.z3util.get_vars(native["post"])}
  eligible=[i for i,(name,sort) in enumerate(parsed["states"])
    if sort=="Bool" and str(parsed["now"][i]) not in post_uses]
  result["source_boolean_states"]=sum(t=="Bool" for _,t in parsed["states"])
  result["eligible_source_boolean_state_indices"]=eligible
  result["source_only_Post_direct_support_mask"]=sorted(
    i for i,v in enumerate(parsed["now"]) if str(v) in post_uses)
  if not (4<=len(eligible)<=32):
   result["status"]="ABSTAIN_SOURCE_ELIGIBLE_BOOL_WIDTH_OUTSIDE_4_32"
   return result
  rows,source_receipt=samples(original,eligible)
  result["original_source_only_64_or_fewer_observed_models"]=len(rows)
  result["original_source_samples_receipt"]=source_receipt
  if len(rows)<8:
   result["status"]="ABSTAIN_NO_DIVERSE_ORIGINAL_SOURCE_STATES"
   return result
  basis,pairs=sample_pairwise_basis(rows,len(eligible))
  result["source_sample_pairwise_upper_bound_on_inductive_span"]=pairs
  # FIRST true trained-model scoring of EVERY four-variable source tuple.
  # Only after all network logits fixed do we compare exact classical.
  queries=[]
  all_compatible=[]
  for cols in itertools.combinations(range(len(eligible)),4):
   feat=features_of_quad(rows,cols)
   prob,_=forward(feat.reshape(1,16),net)
   relation=int(np.argmax(prob[0]))
   if relation not in (1,2):continue
   offset=relation-1
   mask=sum(1<<k for k in cols)|(offset<<len(eligible))
   # The no-pairwise-explanation screen is overapproximated by all
   # sample-consistent pairwise constraints. Never the full gold invariant.
   if gf2_in_span(basis,mask):continue
   cand={"actual_source_bool_index_quad":[eligible[k] for k in cols],
     "relative_eligible_indices":cols,
     "xor4_equals":offset,
     "MLP_probability":round(float(prob[0,relation]),6),
     "source_sample_consistent_all":all(
          sum(row[k] for k in cols)%2==offset for row in rows)}
   queries.append(cand)
  queries.sort(key=lambda z:(-z["MLP_probability"],z["actual_source_bool_index_quad"]))
  result["neural_proposed_outside_sample_pairwise_span_count"]=len(queries)
  verified=[]
  for item in queries[:FIRST_PROPOSALS]:
   expr=xor4(original,eligible,item["relative_eligible_indices"],item["xor4_equals"])
   proofs=preproved_and_source_inductive(original,expr)
   row={k:v for k,v in item.items() if k!="relative_eligible_indices"}
   row.update({"source_bool_xor4_candidate_SMT":expr.sexpr(),
     "real_original_Z3_independent_cvc5_2VC":proofs})
   verified.append(row)
  result["original_first_frozen_learner_48_or_fewer"]=verified
  result["learned_first_source_original_dual_2VC_count"]=sum(
    z["real_original_Z3_independent_cvc5_2VC"]["dual_2vc"] for z in verified)
  # Exact parity-based classical 4-variable search over THE SAME samples.
  # Classifier-free and same 4var/GF2 independence restrictions.
  candidate_cl=[]
  for cols in itertools.combinations(range(len(eligible)),4):
   offset=sum(rows[0][k] for k in cols)%2
   if any(sum(row[k] for k in cols)%2!=offset for row in rows):continue
   mask=sum(1<<k for k in cols)|(offset<<len(eligible))
   if gf2_in_span(basis,mask):continue
   candidate_cl.append((cols,offset))
  result["classical_exact_full_sample_consistent_higher_order_count"]=len(candidate_cl)
  classical=[]
  for quad,offset in candidate_cl[:FIRST_PROPOSALS]:
   expr=xor4(original,eligible,quad,offset)
   proof=preproved_and_source_inductive(original,expr)
   classical.append({"actual_source_bool_index_quad":[eligible[k] for k in quad],
       "xor4_equals":offset,"candidate_SMT":expr.sexpr(),
       "actual_original_Z3_cvc5_2VC":proof})
  result["classical_first_frozen_48_or_fewer"]=classical
  result["strong_classical_first_source_original_dual_2VC_count"]=sum(
    q["actual_original_Z3_cvc5_2VC"]["dual_2vc"] for q in classical)
  result["status"]="COMPLETE_SCOPED_XOR4_FIRST_REAL_ORIGINAL"
 except Exception as exc:
  result["status"]="ABSTAIN_SOURCE_OR_PROOF_FAILURE"
  result["error"]=type(exc).__name__+":"+str(exc)[:330]
 result["wall_ms"]=elapsed(st)
 print("FIRST_SOURCE_XOR4",path,result["status"],
  "LEARNED2VC",result["learned_first_source_original_dual_2VC_count"],
  "CLASSICAL2VC",result["strong_classical_first_source_original_dual_2VC_count"],
  "ERROR",result.get("error"),flush=True)
 return result

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",type=Path,required=True)
 parser.add_argument("--out",type=Path,required=True)
 args=parser.parse_args()
 t=time.perf_counter_ns()
 model,study=learn() # BEFORE any pinned source body is parsed
 print("SYNTH_TRAINED_XOR4_MODEL_SHA",study["first_model_weight_sha256"],
  "HELDOUT",study["learned_test_correct"],
  "SHUFFLE",study["shuffled_train_labels_test_correct"],
  "EXACT",study["unlearned_exact_contingency_test_correct"],flush=True)
 cases=[evaluate(args.root,*entry,model) for entry in ORIGINS]
 report={"schema":"neumann.q3.gateR.learned_compositional_XOR4.first_presource.v1",
   "protocol_pre_source_git_commit":PRESOURCE_COMMIT,
   "first_two_original_file_Git_blobs_frozen_before_source_body_read":True,
   "source_one_author_origin_not_cross_author_disjoint":True,
   "source_free_synthetic_training_before_target_source_read":True,
   "model":study,
   "all_two_source_git_blobs_authenticated":all("actual_original_bytes_sha256" in c for c in cases),
   "learned_independent_real_original_2VC_count":sum(
      c["learned_first_source_original_dual_2VC_count"] for c in cases),
   "strong_classical_independent_real_original_2VC_count":sum(
      c["strong_classical_first_source_original_dual_2VC_count"] for c in cases),
   "new_operator_outside_predeclared_XOR4_grammar":"NOT_DEMONSTRATED",
   "model_genuine_new_author_origin_G1":"NOT_TESTED",
   "no_real_original_Post_goal_downgrade":True,
   "real_published_safety_3VC_from_learned_candidate":"NOT_CLAIMED",
   "global_Q3":"OPEN","gate_R_full":"OPEN","gate_V":"OPEN","global_Q1_Q7":"OPEN",
   "GPU_calls":0,"paid_API_calls":0,"whole_wall_ms_including_training":elapsed(t),
   "cases":cases}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("GATE_R_FIRST_UNOPENED_SOURCE_LEARNED_XOR4_ORIGINAL_2VC",
   report["learned_independent_real_original_2VC_count"])
 print("CLASSICAL_SOURCE_XOR4_ORIGINAL_2VC",
   report["strong_classical_independent_real_original_2VC_count"])
 print("GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":main()
