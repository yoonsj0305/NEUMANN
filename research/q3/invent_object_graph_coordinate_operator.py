"""Q3: invent an object-graph rewrite operator when pixel/panel grammar fails.

This inventor learns both (a) a new input representation using connected
colored components rather than aligned panels and (b) a new executable
symbolic coordinate rule from actual TRAIN input/output counterexamples.
It DOES NOT contain a prewritten "draw corner markers" function, target task
ID, output picture, hardcoded source color, shape choice or frame template.

The logic infers the exact relative pixel-emission set from observed edits,
learns color-invariant object selection conditions from positive/negative
component evidence, and compiles a new Grid->Grid operator AST. Edits on
unmodeled inputs cause ABSTAIN, never an invented assertion of certainty.

Scientific scope: human supplies universal component extraction, symbolic
bbox-coordinate constructors, and constraint solver. NEUMANN discovers and
compiles novel *instances* of graph transformation semantics, not an
unrestricted programming language or a learned-neural frontier creator.
Test on fixed ARC2 source-distinct public TRAIN originals, not unseen EVAL.
"""
from __future__ import annotations
from collections import Counter,deque
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path

from research.q3.induce_binary_algebra_original import PIN as ARC1_PIN,grid_ok

ARC2_PIN="f3283f727488ad98fe575ea6a5ac981e4a188e49"
SCHEMA="neumann.q3.counterexample-invented-object-coordinate-operator.v1"


def stablehash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,
                           separators=(",",":")).encode()).hexdigest()


@dataclass(frozen=True)
class Component:
    color:int
    top:int
    left:int
    bottom:int
    right:int
    area:int
    points:tuple

    def field(self,key):
        h=self.bottom-self.top+1
        w=self.right-self.left+1
        if key=="h":return h
        if key=="w":return w
        if key=="min_dim":return min(h,w)
        if key=="max_dim":return max(h,w)
        if key=="area":return self.area
        if key=="aspect_diff":return abs(h-w)
        if key=="is_square":return int(h==w)
        if key=="fill_milli":return (1000*self.area)//(h*w)
        if key=="perimeter_box":return 2*(h+w)
        if key=="occupied_border":
            return sum(y in (self.top,self.bottom) or
                       x in (self.left,self.right) for y,x in self.points)
        if key=="interior_area":return max(0,h-2)*max(0,w-2)
        raise ValueError("UNKNOWN_CANDIDATE_FEATURE")


FIELDS=("min_dim","max_dim","area","aspect_diff","is_square",
        "fill_milli","h","w","perimeter_box","occupied_border",
        "interior_area")


def objects(grid,connectivity):
    """Generic graph conversion, derived from raw grid, NOT target programs."""
    if not grid_ok(grid):return None
    h,w=len(grid),len(grid[0])
    bg=Counter(x for row in grid for x in row).most_common(1)[0][0]
    if connectivity==4:
        directions=((0,1),(0,-1),(1,0),(-1,0))
    elif connectivity==8:
        directions=tuple((y,x) for y in (-1,0,1)
                         for x in (-1,0,1) if y or x)
    else:raise ValueError("BAD_GRAPH_CONNECTIVITY")
    seen=set()
    result=[]
    for y in range(h):
        for x in range(w):
            color=grid[y][x]
            if color==bg or (y,x) in seen:continue
            seen.add((y,x))
            queue=deque([(y,x)])
            pts=[]
            while queue:
                cy,cx=queue.popleft()
                pts.append((cy,cx))
                for dy,dx in directions:
                    ny,nx=cy+dy,cx+dx
                    if 0<=ny<h and 0<=nx<w and grid[ny][nx]==color \
                       and (ny,nx) not in seen:
                        seen.add((ny,nx))
                        queue.append((ny,nx))
            ys=[p[0] for p in pts];xs=[p[1] for p in pts]
            result.append(Component(color,min(ys),min(xs),max(ys),
                                    max(xs),len(pts),tuple(sorted(pts))))
    return bg,result


def on_component_ring(comp,y,x):
    return ((y in (comp.top-1,comp.bottom+1) and
             comp.left<=x<=comp.right) or
            (x in (comp.left-1,comp.right+1) and
             comp.top<=y<=comp.bottom))


def symbolize(value,minimum,maximum):
    """Infer a coordinate term from the observed TRAIN edit itself.

    Coordinates not equal to a boundary +/- 1 have NO legal expression.
    The operator can never memorize a task's absolute pixel location.
    """
    choices=[]
    for anchor,ref in (("min",minimum),("max",maximum)):
        for d in (-1,0,1):
            if ref+d==value:
                choices.append(((abs(d),0 if anchor=="min" else 1),
                                 (anchor,d)))
    if not choices:return None
    return min(choices)[1]


def template_for(comp,edits):
    """A new symbolic EMISSION function is written from changed locations."""
    points=sorted((y,x) for y,x in edits if on_component_ring(comp,y,x))
    if not points:return None
    terms=[]
    for y,x in points:
        ry=symbolize(y,comp.top,comp.bottom)
        rx=symbolize(x,comp.left,comp.right)
        if ry is None or rx is None:return None
        terms.append((ry[0],ry[1],rx[0],rx[1]))
    return tuple(sorted(set(terms)))


