"""NEUMANN Q3 decisive immutable-receipt adjudicator (2026-10-20).

No training, source editing, oracle or new G1 evaluation. This is an
independently repeatable exact stdlib arithmetic + immutable SHA auditor.
The Q3 current fixed-42 line may CLOSE as mathematical NO-GO; global
North Star Q3 cannot be promoted by this decision.

Inputs: four raw GitHub Actions JSON receipts from pinned finished runs:
 PR315 theorem, PR316 prereg five, PR317 first invalid 3-blob run,
 PR317 actual source-bound independent classical verifier.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

EXPECTED = {
 "theorem":"640c0b33d086f023fb62f2c8f843b7aba99e5f8e5022c66d7c2d0b2ee8f1f8db",
 "five":"8333563ca90ba7e2d8afe6ee807b1fe36f62a0be4514d038ebec47ea9594f592",
 "external_first":"825afcbe5bb374dea536fa66ad85d5b19ed2458f6ac2596a69156468ceb65c14",
 "external_classical":"25d4f95756e260450927dbffda1dff1d509d7b2b9c521a81dd0f90ff344dc82e",
}
WEIGHTS_SHA="563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78"

def load(path, expected):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError("ORIGINAL_RECEIPT_SHA_MISMATCH: "+str(path))
    return json.loads(raw)

def exact_universal_proof(doc):
    if doc["strict_neural_operator_novelty_within_this_fixed_grammar"]!="MATHEMATICALLY_NO_GO":
        raise ValueError("THEOREM_SCOPE_IS_NOT_NO_GO")
    if doc["equivalence_entire_Q_polynomial_degree_5"] is not True or \
       doc["exact_rational_matrix_identity_B_times_L_is_I6"] is not True:
        raise ValueError("MISSING_EXISTING_THEOREM_ASSERTIONS")
    if doc["difference_operator_determinant"]!=720:
        raise ValueError("WRONG_DIFFERENCE_OPERATOR_DETERMINANT")
    W=doc["frozen_integer_weight_matrix"]
    if len(W)!=6 or any(len(row)!=7 for row in W):
        raise ValueError("FROZEN_WEIGHT_SHAPE_WRONG")
    packed=b"".join(struct.pack(">q",int(x)) for row in W for x in row)
    if hashlib.sha256(packed).hexdigest()!=WEIGHTS_SHA:
        raise ValueError("FROZEN_WEIGHT_BYTES_CHANGED")
    assert doc["frozen_integer_weight_denominator"]==5040
    # Compute the coefficient finite-difference operator D without SymPy.
    # F(t+1)-F(t)=(sum over j>=1 F_j*(t+1)^j) - (sum F_j*t^j)
    D=[[math.comb(j,k) if j>k else 0 for j in range(1,7)]
       for k in range(6)]
    assert D==doc["difference_operator_integer_matrix"]
    # D @ (W.T[:,1:]/5040) = I_6 *exactly* in signed integers.
    out=[[sum(D[row][j]*W[column][j+1] for j in range(6))
          for column in range(6)] for row in range(6)]
    identity=[[5040*int(row==col) for col in range(6)] for row in range(6)]
    if out!=identity or any(row[0]!=0 for row in W):
        raise ValueError("EXACT_POLYNOMIAL_OPERATOR_IDENTITY_FAIL")
    # Crucial negative control, no optimistic 64-sample inference.
    mutated=[r.copy() for r in W]
    mutated[0][1]+=1
    neg=[[sum(D[row][j]*mutated[column][j+1] for j in range(6))
          for column in range(6)] for row in range(6)]
    if neg==identity:
        raise ValueError("MUTATION_NEGATIVE_CONTROL_NOT_DETECTED")
    if doc["unique_polynomial_antidifference_given_zero_initial"] is not True:
        raise ValueError("UNIQUE_ANTIDIFFERENCE_NOT_CERTIFIED")
    return {"input_polynomial_degree_max":5,
      "integral_degree_max":6,"learned_weights_SHA256":WEIGHTS_SHA,
      "matrix_exact_difference_identity":"PASS_36_ENTRIES",
      "mutated_single_weight_negative_control":"PASS_DETECTED",
      "current_fixed_42w_unique_operator":"MATHEMATICALLY_NO_GO"}

def adjudicate(inputs):
    theorem=inputs["theorem"]
    five=inputs["five"]
    first=inputs["external_first"]
    classical=inputs["external_classical"]
    for name,item in inputs.items():
        if item.get("global_Q3")!="OPEN":
            raise ValueError("UNAUTHORIZED_GLOBAL_Q3_PROMOTION:"+name)
    math_proof=exact_universal_proof(theorem)
    if five["frozen_model_weight_sha256"]!=WEIGHTS_SHA or \
       five["all_five_source_hashes_verified"] is not True or \
       five["all_five_source_rows_retained"] is not True:
        raise ValueError("FIVE_ORIGINS_IDENTITY_NOT_PRESERVED")
    if len(five["five_actual_original_sources"])!=5 or \
       five["learned_first_original_3VC_pass_count"]!=0:
        raise ValueError("FIRST_FIVE_NEURAL_RESULT_CHANGED")
    if first["frozen_weights_and_synthetic_training"]["frozen_trained_weights_sha256"]!=WEIGHTS_SHA or \
       first["learned_certified_new_originals"]!=0:
        raise ValueError("FIRST_EXTERNAL_NEGATIVE_CHANGED")
    if first["all_three_original_git_blobs_verified"] is not False:
        raise ValueError("ORIGINAL_MALFORMED_3RD_SHA_WAS_RETROFITTED")
    if classical["first_valid_blind_source_count"]!=2 or \
       classical["third_SHA_corrected_POSTHOC_not_blind"] is not True:
        raise ValueError("THIRD_ORIGINAL_POSTHOC_LEAKAGE")
    if classical["external_valid_blind_cvc5_dual_native_original_3VC"]!=1 or \
       classical["posthoc_third_classical_dual_native_original_3VC"]!=1 or \
       classical["original_dual_certified_cvc5_synthesized_count"]!=2:
        raise ValueError("INDEPENDENT_CLASSICAL_ORIGINAL_CERT_CHANGED")
    cases=classical["cases"]
    if len(cases)!=3:raise ValueError("CLASSICAL_ROWS_INCOMPLETE")
    for row in (cases[0],cases[2]):
        if not row["source_original_cvc5_generated_invariant_dual_3VC"]:
            raise ValueError("CLASSICAL_SOURCE_CERT_MISSING")
        if row["original_native_custom_parity"]!={"pre":"unsat","trans":"unsat","post":"unsat"}:
            raise ValueError("CLASSICAL_SOURCE_PARSE_PARITY_MISSING")
        proofs=row["actual_published_original_3VC_Z3_independent_cvc5"]
        if set(proofs)!={"initial","consecution","post"} or not all(
           p["Z3"]=="unsat" and p["native_original_cvc5"]["status"]=="unsat"
           and p["native_original_cvc5"]["exit_code"]==0 for p in proofs.values()):
            raise ValueError("CLASSICAL_DUAL_REAL_SOURCE_3VC_MISSING")
    if cases[1]["source_original_cvc5_generated_invariant_dual_3VC"]:
        raise ValueError("BOOL_UNVERIFIED_SOURCE_FALSE_CERTIFICATE")
    return {
      "schema":"neumann.q3.immutable_original_receipt_stop_gate.v1",
      "inputs_SHA256":EXPECTED,
      "result":"DECISION_CLOSED_CURRENT_42W_ARCHITECTURE_NO_GO",
      "current_polynomial_operator_exact_negative_theorem":math_proof,
      "learned_frozen_first_external_five": "0/5_CERTIFIED",
      "learned_frozen_first_valid_other_external":"0/2_CERTIFIED",
      "independently_verified_other_origin_classical_originals":{
        "valid_first_source_origin":"1/2",
        "third_SHA_corrected_posthoc":"1/1",
        "unverified_Lustre_original":"UNKNOWN_NOT_SAFE_PROOF",
      },
      "Q3_oracle_free_structure_discovery":"PASS_SCOPED_PRIOR_ORIGINALS",
      "Q3_global_deployable_cross_origin":"OPEN",
      "Q3_current_fixed_42w_learned_exclusive_math":"NO_GO_CLOSED",
      "Q3_new_representation_constructed_learned":"NOT_DEMONSTRATED",
      "Q3_matched_strong_classical_advantage":"NOT_DEMONSTRATED",
      "remaining_Q3_decisive_gates":[
        "GATE_R: genuinely broader source-semantic representation and generative candidate beyond fixed polynomial grammar; no source-specific leakage",
        "GATE_V: preregister new source-author families; first attempt authentic original Z3/cvc5 full safety proof and non-Post useful structures, compare equally capable classical and ablations"],
      "Q4_Q5_separate_followup":"full discovery + execution + verification + training/cold accounting at matched capability",
      "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
      "GPU_calls":0,"paid_API_calls":0,
      "do_not_run_more_fixed42_training_for_operator_novelty":True,
    }

def main():
    ap=argparse.ArgumentParser()
    for name in EXPECTED:ap.add_argument("--"+name.replace("_","-"),required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    inputs={name:load(getattr(args,name),expected)
      for name,expected in EXPECTED.items()}
    decision=adjudicate(inputs)
    Path(args.out).write_text(json.dumps(decision,ensure_ascii=False,indent=2)+"\n")
    print("Q3_CURRENT_42W_ARCHITECTURE",decision["result"])
    print("Q3_GLOBAL",decision["global_Q3"])
    print("TWO_REMAINING_DECISIVE_GATES",*decision["remaining_Q3_decisive_gates"],sep="\n")

if __name__=="__main__":main()
