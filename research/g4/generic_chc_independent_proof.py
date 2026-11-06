"""Generic CHC *SAT witness* checker for independent learned structural candidates.

This is the critical interface from a future learned typed graph program to
a real original external CHC, not an oracle that invents an invariant.

Given an unmodified original (set-logic HORN) source with arbitrary
declared Boolean relations R_i and N Horn assertions, a candidate supplies
one *total typed closed definition* R_i(args_i) := Formula_i(args_i) per
relation. Substitute those definitions, then prove each ORIGINAL assertion
valid by asking Z3 whether its negation is UNSAT.

Soundness: a model consisting of these concrete relation functions satisfies
every original Horn clause, thus the original CHC source is SAT. Finite
samples, native solver "sat" output and model confidence alone are NEVER
accepted. The candidate never changes an original assertion.

Restriction: This ONLY verifies a SAT witness (safe CHC solution), not an
UNSAT/reachable-error certificate. Requires definitions for every original
uninterpreted Boolean relation. Non-Boolean uninterpreted function symbols
remain source declarations. Unsupported parser is fail-closed.

No CHC-COMP 2025 reserved target is opened by the module or its synthetic CI.
"""
from __future__ import annotations
import hashlib,re,time
from dataclasses import dataclass

def tokens(source:str)->list[str]:
    i=0;n=len(source);out=[]
    while i<n:
        c=source[i]
        if c.isspace():i+=1;continue
        if c==";":
            j=source.find("\n",i)
            i=n if j<0 else j+1
            continue
        if c in "()":
            out.append(c);i+=1;continue
        if c=="|":
            j=source.find("|",i+1)
            if j<0:raise ValueError("UNTERMINATED_QUOTED_SMT_IDENTIFIER")
            out.append(source[i:j+1]);i=j+1;continue
        if c=='"':
            j=i+1
            while j<n:
                if source[j]=='"':
                    if j+1<n and source[j+1]=='"':j+=2;continue
                    break
                j+=1
            if j>=n:raise ValueError("UNTERMINATED_SMT_STRING")
            out.append(source[i:j+1]);i=j+1;continue
        j=i
        while j<n and not source[j].isspace() and source[j] not in "();":
            if source[j] in '|"' and j!=i:
                raise ValueError("QUOTED_TOKEN_WITHOUT_SEPARATION")
            j+=1
        if i==j:raise ValueError("UNPARSEABLE_SMT_CHARACTER")
        out.append(source[i:j]);i=j
    return out

def parse(source:str):
    t=tokens(source)
    position=0
    def read():
        nonlocal position
        if position>=len(t):raise ValueError("TRUNCATED_SMT_FORM")
        c=t[position];position+=1
        if c=="(":
            children=[]
            while True:
                if position>=len(t):raise ValueError("TRUNCATED_SMT_FORM")
                if t[position]==")":
                    position+=1
                    return children
                children.append(read())
        if c==")":raise ValueError("UNEXPECTED_CLOSING_SMT_PAREN")
        return c
    forms=[]
    while position<len(t):
        forms.append(read())
    return forms

def render(expr):
    if isinstance(expr,str):return expr
    if not isinstance(expr,list):raise ValueError("NON_CANONICAL_SMT_AST")
    return "("+" ".join(render(c) for c in expr)+")"

def is_head(form,head:str)->bool:
    return isinstance(form,list) and len(form)>0 and form[0]==head

def source_contract(source:str)->dict:
    forms=parse(source)
    logics=[f for f in forms if is_head(f,"set-logic")]
    if len(logics)!=1 or logics[0]!=["set-logic","HORN"]:
        raise ValueError("ORIGINAL_SOURCE_NOT_HORN")
    rels={}
    for form in forms:
        if not is_head(form,"declare-fun"):continue
        if len(form)!=4 or not isinstance(form[2],list):
            raise ValueError("UNSUPPORTED_ORIGINAL_RELATION_SIGNATURE")
        if form[3]=="Bool":
            name=form[1]
            if name in rels:raise ValueError("DUPLICATED_ORIGINAL_RELATION")
            rels[name]=form[2]
    assertions=[f[1] for f in forms if is_head(f,"assert") and len(f)==2]
    if not rels or not assertions:raise ValueError("NO_HORN_ORIGINAL_RELATIONS_OR_ASSERTIONS")
    if any(is_head(f,"push") or is_head(f,"pop") or is_head(f,"define-funs-rec") for f in forms):
        raise ValueError("UNSUPPORTED_ORIGINAL_DYNAMIC_OR_RECURSIVE_SMT_CONTEXT")
    return {"forms":forms,"relations":rels,"assertions":assertions}


