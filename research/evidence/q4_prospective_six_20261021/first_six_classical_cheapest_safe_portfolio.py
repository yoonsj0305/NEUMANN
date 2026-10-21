"""Pre-source-frozen Q4 prospective six real originals, same-run classical routes.

Both solvers independently prove ORIGINAL unchanged source Pre/Trans/Post
before counting PASS. Cheap-first has strictly fixed 0.75 sec source-SyGuS
budget and PDR fallback; no source-dependent tuning. Reuse of a prior
source parser and proof verifier is deliberate. No learned Q3 claim.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import z3

from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sha,sexprs,parse_signature,compile_original,compile_typed_original,
    compile_independent_native,dual,elapsed
)
from research.evidence.q3_affine_unopened_transfer_20261021.dragon4_spacer_extracted_dual_3vc import from_spacer_answer

REVISION="13c8deb68a873635879c9a69bc78caebd340f646"
FAST_S=0.75
SLOW_S=15.0
PDR_MS=15000
DUAL_S=8
FROZEN_COMMIT="63f8ca99b8f9f00aa2bd562226d78641e7e9889c"

def verified_3vc(src,native,invariant):
    nxt=z3.substitute(invariant,*list(zip(src["now"],src["next"])))
    obligations={
        "init":z3.And(native["pre"],z3.Not(invariant)),
        "consecution":z3.And(invariant,native["trans"],z3.Not(nxt)),
        "goal":z3.And(invariant,z3.Not(native["post"]))
    }
    tests={key:dual(formula,"unsat",DUAL_S) for key,formula in obligations.items()}
    return all(q["dual_pass"] for q in tests.values()), tests

def original_syguS(raw,src,native,limit_seconds):
    begin=time.perf_counter_ns()
    out={"route":"original_cvc5_SyGuS","allowed_wall_s":limit_seconds,"certified":False}
    try:
        p=subprocess.run(["cvc5","--lang=sygus2",
                          "--tlimit-per="+str(int(limit_seconds*1000)),"-"],
                         input=raw.decode("utf-8"),text=True,
                         capture_output=True,timeout=limit_seconds+0.25)
        out["cvc5_exit"]=p.returncode
        out["raw_solver_stdout_sha256"]=sha(p.stdout.encode())
        out["raw_solver_stdout_bytes"]=len(p.stdout.encode())
        if p.returncode!=0:
            out["status"]="ABSTAIN_SYGUS_EXIT_OR_TIMEOUT"
            return out
        responses=sexprs(p.stdout.encode())
        expected=[x for x in sexprs(raw)
                  if isinstance(x,list) and x and x[0]=="synth-inv"]
        if len(expected)!=1:raise ValueError("UNEXPECTED_SYNTH_INV_SIGNATURE")
        target=expected[0][1]
        found=[]
        def visit(q):
            if not isinstance(q,list):return
            if q and q[0]=="define-fun":found.append(q)
            else:
                for part in q:visit(part)
        for response in responses:visit(response)
        candidates=[x for x in found if len(x)==5 and x[1]==target]
        if len(candidates)!=1 or candidates[0][3]!="Bool":
            out["status"]="ABSTAIN_NO_UNIQUE_SYGUS_INVARIANT"
            return out
        if parse_signature(candidates[0][2])!=src["states"]:
            raise RuntimeError("ORIGINAL_SYGUS_SIGNATURE_MISMATCH")
        state={name:v for (name,_),v in zip(src["states"],src["now"])}
        inv,_=compile_original(candidates[0][4],state,{})
        if not z3.is_bool(inv):raise RuntimeError("INVALID_ORIGINAL_SMT_INVARIANT")
        good,tests=verified_3vc(src,native,inv)
        out["original_native_Z3_cvc5_3VC"]=tests
        out["candidate_original_smt_sha256"]=sha(inv.sexpr().encode())
        out["certified"]=good
        out["status"]="PASS_ORIGINAL_DUAL_3VC" if good else "ABSTAIN_3VC_NOT_DUAL_CERTIFIED"
    except Exception as e:
        out["status"]="ABSTAIN_TIMEOUT_OR_SYGUS_PARSE"
        out["exception"]=type(e).__name__+":"+str(e)[:240]
    finally:
        out["total_route_wall_ms"]=elapsed(begin)
    return out

def native_pdr(src,native):
    begin=time.perf_counter_ns()
    out={"route":"source_Z3_SPACER_plus_Z3_cvc5_original_3VC",
         "PDR_timeout_ms":PDR_MS,"certified":False}
    try:
        now,nxt=src["now"],src["next"]
        reach=z3.Function("source_reach",*[v.sort() for v in now],z3.BoolSort())
        bad=z3.Function("source_bad",z3.BoolSort())
        used=z3.z3util.get_vars(z3.And(native["pre"],native["trans"],native["post"]))
        names={str(x) for x in used}
        allvars=list(used)
        for v in now+nxt:
            if str(v) not in names:
                allvars.append(v);names.add(str(v))
        fp=z3.Fixedpoint()
        fp.set(engine="spacer",timeout=PDR_MS)
        fp.register_relation(reach,bad)
        fp.declare_var(*allvars)
        fp.rule(reach(*now),native["pre"])
        fp.rule(reach(*nxt),z3.And(reach(*now),native["trans"]))
        fp.rule(bad(),z3.And(reach(*now),z3.Not(native["post"])))
        status=fp.query(bad())
        out["original_PDR_reachability"]=str(status)
        if status!=z3.unsat:
            out["status"]="ABSTAIN_PDR_SAT_UNREPLAYED_OR_UNKNOWN"
            if status==z3.unknown:out["reason"]=fp.get_reason_unknown()
            return out
        answer=fp.get_answer()
        out["PDR_answer_sha256"]=sha(str(answer).encode())
        invs=from_spacer_answer(answer,reach,now)
        out["inductive_candidates_extracted"]=len(invs)
        records=[]
        for inv in invs:
            good,checks=verified_3vc(src,native,inv)
            records.append({
                "candidate_sha256":sha(inv.sexpr().encode()),
                "original_full_dual_3VC":checks,
                "certified":good
            })
            if good:
                out["certified"]=True
                break
        out["original_independently_certified_candidates"]=records
        out["status"]="PASS_ORIGINAL_DUAL_3VC" if out["certified"] else "ABSTAIN_UNEXTRACTED_OR_FAILED_INDEPENDENT_3VC"
    except Exception as e:
        out["status"]="ABSTAIN_PDR_EXCEPTION"
        out["exception"]=type(e).__name__+":"+str(e)[:240]
    finally:
        out["total_route_wall_ms"]=elapsed(begin)
    return out

def prepare(root,item):
    raw=(root/item["path"]).read_bytes()
    if len(raw)!=item["bytes"] or blob(raw)!=item["git_blob"]:
        raise RuntimeError("PRECOMMITTED_GIT_OR_LENGTH_MISMATCH")
    source=compile_typed_original(sexprs(raw))
    native=compile_independent_native(sexprs(raw),source)
    checks={kind:dual(z3.Xor(source[kind],native[kind]),"unsat",DUAL_S)
            for kind in ("pre","trans","post")}
    if not all(q["dual_pass"] for q in checks.values()):
        raise RuntimeError("ORIGINAL_SOURCE_NATIVE_PARITY_NOT_DUAL")
    ispre=dual(native["pre"],"sat",DUAL_S)
    notpost=dual(z3.Not(native["post"]),"sat",DUAL_S)
    if not(ispre["dual_pass"] and notpost["dual_pass"]):
        raise RuntimeError("SOURCE_PRE_SAT_OR_NONTRIVIAL_POST_UNPROVEN")
    return raw,source,native,{
        "pinned_source_git_blob":item["git_blob"],
        "source_bytes_sha256":sha(raw),
        "source_original_native_parity":checks,
        "source_original_Pre_SAT":ispre,
        "source_original_NotPost_SAT":notpost
    }

def negative_control(src,native):
    now,nxt=src["now"],src["next"]
    reach=z3.Function("source_reach_neg",*[v.sort() for v in now],z3.BoolSort())
    bad=z3.Function("source_bad_neg",z3.BoolSort())
    used=z3.z3util.get_vars(z3.And(native["pre"],native["trans"],native["post"]))
    vals=list(used);names={str(z) for z in vals}
    for z in now+nxt:
        if str(z) not in names:
            vals.append(z);names.add(str(z))
    fp=z3.Fixedpoint()
    fp.set(engine="spacer",timeout=10000)
    fp.register_relation(reach,bad);fp.declare_var(*vals)
    fp.rule(reach(*now),native["pre"])
    fp.rule(reach(*nxt),z3.And(reach(*now),native["trans"]))
    fp.rule(bad(),z3.And(reach(*now),z3.BoolVal(True)))
    r=fp.query(bad())
    return {"mutation":"Post=False_SYNTHETIC_NEGATIVE_ONLY","actual_query":str(r),
            "correctly_rejects_unsafe_mutation":r==z3.sat}

def per_source(root,item,group_control=False):
    t=time.perf_counter_ns()
    entry={"source":item["path"],"preregistered_git_blob":item["git_blob"],
           "status":"ABSTAIN","new_neural_training":0,"global_Q4":"OPEN"}
    try:
        raw,src,native,identity=prepare(root,item)
        entry["source_identity_and_preconditions"]=identity
        # Equal source, equal CPU: all methods run irrespective of results.
        # The smart method ALWAYS attempts fast SyGuS for 0.75s first.
        entry["standalone_full_SyGuS"]=original_syguS(raw,src,native,SLOW_S)
        entry["standalone_full_PDR"]=native_pdr(src,native)
        start=time.perf_counter_ns()
        first=original_syguS(raw,src,native,FAST_S)
        backup=None
        if not first["certified"]:
            backup=native_pdr(src,native)
        entry["cheap_first_route"]={
          "fast_original_sygus":first,
          "fallback_original_pdr_if_needed":backup,
          "certified":first["certified"] or bool(backup and backup["certified"]),
          "actual_end_to_end_wall_ms":elapsed(start),
          "fallback_used":backup is not None,
        }
        entry["status"]="COMPLETE_ALL_THREE_CLASSICAL_ROUTES"
        if group_control:
            entry["mutated_negative_Post_control"]=negative_control(src,native)
        p=entry["standalone_full_PDR"]
        c=entry["cheap_first_route"]
        if p["certified"] and c["certified"]:
            entry["paired_PDR_over_portfolio_time_ratio"]=p["total_route_wall_ms"]/c["actual_end_to_end_wall_ms"]
        else:
            entry["paired_PDR_over_portfolio_time_ratio"]=None
    except Exception as e:
        entry["status"]="ABSTAIN_ORIGINAL_UNSUPPORTED_OR_RESOURCE"
        entry["error"]=type(e).__name__+":"+str(e)[:320]
    finally:
        entry["full_study_wall_ms"]=elapsed(t)
        print("FIRST_SIX_ORIGINAL",entry["source"],entry["status"],
              "PDR",entry.get("standalone_full_PDR",{}).get("certified"),
              "SYGUS",entry.get("standalone_full_SyGuS",{}).get("certified"),
              "CHEAP_FIRST",entry.get("cheap_first_route",{}).get("certified"),
              "COST_RATIO",entry.get("paired_PDR_over_portfolio_time_ratio"),
              "ERROR",entry.get("error"),flush=True)
    return entry

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    frozen=json.loads(a.freeze.read_text())
    if len(frozen["sources"])!=6 or frozen["upstream_sha"]!=REVISION:
        raise RuntimeError("FROZEN_SIX_REAL_SOURCE_IDENTITY_CHANGED")
    result=[]
    for idx,target in enumerate(frozen["sources"]):
        result.append(per_source(a.root,target,idx in (0,2,4)))
    ratios=[x["paired_PDR_over_portfolio_time_ratio"] for x in result
            if x.get("paired_PDR_over_portfolio_time_ratio") is not None]
    src_count=sum("source_identity_and_preconditions" in x for x in result)
    old_count=sum(x.get("standalone_full_SyGuS",{}).get("certified",False) for x in result)
    pdr_count=sum(x.get("standalone_full_PDR",{}).get("certified",False) for x in result)
    portfolio_count=sum(x.get("cheap_first_route",{}).get("certified",False) for x in result)
    total_PDR=sum(x["standalone_full_PDR"]["total_route_wall_ms"]
                  for x in result if "standalone_full_PDR" in x)
    total_portfolio=sum(x["cheap_first_route"]["actual_end_to_end_wall_ms"]
                        for x in result if "cheap_first_route" in x)
    controls=[x.get("mutated_negative_Post_control") for x in result
              if "mutated_negative_Post_control" in x]
    report={
        "schema":"neumann.q4.first_presource_six_true_original_cheap_first.v1",
        "source_freeze_commit":FROZEN_COMMIT,
        "real_source_first_experiment_not_retuned":True,
        "total_original_program_cases_preserved":len(result),
        "all_six_authenticated":src_count,
        "full_SyGuS_native_dual3VC":old_count,
        "full_PDR_native_dual3VC":pdr_count,
        "cheap_first_native_dual3VC":portfolio_count,
        "total_standalone_PDR_observed_wall_ms":total_PDR,
        "total_cheap_first_observed_wall_ms":total_portfolio,
        "observed_aggregate_PDR_over_portfolio_ratio":total_PDR/total_portfolio if total_portfolio else None,
        "paired_both_success_count":len(ratios),
        "paired_both_success_speed_ratios":ratios,
        "number_cases_cheap_first_faster_than_PDR":sum(r>1 for r in ratios),
        "all_three_mutated_negative_controls":controls,
        "all_controls_pass":len(controls)==3 and all(x["correctly_rejects_unsafe_mutation"] for x in controls),
        "not_generalized_independent_author_family":True,
        "not_SOTA_classical_or_neural_gap_10x":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","neural_model_forward":0,
        "results":result
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("PROSPECTIVE_SIX_SYGUS_PDR_CHEAP_FIRST",old_count,pdr_count,portfolio_count)
    print("PROSPECTIVE_SIX_AGGREGATE_PDR_TO_CHEAP_FIRST",report["observed_aggregate_PDR_over_portfolio_ratio"])
    print("NEGATIVE_CONTROLS",report["all_controls_pass"])
    print("GLOBAL_Q4",report["global_Q4"])
if __name__=="__main__":
    main()
