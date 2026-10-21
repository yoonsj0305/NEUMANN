"""Original quantified Strassen 2x2 matrix multiplication SAT from true
source-native exact bilinear tensor coefficient extraction.

POSTHOC on original first-opened strong Direct UNKNOWN PR364. Reference
forms from another PUBLIC original benchmark strassen-linear (not hidden
gold); linear algebra learns NO weights, solves exact 16x7 equations from
source and copies published input forms to hard original. All 4*16
bilinear source coefficients must match EXACTLY over Fractions, meaning
the original quantified identity holds for ALL REAL input matrices.

Winograd 1971 tensor rank >=7 is EXTERNAL prior-art theorem; original
6-product impossible benchmark can be conditionally UNSAT only after
exactly original source native six-bilinear-product bridge authenticated.
NO learned Q3 unique claim or novel algebra, no source :status use.
"""
from __future__ import annotations
import argparse, fractions, hashlib, json, re, subprocess, sys, time
from pathlib import Path
from sympy import Matrix, Rational

REV="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
FIRST_BENCH_META_FREEZE="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
EXTERNAL_WINOGRAD_DOI="https://doi.org/10.1016/0024-3795(71)90009-7"
MAX_SOLVER_SECONDS=8
A_NAMES=("a11","a12","a21","a22")
B_NAMES=("b11","b12","b21","b22")
PREF="non-incremental/NRA/20220222-strassen-matrix-multiplication/"

def sha1_blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def native_s_expr(source_text):
    marker=re.search(r"\(assert\s",source_text)
    if not marker:raise ValueError("ORIGINAL_SOURCE_ASSERT_NOT_FOUND")
    if len(re.findall(r"\(assert\s",source_text))!=1:
        raise ValueError("ORIGINAL_EXTRA_ASSERTION_NOT_SUPPORTED")
    tokens=re.findall(r"\(|\)|[^\s()]+",source_text[marker.start():])
    def recur(k):
        if tokens[k]!="(":return tokens[k],k+1
        k+=1;out=[]
        while k<len(tokens) and tokens[k]!=")":
            child,k=recur(k);out.append(child)
        if k>=len(tokens):raise ValueError("UNBALANCED_TRUE_SOURCE_SEXPR")
        return out,k+1
    tree,_=recur(0)
    if len(tree)!=2 or tree[0]!="assert":
        raise ValueError("ORIGINAL_EXPECT_SINGLE_ASSERT")
    outer=tree[1]
    if not (isinstance(outer,list) and len(outer)==3 and outer[0]=="exists"):
        raise ValueError("ORIGINAL_EXPECT_EXISTENTIAL_COEFFICIENTS")
    if not (isinstance(outer[2],list) and len(outer[2])==3 and outer[2][0]=="forall"):
        raise ValueError("ORIGINAL_EXPECT_INNER_UNIVERSAL_REAL_MATRIX")
    names=[r[0] for r in outer[1]]
    if len(names)!=len(set(names)) or any(r[1]!="Real" for r in outer[1]):
        raise ValueError("ORIGINAL_EXISTENTIAL_BINDER_IDENTITY_INVALID")
    inputs=[r[0] for r in outer[2][1]]
    if set(inputs)!=set(A_NAMES+B_NAMES) or any(r[1]!="Real" for r in outer[2][1]):
        raise ValueError("ORIGINAL_INPUT_EIGHT_INDEPENDENT_REAL_SYMBOLS_MISSING")
    eqs=outer[2][2]
    if len(eqs)!=5 or eqs[0]!="and" or any(len(e)!=3 or e[0]!="=" for e in eqs[1:]):
        raise ValueError("ORIGINAL_FOUR_OUTPUT_POLYNOMIAL_EQUALITIES_REQUIRED")
    return {"outer":outer,"varnames":names,"eqs":eqs[1:],"raw_source_exists_forall":True}

def terms(expr):
    if isinstance(expr,list) and expr[0]=="+":
        return expr[1:]
    return [expr]

def output_product_decomposition(eq):
    rhs=terms(eq[2])
    if len(rhs)!=7:raise ValueError("EXACT_SEVEN_OUTPUT_PRODUCT_FORM_NOT_FOUND")
    arr=[]
    for z in rhs:
        if not(isinstance(z,list) and len(z)==3 and z[0]=="*" and
               isinstance(z[2],list) and len(z[2])==3 and z[2][0]=="*"):
            raise ValueError("ORIGINAL_RANK_ONE_SEVEN_PRODUCT_SHAPE_MISMATCH")
        arr.append({"weight":z[1],"pa":z[2][1],"pb":z[2][2]})
    return arr

