"""Source-only counterexample-driven grammar tests; no new MBPP original read."""
import unittest
from research.q3.feature_predicate_from_counterexample import (
    classify,infer_predicate,pred_value,generate_fold_from_learned_constructor,
    run_generated,
)
from research.q3.reflexive_constructor_from_experience import fit_sources,construct,execute_safe


def exp(identifier,removed,pairs):
    return {"id":identifier,
            "verified_program":{
                "kind":"DerivedSequenceFilter","removed":removed,
                "source_arg":0},
            "train_io":[([x],y) for x,y in pairs]}

SOURCE=[
  exp(834,["!"],[("a!b","ab"),("c!d!","cd"),
                 ("f!g!h","fgh")]),
  exp(841,[" "],[("a b","ab"),("alpha beta","alphabeta"),
                  ("  t  ","t")]),
]

class FeaturePredicateInventionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen,_=fit_sources(SOURCE)

    def test_data_induces_parity_predicate_unseen_ints(self):
        train=[([[1,2,3]],[2]),([[2,4,6]],[2,4,6])]
        predicate,n,_=infer_predicate(train)
        self.assertEqual(predicate,["mod_equals",2,1])
        new,attempts,trace=generate_fold_from_learned_constructor(
            self.frozen,train)
        self.assertEqual(new["predicate"],predicate)
        self.assertEqual(run_generated(new,[[9,10,11,12]]),[10,12])
        literal=construct(self.frozen,train)
        self.assertNotEqual(execute_safe(literal,[[9,10,11,12]])[1],[10,12])

    def test_data_induces_even_dropping(self):
        train=[([[1,2,3,4,5,6]],[1,3,5]),
               ([[10,20,45,67,84,93]],[45,67,93])]
        new,_,_=generate_fold_from_learned_constructor(self.frozen,train)
        self.assertIsNotNone(new)
        self.assertEqual(new["predicate"],["mod_equals",2,0])
        self.assertEqual(run_generated(new,[[11,12,13,14]]),[11,13])

    def test_unicode_space_predicate_generalizes_new_characters(self):
        train=[([" a b "],"ab"),([" one two "],"onetwo")]
        new,n,trace=generate_fold_from_learned_constructor(self.frozen,train)
        self.assertEqual(new["predicate"],["unicode_class","space"])
        self.assertEqual(run_generated(new,["x\ty\nz"]),"xyz")

    def test_unicode_digit_predicate_not_hardcoded_digit_list(self):
        train=[(["a1b2"],"ab"),(["9z0"],"z")]
        new,_,_=generate_fold_from_learned_constructor(self.frozen,train)
        self.assertEqual(new["predicate"],["unicode_class","digit"])
        self.assertEqual(run_generated(new,["a۴b٣c"]),"abc")

    def test_new_types_use_same_persisted_constructor(self):
        train=[([(1,0,2,0)],(1,2)),
               ([(4,0,5)],(4,5))]
        new,_,_=generate_fold_from_learned_constructor(self.frozen,train)
        self.assertIsNotNone(new)
        self.assertEqual(run_generated(new,[(7,0,8,0)]),(7,8))
        self.assertEqual(new["source_constructor"],self.frozen["symbol"])

    def test_refuse_noncausal_or_contradictory_training(self):
        self.assertIsNone(classify([(["ab"],"ba")]))
        self.assertIsNone(classify([([[1,1]],[1])]))
        self.assertIsNone(classify([([[1,2]],[2]),([[1]],[1])]))
        self.assertIsNone(generate_fold_from_learned_constructor(
            self.frozen,[(["abc"],"cba")])[0])
        self.assertIsNone(generate_fold_from_learned_constructor(
            self.frozen,[([object()],3)])[0])

if __name__=="__main__":
    unittest.main()
