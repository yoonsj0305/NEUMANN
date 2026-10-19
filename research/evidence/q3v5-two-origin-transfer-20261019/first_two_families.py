"""Q3V5: exact preregistered prospective two-origin classical transfer screen.
Public original content MUST NOT be read until after prereg PR #240 comment 6257361975.
Locked classical Q3V4/Git blobs; this script selects files by path only.
"""
import argparse, collections, json, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3v4-proof-portfolio-20261019"))
from first_integrated_original_portfolio import prove_one,synthetic
from first_integrated_original_portfolio import EXPECTED,PROVEN,REV
from first_integrated_original_portfolio import blobhash,LICENSE_GIT_BLOB

FAMILIES=[
 "benchmarks/LIA/2013.OOPSLA_Hola",
 "benchmarks/LIA/2015.FMCAD_Acceleration"
]
MAX_ORIGINALS_PER_FAMILY=4
MIN_ORIGINALS_PER_FAMILY=2

def selected_paths(root):
    selectors=[]
    for group in FAMILIES:
        directory=root/group
        if directory.is_dir():
            paths=sorted(directory.rglob("*.sl"),key=lambda p:p.relative_to(directory).as_posix())
        else:
            paths=[]
        n=len(paths)
        chosen=paths[:min(n,MAX_ORIGINALS_PER_FAMILY)]
        selectors.append({"family":group,"total_source_files":n,
           "eligibility":n>=MIN_ORIGINALS_PER_FAMILY,
           "selection":"FIRST_MIN4_SORTED_SL_FILENAMES",
           "selected_paths":[p.relative_to(root).as_posix() for p in chosen]})
    return selectors

def process(root):
    if blobhash((root/"LICENSE.md").read_bytes())!=LICENSE_GIT_BLOB:
        raise ValueError("UPSTREAM_LICENSE_MISMATCH")
    manifest=selected_paths(root)
    admissible=all(a["eligibility"] for a in manifest)
    controls=synthetic()
    cases=[]
    if admissible:
        for selector in manifest:
            for path in selector["selected_paths"]:
                # prove_one does NOT know family labels, source answers, or output names.
                case=prove_one(root/path,root,len(cases))
                case["predeclared_origin_group"]=selector["family"]
                first=next((a for a in case.get("proofs_attempted",[])
                    if a.get("arm")=="POST_ONLY"),{})
                case["original_source_post_alone_3vc"]=first.get("status","NOT_EVALUATED")
                case["nontrivial_original_safe_proof"]=(
                    case["status"]=="ORIGINAL_THREE_VC_CERTIFIED"
                    and case.get("selected_arm") not in ["POST_ONLY","NO_PROOF",None]
                    and first.get("accepted") is False
                    and any(a.get("arm")==case.get("selected_arm")
                        and a.get("vcs")==EXPECTED and a.get("accepted") is True
                        for a in case.get("proofs_attempted",[]))
                )
                cases.append(case)
    counts={}
    for m in manifest:
        subset=[c for c in cases if c["predeclared_origin_group"]==m["family"]]
        counts[m["family"]]={
          "selected":len(m["selected_paths"]),
          "attempted":len(subset),
          "actual_original_three_vc_proven":sum(
              c["status"]=="ORIGINAL_THREE_VC_CERTIFIED" for c in subset),
          "original_post_alone_proven":sum(c.get("selected_arm")=="POST_ONLY" for c in subset),
          "nontrivial_original_three_vc_proven":sum(
              c.get("nontrivial_original_safe_proof",False) for c in subset),
          "source_only_spacer_unsat_reports":sum(
              c.get("strong_SPACER_raw_original_bad_exit")=="unsat" for c in subset),
          "no_usable_spacer_baseline":sum(
              c.get("strong_SPACER_raw_original_bad_exit")!="unsat" for c in subset),
          "original_native_parity_all_unsat":sum(
              len(c.get("source_semantics_native_xor_parity",{}))==3
              and all(v=="unsat" for v in c["source_semantics_native_xor_parity"].values())
              for c in subset),
          "case_statuses":dict(collections.Counter(c["status"] for c in subset))
        }
    unique_sources=len({c.get("original_source_git_blob") for c in cases})==len(cases)
    zero_parity_mismatch=all(
        len(c.get("source_semantics_native_xor_parity",{}))==3
        and all(v=="unsat" for v in c["source_semantics_native_xor_parity"].values())
        for c in cases)
    all_certificates_exact=all(any(
        x.get("arm")==c.get("selected_arm")
        and x.get("accepted") is True
        and x.get("vcs")==EXPECTED
        for x in c.get("proofs_attempted",[]))
        for c in cases if c["status"]=="ORIGINAL_THREE_VC_CERTIFIED")
    scoped_pass=(
        admissible and len(cases)==sum(len(m["selected_paths"]) for m in manifest)
        and unique_sources and zero_parity_mismatch and all_certificates_exact
        and controls["synthetic_unsafe_mutants"]=="REJECTED_2_OF_2"
        and all(c["nontrivial_original_three_vc_proven"]>=1 for c in counts.values()))
    return {"study":"Q3V5_PROSPECTIVE_TWO_INDEPENDENT_ORIGIN_SAME_FROZEN_CLASSICAL_ALGORITHM",
       "provenance_original_git_rev":REV,
       "status":"FIRST_FROZEN_TRANSFER_PASS" if scoped_pass
          else "FIRST_FROZEN_TRANSFER_FAIL" if admissible else "SOURCE_COHORT_INELIGIBLE",
       "frozen_file_selection_before_source_body":manifest,
       "first_original_cases":cases,
       "by_origin_group":counts,
       "controls":controls,
       "total_sources_attempted":len(cases),
       "all_source_blobs_unique":unique_sources,
       "all_original_xor_parity_unsat":zero_parity_mismatch,
       "all_claimed_original_three_vc_exact":all_certificates_exact,
       "frozen_science_gate_pass":scoped_pass,
       "new_learned_operator":False,"neural_model_calls":0,
       "source_text_opened_before_prereg":False,
       "frontier_same_capability_comparison":False,
       "global_Q1_Q7":"OPEN"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    r=process(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("Q3V5_FROZEN_FAMILY_MANIFEST",json.dumps(r["frozen_file_selection_before_source_body"],sort_keys=True))
    print("Q3V5_ORIGINAL_PER_FAMILY",json.dumps(r["by_origin_group"],sort_keys=True))
    print("Q3V5_FIRST_STATUS",r["status"])
    print("Q3V5_FIRST_GATE",r["frozen_science_gate_pass"])
if __name__=="__main__":main()
