"""NEUMANN: source-driven relational representation and executable rule invention.

Unlike a fixed grid transformation vocabulary, this engine *constructs new
Boolean spatial predicates from original positive/negative cell changes*.
This is genuine bounded program-language growth: conditions are synthesized
as a Boolean set-cover over typed geometric/graph features, then wrapped in
an executable cell rewrite. It also searches structural color-role outputs.

This is NOT universal Q3: feature extractors, set-cover logic, relation
operators, and default actions remain human-coded. Only original example
I/O supplies the new rule's predicates and parameters.

A demonstration fit does not prove a withheld test. Always score it on
unseen original test grids separately, after the program is frozen.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import math
import time

Grid=tuple[tuple[int,...],...]
MAX_PIXELS=900
MAX_SOURCE_CELLS=4200

class SearchBudgetExceeded(Exception):
    pass

def _deadline(deadline):
    if deadline is not None and time.perf_counter_ns()>deadline:
        raise SearchBudgetExceeded('causal representation search cost cap')


def grid(data):
    if not 1<=len(data)<=30 or not 1<=len(data[0])<=30:
        raise ValueError("invalid grid size")
    g=tuple(tuple(int(x) for x in row) for row in data)
    if any(len(r)!=len(g[0]) or any(x<0 or x>9 for x in r) for r in g):
        raise ValueError("invalid grid values")
    return g

def _color_roles(g):
    c=Counter(x for row in g for x in row)
    nz={k:v for k,v in c.items() if k!=0}
    role={"top_left":g[0][0],"bottom_right":g[-1][-1],
          "mode":min(c,key=lambda v:(-c[v],v)),
          "rare":min(c,key=lambda v:(c[v],v)),
          "min":min(c),"max":max(c)}
    if nz:
        role.update(
          mode_nonzero=min(nz,key=lambda v:(-nz[v],v)),
          rare_nonzero=min(nz,key=lambda v:(nz[v],v)),
          min_nonzero=min(nz),max_nonzero=max(nz))
    comps=_components(g)
    if comps:
        for prefix,cho in (("largest",max),("smallest",min)):
            selected=cho(comps,key=lambda x:(x["size"],-x["r0"],-x["c0"]))
            role[prefix+"_component_color"]=selected["color"]
        by_col=Counter(z["color"] for z in comps)
        role["most_components_color"]=min(by_col,key=lambda k:(-by_col[k],k))
        role["least_components_color"]=min(by_col,key=lambda k:(by_col[k],k))
    return role

def _components(g):
    h,w=len(g),len(g[0]);seen=set();out=[]
    for i in range(h):
        for j in range(w):
            if (i,j) in seen:continue
            col=g[i][j]
            queue=[(i,j)];seen.add((i,j));part=[]
            while queue:
                r,c=queue.pop()
                part.append((r,c))
                for yy,xx in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if 0<=yy<h and 0<=xx<w and (yy,xx) not in seen and g[yy][xx]==col:
                        seen.add((yy,xx));queue.append((yy,xx))
            r0=min(r for r,c in part);r1=max(r for r,c in part)
            c0=min(c for r,c in part);c1=max(c for r,c in part)
            out.append({"color":col,"cells":part,"size":len(part),
                        "r0":r0,"r1":r1,"c0":c0,"c1":c1})
    return out

def _fields(g):
    """A typed object/coordinate graph: a feature vector for EVERY pixel.
    Output answers never participate in generating these input features.
    """
    h,w=len(g),len(g[0])
    counts=Counter(v for row in g for v in row)
    roles=_color_roles(g)
    nonzero=[(r,c) for r in range(h) for c in range(w) if g[r][c]!=0]
    if nonzero:
        bbox=(min(r for r,c in nonzero),max(r for r,c in nonzero),
              min(c for r,c in nonzero),max(c for r,c in nonzero))
    else:bbox=None
    comp_map={}
    for component in _components(g):
        for x in component["cells"]:comp_map[x]=component
    values=[]
    for r in range(h):
        for c in range(w):
            v=g[r][c];comp=comp_map[(r,c)]
            neighbors=[g[rr][cc] for rr,cc in
                       ((r-1,c),(r+1,c),(r,c-1),(r,c+1))
                       if 0<=rr<h and 0<=cc<w]
            diag=[g[rr][cc] for rr,cc in
                  ((r-1,c-1),(r-1,c+1),(r+1,c-1),(r+1,c+1))
                  if 0<=rr<h and 0<=cc<w]
            feats={
                "color":v,
                "row":r,"col":c,
                "dist_top":r,"dist_left":c,
                "dist_bottom":h-1-r,"dist_right":w-1-c,
                "dist_r_edge":min(r,h-1-r),
                "dist_c_edge":min(c,w-1-c),
                "on_border":int(r in (0,h-1) or c in (0,w-1)),
                "on_corner":int(r in (0,h-1) and c in (0,w-1)),
                "diagonal":int(r==c),
                "anti_diagonal":int(r+c==w-1),
                "row_parity":r%2,"col_parity":c%2,
                "checker_parity":(r+c)%2,
                "row_color_count":sum(x==v for x in g[r]),
                "col_color_count":sum(g[y][c]==v for y in range(h)),
                "row_nonzero_count":sum(x!=0 for x in g[r]),
                "col_nonzero_count":sum(g[y][c]!=0 for y in range(h)),
                "color_count":counts[v],
                "component_size":comp["size"],
                "component_h":comp["r1"]-comp["r0"]+1,
                "component_w":comp["c1"]-comp["c0"]+1,
                "component_is_solid":int(comp["size"]==(
                    comp["r1"]-comp["r0"]+1)*(comp["c1"]-comp["c0"]+1)),
                "component_border":int(comp["r0"]==0 or comp["c0"]==0
                    or comp["r1"]==h-1 or comp["c1"]==w-1),
                "component_pixel_boundary":int(r in (comp["r0"],comp["r1"])
                    or c in (comp["c0"],comp["c1"])),
                "same_neighbors":sum(x==v for x in neighbors),
                "different_neighbors":sum(x!=v for x in neighbors),
                "nonzero_neighbors":sum(x!=0 for x in neighbors),
                "same_diagonals":sum(x==v for x in diag),
                "different_diagonals":sum(x!=v for x in diag),
                "nonzero_diagonals":sum(x!=0 for x in diag),
                "mirror_lr_same":int(v==g[r][w-1-c]),
                "mirror_ud_same":int(v==g[h-1-r][c]),
            }
            if bbox:
                r0,r1,c0,c1=bbox
                feats.update(bbox_inside=int(r0<=r<=r1 and c0<=c<=c1),
                    bbox_edge=int((r in (r0,r1) and c0<=c<=c1) or
                                  (c in (c0,c1) and r0<=r<=r1)))
            for role,col in roles.items():
                feats["eq_role_"+role]=int(v==col)
                feats["adj_role_"+role]=sum(x==col for x in neighbors)
            values.append(feats)
    return values

def _features_for_demos(demo):
    rows=[];outputs=[]
    for inp,out in demo:
        if len(inp)!=len(out) or len(inp[0])!=len(out[0]):
            return None
        feats=_fields(inp)
        rows.extend(feats)
        outputs.extend((inp[r][c],out[r][c],inp)
                       for r in range(len(inp)) for c in range(len(inp[0])))
        if len(rows)>MAX_SOURCE_CELLS:return None
    return rows,outputs

def _guards(features, positives,deadline=None):
    """Invent relational comparisons from actual positive/negative feature
    distributions. Every predicate is a newly generated executable AST;
    NONE of the resulting formulas is hardcoded before demonstrations.
    """
    if not features or not positives:return []
    names=sorted(features[0])
    n=len(features)
    answer=[]
    for name in names:
        _deadline(deadline)
        vector=[x.get(name,0) for x in features]
        unique=sorted(set(vector))
        if len(unique)>25:
            support=sorted({vector[i] for i in positives})
            thresholds=sorted(set((support[0],support[-1],0,1,2,3)))
        else:
            thresholds=unique
        for value in thresholds:
            for kind in ("eq","le","ge"):
                # Equal-range predicates duplicate each other; retaining
                # only one representation reduces meta program search cost.
                if len(unique)==1 and kind!="eq":continue
                if kind=="eq":
                    bits=sum(1<<i for i,v in enumerate(vector) if v==value)
                elif kind=="le":
                    bits=sum(1<<i for i,v in enumerate(vector) if v<=value)
                else:
                    bits=sum(1<<i for i,v in enumerate(vector) if v>=value)
                if bits==0 or bits==(1<<n)-1:continue
                pred=(name,kind,int(value))
                # Prefer relational color roles to fixed literal colors or
                # absolute row numbers, which overfit source coordinates.
                complexity=(1.0 if "role" in name else 1.4 if
                    name.startswith(("component_","same_","different_")) else
                    1.8 if "count" in name else 2.6 if name in
                    ("row","col","color","dist_top","dist_left",
                     "dist_bottom","dist_right") else 1.6)
                answer.append((pred,bits,complexity))
    # Exact masks are identical predicates; retain simplest one only.
    dedup={}
    for pred,bits,complexity in answer:
        key=bits
        if key not in dedup or (complexity,pred)<(dedup[key][2],dedup[key][0]):
            dedup[key]=(pred,bits,complexity)
    return sorted(dedup.values(),key=lambda x:(x[2],x[0]))

def _cover_rule(features,positives,negatives,max_clauses=3,deadline=None):
    if not positives:return None
    if not negatives:
        return ((('__always__','eq',1),),)
    P=sum(1<<i for i in positives)
    N=sum(1<<i for i in negatives)
    atomics=_guards(features,positives,deadline)
    compatible=[]
    for pred,bits,cost in atomics:
        hit=bits & P
        if hit and not bits&N:compatible.append(((pred,),bits,cost))
    # The candidates are generated by conjunction of two arbitrary
    # observed relational features, not by pre-enumerated ARC templates.
    # Thresholds are dynamically inferred from source labels.
    for i,(p,b,c) in enumerate(atomics):
        if i%16==0:_deadline(deadline)
        if not b&P:continue
        for q,d,e in atomics[i+1:]:
            both=b&d
            if both&P and not both&N:
                compatible.append(((p,q),both,c+e+.15))
    if not compatible:return None
    remaining=P;clauses=[]
    for _ in range(max_clauses):
        chosen=None;score=None
        for predicates,bits,cost in compatible:
            gain=(bits&remaining).bit_count()
            if not gain:continue
            rank=(-gain/cost,cost,tuple(predicates))
            if score is None or rank<score:
                chosen=(predicates,bits);score=rank
        if chosen is None:break
        clauses.append(chosen[0])
        remaining &= ~chosen[1]
        if remaining==0:return tuple(clauses)
    return None

def _match(pred,feat):
    name,op,value=pred
    if name=='__always__':return True
    x=feat.get(name,0)
    if op=="eq":return x==value
    if op=="le":return x<=value
    if op=="ge":return x>=value
    raise ValueError("unknown generated relational operator")

def _guard_exec(clauses,feat):
    return any(all(_match(p,feat) for p in clause) for clause in clauses)

def _output_roles(demo):
    # Bind an output-color symbolic role from the DEMONSTRATIONS only, so
    # future unseen input colors can still inherit the correct semantics.
    options=[]
    for role in ("mode","mode_nonzero","rare","rare_nonzero",
                 "min","min_nonzero","max","max_nonzero",
                 "top_left","bottom_right",
                 "largest_component_color","smallest_component_color",
                 "most_components_color","least_components_color"):
        colors=[]
        for inp,out in demo:
            r=_color_roles(inp)
            if role not in r:break
            colors.append(r[role])
        else:options.append((("role",role),colors))
    for color in range(10):
        options.append((("constant",color),[color]*len(demo)))
    return options

def _source_one_step(demo,*,max_guards=3,deadline=None):
    prepared=_features_for_demos(demo)
    if prepared is None:return None
    features,output_rows=prepared
    slices=[];start=0
    for inp,out in demo:
        n=len(inp)*len(inp[0])
        slices.append(slice(start,start+n));start+=n
    best=None;best_cost=math.inf
    for role,colors in _output_roles(demo):
        _deadline(deadline)
        positive=[];negative=[]
        for gi,s in enumerate(slices):
            color=colors[gi]
            for i in range(s.start,s.stop):
                source,target,_=output_rows[i]
                if source!=target and target==color:
                    positive.append(i)
                elif source!=color and target!=color:
                    negative.append(i)
        if not positive:continue
        # For a single-step program, this role must explain ALL changes.
        total_changes=sum(a!=b for a,b,_ in output_rows)
        if len(positive)!=total_changes:continue
        guard=_cover_rule(features,positive,negative,max_guards,deadline)
        if guard is None:continue
        program={"action":role,"guard":guard}
        predictions=[execute(inp,program) for inp,out in demo]
        if not all(p==out for p,(_,out) in zip(predictions,demo)):
            continue
        complexity=sum(len(clause) for clause in guard)
        # Role outputs receive modest simplicity preference, only when
        # supported by actual training-to-training equality.
        cost=complexity*2+len(guard)*.5+(0 if role[0]=="role" else 1)
        if cost<best_cost:
            best=program;best_cost=cost
    return best

def execute(inp,program):
    if program is None:return None
    if program["action"][0]=="role":
        col=_color_roles(inp).get(program["action"][1])
        if col is None:return None
    else:
        col=program["action"][1]
    features=_fields(inp)
    new=[]
    p=0
    for row in inp:
        outrow=[]
        for source in row:
            value=col if _guard_exec(program["guard"],features[p]) else source
            outrow.append(value);p+=1
        new.append(tuple(outrow))
    return tuple(new)

def _source_parallel_parts(demo,max_parts=3,deadline=None):
    """Invent a parallel operator by composing independent source-verified
    relational rewrites, rejecting contradictory proposed pixel values."""
    if any(len(a)!=len(b) or len(a[0])!=len(b[0]) for a,b in demo):
        return None
    changed_colors=[
        {b[r][c] for r in range(len(a)) for c in range(len(a[0]))
         if a[r][c]!=b[r][c]} for a,b in demo]
    if max(map(len,changed_colors),default=0)<2:
        return None
    if max(map(len,changed_colors),default=0)>max_parts:
        return None  # one rule supplies only one target color per example
    # A mathematically necessary role-cover lower bound comes BEFORE any
    # expensive pixel-level causal-guard search. Every changed pixel must
    # be explained by one of at most max_parts role-bound actions.
    positions=[]
    for gi,(a,b) in enumerate(demo):
        positions.extend((gi,b[r][c]) for r in range(len(a))
                         for c in range(len(a[0])) if a[r][c]!=b[r][c])
    candidates=_output_roles(demo)
    covers=[]
    for role,colors in candidates:
        covers.append(sum(1<<i for i,(gi,col) in enumerate(positions)
                          if col==colors[gi]))
    full=(1<<len(positions))-1
    if not covers or not any(
            (covers[i]|covers[j])==full
            for i in range(len(covers)) for j in range(i,len(covers))):
        # Some problems genuinely need three actions; before abstaining,
        # check exactly those distinct semantic color-role triples.
        if not any((covers[i]|covers[j]|covers[k])==full
                   for i in range(len(covers))
                   for j in range(i,len(covers))
                   for k in range(j,len(covers))):
            return None
    _deadline(deadline)
    prepared=_features_for_demos(demo)
    if prepared is None:return None
    features,output_rows=prepared
    slices=[];start=0
    for a,b in demo:
        n=len(a)*len(a[0]);slices.append(slice(start,start+n));start+=n
    changed={i for i,(a,b,_) in enumerate(output_rows) if a!=b}
    actions=[]
    for role,colors in _output_roles(demo):
        _deadline(deadline)
        positive=[];negative=[]
        for gi,span in enumerate(slices):
            target_color=colors[gi]
            for i in range(span.start,span.stop):
                src,tgt,_=output_rows[i]
                if src!=tgt and tgt==target_color:
                    positive.append(i)
                elif src!=target_color and tgt!=target_color:
                    negative.append(i)
        if not positive:continue
        guard=_cover_rule(features,positive,negative,max_clauses=3,deadline=deadline)
        if guard is None:continue
        part={"action":role,"guard":guard}
        generated=[execute(a,part) for a,b in demo]
        if any(p is None for p in generated):continue
        coverage=set();ok=True;at=0
        for (a,b),proposal in zip(demo,generated):
            for r in range(len(a)):
                for c in range(len(a[0])):
                    if proposal[r][c]!=a[r][c]:
                        if proposal[r][c]!=b[r][c]:ok=False
                        else:coverage.add(at)
                    at+=1
        if not ok or not coverage:continue
        complexity=(sum(len(clause) for clause in guard)
                    +.5*len(guard)+int(role[0]=="constant"))
        actions.append((part,coverage,complexity))
    if len(actions)<2:return None
    actions.sort(key=lambda x:(-len(x[1])/max(1,x[2]),x[2],str(x[0])))
    actions=actions[:14]
    best=None;best_cost=float("inf")
    for k in range(2,min(max_parts,len(actions))+1):
        for positions in itertools.combinations(range(len(actions)),k):
            coverage=set().union(*(actions[j][1] for j in positions))
            if not changed.issubset(coverage):continue
            parts=[actions[j][0] for j in positions]
            if all(_parallel_predict(a,parts)==b for a,b in demo):
                cost=sum(actions[j][2] for j in positions)+k
                if cost<best_cost:best=parts;best_cost=cost
        if best is not None:
            return {"kind":"parallel_relational_rewrites","parts":best}
    return None


def _parallel_predict(inp,parts):
    candidates=[execute(inp,p) for p in parts]
    if any(p is None for p in candidates):return None
    final=[]
    for r,row in enumerate(inp):
        out=[]
        for c,v in enumerate(row):
            updates={p[r][c] for p in candidates if p[r][c]!=v}
            if len(updates)>1:return None
            out.append(next(iter(updates)) if updates else v)
        final.append(tuple(out))
    return tuple(final)


def induce(demo,deadline=None):
    """Return a new executable source-grounded program, never just labels."""
    if not demo or any(len(x)*len(x[0])>MAX_PIXELS for x,y in demo):
        return None
    out=_source_one_step(demo,deadline=deadline)
    if out:return {"kind":"cell_relational_rewrite","program":out}
    _deadline(deadline)
    multi=_source_parallel_parts(demo,deadline=deadline)
    if multi:return multi
    # Shape-changing role abstraction: infer output as a global color
    # selected by a relational statistic of the new input.
    if all(len(y)==1 and len(y[0])==1 for _,y in demo):
        for role,colors in _output_roles(demo):
            if all(color==y[0][0] for color,(_,y) in zip(colors,demo)):
                return {"kind":"select_color_role","role":role}
    return None

def predict(inp,method):
    if method is None:return None
    if method["kind"]=="cell_relational_rewrite":
        return execute(inp,method["program"])
    if method["kind"]=="parallel_relational_rewrites":
        return _parallel_predict(inp,method["parts"])
    if method["kind"]=="select_color_role":
        typ,val=method["role"]
        color=val if typ=="constant" else _color_roles(inp).get(val)
        return ((color,),) if color is not None else None
    raise ValueError("unsupported discovered method")

def check_demonstrations(demo,method):
    return bool(method) and all(predict(inp,method)==out for inp,out in demo)

@dataclass(frozen=True)
class GridInventionResult:
    method: dict|None
    source_fit: bool
    source_examples: int
    generator: str
    elapsed_ms: float

class RelationalGridInventor:
    """NEUMANN executable causal method invention with explicit cost bound."""
    def __init__(self,max_search_ms=450):
        if type(max_search_ms) not in (int,float) or not 1<=max_search_ms<=120000:
            raise ValueError("finite bounded meta-invention budget required")
        self.max_search_ms=max_search_ms

    def solve(self,demonstrations):
        t=time.perf_counter_ns()
        demo=[(grid(a),grid(b)) for a,b in demonstrations]
        deadline=t+int(self.max_search_ms*1e6)
        try:
            method=induce(demo,deadline=deadline)
            correct=check_demonstrations(demo,method)
        except SearchBudgetExceeded:
            method=None
            correct=False
        return GridInventionResult(
            method=method if correct else None,
            source_fit=bool(correct),
            source_examples=len(demo),
            generator="semantically_inferred_relational_predicate_ast",
            elapsed_ms=round((time.perf_counter_ns()-t)/1e6,5))

    def apply(self,result:GridInventionResult,source_input):
        if not result.source_fit or result.method is None:
            return None
        return predict(grid(source_input),result.method)
