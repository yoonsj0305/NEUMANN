"""Frozen ARC2 object graph inventor, all original ARC1 development sources.

The exact graph representation and coordinate-rule invention algorithm was
frozen at blob 99eac52f4dd965f2f9ba8b7ac5315aa43a03d0d7 before this
cross-source attempt. Never retune. This reuses the same method on all 400
ARC1 public TRAIN and exact 32 prior opened original EVAL, excluding sealed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from research.q3.induce_binary_algebra_original import PIN,EVAL32
from research.q3.invent_object_graph_coordinate_operator import study

SOURCE_BLOB="99eac52f4dd965f2f9ba8b7ac5315aa43a03d0d7"
SCHEMA="neumann.q3.frozen-object-graph-original-cross-source-arc1.v1"


def gitblob(file):
    data=file.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()


def run(arc_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_FIRST")
    source=Path(__file__).with_name("invent_object_graph_coordinate_operator.py")
    if gitblob(source)!=SOURCE_BLOB:raise ValueError("GRAPH_INVENTOR_RETUNED")
    out.mkdir(parents=True)
    rows=[]
    for cohort,folder,names in (
        ("ARC1_TRAIN_400","training",None),
        ("ARC1_ALREADY_OPENED_EVAL_32","evaluation",EVAL32)
    ):
        root=arc_root/"data"/folder
        files=sorted(root.glob("*.json")) if names is None \
              else [root/(s+".json") for s in names]
        if len(files)!=(400 if names is None else 32):
            raise ValueError("ORIGINAL_COHORT_CHANGED")
        for file in files:
            case=json.loads(file.read_text())
            rec=study(case,file.stem,cohort)
            rows.append(rec)
            if rec["status"]=="INVENTED_GRAPH_REWRITE_OPERATOR":
                print("CROSS_SOURCE_GRAPH_INVENTION",cohort,file.stem,
                      "test",rec["exact"],"submitted",rec["submitted"],
                      flush=True)
    totals={}
    for cohort in ("ARC1_TRAIN_400","ARC1_ALREADY_OPENED_EVAL_32"):
        arr=[a for a in rows if a["cohort"]==cohort]
        totals[cohort]={"originals":len(arr),
            "operator_definitions":sum(a["status"]=="INVENTED_GRAPH_REWRITE_OPERATOR" for a in arr),
            "original_test_submissions":sum(a["submitted"] for a in arr),
            "original_test_exact":sum(a["exact"] for a in arr),
            "wrong":sum(a.get("wrong_submission",False) for a in arr)}
    report={"schema":SCHEMA,"pin":PIN,"source_blob":SOURCE_BLOB,
        "graph_mechanism_unchanged":True,
        "source_previously_opened_originals_only":True,
        "none_of_11_sealed_eval_ids_consumed":True,
        "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
        "summary":totals,"rows":rows}
    (out/"FIRST.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"},
                               sort_keys=True))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--arc-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();run(a.arc_root,a.out)
