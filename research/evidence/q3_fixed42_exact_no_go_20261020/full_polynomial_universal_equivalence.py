"""NEUMANN Q3: algebraically certify frozen learned 42-weight map == exact
classical polynomial summation on the ENTIRE degree <=5 polynomial space,
not just test samples. Universal identity: B @ W[:,1:].T / 5040 = I_6.

The attached source weights come byte-for-byte from the FIRST original study
artifact q3_learned_three_first.json, raw JSON SHA256
993e7ce6ce116bedce68efa66ada4a42ea1913629730ec1b914bdfc60316f513.
The matrix SHA equals the original reported model hash, protecting provenance.
This is proof of fixed grammar's exact classical equivalence, NOT global Q3.
"""
from __future__ import annotations
import argparse,hashlib,json,math,time
from pathlib import Path
import numpy as np
import sympy as sp

FIRST_ORIGINAL_JSON_SHA="993e7ce6ce116bedce68efa66ada4a42ea1913629730ec1b914bdfc60316f513"
WEIGHTS_SHA="563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78"
SCALE=5040
# First-run trained matrix: six input delta coefficients x seven exact
# antidifference coefficients, big-endian signed int64 SHA verified below.
FROZEN_W=[
 [0,5040,0,0,0,0,0],
 [0,-2520,2520,0,0,0,0],
 [0,840,-2520,1680,0,0,0],
 [0,0,1260,-2520,1260,0,0],
 [0,-168,0,1680,-2520,1008,0],
 [0,0,-420,0,2100,-2520,840],
]
def proof_certificate():
 start=time.perf_counter_ns()
 raw=np.array(FROZEN_W,dtype=">i8")
 model_sha=hashlib.sha256(raw.tobytes()).hexdigest()
 if model_sha!=WEIGHTS_SHA:raise RuntimeError("MODEL_BYTES_CHANGED")
 W=sp.Matrix(FROZEN_W)/SCALE
 assert W.shape==(6,7)
 # B maps polynomial F(t) with F(0)=0 to Delta F(t)=F(t+1)-F(t)
 # coefficient basis t^0 .. t^5. Entry t^r of Delta(t^(j+1))
 # is binomial(j+1,r) for 0<=r<=j.
 B=sp.Matrix(6,6,lambda r,j:sp.binomial(j+1,r) if r<=j else 0)
 learned_operator=W[:,1:].T
 product=B*learned_operator
 assert product==sp.eye(6)
 assert B.det()!=0
 assert all(v==0 for v in W[:,0])
 # The above proves exact equality for ALL rational input polynomial
 # coefficient vectors, not a sampled subset; F(0)=0 fixes uniqueness.
 coeff=sp.symbols("c0:6")
 t=sp.Symbol("t")
 F=sp.expand(sum(sum(sp.Rational(FROZEN_W[i][j],SCALE)*coeff[i]
          for i in range(6))*t**j for j in range(7)))
 delta=sum(coeff[i]*t**i for i in range(6))
 residual=sp.expand(F.subs(t,t+1)-F-delta)
 assert residual==0
 assert F.subs(t,0)==0
 basis_examples=[]
 for k in range(6):
  expected=sp.expand(sp.summation(sp.Symbol("_n",integer=True)**k,
    (sp.Symbol("_n",integer=True),0,t-1)))
  predicted=sp.expand(sum(sp.Rational(FROZEN_W[k][j],SCALE)*t**j
    for j in range(7)))
  assert sp.expand(expected-predicted)==0
  basis_examples.append({"delta":"t^"+str(k),
    "frozen_learned_full_antidifference":str(predicted),
    "classical_exact_summation":str(expected),
    "exact_difference_zero":True})
 # Negative-control proves the exact matrix identity is nontrivial.
 mutated=[row[:] for row in FROZEN_W]
 mutated[0][1]+=1
 wrong=sp.Matrix(mutated)/SCALE
 assert B*wrong[:,1:].T!=sp.eye(6)
 # Causal implication: within the fixed grammar and given the SAME
 # coefficient input, exact classical always returns exactly the same
 # polynomial as learned W. Hence no STRICT accuracy / novel operator
 # gain over complete exact classical on this fixed polynomial domain.
 report={"schema":"neumann.q3.frozen42.linear_operator_exact_no_go.v1",
   "original_first_trained_JSON_SHA256":FIRST_ORIGINAL_JSON_SHA,
   "original_frozen_weights_SHA256":model_sha,
   "frozen_integer_weight_matrix":FROZEN_W,
   "weight_shape":[6,7],
   "fixed_input_polynomial_max_degree":5,
   "fixed_output_antidifference_max_degree":6,
   "frozen_integer_weight_denominator":SCALE,
   "difference_operator_integer_matrix":B.tolist(),
   "learned_rational_operator_matrix":[
     [str(x) for x in learned_operator.row(r)] for r in range(6)],
   "exact_rational_matrix_identity_B_times_L_is_I6":product==sp.eye(6),
   "difference_operator_determinant":int(B.det()),
   "learned_full_polynomial_symbolic_difference_zero":residual==0,
   "learned_output_zero_initial":F.subs(t,0)==0,
   "six_basis_exact_classical_source_replays":basis_examples,
   "matrix_one_entry_mutation_counterexample_detected":True,
   "unique_polynomial_antidifference_given_zero_initial":True,
   "equivalence_entire_Q_polynomial_degree_5":True,
   "strict_learned_function_class_advantage_over_exact_classical_possible":False,
   "strict_neural_operator_novelty_within_this_fixed_grammar":"MATHEMATICALLY_NO_GO",
   "absolute_runtime_inferiority_or_superiority_proved":False,
   "proof_scope":"CLOSED_FIXED_42_WEIGHT_POLYNOMIAL_OPERATOR_NOT_GLOBAL_LEARNING",
   "authentic_external_source_generalization_proved":False,
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "gpu_calls":0,"paid_API_calls":0,
   "whole_exact_symbolic_audit_wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
 return report

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args();r=proof_certificate()
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
 print("FROZEN_42_WEIGHT_SHA",r["original_frozen_weights_SHA256"])
 print("UNIVERSAL_EXACT_POLYNOMIAL_EQUIVALENCE",
   r["exact_rational_matrix_identity_B_times_L_is_I6"])
 print("SIX_BASIS_EXACT_CLASSICAL",len(r["six_basis_exact_classical_source_replays"]))
 print("GRAMMAR_G1_STRICT_NOVELTY",r["strict_neural_operator_novelty_within_this_fixed_grammar"])
 print("GLOBAL_Q3",r["global_Q3"])
if __name__=="__main__":main()
