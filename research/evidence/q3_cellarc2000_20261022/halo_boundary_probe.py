#!/usr/bin/env python3
"""Physically correct partial-ring training halos for independently sourced CellARC.
Source-only all 2000: baseline unchanged, proposed one-step model and held-demo CV.
Rule grammar is classical/predefined; no neural invention or universal correctness certificate.
"""
import argparse,collections,hashlib,json,pathlib,time
from exact_local_rule_probe import attempt as legacy_attempt, feature, win, KINDS

RADII=(1,2,3)
def fit(pairs,r,kind):
    table={}
    for pair in pairs:
        a=pair["input"];b=pair["output"]
        if len(a)!=len(b) or len(a)<2*r+1:return None
        # Segments have r halo cells from a larger de Bruijn ring. Only the
        # interior is supported by actual input context; do not wrap the segment.
        for i in range(r,len(a)-r):
            key=feature(tuple(a[i-r:i+r+1]),kind)
            value=b[i]
            if key in table and table[key]!=value:return None
            table[key]=value
    return table if table else None

def proposed(d):
    t0=time.perf_counter()
    pairs=d["train"];query=d["query"]
    if len(pairs)!=5 or not query:return {"status":"UNSUPPORTED","prediction":None}
    models=[];tallies=collections.Counter()
    for r in RADII:
        for kind in KINDS:
            table=fit(pairs,r,kind)
            if table is None:
                tallies["inconsistent_or_empty"]+=1;continue
            keys=[feature(win(query,i,r),kind) for i in range(len(query))]
            if any(k not in table for k in keys):
                tallies["unknown_query_window"]+=1;continue
            prediction=[table[k] for k in keys]
            # Whole-source-demonstration cross-validation, never use test targets.
            seen=0;mismatch=0
            for k,pair in enumerate(pairs):
                excluding=fit(pairs[:k]+pairs[k+1:],r,kind)
                if not excluding:continue
                x=pair["input"];y=pair["output"]
                for i in range(r,len(x)-r):
                    key=feature(tuple(x[i-r:i+r+1]),kind)
                    if key in excluding:
                        seen+=1;mismatch+=int(excluding[key]!=y[i])
            models.append({"radius":r,"kind":kind,"prediction":prediction,
                           "source_loo_known":seen,"source_loo_wrong":mismatch,
                           "source_distinct_keys":len(table)})
    if not models:
        return {"status":"ABSTAIN_NO_SOURCE_COVERAGE","prediction":None,
                "stats":dict(tallies),"s":time.perf_counter()-t0}
    def consensus(candidates,label):
        if not candidates:return {"status":"ABSTAIN_NO_CV_ELIGIBLE" if label=="cv" else "ABSTAIN_NO_SOURCE_COVERAGE","prediction":None}
        classes=collections.defaultdict(list)
        for c in candidates:classes[tuple(c["prediction"])].append(c)
        if len(classes)!=1:
            return {"status":"ABSTAIN_HYPOTHESES_DISAGREE","prediction":None,
                    "n_hypotheses":len(candidates),"distinct_predictions":len(classes)}
        best=min(candidates,key=lambda c:(KINDS.index(c["kind"]),c["radius"]))
        return {"status":"SOURCE_CONSENSUS","prediction":best["prediction"],"n_hypotheses":len(candidates),
                "radius":best["radius"],"kind":best["kind"],
                "source_loo_known":best["source_loo_known"],
                "source_loo_wrong":best["source_loo_wrong"]}
    raw=consensus(models,"raw")
    # Additional source-only correctness gate: independent source-demo fold
    # coverage at least one previously seen pattern, all observed exact.
    cv=consensus([m for m in models if m["source_loo_known"]>0 and m["source_loo_wrong"]==0],"cv")
    return {"status":raw["status"],"prediction":raw["prediction"],
            "raw":raw,"cv":cv,"candidate_count":len(models),"stats":dict(tallies),
            "s":time.perf_counter()-t0}

