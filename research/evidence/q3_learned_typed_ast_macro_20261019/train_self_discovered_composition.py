"""Q3 compositional AST macro, first complete source-bound CI experiment.
First AST FOUND by UNTRAINED stochastic grammar search, NOT by gradient learning.
Then 29-param gradient-trained categorical decoder SELF-DISTILLS the found
expression and reuses it on heldout synthetic cases and opened real original.
A complete exact classical grammar search also solves the same problem.
NO global Q3 or novel primitive claim is made.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,subprocess,time
from pathlib import Path
import numpy as np
import z3
from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,
  check_formula,source_proof,_obligations)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

SHAPES=[((('p','q'),'r'),'s'),(('p',('q','r')),'s'),
 (('p','q'),('r','s')),('p',(('q','r'),'s')),('p',('q',('r','s')))]
OPS=('+','-','*','div')
LEAVES=('a','b','one')
SEED=20261019
TRAIN_K=(2,3,4,5,6)
TEST_K=(7,8,9,11)
ORIG="benchmarks/NIA/2016.ATVA_PILAT/mannadiv.sl"
ORIG_BLOB="8530c3a189403f14db1f505820a65e92ba876193"
EXPECTED={"initial":"unsat","consecution":"unsat","post":"unsat"}
def ms(t):return round((time.perf_counter_ns()-t)/1e6,3)
def tree(desc):
 shape,ops,leaves=desc;oi=li=0
 def rec(node):
  nonlocal oi,li
  if isinstance(node,str):
   v=leaves[li];li+=1
   return ('leaf',v)
  v=ops[oi];oi+=1
  return (v,rec(node[0]),rec(node[1]))
 return rec(SHAPES[shape])
def ast_string(t):
 if t[0]=="leaf":return LEAVES[t[1]]
 return f"({OPS[t[0]]} {ast_string(t[1])} {ast_string(t[2])})"
def evaluate(t,a,b):
 if t[0]=="leaf":return (a,b,np.ones_like(a))[t[1]]
 x=evaluate(t[1],a,b);y=evaluate(t[2],a,b)
 with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
  value=(x+y if t[0]==0 else x-y if t[0]==1 else x*y if t[0]==2
         else np.where(y==0,999999,np.floor_divide(x,np.where(y==0,1,y))))
 return np.clip(value,-999999,999999)
def z3_ast(t,a,b):
 if t[0]=="leaf":return (a,b,z3.IntVal(1))[t[1]]
 x=z3_ast(t[1],a,b);y=z3_ast(t[2],a,b)
 if t[0]==0:return x+y
 if t[0]==1:return x-y
 if t[0]==2:return x*y
 return x/y
def all_programs():
 return [(shape,ops,leaf) for shape in range(5)
  for ops in itertools.product(range(4),repeat=3)
  for leaf in itertools.product(range(3),repeat=4)]
def recurrence_data(moduli,steps):
 """Outputs come ONLY from a published recurrence, not from modulo or gold AST."""
 aa=[];bb=[];rr=[]
 for k in moduli:
  state=0
  for i in range(steps):
   aa.append(i);bb.append(k);rr.append(state)
   state=0 if state==k-1 else state+1
 return (np.array(aa,dtype=np.int64),np.array(bb,dtype=np.int64),
  np.array(rr,dtype=np.int64))
def discover(data,proposals):
 a,b,y=data
 for attempts,desc in enumerate(proposals,1):
  if np.array_equal(evaluate(tree(desc),a,b),y):
   return attempts,desc
 return None,None

class LearnedDecoder:
 """29 trainable one-layer categorical logits; exact CPU Adam backprop."""
 def __init__(self):
  self.logits=[np.zeros(5),*[np.zeros(4) for _ in range(3)],
    *[np.zeros(3) for _ in range(4)]]
 def indices(self,d):return [d[0],*d[1],*d[2]]
 def greedy(self):
  ix=[int(np.argmax(v)) for v in self.logits]
  return (ix[0],tuple(ix[1:4]),tuple(ix[4:8]))
 def neglog(self,d):
  loss=0.
  for v,j in zip(self.logits,self.indices(d)):
   s=v-v.max();loss+=float(np.log(np.exp(s).sum())-s[j])
  return loss
 def train_on_self_discovered(self,d,updates=100,rate=0.2):
  moment=[np.zeros_like(x) for x in self.logits]
  variance=[np.zeros_like(x) for x in self.logits]
  loss0=self.neglog(d)
  t=time.perf_counter_ns()
  for iteration in range(1,updates+1):
   for j,(logits,k) in enumerate(zip(self.logits,self.indices(d))):
    probs=np.exp(logits-logits.max());probs/=probs.sum()
    grad=probs;grad[k]-=1
    moment[j]=.9*moment[j]+.1*grad
    variance[j]=.999*variance[j]+.001*grad*grad
    logits-=rate*(moment[j]/(1-.9**iteration))/(
      np.sqrt(variance[j]/(1-.999**iteration))+1e-8)
  return {"gradient_updates":updates,"trainable_parameters":29,
    "gradient_optimizer":"pure numpy analytic Adam gradients",
    "loss_before":round(loss0,9),"loss_after":round(self.neglog(d),9),
    "training_component_ms":ms(t)}
 def weight_sha256(self):
  return hashlib.sha256(b"".join(v.astype(">f8").tobytes()
                        for v in self.logits)).hexdigest()

def independent_cvc5(script,seconds=7):
 t=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=smt2","--decision=internal",
    f"--tlimit-per={seconds*1000}","-"],
    input=script,text=True,capture_output=True,timeout=seconds+4,check=False)
  lines=[z.strip() for z in p.stdout.splitlines() if z.strip()]
  return {"status":lines[-1] if lines else "EMPTY",
    "returncode":p.returncode,"wall_ms":ms(t),"stderr_excerpt":p.stderr[:150]}
 except Exception as e:
  return {"status":"NO_RESULT","error":str(e)[:180],"wall_ms":ms(t)}

def check_bounded_counter(k,model_ast,classic_ast):
 i,r,ni,nr=z3.Ints(f"i_{k} r_{k} i_next_{k} r_next_{k}")
 pre=z3.And(i==0,r==0)
 trans=z3.And(ni==i+1,nr==z3.If(r==k-1,0,r+1))
 post=r==i%k
 expression=z3_ast(model_ast,i,z3.IntVal(k))
 bounds=z3.And(i>=0,r>=0,r<k)
 inv=z3.And(bounds,r==expression)
 newer=z3.substitute(inv,(i,ni),(r,nr))
 conditions={"initial":z3.And(pre,z3.Not(inv)),
   "consecution":z3.And(inv,trans,z3.Not(newer)),
   "post":z3.And(inv,z3.Not(post))}
 z3out={};external={}
 for name,pred in conditions.items():
  solver=z3.Solver();solver.set(timeout=3000)
  solver.add(pred);z3out[name]=str(solver.check())
  if z3out[name]=="unsat":
   external[name]=independent_cvc5(solver.to_smt2(),seconds=8)
  else:external[name]={"status":"NOT_RUN_DUE_TO_Z3_FAIL"}
 control=z3.Solver();control.set(timeout=2000)
 control.add(bounds,z3.Not(post))
 helper_only=str(control.check())
 comp=z3.Solver();comp.set(timeout=2500)
 comp.add(z3.And(bounds,r==z3_ast(classic_ast,i,z3.IntVal(k))),z3.Not(post))
 classical_proof=str(comp.check())
 return {"k":k,"neural_original_z3_three_vc":z3out,
   "independent_cvc5_three_vc":external,
   "helper_only_post_bad_is_sat":helper_only=="sat",
   "same_info_classical_macro_implies_post":classical_proof=="unsat",
   "all_original_three_vcs_dual_proved":z3out==EXPECTED and
     set(external)==set(EXPECTED) and all(v.get("status")=="unsat"
       and v.get("returncode")==0 for v in external.values())}

def original_transfer(root,model_ast,classic_ast):
 path=root/ORIG;raw=path.read_bytes()
 blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
 if blob!=ORIG_BLOB:raise ValueError("EXTERNAL_REAL_ORIGINAL_BLOB_MISMATCH")
 forms=sexprs(raw);original=extract_mixed_original(forms)
 nat=native_original_relations(forms,original)
 nat.update({"now":original["now"],"next":original["next"]})
 parity=check_parity(original,nat)
 if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
  raise ValueError("EXTERNAL_REAL_ORIGINAL_PRE_TRANS_POST_PARITY_MISMATCH")
 if len(original["now"])!=5 or original["num_bool"]!=0:
  raise ValueError("REAL_ORIGINAL_STATE_ARITY_MISMATCH")
 x1,x2,y1,y2,y3=original["now"]
 # This original-source bilinear conservation relation is ALREADY CLASSICALLY
 # KNOWN from PR #295. It is NOT invented by the frozen policy here.
 base=z3.And(x1==x2*y1+y2+y3,x2>0,y3>=0,y2>=0,y2<x2)
 original_proof=source_proof(base,nat)
 macro_relation=y2==z3_ast(model_ast,x1-y3,x2)
 clas_relation=y2==z3_ast(classic_ast,x1-y3,x2)
 outs={}
 for nm,predicate in (("neural_macro_consequence",z3.And(base,z3.Not(macro_relation))),
    ("classical_macro_consequence",z3.And(base,z3.Not(clas_relation)))):
  solver=z3.Solver();solver.set(timeout=5000)
  solver.add(predicate)
  status=str(solver.check())
  ext=independent_cvc5(solver.to_smt2(),seconds=15) if status=="unsat" else {"status":"NOT_RUN"}
  outs[nm]={"native_Z3":status,"independent_cvc5":ext}
 candidate=z3.And(base,macro_relation)
 stronger=source_proof(candidate,nat)
 external_cert=None
 if stronger["accepted"]:
  checked=check_original_candidate(path,candidate.sexpr(),
    expected_source_sha256=hashlib.sha256(raw).hexdigest())
  external_cert={"status":checked.get("status"),
    "cvc5_original_three_vc":checked.get("cvc5_original_three_vc")}
 return {"original_source":ORIG,"source_sha256":hashlib.sha256(raw).hexdigest(),
  "original_semantic_parity":parity,
  "previously_known_source_base_3VC":original_proof["vcs"],
  "transferred_macro_derived_lemma":outs,
  "augmented_original_Z3_three_vc":stronger["vcs"],
  "augmented_original_independent_cvc5_3s":external_cert,
  "genuinely_new_blind_source":False}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--original-root",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 train=recurrence_data(TRAIN_K,48)
 complete=all_programs()
 if len(complete)!=25920:raise AssertionError("PROGRAM_SPACE_WRONG")
 rng=np.random.default_rng(SEED)
 t=time.perf_counter_ns()
 randomized=[complete[int(j)] for j in rng.permutation(len(complete))]
 r,found=discover(train,randomized)
 search_ms=ms(t)
 if found is None:raise AssertionError("UNTRAINED_SYMBOLIC_DISCOVERY_FAILED")
 model=LearnedDecoder()
 initial_greedy=model.greedy()
 initial_good=np.array_equal(evaluate(tree(initial_greedy),*train[:2]),train[2])
 train_metrics=model.train_on_self_discovered(found)
 frozen=model.greedy()
 decoded_ast=tree(frozen)
 if not np.array_equal(evaluate(decoded_ast,*train[:2]),train[2]):
  raise AssertionError("LEARNED_POLICY_FROZEN_GREEDY_REPRODUCTION_FAIL")
 t=time.perf_counter_ns()
 classical_n,classical_candidate=discover(train,complete)
 classical_ms=ms(t)
 if classical_candidate is None:raise AssertionError("EXACT_CLASSICAL_BASELINE_MISSING")
 counters=[]
 for k in TEST_K:
  sample=recurrence_data((k,),100)
  neural_fit=np.array_equal(evaluate(decoded_ast,*sample[:2]),sample[2])
  classical_fit=np.array_equal(evaluate(tree(classical_candidate),*sample[:2]),sample[2])
  proof=check_bounded_counter(k,decoded_ast,tree(classical_candidate))
  counters.append({**proof,"heldout_source_states":len(sample[0]),
    "trained_policy_prediction_exact":bool(neural_fit),
    "full_classical_prediction_exact":bool(classical_fit)})
 real=original_transfer(a.original_root,decoded_ast,tree(classical_candidate))
 good=all(x["trained_policy_prediction_exact"] and
          x["full_classical_prediction_exact"] and
          x["all_original_three_vcs_dual_proved"] and
          x["helper_only_post_bad_is_sat"] and
          x["same_info_classical_macro_implies_post"] for x in counters)
 out={"schema":"neumann.q3.self_discovered_neural_ast_macro.posthoc.v1",
  "initial_grammar_primitives":{"ops":list(OPS),"leaves":list(LEAVES),
       "binary_tree_operators":3,"programs_complete_closure":len(complete),
       "has_mod_operator":False},
  "synthetic_training_programs":list(TRAIN_K),"synthetic_train_rows":len(train[0]),
  "search_finding_credit":"UNTRAINED_UNIFORM_SYMBOLIC_SEARCH, NOT NEURAL",
  "search_random_seed":SEED,
  "untrained_symbolic_first_exact_program_rank":r,
  "untrained_symbolic_search_component_ms":search_ms,
  "discovered_macro":ast_string(tree(found)),
  "policy_metrics":train_metrics,
  "greedy_untrained_correct":bool(initial_good),
  "trained_greedy_ast":ast_string(decoded_ast),
  "trained_greedy_exact_discovered_structure":frozen==found,
  "trained_weights_sha256":model.weight_sha256(),
  "matched_complete_classical_first_rank":classical_n,
  "matched_complete_classical_discovery_component_ms":classical_ms,
  "matched_complete_classical_ast":ast_string(tree(classical_candidate)),
  "no_gold_AST_supplied_as_training_label":True,
  "neural_training_uses_self_discovered_symbolic_pseudolabel":True,
  "synthetic_holdout":counters,
  "external_original_posthoc_transfer":real,
  "synthetic_scope_pass":good and not initial_good and frozen==found,
  "new_composite_macro_absent_from_primitive_library":True,
  "neural_learned_to_reuse_source_discovered_macro":True,
  "learned_neural_discovered_initial_macro_without_symbolic_search":False,
  "new_mathematical_primitive_outside_complete_grammar":False,
  "strong_matched_classical_also_solves":True,
  "real_external_original_fresh_blind":False,
  "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "GPU_calls":0,"paid_API_calls":0}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print("DISCOVERY",r,"COMPOSITE_MACRO",out["discovered_macro"])
 print("GRADIENT_UPDATES",train_metrics["gradient_updates"],"TRAINED_POLICY_FROZEN",out["trained_weights_sha256"])
 print("CLASSICAL_FIRST",classical_n,out["matched_complete_classical_ast"])
 for x in counters:print("SYNTHETIC_HELDOUT",x["k"],x["all_original_three_vcs_dual_proved"])
 print("REAL_OPENED_ORIGINAL_LEMMA",real["transferred_macro_derived_lemma"])
 print("SCOPED_SYNTHETIC_COMPOSITION_PASS",out["synthetic_scope_pass"])
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
