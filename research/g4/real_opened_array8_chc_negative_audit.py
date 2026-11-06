"""G4 ORIGINAL 2025 already-OPENED Array8 generic CHC interface NEGATIVE audit.

This DOES NOT generate/source-learn an invariant. It only verifies that
a source-independent formal checker can parse all 8 real CHC problems and
REJECT vacuous all-false and all-true typed relation assignments, while
proving no original benchmark has been replaced or given a fake SAT witness.

The next eight fresh reserved CHC 2025 sources remain entirely unopened.
"""
from __future__ import annotations

import hashlib,json,time,sys
from pathlib import Path
from urllib.request import Request,urlopen
from research.g4.generic_chc_independent_proof import (
 source_contract,independent_verify_original_chc_sat,
)

ROOT=Path(__file__).resolve().parents[2]
CON=ROOT/"docs/experiments/G4_REAL_G3_OPENED_ARRAY8_GENERIC_CHC_NEGATIVE_PROOF_CONTRACT_2026_11_06.json"
PRE=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
SOURCE_FIRST_SHA="47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8"

def sha(raw:bytes):return hashlib.sha256(raw).hexdigest()
def gitblob(raw:bytes):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def read_source(ref:str,path:str)->bytes:
    url="https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/"+ref+"/"+path
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G4-CHC-2025-already-opened-negative-only"}),timeout=40) as r:
       return r.read(50000)

def audit(original_first_path:Path):
    contract=json.loads(CON.read_text())
    pre=json.loads(PRE.read_text())
    original=original_first_path.read_bytes()
    if sha(original)!=SOURCE_FIRST_SHA or contract["source"]["prior_first_SHA256"]!=SOURCE_FIRST_SHA:
        raise ValueError("G4_ORIGINAL_SOURCE_EIGHT_FIRST_SHA_CHANGED")
    first=json.loads(original)
    if first["cohort"]!="ARRAY_CHC" or len(first["rows"])!=8:
        raise ValueError("FIRST_ORIGINAL_ARRAY_DENOMINATOR_DRIFT")
    grp=next(c for c in pre["cohorts"] if c["id"]=="ARRAY_CHC")
    if len(grp["targets"])!=8:
        raise ValueError("REGISTERED_ORIGINAL_SOURCE_COUNT_CHANGED")
    if any(not t["file"].endswith(".smt2") for t in grp["targets"]):
        raise ValueError("UNAUTHORIZED_ORIGINAL_SUFFIX")
    rows=[]
    for row,target in zip(first["rows"],grp["targets"]):
        if row["file"]!=target["file"] or row.get("git_blob")!=target["git_blob"]:
            raise ValueError("REGISTERED_ORIGINAL_SOURCE_ORDER_OR_BLOB_CHANGED")
        raw=read_source(pre["upstream"]["commit"],grp["folder"]+"/"+target["file"])
        if gitblob(raw)!=target["git_blob"] or sha(raw)!=row["original_source_sha256"]:
            raise ValueError("PUBLISHER_ORIGINAL_BLOB_SHA_MISMATCH")
        whole=raw.decode("utf8")
        spec=source_contract(whole)
        names=spec["relations"]
        deg=[len(sorts) for sorts in names.values()]
        arrays=sum(
           1 for sorts in names.values() for s in sorts
           if isinstance(s,list) and len(s)>=1 and s[0]=="Array"
        )
        typed_param_map={name:[f"q{i}" for i in range(len(sorts))] for name,sorts in names.items()}
        mutants={}
        for flag in ("false","true"):
            proposal={name:{"params":typed_param_map[name],"body":flag}
                      for name in names}
            mutants[flag]=independent_verify_original_chc_sat(whole,proposal,2000)
        # Rejection is a semantic finding, not mere parsing failure.
        if any(mutants[x]["verified"] for x in mutants):
            raise ValueError("G4_FULL_ORIGINAL_CHC_FALSE_MUTANT_UNEXPECTEDLY_ACCEPTED_"+target["file"])
        rows.append({
           "source_file":target["file"],"source_git_blob":target["git_blob"],
           "original_source_sha256":sha(raw),
           "original_CHC_relations":len(names),
           "Horn_original_assertions":len(spec["assertions"]),
           "source_relation_max_arity":max(deg),
           "original_array_sort_argument_slots":arrays,
           "semantic_false_model_rejected":not mutants["false"]["verified"],
           "semantic_true_model_rejected":not mutants["true"]["verified"],
           "false_model_first_failed_obligation":mutants["false"]["independent_checks"][-1] if mutants["false"]["independent_checks"] else None,
           "true_model_first_failed_obligation":mutants["true"]["independent_checks"][-1] if mutants["true"]["independent_checks"] else None,
           "supported_generic_original_types":True,
           "no_model_synthesis_or_learned_structure":True})
    assert len(rows)==8
    return {
      "schema":"neumann.g4.2025-opened-array8-generic-CHC-source-SAT-witness-negative.v1",
      "audit_pass":all(r["semantic_false_model_rejected"] and r["semantic_true_model_rejected"] for r in rows),
      "original_first_pinned_sha256":SOURCE_FIRST_SHA,
      "original_source_files":len(rows),
      "all_original_CHC_parser_supported":all(r["supported_generic_original_types"] for r in rows),
      "all_false_candidate_relations_rejected":sum(r["semantic_false_model_rejected"] for r in rows),
      "all_true_candidate_relations_rejected":sum(r["semantic_true_model_rejected"] for r in rows),
      "original_CHC_relation_totals":sum(r["original_CHC_relations"] for r in rows),
      "original_array_sort_argument_slots":sum(r["original_array_sort_argument_slots"] for r in rows),
      "max_original_relation_arity":max(r["source_relation_max_arity"] for r in rows),
      "valid_original_2025_source_SAT_invariant_found":0,
      "reserved_unread_eight_sources_opened":0,
      "learned_neural_model_training_or_inference_calls":0,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "rows":rows}
if __name__=="__main__":
    try:
        o=audit(Path(sys.argv[1]))
        print(json.dumps(o,indent=2,sort_keys=True))
        if not o["audit_pass"]:raise SystemExit(1)
    except Exception as e:
        print("G4_REAL_ORIGINAL_CHC_NEGATIVE_INTERFACE_FAIL_CLOSED",type(e).__name__,str(e)[:290],file=sys.stderr)
        raise SystemExit(2)
