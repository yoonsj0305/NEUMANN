"""Q3 independently authored original-program invention, paired causal study.

ONE learned discovery policy, one generic executable Python expression
substrate and one original SOURCE verifier. A uniform classical program
search, B same search + directly memorized older SOURCE-certified programs,
C operator grammar fitted to old certified method ASTs. No family-routed
inventor, TARGET oracle, or change to 6500-state/250000-eval search rights.

PREPARE/INFER has access to training SOURCE + original test INPUTS only.
SCORE is a separate process and is the only action that reads author gold.
Frozen SHA receipts are mandatory. CodeARC is PRIOR-EXPOSED development.
ARCANA is a separately authored data set with deterministic SHA-salted
registration before any chosen task's test outputs are used for scoring.

Never report Q3 global PASS from SOURCE fit, constant-output successes,
hand-coded primitives, or a single author. C must independently beat the
classical/memorized baseline in BOTH semantic origins to qualify for a
candidate novelty audit, and the strongest external classic also matters.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import re

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_single_discovery_core import SingleDiscoveryCore,SourceMethodMemory
from neumann1.q3_structural_invention import (
    LearnedDiscoveryPolicy,StructuralInventionPolicy)

SCHEMA="NEUMANN.Q3.UNIFIED-STRUCTURAL-INVENTION.v1"
ARCANA_REVISION="3f3dc8f650deb271a29e282bfb0e5ca95a7d64d6"
CODEARC_REVISION="119512573bf96148cbb95e99cf7cdd21c06153e4"
CODEARC_ORIGINAL_SHA="3f08820594d4825c78bbdcc3b8eb2e6c8c0285fb3de966e900463b53f1723962"
SALT="NEUMANN-Q3-LEARNED-STRUCTURAL-AUTHOR-FREEZE-20261109-V1"
ARCANA_N=4
ARCANA_DEV_EXCLUSION="archimedes1.json"


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def sha_file(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def freeze_codearc(previous_blind,output):
    record=json.loads(Path(previous_blind).read_text())
    if (record.get("schema")!="NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1"
            or record.get("original_sha256")!=CODEARC_ORIGINAL_SHA
            or len(record.get("records",[]))!=8):
        raise ValueError("not the previously frozen original CodeARC cohort")
    rows=[{
        "id":str(e["id"]),
        "source":e["source"],
        "target_inputs":e["target_inputs"],
    } for e in record["records"]]
    if len({row["id"] for row in rows})!=8:
        raise ValueError("duplicate original authors' problem IDs")
    out={"schema":SCHEMA,"origin":"codearc","scope":"POSTFIRST_ALREADY_EXPOSED",
         "revision":CODEARC_REVISION,
         "source_fingerprint":sha_file(previous_blind),
         "records":rows,"no_target_gold_in_blind":True}
    Path(output).write_text(canonical(out)+"\n")
    print("Q3_AUTHOR_SOURCE_BLIND_FROZEN", "codearc",
          [v["id"] for v in rows],sha_file(output),flush=True)


def freeze_arcana(author_data_dir,output):
    root=Path(author_data_dir)
    files=[p for p in root.glob("*.json")
           if p.name!=ARCANA_DEV_EXCLUSION]
    if len(files)<ARCANA_N:
        raise ValueError("too few independent ARCANA author original tasks")
    files.sort(key=lambda p:sha256(
        (SALT+"/"+p.name).encode()).hexdigest())
    files=files[:ARCANA_N]
    entries=[]
    for file in files:
        record=json.loads(file.read_text())
        source=record.get("train",[])
        held=record.get("test",[])
        if len(source)<3 or not held:
            raise ValueError("insufficient original SOURCE or target INPUTS")
        entries.append({
            "id":file.name,
            "source":[[r["input"],r["output"]] for r in source[:3]],
            "target_inputs":[r["input"] for r in held],
            "file_sha256":sha_file(file),
        })
    out={"schema":SCHEMA,"origin":"arcana","scope":"FIRST_AUTHOR_BLIND",
         "revision":ARCANA_REVISION,
         "source_fingerprint":sha256(canonical(
             [(file.name,sha_file(file)) for file in files]).encode()).hexdigest(),
         "records":entries,"no_target_gold_in_blind":True,
         "developer_exclusion":ARCANA_DEV_EXCLUSION}
    Path(output).write_text(canonical(out)+"\n")
    print("Q3_AUTHOR_SOURCE_BLIND_FROZEN","arcana",
          [r["id"] for r in entries],sha_file(output),flush=True)


def freeze_arcana_next8(author_data_dir,output):
    """New SOURCE registry frozen before reading chosen author TARGET labels.

    Excludes every previously opened ARCANA development task, including the
    original 4 in PR #753. No model, selected operator or prompt is tuned
    against new heldout target correctness. Author identity/shape never
    dispatches the discovery algorithm.
    """
    exclude={
        ARCANA_DEV_EXCLUSION,
        "magnetic1.json","mop2.json","cup1.json","pocket_watch1.json",
    }
    root=Path(author_data_dir)
    files=[p for p in root.glob("*.json") if p.name not in exclude]
    salt="NEUMANN-Q3-STRUCTURAL-LIFT-NEXT8-20261110-FROZEN-V1"
    files.sort(key=lambda p:sha256((salt+"/"+p.name).encode()).hexdigest())
    selected=files[:8]
    if len(selected)!=8:
        raise ValueError("independent-author holdout not available")
    entries=[]
    for file in selected:
        record=json.loads(file.read_text())
        train=record.get("train",[])
        held=record.get("test",[])
        if len(train)<3 or not held:
            raise ValueError("author original lacks independent SOURCE verifier")
        entries.append({
            "id":file.name,
            "source":[[r["input"],r["output"]] for r in train[:3]],
            "target_inputs":[r["input"] for r in held],
            "file_sha256":sha_file(file),
        })
    out={
        "schema":SCHEMA,
        "origin":"arcana",
        "scope":"NEWLY_FROZEN_AUTHOR_ORIGINALS_NO_TUNING",
        "revision":ARCANA_REVISION,
        "source_fingerprint":sha256(canonical(
            [(p.name,sha_file(p)) for p in selected]
            ).encode()).hexdigest(),
        "records":entries,
        "no_target_gold_in_blind":True,
        "prior_excluded":sorted(exclude),
        "salt":salt,
        "run_pre_registration":"No representation-policy changes after first freeze",
    }
    Path(output).write_text(canonical(out)+"\n")
    print("Q3_NEXT8_EXTERNAL_SOURCE_BLIND_FROZEN",
          [x["id"] for x in entries],sha_file(output),flush=True)


def _verified_method(memory,train,checks):
    """Strong B: past programs can be reused directly, no learning at test."""
    inputs=[x for x,y in (*train,*checks)]
    expected=[y for x,y in (*train,*checks)]
    for entry in sorted(memory.episodes,key=lambda x:x.identity):
        result=memory.runner.evaluate(entry.program,inputs)
        if (result.status=="EXECUTED"
                and len(result.outputs)==len(inputs)
                and all(source_same_value(a,b)
                        for a,b in zip(result.outputs,expected))):
            return entry.program
    return None


def _classical_arcana(source,targets):
    """Existing strong independent classical comparator, NOT the Q3 policy."""
    try:
        from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor
        model=HybridArcGridInventor(max_attempts=2)
        r=model.solve(source,targets)
        return [list(c.outputs) for c in r.candidates],"SOURCE_NATIVE_STRONG"
    except (ValueError,TypeError,IndexError,AttributeError) as exc:
        return [],"ABSTAIN_NATIVE_"+type(exc).__name__


def infer(blind,teacher_file,output):
    inp=json.loads(Path(blind).read_text())
    if inp.get("schema")!=SCHEMA or not inp.get("no_target_gold_in_blind"):
        raise ValueError("invalid original author blind")
    rows=[json.loads(line) for line in Path(teacher_file).open()
          if line.strip()]
    runner=IsolatedPython(max_seconds=8)
    library=SourceMethodMemory(runner)
    library.import_source_teachers(rows)
    library.freeze()
    if len(library.episodes)<2:
        raise ValueError("not enough prior SOURCE-certified methods")
    fitted=LearnedDiscoveryPolicy.fit(library.episodes)
    if not fitted.weights or not fitted.provenance:
        raise ValueError("no learned discovery operator policy")
    known={e.program for e in library.episodes}

    all_results=[]
    for e in inp["records"]:
        source=e["source"]
        train=tuple((x,y) for x,y in source[:-1])
        checks=tuple((x,y) for x,y in source[-1:])
        if not train or not checks:
            raise ValueError("missing disjoint SOURCE verification")
        src_outputs={canonical(y) for x,y in source}
        row={"id":e["id"],
             "source_output_diverse":len(src_outputs)>1,
             "arms":{},
             "native":[],"native_status":"NOT_APPLICABLE"}
        if inp["origin"]=="arcana":
            native,status=_classical_arcana(source,e["target_inputs"])
            row["native"],row["native_status"]=native,status

        for arm in ("A","B","C"):
            cached=None
            if arm=="B":
                cached=_verified_method(library,train,checks)
            fitted_prior=fitted if arm=="C" else None
            policy=StructuralInventionPolicy(
                fitted_prior,max_states=6500,
                max_evaluations=250000,max_candidates=12,
                prior_method_count=len(library.episodes))
            outcome=SingleDiscoveryCore(
                policy,runner,memory=library,max_proposals=12).discover(
                train,checks,reuse_memory=False)
            discovery=outcome.discovery
            solved_code=cached if cached is not None else (
                discovery.program if discovery.verified else None)
            original_preds=[]
            status=("SOURCE_VERIFIED_MEMORY_ONLY" if cached is not None
                    else discovery.status)
            if solved_code:
                execution=runner.evaluate(
                    solved_code,e["target_inputs"])
                if execution.status=="EXECUTED":
                    original_preds=list(execution.outputs)
                else:
                    status="ABSTAIN_ORIGINAL_INPUT_EXECUTION"
            row["arms"][arm]={
                "status":status,
                "source_verified":bool(solved_code),
                "program":solved_code,
                "program_sha256":(
                    sha256(solved_code.encode()).hexdigest()
                    if solved_code else None),
                "new_not_in_prior_teacher_programs":(
                    solved_code not in known if solved_code else False),
                "original_target_predictions":original_preds,
                "search_evaluations":(
                    policy.receipt.evaluated_expressions
                    if policy.receipt else 0),
                "search_unique_semantics":(
                    policy.receipt.unique_semantics
                    if policy.receipt else 0),
                "search_elapsed_seconds":(
                    policy.receipt.elapsed_seconds
                    if policy.receipt else 0),
            }
        all_results.append(row)
        print("Q3_STRUCTURAL_SOURCE_ONLY",inp["origin"],e["id"],
              {a:(x["status"],x["program"])
               for a,x in row["arms"].items()},flush=True)
        Path(str(output)+".SOURCE_PARTIAL").write_text(
            canonical({"scope":"SOURCE_ONLY_UNGRADED","rows":all_results})+"\n")
    receipt={
        "schema":"NEUMANN.Q3.STRUCTURAL-PREDICTIONS.v1",
        "origin":inp["origin"],
        "scope":inp["scope"],
        "blind_sha256":sha_file(blind),
        "teacher_sha256":sha_file(teacher_file),
        "policy_weights_sha256":sha256(canonical(fitted.weights).encode()).hexdigest(),
        "learned_operator_weights":fitted.weights,
        "same_general_executable_substrate":True,
        "max_states":6500,
        "max_evaluations":250000,
        "max_proposals":12,
        "target_gold_accessed":False,
        "records":all_results,
    }
    Path(output).write_text(canonical(receipt)+"\n")
    print("Q3_STRUCTURAL_ORIGINAL_PREDICTIONS_FROZEN",
          inp["origin"],sha_file(output),flush=True)


def _codearc_gold(original,problem_id):
    rows={}
    with Path(original).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record=json.loads(line)
            if (record.get("type")=="annotated"
                    and str(record.get("problem_id"))==str(problem_id)):
                rows[int(record["index"])]=record["output"]
    if not all(i in rows for i in (7,8,9)):
        raise ValueError("external original has incomplete target cohort")
    gold=[]
    for i in (7,8,9):
        match=re.match(r"^Result\s+\d+\s*:\s?",rows[i])
        if not match:
            raise ValueError("unexpected original author output format")
        text=rows[i][match.end():]
        try:
            gold.append(ast.literal_eval(text))
        except (SyntaxError,ValueError):
            gold.append(text)
    return gold


def score(blind,predictions,expected_sha,original,output):
    if sha_file(predictions)!=expected_sha:
        raise ValueError("prediction freeze SHA mismatch")
    inp=json.loads(Path(blind).read_text())
    rec=json.loads(Path(predictions).read_text())
    if (rec.get("schema")!="NEUMANN.Q3.STRUCTURAL-PREDICTIONS.v1"
        or rec.get("blind_sha256")!=sha_file(blind)
        or rec.get("target_gold_accessed") is not False
        or rec.get("origin")!=inp.get("origin")
        or len(rec.get("records",[]))!=len(inp.get("records",[]))):
        raise ValueError("wrong external original or target leak")
    if inp["origin"]=="codearc":
        if sha_file(original)!=CODEARC_ORIGINAL_SHA:
            raise ValueError("original CodeARC SHA changed")
    counts={a:0 for a in ("A","B","C")}
    native_count=0
    results=[]
    for x,pred in zip(inp["records"],rec["records"]):
        if x["id"]!=pred["id"]:
            raise ValueError("reordered source-original cohort")
        if inp["origin"]=="codearc":
            gold=_codearc_gold(original,x["id"])
        else:
            grid=json.loads((Path(original)/x["id"]).read_text())
            if sha_file(Path(original)/x["id"])!=x["file_sha256"]:
                raise ValueError("external task original SHA changed")
            gold=[t["output"] for t in grid["test"]]
        arm_exact={}
        for arm in ("A","B","C"):
            row=pred["arms"][arm]
            guess=row["original_target_predictions"]
            exact=bool(
                row["source_verified"] and len(guess)==len(gold)
                and all(source_same_value(y,z)
                        for y,z in zip(guess,gold)))
            arm_exact[arm]=exact
            counts[arm]+=int(exact)
        native=any(len(guess)==len(gold)
                   and all(source_same_value(a,b)
                           for a,b in zip(guess,gold))
                   for guess in pred["native"])
        native_count+=int(native)
        c_only=bool(arm_exact["C"]
                    and not arm_exact["A"] and not arm_exact["B"]
                    and not native)
        results.append({
            "id":x["id"],**arm_exact,
            "native_exact":native,
            "C_exclusive":c_only,
            "C_new_program":pred["arms"]["C"]["new_not_in_prior_teacher_programs"],
            "nonconstant_original_SOURCE":pred["source_output_diverse"],
            "C_exclusive_nonconstant":c_only and pred["source_output_diverse"],
        })
    summary={
        "origin":inp["origin"],"scope":inp["scope"],
        "originals":len(results),
        **counts,
        "native_applicable":inp["origin"]=="arcana",
        "native_exact":native_count if inp["origin"]=="arcana" else None,
        "C_exclusive":sum(x["C_exclusive"] for x in results),
        "C_exclusive_nonconstant":sum(x["C_exclusive_nonconstant"]
                                      for x in results),
        "C_new_executable_original_exact":sum(
            x["C"] and x["C_new_program"] and x["nonconstant_original_SOURCE"]
            for x in results),
        "original_predictions_sha256":expected_sha,
        "q3_global":"OPEN",
    }
    Path(output).write_text(canonical({"summary":summary,"records":results})+"\n")
    print("Q3_STRUCTURAL_ORIGINAL_SCORE",canonical(summary),flush=True)


def gate(codearc,arcana):
    a=json.loads(Path(codearc).read_text())["summary"]
    b=json.loads(Path(arcana).read_text())["summary"]
    if a["origin"]!="codearc" or b["origin"]!="arcana":
        raise ValueError("two independent original author sources required")
    condition=bool(a["C_exclusive_nonconstant"]>0
                   and b["C_exclusive_nonconstant"]>0)
    status=("CROSS_ORIGIN_CANDIDATE_REQUIRES_FURTHER_NOVELTY_AUDIT"
            if condition else "Q3_CAUSAL_CROSS_ORIGIN_GATE_FAIL")
    print("Q3_STRUCTURAL_GLOBAL_GATE",canonical({
        "status":status,"codearc":a,"arcana":b,
        "global_q3":"OPEN","operator_policy_learned_from_prior_SOURCE":True
    }),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    sp=parser.add_subparsers(dest="cmd",required=True)
    for name in ("freeze-codearc","freeze-arcana","freeze-arcana-next8","infer","score","gate"):
        x=sp.add_parser(name)
        if name in ("freeze-codearc","freeze-arcana","freeze-arcana-next8"):
            x.add_argument("--original",required=True)
            x.add_argument("--out",required=True)
        if name=="infer":
            x.add_argument("--blind",required=True)
            x.add_argument("--teachers",required=True)
            x.add_argument("--out",required=True)
        if name=="score":
            x.add_argument("--blind",required=True)
            x.add_argument("--predictions",required=True)
            x.add_argument("--expected-sha",required=True)
            x.add_argument("--original",required=True)
            x.add_argument("--out",required=True)
        if name=="gate":
            x.add_argument("--codearc",required=True)
            x.add_argument("--arcana",required=True)
    args=parser.parse_args()
    if args.cmd=="freeze-codearc":
        freeze_codearc(args.original,args.out)
    elif args.cmd=="freeze-arcana":
        freeze_arcana(args.original,args.out)
    elif args.cmd=="freeze-arcana-next8":
        freeze_arcana_next8(args.original,args.out)
    elif args.cmd=="infer":
        infer(args.blind,args.teachers,args.out)
    elif args.cmd=="score":
        score(args.blind,args.predictions,args.expected_sha,
              args.original,args.out)
    elif args.cmd=="gate":
        gate(args.codearc,args.arcana)
