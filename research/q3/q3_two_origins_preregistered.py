"""Q3: pre-registered TWO independent-author origins, ONE learned discovery core.

Source-only proposal process and post-freeze grader share NO target output
parameter. ARCANA and CodeARC adapters are DATA ONLY; all Q3 arms invoke
exactly the same `SingleDiscoveryCore`, sandbox, program ISA and verifier.
Scientific FIRST: ARCANA novel task IDs, CodeARC POSTFIRST family despite
the newly chosen 4 original IDs. Native baselines declared separately.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

CODEARC_SHA = "119512573bf96148cbb95e99cf7cdd21c06153e4"
ARCANA_SHA = "3f3dc8f650deb271a29e282bfb0e5ca95a7d64d6"
SALT = "NEUMANN-Q3-TWO-ORIGINS-FROZEN-20261109-V1"
SIZES = {"codearc": 4, "arcana": 4}
CODEARC_OFFSET = 88
ARCANA_SOURCE_DEVELOPMENT = "archimedes1.json"
MODEL_ID = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
SCHEMA = "NEUMANN.Q3.TWO-ORIGIN.BLIND.v1"


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",",":"),
                      allow_nan=False,ensure_ascii=True)


def sha(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _codearc_input(row):
    expr=ast.parse(row["input"],mode="exec").body
    if len(expr)!=1 or not isinstance(expr[0],ast.Expr):
        raise ValueError("not an original codearc invocation")
    call=expr[0].value
    if not (isinstance(call,ast.Call) and
            isinstance(call.func,ast.Name) and call.func.id=="print" and
            len(call.args)==1):
        raise ValueError("unexpected print wrapper")
    outer=call.args[0]
    if not isinstance(outer,ast.BinOp) or not isinstance(outer.op,ast.Add):
        raise ValueError("unexpected result wrapper")
    inner=outer.right
    if isinstance(inner,ast.Call) and isinstance(inner.func,ast.Name) and inner.func.id=="str":
        if len(inner.args)!=1:raise ValueError("unexpected string wrapper")
        inner=inner.args[0]
    if not isinstance(inner,ast.Call) or inner.keywords or not 1<=len(inner.args)<=2:
        raise ValueError("unknown function invocation")
    val=[ast.literal_eval(q) for q in inner.args]
    if any(type(v) not in (int,bool,str,float,list,tuple) for v in val):
        raise ValueError("unsupported python source type")
    return val[0] if len(val)==1 else val


def _codearc_output(row):
    text=row["output"]
    label=re.match(r"^Result\s+\d+\s*:\s?",text)
    if not label:raise ValueError("unknown original result")
    body=text[label.end():]
    try:return ast.literal_eval(body)
    except (SyntaxError,ValueError):return body


def codearc_corpus(original):
    corpus={}
    for line in Path(original).open(encoding="utf-8"):
        if not line:continue
        row=json.loads(line)
        if row.get("type")!="annotated":continue
        try:pid=int(row["problem_id"]);idx=int(row["index"])
        except (ValueError,KeyError,TypeError):continue
        if 0<=idx<=9:
            corpus.setdefault(pid,{})[idx]=row
    return corpus


def codearc_registry(corpus):
    eligible=[]
    for pid,rows in corpus.items():
        if pid<=20 or len(rows)!=10:continue
        if int(hashlib.sha256(("NEUMANN-Q3-FIRST/"+str(pid)).encode()).hexdigest()[:8],16)%17==0:
            continue
        try:
            source=[[_codearc_input(rows[i]),_codearc_output(rows[i])]
                    for i in range(7)]
            target=[_codearc_input(rows[i]) for i in (7,8,9)]
            if len(canonical(source))>40000:continue
        except (SyntaxError,ValueError,TypeError,KeyError,IndexError):
            continue
        eligible.append((pid,source,target))
    # Old #744 registers 0..87 under this same hash; 88..91 is new index
    # but CodeARC remains previously studied, never global FIRST.
    eligible.sort(key=lambda x:hashlib.sha256(
        ("NEUMANN_Q3_OPEN_NEURAL_POSTFIRST_20261109_V1/"+str(x[0])).encode()
        ).hexdigest())
    selected=eligible[CODEARC_OFFSET:CODEARC_OFFSET+SIZES["codearc"]]
    if len(selected)!=SIZES["codearc"]:
        raise ValueError("CodeARC original registry cannot be frozen")
    return [{"id":str(pid),"source":src,"target_inputs":dst}
            for pid,src,dst in selected]


def arcana_registry(folder):
    candidates=[x for x in Path(folder).glob("*.json")
                if x.name != ARCANA_SOURCE_DEVELOPMENT]
    candidates.sort(key=lambda p:hashlib.sha256(
        (SALT+"/arcana/"+p.name).encode()).hexdigest())
    selected=candidates[:SIZES["arcana"]]
    if len(selected)!=SIZES["arcana"]:
        raise ValueError("ARCANA original registry cannot be frozen")
    return selected


def prepare(origin, original, out):
    if origin not in SIZES:raise ValueError("origin must be one of TWO")
    if origin=="codearc":
        tasks=codearc_registry(codearc_corpus(original))
        provenance=file_sha(original)
    else:
        files=arcana_registry(original)
        provenance=sha([[p.name,file_sha(p)] for p in files])
        tasks=[]
        for path in files:
            task=json.loads(path.read_text())
            if len(task.get("train",[]))<3 or len(task.get("test",[]))<1:
                raise ValueError("not enough ORIGINAL SOURCE or TARGET examples")
            source=[[r["input"],r["output"]] for r in task["train"][:3]]
            target=[r["input"] for r in task["test"]]
            tasks.append({"id":path.name,"source":source,"target_inputs":target,
                          "source_sha256":file_sha(path)})
    if len({r["id"] for r in tasks})!=len(tasks):
        raise ValueError("duplicate originals")
    data={"schema":SCHEMA,"origin":origin,
          "source_revision":CODEARC_SHA if origin=="codearc" else ARCANA_SHA,
          "source_fingerprint":provenance,"task_count":len(tasks),
          "developer_excluded":ARCANA_SOURCE_DEVELOPMENT if origin=="arcana" else None,
          "model":MODEL_ID,"arms":["A","B","C"],"max_proposals":1,
          "records":tasks,
          "no_target_gold_extracted_or_transmitted":True,
          "pre_registered_gate":"C-only > B and applicable strongest classic on BOTH origins, 1+ each; no regression"}
    Path(out).write_text(canonical(data)+"\n")
    print("Q3_TWO_ORIGIN_INPUTS_FROZEN",origin,len(tasks),file_sha(out),flush=True)


def _native_original_grid(source,inputs):
    """Existing mainline strong 2D specialist, SOURCE ONLY. No new grid inventor."""
    from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor
    from neumann1.relational_grid_inventor import grid
    training=[(grid(x),grid(y)) for x,y in source]
    inf=[grid(x) for x in inputs]
    result=HybridArcGridInventor(max_attempts=2).solve(training,inf)
    # Each member denotes ONE algorithm predicting every target test input.
    return [json.loads(canonical(list(row.outputs))) for row in result.candidates]


def propose(blind, teachers, adapter, model_revision, output):
    from neumann1.q3_single_discovery_core import SingleDiscoveryCore,SourceMethodMemory
    from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
    from neumann1.open_program_inventor import IsolatedPython
    data=json.loads(Path(blind).read_text())
    if data.get("schema")!=SCHEMA or len(data["records"])!=SIZES[data["origin"]]:
        raise ValueError("not preregistered ORIGINAL inputs")
    prior=[json.loads(line) for line in Path(teachers).read_text().splitlines() if line]
    runner=IsolatedPython(max_seconds=8)
    memory=SourceMethodMemory(runner)
    memory.import_source_teachers(prior)
    memory.freeze()
    if not memory.episodes:raise ValueError("no prior certified methods")
    source_ids={e.source_id for e in memory.episodes}
    if data["origin"]=="codearc" and any(
        "source-teacher/"+r["id"] in source_ids for r in data["records"]):
        raise ValueError("original SOURCE training overlap")
    base=LocalCausalCodePolicy(model_name=MODEL_ID,
        model_revision=model_revision,max_new_tokens=384,temperature=0.3)
    adapted=LocalCausalCodePolicy(model_name=MODEL_ID,
        model_revision=model_revision,adapter_path=adapter,
        max_new_tokens=384,temperature=0.3)
    rows=[]
    for entry in data["records"]:
        row={"id":entry["id"],"arms":{},"native":[],
             "native_status":"NOT_APPLICABLE_NON_GRID"}
        src=entry["source"]
        train=src[:-1]
        check=src[-1:]
        if data["origin"]=="arcana":
            try:
                row["native"]=_native_original_grid(src[:2],entry["target_inputs"])
                row["native_status"]="SOURCE_ONLY_NATIVE"
            except Exception as exc:
                row["native_status"]="ABSTAIN_"+type(exc).__name__
        for name,policy,reuse in [
            ("A",base,False),("B",base,True),("C",adapted,True)]:
            one={"status":"ABSTAIN","program_sha256":None,
                 "program":None,"target_predictions":[],"source_pass":False}
            try:
                result=SingleDiscoveryCore(
                    policy,runner,memory=memory,max_proposals=1).discover(
                        train,check,reuse_memory=reuse)
                discovery=result.discovery
                one["status"]=discovery.status
                one["source_pass"]=bool(discovery.verified)
                one["program_sha256"]=discovery.frozen_sha256
                if discovery.verified:
                    one["program"]=discovery.program
                    scored=runner.evaluate(discovery.program,entry["target_inputs"])
                    if scored.status=="EXECUTED":
                        one["target_predictions"]=json.loads(canonical(scored.outputs))
                    else:
                        one["status"]="ABSTAIN_TARGET_EXECUTION"
            except Exception as exc:
                # Model prompt too large, validator reject, sandbox unavailable:
                # NEVER selectively drop hard originals or claim repaired.
                one["status"]="ABSTAIN_"+type(exc).__name__
            row["arms"][name]=one
        rows.append(row)
        # In a bounded original-author run, preserve unscored SOURCE-only
        # partials if external runner times out; these are NEVER target gold.
        Path(str(output)+".SOURCE_PARTIAL.json").write_text(
            canonical({"origin":data["origin"],"source_only":True,
                       "scored":False,"records":rows})+"\\n")
        print("Q3_TWO_ORIGIN_SOURCE_ONLY",data["origin"],entry["id"],
              [(k,v["status"]) for k,v in row["arms"].items()],flush=True)
    p={"schema":"NEUMANN.Q3.TWO-ORIGIN.PREDICTIONS.v1",
       "origin":data["origin"],"blind_sha256":file_sha(blind),
       "memory_sha256":file_sha(teachers),
       "model_revision":model_revision,
       "adapter_hash":sha(json.loads(
           (Path(adapter)/"neumann_source_training_manifest.json").read_text())),
       "no_original_gold_in_policy":True,"records":rows}
    Path(output).write_text(canonical(p)+"\n")
    print("Q3_TWO_ORIGIN_PREDICTIONS_FROZEN",data["origin"],
          file_sha(output),flush=True)


def score(origin, original, blind, predictions, expected_sha, output):
    if file_sha(predictions)!=expected_sha:
        raise ValueError("prediction freeze broken")
    plan=json.loads(Path(predictions).read_text())
    inp=json.loads(Path(blind).read_text())
    if (plan.get("blind_sha256")!=file_sha(blind)
            or plan.get("origin")!=origin
            or inp["source_revision"]!=(CODEARC_SHA if origin=="codearc" else ARCANA_SHA)):
        raise ValueError("not a frozen original scorer")
    corpus=codearc_corpus(original) if origin=="codearc" else None
    results=[]
    for entry,row in zip(inp["records"],plan["records"]):
        if entry["id"]!=row["id"]:raise ValueError("reordered original")
        if origin=="codearc":
            gold=[_codearc_output(corpus[int(entry["id"])][i]) for i in (7,8,9)]
        else:
            gold=[x["output"] for x in json.loads(
                (Path(original)/entry["id"]).read_text())["test"]]
        exact=lambda preds: bool(preds and canonical(preds)==canonical(gold))
        scores={arm:exact(row["arms"][arm]["target_predictions"])
                for arm in ("A","B","C")}
        native=any(exact(c) for c in row["native"])
        if origin=="codearc":native=None
        new=bool(scores["C"] and not scores["B"] and not scores["A"] and
                 (native is False or native is None))
        results.append({"id":entry["id"],"A":scores["A"],"B":scores["B"],
                        "C":scores["C"],"native":native,
                        "c_only_exact":new,
                        "B_only_vs_C":scores["B"] and not scores["C"],
                        "source_pass":{arm:row["arms"][arm]["source_pass"]
                                       for arm in ("A","B","C")},
                        "C_program_sha256":row["arms"]["C"]["program_sha256"]})
    summary={"origin":origin,"n":len(results),
             **{arm:sum(x[arm] for x in results) for arm in ("A","B","C")},
             "native":None if origin=="codearc" else
                        sum(bool(x["native"]) for x in results),
             "C_only":sum(x["c_only_exact"] for x in results),
             "B_only":sum(x["B_only_vs_C"] for x in results),
             "true_original_predictions_sha256":expected_sha,
             "native_specialist_checked":origin=="arcana",
             "global_Q3":"OPEN"}
    Path(output).write_text(canonical({"summary":summary,"results":results})+"\n")
    print("Q3_TWO_ORIGIN_ORIGINAL_SCORE",canonical(summary),flush=True)


def gate(codearc_score,arcana_score):
    a=json.loads(Path(codearc_score).read_text())["summary"]
    b=json.loads(Path(arcana_score).read_text())["summary"]
    if a["origin"]!="codearc" or b["origin"]!="arcana":
        raise ValueError("wrong independent authors")
    if a["n"]!=SIZES["codearc"] or b["n"]!=SIZES["arcana"]:
        raise ValueError("wrong preregistered denominators")
    residual=bool(a["C_only"]>=1 and b["C_only"]>=1 and
                  a["B_only"]==0 and b["B_only"]==0)
    # Even both-domain C-only is not sufficient for global Q3 unless
    # strongest applicable native baseline and novel-method audit exist.
    status=("CROSS_ORIGIN_RESIDUAL_CANDIDATE_REQUIRES_NATIVE_AND_NOVELTY_AUDIT"
            if residual else "Q3_CROSS_ORIGIN_CAUSAL_GATE_FAIL")
    print("Q3_TWO_ORIGIN_FINAL",canonical({"status":status,
        "codearc":a,"arcana":b,
        "global_q3":"OPEN","model_training_not_automatically_invention":True}))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    commands=p.add_subparsers(dest="command",required=True)
    x=commands.add_parser("prepare")
    x.add_argument("--origin",choices=list(SIZES),required=True)
    x.add_argument("--original",required=True)
    x.add_argument("--out",required=True)
    x=commands.add_parser("propose")
    x.add_argument("--blind",required=True)
    x.add_argument("--teachers",required=True)
    x.add_argument("--adapter",required=True)
    x.add_argument("--model-revision",required=True)
    x.add_argument("--out",required=True)
    x=commands.add_parser("score")
    x.add_argument("--origin",choices=list(SIZES),required=True)
    x.add_argument("--original",required=True)
    x.add_argument("--blind",required=True)
    x.add_argument("--predictions",required=True)
    x.add_argument("--expected-sha",required=True)
    x.add_argument("--out",required=True)
    x=commands.add_parser("gate")
    x.add_argument("--codearc-score",required=True)
    x.add_argument("--arcana-score",required=True)
    args=p.parse_args()
    if args.command=="prepare":prepare(args.origin,args.original,args.out)
    elif args.command=="propose":propose(args.blind,args.teachers,args.adapter,
                                        args.model_revision,args.out)
    elif args.command=="score":
        score(args.origin,args.original,args.blind,args.predictions,args.expected_sha,args.out)
    else:gate(args.codearc_score,args.arcana_score)
