"""Q3 object/relationship representation induction over typed nested arrays.

A generic latent-object grammar, NOT a named grid/ARC task solver. We choose
the representation by whether one compact executable correspondence law
explains multiple SOURCE demonstrations. Background is the empirical modal
leaf; nodes are connected monochromatic non-background components.

Match component identities by shape, not absolute position. Induce a simple
relational rewrite law using observable node features (category, geometry,
spatial order); compile to a standalone Python transform(x) and independently
re-execute in the *existing* SOURCE Docker verifier. This is one bounded
candidate representation inside StructuralInventionPolicy, not a second task
dispatcher. The algorithm never sees SOURCE heldout checks or TARGET gold.

CAUTION: Current graph-feature operators and matching are human implemented.
Discovering their best parameters is constrained autonomous synthesis, not
proof that a model invented its own representation grammar. Global Q3 OPEN.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from typing import Any

from .open_program_inventor import source_same_value, validate_code
from .q3_structure_factorization import StructuralFactor


@dataclass(frozen=True)
class Node:
    color: Any
    points: tuple[tuple[int,int],...]
    shape: tuple[tuple[int,int],...]
    r0: int
    c0: int
    h: int
    w: int
    area: int


def _rect(v):
    return (
        type(v) is list and bool(v)
        and 1 <= len(v) <= 30
        and all(
            type(row) is list and row and len(row)==len(v[0])
            and all(type(x) in (int,str,bool) for x in row)
            for row in v)
        and len(v[0])<=30)


def _mode(v):
    if not _rect(v):return None
    counts=Counter(t for row in v for t in row)
    # Avoid ambiguous segmentation in nearly uniform but tied inputs.
    top=counts.most_common(2)
    if len(top)>1 and top[0][1]==top[1][1]:return None
    return top[0][0]


def _nodes(grid,background):
    if not _rect(grid):return ()
    h,w=len(grid),len(grid[0])
    seen=set();nodes=[]
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if (r,c) in seen or source_same_value(color,background):
                continue
            stack=[(r,c)];seen.add((r,c));points=[]
            while stack:
                y,x=stack.pop()
                points.append((y,x))
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if (0<=yy<h and 0<=xx<w and
                            (yy,xx) not in seen and
                            source_same_value(grid[yy][xx],color)):
                        seen.add((yy,xx));stack.append((yy,xx))
            r0=min(p[0] for p in points)
            c0=min(p[1] for p in points)
            shape=tuple(sorted((y-r0,x-c0) for y,x in points))
            height=max(y for y,x in points)-r0+1
            width=max(x for y,x in points)-c0+1
            nodes.append(Node(color,tuple(sorted(points)),shape,r0,c0,
                              height,width,len(points)))
    return tuple(sorted(nodes,key=lambda n:(n.r0,n.c0,str(n.color))))



# D4 symmetries are an algebra of possible coordinate re-representations,
# not task-specific operators. Fit which transformation actually applies
# across independent SOURCE examples rather than hard-coding its name.
_SYMMETRIES=("identity","turn90","turn180","turn270",
             "reflect_rows","reflect_cols","swap_axes","reflect_diagonal")


def _symmetry_points(points,operator):
    if operator=="identity":
        raw=[(y,x) for y,x in points]
    elif operator=="turn90":
        raw=[(x,-y) for y,x in points]
    elif operator=="turn180":
        raw=[(-y,-x) for y,x in points]
    elif operator=="turn270":
        raw=[(-x,y) for y,x in points]
    elif operator=="reflect_rows":
        raw=[(-y,x) for y,x in points]
    elif operator=="reflect_cols":
        raw=[(y,-x) for y,x in points]
    elif operator=="swap_axes":
        raw=[(x,y) for y,x in points]
    elif operator=="reflect_diagonal":
        raw=[(-x,-y) for y,x in points]
    else:
        raise ValueError("unrecognized source-inferred coordinate symmetry")
    r0=min(y for y,x in raw);c0=min(x for y,x in raw)
    return tuple(sorted((y-r0,x-c0) for y,x in raw))


def _symmetry_matches(shape,target):
    return tuple(operator for operator in _SYMMETRIES
                 if _symmetry_points(shape,operator)==target)

def _pair_nodes(src,dst,background):
    left=_nodes(src,background)
    right=_nodes(dst,background)
    if not left or len(left)!=len(right) or len(left)>40:
        return None
    # Group only by observed normalized geometry, independent of color/position.
    # Ambiguous shape matches abort: assigning identities via hindsight would
    # let withheld SOURCE labels leak into the learned "representation".
    candidate_matches=[]
    for l in left:
        choices=[]
        for j,r in enumerate(right):
            for op in _symmetry_matches(l.shape,r.shape):
                choices.append((j,op))
        if not choices:return None
        candidate_matches.append(choices)
    if any(len(choices)>7 for choices in candidate_matches):
        return None
    # Max 40 components, bounded DFS candidates; minimize geometry and token
    # consistency across ALL observations, not a benchmark-specific key.
    order=sorted(range(len(left)),key=lambda i:len(candidate_matches[i]))
    best=None;best_cost=None;examined=0
    def dfs(pos,used,matching,cost):
        nonlocal best,best_cost,examined
        examined+=1
        if examined>=15000:return
        if best_cost is not None and cost>best_cost:return
        if pos==len(order):
            sig=tuple(matching[i] for i in range(len(left)))
            if best_cost is None or (cost,sig)<(best_cost,best):
                best_cost=cost;best=sig
            return
        i=order[pos];old=left[i]
        for j,orientation in candidate_matches[i]:
            if j in used:continue
            new=right[j]
            distance=abs(new.r0-old.r0)+abs(new.c0-old.c0)
            # Penalize invented state changes without making any selected
            # target gold available to the final inference policy.
            delta=(distance+5*int(not source_same_value(
                old.color,new.color))+2*int(orientation!="identity"))
            matching[i]=(j,orientation)
            dfs(pos+1,used|{j},matching,cost+delta)
            del matching[i]
    dfs(0,set(),{},0)
    if best is None:return None
    return tuple((l,right[best[i][0]],best[i][1])
                 for i,l in enumerate(left))


def _features(node,nodes,height,width):
    row_rank=sorted(nodes,key=lambda n:(n.r0,n.c0)).index(node)
    col_rank=sorted(nodes,key=lambda n:(n.c0,n.r0)).index(node)
    # Generic scalar node attributes, no named ARC objects or colors.
    return {
        "category":node.color,
        "area":node.area,
        "height":node.h,
        "width":node.w,
        "row_rank":row_rank,
        "col_rank":col_rank,
        "left_half":int(2*node.c0<width),
        "top_half":int(2*node.r0<height),
        "bbox_aspect":(node.h,node.w),
        "shape":node.shape,
    }


def _key(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def _choose_law(source_pairs):
    all_examples=[]
    for inp,out in source_pairs:
        if not _rect(inp) or not _rect(out):
            return None
        if len(inp)!=len(out) or len(inp[0])!=len(out[0]):
            return None
        bg=_mode(inp)
        if bg is None or not source_same_value(bg,_mode(out)):
            return None
        pairs=_pair_nodes(inp,out,bg)
        if pairs is None:return None
        original_nodes=_nodes(inp,bg)
        for src,dst,orientation in pairs:
            action=(dst.r0-src.r0,dst.c0-src.c0,dst.color,
                    orientation)
            all_examples.append(
                (_features(src,original_nodes,len(inp),len(inp[0])),
                 action))
    if not all_examples or all(a==(0,0,f["category"],"identity")
                                for f,a in all_examples):
        return None
    keys=("global","category","area","height","width","row_rank",
          "col_rank","left_half","top_half","bbox_aspect","shape")
    choices=[]
    for key in keys:
        mapping={}
        supports=Counter()
        good=True
        for features,action in all_examples:
            value="ALL" if key=="global" else features[key]
            # Native hashable feature values (int/str/tuple) preserve typed
            # equality at code generation and runtime. Do NOT stringify them:
            # a str encoding mismatch previously made all rules unreachable.
            if value in mapping and mapping[value]!=action:
                good=False;break
            mapping[value]=action
            supports[value]+=1
        if not good or len(mapping)>10:continue
        if any(n<2 for n in supports.values()):
            # Each learned branch must receive repeat SOURCE evidence.
            # A unique object identity is not a transferable rule.
            continue
        if key!="global" and len(mapping)<=1:
            continue
        cost=8+len(mapping)*6+(0 if key=="global" else 3)
        choices.append((cost,key,mapping))
    if not choices:return None
    choices.sort(key=lambda c:(c[0],c[1]))
    return choices[0]


def _compiled_program(key,mapping):
    # Compile the learned correspondence into ordinary Python. Only fixed
    # extraction code is human-authored; guards and action parameters are
    # generated from independently observed source node relations.
    # Color/area/rank features share a common feature template.
    lookup={k:v for k,v in mapping.items()}
    # Source must fit the sandbox's existing 6000-byte code cap.
    code=(
        "def transform(x):\n"
        "    h=len(x)\n"
        "    w=len(x[0])\n"
        "    counts={}\n"
        "    for row in x:\n"
        "        for v in row:\n"
        "            counts[v]=counts.get(v,0)+1\n"
        "    bg=max(counts,key=counts.get)\n"
        "    seen={}\n"
        "    nodes=[]\n"
        "    for r in range(h):\n"
        "        for c in range(w):\n"
        "            color=x[r][c]\n"
        "            if color==bg or seen.get((r,c),False):\n"
        "                continue\n"
        "            stack=[(r,c)]\n"
        "            seen[(r,c)]=True\n"
        "            pts=[]\n"
        "            while stack:\n"
        "                y,z=stack.pop()\n"
        "                pts.append((y,z))\n"
        "                for yy,xx in ((y-1,z),(y+1,z),(y,z-1),(y,z+1)):\n"
        "                    if 0<=yy<h and 0<=xx<w and not seen.get((yy,xx),False) and x[yy][xx]==color:\n"
        "                        seen[(yy,xx)]=True\n"
        "                        stack.append((yy,xx))\n"
        "            r0=min(p[0] for p in pts)\n"
        "            c0=min(p[1] for p in pts)\n"
        "            rh=max(p[0] for p in pts)-r0+1\n"
        "            cw=max(p[1] for p in pts)-c0+1\n"
        "            shape=tuple(sorted((p[0]-r0,p[1]-c0) for p in pts))\n"
        "            nodes.append((color,pts,r0,c0,rh,cw,shape))\n"
        "    row_sorted=sorted(nodes,key=lambda n:(n[2],n[3]))\n"
        "    col_sorted=sorted(nodes,key=lambda n:(n[3],n[2]))\n"
        "    out=[[bg for c in range(w)] for r in range(h)]\n"
        f"    mapping={repr(lookup)}\n"
        "    for node in nodes:\n"
        "        color,pts,r0,c0,rh,cw,shape=node\n"
        f"        key={repr(key)}\n"
        "        if key=='global':val='ALL'\n"
        "        elif key=='category':val=color\n"
        "        elif key=='area':val=len(pts)\n"
        "        elif key=='height':val=rh\n"
        "        elif key=='width':val=cw\n"
        "        elif key=='row_rank':val=row_sorted.index(node)\n"
        "        elif key=='col_rank':val=col_sorted.index(node)\n"
        "        elif key=='left_half':val=int(2*c0<w)\n"
        "        elif key=='top_half':val=int(2*r0<h)\n"
        "        elif key=='bbox_aspect':val=(rh,cw)\n"
        "        else:val=shape\n"
        "        if val not in mapping:\n"
        "            return x\n"
        "        dr,dc,dest,orientation=mapping[val]\n"
        "        rel=[]\n"
        "        for y,z in pts:\n"
        "            dy=y-r0\n"
        "            dx=z-c0\n"
        "            if orientation=='identity':a,b=dy,dx\n"
        "            elif orientation=='turn90':a,b=dx,-dy\n"
        "            elif orientation=='turn180':a,b=-dy,-dx\n"
        "            elif orientation=='turn270':a,b=-dx,dy\n"
        "            elif orientation=='reflect_rows':a,b=-dy,dx\n"
        "            elif orientation=='reflect_cols':a,b=dy,-dx\n"
        "            elif orientation=='swap_axes':a,b=dx,dy\n"
        "            else:a,b=-dx,-dy\n"
        "            rel.append((a,b))\n"
        "        mr=min(v[0] for v in rel)\n"
        "        mc=min(v[1] for v in rel)\n"
        "        for a,b in rel:\n"
        "            yy=r0+dr+a-mr\n"
        "            xx=c0+dc+b-mc\n"
        "            if 0<=yy<h and 0<=xx<w:\n"
        "                out[yy][xx]=dest\n"
        "    return out"
    )
    return validate_code(code)


def induce_object_graph_factors(source_pairs,*,max_candidates=4):
    """Return a generic graph-correspondence rule iff its SOURCE fit is exact."""
    if not 2<=len(source_pairs)<=32 or not 1<=max_candidates<=12:
        raise ValueError("bounded source evidence required")
    chosen=_choose_law(source_pairs)
    if chosen is None:return ()
    description,key,mapping=chosen
    try:
        program=_compiled_program(key,mapping)
    except (TypeError,ValueError,OverflowError):
        return ()
    # This is a hypothesis, not certified. The existing GenerativeProgramInventor
    # will execute it on withheld independent SOURCE examples before acceptance.
    return (StructuralFactor(program,
                             "source-inferred-graph-rewrite/"+key,
                             description,len(source_pairs)),)
