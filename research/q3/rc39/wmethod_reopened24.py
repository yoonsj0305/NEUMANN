"""POST-FIRST same 24 opened RC39 tasks: classical W-method vs enumeration.

All original FIRST receipts are immutable. This is a new verification-cost
ablation, not a new independent-family or autonomous-neural-discovery test.
Reference target graphs are only imported to make the membership callback
and the independent AFTER-freeze product audit. The conformance tester itself
never receives the graph. No favorable regrading of original results.
"""
from __future__ import annotations
import json
from time import process_time_ns

from research.q3.rc39.active_mealy import ActiveMealyLearner, MealyProgram
from research.q3.rc39.membership_conformance import compare_source_rights
from research.q3.rc39.wmethod_conformance import compare_wmethod_source_rights
from research.q3.rc39.independent_first_grader import hidden_family, independent_product_prove

FAMILIES = ("prefix_parity", "prefix_mod3", "presence",
            "random_3state", "random_4state", "random_5state")
SEEDS = (39, 40, 41, 42)


def run():
    start = process_time_ns()
    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            hidden = hidden_family(family, seed)
            assert hidden.n <= 5
            def learner():
                return ActiveMealyLearner("ABC", "01", max_states=8,
                        max_membership=100000, max_equivalence=200)
            # Same source rights and budget for both classical methods.
            baseline = compare_source_rights(
                learner(), hidden.run, upper_bound=5,
                source_cap=100000, conformance_cap=100000)
            proposed = compare_wmethod_source_rights(
                learner(), hidden.run, upper_bound=5,
                source_cap=100000, conformance_cap=100000)
            programs=[]
            for receipt in (baseline,proposed):
                model=(MealyProgram.from_source(receipt["model_source"])
                       if receipt["model_source"] else None)
                proof=independent_product_prove(hidden,model) if model else {"equivalent":False,"counterexample":None}
                programs.append(bool(proof["equivalent"]))
            rows.append({
                "family":family,"seed":seed,
                "reference_states_evaluator_only":hidden.n,
                "enumeration":{"status":baseline["status"],
                    "independently_equivalent":programs[0],
                    "distinct_source_calls":baseline["total_unique_source_membership_calls"],
                    "distinct_source_symbols":baseline["total_unique_source_symbols"],
                    "conformance_words":baseline["conformance_full_word_checks"],
                    "cpu_ms":baseline["total_process_cpu_ms"]},
                "wmethod":{"status":proposed["status"],
                    "independently_equivalent":programs[1],
                    "distinct_source_calls":proposed["total_unique_source_membership_calls"],
                    "distinct_source_symbols":proposed["total_unique_source_symbols"],
                    "conformance_words":proposed["conformance_full_word_checks"],
                    "cpu_ms":proposed["total_process_cpu_ms"],
                    "verified_with_classical_wmethod":True}
            })
    a=sum(r["enumeration"]["distinct_source_calls"] for r in rows)
    b=sum(r["wmethod"]["distinct_source_calls"] for r in rows)
    good=all(r[key]["status"]=="SCOPED_ALL_LENGTHS_PROVED" and
             r[key]["independently_equivalent"]
             for r in rows for key in ("enumeration","wmethod"))
    return {
        "schema":"neumann.q3.rc39.classical-wmethod.reopened24.v1",
        "cohort":"SAME PREVIOUSLY OPENED 24; not first heldout",
        "finite_state_bound_assumption":5,
        "comparison":"identical source membership interface and limits; two classical verifiers",
        "n_tasks":len(rows),"same_rights_all_length_pass":good,
        "reference_enumeration_distinct_queries":a,
        "candidate_wmethod_distinct_queries":b,
        "source_call_reduction_ratio":(a/b if b else None),
        "source_call_reduction_percent":((a-b)/a*100 if a else None),
        "total_cpu_ms_measured_sequentially":(process_time_ns()-start)/1e6,
        "Q3_neural_discovery":"OPEN", "Q6_independent_family":"OPEN",
        "Q4_classical_over_neural_10x":"NOT_TESTED",
        "rows":rows
    }


if __name__=="__main__":
    out=run()
    print(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2))
    if not out["same_rights_all_length_pass"]:
        raise SystemExit(1)
