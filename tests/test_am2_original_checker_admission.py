"""First AM2 source-checker admission NEGATIVE contract tests; no model/task content.

The words PASS in a forged task or a synthetic checker are never authority.
"""
import importlib
import sys
import types
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
if "neumann1" not in sys.modules:
    m=types.ModuleType("neumann1")
    m.__path__=[str(ROOT/"neumann1")]
    sys.modules["neumann1"]=m
abi=importlib.import_module("neumann1.am2_generic_qa_abi")
gate=importlib.import_module("neumann1.am2_original_checker_admission")

PUBLIC={"schema":abi.SCHEMA,"question":"Return the original derivation.",
        "answer_kind":"short_text"}
def task(origin,idx=0):
    spec=next(x for x in gate.CATALOG if x["origin"]==origin)
    return {"origin":origin,"commit":spec["commit"],"original_path":"opened/src"+str(idx)+".sl",
       "original_sha256":("%064x"%(idx+1)),
       "task_id":"OPENED_REAL_TASK_"+str(idx),
       "checker_modality":spec["modality"],
       "checker_artifact_sha256":("%064x"%(idx+200)),
       "checker_runtime_kind":"TRUSTED_SMT_SOURCE_PROVER",
       "license_status":"ORIGINAL_SOURCE_PERMISSION_VERIFIED",
       "public":dict(PUBLIC)}

class TestAdmission(unittest.TestCase):
    def test_all_three_upstream_candidates_are_metadata_only(self):
        self.assertEqual(len(gate.CATALOG),3)
        self.assertEqual(len(set(x["origin"] for x in gate.CATALOG)),3)
        self.assertEqual(len(set(x["commit"] for x in gate.CATALOG)),3)
        self.assertEqual(set(x["answer_representation"] for x in gate.CATALOG),
           {"INDUCTIVE_SMT_FORMULA","PYTHON_FUNCTION_BODY","LEAN_PROOF_TERM"})
    def test_real_current_registry_is_zero_not_faked(self):
        result=gate.evaluate([])
        self.assertEqual(result["actual_original_task_records"],0)
        self.assertFalse(result["scientific_admitted"])
        self.assertEqual(result["global_Q1_Q7"],"OPEN")
        self.assertEqual(result["model_calls"],0)
    def test_applicant_forged_receipt_cannot_admit(self):
        r=gate.evaluate([],
          submitted_receipts=[{"all_checks_pass":True,"model_success":True}])
        self.assertFalse(r["scientific_admitted"])
        self.assertTrue(r["self_attested_checker_result_not_authority"])
        self.assertEqual(r["ignored_untrusted_receipt_count"],1)
    def test_fake_twentyfour_not_original_admission(self):
        origins=[x["origin"] for x in gate.CATALOG]
        rows=[task(origins[i//8],i) for i in range(24)]
        result=gate.evaluate(rows,submitted_receipts=[{"signed":True}]*24)
        self.assertTrue(result["gates"]["at_least_24_actual_original_source_records"])
        self.assertTrue(result["gates"]["at_least_3_registered_origins_8_each"])
        self.assertTrue(result["gates"]["all_unique_original_ids"])
        self.assertTrue(result["gates"]["all_unique_original_sha256"])
        self.assertFalse(result["gates"]["all_source_metadata_valid"])
        self.assertFalse(result["scientific_admitted"])
    def test_duplicate_original_id_rejected(self):
        a=task("SyGuS-Org/benchmarks",1)
        b=task("SyGuS-Org/benchmarks",2);b["task_id"]=a["task_id"]
        self.assertFalse(gate.evaluate([a,b])["gates"]["all_unique_original_ids"])
    def test_duplicate_exact_source_sha_rejected(self):
        a=task("SyGuS-Org/benchmarks",1)
        b=task("SyGuS-Org/benchmarks",2);b["original_sha256"]=a["original_sha256"]
        self.assertFalse(gate.evaluate([a,b])["gates"]["all_unique_original_sha256"])
    def test_unknown_origin_fails(self):
        a=task("SyGuS-Org/benchmarks")
        a["origin"]="unknown/benchmark"
        self.assertIn("UNREGISTERED_ORIGIN",gate.metadata_errors(a))
    def test_mismatched_original_commit_fails(self):
        a=task("SyGuS-Org/benchmarks");a["commit"]="0"*40
        self.assertIn("UPSTREAM_COMMIT_DRIFT",gate.metadata_errors(a))
    def test_original_directory_traversal_fails(self):
        a=task("SyGuS-Org/benchmarks");a["original_path"]="../private.sol"
        self.assertIn("ORIGINAL_SOURCE_PATH_UNSAFE",gate.metadata_errors(a))
    def test_source_or_checker_hash_missing_rejected(self):
        a=task("SyGuS-Org/benchmarks");a["original_sha256"]="garbage"
        self.assertIn("MISSING_ORIGINAL_SHA256",gate.metadata_errors(a))
        a=task("SyGuS-Org/benchmarks");a["checker_artifact_sha256"]=None
        self.assertIn("MISSING_CHECKER_ARTIFACT_SHA256",gate.metadata_errors(a))
    def test_invariant_cannot_be_verified_by_lean_or_label_key(self):
        a=task("SyGuS-Org/benchmarks")
        a["checker_modality"]="FORMAL_LEAN_PROOF_KERNEL"
        self.assertIn("WRONG_ORIGINAL_CHECKER_MODALITY",gate.metadata_errors(a))
        a=task("SyGuS-Org/benchmarks")
        a["checker_runtime_kind"]="LOOKUP_GOLD_ANSWER"
        self.assertIn("NO_ACTUAL_ORIGINAL_CHECKER_RUNTIME",gate.metadata_errors(a))
    def test_private_gold_field_rejected(self):
        a=task("SyGuS-Org/benchmarks")
        a["public"]["gold"]="secret"
        self.assertIn("PUBLIC_PRIVATE_INPUT_BOUNDARY_INVALID",gate.metadata_errors(a))
    def test_original_license_unknown_blocks(self):
        a=task("SyGuS-Org/benchmarks")
        a["license_status"]="UNKNOWN"
        self.assertIn("ORIGINAL_LICENSE_NOT_AUDITED",gate.metadata_errors(a))
    def test_short_text_answer_does_not_implement_smt_original_checker(self):
        a=task("SyGuS-Org/benchmarks")
        self.assertIn("ORIGINAL_ANSWER_ABI_NOT_IMPLEMENTED",
                      gate.metadata_errors(a))
    def test_lean_and_code_do_not_inherit_short_text_authority(self):
        for origin in ("openai/human-eval","facebookresearch/miniF2F"):
            with self.subTest(origin=origin):
                self.assertIn("ORIGINAL_ANSWER_ABI_NOT_IMPLEMENTED",
                              gate.metadata_errors(task(origin)))
    def test_developer_boolean_markers_are_rejected(self):
        a=task("SyGuS-Org/benchmarks")
        a["admitted"]=True
        a["original_checker_pass"]=True
        self.assertIn("UNTRUSTED_EXTRA_OR_MISSING_FIELDS",
                      gate.metadata_errors(a))
    def test_mainline_authentic_provenance_remains_unproven(self):
        r=gate.evaluate([])
        self.assertFalse(r["gates"]["real_source_bound_checker_executed"])
        self.assertFalse(r["gates"]["strong_tool_plus_headroom_independently_measured"])
        self.assertFalse(r["gates"]["license_original_provenance_audited"])
        self.assertFalse(r["sealed_task_content_accessed"])
        self.assertEqual(r["historical_AM1"],"FAIL_UNCHANGED")

if __name__=="__main__":
    unittest.main()
