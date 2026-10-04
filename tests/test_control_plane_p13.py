"""Synthetic P1.3 control contracts; zero actual model inference."""
import json
import unittest
from unittest.mock import Mock, patch

from neumann1.control_plane_v1 import snapshot
from neumann1.control_plane_p13 import (admissibility, route, execute_selected, contract,
    MODEL, CODE_TOKEN_IDS, CodePlan, plan_cost)
from neumann1.control_plane_p12 import PERMUTATIONS


def math_view():
    return {"instruction": "Compute the supplied expression exactly.",
            "public": {"expression": "(a+b)/c", "bindings": {"a": 5, "b": 7, "c": 4}, "background": "CSP PYTHON"}}


def csp_view():
    return {"instruction": "Find a complete satisfying assignment.",
            "public": {"domains": {"x": [1,2], "y": [1,2]}, "constraints": [["lt", "x", "y"]]}}


def code_view():
    return {"instruction": "Implement solve(items).", "public": {"requirement": "Return the first element or zero if empty.",
            "examples": [{"input": [7,8], "output": 7}]}}


def mixed_view():
    return {"instruction": "Use the constraint representation to fulfill the obligation.",
            "public": {**math_view()["public"], **csp_view()["public"]}}


def receipt():
    # The inadmissible DIRECT/PYTHON routes dominate deliberately. Eligible
    # CSP must still win over eligible ARITHMETIC after masking, in all modes.
    scores = [-1., -8., -3., -2.]
    matrix = [[scores[p.index(i)] for i in range(4)] for p in PERMUTATIONS]
    passes = []; totals = {k: 0 for k in ("input_rows", "score_rows", "scored_tokens", "evaluated_tokens", "padded_tokens", "forward_calls")}
    for mode,size,order in (("batch4",4,list(range(24))), ("unbatched1",1,list(range(24))), ("reverse_batch4",4,list(reversed(range(24))))):
        prefixes = [[1,2,3] for _ in order]
        cost = plan_cost(CodePlan(tuple(tuple(p) for p in prefixes), CODE_TOKEN_IDS), size)
        for k,v in cost.items(): totals[k] += v
        passes.append({"status": "COMPLETE", "mode": mode, "batch_size": size, "order": order,
            "prefixes": prefixes, "code_ids": list(CODE_TOKEN_IDS), "planned": cost, "actual": cost,
            "matrix": snapshot(matrix), "peak_accelerator_memory_bytes": 1})
    return {"status": "COMPLETE", "identity": dict(MODEL), "audit": {"unchanged": True},
            "passes": passes, "ledger": totals, "generated_calls": 0}


