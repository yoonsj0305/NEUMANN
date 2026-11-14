"""First sealed tenth32 model behavior/cost audit; NO post-hoc original retuning.

SHA locks source X/Y, private full author truth, frozen model predictions,
independent grade from actual 3-stage Actions #39934318424. Entire ORIGINAL
first output is immutable. Audits executed graph edit ACTION distributions,
case-wise learned-only claims, macro-memory reuse, full source CPU accounts,
and actual exact original mathematical nonrational/rational categories.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_tenth import allowed_formula,calc,SYM
X=sp.Symbol("x")
LOCKS={"source":"a4aa84d77232e50fe199a0bfd417bed31b43d0c323a18fd239e92b81924ed799",
       "truth":"7d7ed619194535ff3fb87b27593eee04eeddf10cc96e1ec9afe9b3513cfa5df5",
       "pred":"917914e53c874e7edaffd86927e600e6850e862b0a7291d6943cf6cc04a7bf40",
       "grade":"5b7448bb5a9d81f9cb6063ca5a40af7b4b6235ed1e8ab2f4f6a00e7f4ec401d9"}
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def read(args,k):
    assert sha(getattr(args,k))==LOCKS[k],(k,"FIRST_RESULTS_MUTATED")
    return json.loads(pathlib.Path(getattr(args,k)).read_text())
def main(a):
    src=read(a,"source");truth=read(a,"truth");pred=read(a,"pred");grade=read(a,"grade")
    assert len(src["source_numeric_without_equations"])==len(truth["private_true_equations"])==32
    methods=pred["methods"]
    name_by_id={r["id"]:r["collection"]+":"+r["task_ID"] for r in truth["private_true_equations"]}
    truth_by_id={r["id"]:r for r in truth["private_true_equations"]}
    per_method={}
    solved={}
    for name,m in methods.items():
        actions=collections.Counter();macros=collections.Counter()
        for row in m["cases"]:
            actions.update(row["actions_executed"])
            for pr in row["candidate_macros"]:
                macros["all_source_valid"]+=1
                macros["new_"+str(pr.get("graph_action","RATIONAL_OR_REUSE"))]+=1
                macros["reused_from_training"]+=int(pr.get("reused_from_memory") is True)
        exact={r["id"] for r in grade["all_original32_case_receipts"][name]
               if r["status"]=="COMPLETE_ORIGINAL_SYMBOLICALLY_EXACT"}
        solved[name]=exact
        per_method[name]={
            "first_exact_full_author_originals":len(exact),
            "exact_author_ids_and_names":{i:name_by_id[i] for i in sorted(exact)},
            "selected_source_action_frequency":dict(actions),
            "first_source_candidate_macro_types":dict(macros),
            "actual_math_oracle_calls":m["source_counts"].get("source_verifier_calls",0),
            "source_only_CPU_s":m["test_candidate_CPU_s"]}
    learned=solved["D_learned_structural_top2"]
    full=solved["A_full_five_structure_actions"]
    fixed=solved["C_fixed_add_plus_rational"]
    random=solved["C_nolearn_random2"]
    assert len(learned)==5 and len(fixed)==len(full)==6 and len(random)==3
    original_cls=collections.Counter();auth=[]
    for row in truth["private_true_equations"]:
        try:
            ast,var=allowed_formula(row["original_expression"])
            expr=sp.cancel(sp.together(calc(ast,{var:X},SYM)))
            if not expr.is_rational_function(X):key="NONRATIONAL_TRUE_AUTHOR"
            else:
                try:
                    num,den=sp.fraction(expr)
                    p,q=sp.Poly(num,X),sp.Poly(den,X)
                    key=("RATIONAL_POLYNOMIAL" if q.degree()==0 else "RATIONAL_NONPOLYNOMIAL")
                except Exception:key="UNKNOWN_CANNOT_CERTIFY_RATIONAL_FORM"
        except Exception:key="UNKNOWN_SOURCE_PARSING"
        original_cls[key]+=1
        auth.append({"id":row["id"],"author_original_name":name_by_id[row["id"]],
          "first_true_function_class":key,"exact_by_learned":row["id"] in learned,
          "exact_by_fixed":row["id"] in fixed,"exact_by_random":row["id"] in random,
          "exact_by_full":row["id"] in full})
    tr=pred["training"]
    learned_cpu=tr["train_cpu_source_oracle_s"]+tr["train_cpu_structural_policy_s"]+methods["D_learned_structural_top2"]["test_candidate_CPU_s"]
    out={"schema":"NEUMANN_Q3_TENTH32_FIRST_FROZEN_LEARNED_STRUCTURE_POLICY_TRACE.v1",
         "first_original_evidence_SHA256":LOCKS,
         "method_model_and_all_classical":per_method,
         "original_true_expression_class":dict(original_cls),
         "all_original_32_rows":auth,
         "learned_unique_v_random":sorted(learned-random),
         "learned_unique_v_fixed":sorted(learned-fixed),
         "learned_unique_v_FULL5":sorted(learned-full),
         "fixed_unique_v_neural":sorted(fixed-learned),
         "correct_source_neural_only_over_ALL_same_rights":0,
         "known_source_neural_train_plus_eval_CPU_s":learned_cpu,
         "known_source_fixed_baseline_eval_CPU_s":methods["C_fixed_add_plus_rational"]["test_candidate_CPU_s"],
         "known_source_allfive_classical_eval_CPU_s":methods["A_full_five_structure_actions"]["test_candidate_CPU_s"],
         "source_training_actions_reward_samples":tr["source_reward_samples"],
         "actual_learned_structural_neural_policy_weights_SHA":tr["learned_action_model_weight_SHA256"],
         "true_reusable_training_macro_count":tr["self_rewarded_defined_macros"],
         "public_source_author_not_official_private_leaderboard":True,
         "methodological_caveat":"Structural action value model selects graph edit kind; candidate local optimizer and primitive semantics human-coded. All five same-structure-action classical is a superset of neural output; no learned-only gain beyond full possible.",
         "global_Q3":"OPEN","G1":"HOLD","full_system_10x":"NOT_PROVED"}
    p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("Q3_FIRST_TENTH32_IMMUTABLE_STRUCTURAL_GRAPH_POLICY_CAUSAL_AUDIT",
        json.dumps({"original_classes":dict(original_cls),
          "selected_modes":per_method["D_learned_structural_top2"]["selected_source_action_frequency"],
          "exact_learner_only_random":len(out["learned_unique_v_random"]),
          "exact_fixed_only_learner":len(out["fixed_unique_v_neural"]),
          "training_macro_reuse_valid_by_method":{k:v["first_source_candidate_macro_types"].get("reused_from_training",0) for k,v in per_method.items()},
          "known_learner_cpu":learned_cpu,
          "source_full_classical_cpu":out["known_source_allfive_classical_eval_CPU_s"],
          "sha256":sha(p)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in LOCKS:p.add_argument("--"+k,required=True)
    p.add_argument("--out",required=True)
    main(p.parse_args())
