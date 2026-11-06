"""NEUMANN Q3 G0: one frozen exact bounded-variable decomposition on original SMT.
No learning, no source filename logic, no answer lookup. Pure original equations.
Unsat requires complete finite cover and TWO independent branch solvers.
Sat requires an exact satisfying integer assignment of the ORIGINAL formula.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import z3

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/q3_G0_VERYMAX4_EXACT_BOUNDED_REFRAME_PREREG_2026_11_06.json"
INPUT=ROOT/"g0_originals"  # job populates from SHA-validated official release

def now(): return time.monotonic()

def vars_in(expr):
    from z3.z3util import get_vars
    return list(get_vars(expr))

def int_literal(e):
    s=z3.simplify(e)
    return s.as_long() if z3.is_int_value(s) else None

def int_var(e):
    return (z3.is_const(e) and e.sort().kind()==z3.Z3_INT_SORT
      and e.decl().kind()==z3.Z3_OP_UNINTERPRETED)

def flat_conjunction(expressions):
    stack=list(expressions)
    while stack:
        e=stack.pop()
        if z3.is_and(e):
            stack.extend(e.children())
        else:
            yield e

def literal_bounds(expressions):
    """Only universal direct conjunction intervals, never disjunctive assumptions."""
    result={}
    for e in flat_conjunction(expressions):
        if e.num_args()!=2 or e.decl().kind() not in (
              z3.Z3_OP_LE,z3.Z3_OP_LT,z3.Z3_OP_GE,z3.Z3_OP_GT,z3.Z3_OP_EQ):
            continue
        lhs,rhs=e.children()
        kind=e.decl().kind()
        direct=z3.simplify(lhs); inverted=z3.simplify(rhs)
        x=None;c=None;rel=None
        if int_var(lhs):
            c=int_literal(rhs);x=lhs
            rel={z3.Z3_OP_LE:"hi",z3.Z3_OP_LT:"hi_strict",
                 z3.Z3_OP_GE:"lo",z3.Z3_OP_GT:"lo_strict",z3.Z3_OP_EQ:"eq"}[kind]
        elif int_var(rhs):
            c=int_literal(lhs);x=rhs
            rel={z3.Z3_OP_LE:"lo",z3.Z3_OP_LT:"lo_strict",
                 z3.Z3_OP_GE:"hi",z3.Z3_OP_GT:"hi_strict",z3.Z3_OP_EQ:"eq"}[kind]
        if x is None or c is None:
            continue
        name=x.decl().name()
        entry=result.setdefault(name,{"var":x,"lo":None,"hi":None})
        if rel in ("lo","lo_strict","eq"):
            lower=c+(rel=="lo_strict")
            entry["lo"]=lower if entry["lo"] is None else max(entry["lo"],lower)
        if rel in ("hi","hi_strict","eq"):
            upper=c-(rel=="hi_strict")
            entry["hi"]=upper if entry["hi"] is None else min(entry["hi"],upper)
    return result

def nonlinear_variables(expressions):
    out=set()
    def scan(e):
        if e.decl().kind()==z3.Z3_OP_MUL:
            groups=[vars_in(x) for x in e.children() if not z3.is_int_value(z3.simplify(x))]
            if len(groups)>=2:
                for group in groups:
                    for variable in group:
                        if int_var(variable):
                            out.add(variable.decl().name())
        for x in e.children():
            scan(x)
    for e in expressions:
        scan(e)
    return out

def choose_finite_split(expressions, cap_vars, cap_cases):
    bounds=literal_bounds(expressions)
    in_nonlinear=nonlinear_variables(expressions)
    choices=[]
    for k,data in bounds.items():
        lo=data["lo"];hi=data["hi"]
        if k in in_nonlinear and lo is not None and hi is not None and 0<=hi-lo+1<=cap_cases:
            choices.append((hi-lo+1,k,data["var"],lo,hi))
    choices.sort(key=lambda t:(t[0],t[1]))
    selected=[];total=1
    for width,k,var,lo,hi in choices:
        if len(selected)>=cap_vars:break
        if total*width>cap_cases:continue
        selected.append((k,var,lo,hi))
        total*=width
    return selected,total

def z3_check(expressions, choices, budget_s):
    s=z3.Solver()
    s.set(timeout=max(1,int(budget_s*1000)))
    s.add(*expressions,*choices)
    t=now()
    outcome=s.check()
    return str(outcome), (s.model() if outcome==z3.sat else None),now()-t

def cvc5_check(smt2_string, budget_s):
    if budget_s<=0:
        return "UNKNOWN_NO_TIME",0.0
    t=now()
    try:
        proc=subprocess.run(["cvc5","--lang","smt2","--tlimit="+str(max(1,int(budget_s*1000)))],
            input=smt2_string,text=True,capture_output=True,timeout=budget_s+0.1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "UNKNOWN_CVC5_UNAVAILABLE_OR_TIMEOUT",now()-t
    lines=[x.strip() for x in proc.stdout.splitlines() if x.strip()]
    if proc.returncode!=0 or not lines or lines[-1] not in ("sat","unsat","unknown"):
        return "UNKNOWN_CVC5_ERROR",now()-t
    return lines[-1],now()-t

def to_smt2(expressions,restrictions):
    s=z3.Solver()
    s.add(*expressions,*restrictions)
    return s.to_smt2()

def validate_exact_model(expressions, model):
    """A SAT certificate is a fully instantiated exact integer model, not just solver sat."""
    names={v.decl().name():v for e in expressions for v in vars_in(e)}
    values={}
    replacements=[]
    for k,v in names.items():
        if v.sort().kind()!=z3.Z3_INT_SORT:
            return False,{}
        answer=model.eval(v,model_completion=True)
        if not z3.is_int_value(z3.simplify(answer)):
            return False,{}
        integer=int(answer.as_long())
        values[k]=integer
        replacements.append((v,z3.IntVal(integer)))
    for e in expressions:
        concrete=z3.simplify(z3.substitute(e,*replacements))
        if not z3.is_true(concrete):
            return False,values
    return True,values

def baseline_z3(expressions,seconds):
    t=now()
    status,model,_=z3_check(expressions,[],seconds)
    valid=False
    if status=="sat":
        valid,_=validate_exact_model(expressions,model)
        if not valid:status="UNKNOWN_SAT_MODEL_REJECTED"
    return {"status":status,"verified_sat_model":valid,"wall_seconds":round(now()-t,6)}

def baseline_cvc5(expressions,seconds):
    status,wall=cvc5_check(to_smt2(expressions,[]),seconds)
    return {"status":status,"wall_seconds":round(wall,6)}

def bounded_reframe(expressions,prereg,deadline):
    chosen,total=choose_finite_split(expressions,
          prereg["budgets"]["max_selected_bounded_vars"],
          prereg["budgets"]["max_cartesian_cases"])
    record={"chosen_bound_vars":[{"name":k,"lo":lo,"hi":hi}
       for k,v,lo,hi in chosen],"branch_count":total if chosen else 0,
       "branches_checked":0,"sat_model":None,"dual_unsat_branches":0,
       "outcome":"UNKNOWN_NO_SUITABLE_COMPLETE_FINITE_SPLIT"}
    if not chosen:
        return record
    if total<=0:
        record["outcome"]="UNKNOWN_INVALID_FINITE_DOMAIN"
        return record
    domains=[range(lo,hi+1) for _,_,lo,hi in chosen]
    for values in itertools.product(*domains):
        remaining=deadline-now()
        if remaining<=0:
            record["outcome"]="UNKNOWN_BUDGET"
            return record
        assignments=[v==z3.IntVal(a) for (_,v,lo,hi),a in zip(chosen,values)]
        status,model,elapsed=z3_check(expressions,assignments,remaining)
        record["branches_checked"]+=1
        if status=="sat":
            valid,integer_model=validate_exact_model(expressions,model)
            if not valid:
                record["outcome"]="UNKNOWN_UNVERIFIED_SAT"
                return record
            record["sat_model"]=integer_model
            record["outcome"]="PROVEN_SAT_EXACT_ORIGINAL_MODEL"
            return record
        if status!="unsat":
            record["outcome"]="UNKNOWN_BRANCH_NOT_Z3_UNSAT"
            return record
        remaining=deadline-now()
        if remaining<=0:
            record["outcome"]="UNKNOWN_NO_INDEPENDENT_PROOF_BUDGET"
            return record
        dual,_=cvc5_check(to_smt2(expressions,assignments),remaining)
        if dual!="unsat":
            record["outcome"]="UNKNOWN_BRANCH_NOT_INDEPENDENTLY_UNSAT"
            return record
        record["dual_unsat_branches"]+=1
    if record["branches_checked"]==total and record["dual_unsat_branches"]==total:
        record["outcome"]="PROVEN_UNSAT_COMPLETE_Z3_AND_CVC5_BRANCH_COVER"
    else:
        record["outcome"]="UNKNOWN_INCOMPLETE_COVER"
    return record

def run():
    prereg=json.loads(PRE.read_text())
    records=[]
    all_source_present=True
    for name in prereg["full_four_source_file_names"]:
        path=INPUT/name
        if not path.exists():
            records.append({"file":name,"status":"INFRA_MISSING_PINNED_ORIGINAL"})
            all_source_present=False
            continue
        raw=path.read_bytes()
        item={"file":name,"source_sha256":hashlib.sha256(raw).hexdigest(),
              "source_bytes":len(raw)}
        if len(raw)>prereg["budgets"]["max_raw_source_bytes_per_case"]:
            item["status"]="UNKNOWN_SOURCE_OVER_CAP";records.append(item);continue
        try:
            assertions=list(z3.parse_smt2_string(raw.decode("utf-8")))
            assert assertions,"EMPTY_BENCHMARK"
        except Exception as err:
            item["status"]="UNKNOWN_SMT2_PARSE";item["parse_error"]=type(err).__name__
            records.append(item);continue
        item["assertion_count"]=len(assertions)
        t=now()
        item["baseline_z3"]=baseline_z3(assertions,prereg["budgets"]["source_solver_wall_seconds_each"])
        item["baseline_cvc5"]=baseline_cvc5(assertions,prereg["budgets"]["source_solver_wall_seconds_each"])
        start=now()
        item["reframe"]=bounded_reframe(assertions,prereg,
            start+prereg["budgets"]["refame_total_wall_seconds_each"])
        item["reframe_wall_seconds"]=round(now()-start,6)
        baseline_z=item["baseline_z3"]["status"]
        baseline_c=item["baseline_cvc5"]["status"]
        new=item["reframe"]["outcome"]
        item["new_matched_positive"]=(new.startswith("PROVEN_")
           and baseline_z not in ("sat","unsat")
           and baseline_c not in ("sat","unsat")
           and baseline_c not in ("UNKNOWN_CVC5_UNAVAILABLE_OR_TIMEOUT",
                                  "UNKNOWN_CVC5_ERROR"))
        item["status"]="G0_POSITIVE" if item["new_matched_positive"] else "G0_NO_MATCHED_GAIN"
        item["total_case_wall_seconds"]=round(now()-t,6)
        records.append(item)
    positives=sum(bool(r.get("new_matched_positive")) for r in records)
    return {"schema":"neumann.q3.g0.verymax4.exact-bounded-reframe-first.v1",
       "science_status":("G0_SCOPED_EXACT_CLASSICAL_HEADROOM_PASS" if positives>0
         and all_source_present and len(records)==4 else "G0_NO_CERTIFIED_MATCHED_HEADROOM"),
       "sources_count":len(records),"all_four_original_sources_present":all_source_present,
       "matched_original_positive_count":positives,
       "overall":"NO_LEARNED_NEURAL_STRUCTURE_GENERATION_TESTED",
       "Q3_original_new_learned_structure":"OPEN",
       "Q4_total_cost_advantage":"OPEN",
       "Q6_cross_formalism_generalization":"OPEN",
       "Q7_frontier":"OPEN",
       "source_archive_provenance":"MD5 pinned by GitHub Actions, source SHA256 in each row",
       "records":records}

if __name__=="__main__":
    evidence=run()
    print(json.dumps(evidence,indent=2,sort_keys=True))
