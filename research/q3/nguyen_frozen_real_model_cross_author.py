"""Cross-AUTHOR test of FROZEN already-trained ERBench neural action policy.

Identical code, training numeric ERBench 128, model seed and actual weights
sha256 to the EARLIER eleventh original first pregrade source model. No model
retraining choices based on Nguyen, no new operator grammar, no new fitting.

Test evaluation is Nguyen-1..8 publicly authored source-only 48 x-y and
physically withheld whole analytic original equation in an independent
third job. All five PRIOR arm actions and SAME language authority.
"""
import argparse,collections,json,pathlib,time
import numpy as np
import sympy as sp
from erbench_original_eleventh import sha,save,allowed_formula,calc,SYM
from learned_additive_macro_ninth32 import original_shape,X
from learned_derived_power_eleventh32 import ACTIONS,train,feature,eval_action

def infer(trainfile,first_pregrade,nguyen_source,out):
    old=json.loads(pathlib.Path(first_pregrade).read_text())
    assert old["schema"]=="NEUMANN_Q3_FIRST_ELEVENTH32_LEARNED_INDUCED_EXPLOG_POWER_MACROS.v1"
    assert len(old["methods"])==5
    model,meta=train(trainfile)
    frozen=old["training"]
    # Nothing trained on Nguyen target; exact SAME model and training source.
    for k in ("training_numeric_source_sha256","trained_weights_SHA256",
              "training_rewards_SHA256","memory_SHA256"):
        print("FROZEN_MODEL_DIGEST",k,meta[k],frozen[k],flush=True)
        assert meta[k]==frozen[k],("NEURAL_WEIGHTS_OR_SOURCE_CHANGED",k)
    source=json.loads(pathlib.Path(nguyen_source).read_text())
    assert len(source["source_numeric_without_equations"])==8
    assert all("original_expression" not in r for r in source["source_numeric_without_equations"])
    assert all(r["collection"]=="Nguyen2021Benchmark" for r in source["source_numeric_without_equations"])
    modes=("D_learned_derived_power_top2","C_safe_add_rational",
           "C_untrained_power_one_and_two","C_random_two","A_full_same_actions")
    rng=np.random.default_rng(71701)
    output={}
    for mode in modes:
        begun=time.process_time();cases=[];totals=collections.Counter()
        for row in source["source_numeric_without_equations"]:
            shape=original_shape(row.get("x",[]),row.get("y",[]))
            if shape is None:
                cases.append({"id":row["id"],"status":"UNKNOWN_INVALID_SOURCE",
                   "graph_actions":[],"source_proposals":[],"source_verifier_calls":0})
                continue
            if mode=="D_learned_derived_power_top2":
                value={a:float(model.predict([feature(shape,a)])[0]) for a in ACTIONS}
                chosen=sorted(ACTIONS,key=lambda a:(-value[a],a))[:2]
            elif mode=="C_safe_add_rational":chosen=["SAFE"]
            elif mode=="C_untrained_power_one_and_two":chosen=["POWER_ONE","POWER_TWO"]
            elif mode=="C_random_two":
                chosen=[ACTIONS[int(k)] for k in rng.choice(len(ACTIONS),size=2,replace=False)]
            else:chosen=list(ACTIONS)
            proposals=[];calls=0
            for act in chosen:
                _,programs,steps=eval_action(row,act)
                calls+=steps
                for p in programs:
                    if p["named_lambda"] not in {v["named_lambda"] for v in proposals}:
                        proposals.append(p)
            cases.append({"id":row["id"],"status":"SOURCE_VALID" if proposals else "UNKNOWN",
                         "graph_actions":chosen,"source_proposals":proposals,
                         "source_verifier_calls":calls})
            totals["calls"]+=calls
            totals["numerically_valid_source"]+=int(bool(proposals))
            totals["source_proposals"]+=len(proposals)
        output[mode]={"cases":cases,"inference_CPU_s":time.process_time()-begun,
                       "source_counts":dict(totals)}
    receipt={"schema":"NEUMANN_Q6_FIRST_INDEPENDENT_NGUYEN_AUTHOR_FROZEN_ERBENCH_NEURAL.v1",
       "first_earlier_ELEVENTH_PREGRADE_sha256":sha(pathlib.Path(first_pregrade).read_bytes()),
       "frozen_prior_weights_sha256":frozen["trained_weights_SHA256"],
       "current_exact_weights_sha256":meta["trained_weights_SHA256"],
       "old_train_source_sha256":frozen["training_numeric_source_sha256"],
       "current_train_source_sha256":meta["training_numeric_source_sha256"],
       "same_prior_model_weights_AND_REWARD_TRACE":True,
       "nguyen_source_numeric_no_original_SHA256":sha(pathlib.Path(nguyen_source).read_bytes()),
       "external_author_benchmark":"NGUYEN 1D 1..8, NeurIPS 2021 Table9, independent of ERBench",
       "source_sampling_points":48,
       "trained_original_equation_family":"PUBLIC ERBENCH ORIGINAL128",
       "nguyen_train_original_formula_used":False,
       "nguyen_true_formula_visible_at_inference":False,
       "all_human_defined_grammar_same_as_previous_ELVENTH":True,
       "methods":output,"G1":"HOLD","Q3":"OPEN","Q6_CROSS_AUTHOR":"PENDING_INDEPENDENT_GRADE"}
    signature=save(out,receipt)
    print("Q6_FIRST_NGUYEN8_STRICT_IDENTICAL_NEURAL_WEIGHTS_BEFORE_AUTHOR_TRUTH",json.dumps({
       "sha256":signature,"weights":meta["trained_weights_SHA256"],
       "methods":{k:{"source":v["source_counts"],"CPU":v["inference_CPU_s"]} for k,v in output.items()}},sort_keys=True),flush=True)

