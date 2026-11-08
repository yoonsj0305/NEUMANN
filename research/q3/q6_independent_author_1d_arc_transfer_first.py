"""Q6 independent-author, structurally distinct 1D-ARC FIRST transfer.

Immutable NEUMANN source-only methods trained/revised on ARC-AGI-2 only.
Here transfer the ENTIRE INVENTION POLICY to different creators'
'khalil-research/1D-ARC' original one-dimensional grid problems.
NO 1D original data is loaded before the pinned meta-method/source hashes
and the task registry are frozen. Never retrain or tune on scored targets.

All outcomes are scored on original withheld target grids, not source fit.
Both methods receive same per-task training demonstrations and at most
two output attempts; baseline is the exact previously frozen 626 macro DSL.
Different expressive languages and hardware telemetry limitations are
disclosed. Independent-author grid geometry is scoped Q6, not universal Q6.
"""
from __future__ import annotations
import collections,hashlib,json,pathlib,sys,time
sys.path.insert(0,".")
sys.path.insert(0,"neumann1")
import arc2_meta_grid_reasoner as old
from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor
from neumann1.relational_grid_inventor import grid

UPSTREAM="1e74dc4cb4c58d8160e1fbd0ba638eb745f37147"
DATA=pathlib.Path("independent_1d_arc/dataset")
SOURCE_MODEL="frozen_source/Q3_RELATIONAL_MULTI_HYBRID_SOURCE_ONLY_V2_FROZEN.json"
FIRST="Q6_1D_ARC_180_DIFFERENT_AUTHOR_ORIGINAL_FIRST.json"
N_PER_GROUP=10
EXPECTED_GROUPS=18
EXPECTED_COUNT=N_PER_GROUP*EXPECTED_GROUPS

