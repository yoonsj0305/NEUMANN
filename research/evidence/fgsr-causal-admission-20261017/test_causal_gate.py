"""Negative controls for the Q3/Q7 science-admission boundary (no ML run)."""
import importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("fgsr_causal_gate",HERE/"causal_gate.py")
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

class FirstEvidence(unittest.TestCase):
    def test_three_historical_heldouts_not_promoted(self):
        cases=json.loads((HERE/"historical_three.json").read_text())["cases"]
        self.assertEqual(len(cases),3)
        for x in cases:
            r=g.assess(x)
            self.assertEqual(r["status"],"BLOCKED_CAUSAL_ADMISSION")
            self.assertEqual(r["q1_q7"],"OPEN")
            self.assertTrue(r["reasons"])
    def test_forged_claims_are_never_proof(self):
        src="a"*64; goal="b"*64
        base={"original_sha256":src,"goal_hash":goal}
        arms={k:dict(base) for k in (*g.ROLES,"small","frontier")}
        arms["strong_classical"].update(actual_run_completed=True,verified=False,matched_original_tool_budget=True,matched_source_information=True)
        arms["without_learning"].update(actual_run_completed=True,verified=False)
        arms["neumann"].update(original_clauses_all_unsat=True,original_proof_independently_replayed=True,negative_controls_pass=True,original_verifier_sha256="c"*64)
        arms["small"].update(run_completed=True,verified=False)
        arms["frontier"].update(verified=True,provider_attested=True)
        x={"contract":"NEUMANN_FGSR_CAUSAL_V1",
           "original":{"sha256":src,"goal_hash":goal,"source_group_disjoint":True,
                       "opened_during_model_design":False,"provenance_audited":True},
           "learned_semantics":{"actual_train_updates":1,"frozen_before_target_access":True,
                "full_source_and_goal_input":True,"unprovided_relation_semantics":True,
                "complete_typed_relational_output":True,
                "model_emitted_semantics_not_compiler_inserted":True,
                "holdout_absent_from_training":True,
                "checkpoint_sha256":"d"*64,"decoder_sha256":"e"*64},
            "arms":arms}
        r=g.assess(x)
        self.assertEqual(r["status"],"ELIGIBLE_FOR_INDEPENDENT_REVIEW_NOT_PROVEN")
        self.assertEqual(r["q7_gap"],"REVIEW_ONLY")
        self.assertEqual(r["q1_q7"],"OPEN")
        x["arms"]["neumann"]["original_sha256"]="f"*64
        self.assertIn("MISMATCH_NEUMANN",g.assess(x)["reasons"])
    def test_malformed_nested_receipts_fail_closed(self):
        r=g.assess({"contract":"NEUMANN_FGSR_CAUSAL_V1",
                    "original":[],"learned_semantics":"nonsense","arms":[42]})
        self.assertEqual(r["status"],"BLOCKED_CAUSAL_ADMISSION")
        self.assertEqual(r["q1_q7"],"OPEN")
    def test_no_real_neural_trained_model_blocks(self):
        case=json.loads((HERE/"historical_three.json").read_text())["cases"][0]
        self.assertIn("NO_ACTUAL_TRAINED_SEMANTIC_MODEL",g.assess(case)["reasons"])
    def test_q3_does_not_require_frontier_provider(self):
        # Explicitly tests that Q7 frontier-pair is not mistakenly a Q3 precondition.
        src="a"*64; goal="b"*64
        roles={key:{"original_sha256":src,"goal_hash":goal} for key in g.ROLES}
        roles["strong_classical"].update(actual_run_completed=True,verified=False,matched_original_tool_budget=True,matched_source_information=True)
        roles["without_learning"].update(actual_run_completed=True,verified=False)
        roles["neumann"].update(original_clauses_all_unsat=True,original_proof_independently_replayed=True,
           negative_controls_pass=True,original_verifier_sha256="c"*64)
        x={"contract":"NEUMANN_FGSR_CAUSAL_V1","original":{"sha256":src,"goal_hash":goal,
           "source_group_disjoint":True,"opened_during_model_design":False,"provenance_audited":True},
           "learned_semantics":{"actual_train_updates":1,"frozen_before_target_access":True,
            "full_source_and_goal_input":True,"unprovided_relation_semantics":True,
            "complete_typed_relational_output":True,"model_emitted_semantics_not_compiler_inserted":True,
            "holdout_absent_from_training":True,"checkpoint_sha256":"d"*64,"decoder_sha256":"e"*64},
            "arms":roles}
        r=g.assess(x)
        self.assertEqual(r["status"],"ELIGIBLE_FOR_INDEPENDENT_REVIEW_NOT_PROVEN")
        self.assertEqual(r["q7_gap"],"BLOCKED_PROVIDER_OR_SMALL")

if __name__=="__main__":unittest.main()
