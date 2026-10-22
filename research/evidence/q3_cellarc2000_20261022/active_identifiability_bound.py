#!/usr/bin/env python3
"""Exact source-only active-information lower bound for fixed radius-3 ONE-STEP CA.

For any source-consistent radius3 deterministic lookup table T and any query
interior radius3 window w absent from training, T0 = T union {w:0} and
T1 = T union {w:1} are TWO explicit source-consistent models whose predictions
disagree on query cell(s) with window w. Hence exact identification of its
output is impossible from observed source alone for unrestricted binary-capable
transition maps. One new transition label per DISTINCT missing query 7-window
is information-theoretically necessary and sufficient to identify all r3-query
interior outputs in that unrestricted hypothesis class.

No original test outputs, true radius, family labels or hidden rule metadata used.
"""
import argparse,collections,hashlib,json,pathlib,time
from version_space_certifier import derive

RADIUS=3
def digest(x):
    return hashlib.sha256(json.dumps(x,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def profile(task):
    q=task["query"];length=len(q);r=RADIUS
    table=derive(task,r)
    valid=length>2*r and table is not None
    if not valid:
        short_context=any(len(e["input"])<2*r+1 or len(e["input"])!=len(e["output"]) for e in task["train"])
        reason=("UNSUPPORTED_SHORT_DEMONSTRATION_CONTEXT" if short_context else
                "INCONSISTENT_R3_DEMONSTRATION_CONSTRAINTS") if table is None else "NO_INTERIOR_INPUT"
        return {"status":reason,
                "n":length,"interior_cells":max(0,length-2*r),"known_r3":0,"missing_r3_cells":0,"missing_distinct":0,
                "maximum_new_cells_per_one_label":0,"witness":None}
    counts=collections.Counter(tuple(q[i-r:i+r+1]) for i in range(r,length-r))
    known=sum(freq for pat,freq in counts.items() if pat in table)
    missing={k:v for k,v in counts.items() if k not in table}
    # Constructive counterexample: identical source demonstrations, two separate
    # deterministic one-step CA tables with opposite outputs for a query window.
    witness=None
    if missing:
        w,freq=max(missing.items(),key=lambda z:(z[1],z[0]))
        A=dict(table);B=dict(table);A[w]=0;B[w]=1
        assert A[w]!=B[w] and all(A[k]==v and B[k]==v for k,v in table.items())
        for d in task["train"]:
            x,y=d["input"],d["output"]
            assert all(A[tuple(x[i-r:i+r+1])]==y[i] and
                       B[tuple(x[i-r:i+r+1])]==y[i] for i in range(r,len(x)-r))
        witness={"query_window_sha256":digest(w),
                 "source_rule_sha256":digest(sorted((list(k),v) for k,v in table.items())),
                 "model_A_extension_sha256":digest(sorted((list(k),v) for k,v in A.items())),
                 "model_B_extension_sha256":digest(sorted((list(k),v) for k,v in B.items())),
                 "A_prediction_at_w":0,"B_prediction_at_w":1,
                 "same_witness_query_cell_count":freq}
    return {"status":"CONSTRUCTIVE_AMBIGUITY" if missing else "ALL_R3_QUERY_INTERIOR_KNOWN",
            "n":length,"interior_cells":length-2*r,"known_r3":known,
            "missing_r3_cells":sum(missing.values()),"missing_distinct":len(missing),
            "maximum_new_cells_per_one_label":max(missing.values(),default=0),
            "witness":witness}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--masked-dir",required=True);parser.add_argument("--out",required=True)
    opts=parser.parse_args();start=time.perf_counter()
    d={"schema":"NEUMANN_CA_SOURCE_ONLY_ACTIVE_INFO_BOUND_ORIGINAL2000.v1",
       "radius":3,"generator_membership_assumed_not_proven":True,
       "requires_one_step_deterministic_local_CA":True,
       "test_solutions_seen":False,"metadata_seen":False,"splits":{},"rows":{}}
    for split in ("test_interpolation","test_extrapolation"):
        path=pathlib.Path(opts.masked_dir)/(split+".jsonl")
        lines=path.read_text().splitlines()
        assert len(lines)==1000
        rows={};cnt=collections.Counter()
        for line in lines:
            task=json.loads(line)
            assert "solution" not in task and "meta" not in task and "program" not in task
            uid=task["id"];assert uid not in rows
            r=profile(task);rows[uid]=r
            cnt["originals"]+=1;cnt[r["status"]]+=1
            if r["status"] in ("CONSTRUCTIVE_AMBIGUITY","ALL_R3_QUERY_INTERIOR_KNOWN"):
                cnt["valid_r3_interior_cells"]+=r["interior_cells"]
                cnt["source_known_cells"]+=r["known_r3"]
                cnt["provably_underdetermined_query_cells"]+=r["missing_r3_cells"]
                cnt["minimal_additional_distinct_transition_labels"]+=r["missing_distinct"]
                cnt["upper_bound_one_best_extra_label_resolved_cells"]+=r["maximum_new_cells_per_one_label"]
            if r["witness"]:cnt["certified_two_model_witness_tasks"]+=1
        d["rows"][split]=rows;d["splits"][split]=dict(cnt)
        print("SOURCE_ONLY_ORIGINAL_CA_IDENTIFIABILITY",split,json.dumps(dict(cnt),sort_keys=True),flush=True)
    d["source_only_elapsed_s"]=time.perf_counter()-start
    out=pathlib.Path(opts.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(d,separators=(",",":"),sort_keys=True)+"\n")
    print("EXACT_WITNESS_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
