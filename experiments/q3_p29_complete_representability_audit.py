"""P2.9 source-independent COMPLETE representability certificate.

Goal: determine whether *any* P2.9 typed coordinate program can fit each
TRAIN set of the already-opened first 48 public original evaluation tasks.
This is NOT fresh accuracy and NOT new problem-solving. It never reads TEST
oracle outputs. The original P29 first receipt and executable source are
validated by SHA-256/Git blob. Exhaustive coordinate enumeration differs from
the runtime's MAX_VIEWS=100 / MAX_GEOMETRY_PAIRS=10000 pruning.

A zero-fit proof is complete for the 2-view zero-mask plus unary per-color
mapping grammar, conditioned on the source-defined 36-shape limit and exactly
the 16x16 typed coordinate selector terms. It does not prove impossibility
for arbitrary future representations or different output shape semantics.
"""
from __future__ import annotations
from hashlib import sha1,sha256
from pathlib import Path
from collections import Counter
import json
import sys
import time

FIRST_RECEIPT_SHA256="aa3a0813e9ba4714875f6c3f4d78ed2c7614f51c417a661cf0a454cecf7d5308"
P29_SOURCE_GIT_BLOB="ca6f76504be5cf2fc00709b6479f0e8436c6fa18"

def git_blob(p):
    b=Path(p).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def dimensions(axis):
    n="h" if axis=="row" else "w"
    other="w" if axis=="row" else "h"
    ops=[
      (n,0,lambda h,w:(h if axis=="row" else w)),
      (other,4,lambda h,w:(w if axis=="row" else h)),
      ("h*w",6,lambda h,w:h*w),
      ("h*h",7,lambda h,w:h*h),
      ("w*w",7,lambda h,w:w*w),
    ]
    for k in range(2,6):
        ops.append((str(k)+"*"+n,3+k,lambda h,w,k=k:k*(h if axis=="row" else w)))
        ops.append((str(k)+"*"+other,7+k,lambda h,w,k=k:k*(w if axis=="row" else h)))
    ops.append((n+"+1",9,lambda h,w:(h if axis=="row" else w)+1))
    return ops

def shape_candidates(train,tests):
    R=dimensions("row")
    C=dimensions("col")
    arr=[]
    for nameR,costR,opR in R:
        for nameC,costC,opC in C:
            if not all(opR(len(t["input"]),len(t["input"][0]))==len(t["output"]) and
                       opC(len(t["input"]),len(t["input"][0]))==len(t["output"][0]) for t in train):
                continue
            target=[(opR(len(x),len(x[0])),opC(len(x),len(x[0]))) for x in tests]
            if any(h<1 or h>30 or w<1 or w>30 for h,w in target):
                continue
            arr.append((costR+costC,nameR,nameC,target))
    arr.sort(key=lambda x:(x[0],x[1],x[2]))
    return arr[:36]

def coordinate_terms():
    # Cartesian product: source-coordinate axis r/c, sampling kind and reverse flag.
    return [(axis,kind,rev)
        for axis in ("r","c")
        for kind in ("raw","mod","block","stretch")
        for rev in (False,True)]

def index(term,r,c,h,w,H,W,axis):
    name,kind,reverse=term
    n=h if axis=="row" else w
    q=r if name=="r" else c
    L=H if name=="r" else W
    if kind=="raw":out=q
    elif kind=="mod":out=q%n
    elif kind=="block":out=q//n
    else:
        if L%n: return None
        out=q//(L//n)
    if reverse:out=n-1-out
    return out if 0<=out<n else None

