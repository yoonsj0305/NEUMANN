"""Proof-carrying negative control: finite source traces alone do not entail
unbounded correctness without a maximum hidden-state assumption.

For ANY finite observation set S let L=max input length in S. Construct a
one-state all-zero machine M0, and an (L+2)-state machine M1 emitting a single
1 only on encountering the (L+1)th A. Every input in S is indistinguishable
under M0 and M1, yet A^(L+1) separates them. This is a constructive proof,
not merely random unsolved tasks or a neural-model underperformance claim.
"""
from itertools import product
import unittest

def zero_machine(word):
    return "0"*len(word)

def delayed_hidden_machine(word,L):
    if type(L)!=int or L<0:raise ValueError("L must be nonnegative")
    state=0
    y=[]
    for a in word:
        should_emit=(a=="A" and state==L)
        if a=="A":state=min(state+1,L+1)
        y.append("1" if should_emit else "0")
    return "".join(y)

class SourceObservabilityLowerBound(unittest.TestCase):
    def test_every_finite_experiment_has_a_nonidentifiable_extension(self):
        for L in range(7):
            with self.subTest(max_source_length=L):
                # Exhaustive all ABC words up to length L, not just a sample.
                for size in range(L+1):
                    for letters in product("ABC",repeat=size):
                        s="".join(letters)
                        self.assertEqual(zero_machine(s),delayed_hidden_machine(s,L))
                longer="A"*(L+1)
                self.assertNotEqual(zero_machine(longer),
                                    delayed_hidden_machine(longer,L))
                self.assertEqual(delayed_hidden_machine(longer,L),"0"*L+"1")

    def test_any_finite_source_log_has_the_same_ambiguity(self):
        logs=[["A","BB","CAABC"],["BC","CCCAA"],[""],["ABCA"*3]]
        for source_inputs in logs:
            L=max(map(len,source_inputs),default=0)
            self.assertTrue(all(zero_machine(w)==delayed_hidden_machine(w,L)
                                for w in source_inputs))
            self.assertNotEqual(zero_machine("A"*(L+1)),
                                delayed_hidden_machine("A"*(L+1),L))
if __name__=="__main__":unittest.main()