def evaluate(path,legacy=False):
    task=json.loads(path)
    assert "solution" not in task and "meta" not in task and "program" not in task
    if legacy:return legacy_attempt(task)
    return proposed(task)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["infer","grade"],required=True)
    p.add_argument("--masked-dir");p.add_argument("--original-dir");p.add_argument("--sealed");p.add_argument("--out",required=True)
    a=p.parse_args()
    if a.mode=="infer":
        rows={};summary={}
        for name in ("test_interpolation","test_extrapolation"):
            entries={};ct=collections.Counter();start=time.perf_counter()
            file=pathlib.Path(a.masked_dir)/(name+".jsonl")
            for line in file.read_text().splitlines():
                task=json.loads(line)
                assert "solution" not in task and "meta" not in task and "program" not in task
                key=task["id"]
                assert key not in entries
                prev=legacy_attempt(task)
                next=proposed(task)
                entries[key]={"legacy":prev,"halo":next}
                ct["legacy_attempted"]+=int(prev.get("prediction") is not None)
                ct["halo_attempted"]+=int(next.get("prediction") is not None)
                ct["halo_cv_attempted"]+=int(next.get("cv",{}).get("prediction") is not None)
            assert len(entries)==1000
            rows[name]=entries;summary[name]={"n":1000,"counts":dict(ct),"elapsed_s":time.perf_counter()-start}
            print("HALO_FIRST_SOURCE_ONLY",name,json.dumps(summary[name],sort_keys=True),flush=True)
        result={"schema":"NEUMANN_CELLARC_SOURCE_HALO_FIRST_FROZEN.v1","n":2000,
                "sees_original_truth":False,"sees_metadata":False,"hypothesis":"t=1 partial-ring interior source, periodic query",
                "summary":summary,"rows":rows}
    else:
        prior=pathlib.Path(a.sealed)
        pre=json.loads(prior.read_text());assert pre["n"]==2000 and not pre["sees_original_truth"]
        scores={};details={}
        for name in ("test_interpolation","test_extrapolation"):
            ct=collections.Counter();record={}
            for line in (pathlib.Path(a.original_dir)/(name+".jsonl")).read_text().splitlines():
                d=json.loads(line);r=pre["rows"][name][d["id"]];truth=d["solution"]
                row={}
                for model,entry in (("legacy",r["legacy"]),("halo",r["halo"]),("halo_cv",r["halo"].get("cv",{}))):
                    prediction=entry.get("prediction")
                    eligible=prediction is not None
                    exact=bool(eligible and prediction==truth)
                    row[model]={"attempted":eligible,"correct":exact}
                    ct[model+"_attempted"]+=int(eligible)
                    ct[model+"_correct"]+=int(exact)
                    ct[model+"_wrong"]+=int(eligible and not exact)
                ct["halo_new_unique_correct"]+=int(row["halo"]["correct"] and not row["legacy"]["correct"])
                ct["cv_new_unique_correct"]+=int(row["halo_cv"]["correct"] and not row["legacy"]["correct"])
                record[d["id"]]=row
            assert len(record)==1000
            details[name]=record;scores[name]={"n":1000,"counts":dict(ct)}
            print("HALO_INDEPENDENT_SOURCE_EXACT",name,json.dumps(scores[name],sort_keys=True),flush=True)
        result={"schema":"NEUMANN_CELLARC2000_CORRECTED_HALO_INDEPENDENT_GRADE.v1",
                "n":2000,"source_only_sha256":hashlib.sha256(prior.read_bytes()).hexdigest(),
                "scores":scores,"rows":details,"global_Q3_new_learner":"OPEN","global_Q4_allcost10x":"OPEN",
                "decision_note":"no metadata fed into source solver; one-step hypothesis unproven by source evidence alone"}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("HALO_FULL_ORIGINAL_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
