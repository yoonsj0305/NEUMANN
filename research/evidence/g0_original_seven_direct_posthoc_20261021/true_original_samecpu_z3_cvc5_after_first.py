"""Posthoc strongest generic direct same-hardware recheck on ALL seven
frozen first-source competition-original STC cases. Not a new first run.

This direct screen does NOT receive learned/mod9 proposer-generated witnesses
or previously found 268/813 answers. Full original untouched SMT-LIB goes
to independent current Z3 and cvc5 (15 seconds each), accepting original
SAT only if exact independently checked grounded model, original UNSAT
only when independently both UNSAT. Timed out/unknown status preserved.
The prior FIRST 2/7 mod9 results remain immutable.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import audit_one

REV="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    fixed=json.loads(a.freeze.read_text())
    assert fixed["source"].endswith("@"+REV) and len(fixed["first_transfer_cohort"])==7
    cases=[audit_one(a.root,e) for e in fixed["first_transfer_cohort"]]
    if len({q["source"] for q in cases})!=7:raise RuntimeError("DUPLICATE_SOURCE")
    result={
      "schema":"neumann.G0.actual_frozen_first_seven_strong_direct_posthoc_bounded.v1",
      "the_7_first_source_result_remains_actions_39531276557":True,
      "posthoc_after_first_algorithm_witnesses_seen":True,
      "no_witness_given_to_generic_direct_solvers":True,
      "same_pinned_cvc5_z3_smt_versions_as_structural_proposer":True,
      "raw_original_authentic_source_count":sum(q.get("full_source_authenticated",False) for q in cases),
      "full_original_strong_generic_direct_15sec_independently_proven_count":sum(
         q["original_SAT_grounded_independent_confirmed"] or q["original_UNSAT_dual_confirmed"]
         for q in cases),
      "individual_solver_results":[
         {"source":q["source"],
          "z3":q.get("z3_direct",{}).get("status"),
          "cvc5":q.get("cvc5_direct",{}).get("status"),
          "independently_dual_proved":q["original_SAT_grounded_independent_confirmed"] or q["original_UNSAT_dual_confirmed"],
          "full_case_wall_ms":q["full_case_wall_ms"]}
         for q in cases],
      "no_learned_neural_oracle":True,
      "strongest_known_classical_specialized_three_cube_algorithm_not_compared":True,
      "not_certified_10x_vs_best_classical":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("G0_SEVEN_POSTHOC_STRONG_DIRECT_SOURCE_AUTHENTIC",result["raw_original_authentic_source_count"],"/7")
    print("G0_SEVEN_POSTHOC_STRONG_GENERIC_DIRECT_DUAL_ORIGINAL_SOLVED",
          result["full_original_strong_generic_direct_15sec_independently_proven_count"],"/7")
    print("Q3_GLOBAL",result["global_Q3"])
if __name__=="__main__":
    main()
