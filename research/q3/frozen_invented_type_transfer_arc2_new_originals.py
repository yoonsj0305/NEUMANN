"""Q3 frozen invented semantics on genuinely different original task source.

Never trains, regenerates or alters the operator type. Decodes only the
content-hash-checked AST frozen in prior ARC-AGI-1 source-first #699, then
applies it to the OFFICIAL ARC-AGI-2 training tasks with filenames absent from
the original ARC-AGI-1 400 training IDs.

ARC-AGI-2 public TRAIN is NOT an independent private benchmark or a blind
neural exclusive test. It is a development-external transfer gate.
No public EVALUATION tasks from either dataset are opened in this experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.q3.autonomously_invent_reusable_semantic_type import (
    NewSemanticType,sha,fit_frozen_library_to_original,
)

ARC1_PIN="399030444e0ab0cc8b4e199870fb20b863846f34"
ARC2_PIN="f3283f727488ad98fe575ea6a5ac981e4a188e49"
PRIOR_FIRST_RUN=42338444257
SCHEMA="neumann.q3.frozen-nonconservative-type-ARC2-new-training-originals.v1"


def load_only_frozen_operator_type(report_path:Path):
    parent=json.loads(report_path.read_text())
    if parent["schema"]!="neumann.q3.new-semantic-type-isomorphism-reuse-original.v1":
        raise ValueError("NOT_FROZEN_NEW_TYPE_FIRST")
    if parent["source_external_original_first_run"]!=42338077481:
        raise ValueError("ORIGIN_CODE_DRIFT")
    if not parent["new_type_frozen_before_target_data"]:
        raise ValueError("NOT_FROZEN_BEFORE_FIRST")
    d=parent["newly_discovered_operator_type"]
    ast=d["function_AST"]
    if ast[0]!="DefineNewReusableSemanticType" or \
       ast[3]!="ColorRole" or ast[4][0]!="Lambda":
        raise ValueError("UNRECOGNIZED_OPERATOR_COMPILER")
    lam=ast[4]
    if lam[2][0]!="Case" or lam[2][3]!=["Abstain","UNKNOWN_SEMANTIC_PAIR"]:
        raise ValueError("NOT_FAIL_CLOSED_OPERATOR")
    if lam[2][1]!=["EncodeArguments",d["learned_input_type"],"roles"]:
        raise ValueError("NEW_TYPE_OBSERVATION_DRIFT")
    cases=tuple((tuple(row[0]),row[1]) for row in lam[2][2])
    operator=NewSemanticType(
        d["learned_input_type"],d["arity"],d["num_abstract_color_roles"],
        cases,tuple(d["source_program_sha256"]))
    if operator.ast()!=ast or sha(ast)!=d["frozen_library_sha256"]:
        raise ValueError("REGENERATED_OR_MUTATED_OPERATOR")
    return operator


def run(arc2_root:Path,arc1_root:Path,frozen_first:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_REAL_SOURCE_FIRST")
    learned=load_only_frozen_operator_type(frozen_first)
    frozen_hash=sha(learned.ast())
    old=[f.stem for f in (arc1_root/"data"/"training").glob("*.json")]
    fresh=sorted((arc2_root/"data"/"training").glob("*.json"))
    if len(old)!=400 or len(fresh)!=1000:
        raise ValueError("PINNED_ORIGINAL_COHORT_SIZE_CHANGED")
    old_ids=set(old)
    newfiles=[f for f in fresh if f.stem not in old_ids]
    if len(newfiles)!=600:
        raise ValueError("ARC2_EXPECTED_EXACTLY_600_NEW_FILES")
    out.mkdir(parents=True)
    (out/"FROZEN_IMPORTED_OPERATOR.json").write_text(json.dumps(
        learned.to_json(),indent=2,sort_keys=True)+"\n")
    results=[]
    for file in newfiles:
        task=json.loads(file.read_text())
        row=fit_frozen_library_to_original(
            learned,task,file.stem,"ARC_AGI_2_NEW_PUBLIC_TRAIN")
        results.append(row)
        if row["status"]=="REUSED_SELF_DISCOVERED_SEMANTIC_TYPE":
            print("FROZEN_TRANSFER_ARC2",file.stem,
                  "exact",row["exact"],"submitted",row["submitted"],
                  flush=True)
    if sha(learned.ast())!=frozen_hash:
        raise ValueError("OPERATOR_CHANGED_AFTER_ARC2_EXPOSURE")
    stats={
        "new_original_cases":len(results),
        "new_original_distinct_from_source_by_id":600,
        "frozen_operator_instantiations":sum(
            x["status"]=="REUSED_SELF_DISCOVERED_SEMANTIC_TYPE"
            for x in results),
        "original_test_submissions":sum(x["submitted"] for x in results),
        "exact_test":sum(x["exact"] for x in results),
        "wrong_submissions":sum(x.get("wrong_submission",False) for x in results),
    }
    report={
        "schema":SCHEMA,
        "original_arc2_pin":ARC2_PIN,
        "original_arc1_pin":ARC1_PIN,
        "frozen_parent_original_first_run":PRIOR_FIRST_RUN,
        "source_programs_from_arcagi1":True,
        "new_cases_from_arcagi2_training_only":True,
        "overlapping_400_original_ids_excluded":True,
        "original_task_ids_not_handpicked":True,
        "new_operator_semantics_never_refit":True,
        "original_test_gold_only_after_frozen_predictions":True,
        "new_operator_type_sha256":frozen_hash,
        "full_original_cohort_statistics":stats,
        "reserved_EVAL_originals_consumed":0,
        "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
        "results":results
    }
    (out/"FIRST.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RESULTS",json.dumps({k:v for k,v in report.items()
                               if k!="results"},sort_keys=True))
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc2-root",required=True,type=Path)
    ap.add_argument("--arc1-root",required=True,type=Path)
    ap.add_argument("--frozen-first",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    run(a.arc2_root,a.arc1_root,a.frozen_first,a.out)
