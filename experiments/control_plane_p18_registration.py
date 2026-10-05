"""Model-free P1.8 opened-development registration and construction controls."""
from itertools import product
import hashlib, json
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p17 import build_candidates, compile_references
from neumann1.control_plane_p18 import Budget as P0Budget, prune_candidates
from neumann1.control_plane_p18_semantic import build_semantic_bundle, contract as semantic_contract
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p16_catalog import catalog as p16_catalog
from experiments.control_plane_p17_catalog import catalog as p17_catalog
from experiments.control_plane_p18_catalog import catalog, negative_controls

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"docs/experiments/control_plane_p18.preregister.json"
PUBLIC=ROOT/"docs/experiments/control_plane_p18_public.json"
REFERENCES=ROOT/"docs/experiments/control_plane_p18_references.json"

GATE={
 "observations_exact":8,
 "a_tasks_exact":4,
 "b_tasks_exact":4,
 "overall_accepted_min":7,
 "a_accepted_exact":4,
 "b_accepted_min":3,
 "a_model_calls_exact":0,
 "a_neural_forward_calls_exact":0,
 "b_model_calls_exact":4,
 "b_neural_forward_calls_exact":144,
 "generated_calls_exact":0,
 "feasibility_calls_exact":24,
 "tool_calls_exact":8,
 "verifier_calls_exact":8,
 "semantic_retries":0,
 "selector_wall_ms":180000.0,
 "per_item_wall_ms":240000.0,
 "whole_study_wall_ms":1800000.0,
 "out_of_grammar_controls_exact":4,
}
BOUNDARY={
 "development_only":True,
 "fresh_validation_registered":False,
 "p2_registration_admitted":False,
 "p2_admitted":False,
 "decision3_admitted":False,
 "global_questions_closed":[],
}

def development_architecture():
    return {
      "schema":"neumann.p18-opened-development.v1",
      "stage":"OPENED_DEVELOPMENT_REGISTERED",
      "p0":"P1.8 feasibility-first P0 retained",
      "semantic_selector":semantic_contract(),
      "task_mix":"4 A feasibility-reducible + 4 B multi-feasible public semantic cue",
      "p0_budget":P0Budget().__dict__,
      "first_only":True,
      "actual_gemma_run":"NOT_RUN",
      "complete_cost_accounting_required":True,
      "selector_startup_accounting":"charged once to whole study before B items; excluded from individual B item wall",
      "baseline_rule":"future baselines share extraction/compiler/pruner/tools/checker access",
    }

def _satisfies(project, answer):
    domains,rules=project["domains"],project["constraints"]
    if type(answer) is not dict or set(answer)!=set(domains): return False
    if any(type(answer[k]) is not int or answer[k] not in domains[k] for k in domains): return False
    for op,name,other in rules:
        a=answer[name]; b=answer[other] if type(other) is str else other
        if op=="eq" and a!=b:return False
        if op=="ne" and a==b:return False
        if op=="lt" and not a<b:return False
        if op=="le" and not a<=b:return False
    return True

def _all_answers(project):
    names=sorted(project["domains"])
    for vals in product(*(project["domains"][k] for k in names)):
        ans=dict(zip(names,vals))
        if _satisfies(project,ans): yield ans

def registration():
    reg=json.loads(REG.read_bytes())
    rows=json.loads(PUBLIC.read_bytes())["rows"]
    refs=json.loads(REFERENCES.read_bytes())["rows"]
    if (rows,refs)!=catalog(): raise ValueError("P1.8 catalog content drift")
    if reg["architecture"]!=development_architecture() or reg["gate"]!=GATE or reg["boundaries"]!=BOUNDARY:
        raise ValueError("P1.8 registration architecture/gate drift")
    if reg["scores_seen_at_registration"] is not False or reg["first_only"] is not True:
        raise ValueError("P1.8 pre-score first-only registration required")
    if reg["task_ids"]!=[r["task_id"] for r in rows] or reg["task_ids"]!=[r["task_id"] for r in refs]:
        raise ValueError("P1.8 task order drift")
    if digest(rows)!=reg["public_sha256"] or digest(refs)!=reg["references_sha256"]:
        raise ValueError("P1.8 data hash drift")
    for path,expected in reg["source_sha256"].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError("P1.8 source byte drift: "+path)
    return reg,rows,refs

def check_construction():
    _,rows,refs=registration()
    previous=set()
    for old in (p16_catalog()[0],p17_catalog()[0]):
        for r in old:
            previous.add(" ".join(r["view"]["public"]["query"].lower().split()))
    queries=[" ".join(r["view"]["public"]["query"].lower().split()) for r in rows]
    if len(set(queries))!=len(rows) or set(queries)&previous:
        raise ValueError("opened raw obligation duplication")

    candidate_counts=[]; a_unique=0; b_multi=0
    for i,(row,ref) in enumerate(zip(rows,refs)):
        parsed,bundle=build_semantic_bundle(row["view"])
        count=len(bundle["candidates"]); candidate_counts.append(count)
        pruning=prune_candidates(parsed,bundle)
        if pruning["unknown_indexes"]: raise ValueError("construction feasibility UNKNOWN")
        expected=ref["expected_candidate"]
        if i<4:
            if pruning["sat_indexes"]!=[expected]: raise ValueError("A must reduce to exactly expected candidate")
            a_unique+=1
        else:
            if len(pruning["sat_indexes"])<2 or expected not in pruning["sat_indexes"]:
                raise ValueError("B must remain genuinely multi-feasible")
            # Every expected-candidate solution must agree with the authored
            # original obligation, and every wrong candidate must be disjoint.
            checker=_checker(ref)
            for idx in pruning["sat_indexes"]:
                project=compile_references(parsed,bundle,idx)["public"]
                answers=list(_all_answers(project))
                if not answers: raise ValueError("SAT candidate without exhaustive witness")
                overlap=[a for a in answers if checker(a)]
                if idx==expected:
                    if not overlap: raise ValueError("expected B candidate has no original-valid answer")
                elif overlap:
                    raise ValueError("wrong B candidate overlaps private original obligation")
            b_multi+=1
        if not _checker(ref)(ref["witness"]): raise ValueError("positive checker control rejected")
        bad={k:987654321 for k in ref["private"]["domains"]}
        if _checker(ref)(bad): raise ValueError("negative checker control accepted")

    stopped=0
    for view in negative_controls():
        try:
            build_semantic_bundle(view)
        except Exception:
            stopped+=1
        else:
            raise ValueError("negative control admitted")

    return {
      "registration_valid":True,
      "observations":8,
      "a_tasks":a_unique,
      "b_tasks":b_multi,
      "candidate_counts":candidate_counts,
      "out_of_grammar_stops":stopped,
      "model_inference":False,
      "weights_loaded":False,
      **BOUNDARY,
    }

if __name__=="__main__":
    print(json.dumps(check_construction(),sort_keys=True))
