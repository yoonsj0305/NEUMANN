"""Q3 graph-coordinate invention tests: no pre-coded correct shape rule."""
import unittest
from research.q3.invent_object_graph_coordinate_operator import (
    objects,template_for,symbolize,learn_object_operator,study,
    InventedObjectOperator,emit_from_template,
)


def make_grid(h,w,background=7):
    return [[background]*w for _ in range(h)]


def object_square(grid,y,x,size,color,hollow):
    for yy in range(y,y+size):
        for xx in range(x,x+size):
            if not hollow or yy in (y,y+size-1) or xx in (x,x+size-1):
                grid[yy][xx]=color


def marked(grid,components,background=7,paint=2):
    # ONLY the synthetic fixture knows how to produce a correct target.
    # This formula is NOT imported or given to the generator.
    out=[r[:] for r in grid]
    for top,left,size in components:
        bot=top+size-1
        right=left+size-1
        locs=[(top-1,left),(top-1,right),
              (top,left-1),(top,right+1),
              (bot,left-1),(bot,right+1),
              (bot+1,left),(bot+1,right)]
        for y,x in locs:
            assert out[y][x]==background
            out[y][x]=paint
    return out


def pair(size,top,left,color=6,hollow=True,others=True):
    grid=make_grid(14,14)
    object_square(grid,top,left,size,color,hollow)
    if others:
        for y in (10,11):
            for x in (9,10,11,12):
                grid[y][x]=color
        grid[0][13]=color
        grid[13][1]=color
    target=marked(grid,[(top,left,size)])
    return {"input":grid,"output":target}


class ObjectGraphOperatorInvention(unittest.TestCase):
    def training(self):
        return [pair(3,2,2,6,True),
                pair(4,2,3,8,True),
                pair(2,5,3,9,False)]

    def test_object_graph_extraction_is_color_independent(self):
        p=self.training()[0]
        bg,comps=objects(p["input"],4)
        self.assertEqual(bg,7)
        self.assertTrue(any(c.color==6 and c.area==8 for c in comps))
        self.assertTrue(any(c.area==1 for c in comps))

    def test_new_symbolic_coordinate_operator_is_invented(self):
        train=self.training()
        op=learn_object_operator(train,4)
        self.assertIsNotNone(op)
        self.assertGreaterEqual(len(op.selector),1)
        self.assertEqual(len(op.template),8)
        self.assertEqual(op.output_color,2)
        self.assertEqual(op.ast()[0],"DefineInventedObjectGraphOperator")
        for q in train:self.assertEqual(op.apply(q["input"]),q["output"])

    def test_unseen_location_and_color_reuses_generated_semantics(self):
        op=learn_object_operator(self.training(),4)
        self.assertIsNotNone(op)
        new=pair(5,2,2,color=5,hollow=True,others=False)
        self.assertEqual(op.apply(new["input"]),new["output"])

    def test_input_output_impossibility_requires_new_color(self):
        train=self.training()
        for q in train:
            self.assertNotIn(2,{v for row in q["input"] for v in row})
        op=learn_object_operator(train,4)
        self.assertIsNotNone(op)
        # Conservative join cannot create a target color absent from source.
        self.assertEqual(op.output_color,2)

    def test_failed_noninvariant_structure_abstains(self):
        p=pair(3,2,2)
        bad={"input":p["input"],"output":[row[:] for row in p["input"]]}
        self.assertIsNone(learn_object_operator([p,bad],4))

    def test_conflicting_unknown_grid_does_not_mutate(self):
        op=learn_object_operator(self.training(),4)
        self.assertIsNotNone(op)
        inp=make_grid(14,14)
        object_square(inp,0,0,3,5,True)
        self.assertIsNone(op.apply(inp))  # computed paint exceeds grid bounds


if __name__=="__main__":
    unittest.main()
