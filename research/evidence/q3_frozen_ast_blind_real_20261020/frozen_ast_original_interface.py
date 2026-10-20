"""Q3 frozen learned AST macro on three uninspected originals.
Pre-source frozen identity contract is committed separately before CI.
This is an AST *interface* audit, not learned new invariant discovery.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import numpy as np
import z3
from research.evidence.q3_behavioral_conditional_ast_20261020.first_cpu_original import (
  TRAIN_K,recurrence_data,all_programs,grammar_evaluation,behavior_posterior,
  sufficient_stats,ConditionalPolicy,train_only_behaviorally,tree)
from research.evidence.q3_learned_typed_ast_macro_20261019.train_self_discovered_composition import (
  ast_string,z3_ast)
from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,
  check_formula,source_proof)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

ORIGINALS=(
 ("NIA.other","benchmarks/NIA/other/div.sl","78ebf3875665cb257631beb87445abaf3c41f4a1"),
 ("NIA.other","benchmarks/NIA/other/lcm.sl","6c0cbaafc0c8b960d6047014dc5670554aacbc85"),
 ("CHI.InvGame","benchmarks/NIA/2018.CHI_InvGame/sqrt-more-rows-swap-columns.sl","66d45fac379b9114a38bed6dc25599e0c0f5caa1"),
)
EXPECTED_WEIGHT_SHA="c67457981ed9f8faea5b1b38061ceebb998340274554e003b67bf47822280f10"
EXPECTED_AST="(- a (* (div a b) b))"
SRC_REF="6ac90265b11431c9477dfbd33e3e3380234c0499"

def git_blob(x):
 return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def sha(x):
 return hashlib.sha256(x).hexdigest()
def ms(t):
 return round((time.perf_counter_ns()-t)/1e6,3)
def cvc5(query,seconds=15):
 start=time.perf_counter_ns()
 try:
  p=subprocess.run(["cvc5","--lang=smt2","--decision=internal",
         f"--tlimit-per={seconds*1000}","-"],input=query,text=True,
         capture_output=True,timeout=seconds+5)
  out=[x.strip() for x in p.stdout.splitlines() if x.strip()]
  return {"status":out[-1] if out else "EMPTY","returncode":p.returncode,
          "wall_ms":ms(start),"stderr_excerpt":p.stderr[:140]}
 except Exception as e:
  return {"status":"NO_RESULT","error":str(e)[:160],"wall_ms":ms(start)}
def verify_original_source(srcpath,origin,relative,sha1,learned_ast):
 start=time.perf_counter_ns()
 try:
  raw=srcpath.read_bytes()
  if git_blob(raw)!=sha1:raise ValueError("FROZEN_GIT_BLOB_SHA_MISMATCH")
 except Exception as e:
  return {"origin_group":origin,"source":relative,"frozen_git_blob":sha1,
    "status":"IDENTITY_OR_IO_FAIL_CLOSED","reason":type(e).__name__+":"+str(e)[:180]}
 row={"origin_group":origin,"source":relative,"frozen_git_blob":sha1,
       "actual_source_sha256":sha(raw),"input_bytes":len(raw),
       "status":"NOT_YET_VERIFIED"}
 try:
  sy=sexprs(raw)
  orig=extract_mixed_original(sy)
  nat=native_original_relations(sy,orig)
  nat.update({"now":orig["now"],"next":orig["next"]})
  parity=check_parity(orig,nat)
  row["native_original_three_semantic_parity"]=parity
  if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
   raise ValueError("NATIVE_ORIGINAL_PRE_TRANS_POST_NOT_EQUIVALENT")
  row["real_original_pre_sat"]=check_formula(nat["pre"])
  row["original_not_post_sat"]=check_formula(z3.Not(nat["post"]))
  if row["real_original_pre_sat"]!="sat" or row["original_not_post_sat"]!="sat":
   raise ValueError("ORIGINAL_NONVACUITY_UNPROVEN")

  # EXACT frozen grammar scope: traversal of published Post, without any
  # source-specific manual operator selection, tuning, or gold invariants.
  mods=[]
  def walk(expr):
   if not z3.is_app(expr):return
   if expr.decl().kind()==z3.Z3_OP_MOD:
    mods.append(expr)
   for ch in expr.children():walk(ch)
  walk(nat["post"])
  row["mod_terms_in_original_post"]=len(mods)
  row["source_variable_count"]=len(orig["now"])
  if not mods:
   row["status"]="OUT_OF_SCOPE_NO_MOD_TERM_IN_PUBLISHED_POST"
   return row
  # Only accept int typed mod and positive source-denominator where true on
  # published source-reachable states. Do not assume positivity from names.
  replacements=[]
  guards=[]
  for modexpr in mods:
   a,b=modexpr.children()
   if a.sort().kind()!=z3.Z3_INT_SORT or b.sort().kind()!=z3.Z3_INT_SORT:
    row["status"]="ABSTAIN_UNSUPPORTED_TYPED_MOD"
    return row
   if check_formula(z3.And(nat["pre"],z3.Not(b>0)))!="unsat":
    row["status"]="ABSTAIN_SOURCE_DOES_NOT_PROVE_POSITIVE_DENOMINATOR_FROM_PRE"
    return row
   guards.append(b>0)
   replacements.append((modexpr,z3_ast(learned_ast,a,b)))
  new_post=z3.substitute(nat["post"],*replacements)
  row["learned_macro_post_syntactically_changed"]=new_post.sexpr()!=nat["post"].sexpr()
  row["rewritten_post_hash"]=sha(new_post.sexpr().encode())
  row["original_post_hash"]=sha(nat["post"].sexpr().encode())
  # Check both tools for semantic equality, and quantify the fact that this
  # is just a replace of a public post term, not learned loop induction.
  sem=z3.And(*guards,z3.Xor(nat["post"],new_post))
  ps=z3.Solver();ps.set(timeout=5000);ps.add(sem)
  row["rewrite_original_post_equivalence_z3"]=str(ps.check())
  row["rewrite_original_post_equivalence_cvc5"]=(
     cvc5(ps.to_smt2(),seconds=12) if row["rewrite_original_post_equivalence_z3"]=="unsat"
     else {"status":"NOT_RUN"})
  original_post_only=source_proof(nat["post"],nat)
  generated_post_only=source_proof(new_post,nat)
  row["unmodified_post_only_original_Z3_VCs"]=original_post_only["vcs"]
  row["learned_rewritten_post_only_original_Z3_VCs"]=generated_post_only["vcs"]
  row["nontrivial_new_invariant_beyond_original_post"]=False
  if generated_post_only["accepted"]:
   receipt=check_original_candidate(srcpath,new_post.sexpr(),
          expected_source_sha256=sha(raw))
   row["rewritten_post_independent_cvc5_original_VCs"]=receipt.get("cvc5_original_three_vc")
   row["rewritten_post_original_dual_cert"]=receipt.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
  else:
   row["rewritten_post_original_dual_cert"]=False
  row["status"]="POST_REWRITE_ONLY_NON_NOVELTY" if row["rewrite_original_post_equivalence_z3"]=="unsat" else "EQUIVALENCE_NOT_PROVEN"
 except Exception as e:
  row["status"]="ABSTAIN_UNSUPPORTED_OR_VERIFIER_ERROR"
  row["reason"]=type(e).__name__+":"+str(e)[:350]
 row["case_wall_ms"]=ms(start)
 return row

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--upstream-root",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 start=time.perf_counter_ns()
 training=recurrence_data(TRAIN_K,48)
 grammar=all_programs()
 scores,_,scoring_ms=grammar_evaluation(training,grammar)
 posterior=behavior_posterior(scores)
 model=ConditionalPolicy()
 actual=train_only_behaviorally(model,sufficient_stats(posterior,grammar))
 expression=ast_string(tree(model.greedy()))
 if expression!=EXPECTED_AST:
  raise ValueError("FROZEN_LEARNED_AST_MISMATCH: "+expression)
 if actual["weights_sha256"]!=EXPECTED_WEIGHT_SHA:
  raise ValueError("FROZEN_LEARNED_MODEL_WEIGHT_SHA_MISMATCH: "+actual["weights_sha256"])
 # Prove actual universal arithmetic identity on arbitrary source independent
 # integers, not just finitely sampled previously seen k values.
 A,B=z3.Ints("q3_universal_num q3_universal_den")
 proposed=z3_ast(tree(model.greedy()),A,B)
 neg=z3.And(B>0, A%B!=proposed)
 ss=z3.Solver();ss.set(timeout=10000);ss.add(neg)
 lemma_z3=str(ss.check())
 lemma_cvc5=cvc5(ss.to_smt2(),seconds=15) if lemma_z3=="unsat" else {"status":"NOT_RUN"}
 universal={"all_integer_numerators_positive_denominators":True,
   "Z3":lemma_z3,"cvc5":lemma_cvc5,
   "both_solver_backends_UNSAT":lemma_z3=="unsat" and
      lemma_cvc5.get("status")=="unsat" and lemma_cvc5.get("returncode")==0}
 rows=[]
 for group,rel,blob in ORIGINALS:
  rows.append(verify_original_source(a.upstream_root/rel,group,rel,blob,tree(model.greedy())))
 out={"schema":"neumann.q3.frozen_typed_AST_unseen_origin_transfer.v1",
    "study_class":"PRE_SOURCE_FROZEN_NON_G1_MACRO_INTERFACE_AUDIT",
    "upstream_pinned_git_revision":SRC_REF,
    "frozen_trained_AST":expression,
    "frozen_trained_weights_sha256":actual["weights_sha256"],
    "frozen_trained_parameters":actual["trainable_parameters"],
    "training_programs":[2,3,4,5,6],"training_source_only_states":240,
    "classical_grammar_count":len(grammar),
    "classical_full_grammar_behavior_scoring_required":True,
    "training_only_grammar_scoring_ms":scoring_ms,
    "training_only_Adam_ms":actual["training_wall_ms"],
    "frozen_universal_arithmetic_identity":universal,
    "originals":rows,
    "all_three_origins_pinned":len(rows)==3 and all(x.get("actual_source_sha256") for x in rows),
    "independent_origin_groups":2,
    "originals_eligible":sum(x.get("mod_terms_in_original_post",0)>0 for x in rows),
    "genuine_blind_original_new_invariant_certified":0,
    "new_operator_outside_frozen_grammar":False,
    "learned_unique_over_exact_classical":False,
    "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
    "GPU_calls":0,"paid_API_calls":0,
    "whole_study_wall_ms":ms(start)}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("FROZEN_WEIGHT_SHA_CHECK_PASS",out["frozen_trained_weights_sha256"])
 print("UNIVERSAL_REMAINDER_IDENTITY",universal)
 for row in rows:print("FRESH_SOURCE",row["source"],row["status"],"MOD_POST",row.get("mod_terms_in_original_post"))
 print("ORIGINAL_NEW_INVARIANT",out["genuine_blind_original_new_invariant_certified"])
 print("GLOBAL_Q3",out["global_Q3"])

if __name__=="__main__":main()
