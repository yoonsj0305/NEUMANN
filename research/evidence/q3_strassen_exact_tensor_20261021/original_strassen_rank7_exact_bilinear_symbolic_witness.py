"""Posthoc source-original exact Strassen rank-seven bilinear tensor certificates.

Authorship: classical known 1969 Strassen method, exact original source
coefficient solving, NOT a novel learned NEUMANN mechanism.

The externally grounded original SMT2 source itself defines the existential
output weights and universally quantified matrix entries. Extract the
original quantifier from source SMT2, solve output weights by EXACT 64=4x16
bilinear coefficient equations, validate every source coefficient on the
native parsed whole ORIGINAL formulas. For hard, infer rank-one Pa/Pb
factorization from the linear source product tensors, reconstruct all full
original quantified witnesses, independently Z3 and cvc5 certify
negation of the actual source universal predicate UNSAT (all REAL inputs).
No original :status or filename conditional decisions in inference.
"""
from __future__ import annotations
import argparse, fractions, hashlib, json, re, subprocess, time
from pathlib import Path
import sympy as sp
from fractions import Fraction

SHA_FREEZE="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
ORIGINAL_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
EXTERNAL_RANK7="Winograd, On multiplication of 2x2 matrices, Linear Algebra Appl. 4 (1971), 381–388"

