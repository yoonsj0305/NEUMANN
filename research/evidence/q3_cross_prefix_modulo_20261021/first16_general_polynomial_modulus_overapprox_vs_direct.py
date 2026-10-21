"""General-original polynomial congruence discovery, NOT special three-cube parser.

Pre-source 16 original source blobs from 8 mathematical problem name prefixes.
Build a SOUND over-approximation of actual original integer polynomial
EQUALITIES (and conjunction) by reducing both sides into Z/mZ and allowing
every source variable all residues. All other source constraints are DROPPED,
never replaced with stronger constraints. UNSAT of the finite abstraction
is therefore a true proof of ORIGINAL unbounded integer UNSAT, independent
of how many dropped clauses the original contained.

This is existing classical modular abstract interpretation, not newly
learned reasoning or a novel NEUMANN solver. SAT in the abstraction does
NOT establish SAT of actual original source. Cap Z3 work; UNKNOWN honest.
"""
from __future__ import annotations
import argparse,json,re,subprocess,time
from pathlib import Path
import z3
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)
from research.evidence.g0_fresh_four_unsat_20261021.first_original_four_complete_integer_unsat_mod9 import original_direct

MODULI=(2,3,4,5,7,8,9,11,13,16)
PRE_SOURCE_FREEZE="4edf65e61bfe3830e07effcadaab4487595dc6bd"
ORIGINAL_REV="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
VAR_CAP=90
Z3_MS=175
CVC5_MS=2000

def source_equations(assertions):
    """Original assertion A∧B entails each conjunct. Never take subformula
    of OR or NOT: would be UNSOUND to assert a branch as necessary."""
    conjuncts=[]
    stack=list(assertions)
    while stack:
        node=stack.pop()
        if z3.is_and(node):
            stack.extend(node.children())
        else:conjuncts.append(node)
    equations=[]
    dropped=0
    for term in conjuncts:
        if z3.is_eq(term) and term.arg(0).sort().kind()==z3.Z3_INT_SORT and term.arg(1).sort().kind()==z3.Z3_INT_SORT:
            equations.append(term)
        else:dropped+=1
    return equations,dropped,len(conjuncts)

def polynomial_mod9_safe(expr,renaming,m):
    """Translate only a semiring-homomorphic Int polynomial term.

    All unsupported arithmetic throws, causing the WHOLE equation to be
    DROPPED, never an invented strengthened condition.
    """
    if z3.is_int_value(expr):
        return z3.IntVal(expr.as_long()%m)
    decl=expr.decl()
    k=decl.kind()
    if k==z3.Z3_OP_UNINTERPRETED and expr.num_args()==0 and expr.sort().kind()==z3.Z3_INT_SORT:
        key=str(expr)
        if key not in renaming:
            if len(renaming)>=VAR_CAP:
                raise OverflowError("FREE_SOURCE_VARIABLES_EXCEED_CAP")
            renaming[key]=z3.Int("res_"+str(len(renaming)))
        return renaming[key]
    kids=expr.children()
    if k==z3.Z3_OP_ADD:
        return z3.Sum(*[polynomial_mod9_safe(v,renaming,m) for v in kids])
    if k==z3.Z3_OP_MUL:
        a=z3.IntVal(1)
        for v in kids:a=a*polynomial_mod9_safe(v,renaming,m)
        return a
    if k==z3.Z3_OP_SUB:
        if len(kids)<2:raise ValueError("UNSUPPORTED_SUB")
        a=polynomial_mod9_safe(kids[0],renaming,m)
        for v in kids[1:]:a-=polynomial_mod9_safe(v,renaming,m)
        return a
    if k==z3.Z3_OP_UMINUS:
        if len(kids)!=1:raise ValueError("UNSUPPORTED_UMINUS")
        return -polynomial_mod9_safe(kids[0],renaming,m)
    if k==z3.Z3_OP_POWER and len(kids)==2 and z3.is_int_value(kids[1]) and 0<=kids[1].as_long()<=12:
        exp=int(kids[1].as_long())
        a=polynomial_mod9_safe(kids[0],renaming,m)
        answer=z3.IntVal(1)
        for _ in range(exp):answer=answer*a
        return answer
    raise ValueError("UNSUPPORTED_INT_ARITHMETIC_TERM_"+str(k))

def build_sound_finite(original_eqs,m):
    # Only genuine original conjuncts and sound homomorphic polynomial rewrites.
    renamed={}
    formulas=[]
    skipped=0
    exceeded=False
    for eq in original_eqs:
        tmp=dict(renamed)
        try:
            lhs=polynomial_mod9_safe(eq.arg(0),tmp,m)
            rhs=polynomial_mod9_safe(eq.arg(1),tmp,m)
            # Commit fresh variables ONLY for supported equations
            renamed=tmp
            formulas.append((lhs-rhs)%m==0)
        except OverflowError:
            exceeded=True
            break
        except (ValueError,z3.Z3Exception,RecursionError):
            skipped+=1
    if exceeded:return None,{"limit":"ABSTAIN_VARIABLE_CAP","free_variables":len(renamed)}
    # Empty abstraction is TRUE, cannot refute actual original.
    if not formulas:
        return None,{"limit":"NO_SUPPORTED_POLYNOMIAL_EQUATIONS","unsupported_equality_count":skipped}
    solver=z3.Solver()
    solver.set(timeout=Z3_MS)
    for r in renamed.values():solver.add(r>=0,r<m)
    solver.add(*formulas)
    return solver,{
       "original_source_polynomial_equalities_preserved":len(formulas),
       "unsupported_polynomial_equalities_DROPPED":skipped,
       "fresh_modular_integer_residue_variables":len(renamed),
       "abstraction_restricts_only_lifted_residue_domain":True,
       "finite_ring_modulus":m
    }

