"""Source-only, product-independent regression and small exhaustive fault domain.

These tests never require the production hidden FIRST grader, and compare
W-method certificates against a separately implemented exact product check.
"""
import itertools
import random
import unittest

from research.q3.rc39.active_mealy import MealyProgram, UnknownStateStructure
from research.q3.rc39.membership_conformance import SourceMeter
from research.q3.rc39.wmethod_conformance import (
    WMethodConformance, minimal_hypothesis, characterization_set
)


def exact_equivalence(first, second):
    """Separate reachable product-state oracle; NEVER fed into conformance."""
    queue = [(first.initial, second.initial)]
    seen = set(queue)
    for x,y in queue:
        for index,_ in enumerate(first.alphabet):
            if first.emissions[x][index] != second.emissions[y][index]:
                return False
            pair = (first.transitions[x][index], second.transitions[y][index])
            if pair not in seen:
                seen.add(pair)
                queue.append(pair)
    return True


def make_machine(n, transitions, emissions, alphabet="AB"):
    k = len(alphabet)
    return MealyProgram(tuple(alphabet), ("0", "1"),
                        tuple(tuple(transitions[i*k:(i+1)*k]) for i in range(n)),
                        tuple(tuple(emissions[i*k:(i+1)*k]) for i in range(n)))


def check_just_one(hypothesis, reference, bound):
    meter = SourceMeter(reference.run, "".join(reference.alphabet), "01", 150000)
    checker = WMethodConformance(meter, bound, 150000)
    result = checker.seek_counterexample(hypothesis)
    proof = exact_equivalence(reference, hypothesis)
    if result is not None:
        assert reference.run(result) != hypothesis.run(result)
    assert (result is None) == proof, (hypothesis, reference, result)
    return meter.unique_queries


class WMethodTests(unittest.TestCase):
    def test_all_two_state_targets_vs_three_unseen_candidates(self):
        # All 4 one-state and all 256 two-state machines, including equivalent,
        # unreachable and non-minimal machines. Total 260 reference structures.
        hypotheses = [
            make_machine(1, (0,0), ("0","0")),
            make_machine(1, (0,0), ("0","1")),
            make_machine(2, (1,0,0,1), ("0","1","1","0")),
        ]
        cases = 0
        for n in (1, 2):
            for transition in itertools.product(range(n), repeat=2*n):
                for emitted in itertools.product("01", repeat=2*n):
                    ref = make_machine(n, transition, emitted)
                    for hyp in hypotheses:
                        check_just_one(hyp, ref, 2)
                        cases += 1
        self.assertEqual(cases, 780)

    def test_random_three_state_adversaries(self):
        rng = random.Random(0x4F_2026)
        hypotheses = [make_machine(1,(0,0),("0","0")),
                      make_machine(2,(1,0,0,1),("0","1","1","0"))]
        for _ in range(250):
            candidate = make_machine(3,
                [rng.randrange(3) for _ in range(6)],
                [rng.choice("01") for _ in range(6)])
            for hyp in hypotheses:
                check_just_one(hyp, candidate, 3)

    def test_nonminimal_candidate_and_characterization(self):
        candidate = make_machine(3, (1,0,1,0,2,2),
                                 ("0","0","0","0","1","1"))
        mini = minimal_hypothesis(candidate)
        self.assertEqual(len(mini.transitions),1)
        self.assertEqual(mini.run("BABBA"), candidate.run("BABBA"))
        self.assertEqual(len(characterization_set(mini)), 1)
        check_just_one(candidate, make_machine(1,(0,0),("0","0")), 2)

    def test_state_bound_and_budget_fail_closed(self):
        hypothesis = make_machine(2,(1,0,0,1),("0","1","1","0"))
        ref = hypothesis
        source = SourceMeter(ref.run,"AB","01", 1)
        checker = WMethodConformance(source,2,100)
        with self.assertRaisesRegex(UnknownStateStructure,"TOTAL_SOURCE_MEMBERSHIP_BUDGET_EXHAUSTED"):
            checker.seek_counterexample(hypothesis)
        self.assertEqual(checker.completed_certificates,0)
        source2 = SourceMeter(ref.run,"AB","01", 100)
        checker2 = WMethodConformance(source2,2,1)
        with self.assertRaisesRegex(UnknownStateStructure,"W_METHOD_WORD_BUDGET_EXHAUSTED"):
            checker2.seek_counterexample(hypothesis)
        self.assertEqual(checker2.completed_certificates,0)
        with self.assertRaisesRegex(UnknownStateStructure,"HYPOTHESIS_EXCEEDS_REFERENCE_STATE_BOUND"):
            WMethodConformance(SourceMeter(ref.run,"AB","01"),1).seek_counterexample(hypothesis)

    def test_trusted_state_bound_is_necessary(self):
        # The implementation graph below has three reachable states.
        # With an INCORRECT stated bound of 1, W-method is NOT sound.
        hidden = make_machine(3,(1,0,2,1,2,2),
                              ("0","0","0","0","1","1"))
        hypothesis = make_machine(1,(0,0),("0","0"))
        tester = WMethodConformance(SourceMeter(hidden.run,"AB","01"),1)
        self.assertIsNone(tester.seek_counterexample(hypothesis))
        self.assertFalse(exact_equivalence(hidden,hypothesis))
        self.assertEqual(hidden.run("AAA"), "001")
        # Invalid assumptions must never be silently promoted to Q3/Q6.

if __name__ == "__main__":
    unittest.main()
