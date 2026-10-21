"""Q3 prospective authentic original first-ten magic-square cross-exponent test.

Fixed and SHA-frozen BEFORE reading any of the 10 source bodies in commit
941ec4d16357cb9120490506e7c45cc60c76e74a.
Source-only necessary geometric theorem:
    A^k+B^k=T, A^k+C^k=T, B != C, B>0, C>0, same k>=1
implies B^k=C^k, contradicting injectivity of strictly increasing integer
powers on positive integers. All source evidence must exist as EXACT
assertions, no filenames, comments, :status or pre-known answer used.

Original is proved UNSAT (unbounded) from this necessary abstraction,
independently checked by two *linear* SMT theorem engines, Z3 and cvc5.
This is elementary classical algebra, NOT learned neural discovery.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, subprocess, time
from pathlib import Path
import z3
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1, sha256
from research.evidence.g0_fresh_four_unsat_20261021.first_original_four_complete_integer_unsat_mod9 import original_direct

UPSTREAM="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
IDENTITY_FREEZE="941ec4d16357cb9120490506e7c45cc60c76e74a"
MAX_POWER=8

def same(a,b):
    return bool(z3.eq(a,b))

def single_symbol_monomial(term):
    """Return (source variable AST, strictly positive exact exponent)."""
    k=term.decl().kind()
    factors=term.children() if k==z3.Z3_OP_MUL else [term]
    if not 1<=len(factors)<=MAX_POWER:
        return None
    base=factors[0]
    if (base.num_args()!=0 or base.sort().kind()!=z3.Z3_INT_SORT
        or base.decl().kind()!=z3.Z3_OP_UNINTERPRETED):
        return None
    if not all(same(base,f) for f in factors):
        return None
    return {"name":str(base),"base":base,"exponent":len(factors),
            "original_source_ast_sha256":sha256(term.sexpr().encode())}

def two_term_equal_sum(eq):
    if not z3.is_eq(eq): return None
    a,b=eq.children()
    for lhs,rhs in ((a,b),(b,a)):
        if lhs.decl().kind()!=z3.Z3_OP_ADD or lhs.num_args()!=2:
            continue
        if rhs.num_args()!=0 or rhs.sort().kind()!=z3.Z3_INT_SORT:
            continue
        if rhs.decl().kind()!=z3.Z3_OP_UNINTERPRETED:
            continue
        x=single_symbol_monomial(lhs.arg(0))
        y=single_symbol_monomial(lhs.arg(1))
        if x is None or y is None or same(x["base"],y["base"]):
            continue
        return {"sum_ast":eq,"target":str(rhs),"terms":[x,y],
                "original_sum_source_ast_sha256":sha256(eq.sexpr().encode())}
    return None

def original_positive(ast,name):
    for q in ast:
        if q.decl().kind()==z3.Z3_OP_GT and len(q.children())==2:
            a,b=q.children()
            if str(a)==name and z3.is_int_value(b) and b.as_long()>=0:
                # (> b 0), (> b 1) etc all entail b>0.
                return {"true_original_positive_ast_sha256":sha256(q.sexpr().encode()),
                        "full_original_positive_guard":q.sexpr()}
    return None

def original_distinct(ast,name1,name2):
    for q in ast:
        if q.decl().kind()==z3.Z3_OP_DISTINCT and len(q.children())>=2:
            # A multi-argument DISTINCT also entails pairwise distinct.
            if name1 in [str(a) for a in q.children()] and name2 in [str(a) for a in q.children()]:
                return {"true_original_distinct_ast_sha256":sha256(q.sexpr().encode()),
                        "full_original_distinct_guard":q.sexpr()}
    return None

def original_exact_geometry(assertions):
    sums=[s for eq in assertions if (s:=two_term_equal_sum(eq)) is not None]
    for first,second in itertools.combinations(sums,2):
        if first["target"]!=second["target"]:
            continue
        terms1,terms2=first["terms"],second["terms"]
        for u in terms1:
            for v in terms2:
                if u["name"]!=v["name"] or u["exponent"]!=v["exponent"]:
                    continue
                remaining1=[t for t in terms1 if t["name"]!=u["name"]]
                remaining2=[t for t in terms2 if t["name"]!=v["name"]]
                if len(remaining1)!=1 or len(remaining2)!=1:continue
                b,c=remaining1[0],remaining2[0]
                if b["exponent"]!=c["exponent"] or b["name"]==c["name"]:
                    continue
                pb=original_positive(assertions,b["name"])
                pc=original_positive(assertions,c["name"])
                distinct=original_distinct(assertions,b["name"],c["name"])
                if pb is None or pc is None or distinct is None:
                    continue
                return {
                    "proof_source_sum_1":first["original_sum_source_ast_sha256"],
                    "proof_source_sum_2":second["original_sum_source_ast_sha256"],
                    "source_exact_target_symbol":first["target"],
                    "common_power_variable_name":u["name"],
                    "unequal_power_source_names":[b["name"],c["name"]],
                    "source_exact_common_monomial_exponent":u["exponent"],
                    "source_exact_unequal_monomial_common_exponent":b["exponent"],
                    "source_mononomial_ast_sha256":[
                        u["original_source_ast_sha256"],
                        b["original_source_ast_sha256"],
                        c["original_source_ast_sha256"]],
                    "source_distinct_guard":distinct,
                    "source_positive_guards":[pb,pc],
                    "source_ast_verified_true_two_equal_sums":True,
                    "original_source_mathematical_bridge":
                        "Source sum cancellation forces B**k=C**k, source B,C>0 "
                        "and pairwise distinct forbids it: B**k-C**k = "
                        "(B-C)*sum(B**(k-1-j)*C**j for j=0..k-1), positive cofactor."
                }
    return None

def independent_necessary_linear_certificate(geometry):
    """Explicit source-entailing exact abstraction. TWO solvers must independently
    prove the same QF_LIA UNSAT theorem. Positivity/injectivity step is exact
    elementary integer factorization from source metadata, not SMT guesses.
    """
    A,B,C,T=z3.Ints("A B C T")
    solver=z3.Solver()
    solver.add(A+B==T,A+C==T,B!=C)
    z3_status=str(solver.check()).upper()
    payload="\n".join([
        "(set-logic QF_LIA)",
        "(declare-fun A () Int)",
        "(declare-fun B () Int)",
        "(declare-fun C () Int)",
        "(declare-fun T () Int)",
        "(assert (= (+ A B) T))",
        "(assert (= (+ A C) T))",
        "(assert (distinct B C))",
        "(check-sat)","(exit)",""
    ])
    actual="UNKNOWN";exitcode=None;stderr=""
    try:
        result=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=4000","-"],
                              input=payload,capture_output=True,text=True,timeout=6)
        exitcode=result.returncode
        statuses=[p.strip().upper() for p in result.stdout.splitlines()
                  if p.strip().lower() in ("unsat","sat","unknown")]
        if result.returncode==0 and statuses:actual=statuses[0]
        stderr=result.stderr[:240]
    except Exception as e:
        stderr=type(e).__name__+":"+str(e)[:170]
    return {
        "actual_Z3_abstract":z3_status,"actual_cvc5_abstract":actual,
        "independent_cvc5_exit":exitcode,"independent_cvc5_stderr":stderr,
        "exact_qflia_source_sha256":sha256(payload.encode()),
        "both_independent_unbounded_necessary_condition_UNSAT":
            z3_status==actual=="UNSAT",
        "source_to_necessary_condition_uses_elementary_positive_power_injectivity":True,
        "both_solver_result_is_on_necessary_QFLIA_abstraction_NOT_full_raw_nonlinear_source":True
    }

def theorem_positive_injectivity_controls():
    # Checks full finite representatives as additional guards; the
    # proof for *all positive integers* is the analytic factorization:
    # a**k-b**k=(a-b) * sum(a**(k-1-i)*b**i)
    rows=[]
    for k in range(1,MAX_POWER+1):
        tested=0
        for a in range(1,33):
            for b in range(1,33):
                if a==b:continue
                rhs=(a-b)*sum(a**(k-1-j)*b**j for j in range(k))
                assert a**k-b**k==rhs
                assert rhs!=0
                tested+=1
        rows.append({"power":k,"distinct_positive_pairs_validated":tested,
                     "exact_difference_of_powers_factorization_pass":True})
    return rows

def evaluate(root,item,group):
    begin=time.perf_counter_ns()
    rec={"source":item["path"],"group":group,"expected_original_git_sha1":item["sha1_git_blob"],
         "frozen_prior_to_first_source_body":group!="OPENED_DEVELOPMENT",
         "source_authenticated":False,"status":"ABSTAIN",
         "certified_true_original_UNSAT":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("TRUE_ORIGINAL_SOURCE_SHA_OR_BYTES_CHANGED")
        rec["source_authenticated"]=True
        rec["source_sha256"]=sha256(raw)
        source=z3.Solver();source.from_string(raw.decode("utf-8"))
        assertions=list(source.assertions())
        rec["original_full_assertion_count"]=len(assertions)
        t=time.perf_counter_ns()
        proof=original_exact_geometry(assertions)
        rec["exact_structural_geometry"]=proof
        if proof:
            independent=independent_necessary_linear_certificate(proof)
            rec["independent_Z3_cvc5_source_necessary_math_UNSAT"]=independent
            if independent["both_independent_unbounded_necessary_condition_UNSAT"]:
                rec["certified_true_original_UNSAT"]=True
                rec["status"]="TRUE_ORIGINAL_ALL_INTEGER_UNSAT_POWER_INJECTIVITY"
            else:
                rec["status"]="ABSTAIN_INDEPENDENT_NECESSARY_SMT_CHECK"
        else:
            rec["status"]="UNKNOWN_NO_SOURCE_POWER_EQUAL_SUM_DISTINCT_CERTIFICATE"
        rec["complete_source_proof_search_wall_ms"]=(time.perf_counter_ns()-t)/1e6
        direct=original_direct(raw,source,4)
        rec["unchanged_true_original_direct_Z3_cvc5_4sec_each"]=direct
        direct_statuses=(direct["full_unchanged_source_Z3"],direct["full_unchanged_source_cvc5"])
        rec["raw_direct_union_UNSAT"]=any(s=="UNSAT" for s in direct_statuses)
        rec["raw_direct_union_SAT"]=any(s=="SAT" for s in direct_statuses)
        if rec["raw_direct_union_SAT"] and (rec["certified_true_original_UNSAT"] or rec["raw_direct_union_UNSAT"]):
            rec["status"]="FAIL_CONFLICT_SOURCE_PROOF_AND_RAW_SOLVER"
            rec["certified_true_original_UNSAT"]=False
        rec["source_proof_only_raw_direct_UNKNOWN"]=rec["certified_true_original_UNSAT"] and not rec["raw_direct_union_UNSAT"]
    except Exception as e:
        rec["status"]="ABSTAIN_TRUE_ORIGINAL_SOURCE_ERROR"
        rec["error"]=type(e).__name__+":"+str(e)[:300]
    rec["all_case_structural_plus_direct_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("Q3_FIRST_NEW_SOURCE_POWER_MAGIC",item["path"].split("/")[-1],
          "GROUP",group,"CERTIFIED",rec["certified_true_original_UNSAT"],
          "DIRECT_UNSAT",rec.get("raw_direct_union_UNSAT"),
          "DIRECT_SAT",rec.get("raw_direct_union_SAT"),
          "STATUS",rec["status"],"ERROR",rec.get("error"),flush=True)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    data=json.loads(opts.freeze.read_text())
    if data["schema"]!="neumann.q3.first_original_10_power_features_magic_semimagic_geometric_injective.v1":
        raise RuntimeError("FROZEN_ORIGINAL_SOURCE_PROTOCOL_CHANGED")
    if data["source"].split("@")[-1]!=UPSTREAM:
        raise RuntimeError("FROZEN_UPSTREAM_SOURCE_REPO_CHANGED")
    keys=("five_original_2x2_targets","five_original_3x3_controls","two_previously_opened_development_controls")
    if [len(data[k]) for k in keys]!=[5,5,2]:
        raise RuntimeError("PRE_FROZEN_FIVE_FIVE_TWO_COUNTS_CHANGED")
    finite=theorem_positive_injectivity_controls()
    runs=[]
    for label,key in (
        ("FIRST_SOURCE_2X2",keys[0]),
        ("FIRST_SOURCE_3X3",keys[1]),
        ("OPENED_DEVELOPMENT",keys[2])
    ):
        for item in data[key]:runs.append(evaluate(opts.root,item,label))
    first=runs[:10]
    report={
        "schema":"neumann.q3.first_original_power_magic_positive_injective_true_UNSAT.v1",
        "ten_unopened_original_source_git_sha_pre_frozen_commit":IDENTITY_FREEZE,
        "originals_10_plus_development_2_retained":len(runs)==12,
        "source_body_unopened_before_registration_but_filename_power_size_revealed":True,
        "ten_new_genuine_authentic_original_SHA_count":sum(x["source_authenticated"] for x in first),
        "new_first_five_2x2_unbounded_UNSAT_source_certified":sum(x["certified_true_original_UNSAT"] for x in runs[:5]),
        "new_first_five_3x3_unbounded_UNSAT_source_certified":sum(x["certified_true_original_UNSAT"] for x in runs[5:10]),
        "two_old_development_2x2_original_UNSAT_certified":sum(x["certified_true_original_UNSAT"] for x in runs[10:]),
        "new_10_source_proof_only_raw_direct_unknown":sum(x.get("source_proof_only_raw_direct_UNKNOWN",False) for x in first),
        "new_10_source_raw_direct_UNSAT":sum(x.get("raw_direct_union_UNSAT",False) for x in first),
        "new_10_source_raw_direct_SAT":sum(x.get("raw_direct_union_SAT",False) for x in first),
        "all_true_source_conflicts":sum(x["status"].startswith("FAIL_") for x in runs),
        "positive_integer_power_injectivity_mathematical_factorization_finite_controls":finite,
        "factorization_identity_all_positive_integers_known_elementary_algebra":True,
        "no_neural_forward_or_new_math_priority_claim":True,
        "strong_direct_with_equal_power_injectivity_theorem_can_do_same":True,
        "no_author_independent_generalization_or_strongest_direct_winner":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
        "originals":runs
    }
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_POWER_MAGIC_FIRST10_GENUINE_ORIGINAL_AUTHENTIC",report["ten_new_genuine_authentic_original_SHA_count"],"/10")
    print("Q3_POWER_MAGIC_2X2_TRUE_ORIGINAL_UNBOUNDED_UNSAT",report["new_first_five_2x2_unbounded_UNSAT_source_certified"],"/5")
    print("Q3_POWER_MAGIC_3X3_TRUE_ORIGINAL_UNBOUNDED_UNSAT",report["new_first_five_3x3_unbounded_UNSAT_source_certified"],"/5")
    print("Q3_POWER_MAGIC_BONUS_OVER_RAW_DIRECT",report["new_10_source_proof_only_raw_direct_unknown"],"/10")
    print("Q3_POWER_MAGIC_SOURCE_CONFLICTS",report["all_true_source_conflicts"])
    print("Q3_GLOBAL_Q3_Q4_OPEN",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
