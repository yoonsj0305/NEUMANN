"""Exact bounded-variable bilinear specialization for original QF_NIA.

Only unconditional, syntactically asserted integer domains are eligible.
When x is known in [L,U] with U-L+1<=8, x*y becomes an exhaustive
integer ITE of constant times y. Semantic replacement is exact on the
source's asserted domain, proved by integer case distinction; independent
cvc5 separately checks the universal symbolic multiplier lemma.
This is a HUMAN-SUPPLIED classical representation, not learned invention.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha1,sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from urllib.request import Request,urlopen
import json
import re
import shutil
import subprocess

import z3

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G0_BOUNDED_BILINEAR_CROSS_AUTHOR_FIRST_PREREG_2026_11_06.json"
DECL=re.compile(r"\(declare-fun\s+([^()\s]+)\s+\(\)\s+(Int|Bool)\s*\)")

def git_blob(raw):
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def fetch_source(spec,repo,commit):
    url="https://raw.githubusercontent.com/"+repo+"/"+commit+"/"+spec["path"]
    req=Request(url,headers={"User-Agent":"NEUMANN-G0-EXACT-LINEARIZATION"})
    with urlopen(req,timeout=35) as response:
        raw=response.read(1_500_000)
    if len(raw)!=spec["bytes"] or git_blob(raw)!=spec["git_blob"]:
        raise ValueError("ORIGINAL_EXTERNAL_GIT_SHA_OR_SIZE_MISMATCH")
    return raw.decode("utf-8"),url

def is_symbolic_int(v):
    return (z3.is_const(v) and v.sort().kind()==z3.Z3_INT_SORT
            and v.decl().kind()==z3.Z3_OP_UNINTERPRETED)

def int_literal(v):
    return int(v.as_long()) if z3.is_int_value(v) else None

def unconditional_source_atoms(assertions):
    """Decompose asserted conjunctions ONLY, never OR or implication."""
    todo=list(assertions)
    atoms=[]
    while todo:
        a=todo.pop()
        if z3.is_and(a):
            todo.extend(a.children())
        else:
            atoms.append(a)
    return atoms

def source_bounded_integer_symbols(assertions,max_range):
    constraints=unconditional_source_atoms(assertions)
    lo={};hi={}
    for a in constraints:
        if not z3.is_app(a):
            continue
        kind=a.decl().kind()
        if kind not in (z3.Z3_OP_LE,z3.Z3_OP_GE,z3.Z3_OP_LT,z3.Z3_OP_GT,z3.Z3_OP_EQ):
            continue
        if a.num_args()!=2:
            continue
        left,right=a.children()
        if is_symbolic_int(left) and (c:=int_literal(right)) is not None:
            v=str(left.decl().name())
            if kind==z3.Z3_OP_LE:
                hi[v]=min(hi.get(v,c),c)
            elif kind==z3.Z3_OP_LT:
                hi[v]=min(hi.get(v,c-1),c-1)
            elif kind==z3.Z3_OP_GE:
                lo[v]=max(lo.get(v,c),c)
            elif kind==z3.Z3_OP_GT:
                lo[v]=max(lo.get(v,c+1),c+1)
            else:
                lo[v]=max(lo.get(v,c),c);hi[v]=min(hi.get(v,c),c)
        elif (c:=int_literal(left)) is not None and is_symbolic_int(right):
            v=str(right.decl().name())
            if kind==z3.Z3_OP_LE:
                lo[v]=max(lo.get(v,c),c)
            elif kind==z3.Z3_OP_LT:
                lo[v]=max(lo.get(v,c+1),c+1)
            elif kind==z3.Z3_OP_GE:
                hi[v]=min(hi.get(v,c),c)
            elif kind==z3.Z3_OP_GT:
                hi[v]=min(hi.get(v,c-1),c-1)
            else:
                lo[v]=max(lo.get(v,c),c);hi[v]=min(hi.get(v,c),c)
    for name in set(lo)&set(hi):
        if lo[name]>hi[name]:
            raise ValueError("INCONSISTENT_UNCONDITIONAL_BOUNDS")
    return {v:(lo[v],hi[v]) for v in set(lo)&set(hi)
            if 1<=hi[v]-lo[v]+1<=max_range}

def exact_finite_multiplier(factor,rest,L,U):
    """Equivalent to factor*rest for all integer L<=factor<=U."""
    expression=z3.IntVal(U)*rest
    for k in range(U-1,L-1,-1):
        expression=z3.If(factor==k,z3.IntVal(k)*rest,expression)
    return expression

class BoundedProductCompiler:
    def __init__(self,finite_domains,max_nodes):
        self.domains=finite_domains
        self.cap=max_nodes
        self.memo={}
        self.replacements=0
        self.ranges=Counter()
        self.original_nonconstant_multiplies=0
        self.unreplaced_nonconstant_multiplies=0

    def rewrite(self,e):
        k=e.get_id()
        if k in self.memo:
            return self.memo[k]
        if not z3.is_app(e) or e.num_args()==0:
            self.memo[k]=e
            return e
        args=[self.rewrite(a) for a in e.children()]
        if e.decl().kind()==z3.Z3_OP_MUL:
            symbolic=sum(not z3.is_int_value(a) for a in args)
            if symbolic>=2:
                self.original_nonconstant_multiplies+=1
                for i,a in enumerate(args):
                    if is_symbolic_int(a) and (domain:=self.domains.get(str(a.decl().name()))) is not None:
                        remaining=args[:i]+args[i+1:]
                        if len(remaining)==1:
                            rest=remaining[0]
                        else:
                            rest=z3.Product(*remaining)
                        self.replacements+=1
                        if self.replacements>self.cap:
                            raise ValueError("DISTINCT_REWRITE_CAP_EXCEEDED")
                        L,U=domain
                        self.ranges[(L,U)]+=1
                        out=exact_finite_multiplier(a,rest,L,U)
                        self.memo[k]=out
                        return out
                self.unreplaced_nonconstant_multiplies+=1
        out=e.decl()(*args)
        self.memo[k]=out
        return out

def check_math_lemma_cvc5(L,U,seconds):
    """Independent source-free universal product counterexample = UNSAT."""
    if L>U or U-L+1>8:
        raise ValueError("LEMMA_OUTSIDE_FROZEN_SCOPE")
    def integer(k):
        return str(k) if k>=0 else "(- "+str(-k)+")"
    expr="(* "+integer(U)+" y)"
    for v in range(U-1,L-1,-1):
        mult="(* "+integer(v)+" y)"
        expr="(ite (= b "+str(v)+") "+mult+" "+expr+")"
    script=(" (set-logic QF_NIA)\n"
            "(declare-fun b () Int)\n(declare-fun y () Int)\n"
            "(assert (<= "+integer(L)+" b))\n"
            "(assert (<= b "+integer(U)+"))\n"
            "(assert (not (= (* b y) "+expr+")))\n(check-sat)\n(exit)\n")
    return run_cvc5(script,seconds)

def run_cvc5(script,seconds):
    tool=shutil.which("cvc5")
    if not tool:
        return {"status":"UNKNOWN_NO_INDEPENDENT_CVC5"}
    with TemporaryDirectory() as temp:
        p=Path(temp)/"original_or_lemma.smt2"
        p.write_text(script)
        begun=perf_counter()
        try:
            proc=subprocess.run([tool,"--lang=smt2",str(p)],capture_output=True,text=True,
                                timeout=seconds,check=False)
            response=proc.stdout.strip().splitlines()
            state=response[0] if response and response[0] in ("sat","unsat","unknown") else "UNKNOWN_CVC5_ERROR"
            return {"status":state,"exit_code":proc.returncode,
                    "wall_ms":round((perf_counter()-begun)*1000,3),
                    "error_head":proc.stderr[:180]}
        except subprocess.TimeoutExpired:
            return {"status":"UNKNOWN_CVC5_TIMEOUT"}

def original_model_evaluation(model,source,original):
    names=DECL.findall(source)
    if not names or len(names)!=len(set(v for v,_ in names)):
        raise ValueError("NO_UNIQUE_NATIVE_ORIGINAL_DECLARATIONS")
    assignments=[]
    for name,sort in names:
        if sort=="Int":
            value=model.eval(z3.Int(name),model_completion=True)
            if not z3.is_int_value(value):
                raise ValueError("NO_GROUND_INTEGER_MODEL")
            v=value.as_long()
            smt_v=str(v) if v>=0 else "(- "+str(-v)+")"
        elif sort=="Bool":
            value=model.eval(z3.Bool(name),model_completion=True)
            if not (z3.is_true(value) or z3.is_false(value)):
                raise ValueError("NO_GROUND_BOOLEAN_MODEL")
            smt_v="true" if z3.is_true(value) else "false"
        else:
            raise ValueError("UNSUPPORTED_ORIGINAL_SORT")
        assignments.append("(assert (= "+name+" "+smt_v+"))")
    valid=all(z3.is_true(model.eval(c,model_completion=True)) for c in original)
    return valid,assignments

def independent_original_witness(source,assignments,seconds):
    if source.count("(check-sat)")!=1:
        return {"status":"UNKNOWN_NOT_ONE_ORIGINAL_CHECK"}
    script=source.replace("(check-sat)","\n".join(assignments)+"\n(check-sat)")
    return run_cvc5(script,seconds)

def solver_result(expressions,timeout_s):
    solver=z3.Solver()
    solver.set(timeout=1000*timeout_s)
    solver.add(*expressions)
    t=perf_counter()
    result=solver.check()
    elapsed=round((perf_counter()-t)*1000,3)
    return {"status":str(result),"wall_ms":elapsed},(solver.model() if result==z3.sat else None)

def process_case(case,origin,commit,pre,dev):
    started=perf_counter()
    out={"case":case["path"].split("/")[-1],
         "source_path":case["path"],"source_git_blob":case["git_blob"],
         "external_author_group":"VeryMax_opened_dev" if dev else "UltimateAutomizer_original_metadata_preregistered",
         "source_bytes":case["bytes"],"original_sound_verdict":"UNKNOWN"}
    try:
        source,url=fetch_source(case,origin,commit)
        out["original_url"]=url
        if "(set-logic QF_NIA)" not in source or source.count("(check-sat)")!=1:
            raise ValueError("ORIGINAL_SOURCE_NOT_EXPECTED_QF_NIA")
        tt=perf_counter()
        original=list(z3.parse_smt2_string(source))
        out["parse_wall_ms"]=round((perf_counter()-tt)*1000,3)
        out["original_assertions"]=len(original)
        maxvals=pre["budgets"]["max_range_values"]
        domains=source_bounded_integer_symbols(original,maxvals)
        compiler=BoundedProductCompiler(domains,pre["budgets"]["max_distinct_rewrites"])
        tt=perf_counter()
        rewritten=[compiler.rewrite(ax) for ax in original]
        out["rewrite_wall_ms"]=round((perf_counter()-tt)*1000,3)
        out["eligible_unconditionally_bounded_variables"]=len(domains)
        out["nonlinear_unique_product_nodes_original"]=compiler.original_nonconstant_multiplies
        out["replaced_unique_product_nodes"]=compiler.replacements
        out["nonlinear_unique_product_nodes_unreplaced"]=compiler.unreplaced_nonconstant_multiplies
        out["used_finite_domains"]=[{"lower":L,"upper":U,"unique_rewrites":n}
                                    for (L,U),n in sorted(compiler.ranges.items())]
        original_cap=(pre["budgets"]["dev_direct_z3_seconds"] if dev else pre["budgets"]["external_each_direct_seconds"])
        rewrite_cap=(pre["budgets"]["dev_reframe_z3_seconds"] if dev else pre["budgets"]["external_each_reframe_seconds"])
        baseline,_=solver_result(original,original_cap)
        candidate,model=solver_result(rewritten,rewrite_cap)
        out["baseline_native_full"]=baseline
        out["transformed_native_full"]=candidate
        out["full_original_assertion_model_recheck"]=False
        out["independent_original_cvc5"]={"status":"NOT_RUN_NO_TRANSFORMED_SAT"}
        if model is not None:
            check,assignments=original_model_evaluation(model,source,original)
            out["full_original_assertion_model_recheck"]=check
            if not check:
                raise ValueError("UNSOUND_TRANSFORMED_MODEL_ORIGINAL_FALSE")
            out["independent_original_cvc5"]=independent_original_witness(
                   source,assignments,pre["budgets"]["independent_cvc5_witness_seconds"])
        proved=(bool(out["full_original_assertion_model_recheck"]) and
                out["independent_original_cvc5"].get("status")=="sat" and
                out["independent_original_cvc5"].get("exit_code")==0)
        out["original_new_sat_independently_proved"]=proved
        out["new_over_equal_classical"]=bool(proved and baseline["status"]!="sat")
        out["science_status"]=("CLASSICAL_NEW_ORIGINAL_SAT" if out["new_over_equal_classical"]
                              else "CLASSICAL_DIRECT_TIE" if proved
                              else "NO_INDEPENDENT_ORIGINAL_PROOF")
    except Exception as e:
        out["science_status"]="FAIL_CLOSED_"+type(e).__name__
        out["error"]=str(e)[:250]
        out["original_new_sat_independently_proved"]=False
        out["new_over_equal_classical"]=False
    out["total_process_wall_ms"]=round((perf_counter()-started)*1000,3)
    return out

def run():
    pre=json.loads(PRE.read_text())
    t=perf_counter()
    cases=[(pre["dev_original"],pre["dev_original"]["repo"],
            pre["dev_original"]["commit"],True)]
    cases.extend((s,pre["external_corpus"]["repo"],pre["external_corpus"]["commit"],False)
                 for s in pre["external_corpus"]["files"])
    rows=[]
    for spec,origin,commit,dev in cases:
        row=process_case(spec,origin,commit,pre,dev)
        rows.append(row)
        print("G0_EXACT_SOURCE_CASE "+json.dumps({k:row.get(k) for k in
              ("case","science_status","eligible_unconditionally_bounded_variables",
               "replaced_unique_product_nodes","new_over_equal_classical")},sort_keys=True),
              flush=True,file=__import__("sys").stderr)
    ranges={tuple((d["lower"],d["upper"])) for r in rows for d in r.get("used_finite_domains",[])}
    lemmas=[]
    for L,U in sorted(ranges):
        check=check_math_lemma_cvc5(L,U,pre["budgets"]["independent_lemma_timeout_seconds"])
        lemmas.append({"lower":L,"upper":U,"independent_cvc5":check})
    lemma_pass=all(a["independent_cvc5"].get("status")=="unsat" and
                   a["independent_cvc5"].get("exit_code")==0 for a in lemmas)
    devrow=rows[0]
    transfer=rows[1:]
    all_pinned=(len(rows)==10 and len(transfer)==9 and
                all(not r["science_status"].startswith("FAIL_CLOSED") for r in rows))
    new=sum(bool(r["new_over_equal_classical"]) for r in rows)
    unsafe=sum(int(r.get("full_original_assertion_model_recheck") is False and
                   r.get("transformed_native_full",{}).get("status")=="sat") for r in rows)
    if unsafe:
        status="UNSOUND_REFRAME_OR_INDEPENDENT_CHECK_FAIL"
    elif not all_pinned or not lemma_pass:
        status="G0_FIRST_INCOMPLETE_OR_LEMMA_UNPROVEN"
    elif new>0:
        status="G0_CLASSICAL_REFRAME_ORIGINAL_NEW_PROOF_SCOPED_PASS"
    else:
        status="SEMANTIC_OPERATOR_PASS_CAPABILITY_NO_GO"
    return {
      "schema":"neumann.g0.exact-bounded-bilinear-original-first.v1",
      "science_status":status,
      "dev_opened_original_count":1,
      "external_metadata_preregistered_original_count":9,
      "total_original_source_count":len(rows),
      "precommitted_distinct_external_blobs":len({x["source_git_blob"] for x in transfer}),
      "scope":"classical_human_supplied_exact_integer_conditional_linearization",
      "independent_math_lemma_checks":lemmas,
      "all_independent_math_lemmas_verified":lemma_pass,
      "total_distinct_nonconstant_product_nodes_rewritten":sum(r.get("replaced_unique_product_nodes",0) for r in rows),
      "externally_authored_sources_rewritten":sum(r.get("replaced_unique_product_nodes",0)>0 for r in transfer),
      "source_verifiable_original_new_solutions_vs_native":new,
      "unsafe_original_sat_admissions":unsafe,
      "all_origins_pinned_and_executed":all_pinned,
      "Q3_neural_invention":"NOT_PROVEN",
      "Q4_all_cost_10x":"NOT_PROVEN",
      "Q6_learned_cross_formalism":"NOT_PROVEN",
      "Q7_frontier":"NOT_PROVEN",
      "measured_total_wall_ms":round((perf_counter()-t)*1000,3),
      "rows":rows
    }

if __name__=="__main__":
    import sys
    try:
        result=run()
    except Exception as exc:
        result={"schema":"neumann.g0.exact-bounded-bilinear-original-first.v1",
                "science_status":"INFRA_OR_COMPILER_FAIL_CLOSED",
                "exception_type":type(exc).__name__,
                "exception_message":str(exc)[:350]}
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["science_status"]!="G0_CLASSICAL_REFRAME_ORIGINAL_NEW_PROOF_SCOPED_PASS":
        raise SystemExit(1)
