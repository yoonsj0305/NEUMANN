"""Q3 Q4 Q6: fifth untouched 1D-ARC original transfer, NO new learning.

The method-learning cost was incurred once in previous source-only policy
run 42449484388. The next 180 original tasks are the last disjoint set
of 10 from each of 18 task types. The exact executable router code and
source policy SHA are not changed after first fourth-180 scoring.

This is an actual zero-new-discovery-cost repeat-transfer check, with
full original task correctness, same two attempts, measured inference cost
and stronger original fixed hybrid/cold comparator.
"""
from __future__ import annotations
import hashlib,json,pathlib,sys,time
sys.path.insert(0,".")
sys.path.insert(0,"research/q3")
import q3q4q6_lazy_meta_router_fourth_180_first as prev
from neumann1.source_learned_grid_router import SourceLearnedGridRouter

UPSTREAM=prev.UPSTREAM
SOURCE_MODEL="source_policy/Q3Q4Q6_LAZY_META_ROUTER_SOURCE_ONLY_FROZEN.json"
FIRST="Q3Q4Q6_LAZY_ROUTER_FIFTH_LAST_180_ORIGINAL_FIRST.json"
N=10
GROUPS=18

def registry():
    model=json.loads(pathlib.Path(SOURCE_MODEL).read_text())
    sig=model.pop("sha256")
    if prev.sha(model)!=sig:
        raise ValueError("SOURCE_POLICY_CHANGED")
    third,fourth=prev.registries()
    opened=set(model["previous_original_ids"]+model["new_unopened_target_ids"])
    # First, second and third original names are checked in prev.registries()
    a=json.loads(pathlib.Path(prev.PREVIOUS_FIRST).read_text())
    b=json.loads(pathlib.Path(prev.PREVIOUS_SECOND).read_text())
    opened.update(a["original_task_names"])
    opened.update(b["original_names"])
    if len(opened)!=720:
        raise ValueError("EXPECTED_4_DISJOINT_SOURCE_TARGET_COHORTS")
    groups=sorted(x for x in prev.DATA.iterdir() if x.is_dir())
    if len(groups)!=GROUPS:raise ValueError("AUTHOR_BENCHMARK_FAMILY_DRIFT")
    fresh=[]
    for group in groups:
        remain=[x for x in group.glob("*.json")
                if str(x.relative_to(prev.DATA)) not in opened]
        remain.sort(key=lambda x:prev.sha((
            "Q3Q4Q6-fifth-last-unopened-original-v1",
            str(x.relative_to(prev.DATA)))))
        if len(remain)<N:raise ValueError("LESS_THAN_10_NEW_ORIGINALS_PER_FAMILY")
        fresh.extend(remain[:N])
    if len(fresh)!=180 or any(str(x.relative_to(prev.DATA)) in opened
                              for x in fresh):
        raise ValueError("HOLDOUT_OVERLAP")
    return model,sig,fresh

def source_locked():
    model,sig,target=registry()
    keys={
      "new_router_sha":"neumann1/source_learned_grid_router.py",
      "relational_inventor_sha":"neumann1/relational_grid_inventor.py",
      "fixed_626_classical_sha":"neumann1/arc2_meta_grid_reasoner.py",
      "hybrid_inventor_sha":"neumann1/hybrid_arc_grid_inventor.py",
      "this_eval_sha":"research/q3/q3q4q6_lazy_meta_router_fourth_180_first.py"}
    for key,path in keys.items():
        if model[key]!=prev.file_sha(path):
            raise ValueError("SOURCE_POLICY_OR_BASELINE_CHANGED:"+key)
    if model["official_independent_author_sha"]!=UPSTREAM:
        raise ValueError("SOURCE_POLICY_AUTHOR_CHANGED")
    return model,sig,target

def main():
    model,policy_sha,files=source_locked()
    print("UNCHANGED_FROZEN_SOURCE_POLICY_BEFORE_LAST_180_NEW_TASK_BYTES",
          policy_sha,len(files),flush=True)
    t=time.perf_counter()
    records=[prev.solve_one(p,model["chosen_policy"],source_modes=False)
             for p in files]
    selected=prev.summarize(records)
    baseline={
      "cold_originals_correct":sum(x.get("comparison",{}).get("classical_correct",False)
                                   for x in records),
      "cold_candidate_search_s":round(sum(
          x.get("comparison",{}).get("classical_runtime_ms",0)
          for x in records)/1000,5),
      "hybrid_originals_correct":sum(x.get("comparison",{}).get("hybrid_correct",False)
                                     for x in records),
      "hybrid_candidate_search_s":round(sum(
          x.get("comparison",{}).get("hybrid_runtime_ms",0)
          for x in records)/1000,5)}
    outcome={
      "schema":"neumann.q3q4q6.fifth-last-independent-author-original-FIRST.v1",
      "official_1d_author_sha":UPSTREAM,
      "originals":len(records),
      "frozen_method_source_sha256":policy_sha,
      "new_discovery_or_policy_tuning":False,
      "total_source_training_wall_seconds_paid_once":model["source_wall_s"],
      "source_strategy":model["chosen_policy"],
      "source_route_method_checksum_verified":True,
      "new_target_original_files":[str(p.relative_to(prev.DATA)) for p in files],
      "selected_router":selected,
      "frozen_previous_comparators":baseline,
      "total_wall_s_including_comparators":round(time.perf_counter()-t,5),
      "records":records,
      "scientific_scope":"Fifth disjoint original 180 in independently authored 1D-ARC after exposed domain-specific adapter and concept-label strategy source calibration. Does not prove global Q3/Q6. Full cross-model compute, data collection and historical discovery costs separate from per-target inference."}
    pathlib.Path(FIRST).write_text(json.dumps(outcome,indent=2))
    print(json.dumps({"router":selected,"comparators":baseline,
      "source_discovery_paid_once_s":model["source_wall_s"],
      "target_wall_including_comparators_s":outcome["total_wall_s_including_comparators"]},indent=2),flush=True)
    return outcome

if __name__=="__main__":main()
