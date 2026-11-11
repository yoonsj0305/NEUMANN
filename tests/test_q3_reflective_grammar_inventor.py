"""Q3 self-extending grammar, causality, persistence, and conservative failure."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research.q3.reflective_grammar_inventor import MetaLanguage,exec_safe
from research.q3.reflective_grammar_experiment import freeze_source,learn_target_set


class Q3ReflectiveGrammarTests(unittest.TestCase):
    def test_induced_meta_grammar_is_not_preloaded(self):
        learner=MetaLanguage.empty()
        self.assertEqual(len(learner.productions),0)
        names=[]
        for k in (1,2):
            result=learner.solve([(x,x*x+k) for x in range(7)],budget=2)
            self.assertIsNotNone(result)
            names.append(result['symbol'])
        production=learner.invent_production(*names)
        self.assertIsNotNone(production)
        self.assertEqual(len(learner.productions),1)
        self.assertEqual(production['sources'],names)
        self.assertIn('hole',str(production['template']))

    def test_new_syntax_compiles_real_function_from_original_examples(self):
        learner=MetaLanguage.empty()
        src=[]
        for k in (1,2):
            src.append(learner.solve([(x,x*x+k) for x in range(7)],budget=2)['symbol'])
        p=learner.invent_production(*src)
        result=learner.solve([(x,x*x+5) for x in range(8)],budget=1)
        self.assertIsNotNone(result)
        self.assertEqual(result['mechanism'],'self_invented_grammar')
        self.assertEqual(result['production'],p['symbol'])
        for x in (-23,-1,11,27):
            success,v=exec_safe(['call',result['symbol'],['arg']],x,learner.defs)
            self.assertTrue(success)
            self.assertEqual(v,x*x+5)

    def test_self_invented_language_round_trip_and_growth(self):
        with TemporaryDirectory() as tmp:
            source,_=freeze_source(Path(tmp))
            self.assertEqual(len(source['productions']),5)
            reloaded=MetaLanguage.load(source)
            self.assertEqual(reloaded.source_only_json(),source)
            grown,results=learn_target_set(source)
            self.assertEqual(len(results),6)
            self.assertEqual(sum(r['heldout_exact'] for r in results),214)
            self.assertTrue(all(r['result']=='EXACT' for r in results))
            self.assertTrue(all(r['mechanism']=='self_invented_grammar' for r in results))
            self.assertTrue(all(not r['source_grammar_ablation_solved'] for r in results))
            self.assertEqual(len(source['defs']),12)
            self.assertEqual(len(grown.defs),18)

    def test_out_of_language_family_abstains_without_improvised_primitive(self):
        with TemporaryDirectory() as tmp:
            source,_=freeze_source(Path(tmp))
            reloaded=MetaLanguage.load(source)
            # Prefix sums require a scan/fold not present in this source core.
            train=[([1,2,3],[1,3,6]),([2,4,1],[2,6,7]),([3,1,2],[3,4,6])]
            self.assertIsNone(reloaded.solve(train,allow_core_lifting=False))

    def test_safe_vm_rejects_undefined_programs(self):
        success,v=exec_safe(['exec','arbitrary Python code'],3,{})
        self.assertFalse(success)
        with self.assertRaisesRegex(ValueError,'UNVERIFIED_DEFINITION'):
            MetaLanguage.empty().define(['lit',10],[(1,99)],'forged')
        self.assertEqual(MetaLanguage.empty().productions,[])

    def test_unrelated_macro_structures_dont_invent_spurious_rules(self):
        grammar=MetaLanguage.empty()
        a=grammar.define(['op','add',['arg'],['lit',1]],[(1,2),(4,5)],'source')
        b=grammar.define(['op','mul',['arg'],['lit',2]],[(1,2),(4,8)],'source')
        self.assertIsNone(grammar.invent_production(a,b))


if __name__=='__main__':
    unittest.main()
