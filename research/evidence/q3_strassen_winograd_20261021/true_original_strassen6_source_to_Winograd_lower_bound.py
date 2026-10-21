"""Original Strassen-impossible source=>6-rank tensor and external Winograd lower bound.

The original source contains 4 universal real 2×2 matrix output equalities,
six shared products of an A-only linear form and B-only linear form, each with
independent real output weights, and a literal scalar 0 multiplying the
seventh term. A source-native exact AST bridge, independent Z3+cvc5 checks
of all four LHS targets and seventh term elimination, and an EXTERNALLY
published Winograd rank>=7 theorem jointly imply full original UNSAT.

Independent solvers DO NOT prove the Winograd theorem here. The classification
is explicitly CONDITIONAL ON EXTERNAL PUBLISHED MATHEMATICS. Source already
opened; NO new learned Q3, zero model forwards, no original answer oracle.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys,time
from pathlib import Path
from research.evidence.q3_strassen_exact_tensor_20261021.original_strassen_rank7_exact_bilinear_symbolic_witness import (
    sexp_extract_source_assertion,stringify,blob_sha,digest,expr_value,original_matrix_basis_inputs
)
from fractions import Fraction

SOURCE="non-incremental/NRA/20220222-strassen-matrix-multiplication/strassen-impossible.smt2"
SOURCE_SHA="9ffe078fd31c26792cde17c3d7c78e55691b0450"
PREREG_SHA="7f09ee21fb2d66f7301b3cfd00218222ae853b45"
INPUT=["a11","a12","a21","a22","b11","b12","b21","b22"]
POSITIONS=["11","12","21","22"]
TARGETS=[(("a11","b11"),("a12","b21")),
         (("a11","b12"),("a12","b22")),
         (("a21","b11"),("a22","b21")),
         (("a21","b12"),("a22","b22"))]

def parse_rank6_formula(source):
    tree=sexp_extract_source_assertion(source)
    exist=tree["all_existential_symbols"]
    if len(exist)!=80 or tree["universal_matrix_inputs"]!=INPUT:
        raise ValueError("TRUE_ORIGINAL_6_RANK_EXISTENTIAL_OR_INPUT_BINDERS_CHANGED")
    expected={f"w{out}{j}" for out in POSITIONS for j in range(1,7)}
    expected|={f"{p}{row}{col}{j}" for p in ("pa","pb")
              for row in (1,2) for col in (1,2) for j in range(1,8)}
    if len(expected)!=80 or set(exist)!=expected:
        raise ValueError("MISSING_OR_ADDITIONAL_NATIVE_WITNESS_SYMBOLS")

    checked_outputs=[];common_products={}
    for oi,(out,eq) in enumerate(zip(POSITIONS,tree["body"][1:])):
        if eq[0]!="=" or len(eq)!=3:
            raise ValueError("SOURCE_MISSING_ONE_OF_FOUR_ALL_REAL_OUTPUTS")
        rhs=eq[2]
        if not (isinstance(rhs,list) and rhs[0]=="+" and len(rhs)==8):
            raise ValueError("NATIVE_RHS_NOT_SEVEN_TERMS")
        for j,term in enumerate(rhs[1:],1):
            if not(isinstance(term,list) and len(term)==3 and term[0]=="*"):
                raise ValueError("NATIVE_RHS_TERM_NOT_SCALAR_TIMES_PRODUCT")
            coeff=term[1]
            if j<=6 and coeff!=f"w{out}{j}":
                raise ValueError("SOURCE_OUTPUT_WEIGHT_NOT_CORRECT_SHARED_PRODUCT")
            if j==7 and coeff!="0":
                raise ValueError("SEVENTH_PRODUCT_NOT_LITERAL_ZERO")
            mul=term[2]
            if not(isinstance(mul,list) and mul[0]=="*" and len(mul)==3):
                raise ValueError("OUTPUT_PRODUCT_NOT_EXACT_BILINEAR")
            pA,pB=mul[1],mul[2]
            if not(all(isinstance(q,list) and q[0]=="+" and len(q)==5
                       for q in (pA,pB))):
                raise ValueError("MISSING_EXACT_FOUR_INPUT_LINEAR_COEFFICIENTS")
            for p,prefix,bases in ((pA,"pa",INPUT[:4]),(pB,"pb",INPUT[4:])):
                for idx,(monom,var) in enumerate(zip(p[1:],bases)):
                    row,col=POSITIONS[idx]
                    if monom!=["*",f"{prefix}{row}{col}{j}",var]:
                        raise ValueError("NONLINEAR_OR_MIXED_INPUT_SOURCE_PRODUCT")
            common=(stringify(pA),stringify(pB))
            if j not in common_products:
                common_products[j]=common
            elif common_products[j]!=common:
                raise ValueError("SOURCE_RANK_ONE_PRODUCT_NOT_SHARED_ALL_FOUR_OUTPUTS")
        eq_coeff=[]
        for i in range(4):
            for j in range(4):
                env=original_matrix_basis_inputs(INPUT,i,j)
                eq_coeff.append(int(expr_value(eq[1],env)))
        source_expected=[
            1 if ((INPUT[i],INPUT[4+j]) in TARGETS[oi]) else 0
            for i in range(4) for j in range(4)]
        if eq_coeff!=source_expected:
            raise ValueError("TRUE_ORIGINAL_LHS_NOT_EXACT_2x2_MATMUL_TENSOR")
        checked_outputs.append({
            "source_output":out,
            "true_original_16_LHS_tensor_coefficients":eq_coeff,
            "exact_target_coefficients":source_expected,
            "source_full_RHS_SHA256":digest(stringify(rhs).encode()),
            "six_exact_active_products":True,
            "seventh_term_is_literal_zero":True,
        })
    return tree,checked_outputs,common_products

def reference_targets():
    return [f"(+ (* {a} {b}) (* {c} {d}))"
            for ((a,b),(c,d)) in TARGETS]

def independent_bridge(tree):
    # Verify on arbitrary Real-valued original matrix inputs that the 4 LHS
    # source expressions are EXACTLY the expected 2×2 matrix tensor;
    # and on arbitrary Real input/witness symbols, replacing the original
    # 7-term RHS with six active terms makes NO mathematical difference.
    lines=["(set-logic QF_NRA)"]
    for name in INPUT+tree["all_existential_symbols"]:
        lines.append("(declare-fun "+name+" () Real)")
    bad=[]
    for i,eq in enumerate(tree["body"][1:]):
        lhs,rhs=eq[1],eq[2]
        expected=reference_targets()[i]
        bad.append(f"(not (= {stringify(lhs)} {expected}))")
        six=["+"]+rhs[1:7]
        bad.append(f"(not (= {stringify(rhs)} {stringify(six)}))")
    lines.append("(assert (or "+" ".join(bad)+"))")
    lines+=["(check-sat)","(exit)"]
    smt="\n".join(lines)+"\n"
    checks={}
    for name in ("Z3_QF_NRA","cvc5_QF_NRA"):
        since=time.perf_counter_ns()
        if name.startswith("Z3"):
            code="import z3,sys;s=z3.SolverFor('QF_NRA');s.set(timeout=7000);s.from_string(sys.stdin.read());print(s.check())"
            cmd=[sys.executable,"-c",code]
        else:
            cmd=["cvc5","--lang=smt2","--tlimit-per=7000","-"]
        status="UNKNOWN";error=None
        try:
            p=subprocess.run(cmd,input=smt,text=True,capture_output=True,timeout=10)
            results=[s.strip().upper() for s in p.stdout.splitlines()
                     if s.strip().lower() in ("sat","unsat","unknown")]
            if p.returncode==0 and results:status=results[0]
            else:error="EXIT_"+str(p.returncode)+":"+p.stderr[:250]
        except Exception as e:
            error=type(e).__name__+":"+str(e)[:180]
        checks[name]={"source_exact_QFNRA_original_tensor_bridge_status":status,
                      "error":error,
                      "source_full_bridge_wall_ms":(time.perf_counter_ns()-since)/1e6}
    return {"QFNRA_exact_native_source_bridge_sha256":digest(smt.encode()),
            "actual_source_native_left_targets_AND_zero_seventh_term_dual_unsat":
                all(v["source_exact_QFNRA_original_tensor_bridge_status"]=="UNSAT"
                    for v in checks.values()),
            "two_independent_source_bridge_engines":checks,
            "SMT_proves_only_source_to_existing_lower_bound_PREMISES":True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--freeze",type=Path,required=True)
    parser.add_argument("--contract",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    prior=json.loads(a.contract.read_text())
    manifest=json.loads(a.freeze.read_text())
    if prior["schema"]!="neumann.q3.posthoc_strassen_impossible_original_source_bilinear_rank6_winograd_external.v1":
        raise RuntimeError("REAL_ORIGINAL_STRASSEN_EXTERNAL_CONTRACT_CHANGED")
    files={item["path"]:item for item in manifest["cases"]}
    if SOURCE not in files or files[SOURCE]["git_blob"]!=SOURCE_SHA:
        raise RuntimeError("AUTHENTIC_ORIGINAL_PRE_BLOB_FREEZE_CHANGED")
    start=time.perf_counter_ns()
    report={
      "schema":"neumann.q3.true_original_strassen6_rank_bridge_published_Winograd_UNSAT.v1",
      "pre_first_independent_published_theorem_source_run_git_commit":PREREG_SHA,
      "original_source_previously_OPENED":True,
      "all_80_source_exists_and_8_forall_reals_native_check":False,
      "all_four_original_multiplication_tensor_targets_validated":False,
      "all_six_native_common_rank_one_products_validated":False,
      "seventh_product_exact_original_literal_zero":False,
      "external_published_Winograd_rank7_required_not_locally_reproved":True,
      "published_Winograd_citation":"https://research.ibm.com/publications/on-multiplication-of-2-2-matrices",
      "external_theorem_disabled_ablation_original_status":"UNKNOWN",
      "original_status":"UNKNOWN",
      "no_neural_model_training_or_unique_structure_discovery":True,
      "strong_Direct_with_same_rank7_theorem_can_match":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN"}
    try:
        raw=(a.root/SOURCE).read_bytes()
        if len(raw)!=files[SOURCE]["bytes"] or blob_sha(raw)!=SOURCE_SHA:
            raise RuntimeError("TRUE_ORIGINAL_SOURCE_BLOB_OR_BYTES_MISMATCH")
        report["exact_real_original_SHA256"]=digest(raw)
        true,output,products=parse_rank6_formula(raw.decode("utf-8"))
        report["all_80_source_exists_and_8_forall_reals_native_check"]=True
        report["all_four_original_multiplication_tensor_targets_validated"]=True
        report["all_six_native_common_rank_one_products_validated"]=len(products)==7
        report["seventh_product_exact_original_literal_zero"]=True
        report["original_4x16_source_matrix_tensor_coefficients"]=output
        report["source_true_original_rank6_shared_products_sha256"]={
          str(k):[digest(x.encode()) for x in pair] for k,pair in products.items()}
        premise=independent_bridge(true)
        report["independent_source_to_rank6_premises_Z3_cvc5"]=premise
        if premise["actual_source_native_left_targets_AND_zero_seventh_term_dual_unsat"]:
            report["original_status"]="UNSAT_CONDITIONAL_ON_PUBLISHED_WINOGRAD_1971_RANK7_LOWER_BOUND"
        else:
            report["original_status"]="UNKNOWN_INDEPENDENT_SOURCE_BRIDGE_INCOMPLETE"
    except Exception as e:
        report["original_status"]="ABSTAIN_NOT_CERTIFIED"
        report["error"]=type(e).__name__+":"+str(e)[:440]
    report["full_source_extraction_and_Z3_cvc5_bridge_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_STRASSEN_REAL_ORIGINAL_SIX_RANK_SOURCE_NATIVE",
          report["all_six_native_common_rank_one_products_validated"])
    print("Q3_STRASSEN_ORIGINAL_LHS_2x2_TENSOR",
          report["all_four_original_multiplication_tensor_targets_validated"])
    print("Q3_STRASSEN_INDEPENDENT_SOURCE_TO_RANK6_DUAL",
          report.get("independent_source_to_rank6_premises_Z3_cvc5",{}).get(
              "actual_source_native_left_targets_AND_zero_seventh_term_dual_unsat"))
    print("Q3_STRASSEN_WINOGRAD_EXTERNAL_MATH_CONDITIONAL_ORIGINAL",report["original_status"])
    print("Q3_GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