def _candidate_body(raw:str,relation_symbols:set[str]):
    f=parse(raw)
    if len(f)!=1:raise ValueError("CANDIDATE_NOT_ONE_TOTAL_SMT_FORM")
    # Prevent proposal from injecting SMT commands or calling original CHC
    # relations recursively; only free variables allowed are typed params.
    forbidden={"assert","set-logic","check-sat","declare-fun","define-fun",
       "define-fun-rec","exit","push","pop","reset","get-model"}
    def validate(node):
        if isinstance(node,str):
            if node in relation_symbols:
                raise ValueError("CANDIDATE_CYCLIC_RELATION_REFERENCE")
            return
        if not node:return
        if isinstance(node[0],str) and node[0] in forbidden:
            raise ValueError("ILLEGAL_CANDIDATE_SMT_COMMAND")
        for value in node:validate(value)
    validate(f[0])
    return f[0]


def independent_verify_original_chc_sat(
  original_source:str,
  proposals:dict[str,dict],
  timeout_ms:int=3500,
)->dict:
    """Constructs original-source proof objects; no external original fetched.

    proposal shape {original-relation-name: {"params":list[str], "body":str}}.
    Param names can vary, but declared types are inherited from source.
    """
    try:import z3
    except ImportError:return {"verified":False,"status":"Z3_NOT_INSTALLED"}
    begin=time.perf_counter_ns()
    contract=source_contract(original_source)
    relations=contract["relations"]
    if set(proposals)!=set(relations):
        raise ValueError("MISSING_OR_EXTRA_CANDIDATE_RELATION")
    defs=[]
    for name,sorts in relations.items():
        candidate=proposals[name]
        args=candidate.get("params")
        body=candidate.get("body")
        if not isinstance(args,list) or len(args)!=len(sorts) or not isinstance(body,str):
            raise ValueError("CANDIDATE_TYPED_RELATION_ARITY_MISMATCH")
        if not all(isinstance(x,str) and re.fullmatch(r"[A-Za-z][A-Za-z_0-9]*",x) for x in args):
            raise ValueError("BAD_TYPED_CANDIDATE_PARAM_NAME")
        if len(set(args))!=len(args):raise ValueError("DUPLICATE_TYPED_CANDIDATE_PARAM_NAME")
        expr=_candidate_body(body,set(relations))
        params=[[arg,sort] for arg,sort in zip(args,sorts)]
        defs.append(["define-fun",name,params,"Bool",expr])
    prefix=[["set-logic","ALL"]]
    for form in contract["forms"]:
        if is_head(form,"set-logic") or is_head(form,"assert") or is_head(form,"check-sat") or is_head(form,"exit"):
            continue
        if is_head(form,"declare-fun") and form[1] in relations:
            continue
        prefix.append(form)
    prefix += defs
    header="\n".join(render(f) for f in prefix)+"\n"
    checks=[]
    for i,original_clause in enumerate(contract["assertions"]):
        verification=(header+"(assert (not "+render(original_clause)+"))\n(check-sat)\n")
        s=z3.Solver()
        s.set(timeout=timeout_ms)
        started=time.perf_counter_ns()
        try:
            s.from_string(verification)
            r=str(s.check())
            reason=s.reason_unknown() if r=="unknown" else None
        except z3.Z3Exception as e:
            r="MALFORMED_CANDIDATE_OR_SMT"
            reason=str(e)[:240]
        checks.append({"clause_index":i,"counterexample":r,
          "proven":r=="unsat",
          "ms":round((time.perf_counter_ns()-started)/1e6,3),
          "error_or_unknown_reason":reason})
        if r!="unsat":break
    proven=len(checks)==len(contract["assertions"]) and all(x["proven"] for x in checks)
    return {"verified":proven,
      "status":"ALL_ORIGINAL_CHC_HORN_ASSERTIONS_INDEPENDENTLY_UNSAT_ON_NEGATION"
        if proven else "NOT_INDEPENDENTLY_PROVED",
      "original_source_sha256":hashlib.sha256(original_source.encode()).hexdigest(),
      "candidate_relations_sha256":hashlib.sha256(
         "\n".join(render(f) for f in defs).encode()).hexdigest(),
      "original_relation_count":len(relations),
      "original_assertion_count":len(contract["assertions"]),
      "independent_checks":checks,
      "proof_wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
      "original_CHC_assertions_untouched":True,
      "learned_proposal_not_trusted_without_proof":True,
      "this_is_only_a_CHC_SAT_witness":True}
