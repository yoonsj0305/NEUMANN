"""Stitch independent read-only real-corpus audit contracts, no Rust needed."""
import unittest

from research.exp2.stitch_real_transfer import (
    canonical, expand, macro_from_stdout, match, mutate_nonhole, parse, replace_macro
)


class ReadonlyStitchTransferTests(unittest.TestCase):
    def test_recursive_parse_round_trip(self):
        s = "(T (repeat (M 1 0 -0.5)) (M #0 0))"
        self.assertEqual(canonical(parse(s)), s)

    def test_one_real_upstream_documented_pilot_macro(self):
        stdout = "fn_0 (1.33x wrt orig): utility: 200 | final_cost: 604 | 1.33x | uses: 2 | body: [fn_0 arity=1: (#0 #0 #0)]"
        arity, macro = macro_from_stdout(stdout)
        self.assertEqual(arity, 1)
        trees = [parse("(foo (a a a))"), parse("(bar (b b b))")]
        for t in trees:
            rw, n = replace_macro(t, macro, arity)
            self.assertEqual(n, 1)
            self.assertEqual(expand(rw, macro, arity), t)
            self.assertNotEqual(expand(rw, mutate_nonhole(macro), arity), t)

    def test_deep_two_argument_typed_macro(self):
        pattern = parse("(T (repeat (C #0) #1) (M 1 0 0 0))")
        original = parse("(C (T (repeat (C l) 6) (M 1 0 0 0)) (T (repeat (C k) 7) (M 1 0 0 0)))")
        rw, hits = replace_macro(original, pattern, 2)
        self.assertEqual(hits, 2)
        self.assertEqual(expand(rw, pattern, 2), original)

    def test_repeated_hole_unification(self):
        p = parse("(mul #0 #0)")
        self.assertTrue(match(p, parse("(mul x x)"), {}))
        self.assertFalse(match(p, parse("(mul x y)"), {}))

    def test_malformed_macro_and_inputs_fail_closed(self):
        for bad in ("", "(a", "a )", "()"):
            with self.assertRaises(ValueError):
                parse(bad)
        for bad in ("Found 1 inventions", "body: [fn_0 arity=5: (#0 #0)]", "body: [fn_0 arity=1: (a b)]"):
            with self.assertRaises(ValueError):
                macro_from_stdout(bad)


if __name__ == "__main__":
    unittest.main()
