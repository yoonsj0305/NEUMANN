"""Automatically discover additive-separable polynomial residue invariants.

New compiled representation avoids delegating original nonlinear cubes to the
SMT SAT search. Completely generic integer-polynomial parsing (+,-,*,^k),
free-variable dependency extraction, exact per-variable finite image and
modular sumset DP. Exact QF_LIA theorem independently Z3+cvc5 UNSAT.

This is POSTHOC after synthetic nonlinear SMT timeout & authentic first16
source opens. Existing classical number theory; not learned unique novelty.
"""
from __future__ import annotations
import argparse,itertools,json,time,subprocess
from pathlib import Path
import z3
from research.evidence.q3_cross_prefix_modulo_20261021.first16_general_polynomial_modulus_overapprox_vs_direct import (
    MODULI,source_equations,independent_cvc5_unsat
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    sha256,git_blob_sha1
)

MAX_TERMS=24
MAX_VARS_PER_EQ=18
MAX_EQS_PER_SOURCE=250
MAX_EXPONENT=12

def additive(expr,sign,terms):
    if len(terms)>MAX_TERMS:raise ValueError("ADDITIVE_TERM_CAP")
    k=expr.decl().kind()
    if k==z3.Z3_OP_ADD:
        for c in expr.children():additive(c,sign,terms)
        return
    if k==z3.Z3_OP_SUB:
        cs=expr.children()
        if not cs:raise ValueError("ZERO_SUBTRACTION")
        additive(cs[0],sign,terms)
        for c in cs[1:]:additive(c,-sign,terms)
        return
    if k==z3.Z3_OP_UMINUS:
        additive(expr.arg(0),-sign,terms)
        return
    terms.append((sign,expr))
    if len(terms)>MAX_TERMS:raise ValueError("ADDITIVE_TERM_CAP")

def variable_symbols(term):
    """Exact integer polynomial free-variable set, no unsupported operators."""
    if z3.is_int_value(term):return set()
    k=term.decl().kind()
    if k==z3.Z3_OP_UNINTERPRETED and term.num_args()==0 and term.sort().kind()==z3.Z3_INT_SORT:
        return {str(term)}
    if k in (z3.Z3_OP_ADD,z3.Z3_OP_SUB,z3.Z3_OP_MUL,z3.Z3_OP_UMINUS):
        total=set()
        for c in term.children():total.update(variable_symbols(c))
        return total
    if k==z3.Z3_OP_POWER and term.num_args()==2 and z3.is_int_value(term.arg(1)):
        exponent=int(term.arg(1).as_long())
        if not 0<=exponent<=MAX_EXPONENT:
            raise ValueError("POLYNOMIAL_EXPONENT_RANGE_EXCEEDED")
        return variable_symbols(term.arg(0))
    raise ValueError("NOT_A_POLYNOMIAL_"+str(k))

def eval_poly(term,environment):
    if z3.is_int_value(term):return int(term.as_long())
    k=term.decl().kind()
    if k==z3.Z3_OP_UNINTERPRETED and term.num_args()==0 and term.sort().kind()==z3.Z3_INT_SORT:
        return int(environment[str(term)])
    cs=term.children()
    if k==z3.Z3_OP_ADD:return sum(eval_poly(x,environment) for x in cs)
    if k==z3.Z3_OP_MUL:
        total=1
        for x in cs:total*=eval_poly(x,environment)
        return total
    if k==z3.Z3_OP_SUB:
        if not cs:raise ValueError("BAD_SUBTRACTION")
        total=eval_poly(cs[0],environment)
        for x in cs[1:]:total-=eval_poly(x,environment)
        return total
    if k==z3.Z3_OP_UMINUS:return -eval_poly(cs[0],environment)
    if k==z3.Z3_OP_POWER and len(cs)==2 and z3.is_int_value(cs[1]):
        exponent=int(cs[1].as_long())
        if 0<=exponent<=MAX_EXPONENT:
            return eval_poly(cs[0],environment)**exponent
    raise ValueError("UNSUPPORTED_ARITH_IN_EXACT_INTEGER_EVALUATOR")

