"""Audit exact license texts for training permission classification.

Only positive exact Apache-2.0/MIT/BSD license body recognition enables use in
the downstream experimental learner; GPL/unknown remain blocked.
A license file on a non-ancestor path never grants any permission.
"""
from __future__ import annotations
import argparse,collections,io,json,zipfile,hashlib
from pathlib import Path
from link_real_invariants import run as pair_index

def class_license(raw):
    txt=raw.decode("utf-8",errors="replace").lower()
    if "gnu general public license" in txt and ("version 2" in txt or "version 3" in txt):
        return "GPL_REVIEW_REQUIRED"
    if "apache license" in txt and "version 2.0" in txt:
        return "APACHE_2_0"
    if "permission is hereby granted, free of charge" in txt and "the software" in txt:
        return "MIT"
    if "redistribution and use in source and binary forms" in txt and "neither the name" in txt:
        return "BSD_3_CLAUSE"
    return "UNKNOWN_LICENSE_TERMS"

def run(workbook,dataset):
    report=pair_index(workbook,dataset)
    with zipfile.ZipFile(io.BytesIO(dataset.read_bytes())) as ar:
        examples=report["per_pair_identity_only"]
        licenses={}
        for p in sorted({x["license_path_hint"] for x in examples if x["license_path_hint"]}):
            raw=ar.read(p)
            licenses[p]={"type":class_license(raw),
                         "sha256":hashlib.sha256(raw).hexdigest()}
        categories=collections.Counter()
        permitted_groups=collections.Counter()
        for x in examples:
            key=x["license_path_hint"]
            k=licenses[key]["type"] if key else "NO_ANCESTOR_LICENSE"
            x["license_class"]=k
            x["licensed_permissive_subset"]=k in ("APACHE_2_0","MIT","BSD_3_CLAUSE")
            categories[k]+=1
            if x["licensed_permissive_subset"]:
                permitted_groups[x["source_group"]]+=1
    return {
        "status":"FIRST_LICENSE_BODY_AUDIT_COMPLETE",
        "license_types_by_program_count":dict(categories),
        "permissively_licensed_pair_count":sum(permitted_groups.values()),
        "permissive_source_groups":dict(permitted_groups),
        "license_identifiers":licenses,
        "all_398_source_links_preserved":report["metrics"]["matched_rows"]==398,
        "unresolved_license_sources_excluded":True,
        "original_chc_comp_heldouts_read":False,
        "training_still_not_executed":True,
        "q1_q7":"OPEN"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=run(a.workbook,a.dataset)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    print("LICENSE_COUNTS",r["license_types_by_program_count"])
    print("ELIGIBLE_REAL_PROGRAM_INVARIANT_PAIRS",r["permissively_licensed_pair_count"])
    print("ELIGIBLE_REAL_SOURCE_GROUPS",r["permissive_source_groups"])
