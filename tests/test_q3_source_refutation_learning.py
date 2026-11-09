"""SOURCE-certified meta-learning from self-generated failed executable methods.

Only tests provenance and causal information flow, NOT original Q3 success.
"""
import hashlib
import json
import pytest

from neumann1.open_program_inventor import (
    IsolatedPython,validate_code,Execution)
from neumann1.q3_trainable_code_policy import certified_source_memory
from neumann1.q3_refutation_learning import source_refutation_episodes

INC="def transform(x):"+chr(10)+"    return x + 1"
REV="def transform(x):"+chr(10)+"    return x[::-1]"


def teacher(pid,code,pairs):
    return {
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "provenance":"ORIGINAL_SOURCE_ONLY",
        "original_id":pid,
        "pairs":pairs,
        "independent_checks":1,
        "program":code,
        "sha256":hashlib.sha256(code.encode()).hexdigest(),
    }


def examples():
    return [
        teacher(7,INC,[[i,i+1] for i in (1,2,3,4,5,6,9)]),
        teacher(8,REV,[[x,x[::-1]] for x in (
            "abcd","wxyz","neumann","structural","proof","open","xyz")])
    ]


def test_real_source_counterexamples_generate_code_repair_training_pairs():
    runner=IsolatedPython(max_seconds=8)
    rows=examples()
    memory=certified_source_memory(rows,runner=runner)
    episodes=source_refutation_episodes(rows,memory,runner,max_per_teacher=2)
    assert len(episodes)>=2
    origins={e["original_source_id"] for e in episodes}
    assert origins=={"source-teacher/7","source-teacher/8"}
    for e in episodes:
        assert e["source_only"] is True
        assert "SOURCE-ONLY REPAIR EPISODE" in e["prompt"]
        assert e["negative_program"] in e["prompt"]
        assert e["program"] not in e["prompt"]  # correct self program is excluded
        assert e["negative_sha256"]!=hashlib.sha256(
            e["program"].encode()).hexdigest()
        assert validate_code(e["negative_program"])
        assert "Original-semantics SOURCE feedback:" in e["prompt"]
        # Independently replay the mutant as a SOURCE hypothesis: it MUST
        # fail at least one originally observed SOURCE pair.
        relevant=rows[0] if e["original_source_id"].endswith("/7") else rows[1]
        out=runner.evaluate(
            e["negative_program"],
            [x for x,y in relevant["pairs"]])
        assert out.status in ("EXECUTED","EXECUTED_WITH_ERRORS")
        assert any(got!=y or err is not None
                   for got,err,(_,y) in zip(
                       out.outputs,out.errors,relevant["pairs"]))
        assert len(e["witness_sha256"])==64


def test_refutation_teacher_cannot_use_failed_or_missing_sandbox():
    class Unavailable:
        def evaluate(self,code,inputs):
            return Execution("ABSTAIN_NO_SANDBOX",(),0)
    rows=examples()
    memory=certified_source_memory(
        rows,runner=IsolatedPython(max_seconds=8))
    assert source_refutation_episodes(
        rows,memory,Unavailable())==[]


def test_refutation_teacher_never_sees_target_gold_sentinel():
    runner=IsolatedPython(max_seconds=8)
    rows=examples()
    memory=certified_source_memory(rows,runner=runner)
    episodes=source_refutation_episodes(rows,memory,runner)
    assert episodes
    assert "TARGET outputs are UNKNOWN" in episodes[0]["prompt"]
    assert "987654321" not in json.dumps(episodes)
