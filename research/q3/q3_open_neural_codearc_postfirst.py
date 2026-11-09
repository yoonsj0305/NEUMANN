"""Model-generated Q3 first code study on independently published CodeARC I/O.

CodeARC examples were seen by other NEUMANN research branches, so this is
POSTFIRST DEVELOPMENT EVIDENCE, not a pristine independent-author FIRST.
The pretrained open code model is frozen at a concrete Hub revision, the
candidate code is generated only from seven SOURCE I/O, and outputs 7-9 are
never accessible to proposer. Separate SHA-gated scoring then opens originals.

The primary scientific question is: can a learned generator propose a FULL
new executable algorithm, and does SOURCE counterexample revision help,
rather than adding another human-authored finite DSL?
"""
from __future__ import annotations
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import re

from neumann1.open_program_inventor import (
    GenerativeProgramInventor,IsolatedPython)
from neumann1.q3_trainable_code_policy import (
    LocalCausalCodePolicy,DEFAULT_MODEL)

SALT="NEUMANN_Q3_OPEN_NEURAL_POSTFIRST_20261109_V1"
MODEL=DEFAULT_MODEL
DATA_REV="119512573bf96148cbb95e99cf7cdd21c06153e4"
LABEL=re.compile(r"^Result\s+\d+\s*:\s?")
N=4


def _sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def original_input(row):
    if row.get("errored") not in (False,0,"false","False"):
        raise ValueError("original function errored")
    body=row["input"]
    tree=ast.parse(body,mode="exec")
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.Expr):
        raise ValueError("unexpected CodeARC invocation")
    expr=tree.body[0].value
    if not isinstance(expr,ast.Call) or not isinstance(expr.func,ast.Name):
        raise ValueError("unexpected original call")
    if expr.func.id!="print" or len(expr.args)!=1:
        raise ValueError("not original displayed return value")
    wrapped=expr.args[0]
    if not isinstance(wrapped,ast.BinOp) or not isinstance(wrapped.op,ast.Add):
        raise ValueError("not original result wrapper")
    hidden=wrapped.right
    if isinstance(hidden,ast.Call) and isinstance(hidden.func,ast.Name):
        if hidden.func.id=="str":
            hidden=hidden.args[0]
    if not isinstance(hidden,ast.Call) or hidden.keywords:
        raise ValueError("not a literal function call")
    if not 1<=len(hidden.args)<=2:
        raise ValueError("unknown source function arity")
    values=[ast.literal_eval(v) for v in hidden.args]
    if any(type(v) not in (int,bool,str,float,list,tuple) for v in values):
        raise ValueError("unsupported original input")
    # Single model contract for one- and two-argument external functions.
    return values[0] if len(values)==1 else list(values)


def original_output(row):
    text=row["output"]
    if not isinstance(text,str) or len(text)>10000:
        raise ValueError("unknown original response")
    label=LABEL.match(text)
    if not label:raise ValueError("unexpected original label")
    result=text[label.end():]
    try:return ast.literal_eval(result)
    except (SyntaxError,ValueError):
        return result


def all_originals(path):
    corpus={}
    for line in Path(path).open(encoding="utf-8"):
        if not line.strip():continue
        r=json.loads(line)
        if r.get("type")!="annotated":continue
        try:pid=int(r["problem_id"]);idx=int(r["index"])
        except (ValueError,KeyError,TypeError):continue
        if 0<=idx<=9:
            corpus.setdefault(pid,{})[idx]=r
    return corpus


def prepare(original,blind,n):
    corpus=all_originals(original)
    eligible=[]
    for pid,rows in corpus.items():
        if pid<=20 or len(rows)!=10:continue
        # Do not overlap the #709 first scored public original cohort.
        old=sha256(("NEUMANN-Q3-FIRST/"+str(pid)).encode()).hexdigest()
        if int(old[:8],16)%17==0:continue
        try:
            source=[(original_input(rows[i]),original_output(rows[i]))
                    for i in range(7)]
            input_only=[original_input(rows[i]) for i in (7,8,9)]
            if len(json.dumps(source))>40000:continue
        except (KeyError,ValueError,TypeError,SyntaxError,IndexError):
            continue
        eligible.append((pid,source,input_only))
    eligible.sort(key=lambda row:sha256(
        (SALT+"/"+str(row[0])).encode()).hexdigest())
    if len(eligible)<n:raise ValueError("too few parseable original tasks")
    selected=eligible[:n]
    # The original heldout OUTPUT strings are never copied or parsed here.
    clean={"schema":"NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1",
           "original_sha256":_sha(original),
           "dataset_revision":DATA_REV,
           "salt":SALT,"selected":len(selected),
           "records":[{"id":pid,"source":source,"target_inputs":inputs}
                      for pid,source,inputs in selected]}
    blind.write_text(json.dumps(clean,separators=(",",":"))+"\n")
    print("Q3_MODEL_BLIND_PREPARED",len(selected),_sha(blind))


