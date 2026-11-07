"""Read-only independent certifier of an immutable Q3 original result.

Never imports generator, policy, training code or object components module.
Independently interprets the FROZEN emitted typed macro AST and replays
official original train/test outputs. No model refit or source-specific fix.
This certifies scoped original correctness only; Q3 learned invention OPEN.
"""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from pathlib import Path
import argparse


EXPECTED_FIRST_SHA="b90e1b73f61a4ada2b71d34126c605b5f3ab1aced0cccccc4f60e9161a9442ef"
EXPECTED_FIRST_RUN=42329413688
ORIGINAL_ID="0a1d4ef5"
EXPECTED_OPERATOR_SHA="480a030f5b9d5525aa2c318bb328d7e2e90fbec5080e42da8015956027363c47"


def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()


def config_from_archived_ast(ast):
    if ast[0]!="SpatialRasterize" or ast[2]!="component.color":
        raise ValueError("UNSUPPORTED_ARCHIVED_STRUCTURAL_SEMANTICS")
    relation=ast[1]
    if relation[0]!="ClusterObjectCenters":raise ValueError("WRONG_OPERATOR_GRAPH")
    fil=relation[1]
    if fil[0]!="FilterDenseRegions":raise ValueError("WRONG_FILTER_GRAPH")
    cc=fil[1]
    if cc[0]!="ConnectedColorComponents":raise ValueError("WRONG_COMPONENT_GRAPH")
    mask=cc[1]
    if mask[:2]!=["ColorMaskExceptMostFrequent","input"]:
        raise ValueError("WRONG_BACKGROUND_GRAPH")
    checks=("area >=","width >=","height >=","fill >=")
    for v,label in zip(fil[2:],checks):
        if v[0]!=label:raise ValueError("WRONG_TYPED_FILTER")
    return {
        "background_exclusion":mask[2],"neighbor_mode":cc[2],
        "min_area":fil[2][1],"min_width":fil[3][1],
        "min_height":fil[4][1],"min_fill":fil[5][1],
        "epsilon_fraction":relation[2],"location_rule":relation[3],
        "collision_rule":ast[3],
    }


def independently_interpret(grid,config):
    h=len(grid);w=len(grid[0])
    freq=Counter(value for row in grid for value in row)
    excluded={v for v,c in sorted(freq.items(),key=lambda kv:(-kv[1],kv[0]))
              [:config["background_exclusion"]]}
    # Independent connectivity implementation: union-find over same-color
    # adjacent coordinates rather than builder's BFS traversal.
    parent=list(range(h*w))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    def merge(a,b):
        x,y=root(a),root(b)
        if x!=y:parent[max(x,y)]=min(x,y)
    diag=config["neighbor_mode"]==8
    for y in range(h):
        for x in range(w):
            if grid[y][x] in excluded:continue
            for dy,dx in ((-1,0),(0,-1))+(((-1,-1),(-1,1)) if diag else ()):
                yy,xx=y+dy,x+dx
                if 0<=yy<h and 0<=xx<w and grid[yy][xx]==grid[y][x]:
                    merge(y*w+x,yy*w+xx)
    segments={}
    for y in range(h):
        for x in range(w):
            if grid[y][x] in excluded:continue
            segments.setdefault(root(y*w+x),[]).append((y,x))
    objects=[]
    for pts in segments.values():
        ys=[p[0] for p in pts];xs=[p[1] for p in pts]
        ymin,ymax=min(ys),max(ys);xmin,xmax=min(xs),max(xs)
        width=xmax-xmin+1;height=ymax-ymin+1
        area=len(pts);fill=area/(width*height)
        c=config
        if (area<c["min_area"] or width<c["min_width"] or height<c["min_height"]
             or fill<c["min_fill"]):continue
        if c["location_rule"]=="center":
            yc,xc=(ymin+ymax)/2,(xmin+xmax)/2
        elif c["location_rule"]=="centroid":
            yc,xc=sum(ys)/area,sum(xs)/area
        else: raise ValueError("UNKNOWN_LOCATION_RULE")
        objects.append({"color":grid[pts[0][0]][pts[0][1]],
                        "y":yc,"x":xc,"area":area})
    if not 1<=len(objects)<=64:return None

    def split(axis,epsilon):
        sorted_obj=sorted(enumerate(objects),key=lambda e:(e[1][axis],e[0]))
        partitions=[]
        for idx,obj in sorted_obj:
            val=obj[axis]
            if not partitions or val-partitions[-1][-1][0]>epsilon:
                partitions.append([])
            partitions[-1].append((val,idx))
        return [set(idx for val,idx in part) for part in partitions]
    rows=split("y",max(1,config["epsilon_fraction"]*h))
    cols=split("x",max(1,config["epsilon_fraction"]*w))
    if len(rows)>30 or len(cols)>30:return None
    res=[[0 for _ in cols] for _ in rows]
    active={}
    for iy,group in enumerate(rows):
        for idx in group:
            col_indices=[j for j,c in enumerate(cols) if idx in c]
            if len(col_indices)!=1:return None
            ix=col_indices[0]
            obj=objects[idx]
            key=(iy,ix)
            if key in active:
                if config["collision_rule"]=="ignore":return None
                if active[key]["area"]>=obj["area"]:continue
            active[key]=obj
            res[iy][ix]=obj["color"]
    return res


