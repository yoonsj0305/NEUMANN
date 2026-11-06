"""G0 critical-path one-shot: real VeryMax SMT original, NOT neural invention.

Try exactly one sound semantic reframe, disjunction specialization, versus
direct native Z3 on identical immutable source within fixed same-runner budgets.
No posthoc tuning after ORIGINAL FIRST. Full original independent cvc5 check
required for a claimed SAT theorem.
"""
from __future__ import annotations

from hashlib import sha1,sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import subprocess
import time
from urllib.request import Request,urlopen

import z3

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G0_VERYMAX_TQLI_BRANCH_FIRST_PREREG_2026_11_06.json"
DECL=re.compile(r"\(declare-fun\s+([^()\s]+)\s+\(\)\s+Int\s*\)")

def git_blob(x:bytes)->str:
    return sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def pinned_original(pre):
    s=pre["source"]
    url="https://raw.githubusercontent.com/"+s["repo"]+"/"+s["commit"]+"/"+s["path"]
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G0-one-first"}),timeout=40) as response:
        data=response.read(1_500_000)
    if len(data)!=s["source_bytes"] or git_blob(data)!=s["git_blob_sha1"]:
        raise ValueError("PINNED_EXTERNAL_ORIGINAL_GIT_BLOB_MISMATCH")
    text=data.decode("utf-8")
    if "(set-logic QF_NIA)" not in text or "(set-info :status sat)" not in text:
        raise ValueError("ORIGINAL_SMT_STATUS_OR_LOGIC_MISMATCH")
    if text.count("(check-sat)")!=1:
        raise ValueError("NOT_ONE_ORIGINAL_CHECK_SAT")
    return data,text,url

def solve_native(clauses,timeout_ms):
    solver=z3.Solver()
    solver.set(timeout=timeout_ms)
    solver.add(*clauses)
    t=time.perf_counter()
    res=solver.check()
    elapsed=(time.perf_counter()-t)*1000
    return str(res),elapsed,(solver.model() if res==z3.sat else None),
           (solver.reason_unknown() if res==z3.unknown else None)

def direct_solver(clauses,seconds):
    solver=z3.Solver()
    solver.set(timeout=int(seconds*1000))
    solver.add(*clauses)
    t=time.perf_counter()
    ans=solver.check()
    return str(ans),(time.perf_counter()-t)*1000,solver.model() if ans==z3.sat else None

def branch_solver(clauses,budget_s,per_candidate_s,max_candidates):
    # Exact strengthening of one original top-level OR, never removing a clause
    # without replacing it with a *sufficient* branch of that same OR.
    eligible=[(i,a) for i,a in enumerate(clauses) if z3.is_or(a)]
    eligible.sort(key=lambda p:(-len(p[1].sexpr()),p[0]))
    if not eligible:
        return {"status":"UNKNOWN_NO_OR_CANDIDATE","candidates":0},None
    idx,original=eligible[0]
    rest=clauses[:idx]+clauses[idx+1:]
    choices=list(original.children())[:max_candidates]
    base=z3.Solver()
    base.add(*rest)
    rows=[]
    begun=time.perf_counter()
    outcome="unknown"
    winner=None
    for j,child in enumerate(choices):
        left=budget_s-(time.perf_counter()-begun)
        if left<=0.15:
            outcome="unknown_budget";break
        # Sound strengthening: branch => original OR. Any model for
        # (rest AND branch) satisfies all ORIGINAL assertions.
        base.push()
        base.add(child)
        base.set(timeout=max(100,int(min(per_candidate_s,left)*1000)))
        started=time.perf_counter()
        r=base.check()
        spent=(time.perf_counter()-started)*1000
        rows.append({"branch_index":j,"status":str(r),"wall_ms":round(spent,3)})
        if r==z3.sat:
            winner=base.model()
            outcome="sat"
            base.pop()
            break
        if r!=z3.unsat and r!=z3.unknown:
            base.pop();raise ValueError("UNSUPPORTED_Z3_RESULT")
        base.pop()
    else:
        outcome="unknown_exhausted_or_unsat" # Cannot infer original UNSAT from capped subset.
    return {"status":outcome,"selected_assertion_index":idx,
            "original_or_children":original.num_args(),
            "original_or_chars":len(original.sexpr()),
            "candidates":len(rows),"candidate_runs":rows,
            "branch_solver_wall_ms":round((time.perf_counter()-begun)*1000,3),
            "budgets":{"total_s":budget_s,"per_candidate_s":per_candidate_s}},winner

def native_original_exact_model(model,source_text,clauses):
    names=DECL.findall(source_text)
    if len(names)!=len(set(names)) or not names:
        raise ValueError("BAD_ORIGINAL_DECLARATION_LIST")
    assignment={}
    for name in names:
        v=model.eval(z3.Int(name),model_completion=True)
        if not z3.is_int_value(v):
            raise ValueError("NON_GROUND_MODEL_VALUE")
        assignment[name]=int(v.as_long())
    assertion_values=[model.eval(ax,model_completion=True) for ax in clauses]
    original_exact=all(z3.is_true(z3.simplify(v)) for v in assertion_values)
    return original_exact,assignment

