"""Q3 expressive power audit: general source-rational dynamical abstraction.

Human-conceived mathematics and classical automatic rational-program enumeration,
not a newly learned neural primitive. The single parameter theorem is over Q(h,x),
not merely finite sampled tasks. Polynomial impossibility is by pole order.
"""
import argparse,hashlib,json,math,pathlib,random,time
import sympy as s

X,H=s.symbols("x h")
POSITIVE=(1,2,3,4,5,6,7,8,9,10,11,12)
NEGATIVE=(2,3,5,7,11,15)

def digest(x):return hashlib.sha256(x).hexdigest()
def write(path,data):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    return digest(p.read_bytes())

def derive_full_parametric_theorem():
    F=(X**2+H**2)/(2*X)
    R=(X+H)/(X-H)
    identity=s.cancel(((F+H)/(F-H)) - R**2)
    assert identity==0,"RATIONAL_SEMICONJUGACY_FAILED"
    pole=s.cancel(X*F).subs(X,0)
    assert s.simplify(pole-H**2/2)==0
    # Algebraic general theorem: for nonzero h, F has a simple pole at 0.
    # For p in Q[x], degree n>=1, p(F) has a pole of exact order n
    # because leading term coeff a_n F^n has pole order n, other terms
    # strictly less; p(x)^2 has no pole. Thus rational identity impossible.
    inverse=(X-H)/(X+H)
    assert s.cancel(((F-H)/(F+H))-inverse**2)==0
    # Iterated theorem follows by composition/induction, no need to expand
    # the huge rational F^{2^n}: R(F^{∘n})=R(x)^(2^n).
    return {"identity":str(identity),
            "parameter_condition":"h any nonzero rational; x is a transcendental indeterminate",
            "source_expression":str(F),
            "constructed_division_primitive":"(x+h)/(x-h)",
            "reciprocal_also_valid":"(x-h)/(x+h)",
            "simple_source_pole_at_x0_residue":str(pole),
            "full_polynomial_no_go":"any nonconstant polynomial p∈Q[x] has pole order deg(p) in p(F), but p(x)^2 is finite at x=0; hence impossible",
            "iterated_dynamics":"R(F^n(x))=R(x)^(2^n) for every n>=0 by induction",
            "vacuous_constants_rejected":[0,1],
            "symbolic_parameter_identity_proven":True}

def exact_affine_poly_fails(k):
    # This is an additional *machine-certified degree-1* no-go, not a
    # substitute for the proof of ALL polynomial degrees above.
    a,b=s.symbols("a b")
    F=(X**2+k)/(2*X)
    lhs=s.factor(s.together((a*F+b)-(a*X+b)**2))
    numerator=s.Poly(s.together(lhs).as_numer_denom()[0],X)
    coeffs=numerator.all_coeffs()
    # x^-1 singularity coefficient is a*k, k>0 => a=0.
    s0=s.solve(coeffs,[a,b],dict=True)
    assert all(z.get(a,0)==0 for z in s0)
    return {"solutions":sorted(str(z) for z in s0),"nonconstant_none":True}

def source_generator(k):
    # Only expanded quadratic rational coefficients are provided to a learner.
    # It is not handed an operator program or the hidden square-root parameter.
    return {"numerator_coefficients":[1,0,k],
            "denominator_coefficients":[2,0],
            "function_domain":"rational x≠0",
            "goal":"find nonconstant rational expression g with exact g(F(x))=g(x)^2"}

def exact_verifier(program,k):
    """Program is typed AST: DIV(ADD(VAR,p), ADD(VAR,q))."""
    p,q=program["num_shift"],program["den_shift"]
    if not isinstance(p,int) or not isinstance(q,int) or p==q:return False
    F=(X**2+k)/(2*X)
    G=(X+p)/(X+q)
    return s.cancel(G.subs(X,F)-G*G)==0

