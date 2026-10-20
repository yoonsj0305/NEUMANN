"""Q3 behavioral-score-trained shape-conditional AST first proposal (NO gold AST).
Important attribution: candidate behavior of ALL 25,920 DSL ASTs is classically
enumerated for reward. Learned AST selection is NOT beyond exact classical.
No external fresh-blind benchmark. All science boundaries fixed in doc.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from research.evidence.q3_learned_typed_ast_macro_20261019.train_self_discovered_composition import (
 all_programs,tree,evaluate,ast_string,recurrence_data,check_bounded_counter,TRAIN_K,TEST_K)

TEMP=0.02
LR=0.2
UPDATES=80
SEED=20261020
def elapsed(t):return round((time.perf_counter_ns()-t)/1e6,3)
def grammar_evaluation(source,programs):
 """Exhaustively evaluates every DSL candidate: a classical, not neural, step."""
 start=time.perf_counter_ns()
 a,b,labels=source
 mat=np.empty((len(programs),len(labels)),dtype=np.int32)
 losses=np.empty(len(programs),dtype=np.float64)
 for i,p in enumerate(programs):
  vals=evaluate(tree(p),a,b)
  mat[i]=vals
  err=np.abs(vals-labels)
  losses[i]=float(np.log1p(np.mean(err)))+0.1*(1-float(np.mean(err==0)))
 return losses,mat,elapsed(start)
def behavior_posterior(loss):
 """Posterior from observed behavioral error only. Never selects a gold AST."""
 logw=-(loss-loss.min())/TEMP
 weights=np.exp(logw)
 return weights/weights.sum()
def sufficient_stats(posterior,programs):
 s=np.zeros(5)
 op=np.zeros((5,3,4))
 leaf=np.zeros((5,4,3))
 op_ind=np.zeros((3,4))
 leaf_ind=np.zeros((4,3))
 for weight,desc in zip(posterior,programs):
  if weight<1e-30:continue
  sh,ops,lv=desc
  s[sh]+=weight
  for j,x in enumerate(ops):op[sh,j,x]+=weight;op_ind[j,x]+=weight
  for j,x in enumerate(lv):leaf[sh,j,x]+=weight;leaf_ind[j,x]+=weight
 return s,op,leaf,op_ind,leaf_ind

class ConditionalPolicy(torch.nn.Module):
 def __init__(self):
  super().__init__()
  self.shape=torch.nn.Parameter(torch.zeros(5,dtype=torch.float64))
  self.ops=torch.nn.Parameter(torch.zeros((5,3,4),dtype=torch.float64))
  self.leaves=torch.nn.Parameter(torch.zeros((5,4,3),dtype=torch.float64))
 def greedy(self):
  sh=int(self.shape.detach().argmax().item())
  ops=tuple(int(x) for x in self.ops[sh].detach().argmax(-1).tolist())
  leaves=tuple(int(x) for x in self.leaves[sh].detach().argmax(-1).tolist())
  return sh,ops,leaves
 def loss(self,stats):
  shapes,ops,leaves,_,_=stats
  sh=torch.tensor(shapes,dtype=torch.float64)
  ow=torch.tensor(ops,dtype=torch.float64)
  lw=torch.tensor(leaves,dtype=torch.float64)
  return -(sh*F.log_softmax(self.shape,-1)).sum() - (
    ow*F.log_softmax(self.ops,-1)).sum() - (
    lw*F.log_softmax(self.leaves,-1)).sum()

class IndependentPolicy(torch.nn.Module):
 def __init__(self):
  super().__init__()
  self.shape=torch.nn.Parameter(torch.zeros(5,dtype=torch.float64))
  self.ops=torch.nn.Parameter(torch.zeros((3,4),dtype=torch.float64))
  self.leaves=torch.nn.Parameter(torch.zeros((4,3),dtype=torch.float64))
 def greedy(self):
  sh=int(self.shape.detach().argmax().item())
  ops=tuple(int(x) for x in self.ops.detach().argmax(-1).tolist())
  leaves=tuple(int(x) for x in self.leaves.detach().argmax(-1).tolist())
  return sh,ops,leaves
 def loss(self,stats):
  shapes,_,__,ops,leaf=stats
  sh=torch.tensor(shapes,dtype=torch.float64)
  ow=torch.tensor(ops,dtype=torch.float64)
  lw=torch.tensor(leaf,dtype=torch.float64)
  return -(sh*F.log_softmax(self.shape,-1)).sum() - (
    ow*F.log_softmax(self.ops,-1)).sum() - (
    lw*F.log_softmax(self.leaves,-1)).sum()

def train_only_behaviorally(policy,stats):
 start=time.perf_counter_ns()
 optimizer=torch.optim.Adam(policy.parameters(),lr=LR)
 first=float(policy.loss(stats).detach())
 untrained=policy.greedy()
 for _ in range(UPDATES):
  optimizer.zero_grad()
  objective=policy.loss(stats)
  objective.backward()
  optimizer.step()
 final=float(policy.loss(stats).detach())
 state=b"".join(p.detach().cpu().numpy().astype(">f8").tobytes()
                for p in policy.parameters())
 return {"start_loss":round(first,9),
  "end_loss":round(final,9),
  "greedy_untrained":untrained,"greedy_trained":policy.greedy(),
  "trainable_parameters":sum(p.numel() for p in policy.parameters()),
  "optimizer_steps":UPDATES,"gradient_optimizer":"Adam on behavioral-weighted AST log-likelihood",
  "training_wall_ms":elapsed(start),
  "weights_sha256":hashlib.sha256(state).hexdigest()}

def heldout_pass(d):
 for k in TEST_K:
  a,b,target=recurrence_data((k,),100)
  if not np.array_equal(evaluate(tree(d),a,b),target):return False
 return True

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--out",type=Path,required=True)
 args=parser.parse_args()
 torch.set_num_threads(1)
 torch.manual_seed(SEED)
 np.random.seed(SEED)
 training=recurrence_data(TRAIN_K,48)
 programs=all_programs()
 assert len(programs)==25920
 losses,all_behavior,complete_wall=grammar_evaluation(training,programs)
 assert int(np.sum(losses==0))==2,"Unexpected operator grammar ground truth count"
 cls_start=time.perf_counter_ns()
 klass=int(np.argmin(losses))
 classical_selection_ms=elapsed(cls_start)
 posterior=behavior_posterior(losses)
 stats=sufficient_stats(posterior,programs)
 # First explicit causal ablation: 29 independent logits with same evidence.
 independent=IndependentPolicy()
 ablated=train_only_behaviorally(independent,stats)
 ablation_holdout=heldout_pass(ablated["greedy_trained"])
 # Actual study model: shape and child dependencies retained.
 conditional=ConditionalPolicy()
 learned=train_only_behaviorally(conditional,stats)
 predicted=learned["greedy_trained"]
 exact_train=bool(np.array_equal(
  evaluate(tree(predicted),*training[:2]),training[2]))
 exact_heldout=heldout_pass(predicted)
 # Shuffle target values as a negative causal control; NO target program labels.
 rng=np.random.default_rng(SEED)
 bad_source=(training[0],training[1],rng.permutation(training[2]))
 bad_loss,_,bad_wall=grammar_evaluation(bad_source,programs)
 bad_policy=ConditionalPolicy()
 bad_fit=train_only_behaviorally(bad_policy,sufficient_stats(
    behavior_posterior(bad_loss),programs))
 neg_heldout=heldout_pass(bad_fit["greedy_trained"])
 exact_classic=heldout_pass(programs[klass])
 # Program verification: independently and fully preserve source Pre, Trans, Post.
 formal=[check_bounded_counter(int(k),tree(predicted),tree(programs[klass]))
         for k in TEST_K]
 all_formal=all(v["all_original_three_vcs_dual_proved"] for v in formal)
 report={
  "schema":"neumann.q3.teacherfree.behavioral.shape_conditional_ast.original_synthetic.v1",
  "scope":"POSTHOC local-dev-guided synthetic same-family, NOT G1 fresh blind",
  "grammar":{"shapes":5,"operators":["+","-","*","div"],"leaves":["a","b","1"],
      "complete_classical_program_count":len(programs),
      "explicit_modulo_primitive":False},
  "training_program_moduli":list(TRAIN_K),
  "train_observed_source_states":len(training[0]),
  "training_targets_are_real_recurrence_state_outputs_not_gold_AST":True,
  "source_output_is_matched_by_full_grammar_classical_evaluation":True,
  "complete_classical_scoring_wall_ms":complete_wall,
  "first_complete_classical_exact_program_zero_based_index":klass,
  "complete_classical_first_exact_ast":ast_string(tree(programs[klass])),
  "classical_first_exact_selection_wall_ms":classical_selection_ms,
  "complete_classical_heldout_all_k":exact_classic,
  "reward_temperature_fixed_from_local_dev":TEMP,
  "rewards_derived_only_from_observed_behavior":True,
  "no_gold_ast_or_search_discovered_ast_as_gradient_pseudolabel":True,
  "gradient_uses_full_enumerated_AST_behavior_scores":True,
  "behavior_posterior_mass_exact_programs":float(posterior[losses==0].sum()),
  "independent_29_parameter_negative_control":{
     **ablated,
     "greedy_AST":ast_string(tree(ablated["greedy_trained"])),
     "heldout_all_k_pass":ablation_holdout,
     "train_exact":bool(np.array_equal(evaluate(tree(ablated["greedy_trained"]),
                    *training[:2]),training[2]))},
  "conditional_125_parameter_learning":{
     **learned,"greedy_AST":ast_string(tree(predicted)),
     "train_exact":exact_train,"heldout_all_k_pass":exact_heldout},
  "shuffled_output_negative_control":{
     **bad_fit,"score_generation_ms":bad_wall,
     "greedy_AST":ast_string(tree(bad_fit["greedy_trained"])),
     "heldout_all_k_pass":neg_heldout},
  "heldout_synthetic_programs":formal,
  "all_four_synthetic_original_Z3_cvc5_3VC":all_formal,
  "scoped_behavioral_gradient_AST_learning_pass": (
    exact_train and exact_heldout and all_formal and exact_classic
    and not ablation_holdout and not neg_heldout
    and not heldout_pass(learned["greedy_untrained"])),
  "conclusion_attribution":{
    "gradient_model_emits_first_greedy_solution_without_gold_program_label":True,
    "full_grammar_behavior_scoring_is_classical_exhaustive":True,
    "new_mathematical_primitive_outside_grammar":False,
    "learned_exclusive_superiority_over_strong_classical":False,
    "user_authored_synthetic_not_independent_original_family":True,
    "same_or_better_on_all_in_compute":False,
    "Q3_global":"OPEN","Q1_Q7_global":"OPEN"},
  "GPU_calls":0,"paid_api_calls":0}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("FROZEN_25K_GRAMMAR_EXACT_COUNT",int(np.sum(losses==0)))
 print("CLASSIC",klass,report["complete_classical_first_exact_ast"])
 print("29_ABLATION",report["independent_29_parameter_negative_control"]["greedy_AST"],ablation_holdout)
 print("125_CONDITIONAL",report["conditional_125_parameter_learning"]["greedy_AST"],exact_heldout)
 print("SHUFFLED_NEGATIVE",report["shuffled_output_negative_control"]["greedy_AST"],neg_heldout)
 print("ORIGINAL_SYNTHETIC_DUAL_PROOF",all_formal)
 print("SCOPED_PASS",report["scoped_behavioral_gradient_AST_learning_pass"])
 print("GLOBAL_Q3",report["conclusion_attribution"]["Q3_global"])
if __name__=="__main__":main()
