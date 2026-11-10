"""Real-original AUTHOR SOURCE gate for learned relational comprehensions.

SOURCE only; original TEST inputs/outputs are not read in this module.
The standard Q3 blinding, prediction freeze, and post-frozen author scoring
are reused without modifying the evidence boundary.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_relational_predicate_invention import (
    induce_relational_comprehensions)
from neumann1.q3_relational_reduce_invention import (
    induce_relational_reducers)
from research.q3.q3_coordinate_original_source_gate import (
    canonical,SCHEMA,UPSTREAM)


def invent(source_file,out):
    source=json.loads(Path(source_file).read_text())
    if (source.get("original_source_count")!=100 or
        source.get("upstream_revision")!=UPSTREAM or
        source.get("source_scope")!=
            "PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY" or
        source.get("no_target_gold_in_payload") is not True):
        raise ValueError("original SOURCE 100 registry missing")
    runner=IsolatedPython(max_seconds=8)
    rows=[]
    stats={"source_eligible":0,"train_hypotheses":0,
           "programs_docker_verified":0}
    for i,task in enumerate(source["records"]):
        pairs=task["source_pairs"]
        verified=[]
        generated=0
        if 3<=len(pairs)<=32:
            stats["source_eligible"]+=1
            train=pairs[:-1]
            checks=pairs[-1:]
            candidates=(
                *induce_relational_comprehensions(train,max_candidates=4),
                *induce_relational_reducers(train,max_candidates=4),
            )
            generated=len(candidates)
            stats["train_hypotheses"]+=generated
            for hypothesis in candidates:
                inputs=[x for x,y in (*train,*checks)]
                targets=[y for x,y in (*train,*checks)]
                trial=runner.evaluate(hypothesis.program,inputs)
                stats["programs_docker_verified"]+=1
                if (trial.status!="EXECUTED"
                    or len(trial.outputs)!=len(inputs)
                    or not all(source_same_value(p,g)
                               for p,g in zip(trial.outputs,targets))):
                    continue
                verified.append({
                    "program":hypothesis.program,
                    "program_sha256":sha256(
                        hypothesis.program.encode()).hexdigest(),
                    "representation":hypothesis.representation,
                    "source_check_count":len(checks),
                    "source_train_count":len(train),
                    "independent_source_certified":True})
        rows.append({
            "id":task["source_id"],
            "status":"SOURCE_VERIFIED" if verified else "NO_SOURCE_VERIFIED",
            "candidate_count":generated,
            "certified":verified,
            "original_author_file_sha256":
                task["original_author_file_sha256"]})
        if verified:
            print("Q3_RELATIONAL_SOURCE_VERIFIED",
                task["source_id"],len(verified),flush=True)
        if (i+1)%20==0:
            print("Q3_RELATIONAL_SOURCE_PROGRESS",i+1,flush=True)
    result={
        "schema":SCHEMA,
        "original_source_file_sha256":sha256(Path(source_file).read_bytes()).hexdigest(),
        "original_revision":UPSTREAM,
        "source_originals":100,
        "source_verified_count":sum(bool(t["certified"]) for t in rows),
        "prior_exposure":"PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY",
        "target_gold_accessed":False,
        "receipts":rows,
        "q3_global":"OPEN",
        "mechanism":"source-induced-relational-set-comprehension",
        "source_stats":stats,
        "not_independent_language_invention_proof":True,
    }
    Path(out).write_text(canonical(result)+"\n")
    print("Q3_RELATIONAL_SOURCE_INVENTION_RESULT",{
        "source_eligible":stats["source_eligible"],
        "train_hypotheses":stats["train_hypotheses"],
        "source_verified":result["source_verified_count"],
        "global_q3":"OPEN"},flush=True)


if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True)
    a.add_argument("--out",required=True)
    args=a.parse_args()
    invent(args.source,args.out)
