"""Typed macro admission never treats operator coincidence as proof."""
import unittest
from neumann1.structural_library_admission_v1 import qualify

H = "a" * 64
S = "b" * 64
M = {"dsl_id": "typed_graphics", "signature": {"inputs": ["Int", "Int"], "output": "Scene"},
     "required_operators": ["T", "M", "repeat", "tan"], "macro_sha256": H}
T = {"dsl_id": "typed_graphics", "signature": {"inputs": ["Int", "Int"], "output": "Scene"},
     "supported_operators": ["T", "M", "repeat", "tan", "C"], "source_metadata_sha256": S}


class StructureAdmissionTest(unittest.TestCase):
    def test_fully_declared_types_and_operators_admit_only_to_proof(self):
        result = qualify(M, T)
        self.assertTrue(result["admissible"])
        self.assertEqual(result["status"], "ADMITTED_REQUIRES_INDEPENDENT_PROOF")
        self.assertFalse(result["original_problem_verified"])
        self.assertEqual(result["Q3"], "OPEN")

    def test_cross_corpus_operator_vocabulary_gate_abstains(self):
        target = dict(T, supported_operators=["C", "line", "polygon"])
        result = qualify(M, target)
        self.assertEqual(result["status"], "ABSTAIN_INCOMPATIBLE_INTERFACE")
        self.assertEqual(result["missing_operator_heads"], ["M", "T", "repeat", "tan"])
        self.assertEqual(result["target_original_source_bodies_read"], 0)

    def test_matching_names_in_different_dsl_never_imply_equivalence(self):
        r = qualify(M, dict(T, dsl_id="different_primitive_semantics"))
        self.assertFalse(r["admissible"])
        self.assertIn("CROSS_DSL_WITHOUT_VERIFIED_TRANSLATOR", r["reasons"])

    def test_mismatched_type_never_executes(self):
        r = qualify(M, dict(T, signature={"inputs": ["Int", "Int"], "output": "Bool"}))
        self.assertFalse(r["admissible"])
        self.assertIn("TYPE_SIGNATURE_MISMATCH", r["reasons"])

    def test_missing_metadata_or_duplicate_operators_fails_closed(self):
        variants = [
            (M, dict(T, supported_operators=[])),
            (M, dict(T, supported_operators=["T", "T"])),
            (dict(M, macro_sha256="not a hash"), T),
            (M, dict(T, signature={"input": ["Int"]})),
            (dict(M, original_answer="leak"), T),
        ]
        for macro, target in variants:
            with self.subTest(macro=macro, target=target):
                with self.assertRaises(ValueError):
                    qualify(macro, target)


if __name__ == "__main__":
    unittest.main()
