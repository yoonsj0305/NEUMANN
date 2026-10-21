"""Proof-carrying structural proposal admission boundary, Q3 Runtime Gate 0.

Read original immutable dual SMT receipts from two independent official CI
runs (24 in-vocabulary, 16 out-of-vocabulary). Every proposal is untrusted.
Accept only triple UNSAT from Z3 AND cvc5 on the ORIGINAL mathematical source;
reject a dual SAT counterexample; require independently certified fallback
before returning SAFE. This is a frozen policy replay, not a NEW external
independent test, not solver rerun, not model-primitive invention.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
SHA_IN="d5a03f1de2efa96be043f2439e3643606f6837aadb71058438cc759139db9d0e"
SHA_OOD="23ff7ab7545f0910cb4f4c790db4af89821795b15fdd9a22ec255ef2281c0168"
def load(path,expected):
    b=Path(path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=expected:raise RuntimeError("OFFICIAL_ARTIFACT_SHA_DRIFT")
    return json.loads(b)
def full_dual(c):
    if len(c)!=3 or [q["name"] for q in c]!=["init","consecution","goal"]:
        raise AssertionError("INCOMPLETE_ORIGINAL_SOURCE_THREE_VC")
    return all(z["independent_dual_unsat"] and z["Z3"]=="unsat" and z["cvc5"]=="unsat" for z in c)
def counterexample(c):
    return len(c)==3 and c[1]["independent_dual_sat"] and c[1]["Z3"]==c[1]["cvc5"]=="sat"
def fingerprint(src):
    s=json.dumps(src,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(s).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for k in ("known","unseen","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    x=load(a.known,SHA_IN);y=load(a.unseen,SHA_OOD)
    if x["schema"]!="neumann.q3.learned_modular_selector_vs_exact_gcd_native_dual_source.v1":
        raise RuntimeError("WRONG_PRIOR_KNOWN_SOURCE_EXPERIMENT")
    if y["schema"]!="neumann.q3.ood_fixed_primitive_vocabulary_failclosed_gcd.v1":
        raise RuntimeError("WRONG_PRIOR_OOD_SOURCE_EXPERIMENT")
    known=x["original_source_lemmas_and_all_receipts"]
    outside=y["evidence"]
    if len(known)!=24 or len(outside)!=16:raise RuntimeError("SOURCE_COHORT_COUNT_CHANGED")
    rows=[]
    for e in known:
        source=e["source_original_AST"]
        proof=e["true_original_dual_source_3VC"]
        classical=e["exact_gcd_classical_dual_source_3VC"]
        if not full_dual(proof) or not full_dual(classical):
            raise AssertionError("MODEL_OR_CLASSICAL_SOURCE_CERTIFICATE_INCOMPLETE")
        if not counterexample(e["mutated_source_trans_k_plus_one_dual_3VC"]):
            raise AssertionError("SOURCE_MUTANT_NOT_REJECTED")
        rows.append(dict(source_sha256=fingerprint(source),
             source_family="synthetic_modular_from_provided_vocabulary",
             observed_seed=e["experiment_seed"],
             proposed_expression=f"x % {e['trained_categorical_operator']['candidate']}",
             operator_origin="provided_mod_primitive_and_bounded_parameter_candidates",
             original_source_inductive_proof_dual=proof,
             decision="ACCEPT_PROVEN_ORIGINAL_SOURCE",
             source_SAFE=True,model_primitive_invention=False,
             independent_strong_classical_also_SAFE=True))
    for e in outside:
        source=e["original_program_AST"]
        learned=e["source_original_model_independent_three_VC"]
        strong=e["native_original_Z3_cvc5_complete_SAFE"]
        if full_dual(learned):raise AssertionError("OUT_OF_VOCABULARY_UNEXPECTED_MODEL_PROOF")
        if not counterexample(learned):raise AssertionError("MISSING_ORIGINAL_NEGATIVE_CONSECUTION_SAT")
        if not full_dual(strong):raise AssertionError("UNPROVEN_ORIGINAL_CLASSICAL_DEGRADED_MODE")
        rows.append(dict(source_sha256=fingerprint(source),
             source_family="synthetic_outside_frozen_modulus_parameter_vocabulary",
             observed_seed=e["seed"],
             proposed_expression=f"x % {e['model_selected_m']}",
             operator_origin="unsupported_frozen_2_20_parameter_range",
             original_source_inductive_proof_dual=learned,
             decision="REJECT_UNVERIFIED_AND_EXECUTE_PROVEN_CLASSICAL",
             source_SAFE=True,model_primitive_invention=False,
             rejected_due_to_true_original_SAT=True,
             original_gcd_degraded_candidate=e["source_native_exact_classical_fallback_m"],
             independent_classical_fallback_full_3VC=strong))
    if len(rows)!=40:raise AssertionError("INTEGRATION_DROPPED_SOURCE")
    status={k:sum(r["decision"]==k for r in rows) for k in (
       "ACCEPT_PROVEN_ORIGINAL_SOURCE","REJECT_UNVERIFIED_AND_EXECUTE_PROVEN_CLASSICAL")}
    if status!={"ACCEPT_PROVEN_ORIGINAL_SOURCE":24,
               "REJECT_UNVERIFIED_AND_EXECUTE_PROVEN_CLASSICAL":16}:
        raise AssertionError("PROOF_ADMISSION_FALSE_VERDICT")
    if not all(r["source_SAFE"] for r in rows):
        raise AssertionError("ORIGINAL_PROOF_MISSING_AFTER_FALLBACK")
    report=dict(schema="neumann.q3.proof_carrying_structural_source_admission_40.v1",
        scientific_scope="REPLAY of prior two executed CI proofs; NOT source-independent verification rerun and NOT real external original transfer",
        official_runs={"in_vocabulary":39623533296,"out_of_vocabulary":39624265173},
        pinned_original_raw_artifact_SHA256={"in_vocabulary":SHA_IN,"out_of_vocabulary":SHA_OOD},
        policy_interface=[
          "canonical_source_sha256","proposed_expression_AST","model_operator_origin",
          "original_independent_three_VCs","ACCEPT_OR_REJECT",
          "certified_classical_degraded_recovery","full_cost_receipt"],
        total_original_source_observations=len(rows),
        independently_PREVIOUSLY_certified_model_admissions=status["ACCEPT_PROVEN_ORIGINAL_SOURCE"],
        previously_source_SAT_refuted_model_proposals=status["REJECT_UNVERIFIED_AND_EXECUTE_PROVEN_CLASSICAL"],
        independent_original_classical_fallback_completed=status["REJECT_UNVERIFIED_AND_EXECUTE_PROVEN_CLASSICAL"],
        model_unsafe_original_source_admissions=0,
        post_decision_source_safe=40,
        all_expressions_from_provided_modulo_operator_grammar=True,
        novel_model_operator_primitive_count=0,
        classical_strong_results_dominate_in_model_unsupported_cases=True,
        not_a_new_Q3_structural_novelty_or_frontier_speed_proof=True,
        original_real_programs_not_tested=True,
        global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",source_decision_ledger=rows)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("total_original_source_observations",
              "independently_PREVIOUSLY_certified_model_admissions",
              "previously_source_SAT_refuted_model_proposals",
              "independent_original_classical_fallback_completed",
              "model_unsafe_original_source_admissions"):
        print("Q3_PROOF_CARRYING_OPERATOR_GATE",k,report[k],flush=True)
    print("PROOF_CARRYING_GATE_JSON_SHA",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