def generate_views(inputs,shapes):
    rs=coordinate_terms()
    cs=coordinate_terms()
    unique={}
    for row_term in rs:
        for col_term in cs:
            values=[]
            valid=True
            for x,(H,W) in zip(inputs,shapes):
                h,w=len(x),len(x[0])
                out=[]
                for r in range(H):
                    for c in range(W):
                        rr=index(row_term,r,c,h,w,H,W,"row")
                        cc=index(col_term,r,c,h,w,H,W,"col")
                        if rr is None or cc is None:valid=False;break
                        out.append(x[rr][cc])
                    if not valid:break
                if not valid:break
                values.extend(out)
            if not valid:continue
            v=tuple(values)
            if v not in unique:unique[v]=(row_term,col_term)
    return unique

def unary_fit(view,train_outputs,train_inputs,train,tests):
    mapping={}
    for src,tgt in zip(view,train_outputs):
        if src in mapping and mapping[src]!=tgt:return False
        mapping[src]=tgt
    # P29 source demands all TEST input projected colors already observed
    # for PREDICTION, but TRAIN-only representability may be positive.
    return True

def binary_mask_fit(a,b,gold):
    masks=[7,7,7,7]
    for u,v,w in zip(a,b,gold):
        k=(2 if u==0 else 0)+(1 if v==0 else 0)
        masks[k]&=(1 if w==0 else 0)|(2 if w==u else 0)|(4 if w==v else 0)
        if not masks[k]:return False
    return True

def audit_one(task):
    train=task["train"]
    test_inputs=[x["input"] for x in task["test"]]  # Never read original test gold.
    rows=shape_candidates(train,test_inputs)
    stat={"shapes":len(rows),"extensional_shape_classes":0,
          "max_distinct_views":0,"view_pairs_early_rejected":0,
          "view_pairs_checked_masks":0,"covered_by_source_color":True,
          "training_unary_fit":False,"training_binary_fit":False,
          "shape_first":None,"example_source_pair":None,
          "source_color_missing":False,
          "model_calls":0,"test_oracle_reads":0}
    if not rows:return stat
    train_ins=[p["input"] for p in train]
    train_gold=tuple(v for p in train for row in p["output"] for v in row)
    source_inputs=train_ins+test_inputs
    representative={}
    for _,row,col,test_sh in rows:
        all_sh=tuple((len(p["output"]),len(p["output"][0])) for p in train)+tuple(test_sh)
        if all_sh not in representative:representative[all_sh]=(row,col)
    stat["extensional_shape_classes"]=len(representative)
    stat["source_color_missing"]=any(
       any(v!=0 and v not in set(u for row in p["input"] for u in row)
           for row in p["output"] for v in row) for p in train)
    for sh,(nameR,nameC) in representative.items():
        unique=generate_views(source_inputs,sh)
        stat["max_distinct_views"]=max(stat["max_distinct_views"],len(unique))
        # Filter train-only view prefixes; all inference also has test inputs
        ntrain=sum(len(p["output"])*len(p["output"][0]) for p in train)
        vals=[(v[:ntrain],sem) for v,sem in unique.items()]
        for a,sem in vals:
            if unary_fit(a,train_gold,train_ins,train,test_inputs):
                stat["training_unary_fit"]=True
                stat["shape_first"]=[nameR,nameC]
                stat["example_source_pair"]=[sem]
                return stat
        if stat["source_color_missing"]:continue
        # Exact necessary source-coverage condition:
        # Every nonzero desired color must be a value of either source view.
        bad_masks=[]
        for a,_ in vals:
            miss=0
            for i,(src,desired) in enumerate(zip(a,train_gold)):
                if desired!=0 and src!=desired:miss|=1<<i
            bad_masks.append(miss)
        for ia,(a,ase) in enumerate(vals):
            mask=bad_masks[ia]
            for ib,(b,bse) in enumerate(vals):
                if mask & bad_masks[ib]:
                    stat["view_pairs_early_rejected"]+=1
                    continue
                stat["view_pairs_checked_masks"]+=1
                if binary_mask_fit(a,b,train_gold):
                    stat["training_binary_fit"]=True
                    stat["shape_first"]=[nameR,nameC]
                    stat["example_source_pair"]=[ase,bse]
                    return stat
    return stat

