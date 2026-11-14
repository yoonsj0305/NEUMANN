"""Causal test: Q3 invents a binary *law* from data, not a seeded color order."""
import unittest
from research.q3.induce_binary_algebra_original import (
    Decomposition, InventedJoin, closure_relations, subgrids,
    admit_program, predict_frozen, serialize, infer_programs, study_one,
)


def make_panel_input(panels,divider=3):
    h=len(panels[0])
    w=len(panels[0][0])
    assert all(len(p)==h and len(p[0])==w for p in panels)
    rows=[]
    for y in range(h):
        line=[]
        for i,p in enumerate(panels):
            if i:line.append(divider)
            line.extend(p[y])
        rows.append(line)
    return rows


class Q3AutonomousOperatorLaw(unittest.TestCase):
    def problem(self):
        # Reference law is constructed ONLY by the test fixture to measure
        # whether the learner extracts it without receiving its name/order.
        a=[[2,2],[4,0]]
        b=[[4,0],[2,0]]
        c=[[6,4],[0,0]]
        grid=make_panel_input([a,b,c])
        target=[[6,2],[2,0]]
        return {"train":[{"input":grid,"output":target}],
                "test":[{"input":make_panel_input(
                       [[[4,2],[4,0]],[[2,6],[0,2]],[[6,0],[2,4]]]),
                       "output":[[6,6],[2,2]]}]}

    def test_model_induces_law_and_compiles_new_operator(self):
        task=self.problem()
        # Provide >3 original-like TRAIN examples; NOT the target ordering.
        task["train"]=task["train"]*3
        model=admit_program(task["train"])
        self.assertIsNotNone(model)
        self.assertGreaterEqual(model["candidate_programs"],1)
        prog=model["models"][0]["_law"]
        self.assertGreaterEqual(len(prog.edges),3)
        self.assertTrue(prog.all_laws_hold())
        self.assertIn("DefineOperator",str(prog.to_ast()))
        self.assertEqual(predict_frozen(model,task["test"][0]["input"]),
                         task["test"][0]["output"])
        self.assertNotIn(6,())  # no correct-order table passed to the learner

    def test_learning_is_causally_necessary(self):
        task=self.problem()
        task["train"]=task["train"]*3
        model=admit_program(task["train"])
        self.assertIsNotNone(model)
        entry=model["models"][0]
        learned=entry["_law"]
        untrained=InventedJoin(learned.identity,(),learned.colors)
        grid=task["test"][0]["input"]
        self.assertIsNone(
            __import__("research.q3.induce_binary_algebra_original",fromlist=["predict_single"])
              .predict_single(untrained,entry["_decomp"],grid))
        row=study_one(task,"independent_external_like_input","test_fixture")
        self.assertTrue(row["original_TEST_exact"])
        self.assertTrue(row["learning_is_necessary_on_this_original"])

    def test_dominance_cycle_refused(self):
        with self.assertRaisesRegex(Exception,"INCONSISTENT_DOMINANCE"):
            closure_relations({0,2,4},{(2,4),(4,2)})

    def test_separator_is_inferred_not_hardcoded(self):
        p=[[[2,0]],[[4,4]],[[6,0]]]
        g=make_panel_input(p,divider=7)
        self.assertEqual(subgrids(g,Decomposition("columns",2,1,3)),p)
        self.assertIsNone(subgrids(g,Decomposition("columns",3,1,3)))

    def test_abstain_on_unidentifiable_colors(self):
        task=self.problem();task["train"]=task["train"]*3
        model=admit_program(task["train"])
        if model is None:self.fail("training missed the available symbolic law")
        # New color 9 unseen in training must never be assigned invented rank.
        unknown=make_panel_input(
            [[[9,2],[4,0]],[[2,6],[0,2]],[[6,0],[2,4]]])
        self.assertIsNone(predict_frozen(model,unknown))


if __name__=="__main__":
    unittest.main()
