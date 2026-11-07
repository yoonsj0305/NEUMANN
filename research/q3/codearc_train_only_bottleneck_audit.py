"""TRAIN-only diagnostic of pinned CodeARC originals; NEVER look at heldout.
Existing 84-task first cohort is DEV-EXPOSED, cannot become new blind cohort.
"""
from __future__ import annotations
import argparse
import json,hashlib
from collections import defaultdict,Counter
from pathlib import Path
from research.q3.codearc_universal_meta_external_first import parse_case,cohort
from research.q3.universal_recursive_meta_inventor import typeid,run

def truncated(v,n=250):
    s=repr(v)
    return s[:n]+("...(clipped)" if len(s)>n else "")

def run_audit(data,out):
    ids=defaultdict(dict)
    with open(data,encoding="utf8") as f:
        for line in f:
            a=json.loads(line)
            try:
                i=int(a["problem_id"]);index=int(a["index"])
                if cohort(i) and a.get("type")=="annotated" and index<7:
                    ids[i][index]=a
            except (ValueError,KeyError,TypeError):pass
    records=[]
    for i,parts in sorted(ids.items()):
        r={"id":i,"train_original_indices":list(range(7))}
        try:
            train=[parse_case(parts[j]) for j in range(7)]
            r["contract"]= [[typeid(x) for x in train[0][0]],typeid(train[0][1])]
            r["train_only"]=[{"args":truncated(args,400),
                              "output":truncated(y,400)} for args,y in train]
            r["train_y_same"]=len({repr(y) for x,y in train})==1
            r["train_y_equal_first_arg"]=all(len(x)>=1 and y==x[0] for x,y in train)
            r["train_y_equal_len_first_arg"]=all(len(x)>=1 and hasattr(x[0],"__len__") and y==len(x[0]) for x,y in train)
            r["status"]="AUDITED"
        except Exception as e:
            r["status"]="UNSUPPORTED_INPUT"
            r["reason"]=(type(e).__name__+":"+str(e))[:160]
        records.append(r)
    o={"schema":"q3.codearc.exposed-first-cohort-train-only-causal-audit.v1",
       "source_hidden_test_examples_consumed":0,
       "first_cohort_criteria":"old SHA256(id)%17 == 0",
       "rows":records,
       "stats":{"selected":len(records),
                "diagnostic_parsed":sum(r["status"]=="AUDITED" for r in records),
                "parse_failures":sum(r["status"]!="AUDITED" for r in records),
                "simple_length_or_identity":sum(r.get("train_y_equal_len_first_arg",False) or r.get("train_y_equal_first_arg",False) for r in records)}}
    Path(out).mkdir(exist_ok=False,parents=True)
    (Path(out)/"TRAIN_ONLY_AUDIT.json").write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print("Q3_TRAIN_ONLY_CAUSAL_AUDIT",json.dumps(o["stats"],sort_keys=True))
    for r in records:
        if r["status"]=="AUDITED":
            print("TASK",r["id"],"CONTRACT",r["contract"],
                  "EXAMPLES",r["train_only"][:2])
    return o

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    run_audit(a.dataset,a.out)