def audit(root,arc,receipt_path):
    root=Path(root);arc=Path(arc)
    raw=Path(receipt_path).read_bytes()
    if sha256(raw).hexdigest()!=FIRST_RECEIPT_SHA256:raise ValueError("P29_FIRST_RECEIPT_SHA_MISMATCH")
    if git_blob(root/"experiments/q3_p29_induced_coordinate_programs.mjs")!=P29_SOURCE_GIT_BLOB:
        raise ValueError("P29_SOURCE_CHANGED")
    receipt=json.loads(raw)
    cohort_path=root/"docs/experiments/q3_p29_FIRST_FRESH48_COHORT_FROZEN.json"
    cohort=json.loads(cohort_path.read_text())
    if receipt["cohort_first_original"]!=48 or receipt["science_decision"]!="P29_FIRST_FRESH_TRANSFER_FAIL_STOP":
        raise ValueError("NO_FIRST_FAIL")
    if len(cohort["ids"])!=48 or [x["id"]+".json" for x in receipt["rows"]]!=cohort["ids"]:
        raise ValueError("COHORT_IDENTITY_DRIFT")
    t0=time.perf_counter()
    rows=[]
    for id,row in zip(cohort["ids"],receipt["rows"]):
        b=(arc/"data/evaluation"/id).read_bytes()
        if sha256(b).hexdigest()!=row["original_file_sha256"]:
            raise ValueError("UPSTREAM_EVAL_BYTES_CHANGED:"+id)
        task=json.loads(b)
        stats=audit_one(task)
        stats["id"]=id
        if (stats["shapes"]>0)!=(row["trace"]["shapePrograms"]>0):
            raise ValueError("SHAPE_FIT_ORIGINAL_DISAGREEMENT:"+id)
        rows.append(stats)
    shape=sum(x["shapes"]>0 for x in rows)
    unary=sum(x["training_unary_fit"] for x in rows)
    binary_=sum(x["training_binary_fit"] for x in rows)
    no_fit=sum(not (x["training_unary_fit"] or x["training_binary_fit"]) for x in rows)
    return {
      "schema":"neumann.q3.p29.independent-complete-coordinate-representability.v1",
      "scope":"SAME_ALREADY_OPENED_48_PROOF_ONLY_NO_NEW_EVAL",
      "first_original_sha256":sha256(raw).hexdigest(),
      "first_original_cohort":cohort["ids"],
      "method":"All 16x16 coordinate views, extensional shape quotient, palette constraints and four-bucket zero-mask feasibility; no runtime maxViews=100/maxPairs=10000 pruning.",
      "conditional_language_limit":"36 preordered shape formulas, 16 typed row and 16 typed col term options, unary color table, binary zero/source1/source2 truth table",
      "original_count":len(rows),
      "shape_fit_count":shape,
      "complete_unary_train_fit":unary,
      "complete_binary_train_fit":binary_,
      "complete_no_train_fit":no_fit,
      "source_color_missing_count":sum(x["source_color_missing"] for x in rows),
      "total_view_pairs_checked_masks":sum(x["view_pairs_checked_masks"] for x in rows),
      "total_view_pairs_early_rejected":sum(x["view_pairs_early_rejected"] for x in rows),
      "counterexample_to_runtime_pruning_missed_train_programs":sum(
        (x["training_unary_fit"] or x["training_binary_fit"]) and
        x["id"][:-5] in {r["id"] for r in receipt["rows"] if r["trace"]["ast"] is None} for x in rows),
      "no_test_oracle_used":True,
      "q3_new_primitive":"OPEN","q6_unseen_transfer":"OPEN","frontier":"OPEN",
      "runtime_seconds":time.perf_counter()-t0,
      "rows":rows
    }

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("python experiments/q3_p29_complete_representability_audit.py ROOT ARC_ROOT FIRST_P29_JSON")
    print(json.dumps(audit(*sys.argv[1:]),indent=2,sort_keys=True))
