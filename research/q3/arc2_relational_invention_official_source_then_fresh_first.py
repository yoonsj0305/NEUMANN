"""Source-only causal relational AST invention vs untouched official ARC2 training holdout.

A FIRST experiment is run once for the 240 pre-registered untouched training
originals, excluded from all source calibration and from manually inspected
samples. This is NOT the original 120 public evaluation cohort, which was
opened and failed earlier. No tuning against target outcomes is allowed.

Compared:
  1. previously frozen 626-program, two-proposal classical ARC2 baseline;
  2. newly inferred executable relational cell-predicate expressions;
  3. the same relational result with identical original-test scoring.

No paid frontier model is called. Any external published 95% semi-private
figure is context, NOT a matched task-by-task competitor on this holdout.
"""
from __future__ import annotations
import hashlib,json,pathlib,statistics,sys,time
sys.path.insert(0,"neumann1")
import arc2_meta_grid_reasoner as old
from relational_grid_inventor import RelationalGridInventor,grid

ROOT=pathlib.Path("arc2_official/data/training")
POLICY="Q3_RELATIONAL_PROGRAM_LANGUAGE_SOURCE_ONLY_FROZEN.json"
FIRST="Q3_RELATIONAL_NEW_TRAINING_ORIGINALS_240_FIRST.json"
UPSTREAM="f3283f727488ad98fe575ea6a5ac981e4a188e49"
HOLDOUT_N=240
INSPECTED={"f25fbde4","de1cd16c","9565186b"}
OLD_REGISTRY_ALGORITHM="frozen_previous_q3_arc2_source_paths_sha256_v1"

