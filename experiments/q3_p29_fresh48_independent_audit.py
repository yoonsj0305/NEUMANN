"""NEUMANN P2.9: independent Python source-bound FIRST ARC48 audit.

No P29 JS synthesis replay; no training or extra model calls. Audit ORIGINAL
unchanged first result, source/filename locks, 48 source SHA256, and execute
every submitted AST with separate Python implementation. Read original TEST
gold only after standalone Python original TRAIN replay.
"""
from __future__ import annotations
from hashlib import sha1,sha256
from pathlib import Path
import json,re,sys

FIRST_SHA256="f20af6575a6479f36352ab95df8883aa4d17e366c3de355735c96c4d4bd37ed8"
UPSTREAM="399030444e0ab0cc8b4e199870fb20b863846f34"
def blob(path):
    b=Path(path).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def original_grid(g):
    return (type(g) is list and 1<=len(g)<=30 and
      type(g[0]) is list and 1<=len(g[0])<=30 and
      all(type(row) is list and len(row)==len(g[0]) and
      all(type(v) is int and 0<=v<=9 for v in row) for row in g))
def dim(code,h,w):
    d={"h":h,"w":w,"h*w":h*w,"h*h":h*h,"w*w":w*w,"h+1":h+1,"w+1":w+1}
    for k in range(2,6):
        d[f"{k}*h"]=k*h
        d[f"{k}*w"]=k*w
    if code not in d:raise ValueError("UNKNOWN_DIMENSION_EXPR:"+str(code))
    return d[code]
def coord(expr,r,c,h,w,H,W,axis):
    parts=expr.split(":")
    if len(parts) not in (2,3) or parts[0] not in ("r","c") or parts[1] not in ("raw","mod","block","stretch"):
        raise ValueError("UNSUPPORTED_COORD_EXPR")
    if len(parts)==3 and parts[2]!="reverse":raise ValueError("COORD_REVERSE_DRIFT")
    n=h if axis=="row" else w
    q=r if parts[0]=="r" else c
    L=H if parts[0]=="r" else W
    kind=parts[1]
    if kind=="raw":v=q
    elif kind=="mod":v=q%n
    elif kind=="block":v=q//n
    else:
        if L%n!=0:return None
        v=q//(L//n)
    if len(parts)==3:v=n-1-v
    return v if 0<=v<n else None
def project(view,g,H,W):
    if type(view) is not dict or set(view)!={"row","col"}:raise ValueError("BAD_VIEW")
    h,w=len(g),len(g[0])
    out=[]
    for r in range(H):
        line=[]
        for c in range(W):
            yy=coord(view["row"],r,c,h,w,H,W,"row")
            xx=coord(view["col"],r,c,h,w,H,W,"col")
            if yy is None or xx is None:return None
            line.append(g[yy][xx])
        out.append(line)
    return out
def execute(ast,g):
    if not original_grid(g) or type(ast) is not dict or "kind" not in ast or "outputShape" not in ast:return None
    shape=ast["outputShape"]
    if type(shape) is not list or len(shape)!=2:return None
    h,w=len(g),len(g[0])
    H,W=dim(shape[0],h,w),dim(shape[1],h,w)
    if H<1 or W<1 or H>30 or W>30:return None
    kind=ast["kind"]
    if kind=="coordinate-unary-palette":
        if set(ast)!={"kind","outputShape","view","palette"}:raise ValueError("UNKNOWN_UNARY_AST_FIELDS")
        v=project(ast["view"],g,H,W)
        if v is None:return None
        palette=ast["palette"]
        if type(palette) is not list or any(type(x) is not list or len(x)!=2 or
              any(type(t) is not int or not 0<=t<=9 for t in x) for x in palette):raise ValueError("BAD_PALETTE")
        mapping=dict(palette)
        if len(mapping)!=len(palette):raise ValueError("DUPLICATE_PALETTE")
        if any(c not in mapping for row in v for c in row):return None
        return [[mapping[c] for c in row] for row in v]
    if kind=="coordinate-two-view-zero-mask":
        if set(ast)!={"kind","outputShape","outer","inner","selector"}:raise ValueError("UNKNOWN_BINARY_AST_FIELDS")
        x=project(ast["outer"],g,H,W)
        y=project(ast["inner"],g,H,W)
        if x is None or y is None:return None
        s=ast["selector"]
        if type(s) is not list or len(s)!=4 or any(c not in ("zero","outer","inner") for c in s):
            raise ValueError("BAD_SELECTOR")
        out=[]
        for i in range(H):
            line=[]
            for j in range(W):
                a,b=x[i][j],y[i][j]
                rule=s[(2 if a==0 else 0)+(1 if b==0 else 0)]
                line.append(0 if rule=="zero" else a if rule=="outer" else b)
            out.append(line)
        return out
    raise ValueError("UNKNOWN_AST_CLASS")
def fnv(s):
    h=2166136261
    for c in s:h=((h^ord(c))*16777619)&0xffffffff
    return h