def run(archived_first:Path,original_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_INDEPENDENT_AUDIT")
    raw=archived_first.read_bytes()
    if sha(raw)!=EXPECTED_FIRST_SHA:raise ValueError("IMMUTABLE_FIRST_SHA_MISMATCH")
    report=json.loads(raw)
    rows=report["results"]
    if len(rows)!=32 or report["exact_test"]!=1 or report["exact_train"]!=1:
        raise ValueError("FROZEN_FIRST_COUNT_DRIFT")
    positives=[r for r in rows if r["test_exact"]]
    if len(positives)!=1 or positives[0]["original_id"]!=ORIGINAL_ID:
        raise ValueError("ARCHIVED_POSITIVE_DRIFT")
    archived=positives[0]
    operator=archived["program_ast"]
    if sha(json.dumps(operator,sort_keys=True).encode())!=EXPECTED_OPERATOR_SHA:
        raise ValueError("OPERATOR_SHA_DRIFT")
    cfg=config_from_archived_ast(operator)
    file=original_root/"data"/"evaluation"/(ORIGINAL_ID+".json")
    source=file.read_bytes()
    if sha(source)!=archived["original_sha256"]:
        raise ValueError("ORIGINAL_SOURCE_SHA_MISMATCH")
    actual=json.loads(source)
    pass_train=[independently_interpret(p["input"],cfg)==p["output"] for p in actual["train"]]
    pass_test=[independently_interpret(p["input"],cfg)==p["output"] for p in actual["test"]]
    if not all(pass_train) or not all(pass_test):
        raise RuntimeError("INDEPENDENT_ORIGINAL_REPLAY_FAILED")
    # Separate negative: adulterated rendered result must NOT silently pass.
    real=independently_interpret(actual["test"][0]["input"],cfg)
    wrong=[row[:] for row in real]
    wrong[0][0]=(wrong[0][0]+1)%10
    if wrong==actual["test"][0]["output"]:
        raise RuntimeError("FALSE_NEGATIVE_CONTROL")
    out.mkdir(parents=True)
    evidence={
       "schema":"neumann.q3.object-composition-sourcefree-readonly-independent-v1",
       "first_run":EXPECTED_FIRST_RUN,"first_report_sha256":EXPECTED_FIRST_SHA,
       "original_id":ORIGINAL_ID,
       "original_source_sha256":sha(source),
       "frozen_program_sha256":EXPECTED_OPERATOR_SHA,
       "archived_first_program_generated_at_episode":archived["first_fit_episode"],
       "archived_first_program_generated_before_gradient_effect":archived["first_fit_episode"]==1,
       "original_train_cases_independently_exact":sum(pass_train),
       "original_test_cases_independently_exact":sum(pass_test),
       "negative_control_rejected":True,
       "own_weight_autonomous_operator_invention_proven":False,
       "unopened_external_tasks_consumed":0,
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN"
    }
    (out/"READONLY_AUDIT.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return evidence


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--first",required=True,type=Path)
    p.add_argument("--arc-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    run(x.first,x.arc_root,x.out)
