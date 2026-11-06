"""Pure-Python contract tests; Z3 proof runs separately in the CI gate."""
import unittest

from research.q3.typed_relation_cegis_classical_control import (
    Candidate, Observation, candidates, consistent, discover,
    h0_collision_for_program, smt_script, source_free_traces,
)


class TypedRelationBaselineTest(unittest.TestCase):
    def test_ground_traces_uniquely_identify_three_relations(self):
        for target in (Candidate('right', 1, 0),
                       Candidate('right', 1, 1),
                       Candidate('right', 2, 0)):
            with self.subTest(target=target):
                observations = source_free_traces(target)
                matches = [c for c in candidates() if consistent(c, observations)]
                self.assertEqual(matches, [target])
                self.assertTrue(h0_collision_for_program(target))

    def test_h0_no_collision_abstains_before_verifier(self):
        def forbidden(*args):
            raise AssertionError('no verifier calls permitted')
        proposed, receipt = discover([], False, forbidden)
        self.assertIsNone(proposed)
        self.assertEqual(receipt['verdict'], 'ABSTAIN_NO_H0_COLLISION')

    def test_unknown_verifier_abstains_without_claiming_proof(self):
        target = Candidate('right', 1, 0)
        proposal, record = discover(source_free_traces(target), True,
                                    lambda c, mutant: ('UNKNOWN_TIMEOUT', 1.0))
        self.assertIsNone(proposal)
        self.assertEqual(record['verdict'], 'ABSTAIN_NO_INDUCTIVE_CANDIDATE')

    def test_no_valid_typed_candidate_abstains(self):
        # Entire deliberately unsupported square transformation.
        observations = [Observation((4, 5, 6), (2, 3, 4), (4, 9, 16), 3)]
        proposal, record = discover(observations, True,
                                    lambda c, mutant: ('unsat', 0.0))
        self.assertIsNone(proposal)
        self.assertEqual(record['z3_calls'], 0)

    def test_prover_has_real_transition_and_mutant_control(self):
        candidate = Candidate('right', 1, 0)
        program = Candidate('right', 1, 1)
        proof = smt_script(candidate, program)
        mutation = smt_script(candidate, program, corruption=True)
        self.assertIn('(+ (* 1 (select right i)) 1)', proof)
        self.assertIn('(store out i (+ (+ (* 1 (select right i)) 1) 1))', mutation)
        self.assertNotEqual(proof, mutation)


if __name__ == '__main__':
    unittest.main()
