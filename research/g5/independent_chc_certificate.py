"""NEUMANN G5: independently certify an executable typed CHC invariant witness.

EXACT PROOF CONTRACT: For every original HORN assert clause C, replace
every unknown Bool relation declaration P with the proposed independently
supplied total typed definition, then require UNSAT of NOT(C) under the
full original theory using an independent SMT solver. Never credit mere
model suggestions, original training examples, or solver return strings.

Source and proposed witness remain unmodified in the receipt, with SHA256.
Supported sorts include Int/Bool/Array/ADT through original SMT-LIB sorts.
No candidate learning, no cached solution, no new ARC IDs. The only trusted
engine is official z3-solver, NOT a custom semantic evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def tokens(source:str)->list[str]:
    """SMT-LIB2 S-expression lexer, including |quoted identifiers| and SMT strings."""
    out=[]
    i=0;n=len(source)
    while i<n:
        c=source[i]
        if c.isspace():
            i+=1;continue
        if c==";":
            j=source.find("\n",i)
            i=n if j<0 else j+1
            continue
        if c in "()":
            out.append(c);i+=1;continue
        if c=="|":
            j=source.find("|",i+1)
            if j<0:raise ValueError("UNTERMINATED_QUOTED_SYMBOL")
            out.append(source[i:j+1]);i=j+1;continue
        if c=='"':
            j=i+1
            while j<n:
                if source[j]=='"':
                    if j+1<n and source[j+1]=='"':
                        j+=2;continue
                    j+=1;break
                j+=1
            else:
                raise ValueError("UNTERMINATED_SMT_STRING")
            out.append(source[i:j]);i=j;continue
        j=i
        while j<n and not source[j].isspace() and source[j] not in "();":
            j+=1
        if j==i:raise ValueError("UNRECOGNIZED_SMT_CHAR")
        out.append(source[i:j]);i=j
    return out

def forms(source:str)->list[Any]:
    toks=tokens(source)
    k=0
    def one():
        nonlocal k
        if k>=len(toks):raise ValueError("UNEXPECTED_SMT_EOF")
        t=toks[k];k+=1
        if t==")":raise ValueError("UNBALANCED_SMT_CLOSE")
        if t!="(":
            return t
        body=[]
        while True:
            if k>=len(toks):raise ValueError("UNBALANCED_SMT_OPEN")
            if toks[k]==")":
                k+=1;return body
            body.append(one())
    out=[]
    while k<len(toks):out.append(one())
    if any(not isinstance(x,list) for x in out):
        raise ValueError("NON_TOP_LEVEL_SMT_COMMAND")
    return out

def emit(x:Any)->str:
    if isinstance(x,str):return x
    if isinstance(x,list):return "("+" ".join(emit(y) for y in x)+")"
    raise ValueError("INVALID_ORIGINAL_SMT_AST")

def contract(source:bytes,witness:dict[str,str])->dict:
    if not isinstance(witness,dict) or not witness:
        raise ValueError("EMPTY_ORIGINAL_WITNESS")
    original=forms(source.decode("utf-8"))
    declarations={}
    assertions=[]
    reused_commands=[]
    proof_command_types={"define-fun","declare-fun","declare-const",
       "declare-datatype","declare-datatypes","define-sort","declare-sort",
       "define-fun-rec","define-funs-rec","set-info"}
    for statement in original:
        if not statement:raise ValueError("EMPTY_ORIGINAL_SMT_FORM")
        kind=statement[0]
        if kind=="assert":
            if len(statement)!=2:raise ValueError("NONSTANDARD_HORN_ASSERT")
            assertions.append(statement)
        elif kind=="declare-fun":
            if len(statement)!=4:raise ValueError("MALFORMED_ORIGINAL_PREDICATE")
            _,name,sorts,ret=statement
            if not isinstance(name,str) or not isinstance(sorts,list):
                raise ValueError("NONCANONICAL_ORIGINAL_DECLARATION")
            if ret=="Bool":
                if name in declarations:raise ValueError("DUPLICATE_BOOL_DECL")
                declarations[name]=sorts
            else:
                reused_commands.append(statement)
        elif kind=="set-logic":
            if statement!=["set-logic","HORN"]:
                raise ValueError("NOT_ORIGINAL_HORN_SOURCE")
        elif kind in ("check-sat","exit"):
            if len(statement)!=1:raise ValueError("NONCANONICAL_SMT_QUERY")
        elif kind in proof_command_types:
            reused_commands.append(statement)
        else:
            raise ValueError("UNSUPPORTED_ORIGINAL_SMT_DIRECTIVE_"+str(kind)[:40])
    if not assertions or not declarations:
        raise ValueError("MISSING_SOURCE_RULES_OR_RELATIONS")
    expected=set(declarations)
    actual=set(witness)
    if expected!=actual:
        raise ValueError("CHC_RELATION_WITNESS_COVERAGE_MISMATCH_"+
                         "missing="+",".join(sorted(expected-actual))+
                         "_extra="+",".join(sorted(actual-expected)))
    # The caller cannot smuggle its own declaration, SMT command or solver
    # output into a "body". Verify all supplied candidate terms parse as
    # SINGLE S-expressions, and reject top-level commands.
    predicate_definitions=[]
    for name in sorted(declarations):
        body=witness[name]
        if not isinstance(body,str) or len(body)>20000:
            raise ValueError("INVALID_OR_TOO_LONG_WITNESS_BODY")
        parsed=forms(body)
        if len(parsed)!=1:
            raise ValueError("WITNESS_MUST_BE_ONE_SMT_EXPR")
        e=parsed[0]
        if not isinstance(e,list) and e not in ("true","false"):
            raise ValueError("WITNESS_MUST_BE_BOOLEAN_EXPRESSION")
        formals=[[f"arg{i}",sort] for i,sort in enumerate(declarations[name])]
        predicate_definitions.append(["define-fun",name,formals,"Bool",e])
    result=[
       ["set-logic","ALL"],
       *reused_commands,
       *predicate_definitions,
       *assertions
    ]
    script="\n".join(emit(x) for x in result)+"\n"
    return {"script":script,"original_source_sha256":sha(source),
            "exact_original_relation_count":len(declarations),
            "exact_original_clause_count":len(assertions),
            "original_relation_signatures":{n:[emit(s) for s in declarations[n]]
                     for n in sorted(declarations)},
            "certificate_sha256":sha(json.dumps(witness,sort_keys=True,
                                 separators=(",",":")).encode("utf-8")),
            "original_source_clause_count_retained":len(assertions),
            "all_bool_relations_interpreted":True,
            "no_original_assertion_dropped":True}

def prove(source:bytes,witness:dict[str,str],cap_ms:int=5000)->dict:
    import z3
    begin=time.perf_counter_ns()
    doc=contract(source,witness)
    solver=z3.Solver()
    try:
        solver.from_string(doc["script"])
    except Exception as exc:
        raise ValueError("WITNESS_OR_ORIGINAL_NOT_VALID_Z3_SMT_"+str(exc)[:400])
    clauses=solver.assertions()
    if len(clauses)!=doc["exact_original_clause_count"]:
        raise ValueError("ORIGINAL_CLAUSE_COUNT_CHANGED_AFTER_PARSE")
    checks=[]
    for i,clause in enumerate(clauses):
        s=z3.Solver()
        s.set(timeout=cap_ms)
        s.add(z3.Not(clause))
        st=time.perf_counter_ns()
        verdict=s.check()
        ms=round((time.perf_counter_ns()-st)/1e6,3)
        proved=str(verdict)=="unsat"
        try:why=s.reason_unknown() if str(verdict)=="unknown" else None
        except Exception:why=None
        checks.append({"original_clause_index":i,
           "source_clause_sha256":sha(emit(forms(emit(["assert",str(clause)]))[0]).encode()) if False else None,
           "counterexample_status":str(verdict),
           "negated_original_rule_UNSAT":proved,
           "verify_wall_ms":ms,
           "unknown_reason":why})
        if not proved:
            break
    checks=[{k:v for k,v in row.items() if k!="source_clause_sha256"} for row in checks]
    ok=(len(checks)==doc["exact_original_clause_count"] and
            all(row["negated_original_rule_UNSAT"] for row in checks))
    return {"schema":"neumann.g5.exact-CHC-source-universal-witness.v1",
        "proof_pass":ok,
        "original_source_sha256":doc["original_source_sha256"],
        "certificate_sha256":doc["certificate_sha256"],
        "original_clause_count":doc["exact_original_clause_count"],
        "original_predicate_count":doc["exact_original_relation_count"],
        "candidate_predicate_signatures":doc["original_relation_signatures"],
        "original_retained_clause_count":doc["original_source_clause_count_retained"],
        "checked_original_clauses":len(checks),
        "all_original_universally_proved":ok,
        "negative_rule_counterexample_checks":checks,
        "solver_version":z3.get_version_string(),
        "total_proof_wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
        "program_generation": "EXTERNALLY_SUPPLIED_NOT_LEARNED",
        "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("witness_json",type=Path)
    p.add_argument("--cap-ms",type=int,default=5000)
    args=p.parse_args()
    if args.cap_ms<=0 or args.cap_ms>30000:raise ValueError("INVALID_VERIFIER_BUDGET")
    result=prove(args.source.read_bytes(),json.loads(args.witness_json.read_text()),
        args.cap_ms)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["proof_pass"] else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as ex:
        print(json.dumps({"schema":"neumann.g5.exact-CHC-proof-fail-closed.v1",
           "proof_pass":False,
           "failure":"INFRA_OR_SOURCE_CONTRACT_NOT_PROOF",
           "exception":type(ex).__name__,"message":str(ex)[:400]},sort_keys=True))
        raise SystemExit(3)
