"""G0 exact-reframe tests use synthetic controls only, never original benchmark bodies."""
import unittest
try:
    import z3
except ModuleNotFoundError:
    # Mainline CI does not install optional research solver extras.
    # This module is required, not skipped, in the pinned G0 original workflow,
    # which installs the exact z3-solver version before running all 8 tests.
    raise unittest.SkipTest("optional z3-solver absent; dedicated G0 CI ran eight controls")
from research.q3.g0_exact_bounded_reframe import (
  choose_finite_split,literal_bounds,nonlinear_variables,
  validate_exact_model,z3_check
)


class ExactBoundedReframeControls(unittest.TestCase):
    def test_explicit_complete_conjunctive_bounds(self):
        x,y=z3.Ints("x y")
        a=[x>=0,x<=2,x*y==6]
        chosen,n=choose_finite_split(a,3,64)
        self.assertEqual(n,3)
        self.assertEqual([(v[0],v[2],v[3]) for v in chosen],[("x",0,2)])
        self.assertEqual(nonlinear_variables(a),{"x","y"})

    def test_disjunctive_or_conditional_bounds_not_trusted(self):
        x,y=z3.Ints("x y")
        f=[z3.Or(x>=0,x<=2),x*y==6]
        chosen,n=choose_finite_split(f,3,64)
        self.assertEqual(chosen,[])
        self.assertEqual(n,1)

    def test_out_of_range_not_accidentally_unbounded(self):
        x,y=z3.Ints("x y")
        a=[x>=0,x<=1000,x*y==3]
        chosen,n=choose_finite_split(a,3,64)
        self.assertEqual(chosen,[])

    def test_unsat_small_original_and_each_exact_branch_unsat(self):
        x,y=z3.Ints("x y")
        a=[x>=0,x<=1,y==0,x*y==3]
        chosen,n=choose_finite_split(a,3,64)
        self.assertEqual(n,2)
        for k in range(2):
            status,_,_=z3_check(a,[x==k],1)
            self.assertEqual(status,"unsat")

    def test_original_sat_witness_checked_exact(self):
        x,y=z3.Ints("x y")
        a=[x>=0,x<=2,x*y==6,y>0]
        status,model,_=z3_check(a,[x==2],1)
        self.assertEqual(status,"sat")
        ok,values=validate_exact_model(a,model)
        self.assertTrue(ok)
        self.assertEqual(values["x"]*values["y"],6)
        self.assertTrue(values["y"]>0)

    def test_noninteger_or_dangling_source_cannot_be_falsely_certified(self):
        x=z3.Int("x");r=z3.Real("r")
        status,model,_=z3_check([x==1,r==2],[],1)
        self.assertEqual(status,"sat")
        valid,_=validate_exact_model([x==1,r==2],model)
        self.assertFalse(valid)

    def test_arbitrary_new_rename_no_filenamerouting(self):
        p,q=z3.Ints("novel_state novel_multiplier")
        a=[p>=-1,p<=1,3*p*q==6]
        chosen,n=choose_finite_split(a,3,64)
        self.assertEqual(n,3)
        self.assertEqual(chosen[0][0],"novel_state")

    def test_negated_false_constraint_rejected_by_original_checker(self):
        x,y=z3.Ints("x y")
        status,model,_=z3_check([x==1,y==2],[],1)
        self.assertEqual(status,"sat")
        valid,_=validate_exact_model([x==2,y==2],model)
        self.assertFalse(valid)

if __name__=="__main__":
    unittest.main()