def audit(root,arc,firstfile):
    root,arc=Path(root),Path(arc)
    b=Path(firstfile).read_bytes()
    receipt=json.loads(b)
    mpath=root/"docs/experiments/q3_p29_FIRST_FRESH_ORIGINAL48_COHORT.json"
    m=json.loads(mpath.read_text())
    lock=json.loads((root/"docs/experiments/q3_p29_FIRST_FRESH_ORIGINAL48_SOURCE_LOCK.json").read_text())
    errors=[]
    def check(v,msg):
        if not v:errors.append(msg)
    check(sha256(b).hexdigest()==FIRST_SHA256,"FIRST_RECEIPT_SHA256_DRIFT")
    check(blob(mpath)==lock["manifest_blob"],"MANIFEST_BLOB_DRIFT")
    for name,expected in lock["source_blobs"].items():
        check(blob(root/name)==expected,"CODE_BLOB_DRIFT:"+name)
    excluded=set()
    for x in m["prior_registration_manifests"]:
        p=root/x["path"]
        check(blob(p)==x["blob"],"PREVIOUS_MANIFEST_DRIFT:"+x["path"])
        d=json.loads(p.read_text())
        check(len(d["ids"])==x["n"],"PRIOR_MANIFEST_LENGTH_DRIFT")
        excluded.update(d["ids"])
    check(len(excluded)==280,"PREVIOUSLY_OPENED_DRIFT")
    files=sorted(p.name for p in (arc/"data/evaluation").glob("*.json"))
    check(len(files)==400,"UPSTREAM_TASK_CENSUS_DRIFT")
    unseen=[x for x in files if x not in excluded]
    chosen=sorted(unseen,key=lambda x:(fnv(m["salt"]+x),x))[:48]
    check(chosen==m["ids"],"FROZEN_FILENAME_RESELECTION_DRIFT")
    check(len(receipt["rows"])==48,"NOT_48_RECEIPTS")
    correct,submitted,wrong,trainfit,shapeFound=0,0,0,0,0
    correct_ids=[]
    source_replays=[]
    for name,row in zip(m["ids"],receipt["rows"]):
        id=name.removesuffix(".json")
        check(row["id"]==id,"ORDER_OR_ID_DRIFT:"+id)
        data=(arc/"data/evaluation"/name).read_bytes()
        check(sha256(data).hexdigest()==row["original_json_sha256"],"ORIGINAL_TASK_SHA_DRIFT:"+id)
        task=json.loads(data)
        trace=row["trace"]
        ast=trace["ast"]
        check((ast is not None)==row["p29_submitted"],"AST_SUBMISSION_DRIFT:"+id)
        if trace["shapePrograms"]>0:shapeFound+=1
        if ast is None:
            check(not row["p29_correct"] and not row["p29_wrong"],"FALSE_UNSUBMITTED_CORRECTNESS:"+id)
            continue
        trainfit+=1
        train_ok=all(execute(ast,p["input"])==p["output"] for p in task["train"])
        check(train_ok,"INDEPENDENT_TRAIN_EXECUTION_MISMATCH:"+id)
        # First original TEST target accesses in independent auditor happen here.
        predictions=[execute(ast,p["input"]) for p in task["test"]]
        gold=[p["output"] for p in task["test"]]
        hit=predictions==gold
        check(all(p is not None for p in predictions),"INDEPENDENT_EXECUTION_NULL:"+id)
        check(hit==row["p29_correct"],"INDEPENDENT_ORIGINAL_TEST_CHECKER_DRIFT:"+id)
        check((not hit)==row["p29_wrong"],"ORIGINAL_WRONG_FLAG_DRIFT:"+id)
        submitted+=1
        if hit:correct+=1;correct_ids.append(id)
        else:wrong+=1
        source_replays.append({"id":id,"train_all_replayed":train_ok,"original_test_exact":hit,"ast":ast})
    first=receipt["counts"]
    check(first["P29_original_exact"]==correct,"FIRST_MODEL_EXACT_COUNT_DRIFT")
    check(first["P29_original_submitted"]==submitted,"FIRST_MODEL_SUBMIT_DRIFT")
    check(first["P29_wrong_submitted"]==wrong,"FIRST_MODEL_WRONG_COUNT_DRIFT")
    check(first["P29_train_consistent_programs"]==trainfit,"FIRST_TRAINFIT_DRIFT")
    check(first["P29_supported_shape_rules"]==shapeFound,"FIRST_SHAPE_COUNT_DRIFT")
    check(first["n"]==48,"FIRST_N_DRIFT")
    check(first["additional_safe_exact"]==1 and first["previous_union_exact"]==1 and
          first["fully_safe_combined_exact"]==2 and first["fully_safe_combined_wrong"]==0,
          "FIRST_OLD_CLASSICAL_FLAG_DRIFT")
    check(receipt["science_status"]=="P29_FIRST_FRESH_TRANSFER_FAIL_OR_UNSAFE","FALSE_SCIENTIFIC_PROMOTION")
    return {"schema":"neumann.q3.p29.fresh48-independent-original-source-audit.v1",
        "first_receipt_sha256":sha256(b).hexdigest(),
        "auditor_pass":len(errors)==0,"errors":errors,
        "original_source_census":400,"unopened_after_first":72,
        "new_eval_items":48,"shape_rules_found":shapeFound,
        "independently_replayed_programs":submitted,"independent_original_correct":correct,
        "independent_original_wrong":wrong,"correct_ids":correct_ids,
        "strong_classical_baselines_independently_reimplemented":False,
        "old_consensus_correct_from_sha_locked_first_receipt":first["previous_union_exact"],
        "independent_source_interpreter":"Python (different language from original Node implementation)",
        "original_gold_used_only_after_predicted_programs":True,
        "scientific_status":"P29_FIRST_FRESH_TRANSFER_FAIL_OR_UNSAFE",
        "q3":"OPEN","q6":"OPEN","q7":"OPEN",
        "source_replays":source_replays}
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: python experiments/q3_p29_fresh48_independent_audit.py repo arc first.json")
    result=audit(*sys.argv[1:])
    print(json.dumps(result,sort_keys=True,indent=2))
    if not result["auditor_pass"]:raise SystemExit(1)
