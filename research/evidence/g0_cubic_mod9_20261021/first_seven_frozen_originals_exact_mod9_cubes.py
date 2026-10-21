"""Fixed algorithm FIRST-transfer on seven source-unopened authentic SMT-COMP
2026 all-17-solver unresolved QF_NIA Sum-of-3-cubes original programs.

One opened development original STC_0228 first found by exact numpy numerical
search AFTER source inspection. The generic 10k / mod9 / two-sum program was
frozen before first reading the other seven source bodies (commit 8ee9fbf).
Every SAT is grounded into unchanged SMT2 assertions in independent Z3 and
pinned cvc5, with a wrong-witness negative control.
No neural model/weights/inference, no novel arithmetic algorithm claim.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import numpy as np
import z3

from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256

SOURCE_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
FIRST_FUTURE_FREEZE="8ee9fbf8588ae0dd3cea67c121d4fde02699426c"
SEARCH_K=10000
ORDER_MOD9=(0,1,8)
BATCH=96

def structural_source(original_bytes):
    solver=z3.Solver()
    solver.from_string(original_bytes.decode("utf-8"))
    assert len(solver.assertions())==1,"REJECT_NOT_SINGLE_ASSERT_ORIGINAL"
    equation=solver.assertions()[0]
    assert z3.is_eq(equation),"REJECT_NOT_CUBIC_EQUALITY"
    lhs,rhs=equation.children()
    if z3.is_int_value(lhs) and not z3.is_int_value(rhs):
        lhs,rhs=rhs,lhs
    assert z3.is_int_value(rhs),"REJECT_NOT_LITERAL_INTEGER_RHS"
    assert lhs.decl().kind()==z3.Z3_OP_ADD and lhs.num_args()==3,"REJECT_NOT_THREE_ADDENDS"
    variables=[]
    for term in lhs.children():
        if term.decl().kind()!=z3.Z3_OP_MUL or term.num_args()!=3:
            raise RuntimeError("REJECT_NOT_EXACT_SYMBOLIC_CUBE")
        a,b,c=term.children()
        if a!=b or b!=c or not z3.is_const(a) or a.sort().kind()!=z3.Z3_INT_SORT:
            raise RuntimeError("REJECT_NOT_IDENTICAL_INTEGER_SYMBOL_CUBE")
        variables.append(a)
    names=[str(v) for v in variables]
    assert len(set(names))==3,"REJECT_NOT_THREE_DISTINCT_SOURCE_VARS"
    from z3.z3util import get_vars
    assert len(get_vars(equation))==3,"REJECT_UNMODELED_SOURCE_SYMBOLS"
    return int(rhs.as_long()),names,solver

def certified_mod9_filter(target):
    # Exhaustive finite mathematical proof: every integer cube modulo nine
    # matches its base's residue class; filtering loses no integer solutions.
    allowed={(x,y,z) for x in range(9) for y in range(9)
             for z in range(9) if (x*x*x+y*y*y+z*z*z-target)%9==0}
    by_cubes={(x,y,z) for x in range(9) for y in range(9)
              for z in range(9) if
              ((x**3)%9+(y**3)%9+(z**3)%9-target)%9==0}
    assert allowed==by_cubes
    for x in range(-100,101):
        assert x**3%9==(x%9)**3%9
    return {"total_mod9_residue_triplets":729,
            "admitted_residue_triplets":len(allowed),
            "all_excluded_729_minus_admitted_residue_classes_provably_impossible":True,
            "mod9_target_remainder":target%9}

def exact_search(target,radius=SEARCH_K):
    started=time.perf_counter_ns()
    domain=np.arange(-radius,radius+1,dtype=np.int64)
    cubes=domain**3
    by_class={v:(domain[np.where(cubes%9==v)[0]],
                 cubes[np.where(cubes%9==v)[0]]) for v in ORDER_MOD9}
    valid_pair_combinations=[]
    eligible_num_pairs=0
    for xclass in ORDER_MOD9:
        for yclass in ORDER_MOD9:
            zclass=(target-xclass-yclass)%9
            if zclass not in ORDER_MOD9:continue
            xs,xc=by_class[xclass]
            ys,yc=by_class[yclass]
            zs,zc=by_class[zclass]
            eligible_num_pairs+=len(xs)*len(ys)
            valid_pair_combinations.append((xclass,yclass,zclass))
    explored=0
    found=None
    for cx,cy,cz in valid_pair_combinations:
        xs,xc=by_class[cx];ys,yc=by_class[cy];zs,zc=by_class[cz]
        for i in range(0,len(xs),BATCH):
            xchunk=xc[i:i+BATCH]
            # Int64 exact at 10k radius: each cube <= 10^12; sum < 2^63.
            wanted=target-(xchunk[:,None]+yc[None,:])
            indices=np.searchsorted(zc,wanted)
            rows,cols=np.where(indices<len(zc))
            explored+=wanted.size
            if len(rows):
                truth=zc[indices[rows,cols]]==wanted[rows,cols]
                if truth.any():
                    j=int(np.flatnonzero(truth)[0])
                    xi,yi=int(rows[j]),int(cols[j])
                    triple=(int(xs[i+xi]),int(ys[yi]),int(zs[int(indices[xi,yi])]))
                    assert sum(int(v)**3 for v in triple)==target
                    found=triple
                    break
        if found is not None:break
    return {
      "radius":radius,
      "fixed_algorithm":"mod9_exact_residue_reframe_plus_sorted_cube_two_sum",
      "source_value_target":target,
      "actual_numeric_witness":found,
      "numeric_witness_exact_equality":None if found is None else sum(int(v)**3 for v in found)==target,
      "candidate_pair_comparisons_executed":explored,
      "total_naive_domain_pairs_eligible_if_unfiltered":(2*radius+1)**2,
      "all_mod9_eligible_pairs_if_full_bound_exhausted":eligible_num_pairs,
      "full_unbounded_integer_satisfiability_if_no_witness":"UNKNOWN_NOT_UNSAT",
      "search_wall_ms":(time.perf_counter_ns()-started)/1e6,
    }

def source_appended_grounded(original_text,names,values):
    # Strip ONLY SMT driver commands; keep every original declaration,
    # definition, assertion, license metadata byte-for-byte.
    remove={"(check-sat)","(exit)","(get-model)","(get-assignment)"}
    rows=[row for row in original_text.splitlines() if row.strip() not in remove]
    def sint(value):return f"(- {-value})" if value<0 else str(value)
    rows.extend(f"(assert (= {name} {sint(value)}))" for name,value in zip(names,values))
    rows.append("(check-sat)")
    rows.append("(exit)")
    return "\n".join(rows)+"\n"

def independent_original_grounded_certificate(original_text,vars_,values,solver,expected):
    begin=time.perf_counter_ns()
    result={"expected_status":expected,"independent_Z3_status":"UNKNOWN",
            "independent_cvc5_status":"UNKNOWN","independent_dual_result":False}
    try:
        local=z3.Solver()
        local.add(*solver.assertions())
        local.add(*(z3.Int(name)==z3.IntVal(value) for name,value in zip(vars_,values)))
        ans=local.check()
        result["independent_Z3_status"]=str(ans).upper()
        payload=source_appended_grounded(original_text,vars_,values)
        result["exact_source_with_ground_assignments_SHA256"]=sha256(payload.encode())
        cvc=subprocess.run(
          ["cvc5","--lang=smt2","--tlimit-per=15000","-"],
          input=payload,capture_output=True,text=True,timeout=18)
        result["independent_cvc5_exit"]=cvc.returncode
        result["independent_cvc5_stdout_sha256"]=sha256(cvc.stdout.encode())
        result["independent_cvc5_stderr_excerpt"]=cvc.stderr[:270]
        candidates=[x.strip().upper() for x in cvc.stdout.splitlines()
                    if x.strip() in ("sat","unsat","unknown")]
        if cvc.returncode==0 and candidates:
            result["independent_cvc5_status"]=candidates[0]
        result["independent_dual_result"]=(
             result["independent_Z3_status"]==expected and
             result["independent_cvc5_status"]==expected)
    except Exception as exc:
        result["error"]=type(exc).__name__+":"+str(exc)[:350]
    result["certificate_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    return result

def evaluate(root,item,development=False):
    begin=time.perf_counter_ns()
    row={
      "source":item["path"],"git_original_blob":item["sha1_git_blob"],
      "scientific_split":"OPENED_DEVELOPMENT" if development else "FIRST_FROZEN_SEVEN_TRANSFER",
      "status":"UNKNOWN_UNTESTED",
      "certified_original_SAT":False,
      "independent_original_verifier_dual":False,
      "model_forward_calls":0,"oracle_answer_at_inference":False
    }
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("AUTHENTIC_ORIGINAL_BYTES_OR_GIT_HASH_CHANGED")
        row["authentic_original_source_sha256"]=sha256(raw)
        target,names,original_solver=structural_source(raw)
        row["original_parsed_three_int_cubes"]=True
        row["original_actual_target"]=target
        row["original_actual_variables"]=names
        row["finite_modular_proof"]=certified_mod9_filter(target)
        if development:
            row["known_local_development_candidate"]=(-3788,-1577,3877)
        numeric=exact_search(target)
        row["reframed_exact_bounded_numeric_search"]=numeric
        candidate=numeric["actual_numeric_witness"]
        if candidate is None:
            row["status"]="UNKNOWN_NO_SAT_WITNESS_WITHIN_FIXED_RADIUS_10000"
        else:
            check=independent_original_grounded_certificate(
                raw.decode("utf-8"),names,candidate,original_solver,"SAT")
            row["authentic_original_dual_Z3_cvc5_model_certificate"]=check
            if check["independent_dual_result"]:
                row["status"]="FULL_ORIGINAL_SAT_INDEPENDENT_Z3_CVC5_CERTIFIED"
                row["certified_original_SAT"]=True
                row["independent_original_verifier_dual"]=True
            else:
                row["status"]="ABSTAIN_UNVERIFIED_NUMERIC_WITNESS"
            if development:
                wrong=list(candidate);wrong[0]+=1
                negative=independent_original_grounded_certificate(
                    raw.decode("utf-8"),names,wrong,original_solver,"UNSAT")
                row["wrong_candidate_original_dual_rejection"]=negative
                row["negative_control_PASS"]=negative["independent_dual_result"]
    except Exception as exc:
        row["status"]="ABSTAIN_ORIGINAL_SOURCE_OR_REFRAME_ERROR"
        row["error"]=type(exc).__name__+":"+str(exc)[:400]
    row["full_source_proof_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("G0_REAL_QFNIA_TRIPLE",row["source"],row["scientific_split"],
          "TARGET",row.get("original_actual_target"),
          "TRIPLE",row.get("reframed_exact_bounded_numeric_search",{}).get("actual_numeric_witness"),
          "STATUS",row["status"],"WALL",round(row["full_source_proof_wall_ms"],2),
          "ERROR",row.get("error"),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    meta=json.loads(opts.freeze.read_text())
    if len(meta["first_transfer_cohort"])!=7 or meta["source"].split("@")[-1]!=SOURCE_COMMIT:
        raise RuntimeError("PRE_FREEZE_SEVEN_ORIGINALS_CHANGED")
    development=evaluate(opts.root,meta["development_original_STC_0228"],True)
    future=[evaluate(opts.root,i,False) for i in meta["first_transfer_cohort"]]
    report={
      "schema":"neumann.g0.qfnia_cubic_mod9_original_first_seven_transfer.v1",
      "seven_before_source_read_frozen_commit":FIRST_FUTURE_FREEZE,
      "all_seven_FIRST_outcome_rows_kept":len(future)==7,
      "opened_posthoc_development_original_STC_0228":{
          "source":development["source"],
          "status":development["status"],
          "found_original_solver_witness":development.get("reframed_exact_bounded_numeric_search",{}).get("actual_numeric_witness"),
          "dual_valid_original_source":development["certified_original_SAT"],
          "negative_control_PASS":development.get("negative_control_PASS",False),
      },
      "first_seven_source_SHA_authenticated":sum(bool(x.get("authentic_original_source_sha256")) for x in future),
      "first_seven_source_source_form_compiles":sum(x.get("original_parsed_three_int_cubes",False) for x in future),
      "first_seven_new_originals_SAT_with_Z3_cvc5_true_source":sum(x["certified_original_SAT"] for x in future),
      "first_seven_not_found_or_unverified":sum(not x["certified_original_SAT"] for x in future),
      "all_actual_source_genuine_dual_witnesses_only":True,
      "NOT_full_integer_unsat_from_bounded_search":True,
      "no_learned_model_or_new_Neumann_weight":True,
      "actual_prior_art_scope":"elementary modular arithmetic and classical sorted two-sum, not new mathematical algorithms",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "first_transfer_rows":future
    }
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_G0_ORIGINAL_OPENED_DEVELOPMENT_SAT_VERIFIED",development["certified_original_SAT"])
    print("Q3_G0_SEVEN_FROZEN_ORIGINAL_FIRST_TRANSFER_SAT_DUAL",
          report["first_seven_new_originals_SAT_with_Z3_cvc5_true_source"],"/7")
    print("Q3_G0_NO_UNSOUND_UNSAT",report["NOT_full_integer_unsat_from_bounded_search"])
    print("Q3_GLOBAL",report["global_Q3"])
if __name__=="__main__":
    main()
