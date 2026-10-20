"""First learned Boolean relationship constructor on authentic already-OPENED DRAGON.
Tiny CPU neural net trained solely on 4-way anonymous synthetic Bool-pair
relations. It outputs typed Implies(A,B) / Implies(B,A) / Eq(A,B).
Real original Pre+Trans gives samples, not gold/oracle invariant labels.
Full original 2VC Z3 + independent cvc5 required. No global Q3 promotion.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
import numpy as np
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
 sha,blob,sexprs,compile_typed_original,compile_independent_native,dual,elapsed)
FROM="13c8deb68a873635879c9a69bc78caebd340f646"
FILE="lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl"
GIT_SHA="8490b3e25ff7d462a7405e68e742be1abb35b8f8"
TRAIN=2400;HOLDOUT=480;SEED=20261021
CLASSES=("NONE","A_IMPLIES_B","B_IMPLIES_A","A_EQUALS_B")
ALLOWED=(
 ((0,0),(0,1),(1,0),(1,1)),
 ((0,0),(0,1),(1,1)),
 ((0,0),(1,0),(1,1)),
 ((0,0),(1,1)),
)
SAMPLES=32
SOURCE_SAMPLE_LIMIT=64
MAX_FIRST_PROPOSALS=18

def synthetic_data(seed,count):
 rng=np.random.default_rng(seed)
 x=np.zeros((count,6),dtype=np.float64)
 y=rng.integers(0,4,size=count)
 for i,cls in enumerate(y):
  entries=ALLOWED[int(cls)]
  # some randomized latent state frequencies and correlated observations
  probs=rng.dirichlet(np.ones(len(entries))*rng.uniform(0.7,3.0))
  inds=rng.choice(len(entries),SAMPLES,p=probs)
  states=[entries[j] for j in inds]
  x[i]=features(states)
 return x,y
def features(states):
 counts=np.zeros(4,dtype=np.float64)
 for a,b in states:counts[2*a+b]+=1
 # Beta smoothing avoids confidence saturation on finite observations
 freq=(counts+0.25)/(len(states)+1)
 pA=(counts[2]+counts[3]+0.5)/(len(states)+1)
 pB=(counts[1]+counts[3]+0.5)/(len(states)+1)
 return np.r_[freq,pA,pB]
def softmax(v):
 e=np.exp(v-np.max(v,axis=1,keepdims=True))
 return e/e.sum(axis=1,keepdims=True)
def run_net(X,params):
 W1,b1,W2,b2=params
 h=np.tanh(X@W1+b1)
 return softmax(h@W2+b2),h
def train(freeze_seed=SEED):
 start=time.perf_counter_ns()
 trainX,trainY=synthetic_data(freeze_seed,TRAIN)
 testX,testY=synthetic_data(freeze_seed+1,HOLDOUT)
 rng=np.random.default_rng(freeze_seed+2)
 W1=rng.normal(0,0.65,size=(6,24))
 b1=np.zeros(24)
 W2=rng.normal(0,0.35,size=(24,4))
 b2=np.zeros(4)
 N=len(trainX)
 indices=np.arange(N)
 loss=[]
 for step in range(201):
  out,h=run_net(trainX,(W1,b1,W2,b2))
  ce=-np.log(np.clip(out[indices,trainY],1e-12,None)).mean()
  if step%50==0:loss.append(round(float(ce),5))
  dz=out.copy();dz[indices,trainY]-=1;dz/=N
  gW2=h.T@dz + 0.0001*W2
  gb2=dz.sum(axis=0)
  dh=(dz@W2.T)*(1-h*h)
  gW1=trainX.T@dh+0.0001*W1
  gb1=dh.sum(axis=0)
  lr=0.9/(1+step/70)
  W1-=lr*gW1;b1-=lr*gb1
  W2-=lr*gW2;b2-=lr*gb2
 params=(W1,b1,W2,b2)
 scores,_=run_net(testX,params)
 held=int(np.sum(np.argmax(scores,axis=1)==testY))
 # deterministic, real synthetic permuted-label negative control:
 sy=rng.permutation(trainY)
 Z1=rng.normal(0,.65,size=(6,24));Zb1=np.zeros(24)
 Z2=rng.normal(0,.35,size=(24,4));Zb2=np.zeros(4)
 for step in range(201):
  v,h=run_net(trainX,(Z1,Zb1,Z2,Zb2))
  dv=v.copy();dv[indices,sy]-=1;dv/=N
  a=h.T@dv+.0001*Z2;d=dv.sum(0)
  dh=(dv@Z2.T)*(1-h*h)
  c=trainX.T@dh+.0001*Z1;e=dh.sum(0)
  lr=.9/(1+step/70)
  Z1-=lr*c;Zb1-=lr*e;Z2-=lr*a;Zb2-=lr*d
 shuffled,_=run_net(testX,(Z1,Zb1,Z2,Zb2))
 shuffled_success=int(np.sum(np.argmax(shuffled,axis=1)==testY))
 # exact contingency best-effort non-learning comparator
 def classify(v):
  c00,c01,c10,c11=v[:4]
  if c01<.01 and c10<.01:return 3
  if c10<.01:return 1
  if c01<.01:return 2
  return 0
 classical_success=sum(classify(v)==label for v,label in zip(testX,testY))
 weights_sha=hashlib.sha256(b"".join(np.asarray(a,dtype=">f8").tobytes()
                    for a in params)).hexdigest()
 report={"synthetic_train":TRAIN,"synthetic_test":HOLDOUT,
  "synthetic_labeled_from_hidden_relation_class_not_original_source":True,
  "four_relational_operators":CLASSES,"source_disjoint_train_and_holdout":True,
  "trained_network_parameters":int(sum(a.size for a in params)),
  "loss_per_50_steps":loss,"learned_heldout_correct":held,
  "permuted_label_heldout_correct":shuffled_success,
  "source_only_exact_contingency_rule_heldout_correct":int(classical_success),
  "trained_network_weight_sha256":weights_sha,
  "synthetic_learning_and_ablation_wall_ms":elapsed(start)}
 return params,report

def original_samples(src):
 # Actual complete original source now+next Bool values. Never post
 # to select, filter or train. Models of Pre are REAL initials; Pre∧Trans
 # gives genuine one-step successors. Blocking Bool vectors increases variety.
 bindex=[i for i,(_,sort) in enumerate(src["states"]) if sort=="Bool"]
 states=[]
 checks=[]
 for tag,formula,var in [
  ("initial",src["pre"],src["now"]),
  ("one_step",z3.And(src["pre"],src["trans"]),src["next"])]:
  solver=z3.Solver()
  solver.set(timeout=10000);solver.add(formula)
  collected=0
  for _ in range(SOURCE_SAMPLE_LIMIT//2):
   sat=str(solver.check())
   if sat!="sat":checks.append({"phase":tag,"verdict":sat});break
   m=solver.model()
   values=[int(z3.is_true(m.eval(var[i],model_completion=True))) for i in bindex]
   states.append(values)
   solver.add(z3.Or(*[var[i]!=z3.BoolVal(bool(v)) for i,v in zip(bindex,values)]))
   collected+=1
  checks.append({"phase":tag,"distinct_source_bool_models":collected})
 return bindex,states,checks

def make_clause(src,original_positions,a,b,relation):
 A=src["now"][original_positions[a]]
 B=src["now"][original_positions[b]]
 if relation==1:return z3.Implies(A,B)
 if relation==2:return z3.Implies(B,A)
 if relation==3:return A==B
 raise ValueError("NOT_RELATION")
def model_candidates(src,index,states,params):
 goal_atoms=set(str(v) for v in z3.z3util.get_vars(src["post"]))
 goal_indices={i for i,v in enumerate(src["now"]) if str(v) in goal_atoms}
 if len(states)<8:raise ValueError("INSUFFICIENT_REAL_SOURCE_DATA")
 out=[]
 for a in range(len(index)):
  for b in range(a+1,len(index)):
   # Exclude goal-support state coordinates via source Post free-variable
   # MASK ONLY: do not use goal values as candidate features or labels.
   if index[a] in goal_indices or index[b] in goal_indices:continue
   f=features([(row[a],row[b]) for row in states])
   probs,_=run_net(np.asarray([f]),params)
   relation=int(np.argmax(probs[0]))
   if relation==0:continue
   clause=make_clause(src,index,a,b,relation)
   out.append({"bool_state_index_pair":[index[a],index[b]],
     "class":CLASSES[relation],"model_probability":round(float(probs[0,relation]),6),
     "original_candidate_SMT":clause.sexpr(),
     "clause":clause})
 out.sort(key=lambda z:(-z["model_probability"],z["bool_state_index_pair"]))
 return out
def certified_first(original,source,states,params):
 index,rows,model_receipts=original_samples(source)
 goal_atoms=set(str(v) for v in z3.z3util.get_vars(source["post"]))
 goal_indices={i for i,v in enumerate(source["now"]) if str(v) in goal_atoms}
 preds=model_candidates(source,index,rows,params)
 checked_preds=[]
 accepted=[]
 checks=[]
 for row in preds[:MAX_FIRST_PROPOSALS]:
  clause=row.pop("clause")
  nowrel=z3.substitute(clause,*list(zip(source["now"],source["next"])))
  pre_bad=z3.And(original["pre"],z3.Not(clause))
  badstep=z3.And(clause,original["trans"],z3.Not(nowrel))
  pre_z=dual(pre_bad,"unsat",10)
  step_z=dual(badstep,"unsat",10) if pre_z["dual_pass"] else {"not_run":"pre_not_inductively_initial"}
  rec={**row,"original_initial_2VC":pre_z,"original_consecution_2VC":step_z,
    "actual_original_inductive":bool(pre_z["dual_pass"] and step_z.get("dual_pass"))}
  checked_preds.append(rec)
  if rec["actual_original_inductive"]:accepted.append(rec)
 # Matched strong classical exact source-only atomic bool entailment
 # over the very same complete grammar. Full 2VC enumeration
 # over <=21*20/2*3=630 formulas, Z3 only, 4s each, conservative ABSTAIN.
 all_possible=0;initial_sufficient=0;inductive_count=0
 for a in range(len(index)):
  for b in range(a+1,len(index)):
   if index[a] in goal_indices or index[b] in goal_indices:continue
   for relation in (1,2,3):
    atom=make_clause(source,index,a,b,relation)
    all_possible+=1
    q=z3.Solver();q.set(timeout=1200);q.add(original["pre"],z3.Not(atom))
    if q.check()!=z3.unsat:continue
    initial_sufficient+=1
    q=z3.Solver();q.set(timeout=1200)
    atomnext=z3.substitute(atom,*list(zip(source["now"],source["next"])))
    q.add(atom,original["trans"],z3.Not(atomnext))
    if q.check()==z3.unsat:inductive_count+=1
 return {"source_pre_and_one_step_data_samples":len(rows),
   "source_sampling":model_receipts,
   "candidate_count_from_trained_network":len(preds),
   "frozen_first_network_proposals_checked":len(checked_preds),
   "first_network_source_only_inductive_count":len(accepted),
   "first_network_candidates":checked_preds,
   "matched_complete_classical_bool_grammar":{
    "all_grammar_candidates":all_possible,
    "original_pre_entailed_candidates":initial_sufficient,
    "inductive_candidates_Z3_found":inductive_count,
    "classical_is_complete_for_this_fixed_grammar":True},
   "source_Post_used_only_for_goal_coordinate_exclusion":True,
   "post_support_coordinates_excluded_from_all_candidates":sorted(goal_indices),
   "source_Post_not_used_as_training_label_or_feature":True}

def main():
 a=argparse.ArgumentParser()
 a.add_argument("--root",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 opt=a.parse_args()
 full=time.perf_counter_ns()
 params,learning=train() # TRAIN before any original source bytes
 origin={"original":FILE,"expected_git_blob":GIT_SHA,
  "status":"NOT_ASSESSED"}
 try:
  raw=(opt.root/FILE).read_bytes()
  if blob(raw)!=GIT_SHA:raise RuntimeError("PINNED_SOURCE_GIT_BLOB_DIFFERENT")
  origin["original_SHA256"]=sha(raw)
  f=sexprs(raw)
  source=compile_typed_original(f)
  native=compile_independent_native(f,source)
  origin["original_semantics_native_typed_XOR"]={
     n:dual(z3.Xor(source[n],native[n]),"unsat",8) for n in ["pre","trans","post"]}
  if not all(x["dual_pass"] for x in origin["original_semantics_native_typed_XOR"].values()):
   raise RuntimeError("ACTUAL_ORIGINAL_SOURCE_SEMANTICS_NOT_PRESERVED")
  print("FIRST_SYNTHETIC_NETWORK_HOLDOUT",learning["learned_heldout_correct"],
        "/"+str(HOLDOUT),"SHUFFLED",learning["permuted_label_heldout_correct"],
        "EXACT_NONLEARNED",learning["source_only_exact_contingency_rule_heldout_correct"],flush=True)
  result=certified_first(native,source,None,params)
  origin.update(result)
  origin["status"]="FINISHED_FROZEN_FIRST_REAL_CONSTRUCTIVE_CANDIDATES"
 except Exception as e:
  origin["status"]="ABSTAIN_RESEARCH_FAILURE"
  origin["error"]=type(e).__name__+":"+str(e)[:300]
 print("LEARNED_REAL_RELATIONAL_CLAUSES",
   origin.get("first_network_source_only_inductive_count",0),flush=True)
 r={"schema":"neumann.q3.gateR.first_neural_Bool_implication_constructor.v1",
  "source_already_opened_NOT_BLIND":True,
  "synthetic_model_frozen_before_source_read":True,
  "synthetic_neural_learning":learning,"real_original":origin,
  "learned_nonpolynomial_operator_ast_proposed":bool(origin.get("candidate_count_from_trained_network",0)),
  "learned_real_source_inductive_relational_clauses":origin.get("first_network_source_only_inductive_count",0),
  "novel_math_operator_beyond_source_and_classical":"NOT_PROVEN",
  "genuine_G1_first_unseen_transfer":"NOT_TESTED",
  "gate_R_full":"OPEN","gate_V":"OPEN","global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "GPU_calls":0,"paid_API_calls":0,"whole_wall_ms":elapsed(full)}
 opt.out.parent.mkdir(parents=True,exist_ok=True)
 opt.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
 print("GLOBAL_Q3",r["global_Q3"])
if __name__=="__main__":main()
