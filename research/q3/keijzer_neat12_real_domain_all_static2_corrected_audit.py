"""Q3 first opened two-author original12 real-domain-corrected 10 static pairs.

Certified first source-only predictions and FULL5 per-action replay are
immutable SHA pinned. Uses *independently proved* Keijzer7 positive REAL
logarithm identity to correct an underinclusive complex-valued grading
heuristic without ever changing original first model predictions or first
3-job gold.

This is postgrade, full positive-real domain, and only compares against
all C(5,2) FIXED, non-contextual 2-action strategies. Learned neural 5
is NOT dominant over the full five-action classical 6 or over every
possible context-adaptive classical routing policy.
"""
import argparse,hashlib,itertools,json,pathlib,sympy as sp
from keijzer7_strict_positive_real_log_author_firstgrade_audit import log_ratio

LOCKS={
    "original_truth":"560843ae60804dc5356f1215687707f76908291bfb424210d35b9238d1f94580",
    "original_firstgrade":"f3ad4c51c4ef35e576e56feebdb59d8b3ad4041e0acd99737edbe0a8025e8995",
    "source_each_action":"0f439a8f2f9b75650c0c413fa45b12428d4785cf2bd2145ddae14036608d1a1e",
    "independent_first_static_grade":"a32a821c0c0d40ae44f55270130533535ba3cf14160f49973284903b1d0005f9",
    "original_real_positive_domain_grade":"a3134f3c5bdd66252943a0131c29e8ee46f5c19e0230ba1fcf5b2fd4c067523b",
}
ACTIONS=("POLYNOMIAL","TRIG_PRODUCT","LOG_SUM","EXP_ROOT","SAFE")
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(args,role):
    digest=sha(getattr(args,role))
    assert digest==LOCKS[role],(role,"STRICT_FIRST_AUTHORED_MATH_EVIDENCE_MUTATED",digest,LOCKS[role])
    return json.loads(pathlib.Path(getattr(args,role)).read_text())
