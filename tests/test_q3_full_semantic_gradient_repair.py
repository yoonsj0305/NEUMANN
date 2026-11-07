"""Q3 causal regression: previously only 6/86 features actually learned."""
import unittest
from research.q3.generative_typed_operator_policy import Generator,AST
from research.q3.task_conditional_operator_generator import (
    TaskConditionalGenerator, BehavioralProblem,
)
from research.q3.behavioral_proof_reward_first import (
    IndependentChecker, observe,
)


class GradientDimensionCausalRegression(unittest.TestCase):
    def test_80_semantic_coefficients_do_update(self):
        m=TaskConditionalGenerator(seed=12)
        p=observe("source_plus_one")
        m.set_observation(p)
        before={k:[row[:] for row in mat] for k,mat in m.weights.items()}
        candidate,events=m.sample(collision=True,failed_proofs=0,
                    root_kind="Int",bound_index=True,max_depth=4,max_nodes=80)
        self.assertEqual(len(events[0][4]),86)
        m.apply_feedback(events,reward=0.75,lr=0.04)
        self.assertEqual(m.gradient_steps,1)
        structural_changes=sum(
            abs(a-b)>1e-13
            for k in m.weights
            for old,new in zip(before[k],m.weights[k])
            for a,b in zip(old[6:],new[6:])
        )
        self.assertGreater(structural_changes,0,
            "fatal prior bug: 80/86 task-semantic coefficients frozen")
        self.assertNotEqual(m.parameters_hash(),
            Generator(seed=12).parameters_hash())

    def test_full_gradient_per_sample_vector_not_global_six(self):
        p=observe("one_minus_source")
        m=TaskConditionalGenerator(seed=9)
        m.set_observation(p)
        _,events=m.sample(collision=True,failed_proofs=0,
                    root_kind="Int",bound_index=True,max_depth=4,max_nodes=80)
        self.assertEqual(len(events[0][4]),86)
        m.apply_feedback(events,reward=-0.35)

    def test_fail_closed_on_feature_dimension_drift(self):
        m=TaskConditionalGenerator(seed=25)
        p=observe("source_plus_one")
        m.set_observation(p)
        ast,events=m.sample(collision=True,failed_proofs=0,
                    root_kind="Int",bound_index=True,max_depth=4,max_nodes=80)
        m.weights[events[0][0]][events[0][3]].pop()
        with self.assertRaisesRegex(ValueError,"LEARNED_FEATURE_DIMENSION_MISMATCH"):
            m.apply_feedback(events,reward=0.2)

    def test_old_exact_match_reward_prefers_unrelated_zero(self):
        p=observe("source_plus_one")
        checker=IndependentChecker("source_plus_one",p)
        source=AST("Int","read_src",(AST("Int","j"),))
        zero=AST("Int","zero")
        a=checker(source)
        b=checker(zero)
        self.assertEqual(a["validated_fraction"],0)
        self.assertEqual(b["validated_fraction"],1/32)
        self.assertGreater(b["validated_fraction"],a["validated_fraction"])
        # The reward defect is not repaired merely by updating weights.
        self.assertEqual(a["verdict"],"CEX")
        self.assertEqual(b["verdict"],"CEX")

if __name__=="__main__":
    unittest.main()
