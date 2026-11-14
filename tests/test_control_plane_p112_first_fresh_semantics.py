"""Source-bound P1.12 first-actual controls. NO model or model scores."""
import unittest
from experiments.control_plane_p112_first_fresh_semantics import (
    load_frozen, public_ir, lexical_guesses, ROOT
)
from neumann1.control_plane_p112 import select_unique_top

class FrozenP112FirstControls(unittest.TestCase):
    def test_source_manifest_immutable_and_twelve_new_roles(self):
        data, lock = load_frozen()
        self.assertEqual(len(data["tasks"]), 12)
        self.assertEqual(data["raw_top_min_correct"], 9)
        self.assertEqual(data["additional_correct_over_best_lexical_min"], 2)
        self.assertIn("s03", [x["id"] for x in data["tasks"]])
        self.assertNotIn("p111", " ".join(x["id"] for x in data["tasks"]))
        self.assertEqual(data["first_frozen_sha"],"46f5d7bf2b5f10c491999f398b182cab5de3fe5d")
        self.assertTrue(lock["source_blobs"])
    def test_pre_inference_reference_correction_is_preserved_not_mutated(self):
        import json
        old=json.loads((ROOT/"docs/experiments/control_plane_p112_FRESH_FIRST_FROZEN.json").read_text())
        new=json.loads((ROOT/"docs/experiments/control_plane_p112_FRESH_FIRST_CORRECTED_FROZEN.json").read_text())
        self.assertEqual(old["tasks"][2]["id"],"s03")
        self.assertEqual(old["tasks"][2]["expected_index"],3)
        self.assertEqual(new["tasks"][2]["expected_index"],0)
        self.assertEqual(new["tasks"][2]["candidate_roles"][0],"buck converter")
        self.assertEqual(new["model_revision"],old["model_revision"])
        self.assertTrue(new["preregistered_before_model_scores"])
    def test_builds_registered_ir_without_gold_or_private_verifier(self):
        data,_=load_frozen()
        for row in data["tasks"]:
            ir=public_ir(row)
            self.assertEqual(len(ir["pairs"]),4)
            self.assertTrue(all(x["query"]=="Target function: "+row["target_role"] for x in ir["pairs"]))
            self.assertNotIn("expected_index",str(ir))
            self.assertEqual([x["entity"] for x in ir["pairs"]],list("ABCD"))
            for idx in range(4):
                scores=[0.0]*4
                scores[idx]=1.0
                got=select_unique_top(ir,scores)
                self.assertEqual(got["selected_candidate_position"],idx)
    def test_label_free_strong_lexical_comparators_cover_each_task(self):
        data,_=load_frozen()
        predictions=lexical_guesses(data["tasks"])
        self.assertEqual(set(predictions),{"word","char","constant_first"})
        for x in predictions.values():
            self.assertEqual(len(x),12)
            for v in x:
                self.assertTrue(v["winner"] is None or v["winner"] in range(4))
    def test_intact_data_record_is_required(self):
        data,_=load_frozen()
        row=data["tasks"][0]
        altered={**row,"leaked_reference":row["expected_index"]}
        with self.assertRaises(ValueError):
            public_ir(altered)

if __name__=="__main__":
    unittest.main()
