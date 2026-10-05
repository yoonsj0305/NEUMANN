"""P1.8 opened-development registration/gate tests; CPU-only."""
import unittest

from neumann1.control_plane_p18_semantic import build_semantic_bundle, selector_prompt, contract as semantic_contract
from experiments.control_plane_p18_registration import registration, check_construction, GATE, BOUNDARY
from experiments.control_plane_p18_runtime import evaluate, totals


def synthetic_rows(b_accept=(True,True,True,True), forwards=36):
    rows=[]
    counts=(2,3,4,3,2,3,4,3)
    for i in range(8):
        is_b=i>=4
        rows.append({
          "task_id":("p18d_b0%d"%(i-3)) if is_b else ("p18d_a0%d"%(i+1)),
          "accepted":b_accept[i-4] if is_b else True,
          "accounting_complete":True,
          "selection":"FEASIBLE_MASKED_SEMANTIC_FULL_S4" if is_b else "UNIQUE_PROVEN_FEASIBLE_ZERO_NEURAL",
          "model_calls":1 if is_b else 0,
          "neural_forward_calls":forwards if is_b else 0,
          "generated_calls":0,"evaluated_tokens":1000 if is_b else 0,"padded_tokens":1000 if is_b else 0,
          "tool_calls":1,"verifier_calls":1,"feasibility_calls":counts[i],
          "feasibility_nodes":counts[i],"feasibility_constraint_checks":counts[i],
          "witness_cache_hits":1,
          "extraction_ms":1.0,"feasibility_ms":1.0,"selection_ms":10.0 if is_b else 0.0,
          "compile_ms":1.0,"routing_ms":1.0,"execution_ms":1.0,"verification_ms":1.0,"complete_ms":20.0,
        })
    return rows


class DevelopmentContracts(unittest.TestCase):
    def test_registration_construction_before_scores(self):
        reg,rows,refs=registration()
        self.assertFalse(reg["scores_seen_at_registration"])
        self.assertTrue(reg["first_only"])
        self.assertEqual(len(rows),8); self.assertEqual(len(refs),8)
        result=check_construction()
        self.assertEqual(result["a_tasks"],4); self.assertEqual(result["b_tasks"],4)
        self.assertEqual(result["candidate_counts"],[2,3,4,3,2,3,4,3])
        self.assertEqual(result["out_of_grammar_stops"],4)
        self.assertFalse(result["model_inference"]); self.assertFalse(result["weights_loaded"])

    def test_semantic_instruction_only_changes_selector_context(self):
        _,rows,_=registration()
        view=rows[4]["view"]; parsed,bundle=build_semantic_bundle(view)
        self.assertNotEqual(view["instruction"],parsed["instruction"])
        self.assertEqual(view["public"]["query"],parsed["public"]["query"])
        prompt=selector_prompt(view,parsed,bundle,(0,1,2,3))
        self.assertIn("spare channel",prompt); self.assertIn("backup channel",prompt)
        self.assertNotIn("semantic_grounding",prompt)
        self.assertFalse(semantic_contract()["generation"])

    def test_synthetic_pass_never_admits_p2(self):
        _,_,refs=registration()
        d=evaluate(synthetic_rows(),refs,True,True,1000.0)
        self.assertEqual(d["verdict"],"PASS")
        self.assertEqual(d["a_accepted"],4); self.assertEqual(d["b_accepted"],4)
        self.assertFalse(d["p2_registration_admitted"]); self.assertFalse(d["decision3_admitted"])

    def test_b_floor_and_cost_are_frozen(self):
        _,_,refs=registration()
        d=evaluate(synthetic_rows((True,True,False,False)),refs,True,True,1000.0)
        self.assertEqual(d["verdict"],"FAIL"); self.assertEqual(d["b_accepted"],2)
        d=evaluate(synthetic_rows(forwards=35),refs,True,True,1000.0)
        self.assertEqual(d["reason"],"CONTROL_PATH_COST_DRIFT")

    def test_accounting_identity_and_wall_fail_closed(self):
        _,_,refs=registration(); rows=synthetic_rows()
        rows[4]["accounting_complete"]=False
        self.assertEqual(evaluate(rows,refs,True,True,1000.0)["reason"],"CONTROL_WORK_ACCOUNTING_FAILURE")
        self.assertEqual(evaluate(synthetic_rows(),refs,False,True,1000.0)["verdict"],"NOT_EVALUATED")
        rows=synthetic_rows(); rows[0]["complete_ms"]=GATE["per_item_wall_ms"]+1
        self.assertEqual(evaluate(rows,refs,True,True,1000.0)["reason"],"TASK_WALL_CAP")

    def test_gate_cost_totals(self):
        rows=synthetic_rows()
        t=totals(rows)
        self.assertEqual(t["model_calls"],4); self.assertEqual(t["neural_forward_calls"],144)
        self.assertEqual(t["feasibility_calls"],24); self.assertEqual(t["tool_calls"],8)
        self.assertEqual(GATE["selector_wall_ms"],180000.0)
        for k in ("p2_registration_admitted","p2_admitted","decision3_admitted"): self.assertFalse(BOUNDARY[k])


if __name__=="__main__": unittest.main()
