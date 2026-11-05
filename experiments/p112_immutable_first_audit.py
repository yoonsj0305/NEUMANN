"""Read-only P1.12 FIRST actual evidence audit: no model load, training or new score.

Independent from the first scoring module. The raw FIRST receipt is immutable.
This audit recomputes every submitted raw-top position, exact correctness,
lexical control comparison and hard original gate against frozen v2 references.

A receipt cannot cryptographically attest model weight bytes by itself. The
first Python loader requested an exact Hub revision and counted parameters;
an independent model artifact hash was NOT acquired. This limitation is explicit.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256, sha1
import json
import math
from pathlib import Path

FIRST_SHA256="67644a9a29c7ff1a3c4c66cff07207208205e956191ad3333974cc20bbb8c16a"
V1_BLOB="46f5d7bf2b5f10c491999f398b182cab5de3fe5d"
V2_BLOB="2a89fecd65cf042079411b94bc31093280aa7d54"
RUN_ID=42013751594

def blob(path):
    raw=Path(path).read_bytes()
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def verify(root,receipt_bytes):
    root=Path(root)
    path=root/"docs/experiments"
    r=json.loads(receipt_bytes)
    old=json.loads((path/"control_plane_p112_FRESH_FIRST_FROZEN.json").read_text())
    d=json.loads((path/"control_plane_p112_FRESH_FIRST_CORRECTED_FROZEN.json").read_text())
    lock=json.loads((path/"control_plane_p112_FIRST_SOURCE_LOCK.json").read_text())
    errors=[]
    def ensure(cond,reason):
        if not cond:errors.append(reason)
    first_sha=sha256(receipt_bytes).hexdigest()
    ensure(first_sha==FIRST_SHA256,"FIRST_SHA256_MISMATCH")
    ensure(blob(path/"control_plane_p112_FRESH_FIRST_FROZEN.json")==V1_BLOB,"V1_MUTATED")
    ensure(blob(path/"control_plane_p112_FRESH_FIRST_CORRECTED_FROZEN.json")==V2_BLOB,"V2_MUTATED")
    ensure(lock["dataset_blob_sha"]==V2_BLOB and
           lock["first_unmodified_source_git_blob"]==V1_BLOB,"SOURCE_LOCK_DRIFT")
    for filename,sha in lock["source_blobs"].items():
        ensure(blob(root/filename)==sha,"CODE_BLOB_DRIFT_"+filename)
    ensure(len(d["tasks"])==12 and len(r.get("rows",[]))==12,"NOT_TWELVE")
    ensure(r.get("dataset_source_git_blob")==V2_BLOB,"RECEIPT_WRONG_DATASET")
    ensure(r.get("reference_revision")==d["model_revision"],"RECEIPT_WRONG_REVISION")
    ensure(r.get("model_id")==d["model_id"],"RECEIPT_WRONG_MODEL")
    ensure(r.get("parameter_count")==d["expected_parameters"],"RECEIPT_WRONG_PARAMETERS")
    ensure(r.get("actual_pretrained_model_loaded") is True,"NO_REAL_MODEL_REPORTED")
    ensure(r.get("model_training") is False,"TRAINING_NOT_FROZEN")
    ensure(r.get("previous_p111_eval_reused") is False,"LEAKED_PRIOR_STUDY")
    ensure(r.get("inference_inputs_exclude_gold") is True,"REFERENCE_ACCESS")
    ensure(r.get("Q1_Q7")=="OPEN","FALSE_GLOBAL_CLOSURE")
    ensure(old["tasks"][2]["expected_index"]==3 and
           d["tasks"][2]["expected_index"]==0 and
           d["tasks"][2]["candidate_roles"][0]=="buck converter","PRE_INFERENCE_ERRATUM_DRIFT")

    model=0
    lex=Counter({"word":0,"char":0,"constant_first":0})
    correct_ids=[]
    wrong_ids=[]
    top_counts=Counter()
    gold_counts=Counter()
    abstentions=0
    tokens=0
    padded=0
    rowids=[]
    for i,(task,row) in enumerate(zip(d["tasks"],r.get("rows",[]))):
        id=task["id"]
        rowids.append(row.get("id"))
        ensure(row.get("id")==id,"ROW_ID_"+id)
        expect=task["expected_index"]
        gold_counts[expect]+=1
        ensure(row.get("gold_index")==expect,"GOLD_"+id)
        ls=row.get("model_logits")
        if not isinstance(ls,list) or len(ls)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in ls):
            errors.append("LOGITS_"+id)
            continue
        maxval=max(ls)
        winners=[j for j,x in enumerate(ls) if x==maxval]
        chosen=winners[0] if len(winners)==1 else None
        if chosen is None:abstentions+=1
        else:top_counts[chosen]+=1
        ensure(chosen==row.get("raw_candidate"),"ARGMAX_"+id)
        ensure(row.get("status")==("UNIQUE_TOP" if chosen is not None else "ABSTAIN"),"ABSTENTION_"+id)
        hit=chosen is not None and chosen==expect
        ensure(row.get("correct")==hit,"CORRECT_"+id)
        if hit:correct_ids.append(id);model+=1
        else:wrong_ids.append(id)
        for name,pred in row.get("lexical_guesses",{}).items():
            ensure(pred is None or type(pred) is int and 0<=pred<4,"LEXICAL_KIND_"+name+"_"+id)
            if pred==expect:lex[name]+=1
        ensure(row.get("forward_calls")==1,"FORWARD_"+id)
        ensure(type(row.get("input_tokens")) is int and row["input_tokens"]>=0,"INPUT_TOKENS_"+id)
        ensure(type(row.get("padded_tokens")) is int and row["padded_tokens"]>=row["input_tokens"],"PADDED_TOKENS_"+id)
        tokens+=row.get("input_tokens",0)
        padded+=row.get("padded_tokens",0)

    summary=r.get("scores",{})
    best=max(lex.values(),default=0)
    ensure(summary.get("N")==12,"SUMMARY_N")
    ensure(summary.get("cross_correct")==model,"SUMMARY_MODEL_SCORE")
    ensure(summary.get("best_lexical_correct")==best,"SUMMARY_BEST_LEXICAL")
    ensure(summary.get("lexical_baselines")==dict(lex),"SUMMARY_LEXICAL_BASELINES")
    ensure(summary.get("extra_correct_vs_best_lexical")==model-best,"SUMMARY_DELTA")
    ensure(summary.get("actual_forward_calls")==12,"SUMMARY_FORWARDS")
    ensure(summary.get("inputs_tokens")==tokens,"SUMMARY_INPUT_TOKENS")
    ensure(summary.get("padded_tokens")==padded,"SUMMARY_PADDED_TOKENS")
    should_pass=model>=d["raw_top_min_correct"] and model-best>=d["additional_correct_over_best_lexical_min"]
    ensure(should_pass is False and r.get("status")=="P112_LOCAL_OPENED_FAIL","SCIENTIFIC_RESULT_CHANGED")
    ensure(r.get("source_lock_sha256")==sha256((path/"control_plane_p112_FIRST_SOURCE_LOCK.json").read_bytes()).hexdigest(),
           "SOURCE_LOCK_HASH_MISMATCH")

    return {
      "schema":"neumann.p112.immutable-first-independent-audit.v1",
      "first_run_id":RUN_ID,"first_receipt_sha256":first_sha,
      "first_receipt_unchanged":first_sha==FIRST_SHA256,
      "actual_pretrained_forward_count":summary.get("actual_forward_calls"),
      "independent_model_correct":model,
      "independent_lexical_correct":dict(lex),
      "independent_best_lexical_correct":best,
      "additional_correct":model-best,
      "gold_positions":dict(gold_counts),"model_top_positions":dict(top_counts),
      "raw_correct_ids":correct_ids,"raw_wrong_ids":wrong_ids,
      "abstained":abstentions,"N":len(rowids),
      "conditioned_on_author_constructed_opened_tasks":True,
      "exact_artifact_weight_sha256_proven":False,
      "model_family_aptitude_for_generic_role_selection":"NOT_ESTABLISHED",
      "Q3_autonomous_new_semantics":"NOT_PROVEN",
      "Q6_unseen_family_transfer":"NOT_PROVEN",
      "scientific_verdict":"P112_FIRST_FAIL_RETENTION_AND_STOP",
      "auditor_pass":len(errors)==0,
      "errors":errors
    }

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("Usage: python -m experiments.p112_immutable_first_audit REPO_ROOT FIRST_RECEIPT_JSON")
    out=verify(Path(sys.argv[1]),Path(sys.argv[2]).read_bytes())
    print(json.dumps(out,indent=2,sort_keys=True))
    if not out["auditor_pass"]:raise SystemExit(1)
