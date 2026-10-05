"""Model-free P1.10 opened-development registration and construction controls."""
from itertools import product
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import prune_candidates
from neumann1.control_plane_p110 import contract as p110_contract, minimal_semantic_contrast
from neumann1.control_plane_p110_semantic import build_bundle, contract as semantic_contract
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p16_catalog import catalog as p16_catalog
from experiments.control_plane_p17_catalog import catalog as p17_catalog
from experiments.control_plane_p18_catalog import catalog as p18_catalog
from experiments.control_plane_p19_catalog import catalog as p19_catalog
from experiments.control_plane_p110_catalog import catalog, negative_controls

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"docs/experiments/control_plane_p110.preregister.json"
PUBLIC=ROOT/"docs/experiments/control_plane_p110_public.json"
REFERENCES=ROOT/"docs/experiments/control_plane_p110_references.json"

GATE={
 "observations_exact":8,"accepted_min":6,"model_calls_exact":8,"neural_forward_calls_exact":16,
 "generated_calls_exact":0,"feasibility_calls_exact":23,"selector_complete_exact":8,
 "selector_wall_ms":60000.0,"per_item_wall_ms":90000.0,"whole_study_wall_ms":900000.0,
 "out_of_grammar_controls_exact":4,
}
BOUNDARY={
 "development_only":True,"fresh_validation_registered":False,"p2_registration_admitted":False,
 "p2_admitted":False,"decision3_admitted":False,"global_questions_closed":[],
}
COUNTS=[2,3,4,2,3,4,3,2]
EXPECTED_FORWARDS=[2]*8

def development_architecture():
    return {
      "stage":"OPENED_DEVELOPMENT_REGISTERED",
      "p0":"P1.10 minimal semantic contrast symmetric pairwise selector",
      "task_mix":"8 fresh multi-feasible semantic binding tasks",
      "semantic_ir":"SOURCE_BOUND_MINIMAL_PRONOUN_BINDING_CONTRAST",
      "response_semantics":{"A":"LEFT_BINDING_MORE_FAITHFUL","B":"RIGHT_BINDING_MORE_FAITHFUL"},
      "pair_orientations":"BOTH",
      "winner_rule":"UNIQUE_CONDORCET_ABOVE_MARGIN",
      "modes":["batch_all","reverse_batch_all"],
      "forward_calls_per_item":2,
      "first_only":True,"actual_gemma_run":"NOT_RUN","complete_cost_accounting_required":True,
      "baseline_rule":"future baselines share extraction, feasibility pruning, compiler, specialist and original verifier access",
    }

def _satisfies(project,answer):
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
    reg=json.loads(REG.read_bytes()); rows=json.loads(PUBLIC.read_bytes())["rows"]; refs=json.loads(REFERENCES.read_bytes())["rows"]
    if (rows,refs)!=catalog(): raise ValueError("P1.10 catalog content drift")
    if reg["architecture"]!=development_architecture() or reg["gate"]!=GATE or reg["boundaries"]!=BOUNDARY:
        raise ValueError("P1.10 registration architecture/gate drift")
    if reg["scores_seen_at_registration"] is not False or reg["first_only"] is not True:
        raise ValueError("P1.10 pre-score first-only registration required")
    if reg.get("p19_opened_task_score_reuse") is not False: raise ValueError("P1.9 score reuse forbidden")
    ids=[r["task_id"] for r in rows]
    if reg["task_ids"]!=ids or ids!=[r["task_id"] for r in refs]: raise ValueError("P1.10 task order drift")
    if reg["candidate_counts"]!=COUNTS: raise ValueError("P1.10 candidate-count drift")
    if reg["expected_candidate_positions"]!=[r["expected_candidate"] for r in refs]: raise ValueError("P1.10 expected-position drift")
    if digest(rows)!=reg["public_sha256"] or digest(refs)!=reg["references_sha256"]: raise ValueError("P1.10 data hash drift")
    core=p110_contract()
    if core["forward_calls_per_item"]!=2 or core["pair_orientations"]!="BOTH":
        raise ValueError("P1.10 P0 core drift")
    if core["future_actual_requires_new_registered_tasks"] is not True or core["p19_opened_tasks_model_score_reuse"] is not False:
        raise ValueError("P1.10 fresh-task boundary drift")
    if semantic_contract()["p19_task_reuse"] is not False: raise ValueError("P1.10 semantic registry reuse drift")
    return reg,rows,refs

def check_construction():
    _,rows,refs=registration()
    previous=set()
    for old in (p16_catalog()[0],p17_catalog()[0],p18_catalog()[0],p19_catalog()[0]):
        for r in old: previous.add(" ".join(r["view"]["public"]["query"].lower().split()))
    queries=[" ".join(r["view"]["public"]["query"].lower().split()) for r in rows]
    if len(set(queries))!=len(rows) or set(queries)&previous: raise ValueError("P1.10 raw obligation duplication")

    counts=[]; multi=0; contrast_bindings=[]
    for row,ref in zip(rows,refs):
        parsed,bundle=build_bundle(row["view"]); count=len(bundle["candidates"]); counts.append(count)
        pruning=prune_candidates(parsed,bundle)
        if pruning["unknown_indexes"]: raise ValueError("P1.10 construction feasibility UNKNOWN")
        if pruning["sat_indexes"]!=list(range(count)): raise ValueError("P1.10 set must remain fully multi-feasible")
        contrast=minimal_semantic_contrast(row["view"],parsed,bundle,pruning["sat_indexes"])
        contrast_bindings.append([b["entity"]["surface"] for b in contrast["bindings"]])
        expected=ref["expected_candidate"]
        if expected not in pruning["sat_indexes"]: raise ValueError("expected P1.10 candidate infeasible")
        checker=_checker(ref)
        for idx in pruning["sat_indexes"]:
            project=compile_references(parsed,bundle,idx)["public"]; answers=list(_all_answers(project))
            if not answers: raise ValueError("SAT candidate without exhaustive witness")
            overlap=[a for a in answers if checker(a)]
            if idx==expected:
                if not overlap: raise ValueError("expected P1.10 candidate has no original-valid answer")
            elif overlap: raise ValueError("wrong P1.10 candidate overlaps private original obligation")
        if not checker(ref["witness"]): raise ValueError("P1.10 positive checker control rejected")
        bad={k:987654321 for k in ref["private"]["domains"]}
        if checker(bad): raise ValueError("P1.10 negative checker control accepted")
        multi+=1

    stopped=0
    for view in negative_controls():
        try: build_bundle(view)
        except Exception: stopped+=1
        else: raise ValueError("P1.10 negative control admitted")
    if counts!=COUNTS: raise ValueError("P1.10 prospective candidate shape drift")
    return {
      "registration_valid":True,"observations":8,"multi_feasible_tasks":multi,"candidate_counts":counts,
      "expected_forward_calls":EXPECTED_FORWARDS,"total_expected_forward_calls":sum(EXPECTED_FORWARDS),
      "contrast_bindings":contrast_bindings,"out_of_grammar_stops":stopped,
      "model_inference":False,"weights_loaded":False,**BOUNDARY,
    }

if __name__=="__main__":
    print(json.dumps(check_construction(),sort_keys=True))
