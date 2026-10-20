"""NEUMANN 1 Q3: one FIRST SHA-frozen cross-origin bounded G1 audit.

Five public SyGuS originals from two named independent submission families.
Before any original source body read, reconstruct and freeze previous exactly
42 trained coefficient weights, prove their operator equals exact classical
discrete antidifference algebraically for *all* degree<=5 inputs.

Then run unchanged actual source-trained frozen 42-weight+co-clock code AND
same-input exact classical candidate, source-by-source with subprocess
isolation and explicit cap. No model retraining from targets, no gold.

No global Q3 or frontier 10x claims. Whole 5-row negative result preserved.
"""
from __future__ import annotations
import argparse,hashlib,json,math,multiprocessing,os,re,time
from pathlib import Path

import numpy as np
import sympy as sp

from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import (
    train_frozen_operator, SCALE, DEG_DELTA, DEG_F)
from research.evidence.q3_coclock_fixed42_20261020.posthoc_genuine_source_affine_controller import (
    one as exact_actual_original_dual_classical_comparison)

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
TARGETS=(
 ("xujie_code2inv","lib/Inv_Track/xujie_code2inv/1.c.sl","859bae24a9f26044a40a3c97f1d2e5fc08504f06"),
 ("xujie_code2inv","lib/Inv_Track/xujie_code2inv/10.c.sl","22bcd1792d96ccdfcd2c829999cb37f6b7f373ba"),
 ("xujie_code2inv","lib/Inv_Track/xujie_code2inv/100.c.sl","ec31090e13e75640447f234a7e2b58cfd09b1086"),
 ("andrew_lustre","lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl","8490b3e25ff7d462a7405e68e742be1abb35b8f8"),
 ("andrew_lustre","lib/Inv_Track/andrew_lustre/DRAGON_2.lus.sl","17f0cea250008e9e3575d38181f7e40804501dde"),
)
WEIGHT_SHA="563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78"
TIMEOUT_PER_SOURCE_S=35

def millis(t):return round((time.perf_counter_ns()-t)/1e6,3)
def hash_blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def exact_discrete_operator_theorem(weight_matrix):
    """Exact rational matrix identity, not empirical high test accuracy."""
    start=time.perf_counter_ns()
    assert weight_matrix.shape==(6,7)
    # D maps F coefficients [f0,..,f6] to increment δ coeffs [δ0,..,δ5].
    D=sp.Matrix(6,7,lambda row,col:
        sp.binomial(col,row) if col>row else sp.Integer(0))
    W=sp.Matrix([[int(c) for c in row] for row in weight_matrix.tolist()])
    learned=sp.Rational(1,SCALE)*W.T
    identity=D*learned
    unique_exact=sp.Matrix.vstack(sp.zeros(1,6),D[:,1:].inv())
    assert D.rank()==6 and D[:,1:].det()!=0
    # Independently check F(0)=0 and perfect Δ for each basis vector.
    assert all(learned[0,j]==0 for j in range(6))
    assert identity==sp.eye(6)
    assert unique_exact==learned
    # Negative control: any perturbation breaks the identity or initial F(0).
    corrupted=sp.Matrix(learned)
    corrupted[1,0]+=sp.Rational(1,SCALE)
    assert D*corrupted!=sp.eye(6)
    return {
      "theorem":"For every rational polynomial δ of degree<=5, there exists exactly one F of degree<=6 with F(0)=0 and F(t+1)-F(t)=δ(t)",
      "source":"exact binomial finite-difference coefficient matrix over Q",
      "delta_dimension":6,"integral_dimension":7,
      "D_rank":int(D.rank()),"D_right_6x6_nonzero_determinant":str(D[:,1:].det()),
      "operator_coordinates_D_6x7":[[int(v) for v in D.row(i)] for i in range(6)],
      "frozen_learned_W_6x7":[[int(v) for v in W.row(i)] for i in range(6)],
      "matrix_identity_D_times_frozen_WT_over_5040_equals_I6":identity==sp.eye(6),
      "trained_F_zero_at_t0_for_all_delta":True,
      "canonical_exact_classical_integrator_equals_learned_operator":unique_exact==learned,
      "perturbed_weight_negative_control_fails":True,
      "mathematically_limited_Q3_claim":"CLOSED_FAIL_LEARNED_EXCLUSIVE_NEW_OPERATOR_WITHIN_FIXED_DEGREE6_GRAMMAR",
      "NOT_global_model_family_no_go":True,
      "exact_theorem_proof_wall_ms":millis(start)
    }

