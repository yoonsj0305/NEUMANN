"""Paired original-author heldout comparison of a genuinely weight-updated Q3 policy.

Gold appears only in the two SHA-gated score files, never the teacher or
prediction process. A positive count alone is not a frontier-level Q3 proof.
"""
import argparse
import hashlib
import json
from pathlib import Path


def compare(base_score,adapted_score,base_predictions,adapted_predictions,
            teacher_jsonl,out):
    bp=Path(base_predictions)
    ap=Path(adapted_predictions)
    b=json.loads(bp.read_text())
    a=json.loads(ap.read_text())
    if b["blind_sha256"]!=a["blind_sha256"]:
        raise ValueError("different heldout originals")
    if (b["model_id"]!=a["model_id"]
            or b["model_revision"]!=a["model_revision"]
            or b.get("adapted_neural_weights",False)
            or not a.get("adapted_neural_weights",False)):
        raise ValueError("model ablation does not isolate weight adaptation")
    x=json.loads(Path(base_score).read_text())
    y=json.loads(Path(adapted_score).read_text())
    if (x["summary"]["sha256_frozen"]!=hashlib.sha256(bp.read_bytes()).hexdigest()
            or y["summary"]["sha256_frozen"]!=hashlib.sha256(ap.read_bytes()).hexdigest()):
        raise ValueError("scored outputs not source-prediction-frozen")
    xmap={r["id"]:r for r in x["records"]}
    ymap={r["id"]:r for r in y["records"]}
    teacher_ids={json.loads(line)["original_id"] for line in
                 Path(teacher_jsonl).read_text().splitlines() if line.strip()}
    if not xmap or set(xmap)!=set(ymap) or set(xmap)&teacher_ids:
        raise ValueError("gold set mismatch or teacher leakage")
    plus=[]
    minus=[]
    both=[]
    for pid in sorted(xmap):
        original=xmap[pid]["revised_original_exact"]
        learned=ymap[pid]["revised_original_exact"]
        if learned and not original:plus.append(pid)
        if original and not learned:minus.append(pid)
        if original and learned:both.append(pid)
    result={
        "schema":"NEUMANN.Q3.NEURAL-POLICY-ADAPTATION-ORIGINAL.v1",
        "heldout_originals":len(xmap),
        "pretrained_correct":len(minus)+len(both),
        "adapted_correct":len(plus)+len(both),
        "adapted_only":len(plus),
        "pretrained_only":len(minus),
        "adapted_only_ids":plus,
        "pretrained_only_ids":minus,
        "pretrained_predictions_sha256":hashlib.sha256(bp.read_bytes()).hexdigest(),
        "adapted_predictions_sha256":hashlib.sha256(ap.read_bytes()).hexdigest(),
        "teacher_sha256":hashlib.sha256(Path(teacher_jsonl).read_bytes()).hexdigest(),
        "weights_updated_in_adapted":True,
        "baseline_same_model_revision":True,
        "scope":"CodeARC POSTFIRST; small same-corpus author family",
        "global_q3_q6":"OPEN"}
    Path(out).write_text(json.dumps(result,indent=2)+"\n")
    print("Q3_NEURAL_WEIGHT_ADAPTATION_RESULT",json.dumps(result,sort_keys=True))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base-score",required=True)
    p.add_argument("--adapted-score",required=True)
    p.add_argument("--base-predictions",required=True)
    p.add_argument("--adapted-predictions",required=True)
    p.add_argument("--teachers",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    compare(args.base_score,args.adapted_score,args.base_predictions,
            args.adapted_predictions,args.teachers,args.output)
