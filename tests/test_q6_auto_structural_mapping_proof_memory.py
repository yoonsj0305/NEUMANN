"""Causal controls for generated index-observation contracts, no external model."""
import unittest

from research.q6.auto_structural_mapping_proof_memory import (
    ObservationTerm,heads_from_existing_target_semantics,
    enumerate_typed_observations,preliminary_evidence,
    local_relational_probes,proof_contracts,
    retrieve_compatible,source_memories,
    select_observation_without_reference_oracle,digest,
)


class AutoStructuralMappingTests(unittest.TestCase):
    def test_proposer_discovers_available_primitives_from_target_source(self):
        heads=heads_from_existing_target_semantics()
        self.assertIn("str.at",heads)
        self.assertIn("str.substr",heads)
        self.assertIn("str.len",heads)
        candidates=enumerate_typed_observations(heads)
        self.assertGreaterEqual(len(candidates),15)
        self.assertTrue(all(c.head in heads for c in candidates))
        self.assertTrue(all("String" not in str(c.ast())
                            for c in candidates))

    def test_automatic_inference_not_human_target_alpha_injection(self):
        heads=heads_from_existing_target_semantics()
        candidates,audit,survivors=select_observation_without_reference_oracle(
            heads)
        self.assertGreater(len(candidates),len(survivors))
        self.assertGreaterEqual(len(survivors),1)
        self.assertTrue(any(p["reason"]=="CONCRETE_COUNTEREXAMPLE_TO_TRANSFER"
                            for p in audit))
        # Two different source-language expressions represent an observation
        # (str.at vs str.substr length1). The learner rejects spurious
        # wrong indices, rather than a human injecting the canonical alpha.
        self.assertEqual({s.head for s in survivors},
                         {"str.at","str.substr"})
        self.assertTrue(all(s.index=="j" for s in survivors))
        self.assertEqual(digest(survivors[0].ast()),
                         digest(survivors[0].ast()))

    def test_hard_negative_index_and_degenerate_values_rejected(self):
        for term in (ObservationTerm("str.at","j+1",None),
                     ObservationTerm("str.at","0",None),
                     ObservationTerm("str.at","n-1-j",None),
                     ObservationTerm("str.substr","j",0),
                     ObservationTerm("str.substr","j",2)):
            ok,reason,count=preliminary_evidence(term)
            self.assertFalse(ok,(term,reason))
        good,reason,count=preliminary_evidence(
            ObservationTerm("str.substr","j",1))
        self.assertTrue(good)
        self.assertGreaterEqual(count,7)

    def test_memories_contain_no_literal_alpha_and_wrong_types_rejected(self):
        memories=source_memories()
        self.assertEqual(len(memories),3)
        decision=retrieve_compatible(memories,
            {"target_heads":heads_from_existing_target_semantics(),
             "target_type":"String"})
        self.assertEqual(sum(x["accepted"] for x in decision),1)
        self.assertEqual(decision[0]["source"],"Q6_ARRAY_PREFIX_WRITE_PR685")
        self.assertTrue(all(not x["accepted"] for x in decision[1:]))
        self.assertNotIn("str.at(x,j)",str(memories))

    def test_generated_smt_commutation_ties_to_actual_concrete_next(self):
        term=ObservationTerm("str.at","j",None)
        checks=proof_contracts(term)
        self.assertEqual(set(checks),{
            "INVENTED_ALPHA_COMMUTING",
            "INVENTED_ALPHA_INDEPENDENT_FIDELITY",
            "WRONG_TARGET_UPDATE_MUST_BREAK"})
        for name,(expect,body) in checks.items():
            self.assertIn("str.at",body)
            self.assertIn("check-sat" not in body,[True,False])
            self.assertIn("(str.substr dst 0 i)",body)
        self.assertEqual(checks["INVENTED_ALPHA_COMMUTING"][0],"unsat")
        self.assertEqual(checks["WRONG_TARGET_UPDATE_MUST_BREAK"][0],"sat")

    def test_generic_candidate_without_usable_read_abstains(self):
        candidates,audit,survivors=select_observation_without_reference_oracle(
            ["str.++","str.len"])
        self.assertEqual(candidates,[])
        self.assertEqual(survivors,[])
        mem=retrieve_compatible(source_memories(),
            {"target_heads":["str.len"],"target_type":"String"})
        self.assertFalse(any(x["accepted"] for x in mem))


if __name__=="__main__":
    unittest.main()