def exact_finite_residue_images(source_eq,m):
    """Return exact images for an original full source equation, or ABSTAIN."""
    if not z3.is_eq(source_eq) or source_eq.arg(0).sort().kind()!=z3.Z3_INT_SORT:
        return None
    terms=[]
    try:
        additive(source_eq.arg(0),1,terms)
        additive(source_eq.arg(1),-1,terms)
        if not terms or len(terms)>MAX_TERMS:raise ValueError("UNSUPPORTED_TERM_COUNT")
        contributions={}
        constant=0
        for sign,term in terms:
            names=variable_symbols(term)
            if len(names)>1:raise ValueError("NON_SEPARABLE_MULTIVARIATE_PRODUCT")
            if len(names)==0:
                constant=(constant+sign*eval_poly(term,{}))%m
            else:
                key=next(iter(names))
                if key not in contributions:
                    if len(contributions)>=MAX_VARS_PER_EQ:
                        raise ValueError("TOO_MANY_SOURCE_SYMBOLS_IN_ONE_EQUATION")
                    contributions[key]=[0]*m
                table=contributions[key]
                for r in range(m):
                    table[r]=(table[r]+sign*eval_poly(term,{key:r}))%m
        images={name:sorted(set(table)) for name,table in sorted(contributions.items())}
        possible={constant}
        for im in images.values():
            possible={(a+b)%m for a in possible for b in im}
        return {
           "modulus":m,
           "source_true_equation_sha256":sha256(source_eq.sexpr().encode()),
           "original_additive_terms":len(terms),
           "source_original_free_integer_symbol_count":len(images),
           "true_source_individual_univariate_images":images,
           "true_source_literal_constant_modulus":constant,
           "possible_source_equation_residues_exact":sorted(possible),
           "source_original_equation_infeasible_modulo_m":0 not in possible,
           "no_nonlinear_smt_required_to_find_obstruction":True,
        }
    except (ValueError,KeyError,OverflowError,RecursionError,z3.Z3Exception):
        return None

def independent_finite_QFLIA_certificate(info):
    """Make a strict SMT-LIB QF_LIA input with SET-LOGIC. The initial CI
    failed because bare Z3 to_smt2 omits set-logic, which strict cvc5 refuses.
    Retain that immutable failure and fix only transport, not the maths."""
    m=info["modulus"]
    s=z3.Solver();s.set(timeout=1000)
    terms=[]
    for i,im in enumerate(info["true_source_individual_univariate_images"].values()):
        v=z3.Int("fin_r_"+str(i))
        s.add(z3.Or(*[v==n for n in im]))
        terms.append(v)
    s.add((z3.Sum(terms)+info["true_source_literal_constant_modulus"])%m==0)
    z=s.check()
    cvc=None
    if z==z3.unsat:
        # Emit a TINY standalone QF_LIA proof independently of Z3's
        # to_smt2(), which is not guaranteed cvc5-compatible (it may
        # embed Z3-specific global declarations/status or parser options).
        # Original generated finite images are exact, and no source label
        # or negative result is passed as a premise.
        lines=["(set-logic QF_LIA)"]
        image_groups=list(info["true_source_individual_univariate_images"].values())
        for i,im in enumerate(image_groups):
            name="fin_r_"+str(i)
            lines.append("(declare-fun "+name+" () Int)")
            allowed=" ".join("(= "+name+" "+str(int(v))+")" for v in im)
            lines.append("(assert (or "+allowed+"))")
        items=["fin_r_"+str(i) for i in range(len(image_groups))]
        items.append(str(int(info["true_source_literal_constant_modulus"])))
        plus="(+ "+" ".join(items)+")" if len(items)>1 else items[0]
        lines.append("(assert (= (mod "+plus+" "+str(m)+") 0))")
        lines+=["(check-sat)","(exit)"]
        payload="\n".join(lines)+"\n"
        start=time.perf_counter_ns()
        cvc={"abstract_source_smt2_sha256":sha256(payload.encode()),
             "cvc5_original_math_status":"UNKNOWN","cvc5_exit":None}
        try:
            r=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=2000","-"],
                input=payload,text=True,capture_output=True,timeout=3)
            cvc["cvc5_exit"]=r.returncode
            statuses=[q.strip().upper() for q in r.stdout.splitlines()
                if q.strip().lower() in ("sat","unsat","unknown")]
            if r.returncode==0 and statuses:
                cvc["cvc5_original_math_status"]=statuses[0]
            else:
                cvc["cvc5_stderr_excerpt"]=r.stderr[:280]
                cvc["cvc5_stdout_excerpt"]=r.stdout[:280]
        except Exception as e:
            cvc["error"]=type(e).__name__+":"+str(e)[:250]
        cvc["cvc5_math_abstract_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return {"abstract_Z3":str(z).upper(),
            "independent_original_math_cvc5":cvc,
            "independent_source_modular_obstruction_dual_Z3_cvc5":(
                z==z3.unsat and cvc is not None and
                cvc["cvc5_original_math_status"]=="UNSAT"
            )}

