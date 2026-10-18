"""Q3O-2 first fixed 40 linear + 16 nonlinear external ORIGINAL SyGuS audit.

All original inputs are read at pinned external git checkout. Original source
and candidate formula text are NEVER output, only hashes+proof metadata.
All expected failures are explicit; no learning, and all Q1-Q7 OPEN.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import first_two_originals as original

REF="6ac90265b11431c9477dfbd33e3e3380234c0499"
SELECTION={"LIA":40,"NIA":16}
ORIGINAL_QUERY_MS=2000

def run(root):
    if original.blobhash((root/"LICENSE.md").read_bytes())!=original.LICENSE_BLOB:
        raise ValueError("PINNED_UPSTREAM_LICENSE_BLOB_CHANGED")
    original.QUERY_MS=ORIGINAL_QUERY_MS
    found=[]
    for logic,cap in SELECTION.items():
        listed=sorted((root/"benchmarks"/logic).rglob("*.sl"))
        if not listed:raise ValueError("NO_UPSTREAM_BENCHMARKS_IN_GROUP_"+logic)
        found.extend([(logic,x) for x in listed[:cap]])
    if not found:raise ValueError("EMPTY_FIRST_SOURCE_SELECTION")
    receipts=[]
    used=set()
    for logic,path in found:
        src=path.read_bytes()
        fingerprint=original.blobhash(src)
        if fingerprint in used:
            details={
                "path":path.relative_to(root).as_posix(),
                "source_git_blob":fingerprint,
                "status":"DUPLICATED_ORIGINAL_BYTES_EXCLUDED",
                "at_least_one_independently_proven_AST_cover":False
            }
        else:
            used.add(fingerprint)
            try:details=original.trial(path,fingerprint)
            except Exception as exc:
                details={
                    "path":path.relative_to(root).as_posix(),
                    "source_git_blob":fingerprint,
                    "status":"UNSUPPORTED_ORIGINAL_SOURCE_OR_BACKEND_ERROR",
                    "error":f"{type(exc).__name__}: {str(exc)[:180]}",
                    "at_least_one_independently_proven_AST_cover":False
                }
        parts=path.relative_to(root).parts
        group="/".join(parts[:3])
        details["original_logic"]=logic
        details["true_original_source_group"]=group
        details["source_rights_inheritance_not_finally_adjudicated"]=True
        if details.get("at_least_one_independently_proven_AST_cover"):
            if details.get("original_initial_states_sat_status")!="sat":
                raise ValueError("CANDIDATE_PROOF_VACUOUS_PRECONDITION")
            assert details["spacer_original_bad_exit_verdict"]=="unsat"
            assert any(x.get("status")=="ALL_ORIGINAL_SYGUS_VCS_UNSAT"
                and all(x.get(c)=="unsat" for c in ("init","inductive","postcondition"))
                for x in details["independently_original_VC_reproved_covers"])
        receipts.append(details)
    verdicts=collections.Counter(x.get("spacer_original_bad_exit_verdict",
                                   x.get("status","UNKNOWN")) for x in receipts)
    proven=[x for x in receipts if x.get("at_least_one_independently_proven_AST_cover")]
    groups=collections.Counter(x["true_original_source_group"] for x in proven)
    per_logic={
      k:{
          "selected_originals":sum(x["original_logic"]==k for x in receipts),
          "original_direct_specialist_unsat":sum(
              x["original_logic"]==k and x.get("spacer_original_bad_exit_verdict")=="unsat"
              for x in receipts),
          "independently_original_3VC_certified_AST_seeds":sum(
              x["original_logic"]==k and x.get("at_least_one_independently_proven_AST_cover")
              for x in receipts),
      } for k in SELECTION
    }
    return {
       "study":"Q3O2_FIXED_FIRST_EXTERNAL_ORIGINAL_SYGUS_PROOF_SEED_CENSUS",
       "status":"FIRST_REAL_EXTERNAL_ORIGINAL_BATCH_RECORDED",
       "source_repo":"SaswatPadhi/LoopInvGen",
       "exact_external_commit":REF,
       "selection_rule":"first 40 lexicographic LIA sl and first 16 lexicographic NIA sl files; include all available if fewer",
       "selected_count":len(found),
       "selected_unique_original_byte_hashes":len(used),
       "source_family_groups_in_selected":len({x["true_original_source_group"] for x in receipts}),
       "direct_SPACER_original_proof_count":sum(x.get("spacer_original_bad_exit_verdict")=="unsat" for x in receipts),
       "independently_3VC_proven_typed_AST_seed_count":len(proven),
       "independently_3VC_proven_AST_source_groups":len(groups),
       "proved_source_group_counts":dict(groups),
       "by_logic":per_logic,
       "original_specialist_verdict_counts":dict(verdicts),
       "fixed_spacer_per_original_timeout_ms":ORIGINAL_QUERY_MS,
       "source_text_or_candidate_formula_exported":False,
       "Q3F_competition_holdout_originals_read":False,
       "any_neural_training":False,
       "any_frontier_API_calls":False,
       "global_Q1_Q7":"OPEN",
       "first_all_source_receipts":receipts
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    x=run(args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(x,indent=2)+"\n")
    print("Q3O2_FIRST_BATCH_SIZE",x["selected_count"],"DIRECT_SOLVER_SAFE",x["direct_SPACER_original_proof_count"],"ACTUAL_THREE_VC_TYPED_SEEDS",x["independently_3VC_proven_typed_AST_seed_count"])
    print("Q3O2_BY_LOGIC",x["by_logic"])
    print("Q3O2_GROUPS",x["proved_source_group_counts"])
    print("Q3O2_STATUS",x["original_specialist_verdict_counts"])
    print("GLOBAL_Q1_Q7",x["global_Q1_Q7"])
