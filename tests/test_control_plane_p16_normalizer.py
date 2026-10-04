"""Prospective finite surface and original-obligation candidate controls."""
from fractions import Fraction
import unittest

from neumann1.control_plane_p15 import parse_sketch as p15_strict_parser
from neumann1.control_plane_p16 import (
    normalize_hypothesis, parse_sketch, compile_sketch, contract,
    FrozenHypothesisCompiler, interpret_and_execute, semantic_prompt,
)
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from test_control_plane_p16 import FakeCore


def candidate(raw,private):
    view={"instruction":"Return a complete assignment satisfying the original query.",
          "public":{"query":"Choose M, N, O from {1,2,3,4}. M=3, N<M, O=N."}}
    ref={"task_id":"synthetic","family":"constraint_planning","private":private}
    r=interpret_and_execute(view,FrozenHypothesisCompiler(FakeCore(raw)),_executor,_hidden_verifier(ref))
    return r


ORIGINAL={"domains":{"M":[1,2,3,4],"N":[1,2,3,4],"O":[1,2,3,4]},
          "constraints":[["eq","M",3],["lt","N","M"],["eq","O","N"]]}


class NormalizationContracts(unittest.TestCase):
    def test_equivalent_surface_classes_have_identical_ir(self):
        expected={"route":"CSP","atoms":[["DOMAIN","A","0","1","2"],["DOMAIN","B","0","1","2"],["LT","A","B"]]}
        for domains in ("DOMAIN A 0 1 2\nDOMAIN B 0 1 2","A 0 1 2\nB 0 1 2",
                        "A {0,1,2}\nB {0, 1, 2}","DOMAIN A {0,1,2}\nDOMAIN B {0,1,2}",
                        "domain\tA\t0 1 2\ndomain\tB\t0 1 2"):
            for relation in ("LT A B","A LT B","A lt B","A < B","A<B"):
                with self.subTest(domains=domains,relation=relation):
                    n=normalize_hypothesis("CSP\n"+domains+"\n"+relation+"\nEND")
                    self.assertEqual(n["sketch"],expected)
                    self.assertEqual(compile_sketch(n["sketch"])["public"],
                                     {"domains":{"A":[0,1,2],"B":[0,1,2]},"constraints":[["lt","A","B"]]})
                    self.assertFalse(n["source_obligation_consulted"])
                    self.assertFalse(n["semantic_choices_added"])

    def test_symbols_words_and_operand_order_preserved(self):
        for surface,op in (("A <= B","LE"),("A≤B","LE"),("A!=B","NE"),("A ≠ B","NE"),
                           ("A = B","EQ"),("A==B","EQ"),("eq A B","EQ"),("A ne B","NE")):
            with self.subTest(surface=surface):
                n=normalize_hypothesis("CSP\nA -2 -1 0\nB -2 -1 0\n"+surface+"\nEND")
                self.assertEqual(n["sketch"]["atoms"][-1],[op,"A","B"])

    def test_wrappers_and_whitespace_are_surface_only(self):
        base="CSP\nA {0,1}\nB {0,1}\nA != B\nEND"
        fence=chr(96)*3
        for raw in (base.replace("\n","\r\n"),fence+"\n"+base+"\n"+fence,
                    fence+"text\n"+base+"\n"+fence,fence+"csp\n"+base+"\n"+fence,
                    "<|channel>final\n"+base+"<|end|>"):
            self.assertEqual(parse_sketch(raw),parse_sketch(base))

    def test_ambiguous_or_unsupported_text_is_not_guessed(self):
        for body in ("A 0,1\nB 0 1\nA < B","A {0,1,}\nB 0 1\nA < B",
                     "A 0 1\nB 0 1\nA < B < 2","A 0 1\nB 0 1\nA > B",
                     "A 0.5 1\nB 0 1\nA < B","LT 0 1\nA 0 1\nLT EQ A",
                     "A 0 1\nB 0 1\nA != B\n# explanation",
                     "A 0 1\nEQ A 1\nB 0 1"):
            with self.subTest(body=body),self.assertRaises(ValueError):
                compile_sketch(parse_sketch("CSP\n"+body+"\nEND"))

    def test_normalizer_has_no_original_query_or_reference_input(self):
        raw="CSP\nM 3\nN 1\nO 1\nLT N M\nEQ O N\nEND"
        with self.assertRaises(TypeError): normalize_hypothesis(raw,ORIGINAL)
        n=normalize_hypothesis(raw)
        self.assertFalse(n["candidate_subset_proved"])
        self.assertFalse(n["original_solution_set_equivalence_proved"])

    def test_valid_narrowed_candidate_is_accepted_by_complete_original_obligation(self):
        raw="CSP\nM 3\nN 1\nO 1\nLT N M\nEQ O N\nEND"
        r=candidate(raw,ORIGINAL)
        self.assertTrue(r["accepted"])
        self.assertEqual(r["execution"]["answer"],{"M":3,"N":1,"O":1})
        self.assertEqual(r["tool_calls"],1); self.assertEqual(r["verifier_calls"],1)
        self.assertFalse(r["normalization"]["candidate_subset_proved"])
        # Full original also permits N=2,O=2; compilation makes no equality claim.
        self.assertTrue(_hidden_verifier({"task_id":"other","family":"constraint_planning","private":ORIGINAL})(
            {},{"M":3,"N":2,"O":2}))

    def test_invalid_narrowing_is_rejected_not_repaired(self):
        for raw in ("CSP\nM 4\nN 1\nO 1\nLT N M\nEQ O N\nEND",
                    "CSP\nM 3\nN 3\nO 3\nEQ O N\nEND"):
            r=candidate(raw,ORIGINAL)
            self.assertFalse(r["accepted"]); self.assertTrue(r["accounting_complete"])
            self.assertEqual(r["status"],"REJECTED_BY_ORIGINAL_VERIFIER")
            self.assertEqual(r["model_calls"],1); self.assertEqual(r["verifier_calls"],1)

    def test_relaxed_candidate_does_not_replace_original_relations(self):
        raw="CSP\nM 3\nN 1\nO 2\nEQ M 3\nEND"
        r=candidate(raw,ORIGINAL)
        self.assertFalse(r["accepted"]); self.assertEqual(r["execution"]["answer"]["O"],2)
        self.assertEqual(r["proposal"]["public"]["constraints"],[["eq","M",3]])

    def test_missing_variable_is_not_restored_from_original_query(self):
        r=candidate("CSP\nM 3\nEQ M 3\nEND",ORIGINAL)
        self.assertFalse(r["accepted"]); self.assertEqual(set(r["execution"]["answer"]),{"M"})
        self.assertEqual(set(r["proposal"]["public"]["domains"]),{"M"})

    def test_duplicate_domains_or_undeclared_names_stop_before_executor(self):
        for raw in ("CSP\nM 1 2\nM 1\nEQ M 1\nEND","CSP\nM 1 2\nEQ M Z\nEND"):
            r=candidate(raw,ORIGINAL)
            self.assertFalse(r["accepted"]); self.assertFalse(r["executed"])
            self.assertTrue(r["accounting_complete"]); self.assertEqual(r["tool_calls"],0)
            self.assertIsNotNone(r["normalization_ms"])

    def test_historical_p15_strict_wire_still_rejects_opened_examples(self):
        opened=("CSP\nM 3\nN 1\nO 1\nLT N M\nEQ O N\nEND",
                "CSP\nI 0 1 2\nJ 2\nK 0 1 2\nL 0 1 2\nI NE K\nJ EQ 2\nK EQ L\nI LT J\nEND",
                "CSP\nS {-2, -1, 0, 1}\nT {-1}\nS <= T\nS != T\nEND",
                "CSP\nP {0,1,2,3}\nQ {0,1,2,3}\nR {0,1,2,3}\nR = 2\nP != 2\nQ <= 2\nP = Q\nEND")
        for raw in opened:
            with self.assertRaises(ValueError): p15_strict_parser(raw)
            compile_sketch(parse_sketch(raw))
        self.assertFalse(contract()["p15_result_rescued"])

    def test_new_prompt_prospectively_allows_candidate_narrowing_without_claiming_verification(self):
        view={"instruction":"Complete assignment.","public":{"query":"Choose X from {0,1}."}}
        prompt=semantic_prompt(view)
        self.assertIn("may narrow domains",prompt)
        self.assertIn("Do not claim that a guessed candidate is verified",prompt)
        self.assertFalse(contract()["p2_registration_admitted"])
        self.assertFalse(contract()["decision3_admitted"])


if __name__ == "__main__": unittest.main()
