"""Independent read-only audit of an immutable P1.12 actual first model receipt.

Does not load/fetch/invoke a neural model. No retuning, no modification to the
first run. Reports post-hoc position imbalance only as a limitation, NEVER
as a new preregistered comparator.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from experiments.control_plane_p112_first_fresh_semantics import (
    load_frozen, public_ir, lexical_guesses, canonical
)
from neumann1.control_plane_p112 import select_unique_top

FIRST_SHA256="67644a9a29c7ff1a3c4c66cff07207208205e956191ad3333974cc20bbb8c16a"
SCHEMA="neumann.p112.first-independent-offline-audit.v1"

def audit(raw_file):
    raw=Path(raw_file).read_bytes()
    rawhash=sha256(raw).hexdigest()
    if rawhash!=FIRST_SHA256:raise ValueError("FIRST_ORIGINAL_RECEIPT_HASH_MISMATCH")
    first=json.loads(raw)
    data,lock=load_frozen()
    original=data["tasks"]
    attempt=first["rows"]
    if len(original)!=12 or len(attempt)!=12:raise ValueError("ORIGINAL_COUNT_DRIFT")
    baseline=lexical_guesses(original)
    rechecked=[]
    for idx,(task,got) in enumerate(zip(original,attempt)):
        ir=public_ir(task)
        if got["id"]!=task["id"]:raise ValueError("ORIGINAL_TASK_ORDER_DRIFT")
        if got["public_ir_sha256"]!=sha256(canonical(ir).encode()).hexdigest():
            raise ValueError("PUBLIC_IR_HASH_DRIFT")
        logits=got["model_logits"]
        if type(logits) is not list or len(logits)!=4 or any(
           type(x) not in (int,float) or not math.isfinite(x) for x in logits):
            raise ValueError("INVALID_FIRST_LOGITS")
        try:
            independent=select_unique_top(ir,logits)["selected_candidate_position"]
        except ValueError:
            independent=None
        gold=task["expected_index"]
        if independent!=got["raw_candidate"] or gold!=got["gold_index"]:
            raise ValueError("FIRST_RANKING_OR_REFERENCE_DRIFT")
        if (independent==gold)!=got["correct"]:
            raise ValueError("FIRST_CORRECTNESS_FLAG_DRIFT")
        for name,preds in baseline.items():
            if got["lexical_guesses"][name]!=preds[idx]["winner"]:
                raise ValueError("FIRST_LEXICAL_DRIFT")
        rechecked.append(independent==gold)
    correct=sum(rechecked)
    first_counts={
       name:sum(p["winner"]==task["expected_index"] for p,task in zip(preds,original))
       for name,preds in baseline.items()
    }
    best=max(first_counts.values())
    registered_pass=(correct>=data["raw_top_min_correct"] and
                     correct-best>=data["additional_correct_over_best_lexical_min"])
    if first["scores"]["cross_correct"]!=correct or first["scores"]["best_lexical_correct"]!=best:
        raise ValueError("FIRST_AGGREGATE_SCORE_DRIFT")
    if first["scores"]["lexical_baselines"]!=first_counts or first["scores"]["extra_correct_vs_best_lexical"]!=correct-best:
        raise ValueError("FIRST_COMPARATOR_SCORE_DRIFT")
    if first["scores"]["actual_forward_calls"]!=12 or not first["actual_pretrained_model_loaded"]:
        raise ValueError("NEURAL_EXECUTION_NOT_EVIDENCED")
    if first["status"]!=("P112_LOCAL_OPENED_PASS" if registered_pass else "P112_LOCAL_OPENED_FAIL"):
        raise ValueError("FIRST_GATE_DRIFT")
    counts=Counter(t["expected_index"] for t in original)
    posthoc_positions={str(i):sum(t["expected_index"]==i for t in original) for i in range(4)}
    return {
       "schema":SCHEMA,
       "original_receipt_sha256":rawhash,
       "independent_audit":"PASS",
       "correct":correct,"total":12,
       "registered_best_lexical_correct":best,
       "registered_accuracy_gain":correct-best,
       "registered_first_verdict":first["status"],
       "independent_registered_verdict":"P112_LOCAL_OPENED_PASS" if registered_pass else "P112_LOCAL_OPENED_FAIL",
       "first_original_unchanged":True,
       "no_new_model_inference":True,
       "gold_position_counts":posthoc_positions,
       "posthoc_constant_position_best":max(posthoc_positions.values()),
       "posthoc_warning":"Gold labels are imbalanced (no index 2; index 1 has 6/12). The majority-position oracle is reported only AFTER the first result and was not a preregistered matched control. Do not use this small opened set for claims of generalization.",
       "interpretation":"Current frozen MS MARCO role-ranker FAIL on one fresh opened diagnostic. Not a theorem about cross encoders, training, Q3, frontier intelligence or other task distributions.",
       "global_Q1_Q7":"OPEN",
    }

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python -m experiments.control_plane_p112_first_offline_audit ORIGINAL_FIRST_JSON")
    print(json.dumps(audit(sys.argv[1]),indent=2))
