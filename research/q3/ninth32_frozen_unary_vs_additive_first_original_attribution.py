"""Causal-boundary-safe first-source model FROZEN transfer versus additive grammar.

The two actual source experiments were preregistered in separate PRs
before ninth author original expressions were exposed. This POSTGRADE
audit never labels either new 'fresh' after truth was publicly opened.

Importantly their source-only x/y observation artifacts are *different
sha*: compare original identities vs full x/y to expose unequal inputs.
Frozen eighth model must have attested byte-identical training weights
and macro history with its first eighth run before ninth independent grade.
Only conclude two empirical original32 solution-set counts and limitations.
"""
import argparse,hashlib,json,pathlib,collections
SHA={
 "frozen_source":"b82821aefe76f4ecabca345c65e7bfef7c54fa08e79bd8db29bdc393bc7694ab",
 "frozen_truth":"70177035c01d16a7c0ed0da003ee3049bc3d605ea282a16bf927ba22a80206e1",
 "frozen_pred":"d5a34eacf2b030ffe584b9f56b8ebae6aa366d23266fdf4a144ef61faf808137",
 "frozen_grade":"a848ca1abb440d948e918e16a2949942d21861ae6021e447928d97b16235b76d",
 "additive_source":"3640eeb5b460746b0d96dbc0b448a563d5810ee630e88c9aa28d6b4803d73efd",
 "additive_truth":"70177035c01d16a7c0ed0da003ee3049bc3d605ea282a16bf927ba22a80206e1",
 "additive_pred":"d00edb5e3ecb019286f8c18dc2f660613e20315854e966f7f1bc222251b147de",
 "additive_grade":"9f4235b00a706db6edeb4232bc51c03290f6d2439b75f54c1f7a2125d02accc7"}
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def read(args,k):
    actual=sha(getattr(args,k));assert actual==SHA[k],(k,actual,SHA[k])
    return json.loads(pathlib.Path(getattr(args,k)).read_text())
def solve(grade,method,key):
    return {r["id"] for r in grade["cases"][method] if r["status"]==key}
def main(args):
    original={k:read(args,k) for k in SHA}
    f=original
    src0=f["frozen_source"]["source_numeric_without_equations"]
    src1=f["additive_source"]["source_numeric_without_equations"]
    assert len(src0)==len(src1)==32
    assert {q["id"] for q in src0}=={q["id"] for q in src1}
    gold=f["frozen_truth"]["private_true_equations"]
    assert len(gold)==32 and f["frozen_truth"]==f["additive_truth"]
    key0="FULL_ORIGINAL_AUTHOR_SYMBOLICALLY_IDENTICAL"
    key1="FULL_AUTHOR_ORIGINAL_EXACT"
    methods_f={m:solve(f["frozen_grade"],m,key0) for m in f["frozen_grade"]["cases"]}
    methods_a={m:solve(f["additive_grade"],m,key1) for m in f["additive_grade"]["cases"]}
    assert len(methods_f["learned_graph_edit_512"])==2
    assert len(methods_f["complete_3920_classical"])==2
    assert len(methods_a["D_learned_macro_top80"])==5
    assert len(methods_a["A_all_basis_greedy_OMP"])==5
    assert methods_a["D_learned_macro_top80"]==methods_a["A_all_basis_greedy_OMP"]
    f_ids=set(methods_f["learned_graph_edit_512"])
    a_ids=set(methods_a["D_learned_macro_top80"])
    same_set=set(methods_f["complete_3920_classical"])
    assert len(a_ids-f_ids)>=2
    row0={q["id"]:q for q in src0};row1={q["id"]:q for q in src1}
    same_numeric=[]
    differing_numeric=[]
    for id in sorted(row0):
        arr0=(row0[id].get("x"),row0[id].get("y"))
        arr1=(row1[id].get("x"),row1[id].get("y"))
        if arr0==arr1:same_numeric.append(id)
        else:differing_numeric.append(id)
    t0=f["frozen_pred"]["training"]
    t1=f["additive_pred"]["training"]
    out={"schema":"NEUMANN_Q3_TWO_PREREGISTERED_NINTH32_FROZEN_MODEL_VS_NEW_ADDITIVE_MACRO.v1",
        "immutable_first_run_SHA256":SHA,
        "same_public_author_original32_frozen_truth_SHA":SHA["additive_truth"],
        "same_task_IDs_and_author_formulas":True,
        "identical_first_original_numeric_x_y_record_ids":same_numeric,
        "DIFFERENT_first_original_numeric_x_y_record_ids":differing_numeric,
        "numeric_observations_exactly_matched_for_all_tasks":len(differing_numeric)==0,
        "frozen_model_first_eighth_weights_and_macro_library_byte_identity":"PASS_FROM_SEPARATE_FIRST_CI_39927068026",
        "frozen_model_no_source_original_training_refit":True,
        "preregistered_frozen_algorithm_before_ninth_labels_seen_in_project":True,
        "project_level_first_ninth_truth_already_opened_by_additive_run_before_frozen_run_finished":True,
        "frozen_unary_first_true_exact":{k:sorted(v) for k,v in methods_f.items()},
        "additive_first_true_exact":{k:sorted(v) for k,v in methods_a.items()},
        "new_additive_learned_exact_beyond_frozen_unary_learned":sorted(a_ids-f_ids),
        "originals_lost_by_additive_vs_frozen_unary":sorted(f_ids-a_ids),
        "new_additive_programs_beyond_complete_frozen_unary_classical_SOLVED_SET":sorted(a_ids-same_set),
        "difference_in_original32_counts":len(a_ids)-len(f_ids),
        "frozen_unary_known_training_and_eval_CPU_s":(
           t0["verifier_source_train_CPU_s"]+t0["actual_MLP_fitting_CPU_s"]+
           f["frozen_pred"]["methods"]["learned_graph_edit_512"]["cpu_s"]),
        "additive_known_training_and_eval_CPU_s":(
           t1["train_reward_verifier_cpu_s"]+t1["neural_fit_cpu_s"]+
           f["additive_pred"]["Arms"]["D_learned_macro_top80"]["cpu_s"]),
        "frozen_unary_complete_3920_test_CPU_s":f["frozen_pred"]["methods"]["complete_3920_classical"]["cpu_s"],
        "additive_all264_OMP_test_CPU_s":f["additive_pred"]["Arms"]["A_all_basis_greedy_OMP"]["cpu_s"],
        "comparison_qualifier":"Different full output-program grammars, different estimators/optimization algorithms and possibly different numeric probe sets. Numbers do NOT isolate causal benefit of learned policy or macro-only grammar.",
        "learned_only_over_own_each_same_language_classical":False,
        "global_G1":"HOLD","global_Q3":"OPEN","system_total_10x":"NOT_PROVED"}
    p=pathlib.Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("Q3_ORIGINAL_NINTH_SAME_AUTHOR_FROZEN_WEIGHT_TRANSFER_VS_COMPOSED_TWO_TERM_MACROS",
       json.dumps({"identical_numeric":len(same_numeric),
        "different_numeric":len(differing_numeric),
        "frozen_originals":len(f_ids),"additive_originals":len(a_ids),
        "new_additive_vs_frozen":out["new_additive_learned_exact_beyond_frozen_unary_learned"],
        "frozen_known_cpu":out["frozen_unary_known_training_and_eval_CPU_s"],
        "additive_known_cpu":out["additive_known_training_and_eval_CPU_s"],
        "sha256":sha(p)},sort_keys=True),flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for k in SHA:parser.add_argument("--"+k.replace("_","-"),dest=k,required=True)
    parser.add_argument("--out",required=True)
    main(parser.parse_args())
