"""Q3 hybrid discovery: source-only development -> untouched official 200 FIRST.

Old method first run: ARC2 official 120 public 0/120 (immutable).
Relational v1 first run: 240 distinct ARC2 official training originals,
                    5/240 vs old 8/240 (immutable).
This v2 run uses those OPENED 240 only as new SOURCE development, not as
fresh evaluation. It freezes all code and target IDs before reading any
new 200 original training problem bytes.

New hybrid: auto-generated single/multi-rule object predicate programs,
paired within fixed 2 attempts with prior general grid macro generator.
Old 626-program reference stays EXACTLY the earlier benchmark code and
retains 2 attempts and candidate scoring rights.
"""
from __future__ import annotations
import hashlib,json,pathlib,sys,time
sys.path.insert(0,"neumann1")
import arc2_meta_grid_reasoner as old
from relational_grid_inventor import grid
from hybrid_arc_grid_inventor import HybridArcGridInventor
ROOT=pathlib.Path("arc2_official/data/training")
PRIOR="previous_source/Q3_RELATIONAL_PROGRAM_LANGUAGE_SOURCE_ONLY_FROZEN.json"
MODEL="Q3_RELATIONAL_MULTI_HYBRID_SOURCE_ONLY_V2_FROZEN.json"
FIRST="Q3_RELATIONAL_MULTI_HYBRID_200_NEW_ORIGINAL_FIRST.json"
UPSTREAM="f3283f727488ad98fe575ea6a5ac981e4a188e49"
LIMIT=200
INSPECTED={"f25fbde4","de1cd16c","9565186b"}

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def fsha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def prior():
    p=json.loads(pathlib.Path(PRIOR).read_text())
    sig=p.pop("sha256")
    if sha(p)!=sig or p["official_upstream"]!=UPSTREAM:
        raise ValueError("PREVIOUS_ORIGINAL_SOURCE_CHANGED")
    if len(p["holdout_ids"])!=240 or len(p["source_ids"])!=256 or len(p["source_validation_ids"])!=128:
        raise ValueError("WRONG_SOURCE_REGISTRY")
    return p,sig

def registries():
    p,sig=prior()
    allp=sorted(ROOT.glob("*.json"))
    if len(allp)!=1000:raise ValueError("WRONG_ORIGINAL_CORPUS")
    source=[ROOT/(id+".json") for id in p["holdout_ids"]]
    opened=set(p["holdout_ids"]+p["source_ids"]+p["source_validation_ids"])|INSPECTED
    new=sorted((x for x in allp if x.stem not in opened),
               key=lambda x:sha(("q3-relational-composition-second-blind-v1",x.name)))
    target=new[:LIMIT]
    if len(target)!=LIMIT or set(x.stem for x in target)&opened:
        raise ValueError("SECOND_FRESH_TARGET_OVERLAP")
    return source,target

def read_problem(path):
    j=json.loads(path.read_text())
    demo=[(grid(x["input"]),grid(x["output"])) for x in j["train"]]
    test=[grid(x["input"]) for x in j["test"]]
    gold=[grid(x["output"]) for x in j["test"]]
    if not 1<=len(demo)<=10 or len(test)<1:
        raise ValueError("UNSUPPORTED_ORIGINAL")
    return demo,test,gold

def solve_one(path):
    receipt={"id":path.stem,"original_sha256":fsha(path)}
    try:
        demo,test,gold=read_problem(path)
        total_start=time.perf_counter_ns()
        output=HybridArcGridInventor(max_attempts=2).solve(demo,test)
        proposed=[tuple(candidate.outputs) for candidate in output.candidates]
        # No gold used before outputs are frozen by HybridArcGridInventor.
        hybrid_correct=any(pred==tuple(gold) for pred in proposed)
        # Legacy reference, completely unchanged: first two full-language
        # original train-compatible programs, one final program for all tests.
        t=time.perf_counter_ns()
        winners,checks=old.fit_task(
            demo,tuple(range(len(old.PROGRAMS))),len(old.PROGRAMS),2)
        old_ms=(time.perf_counter_ns()-t)/1e6
        classic_preds=[]
        for idx,adapter in winners:
            prediction=[]
            for g in test:
                obj=old.predict(g,old.PROGRAMS[idx])
                if obj is not None and adapter["kind"]=="recolor":
                    obj=old.recolor(obj,adapter["mapping"])
                prediction.append(obj)
            classic_preds.append(tuple(prediction))
        old_correct=any(x==tuple(gold) for x in classic_preds)
        receipt.update({
           "source_examples":len(demo),"original_test_examples":len(test),
           "hybrid_original_test_correct":bool(hybrid_correct),
           "hybrid_candidate_origins":[c.origin for c in output.candidates],
           "hybrid_candidate_count":len(output.candidates),
           "hybrid_new_relation_source_fit":output.new_source_fit,
           "hybrid_old_dsl_source_fit":output.old_source_fit,
           "hybrid_total_search_ms":output.total_search_ms,
           "hybrid_relation_search_ms":output.new_search_ms,
           "hybrid_legacy_dsl_search_ms":output.old_search_ms,
           "hybrid_old_program_checks":output.old_candidate_checks,
           "legacy_original_test_correct":bool(old_correct),
           "legacy_candidate_checks":checks,
           "legacy_search_ms":round(old_ms,5),
           "legacy_program_ids":[int(i) for i,a in winners],
           "new_method_summary":[c.expression for c in output.candidates
                                  if c.origin=="self_invented_relational_rule"],
           "total_wall_ms":round((time.perf_counter_ns()-total_start)/1e6,5)})
    except Exception as e:
        receipt["error"]=type(e).__name__+": "+str(e)[:300]
    return receipt

