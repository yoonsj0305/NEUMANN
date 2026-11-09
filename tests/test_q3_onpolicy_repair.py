"""On-policy Q3 learning contracts. Real isolated SOURCE execution only.

These checks establish that model-created failure, not AST mutation or
target answer, supplies the negative hypothesis. Not evidence of Q3 PASS.
"""
import hashlib
import json
import pytest

from neumann1.q3_trainable_code_policy import certified_source_memory
from neumann1.q3_onpolicy_repair import (
    SCHEMA,collect_onpolicy_episodes,verify_onpolicy_episodes,
    source_error_witness)
from neumann1.open_program_inventor import (
    IsolatedPython,Execution,UnsafeProposal)

INC="def transform(x):"+chr(10)+"    return x + 1"
REV="def transform(x):"+chr(10)+"    return x[::-1]"
FAKE_WRONG="def transform(x):"+chr(10)+"    return x"


def teacher(pid,program,pairs):
    return {
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "provenance":"ORIGINAL_SOURCE_ONLY",
        "original_id":pid,"program":program,"pairs":pairs,
        "independent_checks":1,
        "sha256":hashlib.sha256(program.encode()).hexdigest()}


def sources():
    return [
        teacher(7,INC,[[x,x+1] for x in (1,2,3,4,5,6,7)]),
        teacher(8,REV,[[x,x[::-1]] for x in (
            "alpha","bravo","charlie","delta","echo","foxtrot","golf")]),
    ]


class ActuallyGeneratedModel:
    seed=1007
    def __init__(self,program=FAKE_WRONG):
        self.program=program
        self.prompts=[]
    def propose(self,prompt):
        self.prompts.append(prompt)
        return self.program


def test_real_docker_source_negative_origin_and_correct_method_recertification():
    runner=IsolatedPython(max_seconds=8)
    rows=sources()
    memory=certified_source_memory(rows,runner=runner)
    model=ActuallyGeneratedModel()
    negatives=collect_onpolicy_episodes(
        rows,memory,runner,model,max_per_teacher=1)
    assert len(negatives)==2
    assert len(model.prompts)==2
    assert set(x["original_source_id"] for x in negatives)=={
        "source-teacher/7","source-teacher/8"}
    assert {x["failed_program"] for x in negatives}=={FAKE_WRONG}
    assert all(x["schema"]==SCHEMA for x in negatives)
    assert all(x["provenance"]=="ACTUAL_FROZEN_MODEL_SOURCE_FAILURE"
               for x in negatives)
    assert all(x["observation"]["train_correct"]<6 for x in negatives)
    verified=verify_onpolicy_episodes(rows,memory,runner,negatives)
    assert len(verified)==2
    for x in verified:
        assert x["source_only"]
        assert FAKE_WRONG in x["prompt"]
        assert "SOURCE-ONLY REPAIR EPISODE" in x["prompt"]
        assert x["program"] not in x["prompt"]
        assert len(x["negative_sha256"])==64
        assert len(x["witness_sha256"])==64


def test_source_oracle_rejects_fabricated_failure_and_stolen_gold():
    runner=IsolatedPython(max_seconds=8)
    rows=sources()
    memory=certified_source_memory(rows,runner=runner)
    negatives=collect_onpolicy_episodes(
        rows,memory,runner,ActuallyGeneratedModel())
    invalid=json.loads(json.dumps(negatives))
    invalid[0]["observation"]["evidence"][0]["got"]="TAMPERED"
    with pytest.raises(ValueError,match="falsification"):
        verify_onpolicy_episodes(rows,memory,runner,invalid)
    invalid=json.loads(json.dumps(negatives))
    invalid[0]["correct_program_sha256"]="0"*64
    with pytest.raises(ValueError,match="SHA"):
        verify_onpolicy_episodes(rows,memory,runner,invalid)
    invalid=json.loads(json.dumps(negatives))
    invalid[0]["provenance"]="SYNTHETIC_AST_MUTATION"
    with pytest.raises(ValueError,match="provenance"):
        verify_onpolicy_episodes(rows,memory,runner,invalid)


def test_verified_solution_is_not_mislabeled_as_model_failure():
    runner=IsolatedPython(max_seconds=8)
    rows=sources()
    memory=certified_source_memory(rows,runner=runner)
    class ExactTeacherModel:
        seed=1007
        def propose(self,prompt):
            return INC if "Source input: 1" in prompt else REV
    negatives=collect_onpolicy_episodes(
        rows,memory,runner,ExactTeacherModel())
    assert negatives==[]


def test_real_independent_source_only_boundary_is_reproduced():
    runner=IsolatedPython(max_seconds=8)
    program="def transform(x):"+chr(10)+"    return min(x)"
    sorted_pairs=[[[x,x+1],x] for x in range(1,7)]
    row=teacher(12,program,sorted_pairs+[[[8,1],1]])
    memory=certified_source_memory([row],runner=runner)
    failed="def transform(x):"+chr(10)+"    return x[0]"
    witness=source_error_witness(failed,row,runner)
    assert witness["kind"]=="independent_source"
    assert witness["train_correct"]==6
    assert witness["independent_correct"]==0
    assert witness["evidence"][0]["source_expected"]==1
    assert witness["evidence"][0]["previous_observed"]==8


def test_fail_closed_if_original_source_runner_unavailable():
    class NoSandbox:
        def evaluate(self,code,inputs):
            return Execution("ABSTAIN_NO_SANDBOX",(),0)
    runner=IsolatedPython(max_seconds=8)
    rows=sources()
    memory=certified_source_memory(rows,runner=runner)
    assert collect_onpolicy_episodes(
        rows,memory,NoSandbox(),ActuallyGeneratedModel())==[]
