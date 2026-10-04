"""P1.4 semantic-interpretation contracts; synthetic only, no model weights."""
import json
import math
import unittest

from neumann1.control_plane_p1_contract import MODEL
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, PERMUTATIONS, CodePlan, plan_cost
from neumann1.control_plane_p14 import (
    contract, interpret_and_execute, parse_proposal, run_mixed_and_execute, semantic_prompt,
)


class FakeCompiler:
    def __init__(self, proposal):
        self.proposal = proposal
        self.calls = 0

    def propose(self, view, remaining_ms):
        self.calls += 1
        return {
            "proposal": self.proposal,
            "raw_sha256": "synthetic",
            "input_tokens": 10,
            "output_tokens": 5,
            "generation_ms": 1.0,
            "deadline_reached": False,
            "peak_accelerator_memory_bytes": 123,
            "core_sha256": "synthetic",
            "complete_ms": 1.0,
        }


def _matrix(winner_route):
    route_index = ("DIRECT", "ARITHMETIC", "CSP", "PYTHON").index(winner_route)
    utilities = [0.0, 0.0, 0.0, 0.0]
    utilities[route_index] = 8.0
    rows = []
    for p in PERMUTATIONS:
        logits = [utilities[p.index(c)] for c in range(4)]
        maximum = max(logits)
        normalizer = maximum + math.log(sum(math.exp(v-maximum) for v in logits))
        rows.append([v-normalizer for v in logits])
    return rows


class FakeFallback:
    def __init__(self, winner):
        self.winner = winner

    def score(self, view, remaining_ms):
        matrix = _matrix(self.winner)
        prefixes = tuple((101, 102, i) for i in range(24))
        ledger = {k: 0 for k in ("input_rows","score_rows","scored_tokens","evaluated_tokens","padded_tokens","forward_calls")}
        passes = []
        for mode,size,order in (
            ("batch4",4,list(range(24))),
            ("unbatched1",1,list(range(24))),
            ("reverse_batch4",4,list(reversed(range(24)))),
        ):
            ordered_prefixes = [list(prefixes[i]) for i in order]
            plan = CodePlan(tuple(tuple(x) for x in ordered_prefixes), CODE_TOKEN_IDS)
            cost = plan_cost(plan,size)
            for k,v in cost.items():
                ledger[k] += v
            # route() expects canonical matrix order even when the execution order reverses.
            passes.append({
                "mode":mode,"status":"COMPLETE","order":order,"batch_size":size,
                "prefixes":ordered_prefixes,"code_ids":list(CODE_TOKEN_IDS),
                "planned":cost,"actual":cost,"matrix":matrix,
                "peak_accelerator_memory_bytes":1234,
            })
        return {
            "status":"COMPLETE",
            "passes":passes,
            "identity":dict(MODEL),
            "ledger":ledger,
            "generated_calls":0,
            "audit":{"unchanged":True},
        }


class SemanticContracts(unittest.TestCase):
    def test_strict_proposal_parser(self):
        a = parse_proposal('{"route":"ARITHMETIC","expression":"a+b","bindings":{"a":1,"b":2}}')
        self.assertEqual(a["route"], "ARITHMETIC")
        c = parse_proposal('{"route":"CSP","domains":{"A":[0,1]},"constraints":[["eq","A",1]]}')
        self.assertEqual(c["route"], "CSP")
        self.assertEqual(parse_proposal('{"route":"ABSTAIN"}'), {"route":"ABSTAIN"})
        for bad in (
            '{"route":"DIRECT"}',
            '{"route":"ABSTAIN","answer":3}',
            '{"route":"ARITHMETIC","expression":"1+1","bindings":{},"answer":2}',
        ):
            with self.assertRaises(ValueError):
                parse_proposal(bad)

    def test_raw_semantic_compilation_reenters_p13_then_original_verifier(self):
        view = {"instruction":"Return the exact rational value.",
                "public":{"query":"Add 2 and 3."}}
        compiler = FakeCompiler({"route":"ARITHMETIC","public":{"expression":"a+b","bindings":{"a":2,"b":3}}})
        def executor(route, project):
            self.assertEqual(route, "ARITHMETIC")
            self.assertEqual(project["expression"], "a+b")
            return "5"
        result = interpret_and_execute(view, compiler, executor, lambda original, answer: answer == "5")
        self.assertTrue(result["accepted"])
        self.assertTrue(result["executed"])
        self.assertEqual(result["selected_route"], "ARITHMETIC")
        self.assertEqual(result["model_calls"], 1)
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(compiler.calls, 1)

    def test_wrong_but_well_typed_proposal_is_not_authority_and_no_retry(self):
        view = {"instruction":"Return the exact rational value.",
                "public":{"query":"Add 2 and 3."}}
        compiler = FakeCompiler({"route":"ARITHMETIC","public":{"expression":"a-b","bindings":{"a":2,"b":3}}})
        result = interpret_and_execute(view, compiler, lambda route, project: "-1",
                                       lambda original, answer: False)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "REJECTED_BY_ORIGINAL_VERIFIER")
        self.assertEqual(compiler.calls, 1)

    def test_abstention_is_safe_and_does_not_execute(self):
        view = {"instruction":"Interpret if safe.","public":{"query":"An unsupported vague request."}}
        compiler = FakeCompiler({"route":"ABSTAIN"})
        result = interpret_and_execute(
            view, compiler,
            lambda *args: self.fail("executor must not run"),
            lambda *args: self.fail("verifier must not run"),
        )
        self.assertEqual(result["status"], "ABSTAINED")
        self.assertFalse(result["executed"])
        self.assertEqual(result["tool_calls"], 0)

    def test_semantic_compiler_cannot_bypass_existing_typed_contract(self):
        typed = {"instruction":"Return exact.","public":{"expression":"a+b","bindings":{"a":1,"b":2}}}
        with self.assertRaises(ValueError):
            semantic_prompt(typed)

    def test_mixed_path_uses_masked_full_s4_then_original_verifier(self):
        view = {
            "instruction":"Return the exact rational value; constraints are unrelated.",
            "public":{
                "expression":"(a*b-c)/(d+e)","bindings":{"a":9,"b":7,"c":3,"d":5,"e":5},
                "domains":{"X":[0,1],"Y":[0,1]},"constraints":[["ne","X","Y"]],
            },
        }
        result = run_mixed_and_execute(
            view,
            fallback_factory=lambda: FakeFallback("ARITHMETIC"),
            executor=lambda route, project: "6",
            original_verifier=lambda original, answer: answer == "6",
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["selected_route"], "ARITHMETIC")
        self.assertEqual(result["routing"]["fallback_calls"], 1)
        self.assertEqual(result["routing"]["generated_calls"], 0)

    def test_boundaries_stay_closed(self):
        c = contract()
        self.assertFalse(c["p2_registration_admitted"])
        self.assertFalse(c["p2_admitted"])
        self.assertFalse(c["decision3_admitted"])
        self.assertEqual(c["coding_semantic_synthesis"], "OUT_OF_SCOPE")


if __name__ == "__main__":
    unittest.main()