def emit_from_template(comp,template):
    result=set()
    for ranchor,rd,canchor,cd in template:
        y=(comp.top if ranchor=="min" else comp.bottom)+rd
        x=(comp.left if canchor=="min" else comp.right)+cd
        result.add((y,x))
    return result


def predicate_hits(comp,atom):
    field,relation,t=atom
    v=comp.field(field)
    if relation=="ge":return v>=t
    if relation=="le":return v<=t
    if relation=="eq":return v==t
    raise ValueError("BAD_GENERATED_PREDICATE")


def learn_selector(samples):
    """Learn a new Boolean AST from positive and negative real components.

    Candidate atoms and numerical constants emerge from the observed feature
    ranges, not from a manually selected output pattern. Search for a
    one/two-clause invariant, with color-independent features preferred.
    """
    if not samples:return None
    positives=[comp for comp,label in samples if label]
    negatives=[comp for comp,label in samples if not label]
    if len(positives)<2:return None
    if not negatives:
        return ()
    n=len(negatives)
    bits=(1<<n)-1
    atoms={}
    for field in FIELDS:
        values=sorted({obj.field(field) for obj,label in samples})
        if len(values)==1:continue
        for t in values:
            for relation in ("ge","le","eq"):
                atom=(field,relation,t)
                if any(not predicate_hits(x,atom) for x in positives):
                    continue
                rejects=0
                for i,x in enumerate(negatives):
                    if not predicate_hits(x,atom):rejects|=1<<i
                if rejects:
                    atoms[atom]=rejects
    if not atoms:return None
    # Choose a one-clause rule when adequate. Prefer a two-clause generic
    # geometry rule over a longer task-specific formula.
    pairs=sorted(atoms.items(),
                 key=lambda item:(FIELDS.index(item[0][0]),
                                  item[0][1],item[0][2]))
    single=[atom for atom,mask in pairs if mask==bits]
    if single:
        return (min(single,key=lambda a:(FIELDS.index(a[0]),a[1],a[2])),)
    best=None
    for i,(a,mask_a) in enumerate(pairs):
        for b,mask_b in pairs[i+1:]:
            if mask_a|mask_b!=bits:continue
            score=(FIELDS.index(a[0])+FIELDS.index(b[0]),
                   a,b)
            if best is None or score<best[0]:
                best=(score,(a,b))
    return best[1] if best else None


def select_object(comp,selector):
    return all(predicate_hits(comp,atom) for atom in selector)


@dataclass(frozen=True)
class InventedObjectOperator:
    connectivity:int
    selector:tuple
    template:tuple
    output_color:int

    def ast(self):
        core=["lambda",["grid","Grid"],
             ["Compose",
              ["ExtractComponents",["ModeBackground"],
               ["Connectivity",self.connectivity]],
              ["Select",["All",[
                    ["Compare",a[0],a[1],a[2]]
                     for a in self.selector]]],
              ["EmitCells",[
                  ["Coordinate",["Boundary",ry,dy],
                                ["Boundary",rx,dx]]
                  for ry,dy,rx,dx in self.template]],
              ["PaintConstantColor",self.output_color],
              ["Fallback","COPY_INPUT_OR_ABSTAIN_ON_CONFLICT"]]]
        return ["DefineInventedObjectGraphOperator",
                "invented_object_"+stablehash(core)[:16],core]

    def apply(self,grid):
        found=objects(grid,self.connectivity)
        if found is None:return None
        bg,comps=found
        h,w=len(grid),len(grid[0])
        edits=set()
        for comp in comps:
            if not select_object(comp,self.selector):continue
            for y,x in emit_from_template(comp,self.template):
                if y<0 or x<0 or y>=h or x>=w:
                    return None
                if grid[y][x]!=bg and grid[y][x]!=self.output_color:
                    return None
                edits.add((y,x))
        result=[row[:] for row in grid]
        for y,x in edits:result[y][x]=self.output_color
        return result


