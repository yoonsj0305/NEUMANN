"""NEUMANN Q3 object-structure program induction from original grid I/O.

Use classical graph traversal to EXTRACT objects; induce the *selection
relation* and the executable rendering/geometry composition from source I/O.
Only the generic source-inferred AST is new. Segmentation connectivity, feature
vocabulary, ranking, D4 and render operators are human-defined primitives,
so this is bounded language growth, not proof of arbitrary autonomous
representation invention.

No original test labels or domain names are passed to this module.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from time import perf_counter_ns

from .relational_grid_inventor import grid
from . import arc2_meta_grid_reasoner as old


@dataclass(frozen=True)
class Obj:
    cells: frozenset[tuple[int,int]]
    bounds: tuple[int,int,int,int]
    color: int
    area: int

    @property
    def height(self): return self.bounds[1]-self.bounds[0]+1
    @property
    def width(self): return self.bounds[3]-self.bounds[2]+1


@lru_cache(maxsize=1024)
def extract(g, background, *, diagonal=False, mixed_colors=False):
    h,w=len(g),len(g[0])
    found=set()
    result=[]
    offsets=[(-1,0),(0,-1),(0,1),(1,0)]
    if diagonal:
        offsets += [(-1,-1),(-1,1),(1,-1),(1,1)]
    for r in range(h):
        for c in range(w):
            if (r,c) in found or g[r][c]==background:continue
            original=g[r][c]
            pending=[(r,c)]
            found.add((r,c))
            pixels=[]
            while pending:
                y,x=pending.pop()
                pixels.append((y,x))
                for dy,dx in offsets:
                    yy,xx=y+dy,x+dx
                    if not (0<=yy<h and 0<=xx<w) or (yy,xx) in found:
                        continue
                    if g[yy][xx]==background:continue
                    if not mixed_colors and g[yy][xx]!=original:continue
                    found.add((yy,xx))
                    pending.append((yy,xx))
            ys=[p[0] for p in pixels]
            xs=[p[1] for p in pixels]
            color=min(Counter(g[y][x] for y,x in pixels).items(),
                      key=lambda kv:(-kv[1],kv[0]))[0]
            result.append(Obj(frozenset(pixels),
                              (min(ys),max(ys),min(xs),max(xs)),
                              color,len(pixels)))
    return tuple(result)


def attribute(o,name,objects,shape):
    r0,r1,c0,c1=o.bounds
    if name=="area":return o.area
    if name=="height":return o.height
    if name=="width":return o.width
    if name=="color":return o.color
    if name=="top":return r0
    if name=="left":return c0
    if name=="bottom":return r1
    if name=="right":return c1
    if name=="fill":return o.area*1000//(o.width*o.height)
    if name=="center_distance":
        return abs(r0+r1-(shape[0]-1))+abs(c0+c1-(shape[1]-1))
    if name=="border":
        return int(r0==0 or c0==0 or r1==shape[0]-1 or c1==shape[1]-1)
    if name=="color_frequency":
        return sum(x.area for x in objects if x.color==o.color)
    if name=="color_object_count":
        return sum(x.color==o.color for x in objects)
    raise ValueError("unknown object feature")


FEATURES=("area","height","width","color","top","left","bottom","right",
          "fill","center_distance","border","color_frequency",
          "color_object_count")
RANKS=("min","max","second_min","second_max","median")
RENDERS=("crop_component","crop_canvas","crop_solid","crop_mask",
         "keep_component","erase_component","fill_bounds",
         "keep_mask","scalar_color","scalar_size")
D4=("identity","flip_lr","flip_ud","transpose",
    "rotate90","rotate180","rotate270","anti_transpose")
SCALES=(1,2,3)


def select_object(objects,shape,feature,rank):
    if not objects:return None
    ordered=sorted(objects,key=lambda o:(
        attribute(o,feature,objects,shape),o.bounds,o.color))
    if rank=="min":return ordered[0]
    if rank=="max":return ordered[-1]
    if rank=="second_min":return ordered[1] if len(ordered)>=2 else None
    if rank=="second_max":return ordered[-2] if len(ordered)>=2 else None
    if rank=="median":return ordered[(len(ordered)-1)//2]
    raise ValueError("invalid object selection rank")


def render(g,obj,background,mode):
    h,w=len(g),len(g[0])
    r0,r1,c0,c1=obj.bounds
    if mode=="scalar_color":return ((obj.color,),)
    if mode=="scalar_size":
        if not 0<=obj.area<=9:return None
        return ((obj.area,),)
    if mode.startswith("crop_"):
        if mode=="crop_solid":
            return tuple(tuple(obj.color for _ in range(c0,c1+1))
                         for _ in range(r0,r1+1))
        if mode=="crop_component":
            return tuple(tuple(g[r][c] if (r,c) in obj.cells else background
                               for c in range(c0,c1+1))
                         for r in range(r0,r1+1))
        if mode=="crop_mask":
            return tuple(tuple(1 if (r,c) in obj.cells else 0
                               for c in range(c0,c1+1))
                         for r in range(r0,r1+1))
        if mode=="crop_canvas":
            return tuple(tuple(g[r][c] for c in range(c0,c1+1))
                         for r in range(r0,r1+1))
    output=[list(row) for row in g]
    for r in range(h):
        for c in range(w):
            if mode=="keep_component" and (r,c) not in obj.cells:
                output[r][c]=background
            elif mode=="keep_mask":
                output[r][c]=1 if (r,c) in obj.cells else 0
            elif mode=="erase_component" and (r,c) in obj.cells:
                output[r][c]=background
            elif mode=="fill_bounds" and r0<=r<=r1 and c0<=c<=c1:
                output[r][c]=obj.color
    return tuple(tuple(row) for row in output)


def scale(g,n):
    if n==1:return g
    h,w=len(g),len(g[0])
    if h*n>30 or w*n>30:return None
    return tuple(tuple(v for v in row for _ in range(n))
                 for row in g for _ in range(n))


@dataclass(frozen=True)
class ObjectProgram:
    bg_policy: str
    diagonal: bool
    mixed_colors: bool
    feature: str
    rank: str
    render_mode: str
    transform: str
    scale_factor: int

    @property
    def ast(self):
        return ("object_transform",
                ("extract","classical_components",self.bg_policy,
                 self.diagonal,self.mixed_colors),
                ("invented_selector",self.feature,self.rank),
                ("render",self.render_mode),
                ("dihedral",self.transform),
                ("scale",self.scale_factor))

    def apply(self,source):
        g=grid(source)
        if self.bg_policy=="zero":
            background=0
        elif self.bg_policy=="modal":
            hist=Counter(v for row in g for v in row)
            background=min(hist,key=lambda v:(-hist[v],v))
        else:
            raise ValueError("unsupported source background")
        objects=extract(g,background,diagonal=self.diagonal,
                        mixed_colors=self.mixed_colors)
        chosen=select_object(objects,(len(g),len(g[0])),self.feature,self.rank)
        if chosen is None:return None
        out=render(g,chosen,background,self.render_mode)
        if out is None:return None
        out=old.d4(out,self.transform)
        out=scale(out,self.scale_factor)
        return out if out is not None else None


@dataclass(frozen=True)
class ObjectInvention:
    programs:tuple[ObjectProgram,...]
    source_checks:int
    elapsed_ms:float
    source_fit:bool
    verified_source_count:int

    def apply(self,g):
        return tuple(p.apply(g) for p in self.programs)


def _dim(g):return len(g),len(g[0])


def _compatible(output_dim,selected_dim,mode,transform,scale_factor):
    if mode.startswith("crop_"):
        h,w=selected_dim
    elif mode.startswith("scalar_"):
        h,w=1,1
    else:
        return True  # same canvas size checked in execution
    if transform in ("rotate90","rotate270","transpose","anti_transpose"):
        h,w=w,h
    return (h*scale_factor,w*scale_factor)==output_dim


class ObjectGrammarInventor:
    """Source-only generate and independently verify a new object AST.

    Ranking primitive count is finite by design, with fixed caps. A
    held-out author original is necessary to assess external generality.
    """

    def __init__(self,max_candidates=300000,max_source_ms=500):
        if type(max_candidates) is not int or max_candidates<1:
            raise ValueError("finite candidate budget required")
        if type(max_source_ms) not in (int,float) or not 1<=max_source_ms<=120000:
            raise ValueError("finite source time required")
        self.max_candidates=max_candidates
        self.max_source_ms=max_source_ms

    def invent(self,demonstrations,*,verification=(),max_programs=2):
        start=perf_counter_ns()
        train=tuple((grid(x),grid(y)) for x,y in demonstrations)
        checks=tuple((grid(x),grid(y)) for x,y in verification)
        if len(train)<2 or not checks:
            raise ValueError("2 source I/O and >=1 independent SOURCE verifier required")
        if max_programs not in (1,2):
            raise ValueError("at most two competing original predictions")
        deadline=start+int(self.max_source_ms*1e6)
        counter=0
        found=[]
        seen_program_signatures=set()
        # Source-relative background, connectivity, color partitions.
        for bg_policy in ("zero","modal"):
            for diagonal in (False,True):
                for mixed_colors in (False,True):
                    groups=[]
                    for g,y in train:
                        hist=Counter(v for row in g for v in row)
                        bg=(0 if bg_policy=="zero" else
                            min(hist,key=lambda v:(-hist[v],v)))
                        objects=extract(g,bg,diagonal=diagonal,
                                        mixed_colors=mixed_colors)
                        groups.append((g,y,bg,objects))
                    if not all(objects for g,y,bg,objects in groups):
                        continue
                    for feature in FEATURES:
                        for rank in RANKS:
                            selected=[select_object(objects,_dim(g),
                                feature,rank) for g,y,bg,objects in groups]
                            if any(x is None for x in selected):
                                continue
                            for mode in RENDERS:
                                rendered=[]
                                skip=False
                                for (g,y,bg,objects),obj in zip(groups,selected):
                                    temp=render(g,obj,bg,mode)
                                    if temp is None:
                                        skip=True;break
                                    rendered.append(temp)
                                if skip:continue
                                for transform in D4:
                                    transforms=tuple(old.d4(x,transform)
                                                     for x in rendered)
                                    for factor in SCALES:
                                        if any(not _compatible(_dim(y),
                                                (obj.height,obj.width),
                                                mode,transform,factor)
                                               for (g,y,bg,objects),obj
                                               in zip(groups,selected)):
                                            continue
                                        if any(_dim(y)!=
                                               (_dim(o)[0]*factor,
                                                _dim(o)[1]*factor)
                                               for o,(g,y,bg,objs) in
                                               zip(transforms,groups)):
                                            continue
                                        counter+=1
                                        if counter>self.max_candidates or (
                                                perf_counter_ns()>deadline):
                                            return ObjectInvention(
                                                tuple(found),counter,
                                                (perf_counter_ns()-start)/1e6,
                                                bool(found),len(checks))
                                        if any(scale(o,factor)!=y for o,
                                               (g,y,bg,objs) in
                                               zip(transforms,groups)):
                                            continue
                                        program=ObjectProgram(
                                            bg_policy,diagonal,mixed_colors,
                                            feature,rank,mode,transform,factor)
                                        try:
                                            if not all(program.apply(x)==y
                                                       for x,y in checks):
                                                continue
                                        except (ValueError,TypeError):
                                            continue
                                        signature=tuple(program.apply(x)
                                                        for x,y in checks)
                                        if signature in seen_program_signatures:
                                            continue
                                        seen_program_signatures.add(signature)
                                        found.append(program)
                                        if len(found)>=max_programs:
                                            return ObjectInvention(
                                                tuple(found),counter,
                                                (perf_counter_ns()-start)/1e6,
                                                True,len(checks))
        return ObjectInvention(tuple(found),counter,
                               (perf_counter_ns()-start)/1e6,bool(found),
                               len(checks))