def canonical(a):return json.dumps(a,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(a):return hashlib.sha256(canonical(a).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def source_method_preflight():
    p=json.loads(pathlib.Path(SOURCE_MODEL).read_text())
    digest=p.pop("sha256")
    if sha(p)!=digest:raise ValueError("SOURCE_CONTRACT_SHA_CHANGED")
    if p["official_upstream_sha"]!="f3283f727488ad98fe575ea6a5ac981e4a188e49":
        raise ValueError("SOURCE_NOT_OFFICIAL_ARC2")
    required={
      "relational_code_sha256":"neumann1/relational_grid_inventor.py",
      "hybrid_core_code_sha256":"neumann1/hybrid_arc_grid_inventor.py",
      "previous_strong_classic_code_sha256":"neumann1/arc2_meta_grid_reasoner.py"}
    for key,path in required.items():
        if p[key]!=file_sha(path):raise ValueError("INVENTOR_UPDATED_AFTER_FREEZE_"+key)
    return p,digest

def registry():
    groups=sorted(p for p in DATA.iterdir() if p.is_dir())
    if len(groups)!=EXPECTED_GROUPS:
        raise ValueError(f"WRONG_GROUPS:{len(groups)}")
    names=[]
    for group in groups:
        tasks=sorted(group.glob("*.json"))
        if len(tasks)<N_PER_GROUP:raise ValueError("INSUFFICIENT_GROUP_"+group.name)
        # Selection uses filename only and a method-independent SHA salt.
        tasks.sort(key=lambda x:sha(("Q6-independent-author-1d-unopened-FIRST-v1",x.name)))
        names.extend(tasks[:N_PER_GROUP])
    if len(names)!=EXPECTED_COUNT:raise ValueError("EXPECTED_180_TARGETS")
    return names

def G(payload):
    # A generic dimension-embedding adapter, fixed before any 1D target:
    # list-of-numbers maps into a single-row 2D grid; a nested grid is kept.
    if isinstance(payload,list) and payload and type(payload[0]) is int:
        return grid([payload])
    return grid(payload)

def read_original(path):
    data=json.loads(path.read_text())
    if not isinstance(data,dict) or "train" not in data or "test" not in data:
        raise ValueError("UNKNOWN_ORIGINAL_FORMAT")
    demo=[(G(x["input"]),G(x["output"])) for x in data["train"]]
    inputs=[G(x["input"]) for x in data["test"]]
    if not 1<=len(demo)<=20 or not inputs or any("output" not in x for x in data["test"]):
        raise ValueError("MISSING_TRAIN_OR_HIDDEN_ORIGINAL_OUTPUT")
    # Held-out gold is reserved for AFTER method proposals are finalized.
    gold=[G(x["output"]) for x in data["test"]]
    return demo,inputs,gold

def solve_one(path):
    start=time.perf_counter_ns()
    item={"id":str(path.relative_to(DATA)), "original_sha256":file_sha(path),
          "concept_group":path.parent.name}
    try:
        demo,inputs,gold=read_original(path)
        hybrid=HybridArcGridInventor(max_attempts=2).solve(demo,inputs)
        fixed=[tuple(p.outputs) for p in hybrid.candidates]
        # This independent-author benchmark's test output is for scoring
        # only. The selected two predictions do NOT depend on that gold.
        passed=any(p==tuple(gold) for p in fixed)
        baseline_start=time.perf_counter_ns()
        possible,checks=old.fit_task(
            demo,tuple(range(len(old.PROGRAMS))),len(old.PROGRAMS),2)
        cold_candidates=[]
        for idx,adapt in possible:
            outputs=[]
            for x in inputs:
                y=old.predict(x,old.PROGRAMS[idx])
                if y is not None and adapt["kind"]=="recolor":
                    y=old.recolor(y,adapt["mapping"])
                outputs.append(y)
            cold_candidates.append(tuple(outputs))
        baseline_ms=(time.perf_counter_ns()-baseline_start)/1e6
        cold_correct=any(p==tuple(gold) for p in cold_candidates)
        item.update({
            "original_test_cases":len(gold),
            "source_demonstrations":len(demo),
            "hybrid_correct":bool(passed),
            "cold_correct":bool(cold_correct),
            "hybrid_source_relational_fit":hybrid.new_source_fit,
            "hybrid_prior_dsl_fit":hybrid.old_source_fit,
            "hybrid_candidate_types":[q.origin for q in hybrid.candidates],
            "hybrid_attempts":len(hybrid.candidates),
            "cold_attempts":len(possible),
            "hybrid_total_search_ms":hybrid.total_search_ms,
            "hybrid_relational_ms":hybrid.new_search_ms,
            "hybrid_old_dsl_ms":hybrid.old_search_ms,
            "cold_search_ms":round(baseline_ms,5),
            "cold_candidate_checks":checks,
        })
    except Exception as exc:
        item["error"]=type(exc).__name__+": "+str(exc)[:240]
    item["wall_ms"]=round((time.perf_counter_ns()-start)/1e6,5)
    return item

def summarize(rows):
    results={}
    for group in sorted({r["concept_group"] for r in rows}):
        group_rows=[x for x in rows if x["concept_group"]==group]
        results[group]={
            "tasks":len(group_rows),
            "errors":sum("error" in r for r in group_rows),
            "hybrid":sum(r.get("hybrid_correct",False) for r in group_rows),
            "cold":sum(r.get("cold_correct",False) for r in group_rows)}
    return {
      "originals":len(rows),
      "source_publisher":"ARC Prize, ARC-AGI-2",
      "target_publisher":"khalil-research 1D-ARC",
      "independent_author":True,
      "different_geometry":"one-dimensional transformations",
      "errors":sum("error" in r for r in rows),
      "hybrid_exact_orig":sum(r.get("hybrid_correct",False) for r in rows),
      "cold_exact_orig":sum(r.get("cold_correct",False) for r in rows),
      "hybrid_only":sum(r.get("hybrid_correct",False) and
                         not r.get("cold_correct",False) for r in rows),
      "cold_only":sum(r.get("cold_correct",False) and
                       not r.get("hybrid_correct",False) for r in rows),
      "both_correct":sum(r.get("hybrid_correct",False) and
                         r.get("cold_correct",False) for r in rows),
      "hybrid_search_s":round(sum(r.get("hybrid_total_search_ms",0) for r in rows)/1000,5),
      "cold_search_s":round(sum(r.get("cold_search_ms",0) for r in rows)/1000,5),
      "cold_candidate_checks":sum(r.get("cold_candidate_checks",0) for r in rows),
      "by_concept":results
    }

def main():
    model,sig=source_method_preflight()
    paths=registry()
    print("FROZEN_1D_AUTHOR_TRANSFER_BEFORE_TARGET_BYTES",sig,UPSTREAM,len(paths),flush=True)
    t=time.perf_counter()
    rows=[solve_one(path) for path in paths]
    report={
      "schema":"neumann.q6.independent-author-1d-arc-originals-first.v1",
      "official_1d_author_commit":UPSTREAM,
      "official_arc2_source_commit":model["official_upstream_sha"],
      "frozen_method_source_hash":sig,
      "original_task_names":[str(p.relative_to(DATA)) for p in paths],
      "summary":summarize(rows),
      "first_run_wall_s":round(time.perf_counter()-t,5),
      "rows":rows,
      "limits":"Different benchmark authors and one-dimensional grid domain, same general GRID task superfamily, not proof of universal math-domain transfer. Models have different expressive power. Results are original task-level exact with <=2 attempts. No frontier proprietary FLOPs or compute-cost comparison.",
      "original_outcome_rule":"One single candidate program must predict EVERY withheld test output in original task; no per-test gold-guided switching."}
    pathlib.Path(FIRST).write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report["summary"].items() if k!="by_concept"},indent=2),flush=True)
    print(json.dumps({"groups":report["summary"]["by_concept"]},indent=2),flush=True)
    return report

if __name__=="__main__":main()
