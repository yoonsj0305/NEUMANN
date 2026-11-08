"""Q3 Q4 Q6: original-source learned STRATEGY grammar, fresh author cohort.

A meta-learner learns which program-generator to EXECUTE from different
author's already OPENED original 180 tasks. On a genuinely NEW fourth 180:
use exactly one source-chosen strategy per concept family, no gold-based
switching. Compare to strongest fixed two-attempt classical and two-attempt
combined baseline on same new originals.

No source tuning after first fourth-original exposure. This is a domain
adapted independent-author transfer, not first unadapted cross-domain Q6.
"""
from __future__ import annotations
from collections import Counter
import hashlib,json,pathlib,sys,time
sys.path.insert(0,".")
sys.path.insert(0,"research/q3")
from neumann1.source_learned_grid_router import SourceLearnedGridRouter,STRATEGIES
from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor
import q6_independent_author_1d_arc_transfer_first as q6
import q6_variable_axis_1d_new_180_source_then_first as third

DATA=pathlib.Path("independent_1d_arc/dataset")
PREVIOUS_FIRST="prior_first/Q6_1D_ARC_180_DIFFERENT_AUTHOR_ORIGINAL_FIRST.json"
PREVIOUS_SECOND="prior_second/Q4_SECOND_1D_180_FILENAMES_FROZEN.json"
PREVIOUS_THIRD="prior_third/Q6_LONG_1D_NEW_180_THIRD_AUTHORIGINAL_FIRST.json"
UPSTREAM="1e74dc4cb4c58d8160e1fbd0ba638eb745f37147"
MODEL="Q3Q4Q6_LAZY_META_ROUTER_SOURCE_ONLY_FROZEN.json"
TARGET="Q3Q4Q6_LAZY_META_ROUTER_FOURTH_180_ORIGINAL_FIRST.json"
EXPECTED_PER_GROUP=10
CONCEPTS=18

def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(v):return hashlib.sha256(canon(v).encode()).hexdigest()
def file_sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def registries():
    first=json.loads(pathlib.Path(PREVIOUS_FIRST).read_text())
    second=json.loads(pathlib.Path(PREVIOUS_SECOND).read_text())
    previous=json.loads(pathlib.Path(PREVIOUS_THIRD).read_text())
    if (first["official_1d_author_commit"]!=UPSTREAM or
            second["official_1d_author_commit"]!=UPSTREAM or
            previous["official_1d_arc_commit"]!=UPSTREAM):
        raise ValueError("SOURCE_AUTHORITY_MISMATCH")
    ids_a=set(first["original_task_names"])
    ids_b=set(second["original_names"])
    ids_c=set(record["id"] for record in previous["records"])
    if not (len(ids_a)==len(ids_b)==len(ids_c)==180):
        raise ValueError("SOURCE_DENOMINATORS_BAD")
    if ids_a & ids_b or ids_a & ids_c or ids_b & ids_c:
        raise ValueError("SOURCE_REGISTRY_OVERLAP")
    groups=sorted(p for p in DATA.iterdir() if p.is_dir())
    if len(groups)!=CONCEPTS:raise ValueError("MISSING_CONCEPT_FAMILY")
    fourth=[]
    opened=ids_a|ids_b|ids_c
    for group in groups:
        candidates=[p for p in group.glob("*.json")
                    if str(p.relative_to(DATA)) not in opened]
        candidates.sort(key=lambda p:sha((
            "Q3Q4Q6-lazy-utility-fourth-unopened-v1",str(p.relative_to(DATA)))))
        if len(candidates)<EXPECTED_PER_GROUP:
            raise ValueError("NOT_ENOUGH_FOURTH_NEW_ORIGINALS")
        fourth.extend(candidates[:EXPECTED_PER_GROUP])
    if len(fourth)!=180:raise ValueError("FOURTH_COUNT")
    if set(str(p.relative_to(DATA)) for p in fourth)&opened:
        raise ValueError("TARGET_WAS_PREVIOUSLY_OPENED")
    source=[DATA/x for x in sorted(ids_c)]
    return source,fourth

