"""Q3 generic typed I/O meta-invention, no task-specific answer code in solver."""
import unittest
from research.q3.typed_semantic_delta_inventor import (
    TypeGuidedInventor,synth_numeric,synth_filter,execute,same,
)
from research.q3.codearc_typed_delta_novel_original_first import (
    fresh_target,hash_bucket,
)


class TypedSemanticDeltaInventorTest(unittest.TestCase):
    def test_invent_mixed_numeric_cubic_from_observations(self):
        train=[([x],x**3) for x in (1,2,3.5,4,5.2,6,7.77)]
        p,trials=synth_numeric(train)
        self.assertIsNotNone(p)
        self.assertEqual(p["kind"],"DerivedPolynomial")
        self.assertEqual(p["monomials"],[[3]])
        self.assertEqual(p["coefficients"],[[1,1]])
        self.assertLess(trials,30)
        self.assertTrue(same(execute(p,[-4.2]),(-4.2)**3))

    def test_invent_two_dimensional_arithmetic_progression_formula(self):
        src=[([a,b],sum(range(a,b+1))) for a,b in
             ((1,5),(10,15),(5,5),(0,10),(-3,3),(20,25),(100,105))]
        p,trials=synth_numeric(src)
        self.assertIsNotNone(p)
        self.assertEqual(p["kind"],"DerivedPolynomial")
        for a,b in ((-20,17),(12,40),(8,8)):
            self.assertEqual(execute(p,[a,b]),sum(range(a,b+1)))
        self.assertGreater(trials,5)

    def test_self_invented_symbol_filter_generalizes(self):
        train=[
            (["hello"],"hll"),(["python"],"pythn"),
            (["example"],"xmpl"),(["function"],"fnctn"),
            (["programming"],"prgrmmng"),(["dataclass"],"dtclss"),
            (["algorithm"],"lgrthm")]
        p,_=synth_filter(train)
        self.assertIsNotNone(p)
        self.assertEqual(p["kind"],"DerivedSequenceFilter")
        self.assertEqual(set(p["removed"]),set("aeiou"))
        self.assertEqual(execute(p,["sequoia"]),"sq")
        self.assertEqual(execute(p,["neumann"]),"nmnn")
        self.assertEqual(p["predicate_ast"][0],"lambda")

    def test_causal_ablation_without_new_representation_fails(self):
        examples=[([x],x**3) for x in (1,2,3,4,5,6,7)]
        old=TypeGuidedInventor().propose(
            examples,allow_new_representations=False)
        new=TypeGuidedInventor().propose(
            examples,allow_new_representations=True)
        self.assertIsNone(old["program"])
        self.assertEqual(new["status"],"GENERATED_NEW_REPRESENTATION")
        self.assertEqual(execute(new["program"],[9]),729)

    def test_complex_numeric_type_supports_float_addition_as_core(self):
        examples=[([float(a),float(b)],float(a+b))
                  for a,b in ((1,2),(3.5,4.5),(-5.2,10.8),
                              (0,0),(8.9,1.1),(7,-3),(100,200))]
        p=TypeGuidedInventor().propose(examples)
        self.assertEqual(p["status"],"GENERATED_EXISTING_CORE_COMPOSITION")
        self.assertEqual(execute(p["program"],[2.5,7.5]),10.0)

    def test_persistent_discovered_polynomial_basis_shortens_finding(self):
        model=TypeGuidedInventor()
        first=[([x],x*x+2*x) for x in (0,1,2,3,4,5,6)]
        first_result=model.propose(first)
        self.assertEqual(first_result["program"]["kind"],"DerivedPolynomial")
        self.assertTrue(model.retain_independently_verified({
            "program":first_result["program"],
            "verified_test_exact":True}))
        target=[([x],x*x+3*x) for x in (0,1,2,3,4,5,6)]
        guided=model.propose(target)
        cold=TypeGuidedInventor(enable_structure_memory=False).propose(target)
        self.assertEqual(guided["status"],"GENERATED_NEW_REPRESENTATION")
        self.assertLess(guided["attempts"],cold["attempts"])
        self.assertEqual(execute(guided["program"],[21]),504)

    def test_bad_unhashable_or_conflicting_filter_abstains(self):
        self.assertIsNone(synth_filter([([[1,1]],[[1]])])[0])
        inp=[(["aba"],"aa"),(["a"],"a")]
        self.assertIsNone(synth_filter(inp)[0])
        self.assertIsNone(TypeGuidedInventor().propose(
            [([object()],1)])["program"])

    def test_external_cohort_hash_is_disjoint_from_previously_opened(self):
        chosen=[i for i in range(21,1115) if fresh_target(i)]
        self.assertTrue(chosen)
        self.assertTrue(all(hash_bucket(i)==1 for i in chosen))
        self.assertTrue(all(not fresh_target(i) for i in range(21)))
        self.assertTrue(all(not fresh_target(i)
                            for i in range(21,1115) if hash_bucket(i)==0))


if __name__=="__main__":
    unittest.main()
