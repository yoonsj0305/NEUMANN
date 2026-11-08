"""NEUMANN | ARC-AGI-2 typed grid-method invention and frontier-gap execution.

Original external ARC2 problems, *not* synthetic 4-bit inversion examples.
Q3 development: source-only program synthesis discovers reusable compositions
of generic typed grid operators, learns conditional METHOD SEARCH ORDER,
compares to identical full-language length-first cold classical enumeration.
All policy, operator library, task registries, budget and grammar frozen
BEFORE opening any ARC2 public evaluation task or test output.

The original public heldout test output is used ONLY AFTER prediction and
cost measurement to score accuracy; it is never a candidate oracle.

Scientific scope: human-coded base DSL and generic composition grammar;
finite search and source-only search policy learning are not universal
meta-algorithm self-invention. ARC2 public vs published semi-private frontier
leaderboard is an external, not same-run, comparison.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
import hashlib,itertools,json,math,os,pathlib,statistics,time,sys,tracemalloc

ARC_COMMIT="f3283f727488ad98fe575ea6a5ac981e4a188e49"
SOURCE_POLICY="ARC2_Q3_META_METHOD_SOURCE_FROZEN.json"
TARGET_FIRST="ARC2_Q3_FRONTIER_PUBLIC_120_FIRST.json"
ROOT=pathlib.Path("arc2_official/data")
DEFAULT_BUDGET=1500
PIXEL_CAP=900
DISCOVERY_N=256
VALIDATION_N=128

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(x):
    return hashlib.sha256(canon(x).encode()).hexdigest()
def _shape_ok(h,w):
    # Identical interface for 2D ARC2, but a 1D row/column may be longer
    # than 30 under the SAME bounded 900-pixel memory budget.
    return (1<=h and 1<=w and h*w<=PIXEL_CAP
            and (min(h,w)==1 or (h<=30 and w<=30)))


def G(rows):
    if not isinstance(rows,(list,tuple)) or not rows or not rows[0]:
        raise ValueError("invalid grid rows")
    g=tuple(tuple(row) for row in rows)
    w=len(g[0])
    if not _shape_ok(len(g),w) or any(len(row)!=w for row in g):
        raise ValueError("grid not rectangular")
    if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):
        raise ValueError("invalid palette")
    return g
def valid(g):
    if not g or not g[0] or not _shape_ok(len(g),len(g[0])):
        return False
    if any(len(row)!=len(g[0]) or any(not 0<=x<=9 for x in row) for row in g):
        return False
    return True
def d4(g,tag):
    if tag=="identity":return g
    if tag=="flip_lr":return tuple(tuple(reversed(row)) for row in g)
    if tag=="flip_ud":return g[::-1]
    if tag=="transpose":return tuple(tuple(g[r][c] for r in range(len(g))) for c in range(len(g[0])))
    if tag=="rotate90":return tuple(tuple(g[len(g)-1-r][c] for r in range(len(g))) for c in range(len(g[0])))
    if tag=="rotate180":return tuple(tuple(reversed(row)) for row in g[::-1])
    if tag=="rotate270":return tuple(tuple(g[r][len(g[0])-1-c] for r in range(len(g))) for c in range(len(g[0])))
    if tag=="anti_transpose":return d4(d4(g,"rotate180"),"transpose")
    raise ValueError("unsupported dihedral op")
def bbox(g, predicate):
    cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if predicate(v)]
    if not cells:return None
    return min(r for r,c in cells),max(r for r,c in cells),min(c for r,c in cells),max(c for r,c in cells)
def crop(g,predicate):
    b=bbox(g,predicate)
    if b is None:return None
    r0,r1,c0,c1=b
    return tuple(tuple(row[c0:c1+1]) for row in g[r0:r1+1])
def background(g):
    values=Counter(v for row in g for v in row)
    return min(values,key=lambda v:(-values[v],v))
def components(g, bg=0):
    H,W=len(g),len(g[0]);done=set();answer=[]
    for r in range(H):
        for c in range(W):
            if (r,c) in done or g[r][c]==bg:continue
            color=g[r][c];q=[(r,c)];done.add((r,c));part=[]
            while q:
                y,x=q.pop();part.append((y,x))
                for yy,xx in ((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
                    if (0<=yy<H and 0<=xx<W and (yy,xx) not in done
                            and g[yy][xx]==color):
                        done.add((yy,xx));q.append((yy,xx))
            answer.append(part)
    return answer
def component_transform(g,name):
    allc=components(g,0)
    if not allc:return None
    if name.endswith("largest"):
        chosen=max(allc,key=lambda c:(len(c),-min(y for y,x in c),-min(x for y,x in c)))
    else:
        chosen=min(allc,key=lambda c:(len(c),min(y for y,x in c),min(x for y,x in c)))
    cells=set(chosen)
    if name.startswith("keep_"):
        return tuple(tuple(g[r][c] if (r,c) in cells else 0
                     for c in range(len(g[0]))) for r in range(len(g)))
    r0=min(y for y,x in chosen);r1=max(y for y,x in chosen)
    c0=min(x for y,x in chosen);c1=max(x for y,x in chosen)
    return tuple(tuple(g[y][x] if (y,x) in cells else 0
                  for x in range(c0,c1+1)) for y in range(r0,r1+1))
def apply(g,op):
    try:
        if op in ("identity","flip_lr","flip_ud","transpose","rotate90","rotate180","rotate270","anti_transpose"):
            out=d4(g,op)
        elif op=="crop_nonzero":
            out=crop(g,lambda v:v!=0)
        elif op=="crop_nondominant":
            bg=background(g)
            out=crop(g,lambda v:v!=bg)
        elif op in ("extract_largest","extract_smallest","keep_largest","keep_smallest"):
            out=component_transform(g,op)
        elif op=="fill_bbox":
            b=bbox(g,lambda v:v!=0)
            if b is None:return None
            y0,y1,x0,x1=b
            colors=Counter(v for row in g for v in row if v!=0)
            color=min(colors,key=lambda x:(-colors[x],x))
            out=tuple(tuple(color if y0<=y<=y1 and x0<=x<=x1 else 0
                      for x in range(len(g[0]))) for y in range(len(g)))
        elif op in ("up2","up3","up4"):
            k=int(op[-1])
            if len(g)*k>30 or len(g[0])*k>30:return None
            out=tuple(tuple(v for v in row for _ in range(k))
                 for row in g for _ in range(k))
        elif op in ("down2","down3"):
            k=int(op[-1]);H=len(g);W=len(g[0])
            if H%k or W%k:return None
            blocks=[]
            for y in range(0,H,k):
                row=[]
                for x in range(0,W,k):
                    vals={g[yy][xx] for yy in range(y,y+k) for xx in range(x,x+k)}
                    if len(vals)!=1:return None
                    row.append(next(iter(vals)))
                blocks.append(tuple(row))
            out=tuple(blocks)
        elif op in ("tile_h2","tile_v2","tile_h3","tile_v3"):
            k=int(op[-1])
            if "tile_h" in op:
                if len(g[0])*k>30:return None
                out=tuple(row*k for row in g)
            else:
                if len(g)*k>30:return None
                out=g*k
        elif op=="mask_nonzero":
            out=tuple(tuple(int(v!=0) for v in row) for row in g)
        elif op=="mask_dominant":
            bg=background(g)
            out=tuple(tuple(int(v==bg) for v in row) for row in g)
        else:
            raise ValueError("bad operator")
        return out if out is not None and valid(out) else None
    except (IndexError,ValueError,TypeError):
        return None

OPERATORS=(
    "identity","flip_lr","flip_ud","transpose",
    "rotate90","rotate180","rotate270","anti_transpose",
    "crop_nonzero","crop_nondominant",
    "extract_largest","extract_smallest","keep_largest","keep_smallest",
    "fill_bbox","up2","up3","up4","down2","down3",
    "tile_h2","tile_v2","tile_h3","tile_v3",
    "mask_nonzero","mask_dominant"
)
# Compile a finite uniform program grammar ONCE. No domain-specific task
# solutions. The learned meta-policy chooses an order over this exact same set.
PROGRAMS=tuple([(x,) for x in OPERATORS] +
               [(x,y) for x,y in itertools.product(OPERATORS,repeat=2)
                if x!="identity" and y!="identity" and x!=y])
assert len(PROGRAMS)==len(set(PROGRAMS))
P2ID={p:i for i,p in enumerate(PROGRAMS)}

def predict(grid,program):
    out=grid
    for op in program:
        out=apply(out,op)
        if out is None:return None
    return out

def fit_color_map(inputs,outputs):
    mapping={}
    for x,y in zip(inputs,outputs):
        if len(x)!=len(y) or len(x[0])!=len(y[0]):
            return None
        for xr,yr in zip(x,y):
            for a,b in zip(xr,yr):
                if a in mapping and mapping[a]!=b:
                    return None
                mapping[a]=b
    return mapping

def recolor(g,mapping):
    return tuple(tuple(mapping.get(v,v) for v in row) for row in g)

def decode_task(path,include_test=False):
    data=json.loads(path.read_text())
    demo=[(G(item["input"]),G(item["output"])) for item in data["train"]]
    if not 1<=len(demo)<=10:raise ValueError("unsupported demonstration count")
    if not include_test:return demo
    return demo,[(G(x["input"]),G(x["output"])) for x in data["test"]]

def bucket(demo):
    matches=all(len(x)==len(y) and len(x[0])==len(y[0]) for x,y in demo)
    grows=all(len(y)*len(y[0])>len(x)*len(x[0]) for x,y in demo)
    shrinks=all(len(y)*len(y[0])<len(x)*len(x[0]) for x,y in demo)
    return ("same" if matches else "grow" if grows else "shrink" if shrinks else "mixed")

def apply_program_to_demos(program,demo):
    candidates=[];targets=[]
    for grid,target in demo:
        result=predict(grid,program)
        if result is None:return None
        candidates.append(result);targets.append(target)
    if candidates==targets:
        return {"kind":"exact","mapping":{}}
    mapping=fit_color_map(candidates,targets)
    if mapping is not None and all(recolor(x,mapping)==y for x,y in zip(candidates,targets)):
        return {"kind":"recolor","mapping":mapping}
    return None

def fit_task(demo,ranked,limit=DEFAULT_BUDGET,max_hits=2):
    checked=0;winners=[]
    for idx in ranked[:limit]:
        checked+=1
        p=PROGRAMS[idx]
        adapted=apply_program_to_demos(p,demo)
        if adapted is not None:
            winners.append((idx,adapted))
            if len(winners)>=max_hits:break
    return winners,checked

def test_task(winners,test):
    # First and second ORIGINAL task-level program candidates,
    # no test solution is used to choose or adjust them.
    if not winners:return False,0
    correct=[]
    for grid,actual in test:
        proposed=[]
        for idx,adapt in winners[:2]:
            output=predict(grid,PROGRAMS[idx])
            if output is None:continue
            if adapt["kind"]=="recolor":
                output=recolor(output,adapt["mapping"])
            proposed.append(output)
        correct.append(any(x==actual for x in proposed))
    return all(correct),len(test)

def source_paths():
    all_paths=sorted((ROOT/"training").glob("*.json"))
    if len(all_paths)!=1000:raise ValueError("expected original training 1000 tasks")
    # Registries frozen independently of task content. No evaluation listing.
    ranked=sorted(all_paths,key=lambda p:sha(("neumann-source-shuffle-v1",p.name)))
    return ranked[:DISCOVERY_N],ranked[DISCOVERY_N:DISCOVERY_N+VALIDATION_N]

def program_library_from_training():
    discovery,validation=source_paths()
    start=time.perf_counter()
    # For each training problem, enumerate only the same frozen typed grammar.
    # A verified demo fit is not proof of full domain generalization.
    by_bucket=defaultdict(Counter)
    global_support=Counter()
    source_ledger=[]
    cold=tuple(range(len(PROGRAMS)))
    for path in discovery:
        demo=decode_task(path)
        b=bucket(demo)
        # Keep ALL successful candidates up to first 8 for source support.
        hits,checks=fit_task(demo,cold,len(PROGRAMS),max_hits=8)
        # Drop trivial identity from reward if it just parrots unchanged data;
        # still record it so no artificially favorable source denominator.
        for idx,adapt in hits:
            by_bucket[b][idx]+=1
            global_support[idx]+=1
        source_ledger.append({"id":path.stem,"bucket":b,"hits":len(hits),
                              "candidates":checks})
    candidate_order={}
    for b in ("same","grow","shrink","mixed"):
        # This is the *source discovered meta-search policy*. Unlike the
        # cold control, its ranking comes ONLY from source DEMO I/O success,
        # not from any evaluation task or gold answer.
        candidate_order[b]=sorted(range(len(PROGRAMS)),
            key=lambda i:(-by_bucket[b][i],-global_support[i],
                          len(PROGRAMS[i]),i))
    validation_data=[]
    for path in validation:
        demo=decode_task(path);b=bucket(demo)
        row={"id":path.stem,"bucket":b}
        for name,ordered in (("classical",cold),("source_policy",candidate_order[b])):
            _,n=fit_task(demo,ordered,len(PROGRAMS),max_hits=2)
            row[name+"_checks"]=n
        validation_data.append(row)
    totals={k:sum(row[k+"_checks"] for row in validation_data)
            for k in ("classical","source_policy")}
    # Prevent negative transfer: select from DISJOINT source validation only.
    use_learned=totals["source_policy"]<totals["classical"]
    policy={"schema":"neumann.arc2.source-verified-grid-meta-order.v1",
      "arc_upstream_git_sha":ARC_COMMIT,"source_task_count":len(discovery),
      "validation_task_count":len(validation),"evaluation_task_count":120,
      "primitive_count":len(OPERATORS),"program_language_count":len(PROGRAMS),
      "candidate_budget":DEFAULT_BUDGET,"task_attempts":2,
      "fixed_training_task_ids":[x.stem for x in discovery],
      "fixed_validation_task_ids":[x.stem for x in validation],
      "source_program_support":{str(i):int(n) for i,n in global_support.items()},
      "source_bucket_program_support":{b:{str(i):int(n) for i,n in c.items()}
                                      for b,c in by_bucket.items()},
      "learned_program_rank_by_bucket":candidate_order,
      "validation_candidate_totals":totals,
      "source_policy_enabled":use_learned,
      "meta_learning_cost_wall_seconds":round(time.perf_counter()-start,5),
      "meta_hypothesis":"rank identical candidate programs by source-proven demonstration fit; fail closed to classical when source validation does not lower checks",
      "human_coded":"typed primitive DSL, composition grammar, shape buckets, source selection, policy selection rule, fixed candidate budget",
      "source_ledger":source_ledger,
      "validation_ledger":validation_data}
    policy["sha256"]=sha(policy)
    pathlib.Path(SOURCE_POLICY).write_text(json.dumps(policy,indent=2))
    print(json.dumps({"source_training":len(discovery),"validation":len(validation),
      "source_support_programs":len(global_support),
      "all_language":len(PROGRAMS),"evaluation_unopened":True,
      "source_policy_enabled":use_learned,
      "validation_candidate_totals":totals,
      "frozen_source_sha256":policy["sha256"],
      "source_wall_seconds":policy["meta_learning_cost_wall_seconds"]},indent=2))
    return policy

def evaluation_first():
    policy=json.loads(pathlib.Path(SOURCE_POLICY).read_text())
    digest=policy.pop("sha256")
    if sha(policy)!=digest or policy["arc_upstream_git_sha"]!=ARC_COMMIT:
        raise ValueError("FROZEN_SOURCE_CHECKSUM_FAILURE")
    if policy["candidate_budget"]!=DEFAULT_BUDGET or policy["program_language_count"]!=len(PROGRAMS):
        raise ValueError("SOURCE_POLICY_CHANGED")
    print("SOURCE_POLICY_FROZEN_BEFORE_ARC2_PUBLIC_EVAL",digest,flush=True)
    paths=sorted((ROOT/"evaluation").glob("*.json"))
    if len(paths)!=120:raise ValueError("EXPECTED_120_PUBLIC_ORIGINALS")
    if any(p.stem in set(policy["fixed_training_task_ids"]+policy["fixed_validation_task_ids"])
           for p in paths):raise ValueError("SOURCE_TARGET_ID_OVERLAP")
    start=time.perf_counter();rows=[]
    for path in paths:
        row={"task_id":path.stem}
        try:
            demo,test=decode_task(path,include_test=True)
            b=bucket(demo)
            row["bucket"]=b
            row["original_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            row["test_examples"]=len(test)
            row["arms"]={}
            for arm,rank in (("equal_grammar_classical",range(len(PROGRAMS))),
                             ("learned_meta_policy",
                              policy["learned_program_rank_by_bucket"][b]
                              if policy["source_policy_enabled"]
                              else range(len(PROGRAMS)))):
                t=time.perf_counter_ns()
                winners,checks=fit_task(demo,rank,DEFAULT_BUDGET,2)
                # The gold outputs are used for scoring only AFTER TWO
                # candidates are frozen by source demonstrations.
                elapsed_ms=(time.perf_counter_ns()-t)/1e6
                solved,_=test_task(winners,test)
                row["arms"][arm]={"solved":solved,
                    "candidate_checks":checks,
                    "wall_ms":round(elapsed_ms,5),
                    "proposed_program_ids":[int(i) for i,a in winners],
                    "hypotheses":len(winners)}
        except Exception as e:
            row["error"]=type(e).__name__+": "+str(e)[:200]
        rows.append(row)
    armnames=("equal_grammar_classical","learned_meta_policy")
    summary={arm:{"solved_original_tasks":sum(int(x.get("arms",{}).get(arm,{}).get("solved",False)) for x in rows),
                  "originals":len(paths),
                  "candidate_checks":sum(x.get("arms",{}).get(arm,{}).get("candidate_checks",0) for x in rows),
                  "search_wall_ms":round(sum(x.get("arms",{}).get(arm,{}).get("wall_ms",0) for x in rows),5)}
             for arm in armnames}
    result={"schema":"neumann.arc2.frontier-public-original-first.v1",
      "official_arc_git_sha":ARC_COMMIT,
      "frozen_source_policy_sha256":digest,
      "full_public_evaluation_originals":len(paths),
      "scoring":"all original test grids correct using up to two frozen per-test program hypotheses, task-level pass@2",
      "frontier_comparison":"ARC Prize published high model 95.0 percent on DISTINCT semi-private 120 tasks, not directly paired, no same-model compute telemetry",
      "source_learning_wall_seconds":policy["meta_learning_cost_wall_seconds"],
      "policy_enabled_from_source_only":policy["source_policy_enabled"],
      "summary":summary,
      "read_or_parse_errors":sum("error" in x for x in rows),
      "eval_run_wall_seconds":round(time.perf_counter()-start,4),
      "rows":rows,
      "q3_reality":"Human wrote DSL and composition grammar. Source learns priority for these candidates, not unconstrained invention of new meta-discovery algorithms. FRONTIER Q3/Q4/Q7 remains OPEN."}
    pathlib.Path(TARGET_FIRST).write_text(json.dumps(result,indent=2))
    print(json.dumps({"errors":result["read_or_parse_errors"],"policy":policy["source_policy_enabled"],
      "summary":summary,"source_s":result["source_learning_wall_seconds"],
      "target_s":result["eval_run_wall_seconds"]},indent=2))
    return result

if __name__=="__main__":
    if sys.argv[1:]==["source"]:program_library_from_training()
    elif sys.argv[1:]==["target"]:evaluation_first()
    else:raise SystemExit("source or target")