def generic_ast_search(k,max_abs=None):
    assert k>0
    limit=max_abs if max_abs is not None else math.isqrt(k)+1
    checked=0
    started=time.process_time()
    # This searches executable DIV/ADD ASTs WITHOUT the true sqrt(k) label.
    for p in range(-limit,limit+1):
        for q in range(-limit,limit+1):
            if p==q:continue
            checked+=1
            trial={"op":"DIV","num_op":"ADD","den_op":"ADD",
                   "num_shift":p,"den_shift":q}
            if exact_verifier(trial,k):
                return {"status":"EXACT_CERTIFIED","program":trial,
                        "exact_verifier_calls":checked,"source_cpu_s":time.process_time()-started}
    return {"status":"UNKNOWN_NO_CERTIFIED_AST","program":None,
            "exact_verifier_calls":checked,"source_cpu_s":time.process_time()-started}

def direct_specialist(k):
    # Strong SAME-INFORMATION classical comparator, source-only integer-root.
    started=time.process_time()
    r=math.isqrt(k)
    if r*r!=k or r==0:
        return {"status":"UNKNOWN_NO_INTEGER_CERTIFICATE","program":None,
                "cpu_s":time.process_time()-started}
    program={"op":"DIV","num_op":"ADD","den_op":"ADD","num_shift":r,"den_shift":-r}
    good=exact_verifier(program,k)
    return {"status":"EXACT_CERTIFIED" if good else "UNKNOWN_NO_CERTIFIED_AST",
            "program":program if good else None,
            "exact_verifier_calls":1,
            "cpu_s":time.process_time()-started}

def execute():
    theorem=derive_full_parametric_theorem()
    output={"schema":"NEUMANN_Q3_RATIONAL_PRIMITIVE_STRICTNESS.v1",
            "primary_theorem":theorem,
            "human_created_new_grammar_operation":"DIV",
            "model_training":False,
            "original_external_benchmark":False,
            "finite_polynomial_grammar_limit":"STRICT_INSUFFICIENCY_FOR_ANY_DEGREE_NOT_JUST_DEPTH_CAP",
            "positive":[],"negative":[]}
    for h in POSITIVE:
        k=h*h
        t0=time.process_time()
        src=source_generator(k)
        enumerative=generic_ast_search(k)
        strongest=direct_specialist(k)
        assert enumerative["status"]==strongest["status"]=="EXACT_CERTIFIED"
        assert exact_verifier(enumerative["program"],k)
        assert exact_verifier(strongest["program"],k)
        finite=exact_affine_poly_fails(k)
        row={"h_private_source_generation":h,"source_no_h":src,
             "enumerative_AST":enumerative,"strong_classical":strongest,
             "degree1_machine_no_go":finite,
             "all_degrees_pole_no_go_proved":True,
             "whole_trial_process_cpu_s":time.process_time()-t0}
        output["positive"].append(row)
    for k in NEGATIVE:
        if math.isqrt(k)**2==k:continue
        source=source_generator(k)
        strongest=direct_specialist(k)
        generic=generic_ast_search(k,max_abs=6)
        # Here NO INTEGER coefficient candidate of the restricted
        # reciprocal-shift program grammar. Do not claim no rational
        # semiconjugacy of arbitrary forms.
        assert strongest["program"] is None and generic["program"] is None
        output["negative"].append({"source":source,"strong_classical":strongest,
                                   "enumerated_div_add":generic,
                                   "full_mobius_or_rational_nonexistence":"NOT_CLAIMED"})
    assert len(output["positive"])==12 and len(output["negative"])==6
    output["decision"]={"new_mathematical_expression_power":"SCOPED_PASS",
        "source_program_synthesis":"CLASSICAL_PASS_12_OF_12",
        "source_grammar_rejection":"6_OF_6_INTEGER_SHIFT_AST_NEGATIVES",
        "neural_expression_creation":"NOT_PROVED",
        "learned_outside_human_grammar":"NOT_PROVED",
        "semantic_original_author_transfer":"NOT_TESTED",
        "full_total_cost_10x":"NOT_PROVED"}
    return output

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    result=execute()
    sha=write(args.out,result)
    print("STRICT_RATIONAL_PRIMITIVE_MATHEMATICAL_RESULT",
          json.dumps({"theorem":result["primary_theorem"],
          "synthetic_positive":len(result["positive"]),
          "synthetic_negative":len(result["negative"]),"sha256":sha,
          "strong_classical_also_solves_all":True},sort_keys=True),flush=True)
