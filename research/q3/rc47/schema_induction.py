"""RC47 compact, REVIEWED research abstraction/anti-unification kernel.
The complete actual experimental engine, independently frozen first outputs,
all-in cost receipts and full reproducible tests live in the RC47 conversation
ZIP. This small reference does not itself constitute model-owned creativity.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256
import json

def _canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def induce_schemata(source_discovered_traces, min_domains=2, min_variants=3):
    """Only source-derived successful trace programs are admitted.
    Each item: {"domain":string, "code":[opcode,...], "source_verified":True}.
    TARGET/GOLD program labels must NOT be supplied to this function.
    """
    groups=defaultdict(list)
    for row in source_discovered_traces:
        if row.get("source_verified") is not True:
            continue
        code=row.get("code")
        domain=row.get("domain")
        if not isinstance(code,list) or len(code)<3 or not isinstance(domain,str):
            continue
        if any(not isinstance(op,str) or not op or op=="SLOT" for op in code):
            continue
        for k,op in enumerate(code):
            key=tuple("SLOT" if i==k else t for i,t in enumerate(code))
            groups[key].append((domain,op))
    out=[]
    for candidate,observations in groups.items():
        domains=sorted({domain for domain,_ in observations})
        variants=sorted({op for _,op in observations})
        proxy_gain=(len(candidate)-1)*len(observations)-len(candidate)
        if len(domains)<min_domains or len(variants)<min_variants or proxy_gain<=0:
            continue
        out.append({
            "schema":list(candidate), "source_domains":domains,
            "source_variants":variants, "mdl_token_proxy_gain":proxy_gain,
            "sha256":sha256(_canonical(candidate).encode()).hexdigest()
        })
    return sorted(out,key=lambda x:(-x["mdl_token_proxy_gain"],x["sha256"]))

def bounded_instantiate(schema, op, allowed_primitives):
    """No arbitary generated Python execution; only named trusted primitives."""
    if not isinstance(schema,list) or schema.count("SLOT")!=1:
        raise ValueError("not a single-slot scheme")
    if op not in allowed_primitives:
        raise ValueError("unknown opcode")
    if any(token!="SLOT" and token not in allowed_primitives for token in schema):
        raise ValueError("schema outside declared ISA")
    return [op if token=="SLOT" else token for token in schema]

def source_gate(program, train_io, interpreter):
    """Source consistency is NOT a proof of unseen/task-global correctness."""
    if not train_io:
        return {"status":"UNKNOWN_NO_SOURCE"}
    try:
        for item in train_io:
            if not isinstance(item,dict) or set(item)!={"input","output"}:
                return {"status":"UNKNOWN_BAD_IO"}
            if _canonical(interpreter(program,item["input"]))!=_canonical(item["output"]):
                return {"status":"UNKNOWN_SOURCE_MISMATCH"}
    except (ValueError,TypeError,KeyError):
        return {"status":"UNKNOWN_OUTSIDE_CONTRACT"}
    return {"status":"SOURCE_FIT_ONLY","authorized_to_deploy":False}
