"""Independent local stress and boundary controls for the RC40 W implementation.
Not fresh generalization evidence. No ARC public original tasks are accessed.
"""
import random
import unittest
from collections import deque

from research.q3.rc39.active_mealy import MealyProgram, UnknownStateStructure
from research.q3.rc39.membership_conformance import SourceMeter
from research.q3.rc39.w_method_conformance import WMethodConformance


def machine(n, rng):
    return MealyProgram(
        ("A", "B"), ("0", "1"),
        tuple(tuple(rng.randrange(n) for _ in "AB") for _ in range(n)),
        tuple(tuple(str(rng.randrange(2)) for _ in "AB") for _ in range(n)))


def exact_product(a, b):
    queue = deque([(a.initial, b.initial)])
    seen = set(queue)
    while queue:
        x, y = queue.popleft()
        for j in range(2):
            if a.emissions[x][j] != b.emissions[y][j]:
                return False
            pair = (a.transitions[x][j], b.transitions[y][j])
            if pair not in seen:
                seen.add(pair)
                queue.append(pair)
    return True


class WMethodTests(unittest.TestCase):
    def test_source_only_matches_independent_product_on_3000_random_pairs(self):
        rng = random.Random(20261106)
        proven = 0
        unknown = 0
        for _ in range(3000):
            target = machine(rng.randrange(1,5), rng)
            hypothesis = machine(rng.randrange(1,5), rng)
            meter = SourceMeter(target.run, "AB", "01", 100000)
            checker = WMethodConformance(meter, 4, 100000)
            try:
                witness = checker.seek_counterexample(hypothesis)
            except UnknownStateStructure:
                unknown += 1  # unreachable or nonminimal candidates MUST fail closed
                continue
            self.assertEqual(witness is None, exact_product(target, hypothesis))
            proven += 1
        self.assertGreater(proven, 1000)
        self.assertGreater(unknown, 0)

    def test_five_state_delayed_discrepancy_found(self):
        target = MealyProgram(
            ("A", "B"), ("0", "1"),
            ((1,0),(2,1),(3,2),(4,3),(4,4)),
            (("0","0"),("0","0"),("0","0"),("0","0"),("1","0")))
        one_state_zero = MealyProgram(
            ("A", "B"), ("0", "1"), ((0,0),), (("0","0"),))
        tester = WMethodConformance(
            SourceMeter(target.run, "AB", "01", 100000), 5, 100000)
        word = tester.seek_counterexample(one_state_zero)
        self.assertIsNotNone(word)
        self.assertNotEqual(target.run(word), one_state_zero.run(word))
        self.assertGreaterEqual(len(word), 5)

    def test_invalid_state_bound_is_rejected(self):
        with self.assertRaises(ValueError):
            WMethodConformance(SourceMeter(lambda w:"0"*len(w),"AB","01"),0)
        target = MealyProgram(("A","B"),("0","1"),
                             ((1,1),(0,0)),(("0","0"),("1","1")))
        checker = WMethodConformance(SourceMeter(target.run,"AB","01"),1)
        with self.assertRaises(UnknownStateStructure):
            checker.seek_counterexample(target)


if __name__ == "__main__":
    unittest.main()
