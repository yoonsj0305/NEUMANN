"""Exhaustive exact Q3 impossibility of fixed 19-template operator vocabulary.

Given original source Pre:x=1, Trans:x'=x+k, and operator candidate
I_m(x)=(x-1) mod m==0, universally inductive closure demands m|k.
Proof:
  If m|k, (x-1) mod m=0 -> (x+k-1) mod m=0.
  If m does NOT divide k, original witness x=1, x'=1+k violates it.
The strong original goal additionally requires m=k among positive prime
examples: if proper m|k, x=1+m is an I_m state but not goal mod k.

Frozen m∈{2,...,20}; OOD original primes k=23,29,31,37 are NOT
divisible by any m. No parameter training or compute budget could
recover exact original inductive safety in THIS fixed invariant family.
All 76 formal original SAT counterexamples are independently Z3+cvc5
certified; no unknown or guessed worst-case.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
from research.evidence.q3_modular_operator_selection_20261022.learn_mod_operator_and_dual_prove import (
    OPTIONS,certified_source)
OOD=(23,29,31,37)
POS=(5,7,11,13,17,19)
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args()
    records=[]
    for k in OOD:
        for m in OPTIONS:
            m=int(m)
            if k%m==0:raise AssertionError("OOD_PRIME_DIVISIBILITY_ASSUMPTION_FALSE")
            certificate=certified_source(k,m)
            if not certificate[1]["independent_dual_sat"]:
                raise AssertionError("EXPECTED_ORIGINAL_CONSECUTION_SAT_MISSING")
            # Smallest simple SOURCE model counterexample to induction:
            # Pre state x=1, original step x'=1+k.
            initial=1
            successor=1+k
            if (initial-1)%m!=0 or (successor-1)%m==0:
                raise AssertionError("CONCRETE_SOURCE_WITNESS_NOT_ACTUAL")
            records.append(dict(original_source_k=k,candidate_operator_m=m,
                frozen_feature_vocabulary="mod(m) m=2..20",
                exact_necessary_inductiveness_condition="m divides k",
                original_canonical_counterexample_x=initial,
                original_canonical_counterexample_xnext=successor,
                original_source_real_independent_Z3_cvc5=certificate,
                source_inductive_invariant_mathematically_impossible=True))
        print("EXHAUSTIVE_Q3_IMPOSSIBILITY_SOURCE",k,"ALL_19_INDUCTIVE_MODELS_REFUTED",flush=True)
    controls=[]
    for k in POS:
        certificate=certified_source(k,k)
        if not all(z["independent_dual_unsat"] for z in certificate):
            raise AssertionError("KNOWN_IN_VOCABULARY_POSITIVE_CONTROL_FAILED")
        controls.append(dict(k=k,candidate_m=k,source_original_complete_safe=True,
                             independent_original_full_Z3_cvc5_3VC=certificate))
    result=dict(schema="neumann.q3.exact_entire_fixed_mod_operator_grammar_impossibility.v1",
      mathematical_iff_inductiveness="For transition x_next=x+k, invariant (x-1) mod m=0 is inductive iff m divides k; source state x=1 witnesses SAT otherwise",
      operator_candidates=[int(x) for x in OPTIONS],
      OOD_genuine_mathematical_sources=list(OOD),
      total_candidate_times_original_source_checks=len(records),
      ALL_76_independently_certified_original_consecution_SAT=len(records)==76,
      admissible_model_candidates_within_vocabulary=0,
      every_model_of_ANY_weights_fail_original_vc=True,
      exact_source_veto_witnesses=len(records),
      positive_source_complete_dual_proof_controls=len(controls),
      learned_primitive_generated=False,
      no_new_external_real_benchmark_source_tested=True,
      globally_all_program_invariant_impossibility_not_claimed=True,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
      all_fixed_operator_source_counterexamples=records,
      positive_in_vocab_actual_original_source_proofs=controls)
    dst=Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("EXHAUSTIVE_IMPOSSIBILITY_ALL_CANDIDATES",len(records),flush=True)
    print("EXHAUSTIVE_IMPOSSIBILITY_POSITIVE_CONTROLS",len(controls),flush=True)
    print("EXHAUSTIVE_IMPOSSIBILITY_OUTPUT_SHA256",hashlib.sha256(dst.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
