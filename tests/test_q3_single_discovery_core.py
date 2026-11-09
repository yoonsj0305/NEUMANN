"""Contract tests for actual single general Q3 core. Not Q3 scientific PASS."""
import hashlib
import json
import pytest

from neumann1.open_program_inventor import (
    Execution, IsolatedPython, UnsafeProposal)
from neumann1.q3_single_discovery_core import (
    SingleDiscoveryCore, SourceMethodMemory)


class StubRunner:
    """Interface-only tests; Docker-backed tests run separately below."""
    def evaluate(self, code, inputs):
        if "return x + 1" in code:
            values=tuple(x+1 for x in inputs)
        elif "return x[::-1]" in code:
            values=tuple(x[::-1] for x in inputs)
        else:
            return Execution("ABSTAIN_UNSAFE_SYNTAX", (), 0.0)
        return Execution("EXECUTED", values, 0.0, (None,)*len(inputs))


class StaticPolicy:
    def __init__(self, code):
        self.code = code
        self.prompts = []
    def propose(self, prompt):
        self.prompts.append(prompt)
        return self.code


INC="def transform(x):\n    return x + 1"
REV="def transform(x):\n    return x[::-1]"


def test_import_prior_original_source_teachers_and_reverify():
    runner=StubRunner()
    memory=SourceMethodMemory(runner)
    teacher={
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "provenance":"ORIGINAL_SOURCE_ONLY",
        "original_id":"real-original-prior",
        "pairs":[[1,2],[2,3],[3,4],[4,5]],
        "independent_checks":1,
        "program":INC,
        "sha256":hashlib.sha256(INC.encode()).hexdigest()
    }
    rows=memory.import_source_teachers([teacher])
    assert len(rows)==1
    assert memory.episodes[0].source_id=="source-teacher/real-original-prior"
    assert memory.teacher_rows()[0]["program"]==INC
    assert rows[0].program_sha256==teacher["sha256"]


def test_falsified_verifier_refused_and_failed_source_not_memorized():
    memory=SourceMethodMemory(StubRunner())
    with pytest.raises(UnsafeProposal,match="SOURCE-certified"):
        memory.admit("false","a",[(10,11)],INC)
    assert not memory.episodes


def test_duplicate_source_input_and_heldout_memory_freeze():
    memory=SourceMethodMemory(StubRunner())
    with pytest.raises(ValueError,match="disjoint"):
        memory.admit("duplicate",[(1,2)],[(1,2)],INC)
    memory.admit("prior",[(1,2)],[(2,3)],INC)
    assert memory.context(excluded_ids=("prior",))==""
    memory.freeze()
    with pytest.raises(ValueError,match="frozen"):
        memory.admit("after",[(5,6)],[(6,7)],INC)


def test_same_neural_core_reuses_certified_memory_on_unrelated_task():
    runner=StubRunner()
    mem=SourceMethodMemory(runner)
    mem.admit("prior-arithmetic",[(1,2),(2,3)],[(4,5)],INC)
    mem.freeze()
    policy=StaticPolicy(REV)
    core=SingleDiscoveryCore(policy,runner,memory=mem,max_proposals=1)
    ans=core.discover([("abcd","dcba"),("str","rts")],
                      [("cats","stac")])
    assert ans.discovery.verified
    assert ans.method_memory_count==1
    assert "Past SOURCE-certified general method" in policy.prompts[-1]
    assert "return x + 1" in policy.prompts[-1]
    assert ans.discovery.program==REV
    assert len(ans.source_context_sha256)==64
    with pytest.raises(UnsafeProposal,match="unverified"):
        core.learn_from_verified_source("holdout",[(1,2)],[(2,3)],object())


def test_same_policy_without_memory_is_A_control():
    policy=StaticPolicy(REV)
    mem=SourceMethodMemory(StubRunner())
    mem.admit("prior",[(1,2)],[(2,3)],INC)
    core=SingleDiscoveryCore(policy,StubRunner(),memory=mem,max_proposals=1)
    ans=core.discover([("abc","cba")],[("dog","god")],
                      reuse_memory=False)
    assert ans.discovery.verified
    assert ans.method_memory_count==0
    assert "Past SOURCE-certified" not in policy.prompts[-1]


def test_core_inference_does_not_accept_duplicate_source_or_check():
    core=SingleDiscoveryCore(StaticPolicy(INC),StubRunner())
    with pytest.raises(ValueError,match="disjoint"):
        core.discover([(1,2)],[(1,2)])
    with pytest.raises(ValueError,match="unique"):
        core.discover([(1,2),(1,2)],[(3,4)])


def test_real_locked_docker_two_source_types_and_learned_memory():
    """Actual verified source runs; interface test, NOT invented original work."""
    runner=IsolatedPython(max_seconds=5)
    memory=SourceMethodMemory(runner)
    prior=memory.admit("prior-increment",[(1,2),(2,3)],[(5,6)],INC)
    assert prior.program_sha256==hashlib.sha256(INC.encode()).hexdigest()
    memory.freeze()
    policy=StaticPolicy(REV)
    core=SingleDiscoveryCore(policy,runner,memory=memory,max_proposals=1)
    out=core.discover([("robot","tobor")],[("space","ecaps")])
    assert out.discovery.verified
    assert len(out.discovery.attempts)==1
    assert out.discovery.program==REV


def test_fail_closed_no_isolated_executor(monkeypatch):
    # Docker is explicitly unavailable. A program string must not become
    # an admitted method simply because a model emitted it.
    import neumann1.open_program_inventor as inventor
    monkeypatch.setattr(inventor.shutil,"which",lambda command: None)
    core=SingleDiscoveryCore(StaticPolicy(INC),IsolatedPython(),
                             max_proposals=1)
    x=core.discover([(1,2)],[(2,3)])
    assert not x.discovery.verified
    assert x.status=="ABSTAIN_NO_SOURCE_PROGRAM"
