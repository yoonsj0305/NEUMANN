"""Build a real SOURCE-certified teacher set from immutable prior model artifacts.

No reference implementation, original withheld TARGET labels, or oracle score
file is accepted. A generated program must re-pass all 6 SOURCE training
observations and the disjoint 7th SOURCE check in locked Docker.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,validate_code


def build(files,holdout_blind,output,*,expected_original_sha=None):
    holdout=json.loads(Path(holdout_blind).read_text())
    if holdout["schema"]!="NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1":
        raise ValueError("holdout protocol mismatch")
    held_ids={r["id"] for r in holdout["records"]}
    if len(held_ids)!=len(holdout["records"]):
        raise ValueError("duplicate heldout IDs")
    orig=holdout["original_sha256"]
    if expected_original_sha is not None and orig!=expected_original_sha:
        raise ValueError("wrong original source snapshot")
    seen=set()
    verified=[]
    runner=IsolatedPython(max_seconds=8)
    for directory in files:
        blind=json.loads((Path(directory)/"BLIND.json").read_text())
        predictions=json.loads((Path(directory)/"PREDICTIONS.json").read_text())
        if (blind["original_sha256"]!=orig
                or predictions["dataset_sha256"]!=orig
                or predictions.get("blind_sha256")!=hashlib.sha256(
                    (Path(directory)/"BLIND.json").read_bytes()).hexdigest()
                or predictions.get("source_only") is not True
                or predictions.get("no_external_target_gold_in_proposals") is not True):
            raise ValueError("teacher provenance is not SOURCE-only")
        source_by_id={r["id"]:r["source"] for r in blind["records"]}
        if len(source_by_id)!=len(blind["records"]):
            raise ValueError("duplicate prior source ID")
        for row in predictions["records"]:
            pid=row["id"]
            if pid in held_ids:
                raise ValueError("training overlaps heldout original problem")
            if pid in seen:
                continue
            seen.add(pid)
            program=row.get("verified_program")
            source=source_by_id.get(pid)
            if not isinstance(program,str) or source is None or len(source)!=7:
                continue
            code=validate_code(program)
            if row.get("program_sha256")!=hashlib.sha256(code.encode()).hexdigest():
                raise ValueError("source-generated program SHA mismatch")
            if len({json.dumps(x,sort_keys=True) for x,y in source})!=7:
                continue
            result=runner.evaluate(code,[x for x,y in source])
            if result.status!="EXECUTED" or any(
                    got!=expected for got,(_,expected) in zip(
                        result.outputs,source)):
                # Never train on an unverified or abstaining teacher.
                continue
            verified.append({
                "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
                "provenance":"ORIGINAL_SOURCE_ONLY",
                "independent_checks":1,
                "original_id":pid,
                "pairs":source,
                "program":code,
                "sha256":hashlib.sha256(code.encode()).hexdigest()})
    if len(verified)<2:
        raise ValueError("insufficient independent source-certified teachers")
    Path(output).write_text("".join(
        json.dumps(r,sort_keys=True,separators=(",",":"))+"\n"
        for r in verified))
    print("Q3_REAL_SOURCE_TEACHERS",len(verified),
          "IDS",[r["original_id"] for r in verified],
          "SHA",hashlib.sha256(Path(output).read_bytes()).hexdigest())


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--prior",type=Path,nargs="+",required=True)
    p.add_argument("--holdout-blind",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    build(args.prior,args.holdout_blind,args.output)
