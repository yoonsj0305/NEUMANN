"""Q3 source-inferred symbolic reducer over a generic object set.

Input/output invariants determine which aggregate statistic selects a
non-background connected component and how to render its selected color.
This is a general GROUP -> ARGMAX -> PROJECT expression, not an ARC
task-ID-specific function, a code cache, or an independently invented
meta-grammar. The *program and parameters* are inferred from SOURCE.

Accepted candidates still require external independent SOURCE verification
in the existing no-network Docker sandbox, then SHA-frozen original TEST.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .open_program_inventor import validate_code,source_same_value
from .q3_object_graph_invention import _nodes
from .q3_structure_factorization import StructuralFactor
from .q3_relational_predicate_invention import _rect,_bg


def _score(node,feature):
    if feature=="area":return node.area
    if feature=="bbox_area":return node.h*node.w
    if feature=="height":return node.h
    if feature=="width":return node.w
    if feature=="density":return node.area/(node.h*node.w)
    if feature=="perimeter":
        points=set(node.points)
        return sum(
            (r+dr,c+dc) not in points for r,c in points
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))
    raise ValueError("noncausal feature")


def _consistent_selection(pairs,feature):
    selected=[]
    for x,y in pairs:
        bg=_bg(x)
        nodes=_nodes(x,bg)
        if not nodes:return None
        values=[_score(n,feature) for n in nodes]
        best=max(values)
        winners=[n for n,v in zip(nodes,values) if v==best]
        # A nondeterministic tie cannot establish a causal role law.
        if len(winners)!=1:return None
        choice=winners[0]
        if not source_same_value(choice.color,y[0][0]):
            return None
        selected.append(choice)
    return selected


def _code(feature,geometry,oh,ow):
    # The emitted syntax is a single safe transform(x), using only approved
    # Python builtins. No imports, subprocess, eval, state or network.
    text=(
        "def transform(x):\n"
        f"    feature={repr(feature)}\n"
        f"    geometry={repr(geometry)}\n"
        f"    out_h={int(oh)}\n"
        f"    out_w={int(ow)}\n"
        "    if not x or not x[0]:return x\n"
        "    h=len(x)\n"
        "    w=len(x[0])\n"
        "    counts={}\n"
        "    for row in x:\n"
        "        for value in row:counts[value]=counts.get(value,0)+1\n"
        "    bg=sorted(counts,key=lambda v:(-counts[v],str(v)))[0]\n"
        "    visited={}\n"
        "    nodes=[]\n"
        "    for r in range(h):\n"
        "        for c in range(w):\n"
        "            color=x[r][c]\n"
        "            if color==bg or (r,c) in visited:continue\n"
        "            stack=[(r,c)]\n"
        "            visited[(r,c)]=True\n"
        "            points=[]\n"
        "            while stack:\n"
        "                rr,cc=stack.pop()\n"
        "                points.append((rr,cc))\n"
        "                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):\n"
        "                    yy=rr+dy\n"
        "                    xx=cc+dx\n"
        "                    if 0<=yy<h and 0<=xx<w and (yy,xx) not in visited and x[yy][xx]==color:\n"
        "                        visited[(yy,xx)]=True\n"
        "                        stack.append((yy,xx))\n"
        "            minr=min(p[0] for p in points)\n"
        "            maxr=max(p[0] for p in points)\n"
        "            minc=min(p[1] for p in points)\n"
        "            maxc=max(p[1] for p in points)\n"
        "            hh=maxr-minr+1\n"
        "            ww=maxc-minc+1\n"
        "            area=len(points)\n"
        "            if feature=='area':score=area\n"
        "            elif feature=='bbox_area':score=hh*ww\n"
        "            elif feature=='height':score=hh\n"
        "            elif feature=='width':score=ww\n"
        "            elif feature=='density':score=area/(hh*ww)\n"
        "            elif feature=='perimeter':\n"
        "                parts={p:True for p in points}\n"
        "                score=0\n"
        "                for rr,cc in points:\n"
        "                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):\n"
        "                        if (rr+dy,cc+dx) not in parts:score+=1\n"
        "            else:return x\n"
        "            nodes.append((score,color,hh,ww))\n"
        "    if not nodes:return x\n"
        "    best=max(z[0] for z in nodes)\n"
        "    winning=[z for z in nodes if z[0]==best]\n"
        "    if len(winning)!=1:return x\n"
        "    selected=winning[0]\n"
        "    if geometry=='bbox':\n"
        "        out_h=selected[2]\n"
        "        out_w=selected[3]\n"
        "    if out_h<1 or out_w<1 or out_h>30 or out_w>30:return x\n"
        "    return [[selected[1] for c in range(out_w)] for r in range(out_h)]"
    )
    return validate_code(text)


def induce_relational_reducers(source_pairs,*,max_candidates=4):
    if not 2<=len(source_pairs)<=32 or not 1<=max_candidates<=12:
        raise ValueError("bounded SOURCE-only aggregate invention required")
    pairs=tuple((x,y) for x,y in source_pairs)
    if not all(_rect(x) and _rect(y) for x,y in pairs):return ()
    if not all(all(source_same_value(y[0][0],v)
                   for row in y for v in row) for x,y in pairs):
        return ()
    # A single fixed output token is not evidence for a generic
    # source-selected object representation; reject constant-answer fits.
    target_colors={repr(y[0][0]) for x,y in pairs}
    if len(target_colors)<2:return ()
    output_shapes={(len(y),len(y[0])) for x,y in pairs}
    proposals=[]
    for feature in ("area","bbox_area","height","width","perimeter","density"):
        selected=_consistent_selection(pairs,feature)
        if selected is None:continue
        geometry=None
        if len(output_shapes)==1:
            oh,ow=next(iter(output_shapes))
            geometry=("constant",oh,ow)
        elif all((len(y),len(y[0]))==(n.h,n.w)
                 for (_,y),n in zip(pairs,selected)):
            geometry=("bbox",0,0)
        if geometry is None:continue
        g,h,w=geometry
        program=_code(feature,g,h,w)
        proposals.append(StructuralFactor(
            program,"source-induced-object-argmax-project/"+feature,
            6+int(feature not in ("area","height","width"))+
              2*int(g=="constant"),len(pairs)))
    proposals.sort(key=lambda v:(v.description_length,v.representation))
    return tuple(proposals[:max_candidates])
