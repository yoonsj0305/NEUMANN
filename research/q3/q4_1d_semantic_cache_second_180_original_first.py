"""Q4 FIRST paired identical-DSL semantic representation reuse: 180 untouched 1D-ARC originals.

Two versions of the SAME production program inventor:
  uncached = exact immutable pre-optimization NEUMANN core commit;
  cached   = bounded memoized pure input structural representation.
Same original tests, candidate grammar, max-two output attempts,
actual original answers, and same runner machine; first-run target registry
is frozen before either arm sees file bytes.

New second set excludes every target in the prior 180 independent-author
FIRST. Original test labels are used for scoring only after predictions.
No architecture tuning on the new second 180 original tasks.
"""
from __future__ import annotations
import hashlib,json,pathlib,sys,time
sys.path.insert(0,'.')
sys.path.insert(0,'research/q3')
import q6_independent_author_1d_arc_transfer_first as q6
ROOT=pathlib.Path("independent_1d_arc/dataset")
FIRST_180="prior_1d/Q6_1D_ARC_180_DIFFERENT_AUTHOR_ORIGINAL_FIRST.json"
FIXED_REGISTRY="Q4_SECOND_1D_180_FILENAMES_FROZEN.json"

def canonical(a):return json.dumps(a,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(a):return hashlib.sha256(canonical(a).encode()).hexdigest()

def registry():
    first=json.loads(pathlib.Path(FIRST_180).read_text())
    if first["official_1d_author_commit"]!=q6.UPSTREAM or len(first["original_task_names"])!=180:
        raise ValueError("WRONG_PRIOR_FIRST")
    old=set(first["original_task_names"])
    groups=sorted(x for x in ROOT.iterdir() if x.is_dir())
    if len(groups)!=18:raise ValueError("EXPECTED_18_AUTHORS_CATEGORIES")
    new=[]
    for group in groups:
        available=[
            p for p in group.glob("*.json")
            if str(p.relative_to(ROOT)) not in old]
        available.sort(key=lambda p:sha(("q4-1d-second-never-opened-v1",p.name)))
        if len(available)<10:raise ValueError("SECOND_TARGET_REGISTRY_INCOMPLETE")
        new.extend(available[:10])
    result=[str(p.relative_to(ROOT)) for p in new]
    if len(result)!=180 or len(set(result))!=180 or set(result)&old:
        raise ValueError("NEW_TARGETS_INCLUDE_OLD")
    return new,result

def prefreeze():
    paths,registry_names=registry()
    payload={"schema":"neumann.q4.paired-same-language-second-author-target-FIRST.v1",
         "official_1d_author_commit":q6.UPSTREAM,
         "old_prior_originals":180,
         "new_original_count":len(paths),
         "original_names":registry_names,
         "baseline_uncached_git_commit":"3f00f54ff71070cf3f9356099775e2afbec6fa61",
         "relational_cache_spec":"bounded maxsize 48/64/64 over pure immutable input grid object graph/features",
         "comparison":"first uncached then cached, BOTH frozen before first original target file bytes read",
         "human_selection":"18 types × 10 original files per type, deterministic fixed hash, excluding the original prior 180"}
    payload["sha256"]=sha(payload)
    pathlib.Path(FIXED_REGISTRY).write_text(json.dumps(payload,indent=2))
    print("Q4_SECOND_180_UNOPENED_FILENAMES_FROZEN",payload["sha256"],flush=True)
    return payload

def target_arm(label):
    p=json.loads(pathlib.Path(FIXED_REGISTRY).read_text())
    digest=p.pop("sha256")
    if sha(p)!=digest or p["official_1d_author_commit"]!=q6.UPSTREAM:
        raise ValueError("FROZEN_REGISTRY_INVALID")
    paths,names=registry()
    if names!=p["original_names"]:raise ValueError("ORIGINAL_IDS_CHANGED")
    if label not in ("uncached","cached"):raise ValueError("UNKNOWN_RESEARCH_ARM")
    print("FROZEN_ABSENT_TARGET_SOURCE_MODEL",digest,label,flush=True)
    start=time.perf_counter()
    rows=[q6.solve_one(path) for path in paths]
    combined=q6.summarize(rows)
    report={"schema":"neumann.q4.paired-memoized-1d-independent-author-180-original-FIRST.v1",
       "frozen_registry_sha256":digest,
       "original_1d_upstream":q6.UPSTREAM,
       "method_arm":label,
       "source_code_sha256":q6.file_sha("neumann1/relational_grid_inventor.py"),
       "new_task_count":len(rows),
       "first_arm_will_open_originals":label=="uncached",
       "original_evaluation":combined,
       "total_wall_s":round(time.perf_counter()-start,5),
       "rows":rows,
       "notes":"Comparing the same original task and same DSL under two previously frozen implementation variants. Invalid size inputs still errors; report all failures. Cost comparison omits previous source discovery and any proprietary frontier FLOPs."}
    dest="Q4_SECOND_1D_ORIGINAL_"+label.upper()+".json"
    pathlib.Path(dest).write_text(json.dumps(report,indent=2))
    print(json.dumps({
       "label":label,"originals":combined["originals"],"errors":combined["errors"],
       "solved":combined["hybrid_exact_orig"],"cold":combined["cold_exact_orig"],
       "hybrid_s":combined["hybrid_search_s"],"cold_s":combined["cold_search_s"],
       "full_wall_s":report["total_wall_s"]},indent=2),flush=True)
    return report

if __name__=="__main__":
    if sys.argv[1:]==["prefreeze"]:prefreeze()
    elif len(sys.argv)==3 and sys.argv[1]=="target":
        target_arm(sys.argv[2])
    else:raise SystemExit("prefreeze | target [uncached|cached]")