class ContractFirstTests(unittest.TestCase):
    def test_unique_contract_no_scorer_construction_or_neural_work(self):
        factory = Mock(side_effect=AssertionError("no model allowed"))
        for view,want in ((math_view(),"ARITHMETIC"),(csp_view(),"CSP"),(code_view(),"PYTHON")):
            with self.subTest(route=want):
                r = route(view,factory)
                self.assertEqual(r["selected_route"],want)
                self.assertEqual(r["admissible_routes"],[want])
                self.assertEqual(r["neural_forward_calls"],0)
                self.assertEqual(r["fallback_calls"],0)
                self.assertEqual(r["generated_calls"],0)
        factory.assert_not_called()

    def test_public_order_background_and_variable_names_do_not_select_routes(self):
        v = csp_view(); v["instruction"] = "ARITHMETIC ARITHMETIC"; v["public"]["background"] = "DIRECT"
        v["public"] = dict(reversed(list(v["public"].items())))
        self.assertEqual(route(v)["selected_route"],"CSP")
        v["public"]["domains"] = {"q": [1,2],"r": [1,2]}; v["public"]["constraints"] = [["lt","q","r"]]
        self.assertEqual(route(v)["selected_route"],"CSP")

    def test_metadata_unknown_keys_and_partial_groups_fail_closed(self):
        for key in ("family","task_id","hidden_answer","compatible_route","reference"):
            for level in ("public","outer"):
                v=math_view(); (v["public"] if level=="public" else v)[key]="CSP"
                self.assertEqual(route(v)["status"],"REJECTED")
        for view,key in ((math_view(),"bindings"),(csp_view(),"constraints"),(code_view(),"examples")):
            del view["public"][key]; self.assertEqual(route(view)["status"],"REJECTED")
        v=mixed_view(); v["public"]["domains"]={"x":[True]}
        self.assertEqual(route(v)["status"],"REJECTED")

    def test_arithmetic_real_grammar_not_presence_only(self):
        for expr,bindings in (("__import__('os')",{}),("a**3",{"a":2}),("a.b",{"a":2}),
                ("True",{}),("1.5",{}),("x+1",{}),("x",{"x":True}),("x",{"x":10**13})):
            v=math_view(); v["public"].update(expression=expr,bindings=bindings)
            self.assertEqual(route(v)["status"],"REJECTED",expr)
        v=math_view(); v["public"]["expression"]="1/0"
        self.assertEqual(route(v)["selected_route"],"ARITHMETIC")

    def test_csp_real_grammar_cardinality_and_resource_admission(self):
        for domains,constraints in (({"x":[1,1]},[]), ({"x":[True]},[]), ({"x":[1]},[["bad","x",1]]),
                ({"x":[1]},[["eq","x","missing"]]), ({"x":[1]},[["eq","x",True]]),
                ({"v%d"%i:list(range(8)) for i in range(9)},[]), ({},[])):
            v=csp_view(); v["public"].update(domains=domains,constraints=constraints)
            self.assertEqual(route(v)["status"],"REJECTED")

    def test_coding_contract_is_not_generated_source_or_correctness(self):
        v=code_view(); v["public"]["examples"][0]["hidden_test"]=True
        self.assertEqual(route(v)["status"],"REJECTED")
        v=code_view(); v["public"]["requirement"]=" "
        self.assertEqual(route(v)["status"],"REJECTED")
        r=route(code_view()); self.assertNotIn("answer",r)

    def test_raw_input_and_mixed_without_adapter_abstain(self):
        v={"instruction":"Solve the raw problem.","public":{"query":"What is x?"}}
        factory=Mock(side_effect=AssertionError("no generic reasoning here"))
        r=route(v,factory); self.assertEqual(r["status"],"NEEDS_SEMANTIC_INTERPRETATION")
        self.assertIsNone(r["selected_route"]); factory.assert_not_called()
        self.assertEqual(route(mixed_view())["status"],"NEEDS_SEMANTIC_FALLBACK")
        v=mixed_view(); v["public"]["query"]="Need semantic alignment"
        self.assertEqual(route(v,factory)["status"],"NEEDS_SEMANTIC_INTERPRETATION")

    def test_masking_before_selection_blocks_inadmissible_high_scores(self):
        adapter=Mock(); adapter.score.return_value=receipt(); factory=Mock(return_value=adapter)
        r=route(mixed_view(),factory)
        self.assertEqual(r["status"],"SELECTED"); self.assertEqual(r["selected_route"],"CSP")
        self.assertEqual(r["neural_forward_calls"],36); factory.assert_called_once()
        self.assertEqual(set(r["project"]),{"domains","constraints"})
        self.assertEqual(set(adapter.score.call_args.args[0]),{"instruction","public"})

    def test_cost_aware_selection_requires_estimate_provenance(self):
        def choose(est,weight):
            a=Mock(); a.score.return_value=receipt(); return route(mixed_view(),lambda:a,est,weight)
        estimates={"CSP":{"ms":100,"provenance":"synthetic assumption"},
                   "ARITHMETIC":{"ms":1,"provenance":"synthetic assumption"}}
        self.assertEqual(choose(estimates,.1)["selected_route"],"ARITHMETIC")
        self.assertEqual(choose(None,.1)["status"],"REJECTED")
        estimates["CSP"]["ms"]=-1
        self.assertEqual(choose(estimates,.1)["status"],"REJECTED")

    def test_fallback_faults_retain_receipts_stop_and_do_not_execute(self):
        for fault in ("identity","audit","generation","partial","cost","nan","margin","mode","codes","numeric","prefix"):
            with self.subTest(fault=fault):
                rec=receipt()
                if fault=="identity": rec["identity"]["model_revision"]="changed"
                elif fault=="audit": rec["audit"]["unchanged"]=False
                elif fault=="generation": rec["generated_calls"]=1
                elif fault=="partial": rec["status"]="FAILED"
                elif fault=="cost": rec["ledger"]["forward_calls"]=0
                elif fault=="nan": rec["passes"][0]["matrix"][0][0]=float("nan")
                elif fault=="margin":
                    for p in rec["passes"]: p["matrix"]=[[-3.]*4 for _ in range(24)]
                elif fault=="mode": rec["passes"][0]["mode"]="unregistered"
                elif fault=="numeric": rec["passes"][1]["matrix"][0][0]-=.2
                elif fault=="prefix": rec["passes"][1]["prefixes"][0][0]=99
                else: rec["passes"][0]["code_ids"][0]=0
                a=Mock(); a.score.return_value=rec; r=route(mixed_view(),lambda:a)
                self.assertEqual(r["status"],"REJECTED"); self.assertIsNone(r["selected_route"])
                self.assertFalse(r["accounting_complete"])
        r=route(mixed_view(),Mock(side_effect=RuntimeError("load failed")))
        self.assertIsNone(r["neural_forward_calls"]); self.assertFalse(r["accounting_complete"])

    def test_execution_original_verifier_and_cross_view_projection_authority(self):
        v=math_view(); r=route(v); execute=Mock(return_value="3"); verify=Mock(return_value=True)
        self.assertTrue(execute_selected(v,r,execute,verify)["accepted"])
        self.assertEqual(execute.call_args.args,("ARITHMETIC",{"expression":"(a+b)/c","bindings":{"a":5,"b":7,"c":4}}))
        self.assertEqual(verify.call_args.args[0],v)
        verify.return_value=False; self.assertFalse(execute_selected(v,r,execute,verify)["accepted"])
        for altered in ("view","route","project"):
            rr=snapshot(r); vv=snapshot(v)
            if altered=="view": vv["public"]["bindings"]["a"]=8
            elif altered=="route": rr["selected_route"]="CSP"
            else: rr["project"]["expression"]="0"
            out=execute_selected(vv,rr,Mock(side_effect=AssertionError("must block")),verify)
            self.assertFalse(out["executed"]); self.assertFalse(out["accepted"])
        verify.return_value={"accepted":True}
        self.assertFalse(execute_selected(v,r,execute,verify)["accepted"])

    def test_execution_failure_does_not_change_route_or_count_as_pass(self):
        v=math_view(); r=route(v); verify=Mock(side_effect=AssertionError("no answer"))
        out=execute_selected(v,r,Mock(side_effect=ZeroDivisionError()),verify)
        self.assertFalse(out["accepted"]); self.assertTrue(out["executed"]); verify.assert_not_called()
        self.assertEqual(r["selected_route"],"ARITHMETIC")
        for k in ("p2_registration_admitted","p2_admitted","decision3_admitted"):
            self.assertFalse(contract()[k])


if __name__ == "__main__": unittest.main()
