"""Q3: same frozen pretrained neural inventor, three evidence transport modes.

A: no remembered method.
B: previously deployed, irrelevant SHA-ordered two methods.
C: ONLY previously certified methods which pass the CURRENT original SOURCE
   more often than a constant-output baseline, with mismatch witnesses.

The proposal model, seed, SOURCE budget, Docker, program ISA and authorized
original IDs are IDENTICAL across A/B/C. This is an interface causal
ablation, NOT a learned general autonomous invention proof.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
from neumann1.q3_single_discovery_core import (
    SingleDiscoveryCore,SourceMethodMemory)
from research.q3.q3_two_origins_preregistered import (
    codearc_corpus,_codearc_output)

# Exact initial prefix of previously exposed 8 original CodeARC problems in
# run #42593621076. NEVER relabel as previously unseen.
IDS=(255,921,184,116)
SCHEMA="NEUMANN.Q3.SOURCE-GROUNDED-METHOD-ABLATION.v1"
ORIGINAL_SHA="3f08820594d4825c78bbdcc3b8eb2e6c8c0285fb3de966e900463b53f1723962"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def infer(blind,teachers,revision,out):
    inp=json.loads(Path(blind).read_text())
    if inp.get("schema")!="NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1":
        raise ValueError("only immutable prior real-author CodeARC blind allowed")
    entries={r["id"]:r for r in inp["records"]}
    if set(IDS)-set(entries):
        raise ValueError("previously opened original cohort missing")
    runner=IsolatedPython(max_seconds=8)
    memory=SourceMethodMemory(runner)
    teacher_rows=[json.loads(line) for line in
                  Path(teachers).read_text().splitlines() if line.strip()]
    memory.import_source_teachers(teacher_rows)
    memory.freeze()
    # One and the same model object and pinned checkpoint for ALL three arms.
    policy=LocalCausalCodePolicy(
        model_revision=revision,max_new_tokens=384,
        temperature=0.3,paired_sampling=True)
    results=[]
    for pid in IDS:
        row=entries[pid]
        source=row["source"]
        if len(source)!=7 or len(row["target_inputs"])!=3:
            raise ValueError("original train and target input count changed")
        original_train=source[:6]
        original_check=source[6:]
        # One hash fixed BEFORE examining predictions, shared by all arms:
        # different text contexts cannot silently alter RNG sampling.
        shared_seed=(1007+int(hashlib.sha256(
            ("Q3-EVIDENCE-TRANSFER-DEV-V1/"+str(pid)).encode()
            ).hexdigest()[:8],16))%(2**31)
        receipt={"id":pid,"seed":shared_seed,"arms":{},
                 "original_source_output_diversity":len({
                   json.dumps(p[1],sort_keys=True) for p in source})}
        for arm,reuse,mode in [
                ("A",False,"sha"),
                ("B",True,"sha"),
                ("C",True,"source_grounded")]:
            policy.seed=shared_seed
            outcome=SingleDiscoveryCore(
                policy,runner,memory=memory,max_proposals=2).discover(
                original_train,original_check,
                reuse_memory=reuse,memory_mode=mode)
            discovery=outcome.discovery
            arm_row={
                "source_verified":bool(discovery.verified),
                "status":discovery.status,
                "method_context_sha256":outcome.source_context_sha256,
                "program":discovery.program if discovery.verified else None,
                "program_sha256":discovery.frozen_sha256,
                "original_target_predictions":[],
                "attempts":[{
                    "iteration":a.iteration,
                    "source_correct":a.source_correct,
                    "source_total":a.source_total,
                    "status":a.status,
                    "program_sha256":a.sha256,
                    "program_source":a.program}
                    for a in discovery.attempts],
            }
            if discovery.verified:
                pred=runner.evaluate(
                    discovery.program,row["target_inputs"])
                if pred.status=="EXECUTED":
                    arm_row["original_target_predictions"]=list(pred.outputs)
            receipt["arms"][arm]=arm_row
        results.append(receipt)
        print("Q3_SOURCE_GROUNDED_TRANSFER",
              pid,{
                a:(r["source_verified"],
                   [x["source_correct"] for x in r["attempts"]])
                for a,r in receipt["arms"].items()},flush=True)
        Path(str(out)+".SOURCE_ONLY_PARTIAL").write_text(
            json.dumps({"source_only":True,"results":results})+"\n")
    report={
        "schema":SCHEMA,
        "task_ids":list(IDS),
        "scope":"PREVIOUSLY_OPENED_DEV_ONLY",
        "source_blind_sha256":digest(blind),
        "prior_certified_method_sha256":digest(teachers),
        "model_revision":revision,
        "paired_noise_across_arms":True,
        "programs_generated_by_same_pretrained_neural_policy":True,
        "no_original_gold_in_inference":True,
        "results":results,
        "q3_global":"OPEN",
    }
    Path(out).write_text(json.dumps(
        report,sort_keys=True,ensure_ascii=True,indent=2)+"\n")
    print("Q3_SOURCE_GROUNDED_PREDICTIONS_FROZEN_SHA256",digest(out),flush=True)


def score(original,blind,predictions,expected_sha,out):
    if digest(predictions)!=expected_sha:
        raise ValueError("not an immutable pre-gold model prediction")
    r=json.loads(Path(predictions).read_text())
    if (r.get("schema")!=SCHEMA or r.get("task_ids")!=list(IDS)
        or r.get("scope")!="PREVIOUSLY_OPENED_DEV_ONLY"
        or r.get("no_original_gold_in_inference") is not True
        or r.get("source_blind_sha256")!=digest(blind)
        or len(r["results"])!=len(IDS)):
        raise ValueError("wrong original receipt, possible leakage or tampering")
    if digest(original)!=ORIGINAL_SHA:
        raise ValueError("original author external dataset SHA mismatch")
    corpus=codearc_corpus(original)
    scored=[]
    for task in r["results"]:
        pid=task["id"]
        gold=[_codearc_output(corpus[pid][i]) for i in (7,8,9)]
        arms={}
        for arm in ("A","B","C"):
            evidence=task["arms"][arm]
            predict=evidence["original_target_predictions"]
            arms[arm]=bool(
                evidence["source_verified"] and
                len(predict)==len(gold) and predict==gold)
        scored.append({"id":pid,**arms,
                       "C_only_vs_A_B":arms["C"] and not (arms["A"] or arms["B"]),
                       "B_only_vs_C":arms["B"] and not arms["C"],
                       "identifiable_development_contrast":
                       task["original_source_output_diversity"]>1})
    summary={
        "originals":len(scored),
        "A":sum(x["A"] for x in scored),
        "B":sum(x["B"] for x in scored),
        "C":sum(x["C"] for x in scored),
        "C_only_vs_A_B":sum(x["C_only_vs_A_B"] for x in scored),
        "B_only_vs_C":sum(x["B_only_vs_C"] for x in scored),
        "C_exclusive_on_nonconstant_SOURCE":sum(
            x["C_only_vs_A_B"] and x["identifiable_development_contrast"]
            for x in scored),
        "q3_global":"OPEN",
        "original_scope":"PREVIOUSLY_OPENED_DEVELOPMENT",
        "prediction_sha256":expected_sha,
    }
    Path(out).write_text(json.dumps(
        {"summary":summary,"results":scored},indent=2,sort_keys=True)+"\n")
    print("Q3_SOURCE_GROUNDED_ORIGINAL_SCORE",
          json.dumps(summary,sort_keys=True),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    commands=p.add_subparsers(dest="command",required=True)
    for name in ("infer","score"):
        g=commands.add_parser(name)
        g.add_argument("--blind",required=True)
        g.add_argument("--out",required=True)
        if name=="infer":
            g.add_argument("--teachers",required=True)
            g.add_argument("--revision",required=True)
        else:
            g.add_argument("--original",required=True)
            g.add_argument("--predictions",required=True)
            g.add_argument("--expected-sha",required=True)
    args=p.parse_args()
    if args.command=="infer":
        infer(args.blind,args.teachers,args.revision,args.out)
    else:
        score(args.original,args.blind,args.predictions,
              args.expected_sha,args.out)