def grade(truthfile,predfile,out):
    gold=json.loads(pathlib.Path(truthfile).read_text())["private_true_equations"]
    pred=json.loads(pathlib.Path(predfile).read_text())
    assert len(gold)==8 and len(pred["methods"])==5
    byid={r["id"]:r for r in gold}
    grades={};allcases={}
    for mode,method in pred["methods"].items():
        counts=collections.Counter();records=[]
        for case in method["cases"]:
            item=byid[case["id"]]
            accepted=[]
            tree,var=allowed_formula(item["original_expression"])
            truth=calc(tree,{var:X},SYM)
            for proposed in case["source_proposals"]:
                try:
                    expr=sp.sympify(proposed["named_lambda"].removeprefix("lambda x: "),locals={"x":X})
                    if sp.simplify(truth-expr)==0:accepted.append(proposed)
                except Exception:pass
            counts["total"]+=1;counts["original_full_exact"]+=int(bool(accepted))
            counts["UNKNOWN"]+=int(not accepted)
            records.append({"id":case["id"],"Nguyen_original_task":item["task_ID"],
              "original_sha256":sha(item["original_expression"].encode()),
              "full_symbolic_original_exact":bool(accepted),
              "verified_original_programs":accepted,
              "status":"FULL_TRUE_NGUYEN_AUTHOR_FUNCTION_PROVED" if accepted else "UNKNOWN"})
        grades[mode]=dict(counts);allcases[mode]=records
    solved={m:{r["id"] for r in rows if r["full_symbolic_original_exact"]} for m,rows in allcases.items()}
    D=solved["D_learned_derived_power_top2"]
    report={"schema":"NEUMANN_Q6_FIRST_TRUE_CROSS_AUTHOR_NGUYEN8_FROZEN_ELEVENTH_NEURAL_GRADE.v1",
      "frozen_source_only_pred_SHA256":sha(pathlib.Path(predfile).read_bytes()),
      "true_independent_Nguyen_author_SHA256":sha(pathlib.Path(truthfile).read_bytes()),
      "grades":grades,"all8_original_cases":allcases,
      "learned_original_extra_over_SAFE":sorted(D-solved["C_safe_add_rational"]),
      "learned_original_extra_over_FULL_classical":sorted(D-solved["A_full_same_actions"]),
      "learned_original_extra_over_random":sorted(D-solved["C_random_two"]),
      "true_new_benchmark_family_pretrained_weight_transfer":True,
      "score_not_official_20_sample_protocol":True,
      "no_new_neural_operator_semantic_atoms":True,
      "G1":"HOLD","Q3_GLOBAL":"OPEN","Q6":"SCOPED_AUTHOR_TRANSFER_VERIFIED_NOT_GLOBAL","Q4_ALLIN10X":"UNPROVED"}
    signature=save(out,report)
    print("Q6_FIRST_NGUYEN_INDEPENDENT_AUTHOR_FROZEN_REAL_MODEL_FULL_EXACT_GRADE",json.dumps({
       "sha256":signature,"scores":grades,
       "learned_extra_vs_all_classical":len(report["learned_original_extra_over_FULL_classical"]),
       "learned_extra_vs_SAFE":len(report["learned_original_extra_over_SAFE"])},sort_keys=True),flush=True)
    assert all(x["total"]==8 for x in grades.values())
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("infer","grade"),required=True)
    for k in ("train","old","source","truth","pred","out"):p.add_argument("--"+k)
    a=p.parse_args()
    if a.mode=="infer":infer(a.train,a.old,a.source,a.pred)
    else:grade(a.truth,a.pred,a.out)
