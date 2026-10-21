"""True original non-linear QF_NIA quotient pivot-substitution experiment.

No learning, no free source answer oracle. Mathematical equivalence of ORIGINAL
source complete 3×3 sum constraints and exact rational pivot equations over
original nonlinear power-feature terms independently checked by Z3 and cvc5.
All original other asserted clauses retained byte-for-byte in native AST.
Raw, exact row subset and non-linear quotient each have same capped Direct
backends, all real original zero/positive outcome statuses recorded.
"""
from __future__ import annotations
import argparse,json,math,subprocess,time
from pathlib import Path
import z3
from sympy import Matrix, ilcm
from research.evidence.q3_original_3x3_rank_20261021.exact_true_original_magic_power_rowspace_dual import (
    parse_true_source_linear_skeleton,frac_rank_exact,independent_source_rowspace_dual,row_qflia
)
from research.evidence.q3_original_3x3_deploy_20261021.compile_full_authentic_smt2_exact_rowspace_and_probe import (
    original_semantics_smt2,status_run
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256

UPSTREAM="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
PRE_RUN="179183548af0e21c74b17de41172b78927751460"

def rational_to_integral(R):
    converted=[]
    for i in range(R.rows):
        if all(R[i,j]==0 for j in range(R.cols)):continue
        denom=1
        for j in range(R.cols):
            denom=int(ilcm(denom,int(R[i,j].q)))
        whole=[int(R[i,j]*denom) for j in range(R.cols)]
        g=math.gcd(*whole)
        if g>1:whole=[n//g for n in whole]
        converted.append(whole)
    return converted

def native_original_monomial(name,k):
    x=z3.Int(name)
    if k==1:return x
    return z3.Product(*([x]*k))

def proof_lines(formal_a,formal_b):
    ncol=len(formal_a[0]);names=[f"formal_power_feature_{i}" for i in range(ncol)]
    def check_one(left,right):
        zvs=[z3.Int(name) for name in names]
        p=z3.Solver();p.set(timeout=4000)
        left_checks=[z3.Sum(*[coef*v for coef,v in zip(row,zvs)])==0 for row in left]
        right_checks=[z3.Sum(*[coef*v for coef,v in zip(row,zvs)])==0 for row in right]
        p.add(*left_checks,z3.Not(z3.And(*right_checks)))
        z_status=str(p.check()).upper()
        lines=["(set-logic QF_LIA)"]
        lines.extend(f"(declare-fun {v} () Int)" for v in names)
        lines.extend("(assert "+row_qflia(row,names)+")" for row in left)
        right_all="(and "+" ".join(row_qflia(row,names) for row in right)+")"
        lines.append("(assert (not "+right_all+"))")
        lines+=["(check-sat)","(exit)"]
        payload="\n".join(lines)+"\n"
        try:
            proc=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=4000","-"],
                input=payload,text=True,capture_output=True,timeout=6)
            status=[x.strip().upper() for x in proc.stdout.splitlines()
                    if x.strip().lower() in ("sat","unsat","unknown")]
            cvc=status[0] if proc.returncode==0 and status else "UNKNOWN"
        except subprocess.TimeoutExpired:cvc="UNKNOWN_TIMEOUT"
        return {"Z3":z_status,"cvc5":cvc,"both_independent_UNSAT":z_status==cvc=="UNSAT",
                "QF_LIA_formula_sha256":sha256(payload.encode())}
    return {"source_original_sum_implies_quotient":check_one(formal_a,formal_b),
            "quotient_implies_ALL_source_original_sums":check_one(formal_b,formal_a)}

def compile_authentic(root,item):
    ts=time.perf_counter_ns()
    result={"source":item["path"],"source_authenticated":False,
            "source_full_equivalence_original_quotient_dual":False,
            "status":"ABSTAIN"}
    try:
        b=(root/item["path"]).read_bytes()
        if len(b)!=item["bytes"] or git_blob_sha1(b)!=item["sha1_git_blob"]:
            raise RuntimeError("IMMUTABLE_AUTHENTIC_ORIGINAL_GIT_SHA_MISMATCH")
        result["source_authenticated"]=True
        result["true_original_source_sha256"]=sha256(b)
        original=z3.Solver();original.from_string(b.decode("utf-8"))
        ast=list(original.assertions())
        source_info,linear_rows=parse_true_source_linear_skeleton(original)
        mat=Matrix(linear_rows)
        rank=int(mat.rank())
        assert frac_rank_exact(linear_rows)==rank
        R,pivots=mat.rref()
        assert len(pivots)==rank and R.rows==len(linear_rows)
        pivot_equations=rational_to_integral(R)
        assert len(pivot_equations)==rank
        candidate=proof_lines(linear_rows,pivot_equations)
        result["original_source_linear_to_quotient_necessary_and_sufficient"]=candidate
        assert all(x["both_independent_UNSAT"] for x in candidate.values())
        chosen=list(mat.T.rref()[1])
        source_basis=independent_source_rowspace_dual(linear_rows,chosen)
        assert source_basis["both_actual_independent_skeleton_equivalence"]
        source_h=set(r["source_ast_sha256"] for r in source_info["source_rows"])
        basis_keep={source_info["source_rows"][i]["source_ast_sha256"] for i in chosen}
        assert len(source_h)==len(linear_rows) and len(basis_keep)==rank
        full_unrelated=[q for q in ast if sha256(q.sexpr().encode()) not in source_h]
        reduced_basis=full_unrelated+[q for q in ast if sha256(q.sexpr().encode()) in basis_keep]
        assert len(reduced_basis)==len(ast)-(len(linear_rows)-rank)
        # Build exact ORIGINAL nonlinear constraints from integer RREF
        # matrix: each column is one source-native x_i**k, last column t.
        actual_terms=[]
        for col in source_info["columns"]:
            if "^" in col:
                name,power=col.rsplit("^",1)
                actual_terms.append(native_original_monomial(name,int(power)))
            else:
                actual_terms.append(z3.Int(col))
        pivot_ast=[z3.Sum(*[coef*term for coef,term in zip(row,actual_terms)])==0
                   for row in pivot_equations]
        assert len(pivot_ast)==rank
        quotient_full=full_unrelated+pivot_ast
        assert all(q.sort().kind()==z3.Z3_BOOL_SORT for q in quotient_full)
        original_h=sorted(sha256(q.sexpr().encode()) for q in full_unrelated)
        # Every *non-sum* true original clause copied exactly into quotient.
        assert original_h==sorted(sha256(q.sexpr().encode()) for q in quotient_full
                                  if sha256(q.sexpr().encode()) in original_h)
        scripts={
            "raw_original":original_semantics_smt2(ast),
            "row_basis_original":original_semantics_smt2(reduced_basis),
            "exact_nonlinear_quotient_original":original_semantics_smt2(quotient_full)
        }
        for k,text in scripts.items():
            check=z3.Solver();check.from_string(text)
            assert len(check.assertions())=={
               "raw_original":len(ast),
               "row_basis_original":len(reduced_basis),
               "exact_nonlinear_quotient_original":len(quotient_full)
            }[k]
        result["exact_full_nonlinear_original_power_term_relation_preserved"]=True
        result["original_non_sum_assertions_identical_in_all_three"]=True
        result["original_linears_rank"]=rank
        result["source_original_full_linear_rows"]=len(linear_rows)
        result["source_original_formal_feature_vars"]=len(linear_rows[0])
        result["actual_original_quotient_free_features"]=len(linear_rows[0])-rank
        result["all_three_executable_source_SHA256"]={k:sha256(t.encode()) for k,t in scripts.items()}
        result["full_compiler_and_original_to_quotient_independent_dual_proof_ms"]=(time.perf_counter_ns()-ts)/1e6
        result["source_full_equivalence_original_quotient_dual"]=True
        # The *same* raw Z3 and cvc5 direct backends are run at the same
        # OS enforced hard cap, even for UNKNOWN. No solver gets answers.
        result["real_same_cpu_complete_original_solver_comparison"]={}
        for program,program_text in scripts.items():
            result["real_same_cpu_complete_original_solver_comparison"][program]={
                engine:status_run(engine,program_text) for engine in ("z3","cvc5")}
        observed=set()
        solved={}
        for label,arms in result["real_same_cpu_complete_original_solver_comparison"].items():
            statuses=[v["source_status"] for v in arms.values()]
            answers=set(statuses)&{"SAT","UNSAT"}
            observed.update(answers)
            solved[label]=next(iter(answers)) if len(answers)==1 else "UNKNOWN"
        result["all_original_same_problem_competing_program_results"]=solved
        result["raw_full_original_solved"]=solved["raw_original"] in ("SAT","UNSAT")
        result["quotient_extra_true_original_capability"]=not result["raw_full_original_solved"] and solved["exact_nonlinear_quotient_original"] in ("SAT","UNSAT")
        result["all_programs_agree_if_certified"]=len(observed)<=1
        result["status"]="TRUE_ORIGINAL_SAT_EQUIVALENT_NONLINEAR_QUOTIENT" if result["all_programs_agree_if_certified"] else "FAIL_CONFLICT_TRUE_ORIGINAL_SOLVERS"
        if not result["all_programs_agree_if_certified"]:
            result["source_full_equivalence_original_quotient_dual"]=False
    except Exception as e:
        result["status"]="ABSTAIN_EXCEPTION_NO_PROOF"
        result["error"]=type(e).__name__+":"+str(e)[:450]
    result["whole_experiment_wall_ms"]=(time.perf_counter_ns()-ts)/1e6
    print("Q3_REAL3X3_NONLINEAR_QUOTIENT",item["path"].split("/")[-1],
          "INDEPENDENT_EQ",result["source_full_equivalence_original_quotient_dual"],
          "SOLUTION",result.get("all_original_same_problem_competing_program_results"),
          "EXTRA",result.get("quotient_extra_true_original_capability"),
          "ERR",result.get("error"),flush=True)
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    v=ap.parse_args()
    c=json.loads(v.contract.read_text());f=json.loads(v.freeze.read_text())
    if c["schema"]!="neumann.q3.posthoc_three_by_three_exact_nonlinear_quotient_v1" or f["source"].split("@")[-1]!=UPSTREAM:
        raise RuntimeError("FROZEN_CONTRACT_OR_SOURCE_REVISION_CHANGED")
    cases=[compile_authentic(v.root,i) for i in f["five_original_3x3_controls"]]
    eq=sum(x["source_full_equivalence_original_quotient_dual"] for x in cases)
    outcome={
       "schema":"neumann.q3.20261021.actual_authentic_3x3_rref_nonlinear_quotient.v1",
       "source_posthoc_already_opened_not_first_blind":True,
       "preregistered_first_contract_commit":PRE_RUN,
       "all_five_genuine_sources_retained":len(cases)==5,
       "full_original_sha_authenticated":sum(x["source_authenticated"] for x in cases),
       "original_full_nonlinear_quotient_independent_Z3_cvc5_equivalence":eq,
       "raw_original_true_task_solved":sum(x.get("raw_full_original_solved",False) for x in cases),
       "new_original_task_capability_over_raw":sum(x.get("quotient_extra_true_original_capability",False) for x in cases),
       "all_new_or_old_backend_original_certified_results_consistent":all(x.get("all_programs_agree_if_certified",False) for x in cases),
       "no_learned_model_or_neural_forward":True,
       "strong_direct_with_same_rank_rewriter_could_do_identical":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
       "cases":cases
    }
    v.out.parent.mkdir(parents=True,exist_ok=True)
    v.out.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print("Q3_REAL3X3_QUOTIENT_FULL_SOURCE_Z3_CVC5_EQUIVALENCE",eq,"/5")
    print("Q3_REAL3X3_QUOTIENT_RAW_ORIGINAL_SOLVED",outcome["raw_original_true_task_solved"],"/5")
    print("Q3_REAL3X3_QUOTIENT_ADDITIONAL_TRUE_ORIGINAL_SOLVED",outcome["new_original_task_capability_over_raw"],"/5")
    print("Q3_Q4_GLOBAL_OPEN",outcome["global_Q3"],outcome["global_Q4"])
if __name__=="__main__":
    main()