def state_header_has_boolean(raw):
    """Read only declared state typing; no target inspection for model fitting."""
    txt=raw.decode("utf-8")
    m=re.search(r"\(synth-inv\s+[^\s()]+\s+\(",txt)
    if not m:return "ABSTAIN_NO_STANDARD_SYNTH_INV_HEADER"
    tail=txt[m.end():]
    # Matching parameter-list parentheses only (not the whole source).
    balance=1;end=None
    for idx,ch in enumerate(tail):
        if ch=="(":balance+=1
        elif ch==")":
            balance-=1
            if balance==0:
                end=idx;break
        if idx>160000:break
    if end is None:return "ABSTAIN_UNPARSEABLE_STATE_SORT_DECLARATION"
    signature=tail[:end]
    all_sorts=re.findall(r"\b(Int|Bool|Real|BitVec)\b",signature)
    if not all_sorts:return "ABSTAIN_NO_EXPLICIT_SORTS"
    if any(t!="Int" for t in all_sorts):
        return "ABSTAIN_UNSUPPORTED_NON_INTEGER_STATE_SORTS"
    return "INTEGER_TYPED_STATE"

def child(queue,root,rel,gitsha,weights):
    try:
        result=exact_actual_original_dual_classical_comparison(root,rel,gitsha,weights)
        queue.put({"ok":True,"result":result})
    except BaseException as exc:
        queue.put({"ok":False,"error":type(exc).__name__+":"+str(exc)[:350]})