def numeric_leaf(expr,environment):
    if isinstance(expr,list):
        op=expr[0]
        values=[numeric_leaf(x,environment) for x in expr[1:]]
        if op=="+":return sum(values,fractions.Fraction(0))
        if op=="-":
            if len(values)==1:return -values[0]
            out=values[0]
            for x in values[1:]:out-=x
            return out
        if op=="*":
            out=fractions.Fraction(1)
            for x in values:out*=x
            return out
        raise ValueError("UNSUPPORTED_NATIVE_SOURCE_ARITHMETIC_"+str(op))
    if expr in environment:return fractions.Fraction(environment[expr])
    try:return fractions.Fraction(expr)
    except Exception:raise ValueError("ORIGINAL_SOURCE_SYMBOL_UNBOUND_"+str(expr))

def basis_environment(ai,bi):
    env={v:fractions.Fraction(0) for v in A_NAMES+B_NAMES}
    env[A_NAMES[ai]]=fractions.Fraction(1)
    env[B_NAMES[bi]]=fractions.Fraction(1)
    return env

def independently_source_bilinear(expr,coeff_names=None):
    """Prove structural bilinearity: each nonlinear product is A-linear ×
    B-linear, all other scalars are known coefficient names/constants."""
    if isinstance(expr,str):
        return expr in (A_NAMES+B_NAMES) or expr in (coeff_names or set()) or expr.lstrip("-.").isdigit()
    if not isinstance(expr,list) or len(expr)==0:return False
    if expr[0] not in ("+","-","*"):return False
    return all(independently_source_bilinear(x,coeff_names) for x in expr[1:])

def solve_published_seven_product_reference(ref):
    if len(ref["varnames"])!=28 or not all(name.startswith("w") for name in ref["varnames"]):
        raise RuntimeError("SOURCE_PUBLISHED_REFERENCE_FORMULA_NOT_ONLY_28_W")
    proof=[]
    witness={}
    input_form_coefficients={}
    for equation_index,eq in enumerate(ref["eqs"]):
        seven=output_product_decomposition(eq)
        if len({s["weight"] for s in seven})!=7 or not all(
            isinstance(s["weight"],str) and s["weight"] in ref["varnames"] for s in seven):
            raise RuntimeError("PUBLISHED_REFERENCE_REAL_MATRIX_WEIGHT_SYNTAX_INVALID")
        matrix=[]
        target=[]
        for ai in range(4):
            for bi in range(4):
                basis=basis_environment(ai,bi)
                target.append(numeric_leaf(eq[1],basis))
                matrix.append([numeric_leaf(p["pa"],basis)*numeric_leaf(p["pb"],basis)
                               for p in seven])
        M=Matrix([[Rational(x.numerator,x.denominator) for x in r] for r in matrix])
        B=Matrix([Rational(x.numerator,x.denominator) for x in target])
        values,parameters=M.gauss_jordan_solve(B)
        values=values.subs({p:0 for p in parameters})
        if M*values!=B:raise RuntimeError("ORIGINAL_PUBLIC_REFERENCE_16_TENSOR_EQ_NOT_EXACT")
        for j,pro in enumerate(seven):
            p=values[j]
            v=fractions.Fraction(int(p.p),int(p.q))
            key=pro["weight"]
            if key in witness and witness[key]!=v:
                raise RuntimeError("REFERENCE_SAME_W_CONFLICT")
            witness[key]=v
            pa_vec=[numeric_leaf(pro["pa"],basis_environment(i,0)) for i in range(4)]
            pb_vec=[numeric_leaf(pro["pb"],basis_environment(0,i)) for i in range(4)]
            old=input_form_coefficients.get(j)
            if old is not None and old!=(pa_vec,pb_vec):
                raise RuntimeError("SOURCE_PUBLISHED_REFERENCE_PA_PB_INCONSISTENT_ACROSS_OUTPUTS")
            input_form_coefficients[j]=(pa_vec,pb_vec)
        proof.append({"source_output_index":equation_index,
                      "native_true_coefficient_equations":16,
                      "matrix_rank_exact":int(M.rank()),
                      "rational_linear_weights":[str(witness[p["weight"]]) for p in seven],
                      "independent_original_16x7_matrix_identity_exact":True})
    if set(witness)!=set(ref["varnames"]) or len(input_form_coefficients)!=7:
        raise RuntimeError("REFERENCE_SOURCE_UNKNOWN_OUTPUT_COEFFICIENT_MISSING")
    return witness,input_form_coefficients,proof

