"""Independent source-level learned AST -> smaller verified executable transition.

READ-ONLY from SHA256-pinned official PR430 original trained receipts.
This compiler NEVER learns coefficients and NEVER reads a gold result as a
training signal. Universal symbolic commuting diagram is required:
    abstraction(T_original(s)) == T_abstract(abstraction(s))
together with original Pre -> abstract Pre and original abstract goal ->
original Post. This proves safety-preserving forward abstraction, not that
the abstract model can reconstruct original trajectories.
Matched strong classical exact-polynomial candidate receives identical
transform compiler and certification authority.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import sympy as sp
from research.evidence.q3_raw_transition_nonlinear_20261021.learned_original_source_nonlinear_AST import sources
OFFICIAL="07a914d0f391119d0089b25fa59afdea0fce87b2aaad1e30e9ee34b3adc14d97"
def genuine_program_rewrite(P,candidate):
 start=time.perf_counter_ns()
 V=P["variables"];s=list(V)
 expr=sp.sympify(candidate,locals={str(x):x for x in V})
 extra=expr.free_symbols-set(V)
 if extra:raise RuntimeError("UNAUTHORIZED_LEARNED_FREE_VARIABLE:"+str(extra))
 q=sp.Symbol("q",integer=True)
 projected_next=sp.factor(expr.xreplace(dict(zip(V,P["next"]))))
 commutation=sp.factor(projected_next-expr)
 abstract_pre=sp.factor(expr.subs(P["pre"],simultaneous=True))
 goal_gap=sp.factor(expr-P["post"])
 # Surjectivity of q onto integers: all other state coordinates 0 and
 # output anchor q. The chosen grammar is anchored at coefficient 1.
 surj=sp.factor(expr.subs({x:(q if x==P["anchor"] else 0) for x in V},
                          simultaneous=True)-q)
 proof=dict(exact_transition_commutation=(commutation==0),
            original_Pre_maps_to_abstract_q0=(abstract_pre==0),
            abstract_q0_entails_original_Post=(goal_gap==0),
            each_abstract_q_has_an_original_witness=(surj==0),
            commutation_residual_AST=str(commutation),
            original_Pre_abstract_q_AST=str(abstract_pre),
            abstract_goal_to_original_post_residual_AST=str(goal_gap),
            abstract_source_state_variables=["q"],
            abstract_source_pre="q == 0",
            abstract_source_transition="q_next = q",
            abstract_source_goal="q == 0",
            original_source_state_variable_count=len(V),
            abstract_source_state_variable_count=1,
            source_state_dimensions_eliminated=len(V)-1,
            all_step_original_transition_arithmetic_replaced_with_identity=True,
            cost_to_compute_original_to_abstract_projection_at_boundary=sp.count_ops(expr),
            source_abstract_compilation_wall_ms=(time.perf_counter_ns()-start)/1e6)
 proof["FULL_VALID_SOURCE_REWRITE"]=all(proof[k] for k in (
    "exact_transition_commutation","original_Pre_maps_to_abstract_q0",
    "abstract_q0_entails_original_Post","each_abstract_q_has_an_original_witness"))
 proof["learned_composed_AST"]=str(expr)
 return proof
def negative_source_witness():
 x,y=sp.symbols("x y",integer=True)
 nonlinear=y-x*x
 mutated={x:x+1,y:y+2*x+1+x*(x-1)*(x-2)}
 residual=sp.factor(nonlinear.xreplace(mutated)-nonlinear)
 if residual!=x*(x-1)*(x-2):raise AssertionError("SOURCE_MUTANT_NEGATIVE_WRONG")
 return dict(source_variant="quadratic original with OOD transition polynomial",
             same_three_early_source_transition_pairs=True,
             universal_candidate_commutation_rejected=True,
             real_state_x3_falsification=int(residual.subs(x,3)),
             symbolic_original_source_residual=str(residual))
def main():
 ap=argparse.ArgumentParser()
 for k in ("official","out"):ap.add_argument("--"+k,required=True)
 a=ap.parse_args()
 raw=Path(a.official).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=OFFICIAL:
  raise RuntimeError("OFFICIAL_TRAINED_SOURCE_RECEIPTS_SHA256_CHANGED")
 training=json.loads(raw)
 if training["schema"]!="neumann.q3.source_transition_nonlinear_learned_AST_synthetic_v1":
  raise RuntimeError("NOT_THE_COMPLETED_ORIGINAL_LEARNED_SOURCE_PROOF_RUN")
 catalogue={p["name"]:p for p in sources()}
 if len(training["all_original_source_trials"])!=24:raise RuntimeError("NOT_24_ACTUAL_TRAINED_RUNS")
 rows=[]
 for record in training["all_original_source_trials"]:
  P=catalogue[record["task"]]
  final=record["all_degree_trials"][-1]
  if not final["learned_full_original_PASS"] or not final["classical_full_original_PASS"]:
   raise RuntimeError("TRAINED_OR_CLASSICAL_FULL_SOURCE_NOT_PROVED")
  learned=genuine_program_rewrite(P,final["learned_composed_AST"])
  classical=genuine_program_rewrite(P,final["classical_exact_polynomial_AST"])
  if not learned["FULL_VALID_SOURCE_REWRITE"] or not classical["FULL_VALID_SOURCE_REWRITE"]:
   raise RuntimeError("SOURCE_TO_QUOTIENT_COMPILER_FAIL_CLOSED")
  rows.append(dict(source=record["task"],seed=record["seed"],
                   independent_original_learned_proof=learned,
                   matched_independent_exact_classical_proof=classical))
  print("GENUINE_SOURCE_TRANSITION_REWRITTEN",record["task"],record["seed"],
        "OLD_STATE",len(P["variables"]),"NEW_STATE",1,
        "ORIGINAL_EXACT_PROOF",learned["FULL_VALID_SOURCE_REWRITE"],
        "CLASSICAL_EXACT_PROOF",classical["FULL_VALID_SOURCE_REWRITE"],flush=True)
 neg=negative_source_witness()
 report=dict(schema="neumann.q3.official_trained24_source_AST_to_verified_one_state_program_rewrite.v1",
    official_original_learning_raw_SHA256=OFFICIAL,
    actual_trained_source_rewrites_independently_certified=len(rows),
    matched_exact_classical_source_rewrites_independently_certified=len(rows),
    original_tasks=3,actual_learning_seed_repeats_per_task=8,
    transformed_source_program_abstract_pre="q == 0",
    transformed_source_program_abstract_transition="q_next = q",
    transformed_source_program_abstract_post="q == 0",
    minimal_abstract_state_variables=1,
    zero_original_transition_simulation_needed_after_certification_for_THIS_goal=True,
    no_measured_computation_advantage_over_strong_exact_classical=True,
    independent_source_mutant_rejection=neg,
    original_learning_and_validation_already_paid_not_free=True,
    learned_new_primitive_operator_not_proven=True,
    originally_unseen_real_benchmark_NOT_TESTED=True,
    strong_classical_transformation_equal=True,
    global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
    exact_source_proof_ledger=rows)
 dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 for k in ("actual_trained_source_rewrites_independently_certified",
           "matched_exact_classical_source_rewrites_independently_certified"):
  print("LEARNED_PROOF_CARRYING_SOURCE_REWRITE",k,report[k])
 print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