def summary(rows):
    return {
      "count":len(rows),"errors":sum("error" in x for x in rows),
      "hybrid_exact_original":sum(x.get("hybrid_original_test_correct",False) for x in rows),
      "legacy_exact_original":sum(x.get("legacy_original_test_correct",False) for x in rows),
      "hybrid_only":sum(x.get("hybrid_original_test_correct",False)
                        and not x.get("legacy_original_test_correct",False) for x in rows),
      "legacy_only":sum(x.get("legacy_original_test_correct",False)
                        and not x.get("hybrid_original_test_correct",False) for x in rows),
      "both_correct":sum(x.get("hybrid_original_test_correct",False)
                         and x.get("legacy_original_test_correct",False) for x in rows),
      "new_relation_source_fit":sum(x.get("hybrid_new_relation_source_fit",False) for x in rows),
      "hybrid_search_wall_s":round(sum(x.get("hybrid_total_search_ms",0) for x in rows)/1000,6),
      "legacy_search_wall_s":round(sum(x.get("legacy_search_ms",0) for x in rows)/1000,6),
      "legacy_candidate_checks":sum(x.get("legacy_candidate_checks",0) for x in rows),
      "scope":"hybrid richer executable program grammar vs PRIOR 626-only reference. Both max TWO outputs, but not equal expressive language. No 10x matched-computation claim."}

def source_only():
    source,targets=registries()
    t=time.perf_counter()
    rows=[solve_one(x) for x in source]
    model={"schema":"neumann.q3.relational-composition-hybrid.source.v2",
      "official_upstream_sha":UPSTREAM,
      "previous_v1_source_method_sha256":prior()[1],
      "source_dev_ids":[x.stem for x in source],
      "fresh_target_ids":[x.stem for x in targets],
      "relational_code_sha256":fsha("neumann1/relational_grid_inventor.py"),
      "hybrid_core_code_sha256":fsha("neumann1/hybrid_arc_grid_inventor.py"),
      "previous_strong_classic_code_sha256":fsha("neumann1/arc2_meta_grid_reasoner.py"),
      "this_evaluator_code_sha256":fsha(__file__),
      "source_dev_summary":summary(rows),
      "source_dev_wall_s":round(time.perf_counter()-t,5),
      "source_dev_rows":rows,
      "source_only":True,
      "new_fresh_target_original_bytes_touched":False,
      "original_attempt_cap":2,
      "human_written":"Two-attempt hybrid candidate selection, exact semantic priority, role feature graph, multi-rule composition grammar. Relational Boolean ASTs are task-source induced. Q3 global remains OPEN."}
    model["sha256"]=sha(model)
    pathlib.Path(MODEL).write_text(json.dumps(model,indent=2))
    print(json.dumps({"development":model["source_dev_summary"],
       "source_policy_sha256":model["sha256"],
       "source_wall_s":model["source_dev_wall_s"],
       "target_registry_not_opened":len(targets)},indent=2),flush=True)
    return model

def target_first():
    model=json.loads(pathlib.Path(MODEL).read_text())
    sig=model.pop("sha256")
    if sha(model)!=sig or not model["source_only"]:
        raise ValueError("SOURCE_METHOD_NOT_FROZEN")
    if model["official_upstream_sha"]!=UPSTREAM:
        raise ValueError("UPSTREAM_CHANGED")
    files={"relational_code_sha256":"neumann1/relational_grid_inventor.py",
           "hybrid_core_code_sha256":"neumann1/hybrid_arc_grid_inventor.py",
           "previous_strong_classic_code_sha256":"neumann1/arc2_meta_grid_reasoner.py",
           "this_evaluator_code_sha256":__file__}
    if any(model[k]!=fsha(p) for k,p in files.items()):
        raise ValueError("SOURCE_CODE_CHANGED_AFTER_FREEZE")
    _,targets=registries()
    if model["fresh_target_ids"]!=[p.stem for p in targets]:
        raise ValueError("TARGET_IDS_NOT_FROZEN")
    print("Q3_HYBRID_CODE_AND_NEW_200_ORIGINALS_FROZEN_BEFORE_ANY_NEW_TARGET",sig,flush=True)
    start=time.perf_counter()
    rows=[solve_one(p) for p in targets]
    result={"schema":"neumann.q3.relational-composition-200-new-official-arc2-training-original-FIRST.v1",
       "upstream_sha":UPSTREAM,
       "source_model_sha256":sig,
       "new_untouched_training_originals":len(rows),
       "original_attempt_cap":2,
       "new_target_summary":summary(rows),
       "source_development_summary":model["source_dev_summary"],
       "target_wall_s":round(time.perf_counter()-start,5),
       "rows":rows,
       "frontier_comparison_caveat":"Official frontier ARC-AGI-2 95.0 percent semi-private refers to DIFFERENT original tasks. Our holdout is 200 official TRAINING tasks. No paired frontier compute/cost receipt.",
       "real_q3_status":"SCOPED_EXPRESSION_INVENTION, NOT UNIVERSAL_SELF_INVENTED_META_ALGORITHM",
       "first_rule":"Do not alter or relabel this original first run after reading target labels."}
    pathlib.Path(FIRST).write_text(json.dumps(result,indent=2))
    print(json.dumps(result["new_target_summary"],indent=2),flush=True)
    return result

if __name__=="__main__":
    if sys.argv[1:]==["source"]:source_only()
    elif sys.argv[1:]==["target"]:target_first()
    else:raise SystemExit("source or target")
