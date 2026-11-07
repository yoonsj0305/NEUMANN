"""Test semantic role binding without any original external source bodies."""
import unittest

from research.q3.auto_copy_chain_semantic_role_postfirst import (
    recover_limit_roles, generated_semantic_body
)

class SemanticRoleRepairTest(unittest.TestCase):
    def static_source(self, corrupt=False):
        specs=[
          ("bb15.i",["R","S","I","D","V","F","X","Y","Z","A1","B1"],"Z","I"),
          ("bb32.i",["N","O","P","Q","G","S","D","U","V","W"],"V","G"),
          ("bb46.i",["N","O","P","Q","G","S","D","U"],"U","G"),
          ("bb60.i",["N","O","P","Q","I","S"],"S","I"),
        ]
        blocks=[]
        for j,(name,args,bound,cursor) in enumerate(specs):
            guard=f"(not (= (<= {bound} {cursor}) B))"
            if corrupt and j==1:
                guard="true"
            call="(main@"+name+" "+" ".join(args)+")"
            blocks.append("(assert (forall ((B Bool)) (=> (and "+call+
                          " "+guard+") "+call+")))")
        return "\n".join(blocks)

    def test_role_recovery_uses_semantic_guard_not_adjacent_int_type(self):
        stage_names=["bb15.i","bb32.i","bb46.i","bb60.i"]
        roles=recover_limit_roles(self.static_source(),stage_names)
        self.assertEqual([roles[x]["bound_argument"] for x in stage_names],
                         [8,8,7,5])
        self.assertEqual([roles[x]["cursor_argument"] for x in stage_names],
                         [2,4,4,4])

    def test_copy3_intermediate_uses_correct_bound_and_future_base(self):
        rhs=generated_semantic_body(1,4,8)
        self.assertIn("(> x7 0)",rhs)
        self.assertIn("(<= x4 x8)",rhs)
        self.assertIn("(COPY_PREFIX x1 x0 x3 x2 x8)",rhs)
        self.assertNotIn("(COPY_PREFIX x1 x0 x3 x2 x7)",rhs)

    def test_missing_semantic_role_is_unknown_not_guess(self):
        with self.assertRaisesRegex(ValueError,"NO_UNIQUE_SEMANTIC_LOOP_LIMIT"):
            recover_limit_roles(self.static_source(corrupt=True),
                                ["bb15.i","bb32.i","bb46.i","bb60.i"])

    def test_old_inferred_wrong_copy3_limit_differs(self):
        from research.q3.auto_copy_chain_chc import generated_body
        original=generated_body(1,4,False)
        repaired=generated_semantic_body(1,4,8)
        self.assertNotEqual(original,repaired)
        self.assertIn("(COPY_PREFIX x1 x0 x3 x2 x7)",original)
        self.assertIn("(COPY_PREFIX x1 x0 x3 x2 x8)",repaired)

    def test_wrong_relation_still_caught_at_first_copy(self):
        right=generated_semantic_body(1,4,8,True)
        self.assertIn("COPY_PREFIX_WRONG x6 x5 x3 x2 x4",right)

if __name__=="__main__":
    unittest.main()
