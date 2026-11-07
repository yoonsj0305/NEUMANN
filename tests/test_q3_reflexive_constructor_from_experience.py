"""Q3 reflective code-constructor tests: source learned programs vs new tasks."""
import unittest
from research.q3.reflexive_constructor_from_experience import (
    compile_verified_source_filter,fit_sources,construct,
    execute_safe,meta_eval,canonical,
)

def source(identifier,chars,pairs):
    return {"id":identifier,
            "verified_program":{"kind":"DerivedSequenceFilter",
                 "source_arg":0,"removed":list(chars)},
            "train_io":[([x],y) for x,y in pairs]}

SOURCES=[
 source(834,"!",[("a!b","ab"),("!hello!","hello"),
                 ("abc!","abc"),("b!e!","be")]),
 source(841," ",[("a b","ab"),(" space here ","spacehere"),
                 (" X Y Z ","XYZ"),("a a","aa")])
]

class ReflectiveConstructorTests(unittest.TestCase):
    def test_meta_invents_executable_constructor_not_answer(self):
        learned,audit=fit_sources(SOURCES)
        self.assertEqual(learned["kind"],"DefineRepresentationConstructor")
        self.assertTrue(learned["symbol"].startswith("invented_constructor_"))
        self.assertEqual(learned["constructor_program"]["hole_count"],1)
        self.assertEqual(len(learned["source_programs"]),2)
        self.assertEqual(learned["constructor_program"]["parameter_binder"][0],"minus")
        self.assertTrue(any(all(q["source_consistency"]) for q in audit
                                if q["binder"][0]=="minus"))
        self.assertNotIn("a!b",canonical(learned))

    def test_new_target_not_in_source_and_cross_type_transfer(self):
        learned,_=fit_sources(SOURCES)
        new_train=[(["a1b2c3"],"abc"),(["9a8b"],"ab"),
                   (["z4p5q"],"zpq")]
        prog=construct(learned,new_train)
        self.assertIsNotNone(prog)
        self.assertTrue(execute_safe(prog,["x1y2z3"])[0])
        self.assertEqual(execute_safe(prog,["x1y2z3"])[1],"xyz")
        self.assertNotIn("DerivedSequenceFilter",canonical(prog))
        # The same learned high-order constructor compiles into a new list
        # function; no list-filter primitive is added to the meta language.
        num_train=[([[1,0,2,0,3]],[1,2,3]),
                   ([[0,4,0,5]],[4,5])]
        list_program=construct(learned,num_train)
        self.assertIsNotNone(list_program)
        self.assertEqual(execute_safe(list_program,[[0,6,0,7]])[1],[6,7])
        tu_train=[([(0,1,0,2)],(1,2)), ([(3,0,4)],(3,4))]
        tu_program=construct(learned,tu_train)
        self.assertIsNotNone(tu_program)
        self.assertEqual(execute_safe(tu_program,[(0,9,0)]),(True,(9,)))

    def test_negative_cases_abstain_not_hallucinate(self):
        learned,_=fit_sources(SOURCES)
        self.assertIsNone(construct(learned,[
            (["abc"],"cba"),(["hi"],"ih")]))
        # Conflicting or non-informative evidence cannot be hallucinated.
        self.assertIsNone(construct(learned,[
            (["abc"],"def"),(["abc"],"xyz")]))
        self.assertFalse(execute_safe(["exec","import os"],["a"])[0])

    def test_old_generated_programs_are_still_executable(self):
        for row in SOURCES:
            ast=compile_verified_source_filter(row["verified_program"])
            self.assertTrue(all(execute_safe(ast,args)==(True,y)
                                for args,y in row["train_io"]))

if __name__=="__main__":
    unittest.main()
