"""NEUMANN1 RC40. No neural inference for classically tractable problems.
Full original raw RC38+RC39 source-only evidence, 5 tests, 9-task CPU audit
in independently verified SHA ZIP referenced in README.
"""
from itertools import combinations, product
from time import process_time
import numpy as np

OFFSETS=tuple(d for d in range(-7,8) if d!=0)

def _validate(rows, alphabet=None):
    if not isinstance(rows,list) or not rows:raise ValueError("nonempty source required")
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"input","output"}:raise ValueError("row")
        x,y=row["input"],row["output"]
        if not isinstance(x,str) or not isinstance(y,str) or not x or len(x)!=len(y):
            raise ValueError("equal length nonempty strings required")
        if alphabet and (set(x)-set(alphabet) or set(y)-set(alphabet)):
            raise ValueError("alphabet")

def classical_affine(rows, bounds=(-1,0,1)):
    _validate(rows);t=process_time();found=[];count=0
    for a,b in product(bounds,repeat=2):
        count+=1;valid=True
        for row in rows:
            w=row["input"];n=len(w)
            js=[a*i+b*(n-1) for i in range(n)]
            if not all(0<=j<n for j in js) or "".join(w[j] for j in js)!=row["output"]:
                valid=False;break
        if valid:found.append([a,b])
    status=("SOURCE_UNIQUE" if len(found)==1 else
            "SOURCE_AMBIGUOUS" if found else "REPRESENTATION_EXHAUSTED")
    return {"status":status,"codes":found,"candidates_checked":count,
            "cpu_seconds":process_time()-t,"all_length_proof":False}

def independent_affine_proof(source_fit, trusted_contract):
    target={"FIRST":[0,0],"LAST":[0,1],"REVERSE":[-1,1]}
    if source_fit["status"]!="SOURCE_UNIQUE":return {"status":"UNKNOWN_SOURCE"}
    if trusted_contract not in target:return {"status":"UNKNOWN_CONTRACT"}
    if source_fit["codes"][0]!=target[trusted_contract]:
        return {"status":"UNKNOWN_MISMATCH"}
    return {"status":"CLASSICAL_CERTIFIED","code":source_fit["codes"][0],
            "proof_scope":"all nonempty finite strings under affine address semantics",
            "neural_needed":False}

def classical_min_reads(rows, max_heads=4, max_candidates=12000):
    _validate(rows,"ABC")
    if max_heads<0 or max_candidates<=0:raise ValueError("invalid search budget")
    t=process_time();cur=[];labels=[];features=[]
    for row in rows:
        w=row["input"]
        for i,(c,y) in enumerate(zip(w,row["output"])):
            cur.append("ABC".index(c));labels.append("ABC".index(y))
            features.append([("ABC^").index(w[i+d] if 0<=i+d<len(w) else "^")
                             for d in OFFSETS])
    cur=np.array(cur,dtype=np.int64)
    labels=np.array(labels,dtype=np.int8)
    features=np.array(features,dtype=np.int8)
    visited=0
    for k in range(min(max_heads,len(OFFSETS))+1):
        for subset in combinations(range(len(OFFSETS)),k):
            if visited>=max_candidates:
                return {"status":"UNKNOWN_BUDGET","tested":visited,
                        "all_length_proof":False}
            visited+=1;ids=cur.copy()
            for j in subset:ids=ids*4+features[:,j]
            order=np.argsort(ids,kind="stable")
            sorted_ids,ys=ids[order],labels[order]
            if not np.any((sorted_ids[1:]==sorted_ids[:-1]) & (ys[1:]!=ys[:-1])):
                return {"status":"SOURCE_MIN_HEADS","heads":[OFFSETS[j] for j in subset],
                        "minimum_count":k,"tested":visited,
                        "cpu_seconds":process_time()-t,"all_length_proof":False}
    return {"status":"REPRESENTATION_EXHAUSTED","tested":visited,
            "all_length_proof":False}

def classical_first_route(result, *, bounded_class_exhausted=False,
                          external_verifier_ready=False, cost_case_documented=False):
    s=result["status"]
    if s=="CLASSICAL_CERTIFIED":
        return {"decision":"EXECUTE_CLASSICAL","neural":False}
    if s in ("SOURCE_UNIQUE","SOURCE_MIN_HEADS"):
        return {"decision":"CLASSICAL_PROOF_REQUIRED","neural":False}
    if s in ("SOURCE_AMBIGUOUS","UNKNOWN_SOURCE"):
        return {"decision":"GET_MORE_DISTINGUISHING_IO","neural":False}
    if s in ("UNKNOWN_BUDGET","UNKNOWN_CLASSICAL_BUDGET"):
        return {"decision":"CONTINUE_CLASSICAL_OR_UNKNOWN","neural":False}
    if s=="REPRESENTATION_EXHAUSTED":
        if not bounded_class_exhausted:
            return {"decision":"CHECK_CLASSICAL_SEARCH_SCOPE","neural":False}
        if not (external_verifier_ready and cost_case_documented):
            return {"decision":"UNKNOWN_NEW_REPRESENTATION","neural":False}
        return {"decision":"NEURAL_RESEARCH_ELIGIBLE","neural":True,
                "deploy_authorized":False,
                "condition":"failed only the specified bounded classical class"}
    return {"decision":"UNKNOWN_FAIL_CLOSED","neural":False}
