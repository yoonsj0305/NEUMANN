"""Tests exact training-language recognition without using external test sources."""
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("q3b_ext", HERE/"frozen_first_external.py")
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def authored_fixture(a,b,p,q):
    def signed(x):return str(x) if x>=0 else f"(- {-x})"
    aa,bb,pp,qq=map(signed,(a,b,p,q))
    rules=[
      "(assert (forall ((x Int)(y Int)) (=> (and (= x 0) (= y 0)) (A x y))))",
      f"(assert (forall ((x Int)(y Int)) (=> (A x y) (A (+ x {aa}) (+ y {bb})))))",
      f"(assert (forall ((x Int)(y Int)) (=> (A x y) (B (+ x {pp}) (+ y {qq})))))",
      f"(assert (forall ((x Int)(y Int)) (=> (B x y) (B (+ x {aa}) (+ y {bb})))))",
      f"(assert (forall ((x Int)(y Int)) (=> (and (B x y) (= y {qq}) (not (= x {pp}))) false)))",
    ]
    return "(set-logic HORN)\n(declare-fun A (Int Int) Bool)\n(declare-fun B (Int Int) Bool)\n"+"\n".join(rules)+"\n(check-sat)\n"

class FrozenTransferControls(unittest.TestCase):
    def test_replays_exact_trained_shape(self):
        raw=authored_fixture(2,3,4,-2)
        info, names, originals=g.extract_exact(raw)
        self.assertEqual(info,(2,3,4,-2))
        self.assertEqual(names,("A","B"))
        coeff=g.frozen_coefficients(*info)
        self.assertEqual(coeff,[-3,2,-3,2,-16])
        self.assertEqual(g.check_original(originals,names,coeff),["unsat"]*5)
    def test_new_goal_rejected(self):
        raw=authored_fixture(2,3,4,-2).replace("(not (= x 4))","(not (= x 5))")
        with self.assertRaises(g.Unsupported):
            g.extract_exact(raw)
    def test_new_rule_rejected(self):
        raw=authored_fixture(2,3,4,-2).replace("(check-sat)","(assert true)\n(check-sat)")
        with self.assertRaises(g.Unsupported):
            g.extract_exact(raw)
    def test_nonlinear_step_rejected(self):
        raw=authored_fixture(2,3,4,-2).replace("(=> (A x y) (A (+ x 2) (+ y 3)))",
                                                     "(=> (A x y) (A (* x x) (+ y 3)))")
        with self.assertRaises(g.Unsupported):
            g.extract_exact(raw)
if __name__=="__main__":
    unittest.main()
