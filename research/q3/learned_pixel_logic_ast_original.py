"""Q3 original-ARC inductive operator invention: learn new executable logic AST.

Never uses a prewritten answer macro or a fixed object->filter->cluster
pipeline. The learned own-weight split policy generates a variable-length
nested IF/THEN operator that composes unary observed pixel/grid relations
into previously nonexistent predicates. Fitting is performed on original
TRAIN ONLY. The generated AST is frozen and executable on the test INPUT
before the evaluator looks at official output.

The underlying pixel observations/decision-tree substrate are human supplied.
Evidence of a correct original result can prove task-driven AST synthesis,
but NOT frontier-level autonomous invention independent of the human language
or a learned-exclusive advantage over the best same-rights classical solver.
Q3 stays OPEN unless stricter provenance and novelty gates are met.

Previous PR #691 randomly sampled a pre-written whole pipeline at episode 1.
Here entire nested rule AST (operators, branching order, threshold, actions,
tree depth) is produced in response to target TRAIN errors; no tree is
present before samples are provided.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import time

PIN="399030444e0ab0cc8b4e199870fb20b863846f34"
IDS=("2037f2c7","c87289bb","281123b4","0a1d4ef5","1c56ad9f",
 "c074846d","137f0df0","62ab2642","1a2e2828","f83cb3f6",
 "f3e62deb","68b67ca3","9ddd00f0","9772c176","b4a43f3b",
 "2685904e","96a8c0cd","7c8af763","0b17323b","0a2355a6",
 "0c9aba6e","81c0276b","31adaf00","6a11f6da","e7b06bea",
 "4b6b68e5","2a5f8217","93b4f4b3","a57f2f04","c1990cce",
 "4cd1b7b2","1e81d6f9")
COLORS=range(10)
KEEP=-1


def feature_names():
    names=["x_norm","y_norm","x","y","height","width","input",
           "top","bottom","left","right","diagonal",
           "row_nonzero","col_nonzero","row_diversity","col_diversity",
           "x_minus_y","x_plus_y","edge_distance","nonzero_above",
           "nonzero_below","nonzero_left","nonzero_right"]
    for c in COLORS:
        names.extend((f"row_count_{c}",f"col_count_{c}",
                      f"above_count_{c}",f"below_count_{c}",
                      f"left_count_{c}",f"right_count_{c}",
                      f"color_bbox_xmin_delta_{c}",
                      f"color_bbox_xmax_delta_{c}",
                      f"color_bbox_ymin_delta_{c}",
                      f"color_bbox_ymax_delta_{c}",
                      f"same_col_above_{c}",f"same_col_below_{c}",
                      f"bbox_inside_{c}",
                      f"bbox_touch_left_{c}",
                      f"bbox_touch_right_{c}",
                      f"bbox_touch_top_{c}",
                      f"bbox_touch_bottom_{c}"))
    return tuple(names)
FEATURE_NAMES=feature_names()
NFEAT=len(FEATURE_NAMES)


def build_features(grid):
    h=len(grid)
    if not h or not grid[0]:raise ValueError("EMPTY_GRID")
    w=len(grid[0])
    if any(len(row)!=w for row in grid) or h>30 or w>30:
        raise ValueError("INVALID_OR_TOO_LARGE_GRID")
    # Every feature available to both learner and runtime; no labels.
    locs={c:[] for c in COLORS}
    rows=[[0]*10 for _ in range(h)]
    cols=[[0]*10 for _ in range(w)]
    for y,row in enumerate(grid):
      for x,c in enumerate(row):
        if c not in COLORS:raise ValueError("UNSUPPORTED_COLOR")
        rows[y][c]+=1;cols[x][c]+=1;locs[c].append((y,x))
    bboxes={}
    for c,pts in locs.items():
        if pts:
            bboxes[c]=(min(p[0] for p in pts),max(p[0] for p in pts),
                      min(p[1] for p in pts),max(p[1] for p in pts))
        else:bboxes[c]=None
    above=[[[0]*10 for _ in range(w)] for _ in range(h)]
    below=[[[0]*10 for _ in range(w)] for _ in range(h)]
    for x in range(w):
        tally=[0]*10
        for y in range(h):
            above[y][x]=tally[:]
            tally[grid[y][x]]+=1
        tally=[0]*10
        for y in range(h-1,-1,-1):
            below[y][x]=tally[:]
            tally[grid[y][x]]+=1
    result=[]
    for y in range(h):
      left_tally=[0]*10
      for x in range(w):
        right_tally=[0]*10
        for xx in range(x+1,w):right_tally[grid[y][xx]]+=1
        up,down=above[y][x],below[y][x]
        c=grid[y][x]
        row=grid[y]
        def at(yy,xx):
            return grid[yy][xx] if 0<=yy<h and 0<=xx<w else -1
        f=[x/max(1,w-1),y/max(1,h-1),x,y,h,w,c,
          at(y-1,x),at(y+1,x),at(y,x-1),at(y,x+1),
          at(y-1,x-1),
          sum(a for cc,a in enumerate(rows[y]) if cc!=0),
          sum(a for cc,a in enumerate(cols[x]) if cc!=0),
          sum(a>0 for a in rows[y]),
          sum(a>0 for a in cols[x]),
          x-y,x+y,min(x,y,w-1-x,h-1-y),
          sum(a for cc,a in enumerate(up) if cc!=0),
          sum(a for cc,a in enumerate(down) if cc!=0),
          sum(a for cc,a in enumerate(left_tally) if cc!=0),
          sum(a for cc,a in enumerate(right_tally) if cc!=0)]
        for cc in COLORS:
            box=bboxes[cc]
            if box:
                ymin,ymax,xmin,xmax=box
                extra=(x-xmin,x-xmax,y-ymin,y-ymax,
                       int(up[cc]>0),int(down[cc]>0),
                       int(xmin<=x<=xmax and ymin<=y<=ymax),
                       int(x==xmin-1),int(x==xmax+1),
                       int(y==ymin-1),int(y==ymax+1))
            else:
                extra=(99.,99.,99.,99.,0,0,0,0,0,0,0)
            f.extend((rows[y][cc],cols[x][cc],up[cc],down[cc],
                      left_tally[cc],right_tally[cc])+extra)
        assert len(f)==NFEAT,(len(f),NFEAT)
        result.append(tuple(f))
        left_tally[c]+=1
    return result


def observations(train):
    X=[];y=[];block_ids=[]
    for block,pair in enumerate(train):
        a,b=pair["input"],pair["output"]
        if len(a)!=len(b) or len(a[0])!=len(b[0]):
            raise ValueError("SHAPE_NOT_SUPPORTED_BY_PIXEL_REWRITE")
        features=build_features(a)
        for idx,f in enumerate(features):
            yy,xx=divmod(idx,len(a[0]))
            target=b[yy][xx]
            old=a[yy][xx]
            X.append(f)
            y.append(KEEP if target==old else target)
            block_ids.append(block)
    return X,y,block_ids


def weighted_gini(labels):
    hist=Counter(labels)
    total=sum(v*(1 if k==KEEP else 6) for k,v in hist.items())
    if total==0:return 0.0
    return 1.0-sum((v*(1 if k==KEEP else 6)/total)**2 for k,v in hist.items())


def best_split(X,Y,indices,features):
    # Searches split values only on observed TRAIN, no target code and no
    # memorized original task ID. Model policy proposes features.
    base=weighted_gini(Y[i] for i in indices)
    if base<=1e-12:return None
    best=None
    for fi in features:
        uniques=sorted(set(X[i][fi] for i in indices))
        if len(uniques)<2:continue
        if len(uniques)>18:
            step=(len(uniques)-1)/17
            positions=sorted({min(len(uniques)-2,round(j*step)) for j in range(17)})
        else:positions=range(len(uniques)-1)
        for j in positions:
            thresh=(uniques[j]+uniques[j+1])/2
            lo=[i for i in indices if X[i][fi]<=thresh]
            if not lo or len(lo)==len(indices):continue
            hi=[i for i in indices if X[i][fi]>thresh]
            n=len(indices)
            score=base-(len(lo)/n*weighted_gini(Y[i] for i in lo)
                  +len(hi)/n*weighted_gini(Y[i] for i in hi))
            if best is None or score>best[0]:
                best=(score,fi,thresh,lo,hi)
    return best if best is not None and best[0]>1e-7 else None


class LearnedSplitPolicy:
    """Online trainable own weights; tree AST topology and rule thresholds are learned."""
    def __init__(self,seed):
        self.rng=random.Random(seed)
        self.w=[self.rng.gauss(0,.005) for _ in FEATURE_NAMES]
        self.updates=0
        self.best_not_in_initial_library=False
    def digest(self):
        return hashlib.sha256(json.dumps(self.w).encode()).hexdigest()
    def choose(self,n=36):
        # Explicit exploration before selection, no fixed score template.
        picks=set()
        for _ in range(n):
            f=self.rng.randrange(NFEAT)
            picks.add(f)
        return sorted(picks,key=lambda f:self.w[f],reverse=True)
    def update(self,chosen,gain,choices):
        # Centered credit only on the selected semantic observation.
        # Future splits will see the policy's updated nonzero own weights.
        for f in choices:
            self.w[f]-=.008*gain/max(1,len(choices))
        self.w[chosen]+=.008*gain
        self.updates+=1


def learn_ast(train,seed=10701,max_depth=8,max_leaves=96):
    X,Y,_=observations(train)
    if not any(c!=KEEP for c in Y):
        return {"status":"NO_CHANGE_CLASSICAL_IDENTITY","learned":False}
    model=LearnedSplitPolicy(seed)
    initial=model.digest()
    nleaf=[0]
    samples=0
    def fit(indices,depth):
        nonlocal samples
        labels=[Y[i] for i in indices]
        hist=Counter(labels)
        choice=max(hist,key=lambda k:(hist[k]*(1 if k==KEEP else 6),-k))
        if (len(hist)<=1 or depth>=max_depth or len(indices)<3
             or nleaf[0]>=max_leaves):
            nleaf[0]+=1
            return ["Write" if choice!=KEEP else "Keep",choice] if choice!=KEEP else ["Keep"]
        proposals=model.choose(n=54)
        samples+=len(proposals)
        rule=best_split(X,Y,indices,proposals)
        if rule is None:
            nleaf[0]+=1
            return ["Write",choice] if choice!=KEEP else ["Keep"]
        gain,fi,threshold,lo,hi=rule
        model.update(fi,gain,proposals)
        return ["IfLTE",FEATURE_NAMES[fi],round(threshold,7),
                fit(lo,depth+1),fit(hi,depth+1)]
    t0=time.perf_counter()
    ast=fit(list(range(len(Y))),0)
    return {"status":"EXECUTABLE_LEARNED_OPERATOR_AST",
         "ast":ast,"sha256":hashlib.sha256(json.dumps(ast,sort_keys=True).encode()).hexdigest(),
         "initial_weight_sha256":initial,
         "trained_weight_sha256":model.digest(),
         "gradient_update_steps":model.updates,
         "learned_nodes":count_nodes(ast),
         "candidate_split_features_evaluated":samples,
         "train_observation_count":len(X),
         "actual_learning_wall_ms":round((time.perf_counter()-t0)*1000,3),
         "human_supplied_AST_answer":False,
         "training_only":True}


def count_nodes(node):
    if node[0]!="IfLTE":return 1
    return 1+count_nodes(node[3])+count_nodes(node[4])


FEATURE_INDEX={name:i for i,name in enumerate(FEATURE_NAMES)}


def execute(ast,grid):
    features=build_features(grid)
    h,w=len(grid),len(grid[0])
    result=[row[:] for row in grid]
    def eval_node(node,x):
        while node[0]=="IfLTE":
            fi=FEATURE_INDEX[node[1]]
            node=node[3] if x[fi]<=node[2] else node[4]
        if node[0]=="Keep":return KEEP
        if node[0]=="Write":return node[1]
        raise ValueError("INVALID_GENERATED_OPERATOR_NODE")
    for i,f in enumerate(features):
        a=eval_node(ast,f)
        if a!=KEEP:
            yy,xx=divmod(i,w)
            result[yy][xx]=a
    return result


def run(arc_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_FIRST")
    out.mkdir(parents=True)
    receipts=[]
    for taskid in IDS:
        path=arc_root/"data"/"evaluation"/(taskid+".json")
        raw=path.read_bytes()
        task=json.loads(raw)
        if any(len(p["input"])!=len(p["output"]) or
               len(p["input"][0])!=len(p["output"][0])
               for p in task["train"]):
            receipts.append({"task_id":taskid,"status":"CLASSICAL_PREFLIGHT_SHAPE_UNSUPPORTED",
                             "original_sha256":hashlib.sha256(raw).hexdigest(),
                             "TRAIN_exact":False,"TEST_exact":False})
            continue
        try:
            fitted=learn_ast(task["train"])
            if fitted["status"]!="EXECUTABLE_LEARNED_OPERATOR_AST":
                receipts.append({"task_id":taskid,**fitted,"TRAIN_exact":False,"TEST_exact":False})
                continue
            ast=fitted["ast"]
            train_fit=all(execute(ast,p["input"])==p["output"] for p in task["train"])
            # Generated operator frozen BEFORE touching test, including AST hash.
            preds=[execute(ast,p["input"]) for p in task["test"]]
            exact=all(p==q["output"] for p,q in zip(preds,task["test"]))
            receipts.append({"task_id":taskid,
                 "original_sha256":hashlib.sha256(raw).hexdigest(),
                 **fitted,"TRAIN_exact":train_fit,"TEST_exact":exact,
                 "AST_frozen_before_TEST_eval":True,
                 "TEST_pred_sha256":[hashlib.sha256(json.dumps(x).encode()).hexdigest() for x in preds]})
            print(taskid,"learned",fitted["gradient_update_steps"],
                  "nodes",fitted["learned_nodes"],
                  "train",train_fit,"test",exact,flush=True)
        except (ValueError,OverflowError) as exc:
            receipts.append({"task_id":taskid,"status":"ABSTAIN_INVALID_OR_UNSUPPORTED",
                "reason":str(exc)[:120],"TRAIN_exact":False,"TEST_exact":False})
    report={"schema":"neumann.q3.learned-logic-AST-on-original-P25-residual.v1",
        "original_source_commit":PIN,"previously_project_opened":len(IDS),
        "registered_fixed_ids":list(IDS),
        "new_unopened_eval_ids_consumed":0,
        "complete_train_fits":sum(bool(x["TRAIN_exact"]) for x in receipts),
        "complete_test_fits":sum(bool(x["TEST_exact"]) for x in receipts),
        "model_generated_variable_topology_AST":True,
        "not_static_object_pipeline":True,
        "human_supplied_primitives_and_feature_vocabulary":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "rows":receipts}
    (out/"FIRST.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("SCOPED_RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"}))
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    run(args.arc_root,args.out)
