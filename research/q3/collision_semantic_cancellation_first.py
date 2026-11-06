"""FIRST frozen semantic-relevance challenge for the prior trained H0 grower.

No training, no resampling, no source-original access. The original trained
policy from GitHub Actions FIRST must classify semantic dependency, not lexical
source-array mention. Independent SMT collision oracle labels each expression.
The oracle is also a powerful equal-rights classical baseline, not 'student'.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.q3.counterexample_representation_grower import (
    task_from, score, count_source_reads, witness_script, solver
)

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/experiments/Q3_CEX_SEMANTIC_CANCELLATION_FIRST_PREREG_2026_11_06.json"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def first_readonly(first_file:Path, output:Path)->dict:
    cfg=json.loads(CONTRACT.read_text())
    original=first_file.read_bytes()
    pre=cfg["original_first"]
    if sha(original)!=pre["original_JSON_sha256"]:
        raise ValueError("ORIGINAL_FIRST_RESULT_BYTES_DRIFT")
    old=json.loads(original)
    if old.get("scientific_status")!="PASS_SCOPED_COLLISION_TO_TYPED_RELATION":
        raise ValueError("NOT_FIRST_HISTORIC_MODEL_RESULT")
    if old.get("learned_checkpoint_sha256")!=pre["checkpoint_sha256"]:
        raise ValueError("ORIGINAL_FIRST_MODEL_HASH_DRIFT")
    ck=old["learned_checkpoint"]
    ckbytes=(json.dumps(ck,sort_keys=True,separators=(",",":"))+"\n").encode()
    if sha(ckbytes)!=pre["checkpoint_sha256"]:
        raise ValueError("FROZEN_TRAINED_WEIGHTS_NOT_REPRODUCIBLE")
    weights=tuple(ck["weights"])
    rows=[]
    for sample in cfg["preregistered_heldout_not_in_initial_first"]:
        task=task_from(sample)
        # Compute and freeze prediction before THIS target's independent Z3 oracle.
        trained=score(weights,task["expr"])>0
        untrained=score((0.0,0.0,0.0),task["expr"])>0
        naive_classical=count_source_reads(task["expr"])>0
        proved=solver(witness_script(task),limit_s=5)
        if proved["verdict"] not in ("sat","unsat"):
            raise RuntimeError("ORIGINAL_SEMANTIC_REFERENCE_UNKNOWN_NO_FAVORABLE_RESULT")
        semantically_requires_source=proved["verdict"]=="sat"
        rows.append({
          "expr_SHA256":sha(json.dumps(task,sort_keys=True).encode()),
          "source_AST_has_lexical_reads":naive_classical,
          "semantic_collision_oracle":proved,
          "requires_H0_expansion_proved_from_Z3":semantically_requires_source,
          "frozen_trained_predicted_expansion":trained,
          "frozen_untrained_predicted_expansion":untrained,
          "syntactic_classical_predicted_expansion":naive_classical,
          "trained_correct":trained==semantically_requires_source,
          "untrained_correct":untrained==semantically_requires_source,
          "syntactic_classical_correct":naive_classical==semantically_requires_source,
          "semantic_SMT_classical_correct":True,
          "no_new_human_H1_target_label_given_to_student":True
        })
    stats={
       "original_author_created_adversarial_examples":len(rows),
       "trained_frozen_correct":sum(x["trained_correct"] for x in rows),
       "untrained_correct":sum(x["untrained_correct"] for x in rows),
       "syntax_only_classical_correct":sum(x["syntactic_classical_correct"] for x in rows),
       "semantic_classical_solver_correct":len(rows),
       "truly_semantically_source_relevant":sum(x["requires_H0_expansion_proved_from_Z3"] for x in rows),
       "source_read_syntax_but_no_semantic_dependence":sum(
          x["source_AST_has_lexical_reads"] and
          not x["requires_H0_expansion_proved_from_Z3"] for x in rows),
       "new_model_training":0,
       "new_original_CHC_source_access":0,
       "semantic_SMT_calls":len(rows)
    }
    outcome={
      "schema":"neumann.q3.frozen-collision-trained-semantic-relevance-adversary-FIRST.v1",
      "scientific_status":("PASS_SEMANTIC_RELEVANCE" if stats["trained_frozen_correct"]==len(rows)
                           else "FAIL_SEMANTIC_RELEVANCE_LEXICAL_PROXY"),
      "first_original_train_and_eval_run":pre["run"],
      "exact_original_FIRST_json_sha256":sha(original),
      "original_frozen_learned_model_sha256":sha(ckbytes),
      "sourcefree_scientific_scope":True,
      "original_FIRST_8_OF_8_UNCHANGED":True,
      "learned_true_new_operator_outside_human_compiler":False,
      "Q3":"OPEN","Q4":"OPEN","Q5":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "stats":stats,"first_rows":rows
    }
    output.write_text(json.dumps(outcome,sort_keys=True,indent=2)+"\n")
    return outcome


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--first",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=first_readonly(a.first,a.out)
    print(json.dumps({k:v for k,v in result.items() if k!="first_rows"},sort_keys=True,indent=2))
    if result["scientific_status"]!="PASS_SEMANTIC_RELEVANCE":
        raise SystemExit(1)


if __name__=="__main__":
    main()