def independent_cvc5_unsat(abstract_solver):
    payload=abstract_solver.to_smt2()
    t=time.perf_counter_ns()
    d={"abstract_source_smt2_sha256":sha256(payload.encode()),"cvc5_original_math_status":"UNKNOWN","cvc5_exit":None}
    try:
        p=subprocess.run(["cvc5","--lang=smt2",f"--tlimit-per={CVC5_MS}","-"],
             input=payload,text=True,capture_output=True,timeout=3)
        d["cvc5_exit"]=p.returncode
        lines=[x.strip().upper() for x in p.stdout.splitlines() if x.strip().lower() in ("sat","unsat","unknown")]
        if p.returncode==0 and lines:d["cvc5_original_math_status"]=lines[0]
        else:d["cvc5_stderr_excerpt"]=p.stderr[:200]
    except Exception as e:d["error"]=type(e).__name__+":"+str(e)[:200]
    d["cvc5_math_abstract_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    return d

def math_discover_true_original_unsat(source_solver):
    t=time.perf_counter_ns()
    equations,dropped,count=source_equations(source_solver.assertions())
    receipt={"all_original_source_asserted_conjuncts_seen":count,
             "original_source_integer_eq_conjuncts":len(equations),
             "unsupported_other_source_conjuncts_DROPPED":dropped,
             "sound_original_overapproximation":True,
             "searched_moduli":[],"status":"UNKNOWN",
             "real_original_unbounded_unsat_proved":False}
    for m in MODULI:
        stepstart=time.perf_counter_ns()
        solver,details=build_sound_finite(equations,m)
        step={"modulus":m,**details}
        if solver is None:
            step["abstract_Z3"]="ABSTAIN"
            step["complete_math_wall_ms"]=(time.perf_counter_ns()-stepstart)/1e6
            receipt["searched_moduli"].append(step)
            if details.get("limit") in ("NO_SUPPORTED_POLYNOMIAL_EQUATIONS","ABSTAIN_VARIABLE_CAP"):
                break
            continue
        z=solver.check()
        step["abstract_Z3"]=str(z).upper()
        if z==z3.unsat:
            independent=independent_cvc5_unsat(solver)
            step["independent_original_math_cvc5"]=independent
            if independent["cvc5_original_math_status"]=="UNSAT":
                receipt["status"]="ORIGINAL_UNBOUNDED_INTEGER_UNSAT_BY_SOURCE_DERIVED_FINITE_RING_OVERAPPROX"
                receipt["real_original_unbounded_unsat_proved"]=True
                receipt["first_discovered_sound_proof_modulus"]=m
        step["complete_math_wall_ms"]=(time.perf_counter_ns()-stepstart)/1e6
        receipt["searched_moduli"].append(step)
        if receipt["real_original_unbounded_unsat_proved"]:break
    receipt["original_source_analysis_complete_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    return receipt

def original(root,item):
    start=time.perf_counter_ns()
    row={"source":item["path"],"original_sha":item["sha1_git_blob"],
         "source_group":item["group"],"status":"ABSTAIN",
         "source_Git_SHA_authenticated":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if git_blob_sha1(raw)!=item["sha1_git_blob"] or len(raw)!=item["bytes"]:
            raise RuntimeError("FROZEN_ORIGINAL_SOURCE_SHA_OR_SIZE_MISMATCH")
        row["source_Git_SHA_authenticated"]=True
        row["original_SHA256"]=sha256(raw)
        parser=z3.Solver();parser.from_string(raw.decode("utf-8"))
        row["original_native_statement_count"]=len(parser.assertions())
        row["math_auto_modulus_no_hardcoded_cubes"]=math_discover_true_original_unsat(parser)
        direct=original_direct(raw,parser,4)
        row["unchanged_original_generic_Direct_Z3_cvc5"]=direct
        outcomes=(direct["full_unchanged_source_Z3"],direct["full_unchanged_source_cvc5"])
        if "SAT" in outcomes and "UNSAT" in outcomes:
            row["status"]="FAIL_CONFLICT_RAW_SOLVERS"
        elif row["math_auto_modulus_no_hardcoded_cubes"]["real_original_unbounded_unsat_proved"]:
            if "SAT" in outcomes:
                row["status"]="FAIL_CONFLICT_SOUND_MODULAR_AND_RAW_SAT"
            else:
                row["status"]="ORIGINAL_UNBOUNDED_UNSAT_GENERAL_MODULAR_DUAL_CERTIFIED"
        elif "SAT" in outcomes:
            row["status"]="RAW_DIRECT_SAT_ONLY_NO_NEUMANN_MATH_PROOF"
        elif "UNSAT" in outcomes:
            row["status"]="RAW_DIRECT_UNSAT_ONLY_NO_NEUMANN_MATH_PROOF"
        else:
            row["status"]="ORIGINAL_UNRESOLVED_MATH_AND_DIRECT"
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_OR_GENERAL_ABSTRACTION_ERROR"
        row["error"]=type(e).__name__+":"+str(e)[:370]
    row["whole_case_paid_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_FRESH_EIGHT_PREFIX_ORIGINAL",item["group"],item["path"].split("/")[-1],
          "AUTO_MODULAR",row.get("math_auto_modulus_no_hardcoded_cubes",{}).get("status"),
          "DIRECT",(
              row.get("unchanged_original_generic_Direct_Z3_cvc5",{}).get("full_unchanged_source_Z3"),
              row.get("unchanged_original_generic_Direct_Z3_cvc5",{}).get("full_unchanged_source_cvc5")),
          "FINAL",row["status"],"ERROR",row.get("error"),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    o=p.parse_args()
    x=json.loads(o.freeze.read_text())
    if x["schema"]!="neumann.q3.cross_eight_original_formula_prefixes_pre_content_16_general_modulo.v1":
        raise RuntimeError("ORIGINAL_FROZEN_SOURCE_COHORT_IDENTITY_CHANGED")
    if len(x["source_hash_targets"])!=16 or x["original_revision"].split("@")[-1]!=ORIGINAL_REV:
        raise RuntimeError("ORIGINAL_PRE_SOURCE_FROZEN_16_CHANGED")
    rows=[original(o.root,i) for i in x["source_hash_targets"]]
    structural=sum(r.get("math_auto_modulus_no_hardcoded_cubes",{}).get("real_original_unbounded_unsat_proved",False) for r in rows)
    direct_sat=sum("SAT" in tuple(r.get("unchanged_original_generic_Direct_Z3_cvc5",{}).get(k,"") for k in (
       "full_unchanged_source_Z3","full_unchanged_source_cvc5")) for r in rows)
    direct_unsat=sum("UNSAT" in tuple(r.get("unchanged_original_generic_Direct_Z3_cvc5",{}).get(k,"") for k in (
       "full_unchanged_source_Z3","full_unchanged_source_cvc5")) for r in rows)
    # SAT string exact comparisons above not substring; strong Direct on original.
    groups={name:{"cases":sum(r["source_group"]==name for r in rows),
                   "modular_unsat":sum(r["source_group"]==name and r.get("math_auto_modulus_no_hardcoded_cubes",{}).get("real_original_unbounded_unsat_proved",False) for r in rows)}
            for name in ("MC","MF","MQ","MS","RTA","SC","SF","SQ")}
    report={
       "schema":"neumann.Q3.first16_origin_8_other_prefixes_general_polynomial_modular.v1",
       "frozen_prior_to_first_body_git_sha_commit":PRE_SOURCE_FREEZE,
       "genuine_original_16_git_sha_authenticated":sum(r["source_Git_SHA_authenticated"] for r in rows),
       "all_16_first_case_source_rows_retained":len(rows)==16,
       "eight_distinct_filename_prefixes_not_guaranteed_distinct_authors":True,
       "global_structural_math_automatic_source_UNSAT_count":structural,
       "generic_raw_direct_any_solver_SAT_count":direct_sat,
       "generic_raw_direct_any_solver_UNSAT_count":direct_unsat,
       "case_statuses_conflict_or_unauthenticated":sum(r["status"].startswith("FAIL_") or not r["source_Git_SHA_authenticated"] for r in rows),
       "general_modular_generator_hardcodes_NO_3cube_specialized_rule":True,
       "nonpolynomial_constraints_dropped_sound_overapprox":True,
       "modular_abstract_SAT_is_NOT_original_SAT":True,
       "true_absent_unsat_source_mod9_proofs_not_claimed":True,
       "all_null_or_negative_results_retained":True,
       "learned_unique_structure":"NOT_PROVED",
       "Q3_cross_author_transfer":"NOT_PROVED",
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
       "groups":groups,"cases":rows
    }
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_FIRST_OTHER_EIGHT_PREFIXES_16_AUTHENTIC",report["genuine_original_16_git_sha_authenticated"],"/16")
    print("Q3_FIRST_OTHER_EIGHT_PREFIXES_GENERAL_MATH_UNSAT",structural,"/16")
    print("Q3_FIRST_OTHER_EIGHT_PREFIXES_RAW_DIRECT",direct_sat,"SAT",direct_unsat,"UNSAT")
    print("Q3_FIRST_OTHER_EIGHT_PREFIXES_GROUPS",groups)
    print("Q3_GLOBAL_Q3_OPEN",report["global_Q3"])
if __name__=="__main__":
    main()
