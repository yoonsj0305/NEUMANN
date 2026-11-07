"""Q3 newly represented computation: bitvector DAG + observational partition.
Original FIRST must run only after source-freezing this human-authored universal
compiler. No problem ID, exact source solution, .sl or target answer used here.
This expands beyond local bit tables; NOT novel universal algorithm invention.
"""
from __future__ import annotations
import hashlib, itertools, json, pathlib, time, urllib.request

MASK=(1<<64)-1
UPSTREAM="e7ae840e5546e9243ff94afb1a29064fc050011c"
SOURCE="Barnard-PL-Labs/sygus-sgi-1"
IDS=[f"PRE_{i}_100" for i in range(30,54)]
HELDOUT_COUNT=32

def run(p,x):
    if p=="x":return x
    if type(p) is int:return p&MASK
    op=p[0]
    if op=="shr":return run(p[1],x)>>p[2]
    if op=="shl":return (run(p[1],x)<<p[2])&MASK
    if op=="not":return (~run(p[1],x))&MASK
    if op=="add":return (run(p[1],x)+run(p[2],x))&MASK
    if op=="xor":return run(p[1],x)^run(p[2],x)
    if op=="and":return run(p[1],x)&run(p[2],x)
    if op=="or":return run(p[1],x)|run(p[2],x)
    if op=="ite":return run(p[2],x) if check_guard(p[1],x) else run(p[3],x)
    raise ValueError("UNKNOWN_PROGRAM_OPCODE")

def check_guard(c,x):
    if c[0]=="bit":return bool(x&(1<<c[1]))
    if c[0]=="eq":return x==c[1]
    raise ValueError("UNKNOWN_GUARD")

def size(p):
    if p=="x" or type(p) is int:return 1
    if p[0] in ("shr","shl","not"):return 1+size(p[1])
    if p[0]=="ite":return 3+size(p[2])+size(p[3])
    return 1+size(p[1])+size(p[2])

def graph_library(xs):
    """Primitive graph grammar; no named target task or outcome-specific code."""
    base=["x",0,1]
    base += [("shr","x",n) for n in (1,4,16)]
    base += [("shl","x",1),("not","x")]
    forms=base[:]
    for sub in base:
        if sub=="x" or isinstance(sub,tuple):
            forms.extend(("add",sub,k) for k in (1,2,3,4))
            forms.extend(("xor",sub,k) for k in (1,2,3))
    for a in base:
        for b in base:
            if a==b:continue
            forms.extend((op,a,b) for op in ("and","or","xor","add"))
    # E-graph-style observational signature merging.
    memo={};results=[]
    for p in forms:
        sig=tuple(run(p,x) for x in xs)
        if sig not in memo:
            memo[sig]=p
            results.append((p,sig))
    return results

def guards(xs):
    opts=[("bit",i) for i in range(64)]+[("eq",0),("eq",1)]
    seen=set();out=[]
    for c in opts:
        sig=tuple(check_guard(c,x) for x in xs)
        if sig not in seen and any(sig) and not all(sig):
            seen.add(sig);out.append((c,sig))
    return out

def synthesize(pairs,allow_guard=True):
    start=time.perf_counter()
    if len(pairs)<5:return {"ast":None,"status":"ABSTAIN_TOO_FEW_SOURCE","candidate_checks":0}
    xs=[x for x,y in pairs]; ys=tuple(y for x,y in pairs)
    forms=graph_library(xs)
    direct=[p for p,s in forms if s==ys]
    if direct:
        best=min(direct,key=lambda p:(size(p),str(p)))
        return {"ast":best,"status":"GRAPH_EXPRESSION","candidate_checks":len(forms),
                "ms":round((time.perf_counter()-start)*1000,5)}
    if not allow_guard:
        return {"ast":None,"status":"ABSTAIN_NO_GRAPH","candidate_checks":len(forms),
                "ms":round((time.perf_counter()-start)*1000,5)}
    choices=[];checks=len(forms)
    for c,labels in guards(xs):
        pos=[i for i,v in enumerate(labels) if v]
        neg=[i for i,v in enumerate(labels) if not v]
        if not pos or not neg:continue
        fits_pos=[p for p,s in forms if all(s[i]==ys[i] for i in pos)]
        fits_neg=[p for p,s in forms if all(s[i]==ys[i] for i in neg)]
        checks += 2*len(forms)
        if not fits_pos or not fits_neg:continue
        p=min(fits_pos,key=lambda e:(size(e),str(e)))
        q=min(fits_neg,key=lambda e:(size(e),str(e)))
        node=("ite",c,p,q)
        # A small-source arm is penalized to avoid gratuitous memorization.
        score=size(node)+10/min(len(pos),len(neg))
        choices.append((score,str(node),node,[len(pos),len(neg)]))
    if choices:
        score,_,node,n=min(choices)
        return {"ast":node,"status":"SOURCE_DISCOVERED_BRANCH_GRAPH",
                "branch_sizes":n,"candidate_checks":checks,
                "ms":round((time.perf_counter()-start)*1000,5)}
    return {"ast":None,"status":"ABSTAIN_NO_SOURCE_CONSISTENT_GRAPH",
            "candidate_checks":checks,
            "ms":round((time.perf_counter()-start)*1000,5)}