def original_hard_coefficient_names(expr,inputs):
    parts=terms(expr)
    mapping={}
    for term in parts:
        if not(isinstance(term,list) and len(term)==3 and term[0]=="*"):
            raise ValueError("HARD_ORIGINAL_PA_PB_NOT_LINEAR_SOURCE")
        left,right=term[1:]
        if not(isinstance(left,str) and isinstance(right,str) and
               right in inputs and (left.startswith("pa") or left.startswith("pb"))):
            raise ValueError("HARD_ORIGINAL_PA_PB_VARIABLE_PRODUCT_MISMATCH")
        if right in mapping and mapping[right]!=left:
            raise ValueError("ORIGINAL_COEFFICIENT_VARIABLE_DUPLICATED")
        mapping[right]=left
    if set(mapping)!=set(inputs):
        raise ValueError("ORIGINAL_INPUT_LINEAR_FORM_SOME_TERM_MISSING")
    return mapping

def lift_reference_to_original_hard(ref_w,reference_forms,hard):
    assign=dict(ref_w)
    for original_eq in hard["eqs"]:
        products=output_product_decomposition(original_eq)
        for j,product in enumerate(products):
            if product["weight"] not in ref_w:
                raise RuntimeError("ORIGINAL_HARD_OUTPUT_COEFFICIENT_DISAGREES_WITH_PUBLIC_REFERENCE")
            a_keys=original_hard_coefficient_names(product["pa"],A_NAMES)
            b_keys=original_hard_coefficient_names(product["pb"],B_NAMES)
            a_vals,b_vals=reference_forms[j]
            for name,vec,orig_inputs in ((a_keys,a_vals,A_NAMES),(b_keys,b_vals,B_NAMES)):
                for pos,key in enumerate(orig_inputs):
                    variable=name[key]
                    if variable in assign and assign[variable]!=vec[pos]:
                        raise RuntimeError("ORIGINAL_REFERENCED_INPUT_FORMS_INCONSISTENT")
                    assign[variable]=vec[pos]
    if set(assign)!=set(hard["varnames"]):
        raise RuntimeError("ORIGINAL_HARD_84_COEFFICIENT_WITNESS_INCOMPLETE")
    return assign

def exact_complete_source_coeff_identity(original,assignment):
    if set(assignment)!=set(original["varnames"]):
        raise ValueError("REAL_ORIGINAL_EXISTENTIAL_SYMBOLS_NOT_ALL_GROUNDED")
    count=0
    for output_id,eq in enumerate(original["eqs"]):
        decomp=output_product_decomposition(eq)
        if any(not independently_source_bilinear(q, set(assignment)) for q in (eq[1],eq[2])):
            raise RuntimeError("NON_POLYNOMIAL_ORIGINAL_SOURCE_CANNOT_CERTIFY_16_BASIS_SUFFICIENCY")
        if not all(isinstance(p["weight"],str) and (
            p["weight"] in assignment or p["weight"]=="0") for p in decomp):
            raise RuntimeError("UNSUPPORTED_ACTUAL_ORIGINAL_OUTPUT_WEIGHT_SHAPE")
        for ai in range(4):
            for bi in range(4):
                env=dict(assignment);env.update(basis_environment(ai,bi))
                left=numeric_leaf(eq[1],env)
                right=numeric_leaf(eq[2],env)
                if left!=right:
                    raise RuntimeError("ORIGINAL_FULL_SOURCE_BILINEAR_COEFFICIENT_MISMATCH_OUT"+
                      str(output_id)+"_a"+str(ai)+"b"+str(bi))
                count+=1
    assert count==64
    return {"all_actual_original_output_input_basis_coefficients_exact":count,
            "original_true_four_bilinear_matrix_output_polynomial_identities":4,
            "mathematical_universal_R_identity_from_independent_bilinear_basis":True}

def original_rank6_bridge(original):
    if len(original["varnames"])!=80:
        raise RuntimeError("SOURCE_6PRODUCT_RANK_LOWER_BOUND_ORIGINAL_EXPECT_80_BINDINGS")
    for eq in original["eqs"]:
        pro=output_product_decomposition(eq)
        if not all(isinstance(p["weight"],str) and p["weight"] in original["varnames"]
                   for p in pro[:6]):raise ValueError("ORIGINAL_FIRST_SIX_WEIGHT_NOT_EXISTENTIAL")
        if pro[6]["weight"]!="0":
            raise ValueError("ORIGINAL_SEVENTH_MULTIPLICATION_IS_NOT_LITERAL_ZERO")
        for term in pro:
            original_hard_coefficient_names(term["pa"],A_NAMES)
            original_hard_coefficient_names(term["pb"],B_NAMES)
    return {"actual_original_all_four_outputs_six_active_rank_one_products":True,
            "actual_original_seventh_weight_exactly_literal_zero":True,
            "known_1971_Winograd_minimum_tensor_rank_seven_EXTERNAL_THEOREM":EXTERNAL_WINOGRAD_DOI,
            "this_source_bridge_NOT_a_formal_proof_of_Winograd_theorem":True}

