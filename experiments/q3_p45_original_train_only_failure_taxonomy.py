"""Q3 P45 original TRAIN-only failure taxonomy.

Post-FIRST causal analysis, NOT fresh source generalization. It reads only
public ARC TRAIN input/output and independently cross-checks immutable P45
FIRST row eligibility. NO TEST target outputs are read or scored.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

FIRST_SHA256="38e41ddd312eb451745f2d73194840e98464e9660d14c52c30537fb7e30bfff5"


def classify(train):
    if not isinstance(train,list) or not train:
        raise ValueError("MISSING_ORIGINAL_TRAIN")
    deltas=Counter()
    changes=0
    for pair in train:
        inp=pair["input"]
        out=pair["output"]
        if not inp or not out or not inp[0] or not out[0]:
            raise ValueError("MALFORMED_ORIGINAL_SHAPE")
        if len(inp)!=len(out) or len(inp[0])!=len(out[0]):
            return {"class":"SHAPE_CHANGE","changed_pixels":None,
                    "distinct_pixel_substitutions":None}
        for i,row in enumerate(inp):
            if len(row)!=len(inp[0]) or len(out[i])!=len(out[0]):
                raise ValueError("NONRECTANGULAR_ORIGINAL")
            for j,v in enumerate(row):
                w=out[i][j]
                if v!=w:
                    deltas[(v,w)]+=1
                    changes+=1
    if changes==0:
        return {"class":"ZERO_PIXEL_CHANGE",
                "changed_pixels":0,"distinct_pixel_substitutions":0}
    if len(deltas)==1:
        return {"class":"SINGLE_PIXEL_MAPPING",
                "changed_pixels":changes,"distinct_pixel_substitutions":1,
                "only_mapping":list(next(iter(deltas)))}
    return {"class":"MULTI_PIXEL_MAPPING",
            "changed_pixels":changes,
            "distinct_pixel_substitutions":len(deltas)}


def run(arc_root,first_path):
    raw=Path(first_path).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=FIRST_SHA256:
        raise ValueError("ORIGINAL_P45_FIRST_SHA_DRIFT")
    first=json.loads(raw)
    rows=first["rows"]
    original=Path(arc_root)/"data"/"training"
    names=sorted(p.name for p in original.glob("*.json"))
    if len(rows)!=400 or len(names)!=400:
        raise ValueError("ORIGINAL_400_DENOMINATOR_DRIFT")
    classified=[]
    classes=Counter()
    for i,filename in enumerate(names):
        if rows[i]["id"]!=filename:
            raise ValueError("ORIGINAL_TASK_ORDER_DRIFT")
        task=json.loads((original/filename).read_text())
        c=classify(task["train"])
        expected_eligible=rows[i]["p45_delta"] is not None
        actual_eligible=c["class"]=="SINGLE_PIXEL_MAPPING"
        if expected_eligible!=actual_eligible:
            raise ValueError("P45_SOURCE_ELIGIBILITY_ROW_MISMATCH_"+filename)
        classes[c["class"]]+=1
        classified.append({"id":filename,**c,
                           "P45_registered_eligible":expected_eligible,
                           "P45_original_first_submitted":rows[i]["p45_submitted"]})
    if classes["SINGLE_PIXEL_MAPPING"]!=63 or sum(classes.values())!=400:
        raise ValueError("FROZEN_P45_ORIGINAL_SUMMARY_CHANGED")
    return {
      "schema":"neumann.q3.p45.train-only-postfirst-expression-taxonomy.v1",
      "scope":"POST_FIRST_DIAGNOSTIC_OPENED_ARC_TRAIN400_NO_TEST_GOLD",
      "original_frozen_first_sha256":sha,
      "source_commit":"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
      "number_originals":len(rows),
      "total_previously_eligible":classes["SINGLE_PIXEL_MAPPING"],
      "class_counts":dict(sorted(classes.items())),
      "original_test_golds_read":0,
      "original_arc_eval_ids_touched":0,
      "inference":"A single-source constant-color, shape-preserving mask extension cannot fit any TRAIN with SHAPE_CHANGE or MULTI_PIXEL_MAPPING. ZERO_PIXEL_CHANGE is INSUFFICIENT_EVIDENCE, not an impossibility theorem. Of the 63 SINGLE_PIXEL_MAPPING, 62 were exactly proven absent from P45 fixed 20-per-task candidate programs by independent first audit.",
      "global_Q3_neural_invention":"OPEN",
      "global_Q6_cross_formalism":"OPEN"
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(sys.argv[1],sys.argv[2]),indent=2,sort_keys=True))
    except Exception as e:
        print(json.dumps({"status":"FAIL_CLOSED","error_type":type(e).__name__,
                          "reason":str(e)}))
        raise SystemExit(1)