def propose(blind,out,*,model_revision,proposals=2):
    data=json.loads(blind.read_text())
    if data["schema"]!="NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1":
        raise ValueError("not original blind source")
    model=LocalCausalCodePolicy(
        model_name=MODEL,model_revision=model_revision,
        max_new_tokens=256,temperature=0.3)
    sandbox=IsolatedPython(max_seconds=6)
    rows=[]
    for rec in data["records"]:
        source=rec["source"]
        discovery=GenerativeProgramInventor(
            model,sandbox,max_proposals=proposals).discover(
                source[:6],independent_source_checks=(source[6],))
        predicted=[]
        if discovery.verified:
            outcome=sandbox.evaluate(discovery.program,rec["target_inputs"])
            if outcome.status=="EXECUTED":
                predicted=list(outcome.outputs)
        first=discovery.attempts[0] if discovery.attempts else None
        first_source_verified=False
        first_pred=[]
        if (first is not None and first.program is not None and
                first.source_correct==first.source_total):
            check=sandbox.evaluate(first.program,[source[6][0]])
            if check.status=="EXECUTED" and check.outputs[0]==source[6][1]:
                first_source_verified=True
                result=sandbox.evaluate(first.program,rec["target_inputs"])
                if result.status=="EXECUTED":
                    first_pred=list(result.outputs)
        row={
            "id":rec["id"],
            "status":discovery.status,
            "model_only_first_checked":first_source_verified,
            "first_predictions":first_pred,
            "refined_predictions":predicted,
            "program_sha256":discovery.frozen_sha256,
            "verified_program":discovery.program if discovery.verified else None,
            "attempts":[{
                "sha256":a.sha256,"source_correct":a.source_correct,
                "source_total":a.source_total,
                "status":a.status,"iteration":a.iteration}
                for a in discovery.attempts],
            "max_proposals":proposals}
        rows.append(row)
        print("Q3_MODEL_SOURCE",rec["id"],discovery.status,
              "attempts",len(discovery.attempts),flush=True)
    payload={
        "schema":"NEUMANN.Q3.NEURAL.CODEARC.POSTFIRST.v1",
        "model_id":MODEL,"model_revision":model_revision,
        "dataset_revision":DATA_REV,"dataset_sha256":data["original_sha256"],
        "blind_sha256":_sha(blind),"source_only":True,
        "no_external_target_gold_in_proposals":True,
        "unrestricted_Q3_Q6_claim":False,"records":rows}
    out.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print("Q3_MODEL_PREDICTIONS_FROZEN_SHA256",_sha(out))


def score(original,predictions,expected_sha,out):
    if _sha(predictions)!=expected_sha:
        raise ValueError("predictions changed after source-only SHA freeze")
    plan=json.loads(predictions.read_text())
    if (plan["dataset_sha256"]!=_sha(original)
            or not plan["no_external_target_gold_in_proposals"]):
        raise ValueError("external source mismatch")
    corpus=all_originals(original)
    entries=[]
    for row in plan["records"]:
        source=corpus[row["id"]]
        gold=[original_output(source[i]) for i in (7,8,9)]
        first=bool(row["first_predictions"] and row["first_predictions"]==gold)
        repaired=bool(row["refined_predictions"] and
                      row["refined_predictions"]==gold)
        entries.append({
            "id":row["id"],"source_status":row["status"],
            "first_original_exact":first,"revised_original_exact":repaired,
            "revised_new_residual":repaired and not first,
            "source_model_train_fitted":bool(row["refined_predictions"])})
    summary={
        "originals_scored":len(entries),
        "one_shot_first_exact":sum(e["first_original_exact"] for e in entries),
        "source_repaired_exact":sum(
            e["revised_original_exact"] for e in entries),
        "causal_new_exact":sum(e["revised_new_residual"] for e in entries),
        "source_verified_predictions":sum(
            e["source_model_train_fitted"] for e in entries),
        "sha256_frozen":expected_sha,
        "scope":"POSTFIRST independent-author original I/O, NOT unopened frontier",
        "global_q3_q6":"OPEN",
        "weights_finetuned_during_study":False}
    out.write_text(json.dumps(
        {"summary":summary,"records":entries},indent=2)+"\n")
    print("Q3_MODEL_EXTERNAL_SCORE",json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    commands=p.add_subparsers(dest="cmd",required=True)
    a=commands.add_parser("prepare")
    a.add_argument("--original",type=Path,required=True)
    a.add_argument("--blind",type=Path,required=True)
    a.add_argument("--n",type=int,default=N)
    a=commands.add_parser("propose")
    a.add_argument("--blind",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--model-revision",required=True)
    a.add_argument("--proposals",type=int,default=2)
    a=commands.add_parser("score")
    a.add_argument("--original",type=Path,required=True)
    a.add_argument("--predictions",type=Path,required=True)
    a.add_argument("--expected-sha",required=True)
    a.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.cmd=="prepare":prepare(args.original,args.blind,args.n)
    elif args.cmd=="propose":propose(
        args.blind,args.output,model_revision=args.model_revision,
        proposals=args.proposals)
    else:score(args.original,args.predictions,args.expected_sha,args.output)
