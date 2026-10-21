"""Posthoc strong source-native SyGuS original-Post 3VC on ALL four frozen sources.

This is a stronger goal than original affine 2VC. Reuses pinned untouched
source blobs from the BEFORE-source freeze commit, but now sources are OPENED
by the previous affine run. Classical only; unmatched neural contribution 0.
"""
import argparse
import json
from pathlib import Path
from research.evidence.q3_gater_relational_mixed_20261020.posthoc_independent_source_cvc5_invariant_3vc import original_case

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    frozen=json.loads(x.freeze.read_text())
    if frozen["first_freeze_presource_commit"] if "first_freeze_presource_commit" in frozen else False:
        raise RuntimeError("FROZEN_METADATA_SCHEMA_CHANGED")
    if frozen["upstream_commit"]!="13c8deb68a873635879c9a69bc78caebd340f646" or len(frozen["source_targets"])!=4:
        raise RuntimeError("PREGISTERED_SOURCES_CHANGED")
    results=[original_case(x.root,e["path"],e["git_blob"]) for e in frozen["source_targets"]]
    report={
        "schema":"neumann.q3.four_original_posthoc_native_sygus_published_post_3VC.v1",
        "source_identity_frozen_prior_affine_commit":"8e6efc5b5a6f637ac6b92fbb459616e30ce97072",
        "this_run_after_four_original_source_opened":True,
        "no_neural_learning_or_training":True,
        "actual_original_source_3VC_Z3_cvc5_dual_success":sum(r["dual_original_full_3VC"] for r in results),
        "all_four_rows_retained":len(results)==4,
        "global_Q3":"OPEN",
        "no_learned_operator_new":True,
        "rows":results,
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("PUBLISHED_FULL_3VC_ORIGINAL_CLASSICAL_PASS",
          report["actual_original_source_3VC_Z3_cvc5_dual_success"],"/4")
    print("GLOBAL_Q3", report["global_Q3"])
if __name__=="__main__":
    main()
