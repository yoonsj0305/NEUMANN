"""Only typed semantic interpreter invariants; NOT a source benchmark score."""
import unittest
from research.q3.relational_object_program_inventor import (
    Comp,CHOICES,ORDER,Program,OwnWeightComposer,
    components,score,synth_execute
)


class Q3ObjectRelationalPrimitives(unittest.TestCase):
    def test_parser_and_composed_program(self):
        grid=[
            [0,0,0,0,0,0,0,0,0,0],
            [0,1,1,0,0,2,2,0,0,0],
            [0,1,1,0,0,2,2,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,3,3,0,0,4,4,0,0,0],
            [0,3,3,0,0,4,4,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ]
        config={
            "connectivity":4,"background_top_k":1,
            "minimum_pixels":4,"minimum_width":2,
            "minimum_height":2,"minimum_fill":0.98,
            "cluster_ratio":0.14,"coordinate":"center",
            "collision":"largest",
        }
        prog=Program(tuple(config[k] for k in ORDER))
        self.assertEqual(synth_execute(prog,grid),[[1,2],[3,4]])
        self.assertEqual(prog.ast()[0],"SpatialRasterize")
        self.assertNotIn("COPY_PREFIX",str(prog.ast()))

    def test_weight_training_is_real_and_not_result_copy(self):
        m=OwnWeightComposer(3)
        first=m.weights_digest()
        p,trace=m.sample()
        m.learn(trace,0.71)
        self.assertNotEqual(first,m.weights_digest())
        self.assertEqual(m.updates,1)
        self.assertTrue(all(p.obj()[k] in CHOICES[k] for k in ORDER))

    def test_components_exclude_background_noise(self):
        grid=[[0,4,4,0],[0,4,4,0],[0,0,0,0]]
        cc=components(grid,{0},4)
        self.assertEqual(len(cc),1)
        self.assertEqual(cc[0].area,4)
        self.assertEqual(cc[0].fill,1.)

    def test_failure_is_explicit_no_fake_grid(self):
        p=Program(tuple(CHOICES[k][0] for k in ORDER))
        self.assertIsNone(synth_execute(p,[]))


if __name__=="__main__":
    unittest.main()
