"""Q3 causal type invention on unrelated finite-state vs numeric-state laws."""
import copy
import unittest

from research.q3.heterogeneous_representation_invention import (
    InventedIntegerState, infer_integer_state,
    invent_representation, HeterogeneousLanguage,
)
from research.q3.heterogeneous_type_first import (
    arithmetic_train,arithmetic_heldout,persisted_language_test,
)
from research.q3.auto_state_type_first import (
    named_machine,samples_whole_word,output_of,
)


class HeterogeneousRepresentationTests(unittest.TestCase):
    def test_new_integer_state_formula_from_complete_io(self):
        sample=arithmetic_train(lambda state,x:state+x,0,1301)
        learned,trials=infer_integer_state(sample)
        self.assertIsNotNone(learned)
        self.assertEqual(learned.initial,0)
        self.assertEqual(learned.update,["add",["prev"],["cur"]])
        self.assertEqual(learned.ast()[0],"DefineAlgebraicType")
        self.assertEqual(learned.ast()[3][0],"DefineRecursiveOperator")
        test=arithmetic_heldout(lambda state,x:state+x,0,61301)
        for word,gold in test:
            self.assertEqual(learned.apply(word),gold)

    def test_output_values_beyond_any_seen_finite_state_symbol(self):
        train=arithmetic_train(lambda p,x:p+x,0,1511)
        selected,trace=invent_representation(train)
        self.assertIsNotNone(selected)
        kind,model,cost=selected
        self.assertEqual(kind,"SymbolicIntegerState")
        seen={c for word,outs in train for c in outs}
        long_input=[1]*60
        computed=model.apply(long_input)
        self.assertEqual(computed, list(range(1,61)))
        self.assertTrue(set(computed)-seen)
        # A frozen finite-output-state machine emitting only TRAIN labels
        # cannot output a new integer absent from its transition chunks.

    def test_independent_finite_type_is_selected_without_new_finite_primitive(self):
        source=samples_whole_word(named_machine("running_mod3"),4331,2)
        selected,trace=invent_representation(source)
        self.assertIsNotNone(selected)
        kind,model,cost=selected
        self.assertEqual(kind,"FiniteVariantState")
        self.assertEqual(model.internal.num_states,3)
        self.assertEqual(model.apply([1,1,1,1]),[1,2,0,1])

    def test_signed_balance_discovers_composite_expression(self):
        source=arithmetic_train(lambda p,x:p+2*x-1,0,987)
        selected,trace=invent_representation(source)
        self.assertIsNotNone(selected)
        kind,model,cost=selected
        self.assertEqual(kind,"SymbolicIntegerState")
        self.assertIn("cur",str(model.update))
        self.assertIn("prev",str(model.update))
        test=arithmetic_heldout(lambda p,x:p+2*x-1,0,912)
        self.assertTrue(all(model.apply(x)==y for x,y in test))

    def test_numeric_output_cap_yields_safe_abstention(self):
        huge=InventedIntegerState(1,["mul",["prev"],["lit",3]])
        self.assertIsNone(huge.apply([0]*25))
        self.assertEqual(huge.apply([0,0,0]),[3,9,27])

    def test_counterexample_outside_both_languages_abstains(self):
        bad=[([0],[0]),([0,1],[1,0])]
        chosen,trace=invent_representation(bad)
        self.assertIsNone(chosen)

    def test_saved_new_types_are_immutable_and_reusable(self):
        stored,events=persisted_language_test()
        self.assertEqual([r["mode"] for r in events],
                         ["invent","reuse","invent","reuse","invent","reuse"])
        self.assertEqual(len(stored["definitions"]),3)
        self.assertTrue(all(e["original_train_exact"] for e in events))
        self.assertEqual(HeterogeneousLanguage.load(stored).dump(),stored)
        tampered=copy.deepcopy(stored)
        entry=next(iter(tampered["definitions"].values()))
        entry["ast"][1]="forged"
        with self.assertRaisesRegex(ValueError,"TAMPER"):
            HeterogeneousLanguage.load(tampered)


if __name__=="__main__":
    unittest.main()