def blob_sha(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def digest(b):
    return hashlib.sha256(b).hexdigest()

def sexp_extract_source_assertion(source):
    # Only literal original assert's SMT-LIB source, not :status/comment/gold.
    i=source.find("(assert ")
    if i<0:raise ValueError("ORIGINAL_SOURCE_HAS_NO_ASSERT")
    start=i;count=0;end=None
    for j in range(i,len(source)):
        c=source[j]
        if c=="(":count+=1
        elif c==")":
            count-=1
            if count==0:end=j+1;break
    if end is None:raise ValueError("UNBALANCED_ORIGINAL_ASSERT")
    tokens=re.findall(r"[()]|[^()\s]+",source[start:end])
    ix=0
    def parse():
        nonlocal ix
        if ix>=len(tokens):raise ValueError("EXHAUSTED_SMT_TOKENS")
        if tokens[ix]=="(":
            ix+=1;result=[]
            while ix<len(tokens) and tokens[ix]!=")":
                result.append(parse())
            if ix==len(tokens):raise ValueError("UNMATCHED_BRACKET")
            ix+=1
            return result
        item=tokens[ix];ix+=1;return item
    tree=parse()
    if ix!=len(tokens) or tree[0]!="assert":
        raise ValueError("ORIGINAL_ASSERT_TOKEN_IDENTITY_MISMATCH")
    q=tree[1]
    if len(q)!=3 or q[0]!="exists":
        raise ValueError("ORIGINAL_NOT_EXISTENTIAL_MATRIX_WITNESS")
    inner=q[2]
    if inner[0]!="forall" or len(inner)!=3:
        raise ValueError("ORIGINAL_NOT_UNIVERSAL_BILINEAR_TARGET")
    binds=q[1];forall_binds=inner[1]
    if len(forall_binds)!=8 or len({x[0] for x in forall_binds})!=8:
        raise ValueError("ORIGINAL_HAS_NOT_EIGHT_MATRIX_INPUTS")
    if any(e[1]!="Real" for e in binds+forall_binds):
        raise ValueError("ORIGINAL_NON_REAL_QUANTIFIER")
    body=inner[2]
    if body[0]!="and" or len(body)!=5 or not all(eq[0]=="=" for eq in body[1:]):
        raise ValueError("ORIGINAL_NOT_FOUR_MATRIX_PRODUCT_EQUATIONS")
    names={e[0] for e in binds};inputs={e[0] for e in forall_binds}
    if names&inputs:raise ValueError("SOURCE_BINDER_SHADOW")
    return {"all_existential_symbols":[x[0] for x in binds],
            "universal_matrix_inputs":[x[0] for x in forall_binds],
            "body":body,"true_assert_AST_s_expr_sha256":digest(source[start:end].encode())}

def stringify(node):
    if isinstance(node,list):return "("+" ".join(stringify(x) for x in node)+")"
    return str(node)

def numeric(atom):
    if re.fullmatch(r"[+-]?\d+",atom):return Fraction(int(atom))
    if re.fullmatch(r"[+-]?\d+\.\d+",atom):return Fraction(atom)
    raise ValueError("UNSUPPORTED_SMT2_NUMBER:"+str(atom))

def expr_value(e,env):
    if isinstance(e,str):
        return env[e] if e in env else numeric(e)
    op=e[0]
    children=[expr_value(p,env) for p in e[1:]]
    if op=="+":return sum(children)
    if op=="*":
        product=1
        for child in children:product*=child
        return product
    if op=="-":
        if len(children)==1:return -children[0]
        val=children[0]
        for c in children[1:]:val-=c
        return val
    if op=="/":
        if len(children)!=2:raise ValueError("DIVISION_ARITY")
        return children[0]/children[1]
    raise ValueError("UNSUPPORTED_ORIGINAL_ARITH_OPERATOR:"+op)

def original_matrix_basis_inputs(input_names,i,j):
    # Source input order is a11 a12 a21 a22 / b11 b12 b21 b22;
    # explicit source variable names audited, not source labels or answers.
    assert input_names==["a11","a12","a21","a22","b11","b12","b21","b22"]
    x={k:Fraction(0) for k in input_names}
    x[input_names[i]]=Fraction(1)
    x[input_names[j+4]]=Fraction(1)
    return x

def original_expressions_at_basis(tree,witness):
    assert set(witness)==set(tree["all_existential_symbols"])
    result=[]
    for eq in tree["body"][1:]:
        pair=[]
        for i in range(4):
            for j in range(4):
                env=dict(witness)
                env.update(original_matrix_basis_inputs(tree["universal_matrix_inputs"],i,j))
                lhs=expr_value(eq[1],env);rhs=expr_value(eq[2],env)
                pair.append((lhs,rhs))
        result.append(pair)
    return result

def solve_linear_original_coefficients(tree):
    unknowns=tree["all_existential_symbols"]
    if len(unknowns)!=28 or not all(re.fullmatch(r"w[12][12][1-7]",v) for v in unknowns):
        raise ValueError("SOURCE_LINEAR_ONLY_OUTPUT_WEIGHTS_NOT_TRUE")
    symbols={name:sp.Symbol(name) for name in unknowns}
    pairs=original_expressions_at_basis(tree,symbols)
    equations=[]
    for p in pairs:
        for left,right in p:
            equations.append(sp.expand(left-right))
    A,b=sp.linear_eq_to_matrix(equations,[symbols[k] for k in unknowns])
    if int(A.rank())!=28:raise ValueError("ORIGINAL_LINEAR_COEFFICIENTS_NOT_FULL_COLUMN_RANK")
    answers=sp.linsolve((A,b))
    if answers is sp.EmptySet:raise ValueError("TRUE_ORIGINAL_LINEAR_RANK7_UNSOLVABLE")
    a=list(answers)
    if len(a)!=1:raise ValueError("MULTIPLE_SOURCE_LINEAR_SOLUTIONS")
    found={}
    for name,v in zip(unknowns,a[0]):
        if not v.is_Rational:
            raise ValueError("SOLVED_NONRATIONAL_EXPECTED_EXACT")
        found[name]=Fraction(int(v.p),int(v.q))
    pairs=original_expressions_at_basis(tree,found)
    if not all(lhs==rhs for row in pairs for lhs,rhs in row):
        raise RuntimeError("EXACT_ORIGINAL_64_COEFFICIENTS_NOT_SAT")
    return found,{"exact_source_coefficient_rows":len(equations),
                  "original_unknown_linear_weights":len(unknowns),
                  "actual_original_rational_matrix_rank":int(A.rank()),
                  "source_exact_all_4x16_basis_coefficients_match":True}

def input_product_rank_one_form(tree,weight_values):
    # The exact original Strassen-linear right hand side includes seven
    # products Pj=(linear A)*(linear B). Turn on one true source output
    # weight at a time and obtain the native original tensor of Pj.
    first=tree["body"][1]
    products=[]
    for j in range(1,8):
        specific={name:Fraction(0) for name in tree["all_existential_symbols"]}
        specific[f"w11{j}"]=Fraction(1)
        C=[]
        for i in range(4):
            row=[]
            for k in range(4):
                env=dict(specific)
                env.update(original_matrix_basis_inputs(tree["universal_matrix_inputs"],i,k))
                row.append(expr_value(first[2],env))
            C.append(row)
        pivot=next(((i,k) for i in range(4) for k in range(4) if C[i][k]),None)
        if pivot is None:raise ValueError("ORIGINAL_SOURCE_PRODUCT_HAS_ZERO_RANK")
        a,b=pivot
        pa=[C[i][b] for i in range(4)]
        pb=[C[a][k]/C[a][b] for k in range(4)]
        if any(pa[i]*pb[k]!=C[i][k] for i in range(4) for k in range(4)):
            raise ValueError("TRUE_SOURCE_LINEAR_PRODUCT_NOT_RANK_ONE")
        products.append({"j":j,"Pa":pa,"Pb":pb,"rank1_tensor":C})
    return products

def transfer_exact_native_source_linear_to_hard(source_linear, source_hard,linear_coeff):
    names=set(source_hard["all_existential_symbols"])
    expected={f"w{i}{j}{k}" for i in (1,2) for j in (1,2) for k in range(1,8)}
    expected|={f"pa{i}{j}{k}" for i in (1,2) for j in (1,2) for k in range(1,8)}
    expected|={f"pb{i}{j}{k}" for i in (1,2) for j in (1,2) for k in range(1,8)}
    if names!=expected:
        raise ValueError("TRUE_ORIGINAL_HARD_EXISTENTIAL_BINDER_IDENTITIES_MISMATCH")
    products=input_product_rank_one_form(source_linear,linear_coeff)
    witness=dict(linear_coeff)
    for p in products:
        for i,(r,c) in enumerate([(1,1),(1,2),(2,1),(2,2)]):
            witness[f"pa{r}{c}{p['j']}"]=p["Pa"][i]
            witness[f"pb{r}{c}{p['j']}"]=p["Pb"][i]
    if set(witness)!=names:raise ValueError("TRANSFER_DID_NOT_FILL_ALL_ORIGINAL_VARS")
    check=original_expressions_at_basis(source_hard,witness)
    if not all(lhs==rhs for row in check for lhs,rhs in row):
        raise ValueError("ACTUAL_ORIGINAL_HARD_COEFFICIENT_VALIDATION_FAILED")
    return witness,products

def numerator_smt(v):
    if v.denominator==1:
        return str(v.numerator) if v.numerator>=0 else f"(- {abs(v.numerator)})"
    n=str(abs(v.numerator))
    atom=f"(/ {n} {v.denominator})"
    return atom if v.numerator>=0 else f"(- {atom})"

def independent_original_universal_negation_certificate(tree,witness,orig_tag):
    # Exact actual SOURCE body is reused UNMODIFIED. Every existential
    # variable replaced by a formally-defined rational constant; its
    # FULL original 8-Real-variable ∀ claim is independently refuted
    # by UNSAT of the native original negation, not just random testing.
    if set(witness)!=set(tree["all_existential_symbols"]):
        raise ValueError("ORIGINAL_FULL_EXISTENTIAL_WITNESS_NOT_COVERED")
    lines=["(set-logic QF_NRA)"]
    for var in tree["universal_matrix_inputs"]:
        lines.append(f"(declare-fun {var} () Real)")
    for var in tree["all_existential_symbols"]:
        lines.append(f"(define-fun {var} () Real {numerator_smt(witness[var])})")
    lines.append(f"(assert (not {stringify(tree['body'])}))")
    lines+=["(check-sat)","(exit)"]
    input_text="\n".join(lines)+"\n"
    solved={}
    for engine in ("Z3_QF_NRA","cvc5_QF_NRA"):
        start=time.perf_counter_ns()
        if engine.startswith("Z3"):
            # Z3 subprocess is an independent QF_NRA nonlinear arithmetic
            # solver. cvc5 directly parses original SMT-LIB native body.
            cmd=["python","-c","import z3,sys; z=z3.SolverFor('QF_NRA');z.set(timeout=6000);z.from_string(sys.stdin.read());print(z.check())"]
        else:
            cmd=["cvc5","--lang=smt2","--tlimit-per=6000","-"]
        state="UNKNOWN";stderr=None
        try:
            r=subprocess.run(cmd,input=input_text,capture_output=True,text=True,timeout=9)
            statuses=[line.strip().upper() for line in r.stdout.splitlines()
                      if line.strip().lower() in ("sat","unsat","unknown")]
            if r.returncode==0 and statuses:state=statuses[0]
            else:stderr="EXIT:"+str(r.returncode)+" "+r.stderr[:200]
        except Exception as e:
            stderr=type(e).__name__+":"+str(e)[:220]
        solved[engine]={"status":state,
                        "actual_native_negated_original_body_source_hash":digest(input_text.encode()),
                        "subprocess_real_wall_ms":(time.perf_counter_ns()-start)/1e6,
                        "original_solver_error":stderr}
    return {"original_name":orig_tag,"original_native_formula_not_replaced":True,
            "witness_exact_all_28_or_84_existential_vars":len(witness),
            "independent_original_QF_NRA_negation_provers":solved,
            "both_independent_engines_proved_forall_over_ALL_REAL_matrices":
                all(x["status"]=="UNSAT" for x in solved.values())}

def solve(root,freeze):
    cases={p["path"].split("/")[-1]:p for p in freeze["cases"] if p["family"]=="STRASSEN"}
    requested=("strassen-linear.smt2","strassen-hard.smt2","strassen-impossible.smt2")
    original={}
    for fn in requested:
        meta=cases[fn];raw=(root/meta["path"]).read_bytes()
        if len(raw)!=meta["bytes"] or blob_sha(raw)!=meta["git_blob"]:
            raise ValueError("TRUE_ORIGINAL_STRASSEN_GIT_BLOB_CHANGED:"+fn)
        original[fn]={"source_sha256":digest(raw),"source_git_blob":meta["git_blob"],
                      "native":sexp_extract_source_assertion(raw.decode("utf-8"))}
    linear=original["strassen-linear.smt2"]["native"]
    hard=original["strassen-hard.smt2"]["native"]
    w,linearproof=solve_linear_original_coefficients(linear)
    certlinear=independent_original_universal_negation_certificate(linear,w,"TRUE_SOURCE_strassen_linear")
    wh,rank7=transfer_exact_native_source_linear_to_hard(linear,hard,w)
    certhard=independent_original_universal_negation_certificate(hard,wh,"TRUE_SOURCE_strassen_hard")
    # For original 'impossible', check coefficient structure of constant
    # zeroed seventh rank-1 output product, but deeper real tensor rank >=7
    # is an EXTERNAL existing Winograd theorem, not silently claimed
    # machine proved by polynomial coefficient tests here.
    impossible=original["strassen-impossible.smt2"]["native"]
    witness_counts={"hard":len(wh),"linear":len(w)}
    return {"source_provenance":{name:{"sha256":val["source_sha256"],"git_blob":val["source_git_blob"],
                                      "native_assert_AST_hash":val["native"]["true_assert_AST_s_expr_sha256"]}
                                  for name,val in original.items()},
            "linear_source_exact_full_tensor_64":linearproof,
            "original_linear_actual_mathematical_witness":{k:str(v) for k,v in w.items()},
            "original_hard_full_84_rational_witness":{k:str(v) for k,v in wh.items()},
            "native_source_7_rank_one_tensor_factorizations":[
                {"product":p["j"],"Pa":[str(q) for q in p["Pa"]],"Pb":[str(q) for q in p["Pb"]]}
                for p in rank7],
            "original_linear_independent_two_solver_all_reals_proof":certlinear,
            "original_hard_independent_two_solver_all_reals_proof":certhard,
            "original_known_external_rank_7_lower_bound_reference":EXTERNAL_RANK7,
            "original_impossible_referenced_lower_bound_is_not_a_machine_proved_UNSAT":True,
            "original_impossible_exact_binder_variable_count":len(impossible["all_existential_symbols"]),
            "original_impossible_status":"UNKNOWN_EXTERNAL_NUMBER_THEORY_RANK7_THEOREM_NOT_FORMALLY_VERIFIED",
            "witness_exact_original_existent_var_counts":witness_counts}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();f=json.loads(a.freeze.read_text());c=json.loads(a.contract.read_text())
    if c["schema"]!="neumann.q3.posthoc_strassen_tensor_coefficient_3_original_source_gate.v1":
        raise RuntimeError("PRE_REGISTERED_STRASSEN_REAL_SOURCE_PROTOCOL_CHANGED")
    if not c["posthoc_after_first_source_open"] or len(f["cases"])!=18:
        raise RuntimeError("TRUE_ORIGINAL_SHA_MANIFEST_REPLACED")
    t=time.perf_counter_ns()
    result={"schema":"neumann.q3.true_original_strassen_linear_and_hard_original_all_real_witness_v1",
            "preregistered_before_first_strassen_exact_method_evidence_commit":"f9d66c5bc9493ad0a1f1106484cf7a05ceca9b85",
            "source_posthoc_previously_opened":True,
            "all_source_files_original_git_authenticated":False,
            "actual_original_linear_proved_SAT_doubly":False,
            "actual_original_hard_proved_SAT_doubly":False,
            "original_impossible_remains_UNPROVEN":True,
            "prior_known_classical_Strassen_algorithm_public":True,
            "no_neural_training_or_learned_unique_Q3":True,
            "strong_classical_direct_can_access_exact_same_bilinear_algorithm":True,
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN"}
    try:
        r=solve(a.root,f)
        result.update(r)
        result["all_source_files_original_git_authenticated"]=len(r["source_provenance"])==3
        result["actual_original_linear_proved_SAT_doubly"]=r["original_linear_independent_two_solver_all_reals_proof"]["both_independent_engines_proved_forall_over_ALL_REAL_matrices"]
        result["actual_original_hard_proved_SAT_doubly"]=r["original_hard_independent_two_solver_all_reals_proof"]["both_independent_engines_proved_forall_over_ALL_REAL_matrices"]
    except Exception as e:
        result["error"]=type(e).__name__+":"+str(e)[:520]
    result["entire_source_exact_witness_dual_process_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3_STRASSEN_TRUE_ORIGINAL_SOURCE_SAT_LINEAR",result["actual_original_linear_proved_SAT_doubly"])
    print("Q3_STRASSEN_TRUE_ORIGINAL_SOURCE_SAT_HARD",result["actual_original_hard_proved_SAT_doubly"])
    print("Q3_STRASSEN_CLASSICAL_RANK7_EXTERNAL_IMPOSSIBLE_NOT_PROVED",result["original_impossible_remains_UNPROVEN"])
    print("Q3_STRASSEN_REAL_SOURCE_RESULT_ERROR",result.get("error"))
    print("Q3_STRASSEN_Q3_Q4_OPEN",result["global_Q3"],result["global_Q4"])
if __name__=="__main__":
    main()
