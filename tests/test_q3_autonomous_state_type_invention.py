"""Q3 generative type invention: actual programs, causality, safety and reuse."""
import copy
import random
import unittest

from research.q3.autonomous_state_type_invention import (
    NotRepresentable,learn_new_type,learn_from_complete_io,
    elementwise_impossibility_witness,SelfExtendingLanguage,
)
from research.q3.auto_state_type_first import (
    named_machine,output_of,samples_whole_word,samples_prefix_observed,
    study_registry,random_machine,
)


class SelfExtendingTypeTests(unittest.TestCase):
    def case(self,name,seed=99,alphabet=2):
        return samples_whole_word(named_machine(name),seed,alphabet)

    def test_induces_two_state_type_without_handwritten_transition(self):
        sample=self.case("running_parity")
        model,attempts=learn_from_complete_io(sample)
        self.assertEqual(model.internal.num_states,2)
        self.assertEqual(len(model.internal.transitions),4)
        self.assertEqual(model.to_ast()[0],"DefineSubsequentialOperator")
        self.assertEqual(model.internal.to_ast()[0],"DefineAlgebraicType")
        for x,y in sample:self.assertEqual(model.apply(x),y)
        self.assertEqual(model.apply([1,0,1,1]),[1,1,0,1])
        self.assertIsNone(model.apply([0,2]))

    def test_invents_other_cardinality_without_source_type(self):
        model,_=learn_from_complete_io(self.case("running_mod3"))
        self.assertEqual(model.internal.num_states,3)
        self.assertEqual(len(model.internal.transitions),6)
        self.assertEqual(model.apply([1,1,1,1]),[1,2,0,1])

    def test_previous_elementwise_language_cannot_represent_source(self):
        examples=self.case("running_parity")
        witness=elementwise_impossibility_witness(examples)
        self.assertGreater(witness["same_symbol_different_outputs"],0)
        self.assertTrue(witness["old_elementwise_map_impossible"])
        # Formal order-dependence witness: f(permuted(x)) != permuted(f(x)).
        a=[1,0];b=[0,1]
        machine=named_machine("running_parity")
        self.assertNotEqual(output_of(machine,b),
                            list(reversed(output_of(machine,a))))

    def test_variable_length_output_needs_no_known_state_count(self):
        for name in ("delete_consecutive_duplicates","duplicate_ones"):
            examples=samples_prefix_observed(named_machine(name),100,2)
            model,_=learn_new_type(examples)
            self.assertTrue(all(model.apply(x)==y for x,y in examples))
        expanded=samples_prefix_observed(named_machine("duplicate_ones"),100,2)
        self.assertTrue(elementwise_impossibility_witness(expanded)
                        ["old_elementwise_map_impossible"])

    def test_unknown_language_abstains_on_noncausal_io(self):
        # Two complete I/O examples force contradictory prefix emissions.
        pairs=[([0],[0]),([0,1],[1,0])]
        with self.assertRaises(NotRepresentable):
            learn_from_complete_io(pairs)

    def test_unsafe_registry_mutation_rejected(self):
        registry=SelfExtendingLanguage()
        name,op,_=registry.solve(self.case("running_parity"))
        saved=registry.dump()
        tampered=copy.deepcopy(saved)
        tampered["definitions"][name]["states"]=99
        with self.assertRaisesRegex(ValueError,"TAMPERED"):
            SelfExtendingLanguage.load(tampered)

    def test_autonomous_language_grows_then_reuses_three_times(self):
        frozen,history=study_registry()
        self.assertEqual([x["mode"] for x in history],
                         ["invent","reuse","invent","reuse","invent","reuse"])
        self.assertEqual(len(frozen["definitions"]),3)
        self.assertTrue(all(row["heldout_exact"]==row["heldout_total"]
                            for row in history))
        self.assertEqual(SelfExtendingLanguage.load(frozen).dump(),frozen)

    def test_random_unseen_transition_table_learned_from_data(self):
        # Random machine compiled outside the learner, no target program.
        generator=random_machine(765432,3,2,False)
        examples=samples_whole_word(generator,4488,2)
        model,_=learn_from_complete_io(examples)
        self.assertEqual(model.apply([0,1,1,0,0,1,1]),
                         output_of(generator,[0,1,1,0,0,1,1]))


if __name__=="__main__":
    unittest.main()
