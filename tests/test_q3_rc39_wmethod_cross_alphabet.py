"""Preregistered cross-alphabet/state/output W-method regression, 512 checks.

NOT an external semantic-family Q6 experiment. Refuses to promote invalid
unbounded generalization; only complete deterministic bounded Mealy systems.
"""
from collections import deque
from hashlib import sha256
import random
import unittest

from research.q3.rc39.active_mealy import MealyProgram
from research.q3.rc39.membership_conformance import SourceMeter
from research.q3.rc39.wmethod_conformance import WMethodConformance


def generated(alphabet, outputs, states, replicate, role):
    key=f"RC39-W-CROSS|{alphabet}|{outputs}|{states}|{replicate}|2026-11-06|{role}"
    rng=random.Random(int.from_bytes(sha256(key.encode()).digest(),"big"))
    transitions=tuple(tuple(rng.randrange(states) for _ in alphabet) for _ in range(states))
    emissions=tuple(tuple(rng.choice(outputs) for _ in alphabet) for _ in range(states))
    return MealyProgram(tuple(alphabet), tuple(outputs), transitions, emissions)


def separate_product_equivalence(a, b):
    """Different implementation than W-method: all reachable product pairs."""
    queue=deque([(a.initial,b.initial)])
    visited=set(queue)
    while queue:
        i,j=queue.popleft()
        for k in range(len(a.alphabet)):
            if a.emissions[i][k]!=b.emissions[j][k]:
                return False
            nxt=(a.transitions[i][k],b.transitions[j][k])
            if nxt not in visited:
                visited.add(nxt);queue.append(nxt)
    return True


class CrossAlphabetGeneralization(unittest.TestCase):
    def test_precommitted_512_cross_alphabet_product_checks(self):
        comparisons=0
        correct_certificates=0
        counterexamples=0
        for alphabet in ('ABC','ABCD'):
            for outputs in ('01','012'):
                for states in (3,4,5,6):
                    for replicate in range(16):
                        hidden=generated(alphabet,outputs,states,replicate,'reference')
                        constant=MealyProgram(tuple(alphabet),tuple(outputs),
                                              (tuple(0 for _ in alphabet),),
                                              (tuple(outputs[0] for _ in alphabet),))
                        challenger=generated(alphabet,outputs,states,replicate,'hypothesis')
                        if replicate%5==0:
                            challenger=hidden
                        for hypothesis in (constant,challenger):
                            meter=SourceMeter(hidden.run,alphabet,outputs,200000)
                            checker=WMethodConformance(meter,states,200000)
                            observed=checker.seek_counterexample(hypothesis)
                            truth=separate_product_equivalence(hidden,hypothesis)
                            self.assertEqual(observed is None, truth,
                                (alphabet,outputs,states,replicate))
                            if observed is not None:
                                self.assertNotEqual(hidden.run(observed),hypothesis.run(observed))
                                counterexamples+=1
                            else:
                                correct_certificates+=1
                            comparisons+=1
        self.assertEqual(comparisons,512)
        self.assertGreater(correct_certificates,0)
        self.assertGreater(counterexamples,0)

if __name__=='__main__': unittest.main()
