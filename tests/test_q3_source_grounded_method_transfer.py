"""Q3 source-evidence transfer. No closed-world target solutions included."""
import pytest
from neumann1.open_program_inventor import IsolatedPython,Execution
from neumann1.q3_single_discovery_core import SourceMethodMemory,SingleDiscoveryCore
from neumann1.q3_trainable_code_policy import generation_seed

INC="def transform(x):"+chr(10)+"    return x + 1"
REV="def transform(x):"+chr(10)+"    return x[::-1]"
TRUE="def transform(x):"+chr(10)+"    return True"
FIRST="def transform(x):"+chr(10)+"    return x[0]"


def test_original_source_evidence_rejects_unrelated_hash_selected_program():
    runner=IsolatedPython(max_seconds=8)
    mem=SourceMethodMemory(runner)
    mem.admit("numeric",[(1,2),(2,3)],[(5,6)],INC)
    mem.admit("reverse",[("cat","tac"),("dog","god")],[("space","ecaps")],REV)
    mem.freeze()
    original=[(1,2),(4,5),(8,9)]
    context=mem.source_supported_context(original)
    assert INC in context
    assert REV not in context
    assert "matches 3/3" in context
    assert "constant-output baseline: 1/3" in context
    assert mem.context(max_methods=2) != context


def test_all_positive_source_is_unidentifiable_without_authorized_probe():
    runner=IsolatedPython(max_seconds=8)
    mem=SourceMethodMemory(runner)
    mem.admit("all_true",[(1,True),(2,True)],[(3,True)],TRUE)
    mem.freeze()
    original=[(x,True) for x in (5,6,7,8,9,10)]
    # A memorized True program DOES NOT outperform constant-True on SOURCE:
    # no proof of a causal decision boundary, so inject no old method.
    assert mem.source_supported_context(original)==""


def test_partial_old_method_receives_executable_counterexample():
    runner=IsolatedPython(max_seconds=8)
    mem=SourceMethodMemory(runner)
    mem.admit("first",[([1,2],1),([3,5],3)],[([7,9],7)],FIRST)
    mem.freeze()
    observed=[
      ([1,2],1),([3,5],3),([4,7],4),
      ([9,2],2),([7,8],7),([6,1],1)]
    context=mem.source_supported_context(observed)
    assert FIRST in context
    assert "matches 4/6" in context
    assert "constant-output baseline: 2/6" in context
    assert '"expected":2' in context
    assert '"got":9' in context
    # The true original independent SOURCE checks were not supplied at all.
    assert "private-original-gold" not in context


def test_missing_runner_or_errored_program_cannot_be_proposed_as_verified_transfer():
    class NoSandbox:
        def evaluate(self,program,inputs):
            return Execution("ABSTAIN_NO_SANDBOX",(),0)
    no=SourceMethodMemory(NoSandbox())
    # SourceMethodMemory admission requires actual execution; use Docker for
    # admission, then swap runner only to prove retrieval fails closed.
    yes=SourceMethodMemory(IsolatedPython(max_seconds=8))
    yes.admit("inc",[(1,2),(3,4)],[(5,6)],INC)
    yes.freeze()
    yes.runner=NoSandbox()
    assert yes.source_supported_context([(8,9),(9,10)])==""


def test_matched_sampling_equal_across_different_method_context_text():
    assert generation_seed(1007,"no memory",paired_sampling=True)==1007
    assert generation_seed(1007,"unrelated memory",paired_sampling=True)==1007
    assert generation_seed(1007,"no memory") != generation_seed(
        1007,"unrelated memory")
    assert generation_seed(-2,"any",paired_sampling=True)==(2**31-2)


def test_generic_core_excludes_irrelevant_memory_not_family_routed():
    class StaticPolicy:
        def __init__(self):self.prompts=[]
        def propose(self,prompt):
            self.prompts.append(prompt)
            return INC
    runner=IsolatedPython(max_seconds=8)
    mem=SourceMethodMemory(runner)
    mem.admit("num",[(1,2),(2,3)],[(5,6)],INC)
    mem.admit("text",[("abc","cba"),("dog","god")],[("cat","tac")],REV)
    mem.freeze()
    policy=StaticPolicy()
    core=SingleDiscoveryCore(policy,runner,memory=mem,max_proposals=1)
    result=core.discover(
        [(2,3),(3,4)],[(7,8)],reuse_memory=True,
        memory_mode="source_grounded")
    assert result.discovery.verified
    assert INC in policy.prompts[-1]
    assert REV not in policy.prompts[-1]
    with pytest.raises(ValueError,match="memory"):
        core.discover([(2,3)],[(7,8)],reuse_memory=True,
                      memory_mode="hidden_human_domain")
