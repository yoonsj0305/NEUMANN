"""RC42 independent read-only audit of immutable FIRST TLS source evidence.

Not importing/rerunning RC39 learner, W-method, TLS source adapter, or original
product oracle. Independently reparses exact external numeric-dot source.
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.request import Request,urlopen
from collections import deque

FIRST_SHA="e577dc6547c5de3d18befaa811d0032074be1b49772475fe376d73b4a573614f"
REPO="damascenodiego/DynamicLstarM"
COMMIT="5095464d597c68a4899cc81e3d415e3696a00242"
FILES={
 "miTLS_0.1.3_server":("experiments/2021_03_dTTT/subjects/tls/miTLS_0.1.3_server_regular.dot",
                       "ecf8810111e643065700e5517740ac88f610a4e4",6,8,8),
 "OpenSSL_1.0.2_server":("experiments/2021_03_dTTT/subjects/tls/OpenSSL_1.0.2_server_regular.dot",
                        "2bde886cab3155ca5388f1f36605f5eb6fd9a660",7,7,7)
}
EDGE=re.compile(r'^\s*(\d+)\s*->\s*(\d+)\s*\[label="([^"]+)"\]\s*$')

def independent_reference(case):
    path,expected_blob,n,ni,no=FILES[case]
    url="https://raw.githubusercontent.com/"+REPO+"/"+COMMIT+"/"+path
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-RC42-first-audit"}),timeout=25) as f:
        raw=f.read(128000)
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if sha!=expected_blob:
        raise ValueError("EXTERNAL_SHA_MISMATCH")
    lines=[x.strip() for x in raw.decode().splitlines() if x.strip()]
    if lines[0]!="digraph {" or lines[-1]!="}":
        raise ValueError("NOT_TLS_DOT")
    initial=None
    states=[]
    edges=[]
    for line in lines[1:-1]:
        if re.fullmatch(r'\d+',line):
            states.append(line)
            if initial is None:
                initial=line
        else:
            m=EDGE.fullmatch(line)
            if not m or "/" not in m.group(3):
                raise ValueError("UNSUPPORTED_TRANSITION")
            s,t,label=m.groups()
            i,o=label.split("/",1)
            edges.append((s,t,i,o))
    if len(states)!=n or len(set(states))!=n or not set(states)==({e[0] for e in edges}|{e[1] for e in edges}):
        raise ValueError("STATES_CHANGED")
    alpha=sorted({e[2] for e in edges})
    output=sorted({e[3] for e in edges})
    if len(alpha)!=ni or len(output)!=no or len(edges)!=n*ni:
        raise ValueError("ALPHABET_OR_COMPLETENESS_CHANGED")
    state_id={s:i for i,s in enumerate(sorted(states,key=lambda s:int(s)))}
    letters={a:chr(65+i) for i,a in enumerate(alpha)}
    emission={a:str(i) for i,a in enumerate(output)}
    table={}
    for s,t,i,o in edges:
        key=(state_id[s],letters[i])
        if key in table:
            raise ValueError("DUPLICATE_EDGE")
        table[key]=(state_id[t],emission[o])
    return state_id[initial],"".join(letters.values()),table

def independent_all_word_product(ast,reference):
    if not isinstance(ast,dict) or ast.get("schema")!="neumann.rc39.mealy-ast.v1":
        return False
    initial,alpha,table=reference
    n=ast.get("states")
    if (ast.get("alphabet")!=list(alpha) or type(n)!=int or n<1
        or type(ast.get("initial"))!=int or not 0<=ast["initial"]<n):
        return False
    moves=ast.get("transitions");outs=ast.get("emissions")
    if not isinstance(moves,list) or not isinstance(outs,list) or len(moves)!=n or len(outs)!=n:
        return False
    q=deque([(initial,ast["initial"])])
    seen=set(q)
    while q:
        a,b=q.popleft()
        if len(moves[b])!=len(alpha) or len(outs[b])!=len(alpha):
            return False
        for i,sym in enumerate(alpha):
            t,o=table[a,sym]
            if outs[b][i]!=o:
                return False
            k=moves[b][i]
            if type(k)!=int or not 0<=k<n:
                return False
            pair=(t,k)
            if pair not in seen:
                seen.add(pair);q.append(pair)
    return True

def audit(path):
    data=Path(path).read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    errors=[]
    if digest!=FIRST_SHA:
        errors.append("ORIGINAL_FIRST_SHA_DRIFT")
    first=json.loads(data)
    rows=first.get("rows",[])
    if len(rows)!=2 or {r["case"] for r in rows}!=set(FILES):
        errors.append("ORIGINAL_MODELS_CHANGED")
    proven=0;mutations=0;queries=0
    for row in rows:
        case=row["case"]
        ref=independent_reference(case)
        ast=row["compiled_ast"]
        valid=independent_all_word_product(ast,ref)
        proven+=int(valid)
        if not valid or not row["complete_source_only_w_certificate"]:
            errors.append("PROGRAM_NOT_PROVEN_"+case)
        # The alternate evaluator uses only raw transitions, never the original product code.
        mutant=json.loads(json.dumps(ast))
        q=mutant["initial"];old=mutant["emissions"][q][0]
        mutant["emissions"][q][0]=next(str(i) for i in range(8) if str(i)!=old)
        if not independent_all_word_product(mutant,ref):
            mutations+=1
        else:
            errors.append("MUTANT_NOT_REJECTED_"+case)
        queries+=row["distinct_source_queries"]
        if row["external_git_blob"]!=FILES[case][1] or not row["wrong_mutant_rejected"]:
            errors.append("ORIGINAL_SOURCE_OR_MUTATION_FLAG_CHANGED_"+case)
    if queries!=742 or first["source_membership_queries_total"]!=742:
        errors.append("ORIGINAL_QUERY_COUNTER_DRIFT")
    if proven!=2 or mutations!=2 or first["science_status"]!="SCOPED_EXTERNAL_TLS_CROSS_PROTOCOL_PASS":
        errors.append("ORIGINAL_SCIENCE_STATUS_INVALID")
    if first["Q6_cross_formalism_semantic_transfer"]!="NOT_PROVEN":
        errors.append("Q6_OVERCLAIM")
    return {"schema":"neumann.q3.rc42.tls-independent-first-audit.v1",
            "audit_pass":not errors,"errors":errors,
            "original_first_sha256":digest,
            "external_first_models":len(rows),
            "independently_all_word_equivalent":proven,
            "mutants_rejected":mutations,
            "source_membership_queries":queries,
            "original_learner_or_W_rerun":False,
            "new_formalism":"NOT_PROVEN"}

if __name__=="__main__":
    x=audit(sys.argv[1])
    print(json.dumps(x,indent=2))
    if not x["audit_pass"]:
        raise SystemExit(1)
