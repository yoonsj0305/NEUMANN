"""Frozen semantic type cannot be changed at target evaluation time."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.q3.autonomously_invent_reusable_semantic_type import NewSemanticType
from research.q3.frozen_invented_type_transfer_arc2_new_originals import (
    load_only_frozen_operator_type
)


class FrozenExternalSemanticType(unittest.TestCase):
    def fixture(self,path):
        op=NewSemanticType("set",2,4,(
            ((0,),1),((0,2),0),((0,3),0),((2,3),0)),
            ("sourceA","sourceB"))
        parent={
            "schema":"neumann.q3.new-semantic-type-isomorphism-reuse-original.v1",
            "source_external_original_first_run":42338077481,
            "new_type_frozen_before_target_data":True,
            "newly_discovered_operator_type":op.to_json()
        }
        path.write_text(json.dumps(parent))
        return op,parent

    def test_decode_exact_frozen_program_no_new_synthesis(self):
        with TemporaryDirectory() as t:
            path=Path(t)/"frozen.json"
            original,report=self.fixture(path)
            restored=load_only_frozen_operator_type(path)
            self.assertEqual(restored.ast(),original.ast())
            self.assertEqual(restored.to_json(),original.to_json())

    def test_modification_rejected(self):
        with TemporaryDirectory() as t:
            path=Path(t)/"frozen.json"
            original,report=self.fixture(path)
            report["newly_discovered_operator_type"]["function_AST"][1]="forged"
            path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,"REGENERATED_OR_MUTATED"):
                load_only_frozen_operator_type(path)

    def test_provenance_fails_closed(self):
        with TemporaryDirectory() as t:
            path=Path(t)/"frozen.json"
            original,report=self.fixture(path)
            report["source_external_original_first_run"]=9
            path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,"ORIGIN_CODE_DRIFT"):
                load_only_frozen_operator_type(path)


if __name__=="__main__":
    unittest.main()