def auto_discover_separable_unbounded(source_solver):
    now=time.perf_counter_ns()
    eqs,dropped,nconj=source_equations(source_solver.assertions())
    record={"status":"UNKNOWN","real_original_unbounded_unsat_proved":False,
            "true_original_conjuncts":nconj,"sound_source_eq_count":len(eqs),
            "unsupported_conjuncts_dropped":dropped,
            "searched_moduli":[],"sparse_univariate_source_term_decomposition":True}
    for m in MODULI:
        begin=time.perf_counter_ns()
        attempt={"modulus":m,"abstract_Z3":"NOT_RUN_NO_OBSTRUCTION",
                 "full_source_equalities_considered":0,"sound_additive_separable_equalities":0}
        for q in eqs[:MAX_EQS_PER_SOURCE]:
            attempt["full_source_equalities_considered"]+=1
            info=exact_finite_residue_images(q,m)
            if info is None:continue
            attempt["sound_additive_separable_equalities"]+=1
            if info["source_original_equation_infeasible_modulo_m"]:
                proof=independent_finite_QFLIA_certificate(info)
                attempt.update(proof)
                attempt["source_proved_equation"]=info
                if proof["independent_source_modular_obstruction_dual_Z3_cvc5"]:
                    record["real_original_unbounded_unsat_proved"]=True
                    record["status"]="SOURCE_ORIGINAL_UNBOUNDED_UNSAT_EXACT_SEPARABLE_RESIDUE_PROOF"
                    record["first_discovered_sound_proof_modulus"]=m
                    break
        attempt["complete_math_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
        record["searched_moduli"].append(attempt)
        if record["real_original_unbounded_unsat_proved"]:break
        if not eqs:break
    record["original_source_analysis_complete_wall_ms"]=(time.perf_counter_ns()-now)/1e6
    return record

def synth_validation():
    # Reuse IDENTICAL immutable 49 test source programs; deliberately the
    # older raw nonlinear-SMT-first controller failed to prove cubes=4 under
    # frozen 175 ms Z3 budget. This new math representation should PASS.
    from research.evidence.q3_cross_prefix_modulo_20261021 import independent_metamorphic_finite_math_guards as test
    test.math_discover_true_original_unsat=auto_discover_separable_unbounded
    test.test()
    print("GENERIC_SEPARABLE_AUTO_DISCOVERY_49_OF_49",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    o=p.parse_args()
    x=json.loads(o.freeze.read_text())
    if x["schema"]!="neumann.q3.cross_eight_original_formula_prefixes_pre_content_16_general_modulo.v1":
        raise RuntimeError("HISTORIC_FIRST_16_COHORT_CHANGED")
    synth_validation()
    cases=[]
    for row in x["source_hash_targets"]:
        rec={"path":row["path"],"sha":row["sha1_git_blob"],"group":row["group"],
             "proven":False,"status":"ABSTAIN"}
        try:
            b=(o.root/row["path"]).read_bytes()
            if len(b)!=row["bytes"] or git_blob_sha1(b)!=row["sha1_git_blob"]:
                raise RuntimeError("TRUE_ORIGINAL_GIT_SHA_MISMATCH")
            source=z3.Solver();source.from_string(b.decode("utf-8"))
            rec["original_source_SHA256"]=sha256(b)
            proof=auto_discover_separable_unbounded(source)
            rec["source_exact_separable_math_certificate"]=proof
            rec["proven"]=proof["real_original_unbounded_unsat_proved"]
            rec["status"]="POSTHOC_TRUE_ORIGINAL_UNBOUNDED_UNSAT" if rec["proven"] else "POSTHOC_UNKNOWN"
        except Exception as e:
            rec["error"]=type(e).__name__+":"+str(e)[:280]
        print("Q3_POSTHOC_SEPARABLE_ORIGINAL",rec["path"].split("/")[-1],
              "PROVED",rec["proven"],"STATUS",rec["status"],
              "ERROR",rec.get("error"),flush=True)
        cases.append(rec)
    count=sum(c["proven"] for c in cases)
    result={
      "schema":"neumann.q3.posthoc_generic_separable_ring_original_16_and_49_synthetic.v1",
      "posthoc_after_first_16_source_opens":True,
      "all_true_original_16_cases_retained":len(cases)==16,
      "original_full_source_SHA_authenticated":sum(bool(c.get("original_source_SHA256")) for c in cases),
      "source_first16_new_unbounded_UNSAT_with_separable_proof":count,
      "previous_raw_nonlinear_modular_synthetic_cube4_failed_at_175ms":True,
      "new_exact_univariate_modular_decomposition_passed_same_49_controls":True,
      "classical_prior_art_algebraic_DP_no_learned_model":True,
      "same_math_structural_compiler_available_to_strong_direct":True,
      "not_first_source_unseen_transfer":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "originals":cases
    }
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3_POSTHOC_DIFFERENT_MATH_16_SOURCE_AUTHENTIC",result["original_full_source_SHA_authenticated"])
    print("Q3_POSTHOC_DIFFERENT_MATH_16_UNBOUNDED_UNSAT",count)
    print("Q3_Q4_GLOBAL_OPEN",result["global_Q3"],result["global_Q4"])
if __name__=="__main__":
    main()
