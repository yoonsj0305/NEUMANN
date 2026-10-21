"""Posthoc remaining genuine DRAGON_4 exact source Post safety k<=8,
without editing original source, zero neural calls. The first 1..3 failed.
"""
import argparse,json
from pathlib import Path
from research.evidence.q3_affine_unopened_transfer_20261021 import four_original_post_k_induction_affine as program

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    frozen=json.loads(args.freeze.read_text())
    selected=[e for e in frozen["source_targets"] if e["path"].endswith("/DRAGON_4.lus.sl")]
    if len(selected)!=1 or selected[0]["git_blob"]!="455422332af42a42d5f9c61562e1912f13bc2946":
        raise RuntimeError("IMMUTABLE_ORIGINAL_DRAGON4_ID_CHANGED")
    program.MAX_K=8
    row=program.check_case(args.root,selected[0])
    report={
        "schema":"neumann.q3.remaining_DRAGON4_orig_post_k8.v1",
        "development_after_first_k3_failed":True,
        "historical_first_3_of_4_safety_preserved":True,
        "same_source_blob":"455422332af42a42d5f9c61562e1912f13bc2946",
        "max_k":8,
        "real_published_Post_safety_proved":row["actual_full_original_Post_proven"],
        "learning_inference":0,"training_steps":0,"paid_API":0,
        "global_Q3":"OPEN",
        "original":row,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("DRAGON4_ORIGINAL_PUBLISHED_POST_K8", "PASS" if report["real_published_Post_safety_proved"] else "UNPROVED")
    print("FIRST_SUCCESS_K",row.get("first_full_success_k","NONE"))
    for item in row.get("proof_trials",[]):
        print("K_GATE",item["k"],"AFFINE",item["uses_affine"],"OUTCOME",item["status"])
if __name__=="__main__":
    main()