def one_source(root,origin,rel,expected,weights):
    began=time.perf_counter_ns()
    row={"origin_group":origin,"original_source":rel,"frozen_git_blob":expected,
         "learned_first_source_3VC":False,"same_input_classical_source_3VC":False,
         "source_science_status":"UNASSESSED"}
    try:
        raw=(root/rel).read_bytes()
        got=hash_blob(raw)
        if got!=expected:raise ValueError("PRE_REGISTERED_SOURCE_BLOB_SHA_MISMATCH")
        row["source_sha256"]=hashlib.sha256(raw).hexdigest()
        row["source_bytes"]=len(raw)
        signature=state_header_has_boolean(raw)
        row["original_state_sort_grammar"]=signature
        if signature!="INTEGER_TYPED_STATE":
            row["source_science_status"]=signature
            return row
        # Avoid a huge or unsupported external source exhausting all remaining
        # CPU budget; exact same cap for the neural/classical pair in child.
        ctx=multiprocessing.get_context("fork")
        queue=ctx.Queue()
        proc=ctx.Process(target=child,args=(queue,root,rel,expected,weights))
        proc.start()
        proc.join(TIMEOUT_PER_SOURCE_S)
        if proc.is_alive():
            proc.terminate()
            proc.join(5)
            if proc.is_alive():proc.kill();proc.join()
            row["source_science_status"]="ABSTAIN_SOURCE_SOLVER_TIMEOUT"
            return row
        if queue.empty():
            row["source_science_status"]="ABSTAIN_SUBPROCESS_FAILURE"
            row["subprocess_exit_code"]=proc.exitcode
            return row
        evidence=queue.get_nowait()
        if not evidence["ok"]:
            row["source_science_status"]="ABSTAIN_CHILD_ERROR"
            row["child_error"]=evidence["error"]
            return row
        old=evidence["result"]
        row["original_dual_semantics"]=old.get("original_pre_trans_post_native_custom_xor")
        row["model_generation_attempt"]=old.get("learned_source_generated")
        row["matched_strong_classical_attempt"]=old.get("classical_source_generated")
        row["original_model_3VC"]=old.get("learned_original_3VC")
        row["original_classical_3VC"]=old.get("classical_original_3VC")
        row["learned_first_source_3VC"]=bool(old.get("learned_full_original_dual_3VC"))
        row["same_input_classical_source_3VC"]=bool(old.get("classical_full_original_dual_3VC"))
        row["original_generated_candidate_identity"]=old.get("identical_candidate_invariant_text")
        row["original_solver_error"]=old.get("error")
        row["original_worker_status"]=old.get("status")
        row["source_science_status"]=(
          "DUAL_INDEPENDENT_BOTH_MODELS_PROVED" if
          row["learned_first_source_3VC"] and row["same_input_classical_source_3VC"]
          else "UNPROVEN_OR_UNSUPPORTED_NOT_LEARNED_UNIQUE")
    except Exception as exc:
        row["source_science_status"]="ABSTAIN_SOURCE_IDENTITY_OR_IO_ERROR"
        row["source_error"]=type(exc).__name__+":"+str(exc)[:250]
    finally:
        row["source_wall_ms"]=millis(began)
    return row

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    started=time.perf_counter_ns()

    # THIS MUST HAPPEN BEFORE A SINGLE SOURCE BODY IS OPENED:
    weights,trained=train_frozen_operator()
    if trained["frozen_trained_weights_sha256"]!=WEIGHT_SHA:
        raise RuntimeError("FROZEN_TRAINED_MODEL_HASH_CHANGED")
    theorem=exact_discrete_operator_theorem(weights)
    print("BEFORE_REAL_SOURCE: TRAINED_SHA",WEIGHT_SHA,
          "UNIVERSAL_EXACT_CLASSICAL_IDENTITY",theorem["canonical_exact_classical_integrator_equals_learned_operator"],
          flush=True)

    rows=[]
    for origin,path,expected in TARGETS:
        result=one_source(args.root,origin,path,expected,weights)
        rows.append(result)
        print("INDEPENDENT_REAL_SOURCE",origin,path,
          result["source_science_status"],
          "learned",result["learned_first_source_3VC"],
          "classical",result["same_input_classical_source_3VC"],flush=True)
    report={
      "schema":"neumann.q3.preregistered_independent_origins_exact_operator_no_go.v1",
      "upstream_revision":UPSTREAM,
      "frozen_pre_content_source_contract":"docs/research/Q3_INDEPENDENT_ORIGIN_FIVE_PRE_SOURCE_FREEZE_20261020.md",
      "frozen_model_weight_sha256":WEIGHT_SHA,
      "model_training_replayed_before_any_original_content_read":True,
      "trained_42_weight_model":trained,
      "exact_algebraic_uniqueness_proof":theorem,
      "two_named_origins_in_one_curated_repo_not_proof_of_separate_authors":True,
      "all_five_source_hashes_verified":all(x.get("source_sha256") for x in rows),
      "all_five_source_rows_retained":len(rows)==5,
      "supported_original_integer_state_cases":sum(x.get("original_state_sort_grammar")=="INTEGER_TYPED_STATE" for x in rows),
      "learned_first_original_3VC_pass_count":sum(x["learned_first_source_3VC"] for x in rows),
      "matched_strong_classical_3VC_pass_count":sum(x["same_input_classical_source_3VC"] for x in rows),
      "original_learned_novel_operator_outside_fixed_polynomial_grammar":False,
      "fixed_operator_learned_exclusive_new_primitive":"BOUNDED_MATHEMATICAL_NO_GO_PROVED",
      "new_architectures_with_unbounded_grammars":"NOT_TESTED",
      "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
      "total_wall_including_synthetic_training_and_proofs_ms":millis(started),
      "all_GPU_calls":0,"all_paid_API_calls":0,
      "five_actual_original_sources":rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("FINAL_FIVE_ORIGINAL_PASS",report["learned_first_original_3VC_pass_count"],
          "STRONG_CLASSIC",report["matched_strong_classical_3VC_pass_count"],
          "BOUNDED_THEOREM",report["fixed_operator_learned_exclusive_new_primitive"],
          "GLOBAL_Q3 OPEN",flush=True)

if __name__=="__main__":main()
