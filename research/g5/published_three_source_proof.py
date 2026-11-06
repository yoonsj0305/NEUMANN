"""Run unchanged independent CHC certificate engine against three published originals.

All manually supplied proposals are post-source-exposure and MUST NOT be
called a learned, blind, novel or general-intelligence result. The only
scientific positive here is a reusable independent verifier that discharges
original full-universal CHC obligations across one- and two-argument forms,
with negative false-invariant controls per original.
"""
from __future__ import annotations

import hashlib,json,sys
from pathlib import Path
from urllib.request import Request,urlopen
from research.g5.independent_chc_certificate import prove

ROOT=Path(__file__).resolve().parents[2]
CON=ROOT/"docs/experiments/G5_PUBLISHED_CHCCOMP_2025_THREE_SOURCE_PROOF_POSTHOC_2026_11_06.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def run():
    c=json.loads(CON.read_text())
    if len(c["tasks"])!=3:raise ValueError("REGISTERED_ORIGINAL3_CHANGED")
    rows=[]
    for item in c["tasks"]:
        url=("https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/"
             "ddd279cab0717db6effe69baad451a8eb04ffd86/"+item["file"])
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G5-independent-real-2025-source-proof"}),timeout=35) as f:
            raw=f.read(20000)
        if gitblob(raw)!=item["git_blob"]:
            raise ValueError("ORIGINAL_G5_PUBLISHED_GIT_BLOB_MISMATCH_"+item["file"])
        source_proof=prove(raw,item["witness"],5000)
        # Apply a deliberately invalid invariant to same exact original:
        # it must not be mistaken for an actual full-source proof.
        bogus={name:"true" for name in item["witness"]}
        mutant=prove(raw,bogus,5000)
        rows.append({
          "original_source":item["file"],
          "original_git_blob":item["git_blob"],
          "exact_original_bytes_sha256":sha(raw),
          "exact_human_supplied_certificate_sha256":source_proof["certificate_sha256"],
          "source_relations":source_proof["original_predicate_count"],
          "source_assertions":source_proof["original_clause_count"],
          "real_original_allstate_certificate_pass":source_proof["proof_pass"],
          "every_original_rule_negation_UNSAT":(
              all(x["negated_original_rule_UNSAT"] for x in source_proof["negative_rule_counterexample_checks"])
              and source_proof["checked_original_clauses"]==source_proof["original_clause_count"]),
          "original_source_witness_proof":source_proof,
          "mutated_always_true_invariant_rejected":not mutant["proof_pass"],
          "mutant_counterexample_statuses":[x["counterexample_status"] for x in mutant["negative_rule_counterexample_checks"]],
          "learned_model_was_asked_to_generate_witness":False
        })
    passed=all(r["real_original_allstate_certificate_pass"]
             and r["every_original_rule_negation_UNSAT"]
             and r["mutated_always_true_invariant_rejected"] for r in rows)
    return {
      "schema":"neumann.g5.three-published-source-universal-proof-engine-transfer.v1",
      "audit_pass":passed,
      "original_total":3,
      "full_inductive_allstate_original_certificates_verified":sum(r["real_original_allstate_certificate_pass"] for r in rows),
      "mutants_refuted":sum(r["mutated_always_true_invariant_rejected"] for r in rows),
      "all_origins_exact_git_blobs_verified":len(rows),
      "predicate_arities_proved":[r["original_source_witness_proof"]["candidate_predicate_signatures"] for r in rows],
      "originals_already_opened_before_manually_authored_witnesses":True,
      "neumann_learned_model_called":False,
      "no_original_benchmark_was_changed":True,
      "no_ARC_eval_IDs_touched":True,
      "science_scope":"SOURCE_INDEPENDENT_VERIFIER_GENERALIZES_NOT_NEUMANN_LEARNED_POLICY",
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "originals":rows}

if __name__=="__main__":
    try:
        result=run()
        print(json.dumps(result,indent=2,sort_keys=True))
        if not result["audit_pass"]:raise SystemExit(1)
    except Exception as ex:
        print("G5_REAL_SOURCE_CHC_PROOF_FAIL_CLOSED",type(ex).__name__,str(ex),file=sys.stderr)
        raise SystemExit(2)