def learn_object_operator(train,connectivity):
    if len(train)<2:return None
    allcomponents=[]
    all_positive=[]
    shapes=[]
    all_target_colors=set()
    for pair in train:
        source,target=pair["input"],pair["output"]
        if not grid_ok(source) or not grid_ok(target) or \
           len(source)!=len(target) or len(source[0])!=len(target[0]):
            return None
        bg,comps=objects(source,connectivity)
        if not comps or len(comps)>70:return None
        edits={}
        for y in range(len(source)):
            for x in range(len(source[0])):
                if source[y][x]!=target[y][x]:
                    # New graph paint semantics must CREATE new output colors,
                    # not merely copy existing conservative JOIN operands.
                    if source[y][x]!=bg:return None
                    edits[(y,x)]=target[y][x]
        if not edits:return None
        colors=set(edits.values())
        if len(colors)!=1:return None
        target_color=next(iter(colors))
        if target_color in set(v for row in source for v in row):
            # Output creation absent from original source entirely.
            return None
        all_target_colors.add(target_color)
        known_edits=set(edits)
        explained=set()
        for comp in comps:
            signature=template_for(comp,known_edits)
            positive=signature is not None
            if positive:
                points=emit_from_template(comp,signature)
                if not points.issubset(known_edits):
                    return None
                all_positive.append(signature)
                explained.update(points)
            allcomponents.append((comp,positive))
        if explained!=known_edits:
            return None
    if len(all_target_colors)!=1 or len(all_positive)<2:
        return None
    if len(set(all_positive))!=1:
        # No shared data-created emission expression across size variations.
        return None
    template=all_positive[0]
    if len(template)<2 or len(template)>40:return None
    selector=learn_selector(allcomponents)
    if selector is None:return None
    candidate=InventedObjectOperator(
        connectivity,selector,template,next(iter(all_target_colors)))
    if any(candidate.apply(p["input"])!=p["output"] for p in train):
        return None
    return candidate


def study(task,taskid,cohort):
    if len(task["train"])<2:
        return {"id":taskid,"cohort":cohort,
                "status":"INSUFFICIENT_EXAMPLES","submitted":False,"exact":False}
    learned=[]
    for connectivity in (4,8):
        operator=learn_object_operator(task["train"],connectivity)
        if operator is not None:learned.append(operator)
    if not learned:
        return {"id":taskid,"cohort":cohort,"status":"NO_GRAPH_PROGRAM_INVENTED",
                "submitted":False,"exact":False}
    # All generated candidate definitions are constructed from TRAIN ONLY.
    before_gold=[c.ast() for c in learned]
    predictions=[]
    for t in task["test"]:
        outputs=[c.apply(t["input"]) for c in learned]
        if not outputs or any(o is None for o in outputs) or \
           any(o!=outputs[0] for o in outputs[1:]):
            predictions.append(None)
        else:predictions.append(outputs[0])
    submitted=all(p is not None for p in predictions)
    exact=submitted and all(p==t["output"] for p,t in zip(predictions,task["test"]))
    return {
        "id":taskid,"cohort":cohort,
        "status":"INVENTED_GRAPH_REWRITE_OPERATOR",
        "invented_operator_AST":before_gold,
        "invented_operator_SHA256":stablehash(before_gold),
        "candidate_operator_count":len(learned),
        "template_sites":[len(c.template) for c in learned],
        "selector_clauses":[len(c.selector) for c in learned],
        "connectivities":[c.connectivity for c in learned],
        "submitted":submitted,"exact":exact,
        "wrong_submission":submitted and not exact,
        "test_prediction_sha256":[stablehash(p) if p is not None else None
                                  for p in predictions],
        "new_type":"Grid -> Graph[Components] -> SymbolicObjectPredicate -> CoordinateEmitter -> Grid",
        "old_join_cannot_create_new_output_color":True,
        "generated_before_test_gold":True,
    }


def run(arc1_root:Path,arc2_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_ORIGINAL_FIRST")
    old={p.stem for folder in ("training","evaluation")
         for p in (arc1_root/"data"/folder).glob("*.json")}
    fresh=sorted((arc2_root/"data"/"training").glob("*.json"))
    if len(old)!=800 or len(fresh)!=1000:
        raise ValueError("ORIGINAL_COHORT_DRIFT")
    novel=[f for f in fresh if f.stem not in old]
    if len(novel)!=233:
        raise ValueError("NEW_SOURCE_COHORT_NOT_233")
    out.mkdir(parents=True)
    rows=[]
    for file in novel:
        result=study(json.loads(file.read_text()),file.stem,"ARC2_SOURCE_DISTINCT")
        rows.append(result)
        if result["status"]=="INVENTED_GRAPH_REWRITE_OPERATOR":
            print("INVENTED_OBJECT_RULE",file.stem,
                  "sites",result["template_sites"],
                  "predicates",result["selector_clauses"],
                  "exact",result["exact"],"submitted",result["submitted"],
                  flush=True)
    stats={
        "source_distinct_originals":len(rows),
        "graph_operator_definitions":sum(x["status"]=="INVENTED_GRAPH_REWRITE_OPERATOR" for x in rows),
        "original_test_submissions":sum(x["submitted"] for x in rows),
        "original_test_exact":sum(x["exact"] for x in rows),
        "original_test_wrong":sum(x.get("wrong_submission",False) for x in rows)
    }
    report={
        "schema":SCHEMA,"ARC1_PIN":ARC1_PIN,"ARC2_PIN":ARC2_PIN,
        "source_originals_source_exposed":True,
        "human_component_and_coordinate_runtime":True,
        "train_only_graph_semantics_inferred":True,
        "same_original_source_233_after_prior_exposure":True,
        "reserved_public_EVAL_ids_consumed":0,
        "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
        "stats":stats,"rows":rows
    }
    (out/"FIRST.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"},sort_keys=True))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--arc1-root",type=Path,required=True)
    p.add_argument("--arc2-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    run(a.arc1_root,a.arc2_root,a.out)