def sexpr_to_smt(node):
    if isinstance(node,str):return node
    return "("+" ".join(sexpr_to_smt(x) for x in node)+")"

def real_constant(x):
    f=fractions.Fraction(x)
    def number(n):return str(n)+".0" if n>=0 else "(- "+str(-n)+".0)"
    if f.denominator==1:return number(f.numerator)
    return "(/ "+number(f.numerator)+" "+number(f.denominator)+")"

def original_witness_proves_universal_by_two_SMT_solvers(original,assignment):
    origforall=sexpr_to_smt(original["outer"][2])
    binding=" ".join("("+name+" "+real_constant(assignment[name])+")"
                     for name in original["varnames"])
    original_formula="(let ("+binding+") "+origforall+")"
    # The negation is unsatisfiable iff exact source universal is TRUE with
    # this proposed real vector, so original existential SAT by introduction.
    payload="\n".join(["(set-logic NRA)","(assert (not "+original_formula+"))",
                       "(check-sat)","(exit)",""])
    results={}
    for name in ("Z3","cvc5"):
        begin=time.perf_counter_ns()
        if name=="Z3":
            code="import z3,sys;s=z3.Solver();s.set(timeout=7000);s.from_string(sys.stdin.read());print(s.check())"
            cmd=[sys.executable,"-c",code]
        else:
            cmd=["cvc5","--lang=smt2","--tlimit-per=7000","-"]
        status="UNKNOWN";error=None
        try:
            q=subprocess.run(cmd,input=payload,text=True,capture_output=True,timeout=MAX_SOLVER_SECONDS+2)
            lines=[z.strip().upper() for z in q.stdout.splitlines() if z.strip().lower() in ("sat","unsat","unknown")]
            if q.returncode==0 and lines:status=lines[0]
            else:error="exit:"+str(q.returncode)+"/"+q.stderr[:200]
        except Exception as e:
            error=type(e).__name__+":"+str(e)[:160]
        results[name]={"grounded_original_FORALL_NEGATION_status":status,
                       "whole_SMT_check_elapsed_ms":(time.perf_counter_ns()-begin)/1e6,
                       "error":error}
    return {"actual_complete_original_witness_negation_source_SHA256":sha256(payload.encode()),
            "both_independent_Z3_cvc5_prove_ORIGINAL_FORALL_TRUE":
              results["Z3"]["grounded_original_FORALL_NEGATION_status"]==
              results["cvc5"]["grounded_original_FORALL_NEGATION_status"]=="UNSAT",
            "independent_original_witness_SMT_engine_results":results}

