"""Audits the ALREADY FINISHED first two-author Q3 neural graph study.

Read ONLY first GitHub Actions #40067150397 immutable artifacts by exact SHA.
This file NEVER proposes a new original answer, changes the trained model,
regrades a changed hypothesis, or claims study is a new first-blind benchmark.

Scientific outcomes:
- original exact whole-author equations grouped by INDEPENDENT benchmark author
- learned actual action coverage & correct true-source graph definitions
- model-vs-strong same-rights source training/inference CPU and verifier counts
- CONDITIONAL steady-state inference break-even assuming *future comparable
  novel tasks* with reused trained weights (not observed transfer superiority)
- duplicated analytic author formulas exposed, preventing 12 independent
  original analytic laws from being accidentally asserted.

Necessary and sufficient model source actions, primitive meanings, fixed CPU
budget, external PySR baseline and global Q3/Q4 remain separate hypotheses.
"""
import argparse,collections,hashlib,json,math,pathlib
import sympy as sp

LOCKS={
    "source":"e22b82e4cfb47fe605e1b049e01359d1752d7bbb26146d421faf08e71696ba32",
    "truth":"560843ae60804dc5356f1215687707f76908291bfb424210d35b9238d1f94580",
    "pred":"d6a0d41e5f58f50fbf563aa5d7aabe0e760bbaa63d473c5205b8f2f29bc327b0",
    "grade":"f3ad4c51c4ef35e576e56feebdb59d8b3ad4041e0acd99737edbe0a8025e8995",
}
D="D_NEURAL_TOP2_GRAPH_FAMILIES"
A="A_ALL_SAME_GRAPH_ACTIONS"
FIXED=("C_FIXED_POLY_SAFE","C_FIXED_TRIG_LOG","C_FIXED_EXP_SAFE")
C=("C_FIXED_POLY_SAFE","C_FIXED_TRIG_LOG","C_FIXED_EXP_SAFE","C_RANDOM_TWO")
EXPECTED_IDS=("Keijzer-1","Keijzer-2","Keijzer-3","Keijzer-4",
              "Keijzer-7","Keijzer-8","Keijzer-9",
              "Neat-1","Neat-2","Neat-3","Neat-4","Neat-6")
def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def file_read(args,role):
    got=sha(getattr(args,role))
    assert got==LOCKS[role],("FIRST_RUN_EVIDENCE_NOT_IMMUTABLE",role,got,LOCKS[role])
    return json.loads(pathlib.Path(getattr(args,role)).read_text())
def ceiling_positive_ratio(num,denom):
    if denom<=0:return None
    return max(1,math.ceil((num-1e-10)/denom))
