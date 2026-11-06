"""Source-free safety controls; no proof outcome is faked by these tests."""
import unittest

from research.q3.counterexample_representation_grower import (
    MANIFEST, public_features, task_from, expr_term, relation, witness_script,
    obligation, count_source_reads, learn, score
)


X=["select","S",["add",["var","b"],["var","i"]]]
T={"expr":["add",X,["const",3]],"db":9,"sb":-7}
C={"expr":["const",7],"db":0,"sb":0}


class CounterexampleRepresentationTests(unittest.TestCase):
    def test_all_human_H1_answers_absent_from_train_record(self):
        import json
        meta=json.loads(MANIFEST.read_text())
        self.assertEqual(meta["actual_run"],"NOT_RUN")
        self.assertEqual(len(meta["train"]["examples"]),6)
        self.assertEqual(len(meta["heldout"]["examples"]),8)
        self.assertEqual(meta["train"]["label_source"],"INDEPENDENT_Z3_SAT_COLLISION_BOOLEAN_ONLY")
        self.assertEqual(meta["Q3"],"OPEN")

    def test_typed_lift_uses_new_bound_index_not_training_string(self):
        lifted=relation(task_from(T))
        self.assertIn("(forall ((j Int))",lifted)
        self.assertIn("(select S (+ b j))",lifted)
        self.assertIn("(select D (+ a j))",lifted)
        self.assertNotIn("COPY_PREFIX",lifted)
        self.assertEqual(count_source_reads(T["expr"]),1)
        self.assertEqual(count_source_reads(C["expr"]),0)

    def test_collision_holds_destination_fixed(self):
        script=witness_script(task_from(T))
        self.assertIn("(select D a)",script)
        self.assertIn("(select S0 b)",script)
        self.assertIn("(select S1 b)",script)
        self.assertIn("(check-sat)",script)

    def test_z3_required_checks_include_nonvacuity_and_real_mutation(self):
        init=obligation(task_from(T),"INIT")
        step=obligation(task_from(T),"STEP")
        wrong=obligation(task_from(T),"WRONG_STORE")
        live=obligation(task_from(T),"NONVACUITY")
        self.assertIn("(not (NewRel S D a b 0))",init)
        self.assertIn("(store D (+ a i)",step)
        self.assertIn("(+ (+ (select S (+ b i)) 3) 1)",wrong)
        self.assertIn("(assert (NewRel S D a b 1))",live)
        with self.assertRaises(ValueError):
            obligation(task_from(T),"UNSUPPORTED")

    def test_invalid_types_and_unregistered_operators_rejected(self):
        for bad in (
            {"expr":["select","D",["var","i"]],"db":0,"sb":0},
            {"expr":["fancy","S"],"db":0,"sb":0},
            {"expr":["mul",X,X],"db":0,"sb":0},
            {"expr":["const",True],"db":0,"sb":0},
            {"expr":X,"db":0,"sb":0,"answer":True},
            {"expr":X,"db":0.0,"sb":0}
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    task_from(bad)

    def test_learned_policy_nonzero_without_h1_program_labels(self):
        cases=[T,C]
        learned=learn(cases,[True,False],0.2,250)
        self.assertTrue(any(abs(v)>0.01 for v in learned))
        self.assertGreater(score(learned,T["expr"]),0)
        self.assertLess(score(learned,C["expr"]),0)
        self.assertEqual(score((0,0,0),T["expr"]),0)


if __name__=="__main__":
    unittest.main()
