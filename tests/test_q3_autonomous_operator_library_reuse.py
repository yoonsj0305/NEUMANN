"""Q3 actual reusable program invention, not just one-task AST generation."""
import unittest

from research.q3.autonomous_operator_library_reuse import (
    AntiUnifier,bind_pattern,substitute,invent_library_from_programs,
    compile_as_executable, LearnedLibrary,
    infer_bindings_using_only_target_train, semantic_interface_of_frozen_library,
    ablate_learned_parameter,
)


class ReusableDiscoveryTests(unittest.TestCase):
    def test_abstraction_discovers_new_parameters_without_named_holes(self):
        # Arbitrary typed program shapes; the anti-unifier does not know
        # the term vocabulary or its semantics.
        a=["Apply",["Partition","columns",4,1],
                   ["MergeLaw",[["blue","green"],["green","red"]]]]
        b=["Apply",["Partition","rows",5,0],
                   ["MergeLaw",[["red","yellow"],["green","yellow"],
                                ["yellow","blue"]]]]
        lib,one,two=invent_library_from_programs(a,b)
        self.assertTrue(lib.name.startswith("invented_library_"))
        self.assertNotIn("TARGET",str(lib.to_ast()))
        self.assertGreaterEqual(len(lib.parameters),4)
        self.assertEqual(substitute(lib.body,one),a)
        self.assertEqual(substitute(lib.body,two),b)
        self.assertEqual(bind_pattern(lib.body,a),one)
        self.assertEqual(bind_pattern(lib.body,b),two)

    def test_abstraction_rejects_completely_unrelated_programs(self):
        with self.assertRaisesRegex(RuntimeError,
                                    "TRIVIAL_WHOLE_PROGRAM_ABSTRACTION"):
            invent_library_from_programs(["A",1],["B",2,3])

    def test_stable_library_semantics_not_target_id_routing(self):
        a=["Top",["Prefix",1],["Priority",[[1,2]]]]
        b=["Top",["Prefix",2],["Priority",[[1,3],[2,3]]]]
        x,_,_=invent_library_from_programs(a,b)
        y,_,_=invent_library_from_programs(a,b)
        self.assertEqual(x.to_data(),y.to_data())

    def test_old_program_resolver_is_not_called_by_library_transfer(self):
        import inspect
        source=inspect.getsource(infer_bindings_using_only_target_train)
        self.assertNotIn("train_invention(",source)
        # Forbidden fallback: a malformed/invented-but-inapplicable library
        # must reject every target, even if the old direct resolver might fit.
        bad=LearnedLibrary("not_a_law",["Keep"],("p0",),("src1","src2"))
        self.assertIsNone(semantic_interface_of_frozen_library(bad))
        train=[{"input":[[1,2]],"output":[[2]]}]
        self.assertEqual(infer_bindings_using_only_target_train(bad,train),[])

    def test_removing_a_learned_operator_parameter_restores_source_constraint(self):
        a=["A",["step","columns",3],["branch",[[1,2],[2,3]]]]
        b=["A",["step","rows",4],["branch",[[4,5]]]]
        lib,ba,bb=invent_library_from_programs(a,b)
        self.assertGreaterEqual(len(lib.parameters),3)
        slot=lib.parameters[0]
        changed=ablate_learned_parameter(lib,slot,ba[slot])
        self.assertEqual(len(changed.parameters),len(lib.parameters)-1)
        self.assertEqual(substitute(changed.body,{
            k:ba[k] for k in changed.parameters}),a)
        self.assertIsNone(bind_pattern(changed.body,b))

    def test_malformed_program_compiler_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"NOT_COMPILED"):
            compile_as_executable(["CopySource",5])


if __name__=="__main__":
    unittest.main()
