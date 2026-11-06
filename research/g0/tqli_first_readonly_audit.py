"""G0 pinned first-result read-only audit: never rerun the original solver."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PINNED_FIRST_SHA256="658cf722962e5b4844518017878506d137efbf6bcf0f6c0d8268fe338a66a1f2"

def audit(path: str) -> dict:
    raw=Path(path).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    pre=json.loads((ROOT/"docs/experiments/G0_VERYMAX_TQLI_BRANCH_FIRST_PREREG_2026_11_06.json").read_text())
    first=json.loads(raw)
    errors=[]
    if sha!=PINNED_FIRST_SHA256:
        errors.append("ORIGINAL_FIRST_RECEIPT_TAMPERED")
    if first.get("schema")!="neumann.g0.verymax-tqli-branch-original-first.v1":
        errors.append("FIRST_SCHEMA_UNEXPECTED")
    recorded=first.get("original_git_blob")
    if recorded is not None and recorded!=pre["source"]["git_blob_sha1"]:
        errors.append("ORIGINAL_SOURCE_SHA_NOT_MATCHED")
    status=first.get("scientific_status","MISSING")
    if status not in (
       "G0_ORIGINAL_CLASSICAL_BRANCH_SAT_VERIFIED",
       "G0_SAT_VERIFIED_BUT_CLASSICAL_DIRECT_TIE",
       "G0_FIRST_NO_NEW_INDEPENDENT_ORIGINAL_PROOF",
       "INFRA_OR_SOURCE_FAIL_CLOSED"):
        errors.append("UNRECOGNIZED_SCIENCE_STATUS")
    if first.get("Q3_neural_new_semantics") not in (None,"NOT_PROVEN"):
        errors.append("FALSE_Q3_PROMOTION")
    if first.get("Q6_unseen_independent_formalism") not in (None,"NOT_PROVEN"):
        errors.append("FALSE_Q6_PROMOTION")
    if (status.startswith("G0_") and status not in
        ("G0_FIRST_NO_NEW_INDEPENDENT_ORIGINAL_PROOF",)
        and not first.get("closed_semantic_proof",False)):
        errors.append("SAT_WITHOUT_INDEPENDENT_PROOF")
    verdict="FIRST_INFRASTRUCTURE_BLOCKED" if status=="INFRA_OR_SOURCE_FAIL_CLOSED" else (
        "FIRST_NO_PROOF" if status=="G0_FIRST_NO_NEW_INDEPENDENT_ORIGINAL_PROOF"
        else "FIRST_SCOPED_G0_SAT_PROOF")
    return {
       "schema":"neumann.g0.verymax-tqli-first-readonly-audit.v1",
       "pinned_first_sha256":sha,
       "audit_pass":not errors,
       "errors":errors,
       "original_unchanged_status":status,
       "audit_interpretation":verdict,
       "original_source_sha":recorded,
       "source_reference_name":pre["source"]["path"].split("/")[-1],
       "original_first_metadata":{
           "original_assertion_count":first.get("original_assertion_count"),
           "direct_z3":first.get("direct_z3"),
           "branch":first.get("branch_reframe"),
           "original_all_assertions_evaluated":first.get("original_all_assertions_evaluated"),
           "independent_cvc5":first.get("independent_original_cvc5_with_exact_witness"),
           "error_type":first.get("exception_type"),
           "error_message":first.get("exception_message")
       },
       "Q3_neural_structure_discovery":"OPEN",
       "G1_learning":"HOLD",
       "relearned_or_resolved_original":False
    }

if __name__=="__main__":
    out=audit(sys.argv[1])
    print(json.dumps(out,indent=2,sort_keys=True))
    if not out["audit_pass"]:
        raise SystemExit(1)
