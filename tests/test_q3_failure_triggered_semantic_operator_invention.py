"""Q3 semantic type change, real compiler, and fail-closed unknown controls."""
import unittest

from research.q3.failure_triggered_semantic_operator_invention import (
    infer_new_observation_type,NovelOperator,learn_new_semantic_operator,
    execute,propose,study,
)
from research.q3.induce_binary_algebra_original import Decomposition


class Q3NovelSemanticFamily(unittest.TestCase):
    def example_data(self):
        # Two panels of length 2; no output rule or target program is supplied
        # to the inference code. Its new output 8/9 is absent from operands.
        return [
            {"input":[[1,3,2,4],[1,3,2,4]],
             "output":[[8,9],[8,9]]},
            {"input":[[3,1,4,2],[3,1,4,2]],
             "output":[[9,8],[9,8]]},
        ]

    def test_external_like_nonconservative_operator_is_created(self):
        train=self.example_data()
        d=Decomposition("columns",2,0,2)
        learned=learn_new_semantic_operator(train,d)
        self.assertIsNotNone(learned)
        op,trace,witnesses=learned
        self.assertEqual(op.mode,"set")
        self.assertTrue(op.definition()[1].startswith("neumann_invented_"))
        self.assertGreater(len(witnesses),2)
        for case in train:
            self.assertEqual(execute(d,op,case["input"]),case["output"])

    def test_refines_type_when_commutative_semantics_conflict(self):
        data=[((1,2),8,0,0,0),
              ((2,1),7,1,0,0),
              ((3,4),9,0,0,1),
              ((4,3),5,1,0,1)]
        mode,table,trace=infer_new_observation_type(data)
        self.assertEqual(mode,"ordered")
        self.assertGreater(trace[0]["conflicts"],0)
        self.assertGreater(trace[1]["conflicts"],0)
        self.assertEqual(trace[2]["conflicts"],0)
        op=NovelOperator(mode,2,tuple(sorted(table.items())))
        self.assertEqual(op.compile()((1,2)),8)
        self.assertEqual(op.compile()((2,1)),7)

    def test_known_signature_reuse_and_unknown_abstention(self):
        d=Decomposition("columns",2,0,2)
        op=learn_new_semantic_operator(self.example_data(),d)[0]
        self.assertEqual(execute(d,op,[[3,1,4,2]]),[[9,8]])
        self.assertIsNone(execute(d,op,[[5,5,6,6]]))

    def test_old_conservative_join_cannot_emulate_new_output(self):
        d=Decomposition("columns",2,0,2)
        train=self.example_data()
        op=learn_new_semantic_operator(train,d)[0]
        self.assertEqual(op.compile()((1,2)),8)
        self.assertNotIn(8,(1,2))
        # Generic old algebra always chooses an existing operand or abstains.
        from research.q3.induce_binary_algebra_original import InventedJoin
        old=InventedJoin(0,((1,2),), (0,1,2))
        self.assertIn(old.compile()(1,2),(1,2,None))

    def test_unlearnable_contradiction_does_not_fabricate_operator(self):
        # Same complete input requires two different outputs.
        train=[
            {"input":[[1,3,2,4]],"output":[[8,9]]},
            {"input":[[1,3,2,4]],"output":[[9,8]]}
        ]
        self.assertEqual(propose(train),[])


if __name__=="__main__":
    unittest.main()
