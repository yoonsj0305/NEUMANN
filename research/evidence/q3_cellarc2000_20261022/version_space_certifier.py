#!/usr/bin/env python3
"""Q3 conditional exact version-space certificates on original CellARC query interiors.

No hidden metadata, query solutions or true-radius information during inference.
For MAX_R in {1,2,3}, enumerate ALL source-consistent deterministic one-step,
cyclic CA radius hypotheses 1..MAX_R. A query cell is CERTIFIED iff EVERY
source-consistent hypothesis has an observed complete neighborhood there and
ALL predict the same value. Any otherwise possible transition is UNKNOWN.

Soundness theorem (conditional): if actual process is a deterministic synchronous
ONE-STEP CA on the queried state, with true radius <=MAX_R and uniform local map
across all source examples, then all CERTIFIED query positions are correct.
No guarantee if the real system is multi-step or process assumptions wrong.
"""
import argparse,collections,hashlib,json,pathlib,time
RADII=(1,2,3)
def derive(task,r):
    table={}
    for pair in task["train"]:
        x,y=pair["input"],pair["output"]
        if len(x)!=len(y) or len(x)<2*r+1:return None
        for i in range(r,len(x)-r):
            k=tuple(x[i-r:i+r+1]);v=y[i]
            if k in table and table[k]!=v:return None
            table[k]=v
    return table if table else None
def infer(task):
    query=task["query"];m=len(query)
    if not query or any(not isinstance(v,int) for v in query):
        return {"status":"UNSUPPORTED","variants":{}}
    tables={r:derive(task,r) for r in RADII}
    result={}
    for R in RADII:
        candidates=[(r,tables[r]) for r in RADII if r<=R and tables[r] is not None]
        out=[None]*m;witness={}
        for i in range(R,m-R):
            vals=[];valid=True
            for r,table in candidates:
                k=tuple(query[i-r:i+r+1])
                if k not in table:
                    valid=False;break
                vals.append(table[k])
            if valid and vals and len(set(vals))==1:
                out[i]=vals[0]
                witness[str(i)]={"value":vals[0],"supporting_radii":[r for r,_ in candidates],
                                 "n_hypotheses":len(candidates)}
        result[str(R)]={"status":"CONDITIONAL_ONE_STEP_CERTIFICATE" if candidates else "ABSTAIN_NO_CONSISTENT_CLASS",
                        "radius_bound":R,"source_consistent_radii":[r for r,_ in candidates],
                        "total_query_cells":m,"certified_cells":sum(v is not None for v in out),
                        "outputs":out,"witness":witness}
    return {"status":"SOURCE_ONLY_DONE","variants":result}

def truthless_evaluate(datafile):
    samples={}
    for text in pathlib.Path(datafile).read_text().splitlines():
        task=json.loads(text);assert set(task).issuperset({"id","train","query"})
        assert "solution" not in task and "meta" not in task and "program" not in task
        assert task["id"] not in samples
        samples[task["id"]]=infer(task)
    assert len(samples)==1000
    return samples

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("infer","grade"),required=True)
    p.add_argument("--masked-dir");p.add_argument("--original-dir");p.add_argument("--sealed");p.add_argument("--out",required=True)
    args=p.parse_args();start=time.perf_counter()
    if args.mode=="infer":
        splits={};stats={}
        for name in ("test_interpolation","test_extrapolation"):
            items=truthless_evaluate(pathlib.Path(args.masked_dir)/(name+".jsonl"))
            splits[name]=items
            total={str(r):{"certified_cells":sum(z["variants"][str(r)]["certified_cells"] for z in items.values()),
                           "tasks_with_certificates":sum(z["variants"][str(r)]["certified_cells"]>0 for z in items.values()),
                           "total_query_cells":sum(z["variants"][str(r)]["total_query_cells"] for z in items.values())} for r in RADII}
            stats[name]=total;print("SOURCE_ONLY_VERSION_SPACE",name,json.dumps(total,sort_keys=True),flush=True)
        report={"schema":"NEUMANN_CA_VERSION_SPACE_CONDITIONAL_CERTIFICATE.v1",
                "n":2000,"masked_query_solutions_not_accessed":True,"metadata_not_accessed":True,
                "conditional_assumption":"true one-step deterministic CA radius<=R, uniform across source/query and correct interiors",
                "inference_wall_s":time.perf_counter()-start,"summary":stats,"rows":splits}
    else:
        before=pathlib.Path(args.sealed);pre=json.loads(before.read_text())
        assert pre["n"]==2000 and pre["masked_query_solutions_not_accessed"] and pre["metadata_not_accessed"]
        totals={}; per_task={}
        for name in ("test_interpolation","test_extrapolation"):
            counts={str(r):collections.Counter() for r in RADII}
            groups={}
            for line in (pathlib.Path(args.original_dir)/(name+".jsonl")).read_text().splitlines():
                task=json.loads(line);y=task["solution"];uid=task["id"]
                x=pre["rows"][name][uid];v={}
                for r in RADII:
                    out=x["variants"][str(r)]["outputs"]
                    assert len(out)==len(y)
                    hits=sum(o is not None for o in out)
                    correct=sum(o==y[i] for i,o in enumerate(out) if o is not None)
                    count=counts[str(r)]
                    count["source_task_n"]+=1
                    count["query_cells_total"]+=len(y)
                    count["certified_cells"]+=hits
                    count["verified_correct_cells"]+=correct
                    count["incorrect_cells"]+=hits-correct
                    count["tasks_with_any_certified"]+=int(hits>0)
                    count["tasks_all_emitted_correct"]+=int(hits>0 and hits==correct)
                    count["fully_certified_exact_tasks"]+=int(hits==len(y) and out==y)
                    v[str(r)]={"reported_cells":hits,"correct":correct,"wrong":hits-correct}
                groups[uid]=v
            assert len(groups)==1000
            per_task[name]=groups;totals[name]={k:dict(c) for k,c in counts.items()}
            print("INDEPENDENT_VERSION_SPACE_CELLARC",name,json.dumps(totals[name],sort_keys=True),flush=True)
        report={"schema":"NEUMANN_CA_VERSION_SPACE_2000_INDEPENDENT_ORIGINAL_TRUTH.v1",
                "n":2000,"original_source_only_receipt_sha256":hashlib.sha256(before.read_bytes()).hexdigest(),
                "condition_not_independently_established":True,
                "no_neural_primitive_creation":True,"global_Q3_Q4":"OPEN",
                "per_split":totals,"per_task":per_task}
    out=pathlib.Path(args.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(report,separators=(",",":"),sort_keys=True)+"\n")
    print("VERSION_SPACE_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
