"""Q3 first use of ALREADY FROZEN counterexample->new-operator mechanism on ARC2.

Previous immutable source mechanism was frozen at GH blob
4dca73336ace47cd3133aecc49b81e207291a48c before seeing any
ARC-AGI-2 new training original test result. It is NOT tuned here.

On all 233 ARC-AGI-2 public TRAIN original IDs absent from the ENTIRE
ARC-AGI-1 source corpus, run the identical algorithm, attempting a newly
compiled semantic operator only when conservative algebra provably fails.
No cherry-picked tasks, no saved programs or foreign code generation, and
no public ARC2 EVAL or remaining 11 ARC1 EVAL tasks accessed.

ARC2 source task data were already opened in a prior fixed-library zero-result
study, so this is post-exposure development evidence, not a pristine blind
test. Global frontier Q3 remains OPEN.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from research.q3.failure_triggered_semantic_operator_invention import (
    study, PIN
)

ARC2_PIN="f3283f727488ad98fe575ea6a5ac981e4a188e49"
SOURCE_GIT_BLOB="4dca73336ace47cd3133aecc49b81e207291a48c"
SCHEMA="neumann.q3.frozen-inventor-on-arc2-source-distinct-originals.v1"


def source_git_blob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()


def run(arc1_root:Path,arc2_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_CROSS_SOURCE_FIRST")
    candidate=Path(__file__).with_name(
        "failure_triggered_semantic_operator_invention.py")
    if source_git_blob(candidate)!=SOURCE_GIT_BLOB:
        raise ValueError("EXISTING_Q3_INVENTOR_WAS_RETUNED")
    older={f.stem for folder in ("training","evaluation")
           for f in (arc1_root/"data"/folder).glob("*.json")}
    newfiles=sorted((arc2_root/"data"/"training").glob("*.json"))
    if len(older)!=800 or len(newfiles)!=1000:
        raise ValueError("ORIGINAL_DATASET_COUNT_DRIFT")
    unseen=[f for f in newfiles if f.stem not in older]
    if len(unseen)!=233:
        raise ValueError("FROZEN_SOURCE_DISTINCT_233_MANIFEST_DRIFT")
    out.mkdir(parents=True)
    results=[]
    for file in unseen:
        task=json.loads(file.read_text())
        result=study(task,file.stem,"ARC2_NEW_TRAIN_233")
        results.append(result)
        if result["status"]=="INVENTED_NONCONSERVATIVE_OPERATOR":
            print("NEW_TYPE_ARC2",file.stem,
                  "invented",result["new_operator_types"],
                  "original_test_exact",result["exact"],
                  "submitted",result["submitted"],flush=True)
    stats={
        "source_distinct_originals":len(results),
        "invented_new_semantic_operators":sum(
            x["status"]=="INVENTED_NONCONSERVATIVE_OPERATOR" for x in results),
        "original_test_submissions":sum(x["submitted"] for x in results),
        "original_test_exact":sum(x["exact"] for x in results),
        "wrong_submissions":sum(x.get("wrong_submission",False)
                                for x in results)
    }
    report={
        "schema":SCHEMA,"ARC2_PIN":ARC2_PIN,"ARC1_PIN":PIN,
        "source_frozen_git_blob":SOURCE_GIT_BLOB,
        "same_unmodified_inventor_as_original_source_first_42338077481":True,
        "all_233_distinct_source_ids_used":True,
        "all_800_arc1_train_and_eval_ids_excluded":True,
        "ARC2_originals_had_prior_frozen_type_exposure":True,
        "no_new_operator_family_handwritten_for_arc2":True,
        "public_evaluation_tasks_used":0,
        "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
        "stats":stats,"rows":results
    }
    (out/"FIRST_AFTER_ARC2_EXPOSURE.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"},
                               sort_keys=True))
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc1-root",type=Path,required=True)
    ap.add_argument("--arc2-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    run(a.arc1_root,a.arc2_root,a.out)
