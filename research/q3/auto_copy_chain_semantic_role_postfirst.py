"""Post-FIRST repair: recover semantic variable roles from original loop guards.

The preserved FIRST failed real COPY3 at clause 3: 9/9 COPY2, only 3/11
COPY3. Its typed-only role mapper swapped two adjacent Int arguments.
This module keeps the original FIRST untouched and extracts the actual
cursor/bound correspondence from self-loop SSA guards, not from argument
position or a task-name-specific patch.

Human grammar still fixed. No neural invention or cross-formalism claims.
"""
from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path
from urllib.request import Request,urlopen

from research.q3 import auto_copy_chain_chc as frozen
from research.q3.real_copy2_chc_h1 import COPY, WRONG, blob, forms, prove, sha

SCHEMA="neumann.q3.postfirst-semantic-loop-guard-role-recovery.v1"
CONTRACT=frozen.CONTRACT


def recover_limit_roles(source: str, stages: list[str]):
    # A loop stage's induction guard is not a type annotation. It is a
    # semantic constraint whose lhs is the bound and rhs is the cursor.
    blocks=forms(source)
    roles={}
    for i,name in enumerate(stages):
        occ=re.compile(r"\(main@"+re.escape(name)+r"\s+([^()]*)\)")
        candidates=set()
        for block in blocks:
            if not re.match(r"^\(\s*assert\s+",block):
                continue
            calls=list(occ.finditer(block))
            if len(calls)!=2:
                continue
            # Only the genuine self-loop assertion can provide this role.
            args=calls[0].group(1).split()
            cursor_index=2 if i==0 else 4
            if cursor_index>=len(args):
                raise ValueError("CHC_STAGE_CURSOR_LAYOUT_CHANGED")
            cursor=args[cursor_index]
            guard=re.compile(
                r"\(\s*not\s+\(\s*=\s+\(\s*<=\s+([A-Za-z][A-Za-z0-9]*)\s+"
                + re.escape(cursor) +
                r"\s*\)\s+[A-Za-z][A-Za-z0-9]*\s*\)\s*\)"
            )
            bounds=guard.findall(block[calls[0].end():])
            for b in bounds:
                indices=[j for j,t in enumerate(args) if t==b]
                if len(indices)!=1:
                    raise ValueError("BOUNDS_VARIABLE_NOT_UNIQUELY_IN_STAGE")
                candidates.add(indices[0])
        if len(candidates)!=1:
            raise ValueError("NO_UNIQUE_SEMANTIC_LOOP_LIMIT_FROM_GUARD")
        bound=next(iter(candidates))
        if (i==0 and bound<=6) or (i==len(stages)-1 and bound!=5) or (
             0<i<len(stages)-1 and bound<7):
            raise ValueError("BOUND_NOT_VALID_FOR_TYPED_STAGE_FORM")
        roles[name]={"cursor_argument":2 if i==0 else 4,
                     "bound_argument":bound,
                     "evidence":"ORIGINAL_SELF_LOOP_SSA_GUARD"}
    return roles


def generated_semantic_body(stage: int,n: int,bound: int,wrong: bool=False):
    if stage==0:
        bases=[1,4]+list(range(6,bound))
        checks=[f"(> x{i} 0)" for i in bases+[bound]]
        checks+=["(<= 0 x2)",f"(<= x2 x{bound})"]
        checks+=[frozen.relation("x3","x1","x5","x4","x2")]
    elif stage==n-1:
        if bound!=5:
            raise ValueError("FINAL_BOUND_MISPLACED")
        checks=["(> x0 0)","(> x2 0)","(> x5 0)",
                "(<= 0 x4)","(<= x4 x5)",
                frozen.relation("x1","x0","x3","x2","x5")]
    else:
        # Extra future bases occur between the newly written array and
        # the SSA loop bound. The old typed-only algorithm could not
        # distinguish these adjacent Ints and produced a real SAT failure.
        base_positions=[0,2,5]+list(range(7,bound))
        checks=[f"(> x{i} 0)" for i in base_positions+[bound]]
        checks+=["(<= 0 x4)",f"(<= x4 x{bound})"]
        checks+=[frozen.relation("x1","x0","x3","x2",f"x{bound}")]
        checks+=[frozen.relation("x6","x5","x3","x2","x4",
                                wrong=(wrong and stage==1))]
    return "(and "+" ".join(checks)+")"


