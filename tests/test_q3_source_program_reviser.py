"""Q3 causal program minimization regression from exposed CodeARC original 447.

This is SOURCE development only; it cannot be counted as a new original Q6
capability. A simpler algorithm preserving all source labels is preferred
over a spurious shape-dependent branch. Docker sandbox remains mandatory.
"""
import pytest

from neumann1.open_program_inventor import Attempt, IsolatedPython
from neumann1.source_program_reviser import (
    SourcePolicyLearner,SourceProgramReviser)


def test_remove_spurious_condition_from_prior_original_447_source():
    source=[
        ([10,1],10),([5,4],5),([20,7],20),
        ([15,10],15),([30,2],30),([25,12],25),
    ]
    independent=[([8,6],8)]
    suspicious=(
        "def transform(x):\n"
        "    return x[0] if len(x) == 2 else x[0] + x[1]")
    attempt=Attempt("old-source-sha",6,6,"EXECUTED",0,suspicious)
    runner=IsolatedPython(max_seconds=12)
    learned=SourcePolicyLearner(adapt=True)
    result=SourceProgramReviser(
        runner,policy=learned,max_source_evals=32).repair(
            (attempt,),source,
            independent_source_checks=independent)
    assert result.status=="SOURCE_VERIFIED_REPAIRED_PROGRAM",result
    assert result.action=="drop_condition_true",result
    assert result.program=="def transform(x):\n    return x[0]"
    check=runner.evaluate(result.program,[[7,3,100],[5,12,17,2]])
    assert check.status=="EXECUTED"
    assert check.outputs==(7,5)
    assert learned.updates>0


def test_source_and_disjoint_verifier_are_mandatory():
    runner=IsolatedPython()
    rev=SourceProgramReviser(runner)
    with pytest.raises(ValueError,match="disjoint"):
        rev.repair(
            (Attempt("h",1,1,"EXECUTED",0,
                     "def transform(x):\n    return x"),),
            [(3,3)],independent_source_checks=[(3,3)])


def test_runtime_absence_abstains_no_python_exec(monkeypatch):
    monkeypatch.setattr(
        "neumann1.open_program_inventor.shutil.which",lambda name:None)
    runner=IsolatedPython()
    rev=SourceProgramReviser(runner,max_source_evals=16)
    trial=rev.repair(
        (Attempt("x",1,1,"EXECUTED",0,
                 "def transform(x):\n    return x"),),
        [([1],[1])],
        independent_source_checks=[([2],[2])])
    assert trial.program is None
    assert trial.status.startswith("ABSTAIN")
