"""CEGIS structural discovery, no named palindrome solution in inventor."""
import itertools
import unittest
from research.q3.discover_index_relation_constructor import (
    discover,run_new_representation,coeffs,generated_coordinates,
)

class GenericRelationInventionTests(unittest.TestCase):
    def test_source_io_discovers_new_coordinate_relation_and_exhaustive_binary_checks(self):
        source=[
            ([""],True),(["aba"],True),(["aaaaa"],True),
            (["zbcd"],False),(["xywyx"],True)
        ]
        result=discover(source)
        self.assertEqual(result["status"],"INVENTED_EXECUTABLE_RELATION")
        p=result["program"]
        self.assertIn("second_index",p["representation_constructor"])
        self.assertEqual(result["coordinate_affine_coefficients"],(-1,1,-1))
        self.assertEqual(p["relation"],{"compare":"eq","reduce":"all"})
        self.assertLess(result["attempts"],1200)
        for n in range(9):
            for bits in itertools.product("ab",repeat=n):
                s="".join(bits)
                self.assertEqual(run_new_representation(p,[s]),
                                 s==s[::-1],(s,p))

    def test_same_program_structure_transfers_to_new_sequence_type(self):
        source=[
            ([[]],True),([[1,2,1]],True),([[1,2,2,1]],True),
            ([[2,5]],False),([[1,2,3,1]],False)
        ]
        learned=discover(source)
        self.assertEqual(learned["status"],"INVENTED_EXECUTABLE_RELATION")
        p=learned["program"]
        self.assertEqual(run_new_representation(p,[(10,11,10)]),True)
        self.assertEqual(run_new_representation(p,[(10,11,12)]),False)

    def test_no_source_evidence_fails_closed(self):
        self.assertEqual(discover([
            (["abc"],True),(["xyz"],True),
            (["123"],True),([""],True)])["status"],
            "ABSTAIN_NO_POSITIVE_NEGATIVE")
        self.assertEqual(discover([
            (["ab"],False),(["xy"],False),
            (["zy"],False),(["gh"],False)])["status"],
            "ABSTAIN_NO_POSITIVE_NEGATIVE")
        self.assertEqual(discover([
            (["abc"],True),(["ab"],False)])["status"],
            "ABSTAIN_INSUFFICIENT_SOURCE")

    def test_no_script_eval_or_named_domain_primitive(self):
        self.assertIsNone(run_new_representation(
            {"kind":"execute_arbitrary_shell","representation_constructor":{},
             "relation":{}},["aba"]))
        candidates=generated_coordinates()
        self.assertGreater(len(candidates),20)
        self.assertTrue(all("palindrome" not in str(x) and
                            "reverse" not in str(x) for x in candidates))

if __name__=="__main__":
    unittest.main()