def compile_candidate(source: str,wrong: bool=False):
    sig,clauses,stages=frozen.signatures_and_edges(source)
    n=frozen.recognize_stage_types(sig,stages)
    roles=recover_limit_roles(source,stages)
    generated=[]
    for i,name in enumerate(stages):
        params=" ".join(f"(x{j} {s})" for j,s in enumerate(sig[name]))
        body=generated_semantic_body(i,n,roles[name]["bound_argument"],wrong)
        generated.append(
            "(define-fun |main@"+name+"| ("+params+") Bool "+body+")")
    prefix="(set-logic ALL)\n"+COPY+"\n"
    if wrong:prefix+=WRONG+"\n"
    prefix+="(define-fun |main@entry| ((x0 Int) (x1 Int)) Bool true)\n"
    prefix+="(define-fun |main@verifier.error.split| () Bool false)\n"
    prefix+="\n".join(generated)+"\n"
    return {"prefix":prefix,"assertions":clauses,"stages":stages,
            "roles":roles,"generated_invariants":generated,"n_arrays":n}


def run(out:Path):
    if out.exists():
        raise ValueError("DO_NOT_OVERWRITE_POSTFIRST_RECEIPT")
    contract=json.loads(CONTRACT.read_text())
    if contract["status"]!="OPENED_DEVELOPMENT_ONLY" or len(contract["cases"])!=2:
        raise ValueError("OPENED_CASE_REGISTRY_CHANGED")
    out.mkdir(parents=True)
    began=time.perf_counter_ns()
    rows=[]
    for entry in contract["cases"]:
        folder=out/entry["name"]
        folder.mkdir(exist_ok=False)
        url=(f"https://raw.githubusercontent.com/{entry['repository']}/{entry['commit']}/"
              +entry["file"])
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-postfirst-typed-role"}),timeout=40) as f:
            raw=f.read(16000)
        if blob(raw)!=entry["git_blob"] or len(raw)!=entry["bytes"]:
            raise ValueError("ORIGINAL_GIT_BLOB_CHANGED")
        original=raw.decode("utf8")
        (folder/"original.smt2").write_bytes(raw)
        generated=compile_candidate(original)
        good=prove(generated,folder/"original_unchanged_clauses",limit_s=7)
        proof=(len(good)==entry["assertions"] and all(x["result"]=="unsat" for x in good))
        bad=[]
        if proof:
            wrong=compile_candidate(original,wrong=True)
            bad=prove(wrong,folder/"mutant",limit_s=7,stop_at_sat=True)
        mutant=any(x["result"]=="sat" for x in bad)
        row={
            "case":entry["name"],"original_git_blob":blob(raw),
            "original_clauses_expected":entry["assertions"],
            "original_clauses_unsat":sum(x["result"]=="unsat" for x in good),
            "source_stage_names":generated["stages"],
            "semantic_roles_from_original_guards":generated["roles"],
            "generated_relations":generated["generated_invariants"],
            "mutant_counterexample_sat":mutant,
            "proof_wall_ms":round(sum(x["wall_ms"] for x in good),3),
            "mutant_wall_ms":round(sum(x["wall_ms"] for x in bad),3),
            "proofs":good,"mutant_proofs":bad
        }
        rows.append(row)
        (folder/"report.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
        if not (proof and mutant):
            break
    report={
      "schema":SCHEMA,"first_run_id_preserved":42320555670,
      "original_first_status":"FAILED_12_OF_20_UNMODIFIED_CLAUSES",
      "postfirst_scope":"REANALYSIS_SAME_ALREADY_OPENED_COPY2_COPY3_NOT_NEW_HOLDOUT",
      "programs_pass":sum(r["original_clauses_unsat"]==r["original_clauses_expected"]
                          and r["mutant_counterexample_sat"] for r in rows),
      "programs_expected":2,
      "original_clauses_unsat":sum(r["original_clauses_unsat"] for r in rows),
      "original_clauses_expected":sum(r["original_clauses_expected"] for r in rows),
      "elapsed_s":round((time.perf_counter_ns()-began)/1e9,4),
      "human_defined_relation_grammar":True,
      "model_train_or_inference_calls":0,
      "new_original_source_access":0,"cross_formalism_transfer":False,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN","rows":rows
    }
    (out/"POSTFIRST_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},sort_keys=True,indent=2))
    if report["programs_pass"]!=2 or report["original_clauses_unsat"]!=20:
        raise RuntimeError("POSTFIRST_SEMANTIC_ROLE_OR_PROOF_STILL_INCOMPLETE")
    return report


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    run(a.parse_args().out)
