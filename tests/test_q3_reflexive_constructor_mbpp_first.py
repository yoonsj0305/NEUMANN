"""Pre-external causal controls for Q3 reflective constructor source-to-target."""
import tempfile
import json
import unittest
from pathlib import Path

from research.q3.reflexive_constructor_from_experience import (
    fit_sources,construct,execute_safe
)
from research.q3.learn_constructor_then_mbpp_original_first import (
    parse_one_assertion,run_mbpp
)

def hist(pid,deleted,examples):
    return {"id":pid,"verified_program":{
        "kind":"DerivedSequenceFilter","source_arg":0,
        "removed":deleted},
        "train_io":[([x],y) for x,y in examples]}

SOURCES=[
    hist(834,["!"],[("a!b","ab"),("h!i!!","hi"),("b! c!","b c")]),
    hist(841,[" "],[("a b","ab"),("a b c","abc"),(" hello ","hello")])
]

class Q3MetaConstructorTests(unittest.TestCase):
    def test_learns_executable_program_constructor_from_prior_solutions(self):
        learned,audits=fit_sources(SOURCES)
        self.assertEqual(learned["kind"],"DefineRepresentationConstructor")
        self.assertEqual(learned["constructor_program"]["hole_count"],1)
        self.assertEqual(learned["source_programs"],[834,841])
        binder=learned["constructor_program"]["parameter_binder"]
        self.assertEqual(binder[0],"minus")
        self.assertTrue(len(audits)>1)

    def test_new_unseen_containers_without_handwritten_per_domain_rules(self):
        learned,_=fit_sources(SOURCES)
        # Lists and tuples were not used among the old source programs.
        for examples,newcase,expected in [
            ([([[1,0,2]],[1,2]),([[0,3,0]],[3])],[[0,4,0]],[4]),
            ([([(4,5,4)],(5,)), ([(6,4,7)],(6,7))],
             [(4,9,4)],(9,)),
        ]:
            program=construct(learned,examples)
            self.assertIsNotNone(program)
            self.assertEqual(execute_safe(program,newcase),(True,expected))

    def test_old_strong_filter_core_can_match_scope_limit(self):
        from research.q3.typed_semantic_delta_inventor import synth_filter,execute
        learned,_=fit_sources(SOURCES)
        train=[(["abc123"],"abc"),(["1b2"],"b")]
        derived=construct(learned,train)
        baseline,_=synth_filter(train)
        self.assertIsNotNone(derived)
        self.assertIsNotNone(baseline)
        self.assertEqual(execute_safe(derived,["k4m5"]), (True,"km"))
        self.assertEqual(execute(baseline,["k4m5"]),"km")
        # Do NOT claim a general accuracy improvement over this strong core.

    def test_does_not_invent_mismatched_causal_rules(self):
        learned,_=fit_sources(SOURCES)
        self.assertIsNone(construct(learned,[
            (["abc"],"cba"),(["hey"],"yeh")]))

    def test_safe_literal_parser_and_untrusted_program_code_excluded(self):
        pair=parse_one_assertion("assert f('a!b') == 'ab'")
        self.assertEqual(pair,("f",(["a!b"],"ab")))
        pair=parse_one_assertion("assert f([1,2,0]) == [1,2]")
        self.assertEqual(pair,("f",([[1,2,0]],[1,2])))
        with self.assertRaises(ValueError):
            parse_one_assertion("assert malicious(os.system('rm -rf /')) == 1")
        with self.assertRaises(ValueError):
            parse_one_assertion("assert f('abc') != 'def'")

    def test_mbpp_scoring_never_changes_learned_constructor(self):
        learned,_=fit_sources(SOURCES)
        import hashlib
        from research.q3.reflexive_constructor_from_experience import canonical
        sha=hashlib.sha256(canonical(learned).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            freeze={"schema":"neumann.q3.self-generated-constructor-external-mbpp.v1",
                    "learned_program_generator":learned,
                    "frozen_generated_constructor_sha256":sha}
            (d/"frozen.json").write_text(json.dumps(freeze))
            # The external evaluator deliberately rejects a tiny toy file:
            # a multi-hundred original corpus must be present.
            (d/"fake.json").write_text(json.dumps([
                {"task_id":25,"test_list":[
                    "assert f('a!b') == 'ab'",
                    "assert f('hi!') == 'hi'",
                    "assert f('t!t') == 'tt'"]}]))
            with self.assertRaisesRegex(ValueError,"SOURCE_DATASET_UNEXPECTED_COUNT"):
                run_mbpp(d/"fake.json",d/"frozen.json",d/"out")

if __name__=="__main__":
    unittest.main()
