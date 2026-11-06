"""Read-only, independent RC41 FIRST audit from immutable saved JSON.

Re-download pinned external DOT at an exact Git commit and Git blob SHA, parse
with an independent parser, then verify compiled source AST using a raw-state
product BFS, without importing/rerunning the active learner or W-method.
"""
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path
from urllib.request import Request,urlopen

FIRST_SHA="87adfee0cd1dc19b4cff1f364d9db71a2c6a9dd6ed623af3cdcdc645a6b78690"
COMMIT="24b5535f37ca92745ddb4c3a5a5381b6ccfa87ce"
MODEL_SHAS={
 "mosquitto":"c6a9116200542ff55acca8f8d02b8bb6ef9ce486",
 "activemq":"cf6b8db0a25b7c56497f77234e4304f13a06da77",
 "hbmqtt":"4d339c12c75921ba7786dc54dfd2bdebd9f37691"}
MODEL_PATHS={
 "mosquitto":"eval/src/main/resources/mqtt/mosquitto/mosquitto.dot",
 "activemq":"eval/src/main/resources/mqtt/ActiveMQ/simple.dot",
 "hbmqtt":"eval/src/main/resources/mqtt/hbmqtt/simple.dot"}
# Intentionally not importing the production parser, learner, or W method.
EDGE=re.compile(r'^\s*(s[0-9]+)\s*->\s*(s[0-9]+)\s*\[label="(.+)"\];\s*$')


def independent_reference(case):
    url="https://raw.githubusercontent.com/mtappler/mut-learn/"+COMMIT+"/"+MODEL_PATHS[case]
    req=Request(url,headers={"User-Agent":"NEUMANN-RC41-readonly-audit"})
    with urlopen(req,timeout=25) as h:
        data=h.read(128000)
    sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if sha!=MODEL_SHAS[case]:
        raise ValueError("EXTERNAL_SOURCE_SHA_CHANGED")
    entries=[]
    initial=None
    for line in data.decode().splitlines():
        if "->" not in line:
            continue
        if "__start0" in line:
            m=re.fullmatch(r'\s*__start0\s*->\s*(s\d+);\s*',line)
            if not m or initial is not None:
                raise ValueError("INVALID_INITIAL")
            initial=m.group(1)
            continue
        match=EDGE.fullmatch(line)
        if not match:
            raise ValueError("UNKNOWN_EDGE")
        src,dst,label=match.groups()
        if " / " not in label:
            raise ValueError("INVALID_LABEL")
        inp,out=label.split(" / ",1)
        entries.append((src,dst,inp,out))
    states=sorted({row[0] for row in entries}|{row[1] for row in entries})
    alphabet=sorted({row[2] for row in entries})
    outputs=sorted({row[3] for row in entries})
    ids={s:i for i,s in enumerate(states)}
    in_code={s:chr(65+i) for i,s in enumerate(alphabet)}
    out_code={s:str(i) for i,s in enumerate(outputs)}
    table={}
    for src,dst,inp,out in entries:
        key=(ids[src],in_code[inp])
        if key in table:
            raise ValueError("DUPLICATE_EDGE")
        table[key]=(ids[dst],out_code[out])
    if initial not in ids or len(table)!=len(states)*len(alphabet):
        raise ValueError("REFERENCE_NOT_COMPLETE")
    return (ids[initial],"".join(in_code.values()),table)


def raw_product(source, reference):
    initial,alphabet,table=reference
    if not isinstance(source,dict) or source.get("schema")!="neumann.rc39.mealy-ast.v1":
        return False
    if source.get("alphabet")!=list(alphabet):
        return False
    n=source.get("states")
    transition=source.get("transitions")
    emission=source.get("emissions")
    start=source.get("initial")
    if type(n) is not int or n<1 or type(start) is not int or not 0<=start<n:
        return False
    if not isinstance(transition,list) or not isinstance(emission,list) or len(transition)!=n or len(emission)!=n:
        return False
    todo=deque([(initial,start)])
    visited=set(todo)
    while todo:
        r,c=todo.popleft()
        if len(transition[c])!=len(alphabet) or len(emission[c])!=len(alphabet):
            return False
        for i,a in enumerate(alphabet):
            to,o=table[(r,a)]
            if emission[c][i]!=o:
                return False
            cto=transition[c][i]
            if type(cto) is not int or not 0<=cto<n:
                return False
            pair=(to,cto)
            if pair not in visited:
                visited.add(pair)
                todo.append(pair)
    return True


def audit(path):
    data=Path(path).read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    errors=[]
    if digest!=FIRST_SHA:
        errors.append("PINNED_FIRST_SHA_DRIFT")
    first=json.loads(data)
    rows=first.get("rows",[])
    if {row["source_case"] for row in rows}!=set(MODEL_SHAS) or len(rows)!=3:
        errors.append("ORIGINAL_CASES_CHANGED")
    exact=0; mutants=0; queries=0
    for row in rows:
        case=row["source_case"]
        reference=independent_reference(case)
        ast=row["compiled_ast"]
        good=raw_product(ast,reference)
        exact+=int(good)
        if not good or not row["complete_source_only_w_certificate"]:
            errors.append("BAD_PROGRAM_OR_CERTIFICATE_"+case)
        altered=json.loads(json.dumps(ast))
        state=altered["initial"];initial_out=altered["emissions"][state][0]
        alternate=next((str(i) for i in range(8) if str(i)!=initial_out),None)
        altered["emissions"][state][0]=alternate
        if not raw_product(altered,reference):
            mutants+=1
        else:
            errors.append("MUTATION_NOT_REJECTED_"+case)
        queries+=row["unique_source_queries"]
        if row["source_git_blob"]!=MODEL_SHAS[case] or not row["negative_mutation_rejected"]:
            errors.append("PROVENANCE_OR_NEGATIVE_DRIFT_"+case)
    if queries!=609 or first["total_unique_source_queries"]!=609:
        errors.append("ORIGINAL_QUERY_METRIC_DRIFT")
    if exact!=3 or mutants!=3:
        errors.append("INDEPENDENT_EXACT_OR_MUTATION_FAIL")
    if first["science_status"]!="SCOPED_EXTERNAL_MQTT_FIRST_PASS":
        errors.append("SCIENCE_STATUS_REWRITTEN")
    if first["Q6_cross_formalism_semantic_transfer"]!="NOT_PROVEN":
        errors.append("Q6_OVERCLAIM")
    return {
        "schema":"neumann.q3.rc41.independent-first-audit.v1",
        "audit_pass":not errors,
        "errors":errors,
        "pinned_first_sha256":digest,
        "original_external_models":len(rows),
        "independent_all_length_proven":exact,
        "mutations_rejected":mutants,
        "total_unique_query_count":queries,
        "used_learner_or_w_method":False,
        "external_semantic_transfer":"OPEN"
    }


if __name__=="__main__":
    result=audit(sys.argv[1])
    print(json.dumps(result,indent=2))
    if not result["audit_pass"]:
        raise SystemExit(1)