def solve_one(path,policy=None,source_modes=False):
    rec={"id":str(path.relative_to(DATA)),"concept":path.parent.name,
         "original_sha256":file_sha(path)}
    try:
        demo,inputs,gold=q6.read_original(path)
        if source_modes:
            choices=STRATEGIES
        else:
            if policy is None:raise ValueError("NO_FROZEN_SOURCE_POLICY")
            choices=(policy[path.parent.name],)
        arm={}
        for mode in choices:
            t=time.perf_counter_ns()
            out=SourceLearnedGridRouter({path.parent.name:mode}).solve(
                path.parent.name,demo,inputs)
            pred=[c.outputs for c in out.candidates]
            arm[mode]={"correct":any(p==tuple(gold) for p in pred),
                "runtime_ms":round((time.perf_counter_ns()-t)/1e6,5),
                "attempt_count":len(pred),
                "classical_candidate_checks":out.classical_program_checks,
                "relational_source_fit":out.relational_source_fit}
        if not source_modes:
            # Only reference comparator uses a separate full grammar search.
            # Its runtime is comparison, NOT charged to the chosen strategy.
            prev=q6.solve_one(path)
            if "error" in prev:raise ValueError("FROZEN_REFERENCE_ERROR:"+prev["error"])
            rec["comparison"]={
                "classical_correct":bool(prev["cold_correct"]),
                "classical_runtime_ms":prev["cold_search_ms"],
                "hybrid_correct":bool(prev["hybrid_correct"]),
                "hybrid_runtime_ms":prev["hybrid_total_search_ms"],
                "classical_checks":prev["cold_candidate_checks"]}
        rec["arms"]=arm
    except Exception as exc:
        rec["error"]=type(exc).__name__+": "+str(exc)[:240]
    return rec

def summarize(rows,mode=None):
    valid=[r for r in rows if "error" not in r]
    if mode is None:
        selected=[next(iter(r["arms"].values())) for r in valid]
    else:
        selected=[r["arms"][mode] for r in valid]
    return {"originals":len(rows),"valid":len(valid),
        "errors":len(rows)-len(valid),
        "correct":sum(x["correct"] for x in selected),
        "runtime_s":round(sum(x["runtime_ms"] for x in selected)/1000,5),
        "classical_candidate_checks":sum(
            x["classical_candidate_checks"] for x in selected),
        "attempts_used":sum(x["attempt_count"] for x in selected)}

def learn_source():
    source,target=registries()
    t=time.perf_counter()
    ledger=[solve_one(p,source_modes=True) for p in source]
    if any("error" in r for r in ledger):
        raise ValueError("SOURCE_POLICY_HAS_ERRORS")
    by_concept={}
    policy={}
    for concept in sorted({r["concept"] for r in ledger}):
        group=[r for r in ledger if r["concept"]==concept]
        by_concept[concept]={kind:summarize(group,kind)
                             for kind in STRATEGIES}
        # Source-only lexicographic objective: preserve verified original
        # correctness first, then minimize measured runtime. No target data.
        best=min(STRATEGIES,key=lambda mode:(
            -by_concept[concept][mode]["correct"],
            by_concept[concept][mode]["runtime_s"],
            STRATEGIES.index(mode)))
        policy[concept]=best
    report={"schema":"neumann.q3q4q6.source-trained-3-way-meta-strategy.v1",
       "official_independent_author_sha":UPSTREAM,
       "source_orig_count":len(source),
       "target_orig_count":len(target),
       "previous_original_ids":[str(p.relative_to(DATA)) for p in source],
       "new_unopened_target_ids":[str(p.relative_to(DATA)) for p in target],
       "chosen_policy":policy,
       "source_concept_evidence":by_concept,
       "source_summary":{m:summarize(ledger,m) for m in STRATEGIES},
       "new_router_sha":file_sha("neumann1/source_learned_grid_router.py"),
       "relational_inventor_sha":file_sha("neumann1/relational_grid_inventor.py"),
       "fixed_626_classical_sha":file_sha("neumann1/arc2_meta_grid_reasoner.py"),
       "hybrid_inventor_sha":file_sha("neumann1/hybrid_arc_grid_inventor.py"),
       "this_eval_sha":file_sha(__file__),
       "source_wall_s":round(time.perf_counter()-t,5),
       "source_only":True,
       "target_bytes_opened":False,
       "limitations":"Source family labels are benchmark metadata; 180 previously seen 1D originals are used to learn this meta strategy. The three routing strategies themselves remain human coded. Independent author compared with ARC2, but this is adapted Q6, not universal Q3 or Q4."}
    report["sha256"]=sha(report)
    pathlib.Path(MODEL).write_text(json.dumps(report,indent=2))
    print(json.dumps({"source_modes":report["source_summary"],
      "chosen_policy":policy,"source_wall_s":report["source_wall_s"],
      "frozen_sha":report["sha256"],"target_unopened":len(target)},indent=2),flush=True)
    return report

