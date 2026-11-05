"""RC39 source-rights ablation on the SAME 24 previously opened originals.

No model's hidden graph is supplied to the learner or its finite conformance
tester. Oracle backend only returns per-word output strings. Separate
reference-graph product checker scores compiled programs AFTER they are frozen.
This is a post-FIRST ablation, not a new unseen benchmark or neural policy.
"""
from __future__ import annotations
from hashlib import sha1
from pathlib import Path
from time import process_time_ns
import json,sys
from research.q3.rc39.active_mealy import ActiveMealyLearner,MealyProgram
from research.q3.rc39.membership_conformance import compare_source_rights
from research.q3.rc39.independent_first_grader import hidden_family,independent_product_prove

ROOT=Path(__file__).resolve().parents[3]
def blob(p):
    x=p.read_bytes()
    return sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def run():
    preregPath=ROOT/"docs/experiments/q3_RC39_MEMBERSHIP_ONLY_REOPENED24_PREREG.json"
    prereg=json.loads(preregPath.read_text())
    lock=json.loads((ROOT/"docs/experiments/q3_RC39_FIRST_LEARNER_SOURCE_LOCK.json").read_text())
    assert blob(ROOT/"research/q3/rc39/active_mealy.py")==lock["original_source_git_blob"]
    assert prereg["original_learner_blob"]==lock["original_source_git_blob"]
    source_rights=prereg["source_rights"]
    n=source_rights["upperbound_true_states"]
    assert n==5
    t0=process_time_ns();rows=[]
    for family in ["prefix_parity","prefix_mod3","presence","random_3state","random_4state","random_5state"]:
        for seed in (39,40,41,42):
            reference=hidden_family(family,seed)
            assert reference.n<=n, "Contract n≤5 has a real independently checked basis"
            learner=ActiveMealyLearner("ABC","01",max_states=8,
                 max_membership=source_rights["max_distinct_membership_queries_per_task"],
                 max_equivalence=source_rights["max_active_equivalence_callback_calls_per_task"])
            # Critical interface: this function supplies ONLY string output,
            # not the hidden reference graph, reference state count, or exact EQ.
            output=lambda w,ref=reference:ref.run(w)
            result=compare_source_rights(
               learner,output,upper_bound=n,
               source_cap=source_rights["max_distinct_membership_queries_per_task"],
               conformance_cap=100000)
            compiled=MealyProgram.from_source(result["model_source"]) if result["model_source"] else None
            # Independent hidden graph is introduced only after output frozen.
            proof=independent_product_prove(reference,compiled) if compiled else {
                "equivalent":False,"counterexample":None,"nodes":0}
            rows.append({
                "family":family,"seed":seed,"reference_states_evaluator_only":reference.n,
                "model_generated":result["model_source"],
                "source_only_claim_status":result["status"],
                "full_word_membership_certificate":result["completed_completeness_cutoff"] is not None,
                "independent_product_exact":proof["equivalent"],
                "independent_discrepancy":proof["counterexample"],
                "independent_product_nodes":proof["nodes"],
                **{k:v for k,v in result.items() if k!="model_source"}
            })
    def total(k):return sum(r[k] or 0 for r in rows)
    allproven=sum(r["independent_product_exact"] for r in rows)
    falsecert=sum((r["source_only_claim_status"]=="SCOPED_ALL_LENGTHS_PROVED"
                  and not r["independent_product_exact"]) for r in rows)
    complete=sum(r["full_word_membership_certificate"] for r in rows)
    full=(allproven==24 and complete==24 and falsecert==0 and
           all(r["source_only_claim_status"]=="SCOPED_ALL_LENGTHS_PROVED" for r in rows))
    return {
       "schema":"neumann.q3.rc39.postfirst-membership-only-24.v1",
       "scope":"REUSED_OPENED_24_SAME_HIDDEN_STATE_FAMILY_NOT_NEW_HELDOUT",
       "learner_original_source_blob":lock["original_source_git_blob"],
       "upper_bound_on_reference_states":n,
       "uses_hidden_reference_graph_during_learning":False,
       "uses_true_equivalence_counterexamples_during_learning":False,
       "source_membership_queries_serve_all_distinguishing_chores":True,
       "exact_all_length_if_bound_respected":True,
       "science_status":"SCOPED_MEMBERSHIP_ONLY_FIRST_24_PASS" if full else "RC39_MEMBERSHIP_ONLY_24_FAIL",
       "tasks":len(rows),"independently_all_length_proven":allproven,
       "false_all_length_certificates":falsecert,
       "completed_finite_membership_conformance_certificates":complete,
       "metrics":{
         "source_distinct_membership_calls":total("total_unique_source_membership_calls"),
         "source_distinct_membership_symbols":total("total_unique_source_symbols"),
         "all_source_membership_requests_including_cache":total("all_source_query_requests_including_cached"),
         "conformance_words_checked":total("conformance_full_word_checks"),
         "conformance_callbacks":total("conformance_callbacks"),
         "combined_cpu_ms":(process_time_ns()-t0)/1e6,
         "per_task_max_distinct_source_membership":max(r["total_unique_source_membership_calls"] for r in rows),
         "per_task_max_conformance_probe":max(r["conformance_full_word_checks"] for r in rows)
       },
       "Q3_autonomous_neural_opcode":"NOT_PROVEN","Q6_unseen_semantic_family":"NOT_PROVEN",
       "Q4_same_rights_10x":"NOT_PROVEN","Q7_frontier":"NOT_PROVEN",
       "rows":rows
    }
if __name__=="__main__":
    result=run()
    print(json.dumps(result,indent=2))
    if result["science_status"]=="RC39_MEMBERSHIP_ONLY_24_FAIL":
        raise SystemExit(1)
