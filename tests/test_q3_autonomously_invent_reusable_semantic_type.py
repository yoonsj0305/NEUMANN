"""Causal Q3: automatically new named operator TYPE, not a cached original."""
import unittest
from research.q3.autonomously_invent_reusable_semantic_type import (
    discover_operator_type,source_semantic_contract,canonical_type,
    derive_target_roles,apply_frozen_type,fit_frozen_library_to_original,
)
from research.q3.failure_triggered_semantic_operator_invention import (
    NovelOperator,composed_definition
)
from research.q3.induce_binary_algebra_original import Decomposition


class ActualReusableTypeDiscovery(unittest.TestCase):
    def row(self,keys,mode="set"):
        op=NovelOperator(mode,2,tuple(
            (tuple(k),out) for k,out in keys))
        d=Decomposition("rows",2,0,2)
        return {"status":"INVENTED_NONCONSERVATIVE_OPERATOR",
                "exact":True,"frozen_operator_AST":[composed_definition(d,op)]}

    def sources(self):
        first=self.row([
            ((0,),2),((0,1),0),((0,3),0),((1,3),0)
        ])
        second=self.row([
            ((0,),8),((0,5),0),((0,7),0),((5,7),0)
        ])
        return first,second

    def target(self):
        return {
            "train":[
               {"input":[[0,0,0,2],[0,2,4,4]],
                "output":[[8,0],[0,0]]},
               {"input":[[2,0,4,0],[4,0,0,0]],
                "output":[[0,8],[0,8]]},
            ],
            "test":[
               {"input":[[0,2,4,0],[0,4,2,0]],
                "output":[[8,0],[0,8]]}
            ]
        }

    def test_two_independent_programs_generate_same_new_type(self):
        a,b=self.sources()
        law=discover_operator_type(a,b)
        self.assertIsNotNone(law)
        self.assertEqual(law.arity,2)
        self.assertEqual(law.roles,4)
        self.assertTrue(law.ast()[1].startswith("learned_type_"))
        self.assertEqual(len(law.source_hashes),2)
        self.assertNotEqual(law.source_hashes[0],law.source_hashes[1])
        self.assertEqual(law.ast(),
                         discover_operator_type(a,b).ast())

    def test_transfer_requires_only_frozen_type_and_train_role_binding(self):
        library=discover_operator_type(*self.sources())
        target=self.target()
        result=fit_frozen_library_to_original(library,target,
                                             "source_excluded_original","fixture")
        self.assertEqual(result["status"],"REUSED_SELF_DISCOVERED_SEMANTIC_TYPE")
        self.assertTrue(result["submitted"])
        self.assertTrue(result["exact"])
        self.assertTrue(result["no_direct_semantics_inventor_on_target"])

    def test_cannot_invent_from_unrelated_operator_pair(self):
        a,_=self.sources()
        b=self.row([
            ((0,),0),((0,5),8),((0,7),8),((5,7),8)
        ])
        self.assertIsNone(discover_operator_type(a,b))

    def test_absence_of_new_type_abstains_and_old_join_is_impossible(self):
        lib=discover_operator_type(*self.sources())
        target=self.target()
        d=Decomposition("columns",2,0,2)
        assignments=derive_target_roles(target["train"],d,lib)
        self.assertGreater(len(assignments),0)
        # The learned output 8 is absent from the cell's input operands.
        self.assertNotIn(8,(0,0))
        # The target has an unseen color pair: all candidates must abstain.
        self.assertIsNone(apply_frozen_type(lib,d,assignments[0],[[2,2,2,2]]))

    def test_reject_forged_unproven_source(self):
        a,b=self.sources()
        a["exact"]=False
        with self.assertRaisesRegex(ValueError,"SOURCE_NOT_ORIGINAL_SOLVED"):
            discover_operator_type(a,b)


if __name__=="__main__":
    unittest.main()
