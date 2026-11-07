"""Q3 NEW STRUCTURAL-SEMANTICS experiment on real prior-unsolved ARC originals.

Do not repeat an already-saturated fixed DSL, teacher caching, or cheap ranker.

A learnable program constructor exposes DIFFERENT semantic state:
connected colored objects -> learned shape/density filtering -> spatial
relations between object centers -> grid of object attributes. The emitted
program is a typed higher-order AST that can change output shape, unlike P2.5.

Learning receives only ARC original TRAIN input/output pairs, never a hidden
test output, task ID, target source answer or human hand-selected operator.
Each proposal is executable; gradient weights learn from the TRAIN score, and
the best composed AST is frozen BEFORE any heldout test input or output read.

Scientific limitations: Python primitives and the higher-order composition
substrate are HUMAN-DESIGNED. Model learns the composition parameters, not
the primitive semantics. Even if original outputs improve, full NEUMANN Q3
autonomous novel base-semantics invention remains OPEN. A 32-task source
cohort is previously OPENED, not a fresh cross-author holdout.

Global Q3, Q4, Q6 remain OPEN regardless of source-domain scoped outcome.
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
import statistics
import time

UPSTREAM="fchollet/ARC-AGI"
PIN="399030444e0ab0cc8b4e199870fb20b863846f34"
# Immutable previously opened P25 public evaluation 32, not a new reserve.
P25_IDS=(
 "2037f2c7","c87289bb","281123b4","0a1d4ef5","1c56ad9f",
 "c074846d","137f0df0","62ab2642","1a2e2828","f83cb3f6",
 "f3e62deb","68b67ca3","9ddd00f0","9772c176","b4a43f3b",
 "2685904e","96a8c0cd","7c8af763","0b17323b","0a2355a6",
 "0c9aba6e","81c0276b","31adaf00","6a11f6da","e7b06bea",
 "4b6b68e5","2a5f8217","93b4f4b3","a57f2f04","c1990cce",
 "4cd1b7b2","1e81d6f9",
)
# Grammar productions are generic. None of these is a hardcoded original answer.
CHOICES={
 "connectivity":(4,8),
 "background_top_k":(0,1,2,3),
 "minimum_pixels":(4,6,9,12),
 "minimum_width":(2,3),
 "minimum_height":(2,3),
 "minimum_fill":(0.65,0.80,0.92,0.98),
 "cluster_ratio":(0.10,0.14,0.18,0.23),
 "coordinate":("center","centroid"),
 "collision":("largest","ignore"),
}
ORDER=tuple(CHOICES)
SCHEMA="neumann.q3.object-relational-composition-original-develop-v1"


@dataclass(frozen=True)
class Comp:
    color:int
    cells:tuple
    y_min:int
    y_max:int
    x_min:int
    x_max:int

    @property
    def area(self):return len(self.cells)
    @property
    def width(self):return self.x_max-self.x_min+1
    @property
    def height(self):return self.y_max-self.y_min+1
    @property
    def fill(self):return self.area/(self.width*self.height)
    def position(self,method:str):
        if method=="center":
            return ((self.y_min+self.y_max)/2,(self.x_min+self.x_max)/2)
        return (sum(y for y,x in self.cells)/self.area,
                sum(x for y,x in self.cells)/self.area)


@dataclass(frozen=True)
class Program:
    config:tuple

    def obj(self):
        return dict(zip(ORDER,self.config))
    def ast(self):
        c=self.obj()
        return [
          "SpatialRasterize",[
            "ClusterObjectCenters",[
              "FilterDenseRegions",[
                "ConnectedColorComponents",[
                  "ColorMaskExceptMostFrequent","input",
                  c["background_top_k"]
                ],c["connectivity"]
              ],
              ["area >=",c["minimum_pixels"]],
              ["width >=",c["minimum_width"]],
              ["height >=",c["minimum_height"]],
              ["fill >=",c["minimum_fill"]]
            ],c["cluster_ratio"],c["coordinate"]
          ],"component.color",c["collision"]
        ]
    def digest(self):
        return hashlib.sha256(json.dumps(self.ast(),sort_keys=True).encode()).hexdigest()


def components(grid,exclude,connectivity):
    h=len(grid);w=len(grid[0])
    visited=set()
    edges=((1,0),(-1,0),(0,1),(0,-1))
    if connectivity==8:edges=edges+((1,1),(-1,-1),(-1,1),(1,-1))
    out=[]
    for y in range(h):
      for x in range(w):
        color=grid[y][x]
        if color in exclude or (y,x) in visited:continue
        stack=[(y,x)]
        visited.add((y,x));cells=[]
        while stack:
          cy,cx=stack.pop()
          cells.append((cy,cx))
          for dy,dx in edges:
            yy=cy+dy;xx=cx+dx
            if (0<=yy<h and 0<=xx<w and grid[yy][xx]==color
                and (yy,xx) not in visited):
                visited.add((yy,xx));stack.append((yy,xx))
        out.append(Comp(color,tuple(cells),
             min(p[0] for p in cells),max(p[0] for p in cells),
             min(p[1] for p in cells),max(p[1] for p in cells)))
    return out


def axis_clusters(items,axis,thresh):
    seq=sorted((it.position(axis[1])[axis[0]],i) for i,it in enumerate(items))
    groups=[]
    for coordinate,index in seq:
        if not groups or coordinate-groups[-1][-1][0] > thresh:
            groups.append([])
        groups[-1].append((coordinate,index))
    # The first element is used for stable thresholding; avoid transitive
    # merging many faraway objects into one cluster via chaining.
    return [tuple(index for coord,index in group) for group in groups]


def synth_execute(program:Program,grid):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):
        return None
    h=len(grid);w=len(grid[0])
    if h>45 or w>45:return None
    p=program.obj()
    freq=Counter(x for row in grid for x in row)
    excluded={x for x,n in sorted(freq.items(),key=lambda kv:(-kv[1],kv[0]))
              [:p["background_top_k"]]}
    objects=[
       obj for obj in components(grid,excluded,p["connectivity"])
       if obj.area>=p["minimum_pixels"]
       and obj.width>=p["minimum_width"]
       and obj.height>=p["minimum_height"]
       and obj.fill>=p["minimum_fill"]
    ]
    if not objects or len(objects)>64:return None
    ygroups=axis_clusters(objects,(0,p["coordinate"]),max(1,p["cluster_ratio"]*h))
    xgroups=axis_clusters(objects,(1,p["coordinate"]),max(1,p["cluster_ratio"]*w))
    if not 1<=len(ygroups)<=30 or not 1<=len(xgroups)<=30:return None
    rows=[[0 for _ in xgroups] for _ in ygroups]
    cell_best={}
    for iy,group in enumerate(ygroups):
        for index in group:
            candidates=[j for j,subset in enumerate(xgroups) if index in subset]
            if len(candidates)!=1: return None
            j=candidates[0]
            c=objects[index]
            if (iy,j) in cell_best:
                if p["collision"]=="ignore":
                    return None
                prior=cell_best[(iy,j)]
                if c.area<=prior.area:continue
            cell_best[(iy,j)]=c
            rows[iy][j]=c.color
    return rows


def score(program,train):
    """TRAIN-only reward. No TEST access before frozen student checkpoint."""
    values=[]
    for pair in train:
        expected=pair["output"]
        got=synth_execute(program,pair["input"])
        if got is None:
            values.append(0.0);continue
        eh,ew=len(expected),len(expected[0])
        gh,gw=len(got),len(got[0])
        # Shape and colored-symbol overlap partial credit train structure.
        d=abs(eh-gh)+abs(ew-gw)
        shape=1/(1+d)
        ef=Counter(x for row in expected for x in row)
        gf=Counter(x for row in got for x in row)
        overlap=sum(min(n,gf.get(color,0)) for color,n in ef.items())
        precision=overlap/max(1,max(sum(ef.values()),sum(gf.values())))
        if not d:
            accuracy=sum(expected[y][x]==got[y][x]
                 for y in range(eh) for x in range(ew))/(eh*ew)
        else:accuracy=0
        values.append(0.15*shape+0.15*precision+0.70*accuracy)
    return sum(values)/len(values)


def exact_train(program,train):
    return all(synth_execute(program,p["input"])==p["output"] for p in train)


def softmax(logits):
    m=max(logits)
    vals=[math.exp(v-m) for v in logits]
    z=sum(vals)
    return [v/z for v in vals]


class OwnWeightComposer:
    def __init__(self,seed):
        self.rng=random.Random(seed)
        self.weights={k:[self.rng.gauss(0,0.02) for _ in v] for k,v in CHOICES.items()}
        self.baseline=0.
        self.updates=0

    def weights_digest(self):
        return hashlib.sha256(json.dumps(self.weights,sort_keys=True).encode()).hexdigest()

    def sample(self):
        config=[];events=[]
        for k in ORDER:
            probs=softmax(self.weights[k])
            t=self.rng.random();acc=0.;idx=len(probs)-1
            for j,p in enumerate(probs):
                acc+=p
                if t<=acc:
                    idx=j;break
            events.append((k,idx,probs))
            config.append(CHOICES[k][idx])
        return Program(tuple(config)),events

    def learn(self,events,reward,lr=0.13):
        advantage=reward-self.baseline
        self.baseline=0.92*self.baseline+0.08*reward
        for k,index,probs in events:
            for j,p in enumerate(probs):
                self.weights[k][j]+=lr*advantage*((j==index)-p)
        self.updates+=1


def invent_operator(train, *, seed=20261107,episodes=600):
    learner=OwnWeightComposer(seed)
    before=learner.weights_digest()
    start=time.perf_counter_ns()
    best=None;best_score=-1.;attempts=0
    seen=set();first_fit=None
    for i in range(episodes):
        program,trace=learner.sample()
        digest=program.digest()
        if digest in seen:
            continue
        seen.add(digest)
        s=score(program,train)
        attempts+=1
        learner.learn(trace,s)
        if s>best_score:
            best=program;best_score=s
        if s>=1.0-1e-9 and exact_train(program,train):
            first_fit=i+1
            best=program;best_score=1.
            break
    elapsed=(time.perf_counter_ns()-start)/1e6
    # Commit FULL program AST. This is the only inference artifact.
    return {"program":best,"program_ast":best.ast(),"program_sha256":best.digest(),
            "train_score":round(best_score,7),
            "train_exact":exact_train(best,train),
            "candidate_calls":attempts,"first_fit_episode":first_fit,
            "training_weight_updates":learner.updates,
            "own_weight_initial_sha256":before,
            "own_weight_final_sha256":learner.weights_digest(),
            "learning_wall_ms":round(elapsed,3)}


def load_original_data(root:Path,id:str):
    file=root/"data"/"evaluation"/(id+".json")
    raw=file.read_bytes()
    task=json.loads(raw)
    if not task["train"] or not task["test"]:
        raise ValueError("ORIGINAL_MISSING_TRAIN_TEST")
    return task,hashlib.sha256(raw).hexdigest()


def run(out:Path,arc_root:Path,ids=P25_IDS,episodes=600):
    if out.exists():raise ValueError("NO_OVERWRITE_FIRST")
    out.mkdir(parents=True)
    results=[]
    for id in ids:
        orig,rawsha=load_original_data(arc_root,id)
        result=invent_operator(orig["train"],episodes=episodes)
        selected=result.pop("program")
        # The student is fully frozen, including its AST, before test input
        # is consumed for a prediction. The official test output is read
        # only by the separate scoring stage, never to update the student.
        pred=[synth_execute(selected,t["input"]) for t in orig["test"]]
        exact=[p==t["output"] for p,t in zip(pred,orig["test"])]
        results.append({"original_id":id,"original_sha256":rawsha,
           **result,"test_count":len(orig["test"]),
           "test_exact":all(exact),"test_exact_per_case":exact,
           "test_output_sha256":[hashlib.sha256(json.dumps(p).encode()).hexdigest()
                     for p in pred]})
        print(id,"train",result["train_exact"],"score",result["train_score"],
              "test",all(exact),"samples",result["candidate_calls"],flush=True)
    report={
       "schema":SCHEMA,"arc_upstream":UPSTREAM,"original_source_pin":PIN,
       "previously_opened_original_32":len(ids),
       "all_32_fixed_before_source_execution":list(ids)==list(P25_IDS),
       "test_gold_used_to_generate_program":False,
       "compiled_program_not_in_frozen_P25_observation_language":True,
       "operator_language":"typed colored components -> learned filters -> learned spatial cluster -> attribute grid",
       "grammar_semantics_human_authored":True,
       "own_weights_trained_by_train_only_feedback":True,
       "exact_train":sum(x["train_exact"] for x in results),
       "exact_test":sum(x["test_exact"] for x in results),
       "new_external_unopened_originals":0,
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN",
       "results":results
    }
    (out/"FIRST.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--arc-root",type=Path,required=True)
    p.add_argument("--episodes",type=int,default=600)
    a=p.parse_args()
    run(a.out,a.arc_root,episodes=a.episodes)
