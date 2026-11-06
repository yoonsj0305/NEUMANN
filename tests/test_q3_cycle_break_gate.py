"""Q3 core admission tests. Every positive result is ONLY preflight readiness."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.q3_cycle_break_gate import (
    COST_FIELDS, CLOSED_MECHANISM_CLASSES, analyze,
)


class Q3CoreCycleBreakTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="q3_core_gate_")
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        artifacts = {}
        for role in ("learned_checkpoint", "learned_training_code",
                     "strong_classical_solver", "independent_original_verifier"):
            name = role + ".bin"
            content = ("frozen mock for admission only: " + role).encode()
            (self.repo / name).write_bytes(content)
            artifacts[role] = {
                "file": name,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        manifest = b"sealed IDs and source owners; no real benchmark is scored"
        (self.repo / "holdout_ids.txt").write_bytes(manifest)
        self.spec = {
            "schema": "neumann.q3.unseen-semantic-proposer-admission.v1",
            "strategy": "OWN_WEIGHT_GENERATIVE_EXECUTABLE_AST",
            "generator": {
                "own_weights_trained": True,
                "candidate_can_escape_frozen_H": True,
                "not_only_ranking_or_retrieval": True,
                "typed_executable_AST": True,
                "frozen_before_original_test": True,
            },
            "artifacts": artifacts,
            "evaluation": {
                "source_author": "independent_outside_lab",
                "task_status": "NEVER_OPENED_BY_PROJECT",
                "original_scope": "DIFFERENT_SEMANTIC_FAMILY",
                "gold_hidden_until_source_freeze": True,
                "training_and_test_task_ids_disjoint": True,
                "source_manifest_file": "holdout_ids.txt",
                "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                "from_arc_agi_1_evaluation": False,
            },
            "comparison": {
                "same_program_language_and_primitives": True,
                "same_input_and_tool_rights": True,
                "same_total_runtime_budget": True,
                "strong_GP_CEGIS_and_domain_specialist": True,
                "untrained_generator_ablation": True,
                "independent_original_witness_checker": True,
            },
            "cost_contract": {
                k: {"unit": "ms", "meter": "monotonic profiler"}
                for k in COST_FIELDS
            },
            "first_run": {
                "original_denominator": 12,
                "one_original_FIRST_only": True,
                "negative_mutations_preregistered": True,
                "no_success_from_unknown": True,
                "complete_cost_and_new_witness_required": True,
            },
        }

    def test_full_contract_only_admits_preflight_never_promotes_Q3(self):
        out = analyze(self.spec, self.repo)
        self.assertEqual(out["decision"], "READY_FOR_ONE_FIRST_ATTEMPT_NOT_A_PROOF")
        self.assertTrue(out["experiment_ready"])
        self.assertEqual(out["Q3_learned_discovery"], "NOT_PROVEN")
        self.assertFalse(out["can_consume_untouched_arc_eval"])

    def test_g1_saturated_native_original_family_is_hard_stop_even_with_trained_weights(self):
        s = copy.deepcopy(self.spec)
        s["strategy"] = "OWN_WEIGHT_FIXED_TWO_TOKEN_STRING_AST"
        # The real G1 student actually trained weights. That alone must NOT
        # override the first original 1/5 or native specialist 8/8 proof.
        decision = analyze(s, self.repo)
        self.assertEqual(decision["decision"], "HARD_STOP_REPEAT_CLASS")
        self.assertFalse(decision["spend_authorized"])
        self.assertFalse(decision["can_consume_untouched_arc_eval"])
        self.assertEqual(decision["Q3_learned_discovery"], "NOT_PROVEN")
        self.assertIn("8/8", decision["reason"])

    def test_g1_stop_does_not_ban_other_new_learned_source_families(self):
        # A truly novel own-weight generator on a separate real source family
        # still needs to pass all independent evidence and cost preflights.
        s = copy.deepcopy(self.spec)
        self.assertEqual(
            analyze(s, self.repo)["decision"],
            "READY_FOR_ONE_FIRST_ATTEMPT_NOT_A_PROOF",
        )

    def test_closed_classes_all_blocked_even_with_positive_bools(self):
        for strategy in CLOSED_MECHANISM_CLASSES:
            with self.subTest(strategy=strategy):
                s = copy.deepcopy(self.spec)
                s["strategy"] = strategy
                out = analyze(s, self.repo)
                self.assertEqual(out["decision"], "HARD_STOP_REPEAT_CLASS")
                self.assertFalse(out["spend_authorized"])

    def test_renaming_reranker_to_learned_with_no_checkpoint_not_enough(self):
        s = copy.deepcopy(self.spec)
        s["artifacts"]["learned_checkpoint"]["sha256"] = "0" * 64
        result = analyze(s, self.repo)
        self.assertIn("MISSING_OR_UNVERIFIED_FROZEN_ARTIFACT_LEARNED_CHECKPOINT", result["errors"])
        self.assertFalse(result["spend_authorized"])

    def test_original_source_mutation_fails_closed(self):
        s = copy.deepcopy(self.spec)
        (self.repo / "strong_classical_solver.bin").write_bytes(b"mutated after freeze")
        r = analyze(s, self.repo)
        self.assertIn("MISSING_OR_UNVERIFIED_FROZEN_ARTIFACT_STRONG_CLASSICAL_SOLVER", r["errors"])

    def test_unopened_task_claim_must_be_independent_author_formalism(self):
        s = copy.deepcopy(self.spec)
        s["evaluation"]["source_author"] = "neumann_project"
        s["evaluation"]["task_status"] = "OPENED"
        s["evaluation"]["original_scope"] = "SAME_FINITE_MEALY"
        r = analyze(s, self.repo)
        self.assertIn("NO_INDEPENDENT_EXTERNAL_TASK_AUTHOR", r["errors"])
        self.assertIn("NOT_PROJECT_UNSEEN", r["errors"])
        self.assertIn("NOT_CROSS_FORMALISM", r["errors"])

    def test_arc_original_evaluation_cannot_be_spent_by_this_gate(self):
        s = copy.deepcopy(self.spec)
        s["evaluation"]["from_arc_agi_1_evaluation"] = True
        r = analyze(s, self.repo)
        self.assertIn("ARC_EVAL_RESERVED_GLOBAL_389_USED_11_LEFT", r["errors"])
        self.assertFalse(r["can_consume_untouched_arc_eval"])

    def test_baselines_need_same_rights_and_same_language(self):
        s = copy.deepcopy(self.spec)
        s["comparison"]["same_program_language_and_primitives"] = False
        s["comparison"]["same_input_and_tool_rights"] = False
        r = analyze(s, self.repo)
        self.assertIn("MISSING_EQUAL_RIGHTS_CONTROL_SAME_PROGRAM_LANGUAGE_AND_PRIMITIVES", r["errors"])
        self.assertIn("MISSING_EQUAL_RIGHTS_CONTROL_SAME_INPUT_AND_TOOL_RIGHTS", r["errors"])

    def test_partial_costs_not_admissible(self):
        s = copy.deepcopy(self.spec)
        del s["cost_contract"]["model_training"]
        self.assertIn("INCOMPLETE_ALL_IN_RESOURCE_ACCOUNTING", analyze(s, self.repo)["errors"])

    def test_scoped_program_selector_cannot_fake_generator(self):
        s = copy.deepcopy(self.spec)
        s["strategy"] = "OWN_WEIGHT_GENERATIVE_EXECUTABLE_AST"
        s["generator"]["candidate_can_escape_frozen_H"] = False
        s["generator"]["not_only_ranking_or_retrieval"] = False
        r = analyze(s, self.repo)
        self.assertIn("GENERATOR_REQUIRED_CANDIDATE_CAN_ESCAPE_FROZEN_H", r["errors"])
        self.assertIn("GENERATOR_REQUIRED_NOT_ONLY_RANKING_OR_RETRIEVAL", r["errors"])

    def test_original_gold_and_negative_proof_protection(self):
        s = copy.deepcopy(self.spec)
        s["evaluation"]["gold_hidden_until_source_freeze"] = False
        s["first_run"]["negative_mutations_preregistered"] = False
        s["first_run"]["no_success_from_unknown"] = False
        r = analyze(s, self.repo)
        self.assertIn("TEST_GOLD_LEAK_RISK", r["errors"])
        self.assertIn("NO_INDEPENDENT_NEGATIVE_CONTROLS", r["errors"])
        self.assertIn("UNSAFE_UNKNOWN_PROMOTION", r["errors"])

    def test_source_manifest_content_must_match_sha(self):
        s = copy.deepcopy(self.spec)
        (self.repo / "holdout_ids.txt").write_text("altered unseen provenance")
        self.assertIn("SOURCE_MANIFEST_UNPINNED_OR_UNVERIFIED",
                      analyze(s, self.repo)["errors"])

    def test_symlink_or_parent_path_escape_not_accepted(self):
        s = copy.deepcopy(self.spec)
        s["artifacts"]["learned_checkpoint"]["file"] = "../checkpoint.pt"
        self.assertIn("MISSING_OR_UNVERIFIED_FROZEN_ARTIFACT_LEARNED_CHECKPOINT",
                      analyze(s, self.repo)["errors"])

    def test_no_favorable_original_rerun(self):
        s = copy.deepcopy(self.spec)
        s["first_run"]["one_original_FIRST_only"] = False
        self.assertIn("FAVORABLE_RERUN_RISK", analyze(s, self.repo)["errors"])

    def test_bad_denominator_fails_without_throwing(self):
        s = copy.deepcopy(self.spec)
        s["first_run"]["original_denominator"] = "400"
        self.assertIn("NO_FROZEN_ORIGINAL_DENOMINATOR",
                      analyze(s, self.repo)["errors"])

    def test_unparseable_spec_cannot_create_success(self):
        self.assertEqual(analyze({}, self.repo)["experiment_ready"], False)

    def test_altering_the_baseline_language_violates_fairness(self):
        s = copy.deepcopy(self.spec)
        s["comparison"]["strong_GP_CEGIS_and_domain_specialist"] = False
        self.assertIn("MISSING_EQUAL_RIGHTS_CONTROL_STRONG_GP_CEGIS_AND_DOMAIN_SPECIALIST",
                      analyze(s, self.repo)["errors"])


if __name__ == "__main__":
    unittest.main()
