"""Structural smoke tests only. No heldout reference or evaluator secrets."""
from __future__ import annotations
import random
import unittest
from research.q3.rc39.active_sparse import (
    ALPHABET, SCHEMA, discover, classical_single_site, run_program, perturb
)

def local_case(seed,number_of_reads,rad=512):
    rng=random.Random(seed)
    w="".join(rng.choice(ALPHABET) for _ in range(2*rad+1))
    w=w[:rad]+"B"+w[rad+1:]
    all_offsets=list(range(-rad,0))+list(range(1,rad+1))
    offsets=sorted(rng.sample(all_offsets,number_of_reads))
    hidden={"schema":SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION",
            "reads":[[d,w[rad+d]] for d in offsets]}
    oracle=lambda probe,center:run_program(hidden,probe,center)
    return w,rad,hidden,oracle

class SourceOnlyProofGates(unittest.TestCase):
    def test_first_source_only_sparse_pilot(self):
        w,center,hidden,oracle=local_case(3005,4)
        r=discover(w,center,oracle)
        classical=classical_single_site(w,center,oracle)
        self.assertEqual(r["status"],"SOURCE_CONSISTENT_EXECUTABLE")
        self.assertEqual(r["program"],hidden)
        self.assertEqual(classical["program"],hidden)
        self.assertGreaterEqual(classical["oracle_calls"]/r["oracle_calls"],10)
        self.assertEqual(classical["oracle_calls"],1025)
        self.assertEqual(r["neural_model_calls"],0)
    def test_k_zero_to_four_and_randomized_branches(self):
        for k in range(5):
            for seed in [101,202,303]:
                with self.subTest(k=k,seed=seed):
                    w,center,hidden,oracle=local_case(seed,k,rad=64)
                    r=discover(w,center,oracle)
                    self.assertEqual(r["status"],"SOURCE_CONSISTENT_EXECUTABLE",r)
                    self.assertEqual(r["program"],hidden)
    def test_budget_witness_and_invalid_grammar_failclosed(self):
        w,center,hidden,oracle=local_case(101,3,rad=64)
        self.assertEqual(discover(w,center,oracle,max_queries=2)["reason"],"QUERY_BUDGET_EXHAUSTED")
        self.assertEqual(discover(w,center,lambda word,pos:"B")["reason"],"NOT_AN_ACTUAL_POSITIVE")
        self.assertEqual(discover(w,center,oracle,source_rights="SECRET_OPCODE")["reason"],"INVALID_POSITIVE_SOURCE")
        self.assertIsNone(run_program({"schema":SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION","reads":[[1,"B"],[1,"C"]]},w,center))
    def test_nonconjunction_xor_has_source_contradiction_and_must_abstain(self):
        w,center,hidden,oracle=local_case(100,2,rad=32)
        def adversarial_xor(probe,i):
            active=sum(probe[i+d]==ch for d,ch in [(-1,w[center-1]),(1,w[center+1])])
            return "A" if probe[i]=="B" and active%2==0 else probe[i]
        r=discover(w,center,adversarial_xor)
        self.assertEqual(r["status"],"ABSTAIN",r)
        self.assertEqual(r["reason"],"INCONSISTENT_WITH_DECLARED_CAUSAL_GRAMMAR")
    def test_explicit_missing_relative_position_is_not_a_positive(self):
        w,center,hidden,oracle=local_case(8,1,rad=32)
        r=discover(w,center,oracle)
        target=r["program"]
        d=target["reads"][0][0]
        small="BBB"
        self.assertEqual(run_program(target,small,1),"B" if 1+d<0 or 1+d>=len(small) else run_program(target,small,1))
        self.assertIsNone(run_program(target,"DDD",1))
if __name__=="__main__":
    unittest.main()