def bits_to_int(v):
    if type(v) is not list or len(v)!=64 or any(type(a) is not int or a not in (0,1) for a in v):
        raise ValueError("INVALID_64BIT_VECTOR")
    z=0
    for a in v:z=(z<<1)|a
    return z

def get_original(task):
    url=(f"https://raw.githubusercontent.com/{SOURCE}/{UPSTREAM}"
         f"/data/benchmarks/hard/{task}/examples.json")
    with urllib.request.urlopen(url,timeout=25) as r:data=r.read(250000)
    if len(data)>=250000:raise ValueError("SOURCE_TOO_LARGE")
    return json.loads(data)

def source_split(data):
    if type(data) is not list:raise ValueError("NOT_ARRAY")
    seen=set();pairs=[]
    for d in data:
        if not isinstance(d,dict):raise ValueError("BAD_SOURCE_ITEM")
        a=bits_to_int(d.get("input"));b=bits_to_int(d.get("output"))
        if a in seen:continue
        seen.add(a);pairs.append((a,b))
    pairs.sort(key=lambda q:hashlib.sha256(f"{q[0]:016x}".encode()).hexdigest())
    if len(pairs)<HELDOUT_COUNT+5:raise ValueError("NOT_ENOUGH_UNIQUE_RECORDS")
    return pairs[:-HELDOUT_COUNT],pairs[-HELDOUT_COUNT:]

def heldout_score(p,heldout):
    if p is None:return {"submitted":False,"exact":False,"hits":0,"n":len(heldout)}
    good=sum(run(p,x)==y for x,y in heldout)
    return {"submitted":True,"exact":good==len(heldout),"hits":good,"n":len(heldout)}

def evaluate_cohort():
    start=time.perf_counter();rows=[]
    for ident in IDS:
        rr={"id":ident}
        try:
            data=get_original(ident)
            train,test=source_split(data)
            rr["source_sha256"]=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            rr["published_n"]=len(data);rr["source_n"]=len(train);rr["heldout_n"]=len(test)
            for tag,flag in (("cold_graph",False),("guard_expansion",True)):
                found=synthesize(train,allow_guard=flag)
                rr[tag]={"synthesis":found,"heldout":heldout_score(found["ast"],test)}
        except Exception as e:
            rr["error"]=type(e).__name__+": "+str(e)[:140]
        rows.append(rr)
    out={"schema":"neumann.q3.executable-conditional-bv-graph-original-first.v1",
         "upstream_commit":UPSTREAM,"cohort":IDS,"rows":rows,
         "heldout_per_original":HELDOUT_COUNT,
         "summary":{tag:{
            "full_exact":sum(int(r.get(tag,{}).get("heldout",{}).get("exact",False)) for r in rows),
            "submitted":sum(int(r.get(tag,{}).get("heldout",{}).get("submitted",False)) for r in rows),
            "candidate_checks":sum(r.get(tag,{}).get("synthesis",{}).get("candidate_checks",0) for r in rows),
            "heldout_hits":sum(r.get(tag,{}).get("heldout",{}).get("hits",0) for r in rows)}
            for tag in ("cold_graph","guard_expansion")},
         "source_errors":sum(int("error" in r) for r in rows),
         "wall_seconds":round(time.perf_counter()-start,3)}
    pathlib.Path("Q3_CONDITIONAL_GRAPH_EXTERNAL_FIRST.json").write_text(json.dumps(out,indent=2))
    print(json.dumps({"task_count":len(IDS),"summary":out["summary"],
                      "source_errors":out["source_errors"],"wall_seconds":out["wall_seconds"]},indent=2))
    return out

if __name__=="__main__":evaluate_cohort()
