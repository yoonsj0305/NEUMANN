"""Model-free frozen P1.5 data, architecture, source and checker controls."""
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p13 import admissibility
from neumann1.control_plane_p15 import contract
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p14_catalog import catalog as previous_catalog
from experiments.control_plane_p15_catalog import catalog

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/experiments/control_plane_p15.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p15_public.json"
REFERENCES = ROOT / "docs/experiments/control_plane_p15_references.json"
GATE = {"raw_semantic_accepted_min":6,"raw_math_accepted_min":3,"raw_csp_accepted_min":3,
        "raw_model_calls_exact":8,"semantic_retries":0,"per_item_wall_ms":180000.0,
        "whole_study_wall_ms":1800000.0}
BOUNDARY = {"development_only":True,"fresh_validation_registered":False,
            "p2_registration_admitted":False,"p2_admitted":False,
            "decision3_admitted":False,"global_questions_closed":[]}


def registration():
    reg = json.loads(REG.read_bytes())
    rows = json.loads(PUBLIC.read_bytes())["rows"]
    refs = json.loads(REFERENCES.read_bytes())["rows"]
    if (rows,refs)!=catalog(): raise ValueError("P1.5 catalog content drift")
    if reg["architecture"]!=contract() or reg["gate"]!=GATE or reg["boundaries"]!=BOUNDARY:
        raise ValueError("P1.5 architecture/gate/boundary drift")
    if reg["first_only"] is not True or reg["scores_seen_at_registration"] is not False:
        raise ValueError("P1.5 first-only pre-score registration required")
    if reg["task_ids"]!=[r["task_id"] for r in rows] or reg["task_ids"]!=[r["task_id"] for r in refs]:
        raise ValueError("P1.5 ordered task coverage drift")
    if digest(rows)!=reg["public_sha256"] or digest(refs)!=reg["references_sha256"]:
        raise ValueError("P1.5 data hash drift")
    for path, expected in reg["source_sha256"].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError("P1.5 source byte drift: "+path)
    return reg, rows, refs


def check_construction():
    _, rows, refs = registration()
    previous = {" ".join(r["view"]["public"]["query"].lower().split())
                for r in previous_catalog()[0] if "query" in r["view"]["public"]}
    queries = [" ".join(r["view"]["public"]["query"].lower().split()) for r in rows]
    if len(set(queries))!=8 or set(queries)&previous: raise ValueError("duplicate raw obligation")
    for row, ref in zip(rows,refs):
        if set(row)!={"task_id","view"} or set(row["view"])!={"instruction","public"} or set(row["view"]["public"])!={"query"}:
            raise ValueError("hidden reference field in public view")
        admitted=admissibility(row["view"])
        if admitted["admissible_routes"]!=["DIRECT"] or admitted["interpretation_required"] is not True:
            raise ValueError("raw obligation must stop at unchanged P1.3")
        check=_checker(ref)
        if not check(ref["witness"]): raise ValueError("original positive checker control rejected")
        bad="987654321" if ref["family"]=="math_logic" else {k:987654321 for k in ref["private"]["domains"]}
        if check(bad): raise ValueError("original negative checker control accepted")
    if [r["family"] for r in refs]!=["math_logic"]*4+["constraint_planning"]*4:
        raise ValueError("P1.5 composition drift")
    return {"registration_valid":True,"raw_semantic":8,"positive_checker_controls":8,
            "negative_checker_controls":8,"dedup_scope":"normalized raw text against P1.4; no semantic-novelty claim",
            "model_inference":False,"weights_loaded":False,**BOUNDARY}


if __name__ == "__main__":
    print(json.dumps(check_construction(),sort_keys=True))
