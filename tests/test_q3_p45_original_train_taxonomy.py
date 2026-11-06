"""Small exact tests for the read-only original TRAIN taxonomy."""
import unittest
from experiments.q3_p45_original_train_only_failure_taxonomy import classify


def example(a,b):
    return [{"input":a,"output":b}]


class Taxonomy(unittest.TestCase):
    def test_shape_change(self):
        self.assertEqual(classify(example([[1,2]],[[1],[2]]))["class"],"SHAPE_CHANGE")

    def test_zero_change_not_impossibility(self):
        self.assertEqual(classify(example([[1,0,1]],[[1,0,1]]))["class"],"ZERO_PIXEL_CHANGE")

    def test_single_pixel_mapping(self):
        v=classify(example([[1,0,2,0,1]],[[1,5,2,5,1]]))
        self.assertEqual(v["class"],"SINGLE_PIXEL_MAPPING")
        self.assertEqual(v["only_mapping"],[0,5])
        self.assertEqual(v["changed_pixels"],2)

    def test_multi_mapping(self):
        self.assertEqual(classify(example([[1,0]],[[2,3]]))["class"],"MULTI_PIXEL_MAPPING")

    def test_conflicting_mapping_across_train_pairs(self):
        task=[{"input":[[1,0]],"output":[[1,2]]},
              {"input":[[3,1]],"output":[[3,4]]}]
        self.assertEqual(classify(task)["class"],"MULTI_PIXEL_MAPPING")

    def test_precedence_shape(self):
        task=[{"input":[[1,0]],"output":[[1,2]]},
              {"input":[[1,0]],"output":[[1],[0]]}]
        self.assertEqual(classify(task)["class"],"SHAPE_CHANGE")


if __name__=="__main__":
    unittest.main()