def target_first():
    policy=json.loads(pathlib.Path(MODEL).read_text())
    sig=policy.pop("sha256")
    if sha(policy)!=sig or not policy["source_only"] or policy["official_independent_author_sha"]!=UPSTREAM:
        raise ValueError("MUTATED_FROZEN_META_STRATEGY")
    for key,path in {
        "new_router_sha":"neumann1/source_learned_grid_router.py",
        "relational_inventor_sha":"neumann1/relational_grid_inventor.py",
        "fixed_626_classical_sha":"neumann1/arc2_meta_grid_reasoner.py",
        "hybrid_inventor_sha":"neumann1/hybrid_arc_grid_inventor.py",
        "this_eval_sha":__file__,
        }.items():
        if policy[key]!=file_sha(path):
            raise ValueError("SOURCE_CODE_CHANGED_AFTER_FREEZE_"+key)
    _,target=registries()
    if policy["new_unopened_target_ids"]!=[
          str(p.relative_to(DATA)) for p in target]:
        raise ValueError("TARGET_REGISTRY_NOT_FROZEN")
    print("FROZEN_META_STRATEGY_BEFORE_FOURTH_AUTHOR_ORIGINAL",sig,flush=True)
    t=time.perf_counter()
    rows=[solve_one(p,policy["chosen_policy"],source_modes=False)
          for p in target]
    selected=summarize(rows)
    refs={
      "classical":{"correct":sum(x.get("comparison",{}).get("classical_correct",False)
                          for x in rows),
                   "runtime_s":round(sum(x.get("comparison",{}).get("classical_runtime_ms",0)
                        for x in rows)/1000,5)},
      "hybrid":{"correct":sum(x.get("comparison",{}).get("hybrid_correct",False)
                          for x in rows),
                   "runtime_s":round(sum(x.get("comparison",{}).get("hybrid_runtime_ms",0)
                        for x in rows)/1000,5)}}
    report={"schema":"neumann.q3q4q6.lazy-meta-router-independent-author-fourth-original-FIRST.v1",
       "official_repo_sha":UPSTREAM,"source_method_sha":sig,
       "new_originals":len(rows),"selected_strategy":selected,
       "frozen_full_grammar_classical":refs["classical"],
       "previous_full_hybrid":refs["hybrid"],
       "results":rows,
       "total_comparison_wall_s":round(time.perf_counter()-t,5),
       "scope":"First fourth 1D-ARC independent original cohort, after domain-specific adapter and source-family strategy calibration. Same two-attempt budget, full source-only cost of policy learning must be amortized separately. No universal Q3 and no frontier-level ARC2."}
    pathlib.Path(TARGET).write_text(json.dumps(report,indent=2))
    print(json.dumps({"new":selected,"reference":refs,
       "source_discovery_wall_s":policy["source_wall_s"],
       "target_comparison_wall_s":report["total_comparison_wall_s"]},indent=2),flush=True)
    return report

if __name__=="__main__":
    if sys.argv[1:]==["source"]:learn_source()
    elif sys.argv[1:]==["target"]:target_first()
    else:raise SystemExit("source|target")
