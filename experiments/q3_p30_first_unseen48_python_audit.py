"""Independent P3.0 original-eval audit, no Node.js synthesis or refitting.

Verify source/census/first receipt bytes, re-execute selected composed programs
using independent Python interpreter of P29 coordinates + P27 object crops.
Audit does NOT independently reimplement all six old TOOL proposers; their
results remain bound to immutable first Node original execution.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha1,sha256
from pathlib import Path
import json,sys
from experiments.q3_p29_fresh48_independent_audit import execute as execute_coordinate,fnv,original_grid

FIRST="8d94cde3a8ce7f0eb1b4265780614fe0b3fc0d5d43deb1367e5c06c595bddbbc"
def blob(path):
    b=Path(path).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def crop_mask(g,fn):
    points=[(i,j) for i,row in enumerate(g) for j,x in enumerate(row) if fn(x)]
    if not points:return None
    r0=min(i for i,_ in points);r1=max(i for i,_ in points)
    c0=min(j for _,j in points);c1=max(j for _,j in points)
    return [row[c0:c1+1] for row in g[r0:r1+1]]
def dominant(g):
    cc=Counter(x for row in g for x in row)
    if not cc:return None
    ranked=sorted(cc.items(),key=lambda x:(-x[1],x[0]))
    if len(ranked)>1 and ranked[0][1]==ranked[1][1]:return None
    return ranked[0][0]
def crop_largest(g):
    H,W=len(g),len(g[0])
    seen=set();components=[]
    for r in range(H):
        for c in range(W):
            if g[r][c]==0 or (r,c) in seen:continue
            queue=[(r,c)];seen.add((r,c))
            for y,x in queue:
                for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                    p=(y+dy,x+dx)
                    if 0<=p[0]<H and 0<=p[1]<W and g[p[0]][p[1]]!=0 and p not in seen:
                        seen.add(p);queue.append(p)
            components.append(queue)
    if not components:return None
    components.sort(key=lambda a:-len(a))
    if len(components)>1 and len(components[0])==len(components[1]):return None
    points=components[0]
    r0=min(r for r,c in points);r1=max(r for r,c in points)
    c0=min(c for r,c in points);c1=max(c for r,c in points)
    return [row[c0:c1+1] for row in g[r0:r1+1]]
def execute(ast,g):
    if not original_grid(g) or type(ast) is not dict or set(ast)!={"kind","preOps","coordinate"}:
        return None
    if ast["kind"]!="object-then-coordinate":return None
    ops=ast["preOps"]
    if type(ops) is not list or len(ops)>1 or any(x not in ("cropNZ","cropBG","cropLargest") for x in ops):
        return None
    x=g
    for op in ops:
        if op=="cropNZ":x=crop_mask(x,lambda v:v!=0)
        elif op=="cropBG":
            bg=dominant(x)
            if bg is None:return None
            x=crop_mask(x,lambda v:v!=bg)
        else:x=crop_largest(x)
        if x is None:return None
    return execute_coordinate(ast["coordinate"],x)
def audit(root,arc,first):
    root,arc=Path(root),Path(arc)
    firstBytes=Path(first).read_bytes();firstHash=sha256(firstBytes).hexdigest()
    receipt=json.loads(firstBytes)
    manifestPath=root/"docs/experiments/q3_p30_FIRST_UNSEEN48_COHORT_FROZEN.json"
    lockPath=root/"docs/experiments/q3_p30_FIRST_UNSEEN48_SOURCE_LOCK.json"
    manifest=json.loads(manifestPath.read_text())
    lock=json.loads(lockPath.read_text())
    errors=[]
    def check(v,e):
        if not v:errors.append(e)
    check(firstHash==FIRST,"ORIGINAL_FIRST_SHA256_DRIFT")
    check(blob(manifestPath)==lock["manifest_blob"],"MANIFEST_CHANGED")
    for p,expected in lock["source_blobs"].items():
        check(blob(root/p)==expected,"SOURCE_CHANGED:"+p)
    excluded=set()
    for src in manifest["previous_manifest_files"]:
        p=root/src["path"]
        check(blob(p)==src["blob"],"EXCLUSION_LIST_CHANGED:"+src["path"])
        doc=json.loads(p.read_text())
        check(len(doc["ids"])==src["count"],"EXCLUSION_COUNT_DRIFT")
        excluded.update(doc["ids"])
    check(len(excluded)==328,"PRIOR_328_UNIQUE_DRIFT")
    allnames=[p.name for p in (arc/"data/evaluation").glob("*.json")]
    check(len(allnames)==400,"UPSTREAM_FILE_COUNT_DRIFT")
    rem=[x for x in allnames if x not in excluded]
    check(len(rem)==72,"FRESH_72_DRIFT")
    selected=sorted(rem,key=lambda x:(fnv(manifest["seed"]+x),x))[:48]
    check(selected==manifest["ids"],"FROZEN_COHORT_SELECTION_DRIFT")
    check(len(receipt["rows"])==48,"FIRST_RECEIPT_COUNT_DRIFT")
    compiled=0;exact=0;wrong=0;new_crop=0;original_ids=[]
    for name,row in zip(manifest["ids"],receipt["rows"]):
        id=name.removesuffix(".json")
        check(row["id"]==id,"ROW_ID_DRIFT:"+id)
        data=(arc/"data/evaluation"/name).read_bytes()
        check(sha256(data).hexdigest()==row["source_json_sha256"],"ORIGINAL_FILE_BYTES_DRIFT:"+id)
        task=json.loads(data)
        ast=row["p30_trace"]["selected_program"]
        check((ast is not None)==row["p30_submitted"],"SUBMISSION_FLAG_DRIFT:"+id)
        if ast is None:
            check(not row["p30_exact"] and not row["p30_wrong"],"FALSE_NON_SUBMITTED_CORRECT:"+id)
            continue
        compiled+=1
        check(all(execute(ast,p["input"])==p["output"] for p in task["train"]),
              "ORIGINAL_TRAIN_EXECUTION_DRIFT:"+id)
        prediction=[execute(ast,x["input"]) for x in task["test"]]
        check(all(x is not None for x in prediction),"ORIGINAL_TEST_UNSUPPORTED:"+id)
        # Original TEST gold consumed only after independent executable output.
        gold=[x["output"] for x in task["test"]]
        accepted=prediction==gold
        check(row["p30_exact"]==accepted,"ORIGINAL_TEST_CORRECTNESS_DRIFT:"+id)
        check(row["p30_wrong"]==(not accepted),"ORIGINAL_TEST_WRONG_FLAG_DRIFT:"+id)
        derived_new=bool(ast["preOps"])
        check(row["p30_new_crop_generated"]==derived_new,"ORIGINAL_NEW_CROP_FLAG_DRIFT:"+id)
        if derived_new:new_crop+=1
        if accepted:exact+=1;original_ids.append(id)
        else:wrong+=1
    c=receipt["counts"]
    for key,v in (
      ("p30_correct",exact),("p30_submitted",compiled),
      ("p30_new_wrong",wrong),("p30_new_crop_generated",new_crop),
      ("p30_fitting_programs",compiled),("N",48)):
        check(c[key]==v,"FIRST_SCORE_DRIFT:"+key)
    check(c["legacy_six_classical_consensus_correct"]==3 and
          c["safe_combined_correct"]==3 and c["safe_added_exact"]==0 and
          c["safe_combined_wrong"]==0 and c["safe_lost_exact"]==0,"FIRST_CLASSICAL_BASELINE_OR_GATE_DRIFT")
    check(receipt["science_status"]=="P30_FIRST_UNSEEN_FAIL_OR_UNSAFE","FALSE_P30_SCIENCE_PROMOTION")
    return {
      "schema":"neumann.q3.p30.first-new48-independent-alternate-language-audit.v1",
      "original_first_sha256":firstHash,
      "audit_pass":len(errors)==0,"errors":errors,
      "first_original_new_evaluation":48,"source_manifest_previous_exclusion":328,
      "original_reserve_after_this_first":24,
      "independent_P30_programs_executed":compiled,
      "independent_original_exact":exact,
      "independent_original_wrong":wrong,
      "independent_new_crop_programs":new_crop,
      "correct_original_ids":original_ids,
      "baseline_original_scores_independently_recomputed":False,
      "baseline_record_anchored_to_original_sha256":True,
      "P30_uses_human_defined_primitive_language":True,
      "scientific_status":"P30_FIRST_UNSEEN_FAIL_OR_UNSAFE",
      "Q3":"OPEN","Q6":"OPEN","Q7":"OPEN"
    }
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: python experiments/q3_p30_first_unseen48_python_audit.py ROOT ARC_ROOT FIRST.json")
    result=audit(*sys.argv[1:])
    print(json.dumps(result,sort_keys=True,indent=2))
    if not result["audit_pass"]:raise SystemExit(1)
