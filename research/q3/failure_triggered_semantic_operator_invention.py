"""Q3: failed conservative algebra triggers a NEW typed semantic operator.

Old InventedJoin is conservative: every output is one source operand.
For original TRAIN evidence that violates this theorem, an inductive program
generates a NEW executable operator with arbitrary output symbols.

The new operator's input representation is inferred by counterexamples:
color set -> color multiset -> ordered colors. Each refinement occurs ONLY if
identical observations require different outputs. A data-derived function
definition with typed arguments and an explicit fallback is then generated.

This is finite semantic function induction with classical code, not a
pretrained NN discovering all possible computation. It is scoped to previously
opened ARC originals, and global Q3 stays OPEN without evidence of general
new operator-family discovery and out-of-family transfer.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from research.q3.induce_binary_algebra_original import (
    PIN,EVAL32,grid_ok,enumerate_decompositions,subgrids,admit_program,
)

SCHEMA="neumann.q3.failed-join-new-semantics-original.v1"


def sha(data):
    return hashlib.sha256(json.dumps(
        data,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def encode(values,mode):
    if mode=="set":return tuple(sorted(set(values)))
    if mode=="multiset":return tuple(sorted(values))
    if mode=="ordered":return tuple(values)
    raise ValueError("BAD_LEARNED_TYPE")


def observations(train,decomp):
    data=[]
    for example,pair in enumerate(train):
        panels=subgrids(pair["input"],decomp)
        if panels is None:return None
        expected=pair["output"]
        h,w=len(expected),len(expected[0])
        if any(len(p)!=h or len(p[0])!=w for p in panels):
            return None
        for y in range(h):
            for x in range(w):
                args=tuple(part[y][x] for part in panels)
                data.append((args,expected[y][x],example,y,x))
    return data


def infer_new_observation_type(data):
    trace=[]
    for mode in ("set","multiset","ordered"):
        table={}
        conflicts=0
        first=None
        for args,result,example,y,x in data:
            key=encode(args,mode)
            if key in table and table[key]!=result:
                conflicts+=1
                if first is None:
                    first={"input_signature":key,
                           "output_old":table[key],"output_new":result,
                           "example":example,"y":y,"x":x}
            else:table[key]=result
        trace.append({"representation":mode,"conflicts":conflicts,
                      "first_conflict":first})
        if not conflicts:
            return mode,table,trace
    return None,None,trace


@dataclass(frozen=True)
class NovelOperator:
    mode:str
    arity:int
    rows:tuple

    def definition(self):
        expr=["Case",["EncodeArguments",self.mode,"args"],
              [[list(key),out] for key,out in self.rows],
              ["Abstain","UNKNOWN_SIGNATURE"]]
        core=["Lambda",["Color"]*self.arity,"Color",expr]
        name="neumann_invented_"+sha(core)[:16]
        return ["DefineNewOperator",name,core]

    def compile(self):
        if self.mode not in ("set","multiset","ordered"):
            raise ValueError("BAD_OPERATOR_MODE")
        if not 2<=self.arity<=9:raise ValueError("BAD_ARITY")
        data=dict(self.rows)
        if len(data)!=len(self.rows):raise ValueError("DUPLICATE_CASE")
        def invented(values):
            if len(values)!=self.arity:return None
            return data.get(encode(values,self.mode))
        return invented


def learn_new_semantic_operator(train,decomp):
    data=observations(train,decomp)
    if data is None or len(train)<2:return None
    counterexamples=[(args,result,example,y,x) for
            args,result,example,y,x in data if result not in args]
    unique={args for args,result,*_ in counterexamples}
    if len(counterexamples)<2 or len(unique)<2:
        return None
    mode,table,trace=infer_new_observation_type(data)
    if mode is None:return None
    op=NovelOperator(mode,decomp.count,tuple(sorted(table.items())))
    fn=op.compile()
    if not all(fn(args)==target for args,target,*_ in data):
        raise RuntimeError("BAD_OBSERVATION_FIT")
    return op,trace,counterexamples


def composed_definition(decomp,op):
    return ["Compose",
           ["Split",decomp.axis,decomp.panel,decomp.gutter,decomp.count],
           ["MapByCell",op.definition()]]


def execute(decomp,op,grid):
    panels=subgrids(grid,decomp)
    if panels is None:return None
    fn=op.compile()
    h=len(panels[0]);w=len(panels[0][0])
    output=[]
    for y in range(h):
        row=[]
        for x in range(w):
            color=fn(tuple(p[y][x] for p in panels))
            if color is None:return None
            row.append(color)
        output.append(row)
    return output


def propose(train):
    if not all(grid_ok(t["input"]) and grid_ok(t["output"]) for t in train):
        return []
    programs=[]
    for d in enumerate_decompositions(train):
        learned=learn_new_semantic_operator(train,d)
        if learned is None:continue
        op,trace,witness=learned
        if not all(execute(d,op,p["input"])==p["output"] for p in train):
            raise RuntimeError("INVALID_LEARNED_TRAIN")
        programs.append((d,op,trace,witness))
    return programs


def study(task,taskid,cohort):
    if len(task["train"])<2:
        return {"id":taskid,"cohort":cohort,
                "status":"INSUFFICIENT_TRAIN","submitted":False,"exact":False}
    # No repeated classical timing experiment; a direct EXISTENCE check is
    # used solely to avoid calling old solved cases novel.
    if admit_program(task["train"]) is not None:
        return {"id":taskid,"cohort":cohort,
                "status":"OLD_JOIN_ALREADY_FITS","submitted":False,"exact":False}
    candidates=propose(task["train"])
    if not candidates:
        return {"id":taskid,"cohort":cohort,
                "status":"NO_NEW_SEMANTICS","submitted":False,"exact":False}
    frozen=[composed_definition(d,op) for d,op,_,_ in candidates]
    # This definition is generated from original TRAIN only, before TEST gold.
    predictions=[]
    for case in task["test"]:
        outputs=[execute(d,op,case["input"]) for d,op,_,_ in candidates]
        if outputs and outputs[0] is not None and all(p==outputs[0] for p in outputs):
            predictions.append(outputs[0])
        else:predictions.append(None)
    submitted=all(p is not None for p in predictions)
    exact=submitted and all(p==t["output"] for p,t in zip(predictions,task["test"]))
    return {"id":taskid,"cohort":cohort,
            "status":"INVENTED_NONCONSERVATIVE_OPERATOR",
            "submitted":submitted,"exact":exact,
            "wrong_submission":submitted and not exact,
            "operator_names":[op.definition()[1] for d,op,_,_ in candidates],
            "new_operator_types":[op.mode for d,op,_,_ in candidates],
            "novel_output_cases":[len(w) for d,op,t,w in candidates],
            "distinct_novel_signatures":[len(set(q[0] for q in w)) for d,op,t,w in candidates],
            "induction_trace":[t for d,op,t,w in candidates],
            "frozen_operator_AST_sha256":sha(frozen),
            "frozen_operator_AST":frozen,
            "test_prediction_sha256":[sha(p) if p is not None else None
                                      for p in predictions],
            "expressivity_theorem":"OLD_JOIN_CONSERVATIVE__NONINPUT_OUTPUT_PROVES_IMPOSSIBLE",
            "original_TEST_gold_used_to_propose":False}


def run(arc_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_FIRST")
    out.mkdir(parents=True)
    rows=[]
    for cohort,folder,ids in (
        ("public_TRAIN_400","training",None),
        ("previously_opened_EVAL_32","evaluation",EVAL32)
    ):
        datadir=arc_root/"data"/folder
        paths=(sorted(datadir.glob("*.json")) if ids is None
               else [datadir/(i+".json") for i in ids])
        if len(paths)!=(400 if ids is None else 32):
            raise ValueError("COHORT_COUNT_CHANGED")
        for path in paths:
            record=study(json.loads(path.read_text()),path.stem,cohort)
            rows.append(record)
            if record["status"]=="INVENTED_NONCONSERVATIVE_OPERATOR":
                print("INVENTED",cohort,path.stem,
                      "types",record["new_operator_types"],
                      "test",record["exact"],"submitted",record["submitted"],
                      flush=True)
    stats={}
    for name in ("public_TRAIN_400","previously_opened_EVAL_32"):
        subset=[r for r in rows if r["cohort"]==name]
        stats[name]={"tasks":len(subset),
           "invented_definitions":sum(r["status"]=="INVENTED_NONCONSERVATIVE_OPERATOR" for r in subset),
           "submitted":sum(r["submitted"] for r in subset),
           "exact":sum(r["exact"] for r in subset),
           "wrong":sum(r.get("wrong_submission",False) for r in subset)}
    report={
       "schema":SCHEMA,"pin":PIN,
       "only_previously_opened_originals":True,
       "new_semantics_generated_from_external_train":True,
       "human_implemented_general_case_machine":True,
       "old_conservative_operator_impossibility_witness_required":True,
       "untouched_eval_ids_consumed":0,
       "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
       "summary":stats,"rows":rows}
    (out/"FIRST.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"}))
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    run(args.arc_root,args.out)