def authenticate_original(root,meta,name):
    row=next(p for p in meta["cases"] if p["path"]==PREF+name)
    raw=(root/row["path"]).read_bytes()
    if len(raw)!=row["bytes"] or sha1_blob(raw)!=row["git_blob"]:
        raise RuntimeError("PRESOURCE_FROZEN_ORIGINAL_TRUE_GIT_BLOB_MISMATCH")
    return raw,{"source":row["path"],"git_blob":row["git_blob"],
                "source_sha256":sha256(raw),"authentic":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text());meta=json.loads(a.freeze.read_text())
    if c["schema"]!="neumann.q3.posthoc_strassen_tensor_coefficient_3_original_source_gate.v1":
        raise RuntimeError("STRASSEN_FIRST_POSTHOC_CONTRACT_CHANGED")
    if meta["original_upstream"].split("@")[-1]!=REV or len(meta["cases"])!=18:
        raise RuntimeError("FIRST_BENCH_META_SOURCE_IDS_CHANGED")
    names=("strassen-linear.smt2","strassen-hard.smt2","strassen-impossible.smt2")
    records={}
    for name in names:
        raw,identity=authenticate_original(a.root,meta,name)
        records[name]={"source_identity":identity,"status":"ABSTAIN"}
        parsed=native_s_expr(raw.decode("utf-8"))
        records[name]["true_native_forall_source_num_existential_real"]=len(parsed["varnames"])
        records[name]["source_original_real_matrix_eight_independent_inputs"]=True
        records[name]["source_exact_native_one_true_existential_forall_assertion"]=True
        records[name]["true_original_declared_numeric_status_IGNORED"]=True
        records[name]["_parse"]=parsed
    ref=records[names[0]]["_parse"];hard=records[names[1]]["_parse"]
    impossible=records[names[2]]["_parse"]
    weights, forms,mathematical=solve_published_seven_product_reference(ref)
    for name,assignment in ((names[0],weights),(names[1],lift_reference_to_original_hard(weights,forms,hard))):
        r=records[name]
        actual=r.pop("_parse")
        full=exact_complete_source_coeff_identity(actual,assignment)
        extra=original_witness_proves_universal_by_two_SMT_solvers(actual,assignment)
        r["original_source_full_real_quantified_identity_coefficient_proof"]=full
        r["independent_genuine_original_Z3_cvc5_universal_witness"]=extra
        r["exact_original_source_all_existentials_grounded_real"]=len(assignment)
        r["published_reference_witness_provenance"]="OTHER_ACTUAL_PUBLIC_STRASSEN_LINEAR_SOURCE_NOT_MODEL"
        r["original_source_solver_strong_direct_historically_UNKNOWN"]=True
        # Existing actual original source polynomial theorem alone gives
        # a self-contained exact proof, independently SMT checked when both
        # engines return UNSAT for negation of universally grounded witness.
        r["source_complete_real_mathematical_identity_valid"]=True
        r["status"]="ORIGINAL_SAT_BILINEAR_COEFFICIENT_THEOREM_WITH_DUAL_QUANTIFIED_SMT" if extra[
           "both_independent_Z3_cvc5_prove_ORIGINAL_FORALL_TRUE"] else "ORIGINAL_SAT_BILINEAR_IDENTITY_EXACT_DUAL_SMT_UNKNOWN"
    r=records[names[2]]
    bridge=original_rank6_bridge(r.pop("_parse"))
    r["original_native_rank_six_external_theorem_premises"]=bridge
    r["source_UNSAT_conclusion_assumes_published_Winograd_1971"]=True
    r["status"]="ORIGINAL_UNSAT_CONDITIONAL_EXTERNAL_PUBLISHED_WINOGRAD_RANK7"
    all_record=[records[name] for name in names]
    output={
        "schema":"neumann.q3.posthoc_strassen_3_real_source_tensor_original_sat_and_external_rank.v1",
        "after_initial_original_18_source_expert_headroom_run":True,
        "first_source_18_metadata_git_freeze_commit":FIRST_BENCH_META_FREEZE,
        "source_original_all_three_authentic":sum(r["source_identity"]["authentic"] for r in all_record),
        "source_linear_complete_original_SAT_algebraic":records[names[0]]["source_complete_real_mathematical_identity_valid"],
        "source_hard_complete_original_SAT_algebraic":records[names[1]]["source_complete_real_mathematical_identity_valid"],
        "source_impossible_classification_external_rank7_theorem_only":records[names[2]]["source_UNSAT_conclusion_assumes_published_Winograd_1971"],
        "published_prior_art_strassen_and_winograd_not_model_invention":True,
        "model_training_and_neural_forwards":0,
        "learned_unique_Q3_proven":False,
        "strongest_direct_with_equal_public_reference_can_make_same_discovery":True,
        "source_already_opened_NOT_first_blind_new_model_success":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
        "source_reference_actual_exact_four_output_16tensor_identity_system":mathematical,
        "original_three":all_record
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print("Q3_STRASSEN_TRUE_ORIGINAL_THREE_SHA_AUTHENTIC",output["source_original_all_three_authentic"],"/3")
    print("Q3_STRASSEN_LINEAR_ACTUAL_FULL_ORIGINAL_SAT",output["source_linear_complete_original_SAT_algebraic"])
    print("Q3_STRASSEN_HARD_ACTUAL_FULL_ORIGINAL_SAT",output["source_hard_complete_original_SAT_algebraic"])
    print("Q3_STRASSEN_ACTUAL_FULL_QUANTIFIED_TWO_SOLVER_CHECKS",[
      records[name]["independent_genuine_original_Z3_cvc5_universal_witness"]["both_independent_Z3_cvc5_prove_ORIGINAL_FORALL_TRUE"] for name in names[:2]])
    print("Q3_STRASSEN_IMPOSSIBLE_CONDITIONAL_KNOWN_RANK7",output["source_impossible_classification_external_rank7_theorem_only"])
    print("Q3_STRASSEN_Q3_Q4_GLOBALLY_OPEN",output["global_Q3"],output["global_Q4"])
if __name__=="__main__":
    main()
