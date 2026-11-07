"""Q3 connection tests: identical typed interface, prior learned AST, cold ablation."""
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from research.q3.discover_index_relation_constructor import discover
from research.q3.connected_constructor_router import (
    ConnectedConstructorRouter,validate_memory,run_canonical,
    score_source_frozen,program_id
)
from research.q3.gp_suite_connected_router_original_first import (
    parse_pair,load_training
)


def source_cases():
    return [
        ([""],True),(["aba"],True),(["aaaaa"],True),
        (["zbcd"],False),(["xywyx"],True),
        (["1234"],False),(["3443"],True),
    ]


class ProofCarryingConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=discover(source_cases())
        assert original["status"]=="INVENTED_EXECUTABLE_RELATION",original
        cls.program=original["program"]

    def test_source_learned_representation_validates_generic_affine_bound(self):
        self.assertTrue(validate_memory(self.program))
        bad=json.loads(json.dumps(self.program))
        bad["representation_constructor"]["second_index"]=["add",["n"],["c",2]]
        self.assertFalse(validate_memory(bad))

    def test_source_frozen_reuse_avoids_reinventing_a_relation(self):
        new_train=[
            ([list("abba")],True),([list("abca")],False),
            ([list("accb")],False),([list("xyzyx")],True),
            ([list("bb")],True),([list("ax")],False),
        ]
        memory=ConnectedConstructorRouter(self.program)
        warm=memory.discover(new_train,use_memory=True)
        cold=memory.discover(new_train,use_memory=False)
        self.assertEqual(warm["status"],"SOURCE_VERIFIED_MEMORY_REUSE")
        self.assertEqual(warm["trials"][0]["candidate_attempts"],1)
        self.assertEqual(warm["program"]["origin"],"prior_verified_relation_memory")
        self.assertGreaterEqual(len(cold["trials"]),3)
        self.assertEqual(warm["selected_ast_sha256"],program_id(self.program))
        heldout=[([[1,2,1]],True),([[1,2,2]],False),
                 ([[2,3,3,2]],True)]
        self.assertTrue(score_source_frozen(warm,heldout)["exact"])

    def test_nonmatching_memory_not_forced_or_executed_as_answer(self):
        train=[
            ([[1,2,3]],6),([[2,3,4]],9),
            ([[1,1,2]],4),([[3,4,5]],12),
            ([[4,5,6]],15),
        ]
        warm=ConnectedConstructorRouter(self.program).discover(train)
        self.assertNotEqual(warm.get("program",{}).get("origin"),
                            "prior_verified_relation_memory")
        self.assertFalse(warm["trials"][0]["is_valid_train"])
        if warm.get("program") is not None:
            self.assertTrue(score_source_frozen(
                warm,[([[1,2,3,4]],10)])["exact"])

    def test_safe_original_jsonl_parser_and_data_disjoint(self):
        sample={"input1":[1,2,3],"output1":6}
        self.assertEqual(parse_pair(sample),([[1,2,3]],6))
        self.assertEqual(parse_pair({
            "input1":1,"input2":2,"output1":3}),([1,2],3))
        with self.assertRaises(ValueError):
            parse_pair({"input1":3,"output1":3,"output2":6})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            edge=root/"edge.json.gz"
            random=root/"random.json.gz"
            with gzip.open(edge,"wt",encoding="utf-8") as f:
                for v in range(12):
                    f.write(json.dumps({"input1":[v,v+1],
                                        "output1":2*v+1})+"\n")
            with gzip.open(random,"wt",encoding="utf-8") as f:
                for v in range(200,350):
                    f.write(json.dumps({"input1":[v,v+1],
                                        "output1":2*v+1})+"\n")
            train,heldout,m=load_training(edge,random)
            self.assertEqual(len(train),20)
            self.assertEqual(len(heldout),32)
            self.assertTrue(m["source_IO_original_test_disjoint"])
            self.assertFalse({json.dumps(x) for x,y in train}&
                             {json.dumps(x) for x,y in heldout})

    def test_negative_prior_memory_fails_closed(self):
        with self.assertRaises(ValueError):
            ConnectedConstructorRouter({"kind":"arbitrary_python_exec"})


if __name__=="__main__":
    unittest.main()