def independent_cvc5_original_sat(source_text,assignment,timeout_s):
    cvc5=shutil.which("cvc5")
    if cvc5 is None:
        return {"status":"UNKNOWN_VERIFIER_UNAVAILABLE","executable":False}
    # Preserve the ORIGINAL full arithmetic and every original assertion,
    # then add all ground model variable equalities before original check-sat.
    forced="\n".join(
        "(assert (= "+n+" "+(str(v) if v>=0 else "(- "+str(-v)+")")+"))"
        for n,v in sorted(assignment.items()))
    if source_text.count("(check-sat)")!=1:
        raise ValueError("BAD_SOURCE_CHECK_SAT_COUNT")
    script=source_text.replace("(check-sat)",forced+"\n(check-sat)")
    with TemporaryDirectory(prefix="g0_original_cvc5_") as tmp:
        f=Path(tmp)/"all_original_with_exact_witness.smt2"
        f.write_text(script)
        try:
            started=time.perf_counter()
            r=subprocess.run([cvc5,"--lang=smt2",str(f)],
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                 timeout=timeout_s,check=False)
            result=r.stdout.strip().splitlines()
            return {"status":result[0] if result and result[0] in ("sat","unsat","unknown")
                       else "UNKNOWN_VERIFIER_ERROR",
                    "exit_code":r.returncode,"wall_ms":round((time.perf_counter()-started)*1000,3),
                    "stdout_head":r.stdout[:150],
                    "stderr_head":r.stderr[:250],"executable":True}
        except subprocess.TimeoutExpired:
            return {"status":"UNKNOWN_VERIFIER_TIMEOUT","executable":True}

def run():
    pre=json.loads(PRE.read_text())
    original,original_text,url=pinned_original(pre)
    tm=time.perf_counter()
    clauses=list(z3.parse_smt2_string(original_text))
    parsed_ms=(time.perf_counter()-tm)*1000
    if len(clauses)!=114:
        raise ValueError("UNREGISTERED_SOURCE_ASSERTION_COUNT")
    if z3.get_version_string()[:4] not in ("4.13","4.14","4.15","4.16"):
        raise ValueError("UNEXPECTED_NATIVE_Z3_MAJOR_VERSION")
    budget=pre["same_run_budget"]
    direct_status,direct_ms,direct_model=direct_solver(clauses,budget["direct_z3_timeout_s"])
    branch,bmodel=branch_solver(clauses,budget["branch_z3_total_timeout_s"],
                              budget["branch_per_candidate_timeout_s"],
                              budget["max_first_disjunct_candidates"])
    evaluated=False
    independent={"status":"NOT_RUN_NO_BRANCH_SAT"}
    model_count=0
    if bmodel is not None:
        evaluated,assignment=native_original_exact_model(bmodel,original_text,clauses)
        model_count=len(assignment)
        if evaluated:
            independent=independent_cvc5_original_sat(
                original_text,assignment,
                budget["native_independent_witness_validation_timeout_s"])
        else:
            independent={"status":"NATIVE_ORIGINAL_ASSERTION_MODEL_REJECTED"}
    all_valid=bool(evaluated and independent.get("status")=="sat" and
                   independent.get("exit_code")==0)
    if all_valid and direct_status!="sat":
        status="G0_ORIGINAL_CLASSICAL_BRANCH_SAT_VERIFIED"
    elif all_valid:
        status="G0_SAT_VERIFIED_BUT_CLASSICAL_DIRECT_TIE"
    else:
        status="G0_FIRST_NO_NEW_INDEPENDENT_ORIGINAL_PROOF"
    return {
       "schema":"neumann.g0.verymax-tqli-branch-original-first.v1",
       "scientific_status":status,
       "original_git_blob":git_blob(original),
       "original_sha256":sha256(original).hexdigest(),
       "original_url":url,"original_assertion_count":len(clauses),
       "native_z3_version":z3.get_version_string(),
       "parse_wall_ms":round(parsed_ms,3),
       "direct_z3":{"status":direct_status,"wall_ms":round(direct_ms,3),
                    "budget_s":budget["direct_z3_timeout_s"]},
       "branch_reframe":branch,
       "original_all_assertions_evaluated":bool(evaluated),
       "concrete_integer_model_variables":model_count,
       "independent_original_cvc5_with_exact_witness":independent,
       "closed_semantic_proof":all_valid,
       "neural_model_proposal_count":0,
       "G0_strongest_classical_headroom":"NOT_ESTABLISHED",
       "Q3_neural_new_semantics":"NOT_PROVEN",
       "Q4_lifecycle_cost":"NOT_PROVEN",
       "Q6_unseen_independent_formalism":"NOT_PROVEN",
       "Q7_frontier":"NOT_PROVEN",
       "scientific_integrity":"All 114 original Z3 assertions retained and the one chosen OR is strengthened by one of its exact source clauses; no source-specific labels or manually supplied answer. Independent cvc5 original source check required for original SAT claim."
    }

if __name__=="__main__":
    try:
        result=run()
    except Exception as exc:
        result={"schema":"neumann.g0.verymax-tqli-branch-original-first.v1",
                "scientific_status":"INFRA_OR_SOURCE_FAIL_CLOSED",
                "exception_type":type(exc).__name__,
                "exception_message":str(exc)[:350]}
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["scientific_status"] not in (
        "G0_ORIGINAL_CLASSICAL_BRANCH_SAT_VERIFIED",
        "G0_SAT_VERIFIED_BUT_CLASSICAL_DIRECT_TIE"):
        raise SystemExit(1)
