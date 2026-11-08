"""Q6 independent-author 1D generalization after source-visible interface repair.

The FIRST independent-author 1D-ARC evaluation had 57 invalid-size errors.
A genuine 32-cell source original shows the cause: arbitrary ARC2 axis cap.

New meta-input contract admits up to 900 pixels in a 1D row or column,
preserving ARC2 2D <=30x30. Both learned and classical arms receive
the SAME 1D shape support.

First 180 1D originals are EXPOSED SOURCE for interface development.
Second 180 are EXPOSED SOURCE by the previous Q4 speed evaluation.
The third 180 original files are chosen by filenames only, FROZEN before
any file bytes are read. Do not claim this is zero-1D-domain-adjustment Q6;
it is prospective transfer to a different new task cohort after generic
interface repair, with full prior exposure disclosed.
"""
from __future__ import annotations
import hashlib,json,pathlib,sys,time
sys.path.insert(0,'.')
sys.path.insert(0,'research/q3')
import q6_independent_author_1d_arc_transfer_first as q6

PRIOR_FIRST="old_first/Q6_1D_ARC_180_DIFFERENT_AUTHOR_ORIGINAL_FIRST.json"
PRIOR_SECOND="old_second/Q4_SECOND_1D_180_FILENAMES_FROZEN.json"
SOURCE="Q6_LONG_1D_INTERFACE_REPAIR_SOURCE_ONLY_FROZEN.json"
FIRST="Q6_LONG_1D_NEW_180_THIRD_AUTHORIGINAL_FIRST.json"
ROOT=pathlib.Path("independent_1d_arc/dataset")
N_PER_GROUP=10
GROUPS=18
REPO_SHA=q6.UPSTREAM

def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def fsha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def registries():
    p=json.loads(pathlib.Path(PRIOR_FIRST).read_text())
    s=json.loads(pathlib.Path(PRIOR_SECOND).read_text())
    if p["official_1d_author_commit"]!=REPO_SHA or s["official_1d_author_commit"]!=REPO_SHA:
        raise ValueError("DIFFERENT_OFFICIAL_REPO")
    old1=set(p["original_task_names"])
    old2=set(s["original_names"])
    if len(old1)!=180 or len(old2)!=180:
        raise ValueError("PRIOR_RECORD_SIZE")
    if len(old1 & old2):raise ValueError("PREVIOUS_TESTS_OVERLAP")
    opened=old1|old2
    groups=sorted(x for x in ROOT.iterdir() if x.is_dir())
    if len(groups)!=GROUPS:raise ValueError("WRONG_TYPE_NUMBER")
    src=[ROOT/x for x in sorted(old1)]
    target=[]
    for group in groups:
        candidates=[
            x for x in group.glob("*.json")
            if str(x.relative_to(ROOT)) not in opened]
        candidates.sort(key=lambda x:sha(("Q6-third-unopened-1d-domain-ext-v1",x.name)))
        if len(candidates)<N_PER_GROUP:
            raise ValueError("EXPECTED_ENOUGH_NEW_1D_ORIGINALS")
        target.extend(candidates[:N_PER_GROUP])
    if len(src)!=180 or len(target)!=180:raise ValueError("WRONG_SET_SIZE")
    if set(str(x.relative_to(ROOT)) for x in target)&opened:
        raise ValueError("FROZEN_REGISTRY_OVERLAP")
    return src,target

def source_only():
    sources,targets=registries()
    t=time.perf_counter()
    rows=[q6.solve_one(p) for p in sources]
    summary=q6.summarize(rows)
    report={
      "schema":"neumann.q6.dimension-generic-source-only.original180.v1",
      "source_exposed_independent_author_originals":180,
      "excluded_prior_first_1d_originals":180,
      "excluded_prior_second_1d_originals":180,
      "original_official_sha":REPO_SHA,
      "source_old_first_ids":[str(p.relative_to(ROOT)) for p in sources],
      "new_third_original_ids":[str(p.relative_to(ROOT)) for p in targets],
      "typed_semantic_inventor_sha256":fsha("neumann1/relational_grid_inventor.py"),
      "typed_classical_interpreter_sha256":fsha("neumann1/arc2_meta_grid_reasoner.py"),
      "inference_router_sha256":fsha("neumann1/hybrid_arc_grid_inventor.py"),
      "evaluator_sha256":fsha(__file__),
      "source_summary":summary,
      "source_wall_s":round(time.perf_counter()-t,5),
      "source_first_exposed":True,
      "target_third_originals_unopened":True,
      "prior_input_error_count":57,
      "new_input_contract":"1xN or Nx1 with N<=900, or 2D dimensions <=30x30, still total pixels <=900",
      "source_rows":rows,
      "human_written":"One-dimensional axis support and row/column count caching derived from previously opened 32-cell 1D original; not a new universal rule/primitive invention."}
    report["sha256"]=sha(report)
    pathlib.Path(SOURCE).write_text(json.dumps(report,indent=2))
    print(json.dumps({"source_exposed_result":{k:v for k,v in summary.items() if k!="by_concept"},
      "source_frozen_sha256":report["sha256"],
      "unopened_new_target_originals":len(targets)},indent=2),flush=True)
    return report

def new_original_first():
    model=json.loads(pathlib.Path(SOURCE).read_text())
    signature=model.pop("sha256")
    if sha(model)!=signature or model["original_official_sha"]!=REPO_SHA:
        raise ValueError("SOURCE_MODEL_MUTATED")
    filenames={
      "typed_semantic_inventor_sha256":"neumann1/relational_grid_inventor.py",
      "typed_classical_interpreter_sha256":"neumann1/arc2_meta_grid_reasoner.py",
      "inference_router_sha256":"neumann1/hybrid_arc_grid_inventor.py",
      "evaluator_sha256":__file__}
    for key,path in filenames.items():
        if model[key]!=fsha(path):
            raise ValueError("CODE_CHANGED_AFTER_SOURCE_LOCK_"+key)
    _,target=registries()
    if model["new_third_original_ids"]!=[str(p.relative_to(ROOT)) for p in target]:
        raise ValueError("FRESH_REGISTRY_CHANGED")
    print("Q6_DIMENSION_ADAPTED_SOURCE_FROZEN_BEFORE_THIRD_180_ORIGINALS",signature,flush=True)
    start=time.perf_counter()
    rows=[q6.solve_one(p) for p in target]
    summary=q6.summarize(rows)
    out={
      "schema":"neumann.q6.third-180-independent-originals-frozen-before-first.v1",
      "official_1d_arc_commit":REPO_SHA,
      "frozen_source_method_sha256":signature,
      "source_originals_previously_opened":180,
      "third_originals_untouched_until_now":180,
      "new_original_summary":summary,
      "new_original_wall_s":round(time.perf_counter()-start,5),
      "records":rows,
      "scope":"Independent author, 18 1D task families, 180 new original files. 1D type adapter was improved using earlier opened 1D task examples. Thus it tests generalization to NEW TASKS after domain adaptation, not a first-ever unseen-domain transfer. Separate ARC2 first proof remains independent.",
      "q3_q4_q6":"No global Q3 self-invention of meta-algorithm, no frontier-level matched results or fully amortized Q4 10x."}
    pathlib.Path(FIRST).write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!="by_concept"},indent=2),flush=True)
    return out

if __name__=="__main__":
    if sys.argv[1:]==["source"]:source_only()
    elif sys.argv[1:]==["target"]:new_original_first()
    else:raise SystemExit("source|target")
