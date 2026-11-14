"""After-FIRST-grade external Nguyen author family + bitwise frozen neural audit.

All 4 artifacts pinned by SHA from run 39939206590, no retry of already
revealed actual authored Nguyen truth; this is a postgrade explanation only.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_eleventh import allowed_formula,calc,SYM
X=sp.Symbol("x")
LOCKS={
 "source":"4261350718c641ac0575e5d0a165a09fd02a5ba8aaa9eb5014fc82341bcbea10",
 "truth":"b4971e75b238b7525da34aab4bd4f7b7162f56a381a91e6fe667d9c651adeaaf",
 "pred":"f2d9626f0c27f3343e597e30ef6d4c3e6ed86bd107924038dd78dccc141444e9",
 "grade":"bbd4efc0f6b7f2127400d5f1d0a89bc739c133fa7545859c4a6ad61c07236fc1"}
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def main(a):
    for key,expected in LOCKS.items():
        assert sha(getattr(a,key))==expected,(key,"ORIGINAL_FIRST_ARTIFACT_SHA_MISMATCH")
    source=json.loads(pathlib.Path(a.source).read_text())
    truth=json.loads(pathlib.Path(a.truth).read_text())
    pred=json.loads(pathlib.Path(a.pred).read_text())
    grade=json.loads(pathlib.Path(a.grade).read_text())
    assert len(source["source_numeric_without_equations"])==len(truth["private_true_equations"])==8
    assert len(pred["methods"])==len(grade["grades"])==5
    original={r["id"]:r for r in truth["private_true_equations"]}
    cases={}
    for name,rows in grade["all8_original_cases"].items():
        cases[name]={v["id"]:v for v in rows}
    result=[];c=collections.Counter()
    for uid,sourcecase in original.items():
        model=cases["D_learned_derived_power_top2"][uid]
        fixed=cases["C_safe_add_rational"][uid]
        full=cases["A_full_same_actions"][uid]
        random=cases["C_random_two"][uid]
        tree,var=allowed_formula(sourcecase["original_expression"])
        expr=calc(tree,{var:X},SYM)
        isr=bool(sp.cancel(sp.together(expr)).is_rational_function(X))
        c["all"]+=1;c["learned_exact"]+=int(model["full_symbolic_original_exact"])
        c["safe_exact"]+=int(fixed["full_symbolic_original_exact"])
        c["full_exact"]+=int(full["full_symbolic_original_exact"])
        key="rational" if isr else "nonrational"
        c["class_"+key]+=1
        for m in model["verified_original_programs"]:
            assert sp.simplify(expr-sp.sympify(m["named_lambda"].removeprefix("lambda x: "),locals={"x":X}))==0
        result.append({"original_source_name":sourcecase["task_ID"],
          "original_source_expr":sourcecase["original_expression"],
          "analytic_family":key,
          "learned_exact":model["full_symbolic_original_exact"],
          "fixed_exact":fixed["full_symbolic_original_exact"],
          "random_exact":random["full_symbolic_original_exact"],
          "full_same_rights_exact":full["full_symbolic_original_exact"],
          "frozen_learned_true_programs":[x["named_lambda"] for x in model["verified_original_programs"]]})
    learned=pred["methods"]["D_learned_derived_power_top2"]
    chosen=collections.Counter(action for r in learned["cases"] for action in r["graph_actions"])
    tr=pred["methods"];t=pred
    known_CPU={k:v["inference_CPU_s"] for k,v in tr.items()}
    proof={"schema":"NEUMANN_Q6_FIRST_NGUYEN8_REAL_DIFFERENT_AUTHOR_FROZEN_OLD_NEURAL_VERDICT.v1",
      "first_original_exact_sha_locked":LOCKS,
      "prior_trained_MLP_weight_SHA256":pred["frozen_prior_weights_sha256"],
      "same_prior_MLP_weight_SHA256":pred["current_exact_weights_sha256"],
      "training_source_SHA256":pred["old_train_source_sha256"],
      "training_reward_MACRO_MEMORY_SHA_MATCH":"VERIFIED_BEFORE_THIS_FIRST_GRADE_IN_INFERENCE_JOB",
      "original_suite":"Nguyen-1..8 published NeurIPS 2021 Table9 1D; this evaluation custom 48 numerical source values, NOT 20-point official protocol",
      "originals":result,"counts":dict(c),
      "frozen_model_actual_nguyen_graph_action_choices":dict(chosen),
      "known_old_ERBench_training_CPU_from_previous_model":5.792755786,
      "Nguyen_source_inference_CPU_s_by_method":known_CPU,
      "learned_new_over_full_classical":0,
      "Nguyen_original_author_family_pretrained_neural_reuse":"SCOPED_PASS_2_OF_8",
      "scientific_verdict":"NO_ADVANTAGE_OVER_SIMPLE_FIXED_CLASSICAL_2_V_3",
      "different_author_task_distribution":True,
      "no_new_math_atomic_semantics":True,
      "G1":"HOLD","Q3_GLOBAL":"OPEN","Q6_STRONG_GENERALIZATION":"NOT_PROVED",
      "Q4_FRONTIER_ALL_IN_10X":"NOT_PROVED"}
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(proof,sort_keys=True,indent=2)+"\n")
    print("Q6_NGUYEN_EXTERNAL_AUTHOR_FROZEN_MLP_FIRST_ORIGINAL_EIGHT_CASE_AUDIT",
        json.dumps({"cases":result,"counts":dict(c),"frozen_model_action_choices":dict(chosen),
                   "sha256":sha(dest)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in LOCKS:p.add_argument("--"+k,required=True)
    p.add_argument("--out",required=True)
    main(p.parse_args())
