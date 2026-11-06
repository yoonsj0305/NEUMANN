"""Postfirst semantic dependency is coefficient-based, never lexical."""
import unittest

from research.q3.affine_semantic_dependency import dependency


def src(index=None):
    return ['select', 'S', index or ['add', ['var', 'b'], ['var', 'i']]]


class AffineInfluenceTests(unittest.TestCase):
    def test_semantically_cancelled_reads_are_independent(self):
        for expr in (
            ['add', src(), ['neg', src()]],
            ['mul', ['const', 0], src()],
            ['add', ['mul', ['const', 2], src()], ['neg', ['mul', ['const', 2], src()]]],
            ['add', ['const', 7], ['mul', ['const', 0], src()]]
        ):
            with self.subTest(expr=expr):
                self.assertEqual(dependency(expr)['verdict'], 'SOURCE_INDEPENDENT')

    def test_real_source_influence_is_preserved(self):
        for expr in (src(), ['add', src(), ['const', 1]],
                     ['mul', ['const', 2], src()]):
            self.assertEqual(dependency(expr)['verdict'], 'SOURCE_DEPENDENT')

    def test_commutative_index_forms_cancel(self):
        s0 = src(['add', ['var', 'b'], ['var', 'i']])
        s1 = src(['add', ['var', 'i'], ['var', 'b']])
        self.assertEqual(dependency(['add', s0, ['neg', s1]])['verdict'],
                         'SOURCE_INDEPENDENT')

    def test_unknown_non_affine_is_not_a_proof(self):
        expr = ['mul', ['var', 'b'], src()]
        self.assertEqual(dependency(expr)['verdict'], 'UNKNOWN_UNSUPPORTED')
        nested = src(['select', 'S', ['var', 'i']])
        self.assertEqual(dependency(nested)['verdict'], 'UNKNOWN_UNSUPPORTED')

    def test_malformed_constants_fail_closed(self):
        self.assertEqual(dependency(['const', True])['verdict'], 'UNKNOWN_UNSUPPORTED')


if __name__ == '__main__':
    unittest.main()
