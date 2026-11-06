"""G0 exact semantic operator controls; ONLY synthetic test ASTs, no original source."""
import unittest
import z3
from research.g0.exact_bounded_bilinear_first import (
    source_bounded_integer_symbols, BoundedProductCompiler,
    exact_finite_multiplier, git_blob
)

class ExactBoundedIntegerProducts(unittest.TestCase):
    def test_conditional_equivalence_for_arbitrary_source_range(self):
        x,y=z3.Ints("test_x test_y")
        for L,U in [(-1,1),(0,1),(-4,-1),(2,5),(-3,4)]:
            expression=exact_finite_multiplier(x,y,L,U)
            s=z3.Solver()
            s.add(x>=L,x<=U,x*y!=expression)
            self.assertEqual(s.check(),z3.unsat,(L,U))

    def test_only_unconditionally_asserted_bounds_available(self):
        x,y=z3.Ints("test_x test_y")
        root=[x>=-1,x<=1,z3.Or(x*y==7,x*y==8)]
        d=source_bounded_integer_symbols(root,8)
        self.assertEqual(d,{"test_x":(-1,1)})
        cc=BoundedProductCompiler(d,100)
        out=[cc.rewrite(a) for a in root]
        self.assertEqual(cc.replacements,1)
        s=z3.Solver()
        s.add(x>=-1,x<=1,z3.Xor(z3.And(*root),z3.And(*out)))
        self.assertEqual(s.check(),z3.unsat)

    def test_or_conditional_bounds_cannot_leak(self):
        x,y=z3.Ints("test_x test_y")
        root=[z3.Or(z3.And(x>=-1,x<=1),y==9),x*y==7]
        bounds=source_bounded_integer_symbols(root,8)
        self.assertNotIn("test_x",bounds)
        cc=BoundedProductCompiler(bounds,100)
        out=[cc.rewrite(a) for a in root]
        self.assertEqual(cc.replacements,0)
        s=z3.Solver();s.add(z3.Xor(z3.And(*root),z3.And(*out)))
        self.assertEqual(s.check(),z3.unsat)

    def test_missing_one_bound_is_not_eligible(self):
        x,y=z3.Ints("test_x test_y")
        self.assertEqual(source_bounded_integer_symbols([x<=1,x*y==2],8),{})

    def test_large_range_not_unrolled(self):
        x,y=z3.Ints("test_x test_y")
        bounds=source_bounded_integer_symbols([x>=-30,x<=30,x*y==1],8)
        self.assertEqual(bounds,{})

    def test_multi_variable_multiplication_is_only_soundly_partial(self):
        x,y,z=z3.Ints("test_x test_y test_z")
        source=[x>=-1,x<=1,x*y*z==z]
        cc=BoundedProductCompiler(source_bounded_integer_symbols(source,8),100)
        out=[cc.rewrite(a) for a in source]
        self.assertEqual(cc.replacements,1)
        s=z3.Solver()
        s.add(z3.Xor(z3.And(*source),z3.And(*out)))
        self.assertEqual(s.check(),z3.unsat)

    def test_single_syntactic_factor_no_double_count(self):
        x,y=z3.Ints("test_x test_y")
        source=[x>=-1,x<=1,x*y==0,x*y==1]
        cc=BoundedProductCompiler(source_bounded_integer_symbols(source,8),100)
        out=[cc.rewrite(a) for a in source]
        self.assertGreaterEqual(cc.replacements,1)
        s=z3.Solver()
        s.add(z3.Xor(z3.And(*source),z3.And(*out)))
        self.assertEqual(s.check(),z3.unsat)

    def test_fail_closed_rewrite_cap(self):
        a,b,c=z3.Ints("test_a test_b test_c")
        source=[a>=-1,a<=1,a*b==0,a*c==0]
        cc=BoundedProductCompiler(source_bounded_integer_symbols(source,8),1)
        with self.assertRaisesRegex(ValueError,"CAP"):
            [cc.rewrite(f) for f in source]

    def test_git_source_blob_hash(self):
        self.assertEqual(git_blob(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

if __name__=="__main__":
    unittest.main()
