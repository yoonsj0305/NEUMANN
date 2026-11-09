"""SHA-gated original CodeARC POSTFIRST scorer for a failed-model repair study.

This script is launched in a SEPARATE process after all A/B/C programs and
their original input predictions are frozen. It may read original gold. The
proposer/trainer cannot. Results from IDs 184/255 are deliberately
PREEXPOSED DEVELOPMENT and cannot satisfy general Q3 novelty.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from research.q3.q3_source_refutation_pilot import SCHEMA, IDS
from research.q3.q3_two_origins_preregistered import codearc_corpus, _codearc_output


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def score(original, prediction_file, expected_prediction_sha, output):
    if digest(prediction_file)!=expected_prediction_sha:
        raise ValueError("frozen SOURCE+TARGET predictions changed after model inference")
    rows=json.loads(Path(prediction_file).read_text())
    if (rows.get("schema")!=SCHEMA
            or rows.get("original_target_gold_seen") is not False
            or rows.get("model_scientific_scope")!="PREEXPOSED_CODEARC_DEV_ONLY"
            or len(rows.get("records",[]))!=len(IDS)
            or [x["id"] for x in rows["records"]]!=list(IDS)):
        raise ValueError("not a frozen pre-exposed SOURCE repair study")

    originals=codearc_corpus(original)
    scored=[]
    for record in rows["records"]:
        pid=record["id"]
        gold=[_codearc_output(originals[pid][i]) for i in (7,8,9)]
        arm_result={}
        for arm in ("A","B","C"):
            armrow=record["arms"][arm]
            predicted=armrow.get("original_target_predictions",[])
            exact=bool(
                armrow.get("source_verified") is True
                and isinstance(predicted,list)
                and len(predicted)==len(gold)
                and predicted==gold)
            arm_result[arm]=exact
        scored.append({"original_id":pid,**arm_result,
                       "C_only_over_B":arm_result["C"] and not arm_result["B"],
                       "C_only_over_A_and_B":arm_result["C"] and
                           not arm_result["B"] and not arm_result["A"],
                       "B_only_over_C":arm_result["B"] and not arm_result["C"]})
    summary={
        "scope":"PREEXPOSED_CODEARC_POSTFIRST_ONLY",
        "n_original_authors":len(scored),
        "source_predictions_sha256":expected_prediction_sha,
        "original_dataset_sha256":digest(original),
        "pretrained_memory_exact":sum(x["A"] for x in scored),
        "contextual_imitation_equal_step_exact":sum(x["B"] for x in scored),
        "repair_curriculum_equal_step_exact":sum(x["C"] for x in scored),
        "C_only_vs_B":sum(x["C_only_over_B"] for x in scored),
        "C_only_over_A_and_B":sum(x["C_only_over_A_and_B"] for x in scored),
        "B_only_vs_C":sum(x["B_only_over_C"] for x in scored),
        "global_q3":"OPEN",
        "novel_original_independent_first":False,
    }
    Path(output).write_text(json.dumps(
        {"summary":summary,"records":scored},sort_keys=True,indent=2)+"\n")
    print("Q3_POSTFIRST_REPAIR_ORIGINAL_SCORE",
          json.dumps(summary,sort_keys=True),flush=True)
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True)
    p.add_argument("--predictions",required=True)
    p.add_argument("--expected-sha",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    score(args.original,args.predictions,args.expected_sha,args.output)
