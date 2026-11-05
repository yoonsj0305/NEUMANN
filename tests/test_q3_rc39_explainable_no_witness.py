"""No-heldout tests of RC39.1 no-witness explanatory schema."""
from __future__ import annotations
import random
import unittest
from research.q3.rc39.explainable_no_witness import discover_without_positive,PROGRAM_SCHEMA

def scratch_oracle(secret):
    p=sorted(secret)
    def oracle(word,center):
        for d,char in p:
            if word[center+d]!=char:return {"status":"VIOLATION","offset":d}
        return {"status":"ACCEPTED"}
    return oracle

class ExplainableSource(unittest.TestCase):
    def test_zero_to_eight_reads_exact_when_new_witness_not_given(self):
        for k in range(9):
            rng=random.Random(k*1001+3)
            opts=list(range(-32,0))+list(range(1,33))
            target=sorted((d,rng.choice("ABC")) for d in rng.sample(opts,k))
            r=discover_without_positive(scratch_oracle(target),radius=32,max_queries=48)
            self.assertEqual(r["status"],"SOURCE_CONSISTENT_EXECUTABLE",r)
            self.assertEqual(r["program"]["reads"],[list(x) for x in target])
            self.assertLessEqual(r["oracle_calls"],5*k+3)
            self.assertEqual(r["positive_witness_supplied"],False)
            self.assertEqual(r["neural_model_calls"],0)
    def test_budget_fails_closed(self):
        r=discover_without_positive(scratch_oracle([(-1,'B'),(1,'C')]),
                                    radius=32,max_queries=2)
        self.assertEqual(r["status"],"ABSTAIN",r)
        self.assertIn("SOURCE_QUERY_BUDGET",r["reason"])
        self.assertNotIn("program",r)
    def test_malformed_oracle_fails_closed(self):
        r=discover_without_positive(lambda w,c:{"status":"VIOLATION","offset":0},
                                    radius=32)
        self.assertEqual(r["status"],"ABSTAIN")
        self.assertNotIn("program",r)
        r=discover_without_positive(lambda w,c:{"status":"VIOLATION","offset":-1,"expected":"B"},
                                    radius=32)
        self.assertEqual(r["status"],"ABSTAIN")
    def test_same_offset_forever_rejected(self):
        r=discover_without_positive(lambda w,c:{"status":"VIOLATION","offset":2},
                                    radius=32)
        self.assertEqual(r["status"],"ABSTAIN")
        self.assertIn("NO_POSSIBLE_EXPECTED_CHARACTER",r["reason"])
    def test_source_degraded_out_of_contract(self):
        r=discover_without_positive(lambda w,c:{"status":"ACCEPTED"},radius=0)
        self.assertEqual(r["status"],"ABSTAIN")
        self.assertNotIn("program",r)
if __name__=="__main__":
    unittest.main()
