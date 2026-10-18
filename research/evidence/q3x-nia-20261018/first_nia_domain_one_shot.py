"""Q3X: first genuinely different nonlinear-integer benchmark domain test.

Original algorithm imported unchanged from Q3W first pre-registered attempt.
No new source content read until frozen path-only selection.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3w-oraclefree-cegis-20261018"))
import affine_hull_original_cegis as core

FIRST_PREREG="c0c99a9a9fd5675518a10e414d250e1c6158d36b"

def select_nia_only_paths(root):
    base=root/"benchmarks"/"NIA"
    if not base.is_dir():
        raise ValueError("PINNED_EXTERNAL_NIA_DIRECTORY_NOT_PRESENT")
    families=[]
    for sub in sorted(x for x in base.iterdir() if x.is_dir()):
        files=sorted(
            (x for x in sub.rglob("*.sl")
             if not any(y.startswith("~") for y in x.relative_to(sub).parts)),
            key=lambda x:x.relative_to(root).as_posix()
        )
        if len(files)>=2:
            families.append((sub.relative_to(root).as_posix(),files))
    if len(families)<2:
        raise ValueError("TWO_NIA_FROZEN_SOURCE_GROUPS_NOT_AVAILABLE")
    chosen=families[:2]
    allfiles=[p for _,files in chosen for p in files[:4]]
    if len({x.relative_to(root).as_posix() for x in allfiles})!=len(allfiles):
        raise ValueError("DUPLICATE_NIA_SOURCE_PATH")
    return [g for g,_ in chosen],allfiles,[
        {"family":g,"all_files_filename_only":len(fs)} for g,fs in families
    ]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    t0=time.perf_counter_ns()
    if core.blobhash((a.root/"LICENSE.md").read_bytes())!=core.LICENSE_BLOB:
        raise ValueError("PINNED_UPSTREAM_LICENSE_CHANGED")
    newgroups,paths,family_meta=select_nia_only_paths(a.root)
    # No original SOURCE contents touched above. Freeze source identities as read.
    controls=core.synthetic_strict_controls()
    historical=core.historical_paths(a.root)
    old=[core.evaluate_original(a.root,p,"PREVIOUSLY_OPENED_LIA_DEVELOPMENT") for p in historical]
    new=[core.evaluate_original(a.root,p,"NEW_NIA_FROZEN_GROUP_PROSPECTIVE") for p in paths]
    allruns=old+new
    if len(set(r["source_blob"] for r in allruns))!=len(allruns):
        raise ValueError("DUPLICATE_CONTENT_SHA_ACROSS_FIXED_ORIGINALS")
    per_group={}
    for group in newgroups:
        members=[r for r in new if r["source"].startswith(group+"/")]
        per_group[group]={
            "count":len(members),
            "parsed_and_formally_compared":sum(
                r["status"]=="COMPLETE_ORIGINAL_SOURCE_COMPARISON" for r in members),
            "non_post_only_original_3vc_certified":sum(
                r["nontrivial_source_only_discovery"] for r in members),
            "direct_spacer_original_safety_solved":sum(
                r.get("original_specialist_spacer_status")=="unsat" for r in members),
            "statuses":[r["status"] for r in members],
            "failure_categories":[r.get("reason_code") for r in members]
        }
    pass_gate=all(per_group[g]["non_post_only_original_3vc_certified"]>=1
                  for g in newgroups)
    result={
        "study":"Q3X_FIRST_ORACLE_FREE_CEGIS_TWO_NONLINEAR_NIA_ORIGINS",
        "status":"COMPLETE_FROZEN_NIA_PROSPECTIVE_RESULT",
        "preregistered_before_source_read_commit":FIRST_PREREG,
        "q3w_first_no_unused_LIA_origin_groups_error_preserved":True,
        "pinned_source_revision":core.UPSTREAM,
        "same_q3w_frozen_oracle_free_discovery_implementation":True,
        "synthetic_controls":controls,
        "historical_original_count":len(old),
        "nia_filename_only_available_family_metadata":family_meta,
        "nia_frozen_new_origin_groups":newgroups,
        "nia_first_original_count":len(new),
        "nia_original_per_case_receipts":new,
        "historical_per_case_receipts":old,
        "nia_witnesses_beyond_post_only":sum(r["nontrivial_source_only_discovery"]
                                           for r in new),
        "historical_witnesses_beyond_post_only":sum(
            r["nontrivial_source_only_discovery"] for r in old),
        "nia_two_distinct_origin_group_gate":pass_gate,
        "nia_per_group_result":per_group,
        "neural_forwards":0,
        "gold_or_oracle_source_invariants_used":False,
        "q3f_two_sealed_chc_originals_opened":False,
        "global_Q1_Q7":"OPEN",
        "full_study_wall_ms":round((time.perf_counter_ns()-t0)/1e6,3)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3X_FIRST_NIA_ORIGINAL_RESULTS",json.dumps({
        "groups":newgroups,
        "gate":pass_gate,
        "nia_wins":result["nia_witnesses_beyond_post_only"],
        "historic_wins":result["historical_witnesses_beyond_post_only"],
        "per_group":per_group,
        "synthetic_controls_pass":controls["pass"],
        "global":result["global_Q1_Q7"]
    },sort_keys=True))
if __name__=="__main__":main()