def run(args):
    truth=read(args,"original_truth")["private_true_equations"]
    original=read(args,"original_firstgrade")
    source=read(args,"source_each_action")
    graded=read(args,"independent_first_static_grade")
    real=read(args,"original_real_positive_domain_grade")
    assert len(truth)==len(source["per_task_source_action_replay"])==12
    assert graded["best_static_two_actions_exact_full_authors"]==3
    assert original["method_full_author_symbolic_exact"]["D_NEURAL_TOP2_GRAPH_FAMILIES"]["author_full_exact"]==5
    assert real["strict_aftergrade_REAL_domain_corrected_counts"]["D_NEURAL_TOP2_GRAPH_FAMILIES"]==5
    assert real["strict_aftergrade_REAL_domain_corrected_counts"]["A_ALL_SAME_GRAPH_ACTIONS"]==6
    authentic={z["id"]:z for z in truth}
    keijzer7=next(z for z in truth if z["task_ID"]=="Keijzer-7")
    kg=next(z for z in source["per_task_source_action_replay"] if z["id"]==keijzer7["id"])
    plus=sp.Symbol("x",positive=True,real=True)
    true=sp.sympify(keijzer7["author_full_expression_sympy"],locals={"x":plus})
    assert sp.simplify(true-sp.log(plus))==0
    logs=[q for q in kg["per_action_UNDEDUPLICATED_source_first_programs"] if q["family"]=="LOG_SUM"]
    assert len(logs)==1
    macro=logs[0]["source_executable_AST_candidate"]
    assert macro is not None
    alt=sp.sympify(macro["defined_operator_AST"],locals={"x":plus})
    cond=log_ratio(alt,plus)
    assert cond["status"]=="ALL_REAL_LOG_ARGUMENTS_POSITIVE",cond
    assert sp.cancel(cond["ratio_sym"]-plus)==0
    sets={a:set() for a in ACTIONS}
    for task in graded["original_independent_per_task_recheck"]:
        for b in task["per_action_entire_analytic_equivalence"]:
            if b["whole_author_exact"]:
                sets[b["action"]].add(task["id"])
    assert keijzer7["id"] not in set.union(*sets.values())
    # Only change is an exact whole positive-real mathematical proof for
    # Keijzer7 LOG_SUM, no candidate/prediction/model/template changes.
    sets["LOG_SUM"].add(keijzer7["id"])
    full=set.union(*sets.values())
    assert len(full)==6
    combos=[]
    for k in range(1,6):
        for actions in itertools.combinations(ACTIONS,k):
            solved=set.union(*(sets[a] for a in actions))
            combos.append({"global_FIXED_action_cardinality":k,
                           "fixed_action_names":list(actions),
                           "real_positive_author_exact_count":len(solved),
                           "entire_authored_equations":[r["task_ID"] for r in truth if r["id"] in solved]})
    pair=[x for x in combos if x["global_FIXED_action_cardinality"]==2]
    assert len(pair)==10 and len(combos)==31
    maxpair=max(v["real_positive_author_exact_count"] for v in pair)
    first_D={v["id"] for v in original["all_original_cases"]["D_NEURAL_TOP2_GRAPH_FAMILIES"]
             if v["status"]=="WHOLE_REAL_AUTHOR_EXACT"}
    assert len(first_D)==5
    needed_for_D=min(v["global_FIXED_action_cardinality"] for v in combos
                     if first_D.issubset(set(z["id"] for z in truth
                     if z["task_ID"] in v["entire_authored_equations"])))
    needed_full=min(v["global_FIXED_action_cardinality"] for v in combos
                    if v["real_positive_author_exact_count"]==6)
    answer={
        "schema":"NEUMANN_Q3_FIRST_TWO_AUTHORS12_REAL_DOMAIN_EXHAUSTIVE_10_STATIC_TWO_VS_NEURAL_ADAPTIVE.v1",
        "SHA_locked_five_evidence_artifacts":LOCKS,
        "source_model_and_first_original_full_expression_grader_UNMODIFIED":True,
        "full_original_author_real_positive_true_mathematical_domain":True,
        "first_strict_unconstrained_complex_grade_learned":5,
        "first_strict_unconstrained_complex_grade_all5":5,
        "corrected_real_author_domain_learned":len(first_D),
        "corrected_real_author_domain_full_classical":len(full),
        "all10_postgrade_undeuped_STATIC_TWO_full_domain_true_equivalence":pair,
        "all31_nonempty_GLOBAL_static_subsets":combos,
        "best_of_ten_global_static_two_action_original_exact":maxpair,
        "learned_neural_CONTEXTUAL_top2_true_authored_exact":len(first_D),
        "adaptive_learned_beats_EVERY_FIXED_STATIC_two_on_this_original12":len(first_D)>maxpair,
        "minimum_GLOBAL_static_action_count_to_cover_all_neural_exact5":needed_for_D,
        "minimum_GLOBAL_static_action_count_to_cover_ALL6_exact":needed_full,
        "true_author_action_sets":{a:[t["task_ID"] for t in truth if t["id"] in z] for a,z in sets.items()},
        "Keijzer7_full_real_domain_log_identity":{
             "source_generated_macro":macro["named_lambda"],
             "log_atoms_strictly_positive":cond["log_atoms"],
             "exact_log_product_ratio_equals_x":True,
             "original_truth":"ln(x), x>0",
             "first_grade_corrected_only_AFTER_AUTHOR_TRUTH":True},
        "fair_cost_lifecycle_train_included":"NOT_IN_THIS_STATIC_PAIR_CARDINALITY_METRIC",
        "not_superior_to_all5_classical_which_finds_six":True,
        "not_superior_to_all_possible_ADAPTIVE_CLASSICAL":True,
        "single_public_first12_aftergrade_not_new_private_benchmark":True,
        "global_G1":"HOLD","global_Q3":"OPEN","Q4_ALLIN10X":"NOT_PROVED"}
    p=pathlib.Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(answer,sort_keys=True,indent=2)+"\n")
    print("Q3_NEW_FIXED_PAIR_CAPABILITY_BOUND_REAL_DOMAIN_KEIJZER_NEAT12",
          json.dumps({"SHA256":sha(p),
            "adaptive_neural":len(first_D),"best_any_static_pair":maxpair,
            "all5_classical_mathematically_corrected":len(full),
            "global_static_min_to_cover_neural5":needed_for_D,
            "global_static_min_for_all6":needed_full,
            "action_sets":answer["true_author_action_sets"],
            "static_pairs":pair},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in LOCKS:p.add_argument("--"+k,required=True)
    p.add_argument("--out",required=True)
    run(p.parse_args())
