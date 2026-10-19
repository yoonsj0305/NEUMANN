"""AM2 original-checker eligibility gate. Engineering only (Issue #265).
Three actual upstream repositories are CANDIDATES, never fabricated original tasks.
The gate cannot certify an externally claimed checker without a trusted runner.
No original task/secret/solution or sealed family is loaded by this code.
"""
from __future__ import annotations
from collections import Counter
import json
import re
from pathlib import Path
from neumann1.am2_generic_qa_abi import validate_public

CATALOG=(
  {"origin":"SyGuS-Org/benchmarks",
   "commit":"13c8deb68a873635879c9a69bc78caebd340f646",
   "modality":"SMT_ORIGINAL_INDUCTIVE_THREE_VC",
   "answer_representation":"INDUCTIVE_SMT_FORMULA",
   "source_license":"NOT_INDEPENDENTLY_VERIFIED"},
  {"origin":"openai/human-eval",
   "commit":"b9453e8f1865df0a0057a1383767caa400acfbcf",
   "modality":"ISOLATED_ORIGINAL_CODE_TESTS",
   "answer_representation":"PYTHON_FUNCTION_BODY",
   "source_license":"REPOSITORY_MIT_LICENSE"},
  {"origin":"facebookresearch/miniF2F",
   "commit":"e4f113090ad82d64f8ce064d2f55b613a9b6bded",
   "modality":"FORMAL_LEAN_PROOF_KERNEL",
   "answer_representation":"LEAN_PROOF_TERM",
   "source_license":"LEAN_FOLDER_APACHE_LICENSE"},
)
REQUIRED=24
ORIGINS=3
MIN_EACH=8
SHAREPORT={"short_text","choice","integer"}
SHA256=re.compile(r"^[0-9a-f]{64}$")

def metadata_errors(row):
    if type(row) is not dict:return ["INVALID_ORIGINAL_RECORD"]
    errors=[]
    catalog={x["origin"]:x for x in CATALOG}
    allowed={"origin","commit","original_path","original_sha256",
             "task_id","checker_modality","checker_artifact_sha256",
             "checker_runtime_kind","license_status","public"}
    if set(row)!=allowed:errors.append("UNTRUSTED_EXTRA_OR_MISSING_FIELDS")
    spec=catalog.get(row.get("origin"))
    if spec is None:errors.append("UNREGISTERED_ORIGIN")
    else:
        if row.get("commit")!=spec["commit"]:errors.append("UPSTREAM_COMMIT_DRIFT")
        if row.get("checker_modality")!=spec["modality"]:
            errors.append("WRONG_ORIGINAL_CHECKER_MODALITY")
        if spec["answer_representation"] not in SHAREPORT:
            errors.append("ORIGINAL_ANSWER_ABI_NOT_IMPLEMENTED")
    path=row.get("original_path")
    if type(path) is not str or len(path)>300 or not path or "\\" in path or path.startswith("/") or any(
        x in ("","..",".") for x in path.split("/")):
        errors.append("ORIGINAL_SOURCE_PATH_UNSAFE")
    for field in ("original_sha256","checker_artifact_sha256"):
        if not SHA256.fullmatch(str(row.get(field))):
            errors.append("MISSING_"+field.upper())
    if type(row.get("task_id")) is not str or not 0<len(row["task_id"])<=100:
        errors.append("ORIGINAL_TASK_ID_INVALID")
    if row.get("checker_runtime_kind") not in {
        "TRUSTED_SMT_SOURCE_PROVER",
        "ISOLATED_EXECUTABLE_CODE_ORIGINAL_TESTS",
        "TRUSTED_LEAN_PROOF_KERNEL",
    }:
        errors.append("NO_ACTUAL_ORIGINAL_CHECKER_RUNTIME")
    if row.get("license_status") not in {
        "ORIGINAL_SOURCE_LICENSE_VERIFIED_MIT",
        "ORIGINAL_SOURCE_LICENSE_VERIFIED_APACHE",
        "ORIGINAL_SOURCE_PERMISSION_VERIFIED",
    }:
        errors.append("ORIGINAL_LICENSE_NOT_AUDITED")
    try:validate_public(row.get("public"))
    except Exception:errors.append("PUBLIC_PRIVATE_INPUT_BOUNDARY_INVALID")
    return errors

def evaluate(tasks,submitted_receipts=None):
    """Applicant metadata and self-attested PASS receipts do not confer authority.

    Real admission needs outside-run original test execution and checker source
    binding, a task-compatible ABI and audited strong-tool headroom. Those are
    NOT installed here; the result intentionally fails closed, never fake 24.
    """
    if type(tasks) is not list:raise ValueError("TASKS_MUST_BE_LIST")
    errors={}
    counts=Counter()
    ids=[]
    hashes=[]
    for i,t in enumerate(tasks):
        e=metadata_errors(t)
        if e:errors[str(i)]=e
        if type(t) is dict:
            counts[t.get("origin")]+=1
            ids.append((t.get("origin"),t.get("task_id")))
            hashes.append(t.get("original_sha256"))
    checks={
        "at_least_24_actual_original_source_records":len(tasks)>=REQUIRED,
        "at_least_3_registered_origins_8_each":sum(
            num>=MIN_EACH for num in counts.values())>=ORIGINS,
        "all_unique_original_ids":len(set(ids))==len(ids),
        "all_unique_original_sha256":len(set(hashes))==len(hashes),
        "all_source_metadata_valid":not errors,
        "real_source_bound_checker_executed":False,
        "type_specific_original_answer_adapter_connected":False,
        "license_original_provenance_audited":False,
        "strong_tool_plus_headroom_independently_measured":False,
    }
    return {"schema":"neumann.am2.original-cohort-admission.v1",
            "catalog":list(CATALOG),
            "catalog_metadata_only":True,
            "registered_public_repo_candidates":len(CATALOG),
            "actual_original_task_records":len(tasks),
            "metadata_rejections":errors,
            "source_count_by_origin":dict(counts),
            "gates":checks,
            "status":"BLOCKED_NOT_AN_ADMITTED_OPENED_24_COHORT",
            "scientific_admitted":False,
            "self_attested_checker_result_not_authority":True,
            "ignored_untrusted_receipt_count":len(submitted_receipts or []),
            "model_calls":0,"gpu_calls":0,"paid_api_calls":0,
            "sealed_task_content_accessed":False,
            "historical_AM1":"FAIL_UNCHANGED",
            "global_Q1_Q7":"OPEN"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=evaluate([])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("REGISTERED_REAL_UPSTREAM_REPO_CANDIDATES",len(CATALOG))
    print("ACTUAL_ADMITTED_OPENED_ORIGINALS",result["actual_original_task_records"])
    print("EX1_METADATA_SOURCE_ELIGIBILITY",result["status"])
    print("Q1_Q7_GLOBAL",result["global_Q1_Q7"])
if __name__=="__main__":main()