def report(args):
    src=file_read(args,"source");gold=file_read(args,"truth")
    pred=file_read(args,"pred");first=file_read(args,"grade")
    xrows=src["source_numeric_without_equations"]
    rows=gold["private_true_equations"]
    assert len(xrows)==len(rows)==12
    assert tuple(r["task_ID"] for r in rows)==EXPECTED_IDS
    assert {x["id"] for x in xrows}=={r["id"] for r in rows}
    assert all("original_expression" not in x for x in xrows)
    assert first["frozen_graph_policy_source_proposals_SHA256"]==LOCKS["pred"]
    assert first["private_published_author_original_full_truth_sha256"]==LOCKS["truth"]
    assert first["G1"]=="HOLD" and first["Q3_GLOBAL"]=="OPEN"
    names=[D,*C,A]
    original={q["id"]:q for q in rows}
    all_source={r["id"]:r for r in xrows}
    solved={}
    first_grade={}
    source_cases={}
    for name in names:
        source_cases[name]={r["id"]:r for r in pred["methods"][name]["cases"]}
        first_grade[name]={r["id"]:r for r in first["all_original_cases"][name]}
        assert len(source_cases[name])==len(first_grade[name])==12
        correct={
            r["id"] for r in first["all_original_cases"][name]
            if r["status"]=="WHOLE_REAL_AUTHOR_EXACT"
        }
        solved[name]=correct
        assert first["method_full_author_symbolic_exact"][name]["all"]==12
        assert first["method_full_author_symbolic_exact"][name]["author_full_exact"]==len(correct)
        assert all(set(first_grade[name])==set(original) for _ in range(1))
    assert len(solved[D])==len(solved[A])==5
    assert len(solved["C_FIXED_POLY_SAFE"])==3
    assert len(solved["C_FIXED_EXP_SAFE"])==2
    assert len(solved["C_FIXED_TRIG_LOG"])==2
    assert len(solved["C_RANDOM_TWO"])==2
    assert solved[D].issubset(solved[A])
    original_union=set.union(*(solved[c] for c in C))
    assert solved[D].issubset(original_union)
    x=sp.Symbol("x");x_real=sp.Symbol("x",real=True)
    all_cases=[]
    math_types=collections.Counter()
    per_family={fam:{n:[] for n in names} for fam in ("DSO_Keijzer","DSO_Neat")}
    expression_class={}
    independent_laws=[]
    for row in rows:
        task_id=row["id"];fam=row["collection"]
        assert fam in per_family
        true=sp.sympify(row["author_full_expression_sympy"],locals={"x":x_real}).subs(x_real,x)
        canonical=sp.cancel(sp.together(true))
        eqclass=("RATIONAL" if canonical.is_rational_function(x) else "NONRATIONAL")
        math_types[eqclass]+=1
        found_same=False
        for z in independent_laws:
            try:
                if sp.simplify(z["representative"]-canonical)==0:
                    z["task_ids"].append(row["task_ID"])
                    found_same=True
                    break
            except Exception:pass
        if not found_same:independent_laws.append({"representative":canonical,
                                                      "task_ids":[row["task_ID"]]})
        verified_macros={}
        for name in names:
            if task_id in solved[name]:
                per_family[fam][name].append(row["task_ID"])
                grade_macros=first_grade[name][task_id]["certified_source_built_macros"]
                assert grade_macros
                # Second independently implemented whole function math
                # certification of each first source-proposed answer.
                for p in grade_macros:
                    candidate=sp.sympify(p["defined_operator_AST"],locals={"x":x})
                    assert sp.simplify(true-candidate)==0,(name,row["task_ID"],"FALSE_MATH")
                    assert p["named_lambda"] in {
                        z["named_lambda"] for z in
                        source_cases[name][task_id]["source_valid_defined_macros"]
                    },("RETROSPECTIVELY_ADDED_PROGRAM",name,row["task_ID"])
                verified_macros[name]=[
                    {"lambda":p["named_lambda"],
                     "action":p.get("structural_action_family")}
                     for p in grade_macros[:3]]
        all_cases.append({
            "task_id":row["task_ID"],"author_family":fam,
            "published_author_formula_sha256":hashlib.sha256(
                row["original_expression"].encode()).hexdigest(),
            "source_exactly_48_numeric_samples":len(all_source[task_id]["x"])==len(all_source[task_id]["y"])==48,
            "math_expression_type":eqclass,
            "solution_flags":{m:task_id in {r["task_ID"] for r in rows if r["id"] in solved[m]} for m in names},
            "first_source_generated_witnesses":verified_macros,
            "D_pregrade_selected_structure_actions":source_cases[D][task_id]["selected_graph_edit_families"],
            "D_original_graph_nodes":source_cases[D][task_id]["constructed_graph_nodes"],
            "D_original_verifier_calls":source_cases[D][task_id]["verifier_calls"],
        })
    training=pred["synthetic_neural_training"]
    train_cpu=training["source_verifier_train_cpu"]+training["trained_neural_CPU"]
    train_calls=training["source_verifier_calls"]
    eval_d=pred["methods"][D]["eval_CPU_s"];eval_a=pred["methods"][A]["eval_CPU_s"]
    calls_d=pred["methods"][D]["source_counts"]["verifier_calls"]
    calls_a=pred["methods"][A]["source_counts"]["verifier_calls"]
    assert 0<eval_d<eval_a and calls_d<calls_a
    s=eval_a-eval_d;c=calls_a-calls_d
    # Two different amortization statements. Both HYPOTHETICAL; first
    # original model is NOT measured on 12 or more unseen repetitions.
    cpu_batches=ceiling_positive_ratio(train_cpu,s)
    call_batches=ceiling_positive_ratio(train_calls,c)
    # Count total evaluations when a single cached policy is used to serve
    # N equal-sized original12 benchmarks; ignoring data prep/CI/setup.
    assert train_cpu+cpu_batches*eval_d <= cpu_batches*eval_a+1e-8
    assert train_calls+call_batches*calls_d <= call_batches*calls_a
    payload={
        "schema":"NEUMANN_Q3_FIRST_KEIJZER_NEAT12_ORIGINAL_SHA_LOCKED_AUTHOR_COST_AND_ANSWER_AUDIT.v1",
        "first_successful_original_GitHub_Actions_run":40067150397,
        "first_4_evidence_sha256":LOCKS,
        "genuine_first_original12_original_author_task_count":12,
        "non_independent_duplicate_formula_classes_count":len(independent_laws),
        "duplicate_expression_equivalence_classes":[
             {"tasks":z["task_ids"],"representative":str(z["representative"])}
             for z in independent_laws],
        "author_math_type_counts":dict(math_types),
        "first_original12_per_problem_full_function_certified":all_cases,
        "per_author_family_all_methods_exact_tasks":per_family,
        "full_math_solution_IDs_by_method":{
            name:[row["task_ID"] for row in rows if row["id"] in solved[name]]
            for name in names},
        "neural_first_full_author_exact":len(solved[D]),
        "same_language_classical_first_full_author_exact":len(solved[A]),
        "neural_exclusive_against_all_equal_rights_classical":[],
        "neural_exclusive_against_union_simple_2action_classical":[],
        "source_test_CPU_s_neural":eval_d,
        "source_test_CPU_s_all5_classical":eval_a,
        "source_test_speedup_same_first_originals":eval_a/eval_d,
        "source_test_verifier_calls_neural":calls_d,
        "source_test_verifier_calls_all5_classical":calls_a,
        "source_test_verifier_call_reduction_factor":calls_a/calls_d,
        "training_verifier_calls":train_calls,
        "training_and_model_CPU_s":train_cpu,
        "first_author12_model_train_plus_eval_CPU_s":train_cpu+eval_d,
        "first_author12_classical_all5_test_only_CPU_s":eval_a,
        "conditional_minimum_similar_12_task_batches_to_amortize_CPU":cpu_batches,
        "conditional_minimum_similar_12_task_batches_to_amortize_verifier_calls":call_batches,
        "conditional_amortization_requires":"Identical pretrained policy reused with no refit; each UNSEEN future 12-task batch has observed first-batch accuracy and speed; common preprocessing and grading costs ignored. NOT measured actual cross-task amortized 10x.",
        "source_budget_comparison_note":"All5 classical expands five legal programs versus learned chooses two; both same primitive rights and 48 input y/x, but total training cost must be charged to learned arm.",
        "strong_GP_CEGIS_baseline":"NOT_EXECUTED",
        "independent_original_author_family":True,
        "public_original_formula_or_not_official_benchmark":"PUBLIC custom 48-point development protocol, no private contest claim",
        "global_Q3":"OPEN","G1":"HOLD","Q4_FULL_COST_FRONTIER_10X":"NOT_PROVED",
    }
    path=pathlib.Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
    print("Q3_FIRST_TWO_AUTHOR12_SHA_LOCKED_MATHEMATICAL_INDEPENDENT_AUDIT",
          json.dumps({"first12_neural_full_exact":len(solved[D]),
           "first12_full_classical_exact":len(solved[A]),
           "neural_exact_by_family":{f:per_family[f][D] for f in per_family},
           "full_classical_exact_by_family":{f:per_family[f][A] for f in per_family},
           "distinct_analytic_laws":len(independent_laws),
           "training_CPU":train_cpu,
           "inference_speedup":eval_a/eval_d,
           "verifier_call_speedup":calls_a/calls_d,
           "amortization_batches_CPU_conditional":cpu_batches,
           "amortization_batches_calls_conditional":call_batches,
           "report_sha256":sha(path)},sort_keys=True),flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for k in LOCKS:parser.add_argument("--"+k,required=True)
    parser.add_argument("--out",required=True)
    report(parser.parse_args())
