"""After-FIRST read-only causal/economic audit, never rerun learner or Z3.

Does a trained policy produce any verified proof obligation different from
the strongest same-rights deterministic source-AST classical baseline?
Verify first artifact exact raw sha, complete coverage, and every Z3
obligation hash pair. Preserve original first outcome unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

FIRST_SHA="ab14bc7d798da9ef05c06a4ae3b6a29e7fb04e76b672601e2f6703bf4fe3f5bf"
FIRST_WEIGHT_SHA="9f8927c24800ad6a37fc784b544ec39d634b68de3d282a23efeb0f90b3c22625"


def audit(filename:Path)->dict:
    raw=filename.read_bytes()
    first_sha=hashlib.sha256(raw).hexdigest()
    if first_sha!=FIRST_SHA:
        raise ValueError("ORIGINAL_FIRST_PROOF_REWARD_JSON_DRIFT")
    f=json.loads(raw)
    if (f.get("schema")!="neumann.q3.proof-reward-owned-typed-relational-first.v1"
        or f["frozen_student_weights_sha256"]!=FIRST_WEIGHT_SHA
        or f["train_sourcefree_synthetic_tasks"]!=6
        or f["heldout_sourcefree_synthetic_tasks"]!=12):
        raise ValueError("FIRST_MANIFEST_OR_WEIGHT_DRIFT")
    same_proofs=0
    base_proofs=0
    labels=set()
    student_proof_ms=0.0
    classical_proof_ms=0.0
    model_calls=0
    for row in f["heldout_evidence"]:
        key=json.dumps(row["heldout_source_AST"],sort_keys=True)
        if key in labels:
            raise ValueError("DUPLICATE_ORIGINAL_HELDOUT_SOURCE_AST")
        labels.add(key)
        if (row["learned_independent_proof"] is not True
                or row["same_rights_classical_direct_proof"] is not True
                or row["untrained_independent_proof"] is not False):
            raise ValueError("FIRST_NOT_COMPLETE_EQUIVALENT_CAPABILITY")
        receipts=row["independent_z3_recipts"]
        student=receipts["student"]
        classical=receipts["classical"]
        if student["candidate"] != classical["candidate"]:
            raise ValueError("LEARNED_AND_CLASSICAL_PROPOSE_DIFFERENT_H1_OPERATOR")
        a=student["checks"];b=classical["checks"]
        if len(a)!=4 or len(b)!=4:
            raise ValueError("INCOMPLETE_H1_INDUCTIVE_CONTROL_CERTIFICATE")
        for x,y in zip(a,b):
            if x["check"]!=y["check"] or x["required"]!=y["required"]:
                raise ValueError("INDEPENDENT_VERIFIER_CONTRACT_DIFFERENCE")
            if x["script_sha256"]!=y["script_sha256"]:
                raise ValueError("H1_CLASSICAL_SMT_SOURCE_DIVERGENCE")
            if x["verdict"]!=y["verdict"] or x["verdict"]!=x["required"]:
                raise ValueError("H1_NOT_SAME_ORIGINAL_PROOF_OUTCOME")
            same_proofs+=1
        student_proof_ms+=float(student["total_z3_wall_ms"])
        classical_proof_ms+=float(classical["total_z3_wall_ms"])
        model_calls+=1
        base_proofs+=1
    if len(labels)!=12 or same_proofs!=48 or base_proofs!=12:
        raise ValueError("FIRST_HELDOUT_CONTROL_COVERAGE_DRIFT")
    training=float(f["training_actual_wall_seconds"])
    if training<=0 or not math.isfinite(training) or f["train_z3_calls"]!=72:
        raise ValueError("FREE_TRAINING_MISSING_DISCOVERY_COST")
    # Do not claim this as deployment-complete cost because BOTH arms are
    # embedded in one experiment process, with cold start/network excluded.
    # It can still establish identity of their proven structures and that
    # learned has positive non-amortized training overhead.
    return {
        "schema":"neumann.q3.first-relational-proof-reward-readonly-economics.v1",
        "original_FIRST_archive_SHA256":first_sha,
        "original_frozen_weights_SHA256":FIRST_WEIGHT_SHA,
        "identical_student_and_classical_h1_operator_on_holdouts":12,
        "identical_independent_original_symbolic_smt_obligation_hashes":48,
        "student_verified_heldout":12,
        "classical_direct_verified_heldout":12,
        "zero_weights_verified_heldout":0,
        "measured_training_wall_seconds":training,
        "train_independent_solver_calls":72,
        "heldout_independent_solver_calls_all_arms":f["heldout_z3_calls"],
        "student_independent_verification_ms_sum":round(student_proof_ms,3),
        "classical_independent_verification_ms_sum":round(classical_proof_ms,3),
        "trained_policy_additional_ability_at_equal_H1_grammar":False,
        "trained_policy_distinct_heldout_original_theorem_or_proof":False,
        "at_iso_capability_10x_total_cost_claim":"NOT_SUPPORTED",
        "measured_end_to_end_cost_ratio":"NOT_COMPARABLE_COLLECTED_IN_ONE_SHARED_EXPERIMENT",
        "required_next_science":"STOP synthetic 3-token proof reward; move to original CHC full-clause learned-new-operator proof",
        "model_training_reruns":0,"original_evaluation_reruns":0,
        "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN"
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--first",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=audit(a.first)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