def canonical(d):return json.dumps(d,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(d):return hashlib.sha256(canonical(d).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def registries():
    source,validation=old.source_paths()
    allp=sorted(ROOT.glob("*.json"))
    if len(allp)!=1000:raise ValueError("original ARC2 training count changed")
    seen={p.stem for p in source+validation}|INSPECTED
    fresh=[p for p in allp if p.stem not in seen]
    ordered=sorted(fresh,key=lambda p:sha(("q3.relational.never-opened.eval.v1",p.name)))
    holdout=ordered[:HOLDOUT_N]
    if len(source)!=256 or len(validation)!=128 or len(holdout)!=HOLDOUT_N:
        raise ValueError("source/target registry unavailable")
    if set(p.stem for p in holdout)&seen:
        raise ValueError("source target overlap")
    return source,validation,holdout

def open_training_original(path):
    d=json.loads(path.read_text())
    pairs=[(grid(a["input"]),grid(a["output"])) for a in d["train"]]
    test_inputs=[grid(x["input"]) for x in d["test"]]
    # Original outputs are allowed ONLY after the candidate proposal has
    # been finalized for scoring. Do not pass these to any learner or search.
    target_values=[grid(x["output"]) for x in d["test"]]
    if not 1<=len(pairs)<=10 or not test_inputs:raise ValueError("unsupported original")
    return pairs,test_inputs,target_values

def one(path,miner,score_original=True):
    started=time.perf_counter_ns()
    record={"task_id":path.stem,"original_sha256":file_sha(path)}
    try:
        pairs,inputs,gold=open_training_original(path)
        t=time.perf_counter_ns()
        result=miner.solve(pairs)
        relational_ms=(time.perf_counter_ns()-t)/1e6
        # The predictions are frozen before touching gold for scoring.
        proposal=[miner.apply(result,x) for x in inputs]
        # EXACT legacy full grammar, 2 independently proposed programs,
        # same source demos and same original test target obligation.
        t=time.perf_counter_ns()
        old_matches,old_checks=old.fit_task(
            pairs,tuple(range(len(old.PROGRAMS))),len(old.PROGRAMS),2)
        old_search_ms=(time.perf_counter_ns()-t)/1e6
        old_proposals=[]
        for i,adapter in old_matches:
            old_proposals.append([
                old.recolor(old.predict(x,old.PROGRAMS[i]),adapter["mapping"])
                if old.predict(x,old.PROGRAMS[i]) is not None and
                   adapter["kind"]=="recolor" else
                old.predict(x,old.PROGRAMS[i])
                for x in inputs])
        # For tests with multiple held-out inputs, one program must be correct
        # on all, not a different program arbitrarily chosen per test.
        relational_score=bool(result.source_fit) and all(
            p==y for p,y in zip(proposal,gold))
        old_score=any(all(pred==target for pred,target in zip(guesses,gold))
                      for guesses in old_proposals)
        record.update({
            "source_examples":len(pairs),"target_examples":len(inputs),
            "new_source_fit":result.source_fit,
            "new_target_correct":bool(relational_score),
            "new_kind":result.method["kind"] if result.method else None,
            "new_method":result.method,
            "new_search_ms":round(relational_ms,5),
            "old_source_fit":bool(old_matches),
            "old_target_correct":bool(old_score),
            "old_candidate_checks":old_checks,
            "old_search_ms":round(old_search_ms,5),
            "old_proposed_ids":[int(i) for i,_ in old_matches]})
    except Exception as e:
        record["error"]=type(e).__name__+": "+str(e)[:220]
    record["task_wall_ms"]=round((time.perf_counter_ns()-started)/1e6,5)
    return record

def summarize(rows):
    n=len(rows)
    return {
        "originals":n,"errors":sum("error" in r for r in rows),
        "relational_source_fit":sum(r.get("new_source_fit",False) for r in rows),
        "relational_original_test_correct":sum(r.get("new_target_correct",False) for r in rows),
        "previous_626_grammar_source_fit":sum(r.get("old_source_fit",False) for r in rows),
        "previous_626_grammar_original_test_correct":sum(r.get("old_target_correct",False) for r in rows),
        "new_only_correct":sum(r.get("new_target_correct",False) and
                               not r.get("old_target_correct",False) for r in rows),
        "old_only_correct":sum(r.get("old_target_correct",False) and
                               not r.get("new_target_correct",False) for r in rows),
        "both_correct":sum(r.get("old_target_correct",False) and
                           r.get("new_target_correct",False) for r in rows),
        "new_search_wall_s":round(sum(r.get("new_search_ms",0) for r in rows)/1000,5),
        "old_search_wall_s":round(sum(r.get("old_search_ms",0) for r in rows)/1000,5),
        "old_candidate_checks":sum(r.get("old_candidate_checks",0) for r in rows),
        "candidate_comparison_scope":"new relational predicate induction vs previously frozen finite 626 macro DSL. DIFFERENT expressive capacity, NOT same-language 10x search proof."}

def source_dev():
    training,validation,holdout=registries()
    # No holdout path.read_text, open, or original file bytes anywhere here.
    # Registry enumerates ONLY filenames to make SHA-locked target IDs.
    started=time.perf_counter()
    learner=RelationalGridInventor()
    source_rows=[one(p,learner) for p in training]
    validation_rows=[one(p,learner) for p in validation]
    metadata={
       "schema":"neumann.q3.semantic-relational-program-invention.source-frozen.v1",
       "official_upstream":UPSTREAM,
       "source_ids":[p.stem for p in training],
       "source_validation_ids":[p.stem for p in validation],
       "holdout_ids":[p.stem for p in holdout],
       "excluded_manually_inspected_ids":sorted(INSPECTED),
       "source_code_sha256":file_sha(pathlib.Path("neumann1/relational_grid_inventor.py")),
       "eval_code_sha256":file_sha(pathlib.Path(__file__)),
       "legacy_classical_code_sha256":file_sha(pathlib.Path("neumann1/arc2_meta_grid_reasoner.py")),
       "source_summary":summarize(source_rows),
       "source_validation_summary":summarize(validation_rows),
       "source_method_types":dict(
           __import__("collections").Counter(r["new_kind"] for r in source_rows+validation_rows
                                             if r.get("new_source_fit"))),
       "source_development_wall_s":round(time.perf_counter()-started,5),
       "source_rows":source_rows,
       "validation_rows":validation_rows,
       "blind_target_file_bytes_opened":False,
       "human_coded":"typed spatial features and role vocabulary, symbolic Boolean comparison grammar, greedy minimal disjunction cover, target selection and scoring. The generated new predicate ASTs come only from each original task's source demonstrations."}
    metadata["sha256"]=sha(metadata)
    pathlib.Path(POLICY).write_text(json.dumps(metadata,indent=2))
    print(json.dumps({"source":metadata["source_summary"],
        "validation":metadata["source_validation_summary"],
        "new_method_types":metadata["source_method_types"],
        "holdout_not_opened":True,
        "policy_sha256":metadata["sha256"]},indent=2),flush=True)
    return metadata

def target_first():
    policy=json.loads(pathlib.Path(POLICY).read_text())
    digest=policy.pop("sha256")
    if sha(policy)!=digest or policy["official_upstream"]!=UPSTREAM:
        raise ValueError("SOURCE_FREEZE_CHANGED")
    if policy["source_code_sha256"]!=file_sha(pathlib.Path("neumann1/relational_grid_inventor.py")):
        raise ValueError("INVENTOR_CHANGED_AFTER_SOURCE_FREEZE")
    if policy["eval_code_sha256"]!=file_sha(pathlib.Path(__file__)):
        raise ValueError("EVALUATOR_CHANGED_AFTER_SOURCE_FREEZE")
    if policy["legacy_classical_code_sha256"]!=file_sha(pathlib.Path("neumann1/arc2_meta_grid_reasoner.py")):
        raise ValueError("BASELINE_CHANGED_AFTER_SOURCE_FREEZE")
    _,_,holdout=registries()
    if policy["holdout_ids"]!=[p.stem for p in holdout]:
        raise ValueError("EVALUATION_REGISTRY_CHANGED")
    print("SOURCE_ONLY_EXACT_PROGRAM_FROZEN_BEFORE_NEW_ORIGINAL_TARGET",digest,flush=True)
    start=time.perf_counter()
    learner=RelationalGridInventor()
    rows=[one(p,learner) for p in holdout]
    result={"schema":"neumann.q3.semantic-object-role-relations-new-original-FIRST.v1",
      "original_upstream_commit":UPSTREAM,
      "frozen_source_policy_sha256":digest,
      "original_task_count":len(rows),
      "source_only_development_summary":policy["source_summary"],
      "source_only_validation_summary":policy["source_validation_summary"],
      "summary":summarize(rows),
      "target_execution_wall_s":round(time.perf_counter()-start,5),
      "rows":rows,
      "originals_are":"Unopened in this ARC2 workflow, 240 fixed original tasks from the official TRAINING directory. This is not a replacement for the already-opened 120 public-evaluation FIRST run and is not the frontier semi-private test set.",
      "q3_caveat":"Automatically INDUCED new executable object/color-relation Boolean predicates; feature vocabulary and synthesizer were human-coded, so not universal meta-discovery.",
      "q4_caveat":"Different expressive languages for old vs new arm, so success gains do not demonstrate fixed-capability faster search. Source discovery+train costs and downstream runtime must be amortized."}
    pathlib.Path(FIRST).write_text(json.dumps(result,indent=2))
    print(json.dumps(result["summary"],indent=2),flush=True)
    return result

if __name__=="__main__":
    if sys.argv[1:]==["source"]:source_dev()
    elif sys.argv[1:]==["target"]:target_first()
    else:raise SystemExit("source|target")
