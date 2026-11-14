"""Software contract only. Real ARC ORIGINAL evaluation is separate."""
import unittest
from research.q3.learned_pixel_logic_ast_original import (
    FEATURE_NAMES,build_features,learn_ast,execute,count_nodes,KEEP
)


class LearnedRuleASTSoftwareContract(unittest.TestCase):
    def test_train_emits_variable_executable_AST_not_pre_authored_macro(self):
        a=[[0,1,0],[0,0,0],[0,1,0]]
        b=[[0,8,0],[0,0,0],[0,8,0]]
        train=[{"input":a,"output":b},{"input":[[1,0,1],[0,0,0],[1,0,1]],
        "output":[[8,0,8],[0,0,0],[8,0,8]]}]
        model=learn_ast(train,max_depth=5)
        self.assertEqual(model["status"],"EXECUTABLE_LEARNED_OPERATOR_AST")
        self.assertGreater(model["gradient_update_steps"],0)
        self.assertNotEqual(model["initial_weight_sha256"],model["trained_weight_sha256"])
        self.assertGreater(model["learned_nodes"],1)
        self.assertEqual(execute(model["ast"],a),b)
    def test_generic_non_target_features_count_matches(self):
        feats=build_features([[0,2],[4,6]])
        self.assertEqual(len(feats),4)
        self.assertEqual(len(feats[0]),len(FEATURE_NAMES))
        self.assertIn("color_bbox_xmin_delta_4",FEATURE_NAMES)
        self.assertEqual(KEEP,-1)
    def test_invalid_color_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_COLOR"):
            build_features([[55]])
    def test_constant_keep_generated_operator(self):
        self.assertEqual(execute(["Keep"],[[1,2],[3,4]]),[[1,2],[3,4]])

if __name__=="__main__":
    unittest.main()
