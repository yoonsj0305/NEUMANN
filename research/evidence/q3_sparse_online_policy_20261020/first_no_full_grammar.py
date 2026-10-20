"""NEUMANN Q3 sparse-online categorical gradient study; fail-closed.
No exhaustive AST reward labels and no gold AST. CPU author-synthetic only.
See docs/research/Q3_SPARSE_ONLINE_POLICY_NEGATIVE_FIRST_CI_FREEZE_20261020.md
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from research.evidence.q3_learned_typed_ast_macro_20261019.train_self_discovered_composition import (
    check_bounded_counter)

SHAPES=[((('p','q'),'r'),'s'),(('p',('q','r')),'s'),
        (('p','q'),('r','s')),('p',(('q','r'),'s')),('p',('q',('r','s')))]
OPS=('+','-','*','div')
LEAVES=('a','b','1')
BUDGET_PRE=2500
BUDGET_POST=500
BATCH=125
EXPLORE=.3
TEMPERATURE=.3
LR=.22
UPDATE_STEPS=7
SEEDS=tuple(range(1,33))

def dataset(moduli,steps):
 a=[];b=[];y=[]
 for k in moduli:
  r=0
  for i in range(steps):
   a.append(i);b.append(k);y.append(r)
   r=0 if r==k-1 else r+1
 return np.asarray(a,dtype=np.int64),np.asarray(b,dtype=np.int64),np.asarray(y,dtype=np.int64)
TRAIN=dataset(range(2,7),48)

def tree(desc):
 shape,ops,leaves=desc;oi=li=0
 def rec(node):
  nonlocal oi,li
  if isinstance(node,str):
   v=leaves[li];li+=1;return ('leaf',v)
  op=ops[oi];oi+=1
  return op,rec(node[0]),rec(node[1])
 return rec(SHAPES[shape])

def print_tree(t):
 if t[0]=='leaf':return LEAVES[t[1]]
 return '('+OPS[t[0]]+' '+print_tree(t[1])+' '+print_tree(t[2])+')'

def calculate(t,a,b):
 if t[0]=='leaf':return (a,b,np.ones_like(a))[t[1]]
 x=calculate(t[1],a,b)
 y=calculate(t[2],a,b)
 with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
  if t[0]==0:v=x+y
  elif t[0]==1:v=x-y
  elif t[0]==2:v=x*y
  else:v=np.floor_divide(x,np.where(y==0,1,y))
 return np.clip(v,-10000,10000)

def evaluate(candidate,source=TRAIN):
 v=calculate(tree(candidate),*source[:2])
 dif=np.abs(v-source[2])
 return float(np.log1p(np.mean(dif))+.1*(1-np.mean(dif==0)))

def heldout(candidate):
 return all(evaluate(candidate,dataset((k,),100))==0 for k in (7,8,9,11))

def draw_uniform(rng):
 return int(rng.integers(5)),tuple(int(x) for x in rng.integers(4,size=3)),tuple(int(x) for x in rng.integers(3,size=4))

def softmax(logits):
 z=logits-np.max(logits,axis=-1,keepdims=True)
 p=np.exp(z)
 return p/p.sum(axis=-1,keepdims=True)

class OnlinePolicy:
 """125 shape-conditional trainable categorical logits with actual Adam updates."""
 def __init__(self):
  self.sh=np.zeros(5)
  self.ops=np.zeros((5,3,4))
  self.leaves=np.zeros((5,4,3))
  self.m=[np.zeros_like(x) for x in (self.sh,self.ops,self.leaves)]
  self.v=[np.zeros_like(x) for x in (self.sh,self.ops,self.leaves)]
  self.updates=0
 def draw(self,rng):
  shape=int(rng.choice(5,p=(1-EXPLORE)*softmax(self.sh)+EXPLORE/5))
  op_probs=(1-EXPLORE)*softmax(self.ops[shape])+EXPLORE/4
  leaf_probs=(1-EXPLORE)*softmax(self.leaves[shape])+EXPLORE/3
  op=tuple(int(rng.choice(4,p=op_probs[j])) for j in range(3))
  leaves=tuple(int(rng.choice(3,p=leaf_probs[j])) for j in range(4))
  return shape,op,leaves
 def update(self,batch):
  vals=np.asarray([loss for candidate,loss in batch])
  weights=np.exp(-(vals-vals.min())/TEMPERATURE)
  weights/=weights.sum()
  shap=np.zeros(5);ops=np.zeros_like(self.ops);leaf=np.zeros_like(self.leaves)
  for (desc,_),w in zip(batch,weights):
   shape,operators,leaves=desc
   shap[shape]+=w
   for j,o in enumerate(operators):ops[shape,j,o]+=w
   for j,k in enumerate(leaves):leaf[shape,j,k]+=w
  arrays=[self.sh,self.ops,self.leaves]
  targets=[shap,ops,leaf]
  for _ in range(UPDATE_STEPS):
   grads=[softmax(a)*np.sum(t,axis=-1,keepdims=True)-t
          for a,t in zip(arrays,targets)]
   self.updates+=1
   for j,(a,g) in enumerate(zip(arrays,grads)):
    self.m[j]=.9*self.m[j]+.1*g
    self.v[j]=.999*self.v[j]+.001*g*g
    a-=LR*(self.m[j]/(1-.9**self.updates))/(
      np.sqrt(self.v[j]/(1-.999**self.updates))+1e-8)
 def digest(self):
  return hashlib.sha256(b''.join(x.astype('>f8').tobytes()
      for x in (self.sh,self.ops,self.leaves))).hexdigest()

def study_one(seed):
 t=time.perf_counter()
 rng=np.random.default_rng(seed)
 model=OnlinePolicy()
 observed=[];pre=[];post=[]
 for start in range(0,BUDGET_PRE,BATCH):
  batch=[]
  for j in range(BATCH):
   candidate=model.draw(rng)
   loss=evaluate(candidate)
   if loss==0:pre.append((start+j+1,candidate))
   batch.append((candidate,loss))
  observed.extend(batch)
  model.update(batch)
 digest=model.digest()
 for j in range(BUDGET_POST):
  candidate=model.draw(rng)
  loss=evaluate(candidate)
  if loss==0:post.append((j+1,candidate))
  observed.append((candidate,loss))
 baseline=np.random.default_rng(seed+100000)
 uni=[]
 for j in range(BUDGET_PRE+BUDGET_POST):
  candidate=draw_uniform(baseline)
  if evaluate(candidate)==0:uni.append((j+1,candidate))
 best=post[0][1] if post else pre[0][1] if pre else None
 return {"seed":seed,"cap":BUDGET_PRE+BUDGET_POST,
   "actual_evaluations":len(observed),
   "distinct_learned_ast":len({d for d,_ in observed}),
   "pre_freeze_exact_count":len(pre),
   "post_freeze_exact_count":len(post),
   "pre_freeze_first_exact":pre[0][0] if pre else None,
   "post_freeze_first_exact":post[0][0] if post else None,
   "positive_ast":(best[0],list(best[1]),list(best[2])) if best else None,
   "positive_program":print_tree(tree(best)) if best else None,
   "source_only_synthetic_heldout_all_k":heldout(best) if best else None,
   "uniform_full_budget_found":bool(uni),
   "uniform_first_exact":uni[0][0] if uni else None,
   "policy_adam_updates":model.updates,
   "policy_weight_sha256_after_pre_freeze":digest,
   "paired_both_arms_wall_s":round(time.perf_counter()-t,4)}

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--out',type=Path,required=True)
 args=p.parse_args()
 rows=[study_one(k) for k in SEEDS]
 positives=[v for v in rows if v["positive_ast"] is not None]
 source_certificate=None
 if positives:
  d=positives[0]["positive_ast"]
  ast=tree((d[0],tuple(d[1]),tuple(d[2])))
  # Full real Z3 and independent official pinned cvc5 1.4.2 for
  # unmodified synthetic original source Pre, Trans, Post on heldout k.
  results=[check_bounded_counter(k,ast,ast) for k in (7,8,9,11)]
  source_certificate={"original_synthetic_holdout_dual_solver":results,
   "all_cvc5_Z3_3VC_verified":all(x["all_original_three_vcs_dual_proved"] for x in results),
   "source_from_positive_seed":positives[0]["seed"],
   "source_discovered_pre_freeze":positives[0]["pre_freeze_exact_count"]>0}
 else:source_certificate={"all_cvc5_Z3_3VC_verified":False}
 learned=sum(x["positive_ast"] is not None for x in rows)
 random_count=sum(x["uniform_full_budget_found"] for x in rows)
 post=sum(x["post_freeze_exact_count"]>0 for x in rows)
 post_novel=sum(x["post_freeze_exact_count"]>0 and not x["pre_freeze_exact_count"] for x in rows)
 report={"schema":"neumann.q3.sparse-online-gradient.v1",
  "science_scope":"DEVELOPMENT_ONLY_SYNTHETIC; no first-neural-only proven invention",
  "train_data_synthetic_source_count":240,
  "equal_evaluation_budget_per_arm":BUDGET_PRE+BUDGET_POST,
  "learned_search_before_freeze":BUDGET_PRE,
  "learned_search_after_freeze":BUDGET_POST,
  "fixed_seeds":list(SEEDS),"full_25920_candidate_pre_evaluation":False,
  "program_target_AST_given":False,
  "model_is_shape_conditional_125_parameter_policy":True,
  "policy_parameter_update_is_adam_gradient_from_executed_candidate_rewards_only":True,
  "learned_exact_any_seeds":learned,
  "uniform_exact_any_seeds":random_count,
  "learned_exact_post_freeze_seeds":post,
  "learned_new_exact_post_freeze_with_no_pre_exact_seeds":post_novel,
  "all_correct_proposals_from_exact_source_experience":True,
  "first_positive_synthetic_Z3_cvc5_certificates":source_certificate,
  "explicit_no_neural_advantage":learned<=random_count,
  "science_verdict":"FAIL_NO_SPARSE_POLICY_ADVANTAGE" if learned<=random_count else
    "DEV_ONLY_OBSERVED_EDGE_NOT_A_BLIND_PROOF",
  "theorem_about_all_neural_policies":False,
  "real_external_original_fresh_blind":False,
  "unique_new_mathematical_primitive_not_in_DSL":False,
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "GPU_calls":0,"paid_API_calls":0,"cases":rows}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print("LEARNED_EXACT_ANY",learned,"UNIFORM_EXACT_ANY",random_count)
 print("LEARNED_POST_FREEZE",post,"NOVEL_AFTER_FREEZE",post_novel)
 print("ORIGINAL_Z3_CVC5",source_certificate["all_cvc5_Z3_3VC_verified"])
 print("SCIENTIFIC_VERDICT",report["science_verdict"])
 print("Q3_GLOBAL",report["global_Q3"])

if __name__=="__main__":main()
