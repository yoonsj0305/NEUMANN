"""Source-free dialect token controls. No real original task opened."""
import unittest
from research.g1.postfirst_official_converter_cvc5 import canonicalize_legacy_string_builtins

class LegacyOperatorControls(unittest.TestCase):
 def test_operator_tokens_only(self):
  src='(int.to.str 3) (str.to.int "42") (notint.to.str 3) (int.to.strExtra 3)'
  out,counts=canonicalize_legacy_string_builtins(src)
  self.assertEqual(out,'(str.from_int 3) (str.to_int "42") (notint.to.str 3) (int.to.strExtra 3)')
  self.assertEqual(counts,{'int.to.str':1,'str.to.int':1})
 def test_never_rewrite_strings_or_comments(self):
  src='(= "old int.to.str (str.to.int 4)" "str.to.int") ;(int.to.str 2)\n(int.to.str 45)'
  out,counts=canonicalize_legacy_string_builtins(src)
  self.assertEqual(out,'(= "old int.to.str (str.to.int 4)" "str.to.int") ;(int.to.str 2)\n(str.from_int 45)')
  self.assertEqual(counts['int.to.str'],1)
 def test_nested_grammar_and_symbol_boundary(self):
  src='((G String ((str.++ (int.to.str x) (str.to.int y)))))'
  out,counts=canonicalize_legacy_string_builtins(src)
  self.assertIn('(str.from_int x)',out)
  self.assertIn('(str.to_int y)',out)
  self.assertEqual(sum(counts.values()),2)
 def test_source_with_no_legacy_tokens_identity(self):
  src='(synth-fun f ((s String)) String ((Start String) (Start (s (str.++ Start Start)))))'
  out,counts=canonicalize_legacy_string_builtins(src)
  self.assertEqual(out,src)
  self.assertEqual(sum(counts.values()),0)
 def test_escaped_double_quotes_are_opaque(self):
  src='(= "a""(int.to.str 999)" "b") (int.to.str 7)'
  out,c=canonicalize_legacy_string_builtins(src)
  self.assertEqual(out,'(= "a""(int.to.str 999)" "b") (str.from_int 7)')
  self.assertEqual(c['int.to.str'],1)

if __name__=='__main__':
 unittest.main()
