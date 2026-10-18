"""Q3I-2 first real frozen Q3G neural candidate ORIGINAL-C proof comparison.

Exactly the historical 32 source-group heldouts, no target labels read,
no retraining/re-decoding. Original proof verifier is the Q3H pycparser/Z3
implementation (scoped finite C). Classical original proofs are bound to
the previously frozen Q3I run, not recomputed or cherry-picked.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,sys,time,zipfile
from pathlib import Path
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3g-real-corpus-20261018"))
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
from train_real_program_invariant import EncoderDecoder,vector,CAP_TARGET
from replay_real_c_loop_invariants import verify

CHECKPOINT_SHA="de16d5be8e92e82de2a08611b79d805da4280ea2b56a39e366ca4460d3ae0091"
Q3G_RECEIPT_SHA="266369a19d8f7fa5f4e76a67130cef2e08f7b50dd49a239a46f0e515b9667b00"
Q3I_CLASSICAL_SHA="cd195fb214e79d1eda9657faa59ac266c4b77969a1ce22dd1eeaa434baec235c"
EXPECTED_Q3I_CLASSICAL=6
EXPECTED_CASES=32

def sha(data):return hashlib.sha256(data).hexdigest()

def run(modelpath:Path,trainreceipt:Path,priorclassical:Path,dataset:Path):
    cp_bytes=modelpath.read_bytes()
    if sha(cp_bytes)!=CHECKPOINT_SHA:raise ValueError("FROZEN_NEURAL_CHECKPOINT_SHA_CHANGED")
    first_json=trainreceipt.read_bytes()
    if sha(first_json)!=Q3G_RECEIPT_SHA:raise ValueError("FROZEN_NEURAL_FIRST_RECEIPT_CHANGED")
    first=json.loads(first_json)
    if first["heldout_examples"]!=EXPECTED_CASES or first["training_examples"]!=105:
        raise ValueError("NEURAL_TRAIN_HOLDOUT_ORIGIN_CHANGED")
    old_bytes=priorclassical.read_bytes()
    if sha(old_bytes)!=Q3I_CLASSICAL_SHA:raise ValueError("FROZEN_CLASSICAL_FIRST_RECEIPT_CHANGED")
    old=json.loads(old_bytes)
    ck=torch.load(io.BytesIO(cp_bytes),map_location="cpu",weights_only=True)
    held=ck["test_source_hashes"]
    training=set(ck["train_source_hashes"])
    if len(held)!=EXPECTED_CASES or len(set(held))!=EXPECTED_CASES:
        raise ValueError("NOT_EXACT_32_HELDOUT_ORIGINALS")
    if training & set(held):raise ValueError("TRAIN_HOLDOUT_DUPLICATE_HASH")
    baseline={r["source_sha256"]:r for r in old["first_originals"]}
    if len(baseline)!=150 or not all(h in baseline for h in held):
        raise ValueError("CLASSICAL_PAIRED_ORIGINAL_IDENTITY_MISSING")
    basewins=sum(baseline[h]["proof"]["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED"
                 for h in held)
    if basewins!=EXPECTED_Q3I_CLASSICAL:
        raise ValueError("FIRST_REPORTED_CLASSICAL_6_OF_32_NOT_REPRODUCED")
    if sha(dataset.read_bytes())!=sha(dataset.read_bytes()):
        raise ValueError("UNREACHABLE")
    target_sources={}
    with zipfile.ZipFile(dataset) as z:
        for item in z.infolist():
            if item.is_dir() or not item.filename.endswith(".c"):continue
            raw=z.read(item)
            h=sha(raw)
            if h not in set(held):continue
            if h in target_sources:raise ValueError("SAME_SOURCE_SHA_MULTIPLE_ARCHIVE_IDENTITIES")
            if item.filename!=baseline[h]["source_path"]:
                raise ValueError("ORIGINAL_SOURCE_PATH_CHANGED")
            target_sources[h]=(item.filename,raw)
    if set(target_sources)!=set(held):
        raise ValueError("FROZEN_NEURAL_TEST_SOURCES_NOT_IN_ORIGINAL_ARCHIVE")
    dictionary=ck["vocabulary"]
    net=EncoderDecoder(len(dictionary))
    net.load_state_dict(ck["state_dict"],strict=True)
    net.eval()
    torch.set_num_threads(2)
    # Match Q3G's 32 heldout source ordering *exactly*.
    texts=[target_sources[h][1].decode("utf-8",errors="replace") for h in held]
    x=torch.tensor(np.stack([vector(t) for t in texts]))
    t0=time.perf_counter_ns()
    sequences=net.generate(x,1,2,CAP_TARGET)
    inference_elapsed=(time.perf_counter_ns()-t0)/1e6
    candidates=["".join(dictionary[i] if 4<=i<len(dictionary) else "" for i in seq)
                for seq in sequences]
    reports=[]
    for h,program,pred in zip(held,texts,candidates):
        name=target_sources[h][0]
        begin=time.perf_counter_ns()
        try:
            raw=verify(program,pred)
            status="NEURAL_ORIGINAL_C_CERTIFIED" if raw["status"]=="ALL_ORIGINAL_LOOP_OBLIGATIONS_UNSAT" else "NEURAL_ORIGINAL_C_NOT_PROVEN"
            evidence={"original_verifier_status":raw["status"],"checks":raw["checks"]}
        except Exception as exc:
            status="NEURAL_ORIGINAL_C_ABSTAIN_PARSE_OR_UNSUPPORTED"
            evidence={"reason_type":type(exc).__name__,
                      "reason_excerpt":str(exc)[:140]}
        original_c=baseline[h]["proof"]
        reports.append({
          "source_path":name,"original_sha256":h,
          "source_group":baseline[h]["group"],
          "model_candidate_sha256":sha(pred.encode()),
          "model_candidate_length":len(pred),
          "model_candidate_original_proof_status":status,
          "verifier_evidence":evidence,
          "classical_original_proof_status":original_c["status"],
          "classical_certificate":original_c["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED",
          "proof_audit_elapsed_ms":round((time.perf_counter_ns()-begin)/1e6,3),
        })
    counts=collections.Counter(r["model_candidate_original_proof_status"] for r in reports)
    neural=sum(r["model_candidate_original_proof_status"]=="NEURAL_ORIGINAL_C_CERTIFIED" for r in reports)
    if neural and not all(
       r["verifier_evidence"]["checks"][k]=="unsat"
       for r in reports if r["model_candidate_original_proof_status"]=="NEURAL_ORIGINAL_C_CERTIFIED"
       for k in ("init","inductive","postcondition","body_signed_overflow","prelude_signed_overflow")
    ):
       raise ValueError("POSSIBLE_FALSE_NEURAL_PROOF")
    return {
      "experiment":"Q3I2_FROZEN_32_SAME_ORIGINAL_C_NEURAL_VS_CLASSICAL_PROOF",
      "frozen_checkpoint_sha256":CHECKPOINT_SHA,
      "original_neural_training_receipt_sha256":Q3G_RECEIPT_SHA,
      "original_classical_150_receipt_sha256":Q3I_CLASSICAL_SHA,
      "model_was_retrained":False,"learned_model_calls":1,
      "actual_original_c_sources_evaluated":len(reports),
      "train_test_source_sha_overlap":0,
      "unmodified_original_source_count":len(reports),
      "classical_whole_original_safety_proofs":basewins,
      "neural_whole_original_safety_proofs":neural,
      "model_original_verification_status_counts":dict(counts),
      "frozen_neural_candidate_generation_ms":round(inference_elapsed,3),
      "original_model_training_historical_exact_string_match":first["model_exact_heldout"],
      "original_model_training_historical_retrieval_exact_string_match":first["retrieval_exact_heldout"],
      "reference_data":"Published genuine C from pinned Loopy dataset; true output published invariants NOT loaded.",
      "reference_input_originals_only":True,
      "q3f_competition_escrow_bodies_accessed":False,
      "global_q1_q7":"OPEN",
      "scientific_scope":"Developer corpus (already used in prior research), Q3G model emits untyped free text, Q3H proof only covers admitted C subset; neither is novel learned operator discovery, Q4 speedup or frontier parity.",
      "per_original":reports
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",required=True,type=Path)
    p.add_argument("--trained-receipt",required=True,type=Path)
    p.add_argument("--classical-receipt",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    r=run(a.checkpoint,a.trained_receipt,a.classical_receipt,a.dataset)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3I2_PAIRED_EXACT_ORIGINAL_C",r["actual_original_c_sources_evaluated"],
      "NEURAL_VERIFIED",r["neural_whole_original_safety_proofs"],
      "CLASSICAL_VERIFIED",r["classical_whole_original_safety_proofs"])
    print("MODEL_VERDICTS",r["model_original_verification_status_counts"])
    print("GLOBAL",r["global_q1_q7"])
