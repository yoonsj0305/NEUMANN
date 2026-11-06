"""Independent finite-source candidate verifier for quantified SMT-LIB HORN.

A new learned proposer may submit ONE typed, executable (define-fun R ...)
for one original (declare-fun R (...) Bool) relation. This module replaces
that declaration ONLY in a byte-identified original CHC source, and asks a
separate SMT solver whether a COUNTEREXAMPLE to each published assertion
exists. Every one must be UNSAT for a source-model PASS.

This is no neural training, no source solution cache, and a PASS here does
NOT prove learned structure novelty, 10x compute or universal transfer.
SAT => a real violated original clause. UNKNOWN/timeout/error => OPEN,
never acceptance. For UNSAT original CHC, no such safe model can PASS.

Current explicit interface: SMT-LIB2 HORN sources with declare-fun Bool
relations and universal/ground assert clauses; candidate define-fun typed
Boolean, nonrecursive. It does not prove UNSAT sources nor accept unsupported
source formats as solutions. Only a separate source SHA lock can make an
external original first blind; this verifier never alters source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


class SMTContractError(ValueError):
    pass


def tokenize(source:str)->list[str]:
    """SMT-LIB balanced tokens, protect comments, quoted symbols and strings."""
    tokens=[]
    i=0
    n=len(source)
    while i<n:
        c=source[i]
        if c.isspace():
            i+=1
            continue
        if c==';':
            while i<n and source[i]!='\n':
                i+=1
            continue
        if c in '()':
            tokens.append(c)
            i+=1
            continue
        if c=='"':
            j=i+1
            while j<n:
                if source[j]=='"':
                    if j+1<n and source[j+1]=='"':
                        j+=2
                        continue
                    j+=1
                    break
                j+=1
            else:
                raise SMTContractError("UNCLOSED_SMT_STRING_LITERAL")
            tokens.append(source[i:j])
            i=j
            continue
        if c=='|':
            j=i+1
            while j<n:
                if source[j]=='\\' and j+1<n:
                    j+=2
                    continue
                if source[j]=='|':
                    j+=1
                    break
                j+=1
            else:
                raise SMTContractError("UNCLOSED_SMT_QUOTED_SYMBOL")
            tokens.append(source[i:j])
            i=j
            continue
        j=i
        while j<n and not source[j].isspace() and source[j] not in '();':
            if source[j] in '"|':
                raise SMTContractError("INVALID_SMT_SYMBOL_DELIMITER")
            j+=1
        if j==i:
            raise SMTContractError("CANNOT_TOKENIZE_SMT_SOURCE")
        tokens.append(source[i:j])
        i=j
    return tokens


def sexps(source:str)->list:
    tokens=tokenize(source)
    stack=[]
    top=[]
    for token in tokens:
        if token=='(':
            new=[]
            if stack:
                stack[-1].append(new)
            stack.append(new)
        elif token==')':
            if not stack:
                raise SMTContractError("EXTRA_CLOSE_PAREN")
            done=stack.pop()
            if not stack:
                top.append(done)
        elif stack:
            stack[-1].append(token)
        else:
            raise SMTContractError("FREE_TOPLEVEL_SYMBOL")
    if stack:
        raise SMTContractError("INCOMPLETE_TOPLEVEL_SEXP")
    return top


def render(form)->str:
    if isinstance(form,list):
        return "("+" ".join(render(x) for x in form)+")"
    if isinstance(form,str):
        return form
    raise SMTContractError("SMT_INVALID_AST_NODE")


def form_name(form)->str:
    return form[0] if isinstance(form,list) and form and isinstance(form[0],str) else ""


def validate_model(source:str,candidate:str,relation:str)->dict:
    src=sexps(source)
    prop=sexps(candidate)
    if len(prop)!=1 or form_name(prop[0])!="define-fun" or len(prop[0])!=5:
        raise SMTContractError("CANDIDATE_MUST_BE_SINGLE_DEFINE_FUN")
    chosen=prop[0]
    if chosen[1]!=relation or not isinstance(chosen[2],list) or chosen[3]!="Bool":
        raise SMTContractError("CANDIDATE_RELATION_NAME_OR_BOOLEAN_RETURN_TYPE_MISMATCH")
    if not chosen[2] or not all(
        isinstance(x,list) and len(x)==2 and isinstance(x[0],str)
        for x in chosen[2]
    ):
        raise SMTContractError("CANDIDATE_PARAMETERS_MALFORMED")
    if len(set(x[0] for x in chosen[2]))!=len(chosen[2]):
        raise SMTContractError("REPEATED_CANDIDATE_ARGUMENT_NAME")
    def all_symbols(expr):
        if isinstance(expr,list):
            return [s for a in expr for s in all_symbols(a)]
        return [expr]
    if relation in all_symbols(chosen[4]):
        raise SMTContractError("SELF_REFERENTIAL_CANDIDATE_NOT_EXECUTABLE")
    allowed={
        "set-logic","set-option","declare-sort","define-sort",
        "declare-datatype","declare-datatypes","declare-fun","declare-const",
        "define-fun","assert","check-sat","exit"
    }
    if not src or form_name(src[0])!="set-logic":
        raise SMTContractError("SOURCE_HAS_NO_DECLARED_SMT_THEORY")
    if not any(form_name(x)=="check-sat" for x in src):
        raise SMTContractError("ORIGINAL_SOURCE_MISSING_CHECK_SAT")
    if any(form_name(x) not in allowed for x in src):
        raise SMTContractError("SOURCE_CONTAINS_UNAPPROVED_TOPLEVEL_ACTION")
    originals=[x for x in src if form_name(x)=="declare-fun" and
        len(x)>=2 and x[1]==relation]
    if len(originals)!=1:
        raise SMTContractError("EXPECTED_ONE_ORIGINAL_DECLARED_RELATION")
    decl=originals[0]
    if len(decl)!=4 or not isinstance(decl[2],list) or decl[3]!="Bool":
        raise SMTContractError("ORIGINAL_BOOLEAN_RELATION_SIGNATURE_MALFORMED")
    if len(chosen[2])!=len(decl[2]):
        raise SMTContractError("RELATION_ARGUMENT_ARITY_MISMATCH")
    if [x[1] for x in chosen[2]]!=decl[2]:
        raise SMTContractError("RELATION_PARAMETER_SORT_MISMATCH")
    clauses=[x[1] for x in src if form_name(x)=="assert" and len(x)==2]
    if len(clauses)<1 or len(clauses)!=sum(form_name(x)=="assert" for x in src):
        raise SMTContractError("ORIGINAL_ASSERTIONS_MALFORMED")
    if any(form_name(x)=="define-fun" and len(x)>1 and x[1]==relation
           for x in src):
        raise SMTContractError("ORIGINAL_ALREADY_DEFINES_CANDIDATE_RELATION")
    # Reject other source assertions used as assumptions: source is a
    # conjunction of Horn clauses; each must be universally true under model.
    context=["(set-logic ALL)"]
    for x in src:
        name=form_name(x)
        if name in ("set-logic","check-sat","exit","assert"):
            continue
        if name=="declare-fun" and x is decl:
            continue
        if name=="set-option":
            # Only pure semantic source; runtime options are not trusted.
            continue
        context.append(render(x))
    context.append(render(chosen))
    return {
       "prefix":"\n".join(context),
       "negated_assertions":["(assert (not "+render(x)+"))" for x in clauses],
       "source_assertions":len(clauses),
       "relation_arity":len(decl[2]),
       "source_sha256":sha(source.encode()),
       "candidate_sha256":sha(candidate.encode())
    }


def check_negated_clause(prefix:str,negated:str,solver:str,cap_s:float)->dict:
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf8") as f:
        f.write(prefix+"\n"+negated+"\n(check-sat)\n")
        f.flush()
        begin=time.perf_counter_ns()
        try:
            p=subprocess.run([solver,"-smt2",f.name],capture_output=True,text=True,
                timeout=cap_s,check=False)
        except subprocess.TimeoutExpired:
            return {"verdict":"OPEN_TIMEOUT",
                "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3)}
        except OSError as e:
            return {"verdict":"INFRA_FAIL_CLOSED","error":str(e)[:160]}
    out=[x.strip().lower() for x in p.stdout.splitlines() if x.strip()]
    elapsed=round((time.perf_counter_ns()-begin)/1e6,3)
    if p.returncode!=0 or out not in (["unsat"],["sat"],["unknown"]):
        return {"verdict":"INFRA_FAIL_CLOSED","exit":p.returncode,
           "stdout_head":out[:5],"stderr_tail":p.stderr[-180:],
           "wall_ms":elapsed}
    return {"verdict":("PROVED_UNSAT" if out==["unsat"] else
            "REFUTED_SAT" if out==["sat"] else "OPEN_UNKNOWN"),
       "wall_ms":elapsed,"solver_answer":out[0]}


def verify(source:str,candidate:str,relation:str,solver:str="z3",cap_s:float=5.0)->dict:
    result={
      "schema":"neumann.q3.independent-original-horn-model-clause-verifier.v1",
      "relation":relation,
      "source_sha256":sha(source.encode()),"candidate_sha256":sha(candidate.encode()),
      "proof_status":"NOT_PROVEN",
      "Q3_learned_invention":"NOT_PROVEN",
      "Q4_full_cost_advantage":"NOT_PROVEN",
      "Q6_independent_formalism_transfer":"NOT_PROVEN",
      "trained_NEUMANN_weights":False,
      "original_source_edited":False,
    }
    if cap_s<=0 or cap_s>60:
        result.update({"proof_status":"INFRA_FAIL_CLOSED","error":"INVALID_PROOF_TIMEOUT"})
        return result
    try:
        ctx=validate_model(source,candidate,relation)
    except SMTContractError as e:
        result.update({"proof_status":"INVALID_CANDIDATE_OR_SOURCE",
            "error":str(e)})
        return result
    proofs=[]
    for i,neg in enumerate(ctx["negated_assertions"]):
        evidence=check_negated_clause(ctx["prefix"],neg,solver,cap_s)
        proofs.append({"original_assertion_index":i,**evidence})
        if evidence["verdict"]!="PROVED_UNSAT":
            result.update({
                "proof_status":("REFUTED_BY_ORIGINAL_SOURCE" if evidence["verdict"]=="REFUTED_SAT" else
                   "OPEN_OR_INFRA_NO_PROOF"),
                "first_failed_assertion":i,"clauses_checked":len(proofs),
                "original_source_assertions":ctx["source_assertions"],
                "relation_arity":ctx["relation_arity"],"evidence":proofs
            })
            return result
    result.update({
        "proof_status":"ALL_ORIGINAL_HORN_ASSERTIONS_PROVED",
        "original_source_assertions":ctx["source_assertions"],
        "relation_arity":ctx["relation_arity"],"clauses_checked":len(proofs),
        "evidence":proofs,
        "all_clause_violations_unsat":True,
        "solver_independence_scope":"Separately run Z3 SMT checks against submitted candidate and original source, NOT source CHC synthesis",
    })
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--candidate",required=True,type=Path)
    ap.add_argument("--relation",required=True)
    ap.add_argument("--solver",default="z3")
    ap.add_argument("--cap-seconds",type=float,default=5)
    args=ap.parse_args()
    verdict=verify(args.source.read_text(),args.candidate.read_text(),
                   args.relation,args.solver,args.cap_seconds)
    print(json.dumps(verdict,indent=2,sort_keys=True))
    return 0 if verdict["proof_status"]=="ALL_ORIGINAL_HORN_ASSERTIONS_PROVED" else 2


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"proof_status":"INFRA_FAIL_CLOSED",
             "error":type(e).__name__+":"+str(e)[:240]},sort_keys=True))
        raise SystemExit(3)
