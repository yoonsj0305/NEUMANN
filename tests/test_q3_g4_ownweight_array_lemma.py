"""G4 independent proof protocol and refusal controls. Source-free only."""
import unittest
from research.g4.array_invariant_verifier import (
 ArrayTask,Candidate,check_invariant,generate_source,
)
from research.g4.ownweight_array_invariant_proposer import (
 source_parse,deterministic_classical_compiler,split,
 OwnWeightProposer,training_data
)


class ArrayLearnedProofInterface(unittest.TestCase):
 def test_strict_whole_heldout_composition(self):
    train,test=split()
    self.assertEqual(len(train),10)
    self.assertEqual(len(test),5)
    self.assertTrue(set(train).isdisjoint(set(test)))
    self.assertEqual(len(set(train+test)),15)

 def test_source_parser_and_classical_access_equal(self):
    for task in (ArrayTask("FILL","A",None,-3),
                 ArrayTask("COPY","B","A",2),
                 ArrayTask("ADD","C","B",11)):
       s=generate_source(task)
       dest,src,x=source_parse(s)
       self.assertEqual((dest,src),(task.dest,task.src))
       self.assertEqual(len(x),10)
       self.assertEqual(deterministic_classical_compiler(s),
                        Candidate(task.kind,task.dest,task.src))

 def test_generator_trains_real_private_gradients_no_task_cache(self):
    train,_=split()
    X,Y,_=training_data(train)
    p=OwnWeightProposer()
    original=p.hash_weights()
    receipt=p.train(X,Y,epochs=100)
    self.assertNotEqual(original,p.hash_weights())
    self.assertEqual(receipt["epochs"],100)

 def test_fail_closed_ill_typed_aliased_array(self):
    with self.assertRaises(ValueError):
       Candidate("COPY","A","A")
    with self.assertRaises(ValueError):
       ArrayTask("ADD","B","B",3)
    with self.assertRaises(ValueError):
       Candidate("FILL","B","A")

 def test_independent_all_three_universal_SMT_proofs_and_bad_mutant(self):
    for source,valid,mutant in (
      (ArrayTask("FILL","A",None,4),
       Candidate("FILL","A",None),
       Candidate("FILL","B",None)),
      (ArrayTask("COPY","B","A",0),
       Candidate("COPY","B","A"),
       Candidate("COPY","A","B")),
      (ArrayTask("ADD","C","B",7),
       Candidate("ADD","C","B"),
       Candidate("COPY","C","B")),
    ):
       yes=check_invariant(source,valid,timeout_ms=3500)
       self.assertTrue(yes["verified"],yes)
       self.assertEqual(len(yes["obligations"]),3)
       self.assertTrue(all(x["counterexample_status"]=="unsat"
                           for x in yes["obligations"]))
       no=check_invariant(source,mutant,timeout_ms=3500)
       self.assertFalse(no["verified"],no)
       self.assertLessEqual(len(no["obligations"]),3)
       self.assertNotEqual(no["status"],"SOURCE_ALL_THREE_OBLIGATIONS_UNSAT")


if __name__=="__main__":
 unittest.main()
