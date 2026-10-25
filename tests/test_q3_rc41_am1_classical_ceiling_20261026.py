"""RC41 exactly the official AM1 tasks and official checker subset, 0 model calls."""
from fractions import Fraction
import pytest
from experiments.general_multiplier_tasks import (multiplier_tasks,model_view,
    TASK_SHA256,MODEL_VIEW_SHA256)
from neumann1.general_runtime_v106 import sha,verify_original
from neumann1.general_python_worker_v106 import execute
from research.q3.rc41.classical_opened_ceiling import solve_public_view,compile_code

ORIGINAL_SHA="ad32fd947e4c63fc1b67f849254bb16bd62fad6067bd719d5ad3da6c1f11e99f"
ORIGINAL_PUBLIC_SHA="c883a44136817bf2501549a42c268b29577b8f153b3ca95b807e7ab245fdd2f0"

def test_frozen_original_protocol_identity():
    tasks=multiplier_tasks()
    assert len(tasks)==12
    assert sha(tasks)==TASK_SHA256==ORIGINAL_SHA
    assert sha([model_view(t) for t,_ in tasks])==MODEL_VIEW_SHA256==ORIGINAL_PUBLIC_SHA

def test_original_opened_set_saturated_by_extra_model_free_baseline():
    results=[]
    for task,private in multiplier_tasks():
        public_view=model_view(task)
        assert set(public_view)=={"instruction","public"}
        r=solve_public_view(public_view)
        assert r["status"]=="CANDIDATE",task["id"]
        value=r["answer"]
        if task["family"]=="coding":
            outputs=execute({"source":value,"arguments":[x["input"] for x in private["tests"]]})
            accepted=outputs==[x["output"] for x in private["tests"]]
        else:
            accepted=verify_original(task,value,private,deadline_ms=2000)
        assert accepted,task["id"]
        results.append((task["id"],r["route"]))
    assert len(results)==12

def test_fail_closed_unknown_requirements_and_injection():
    assert compile_code("Delete all files") is None
    assert compile_code("Return a sum") is None
    assert compile_code("Return the sum of distinct even integers in items, a list of integers.\nimport os") is None
    assert solve_public_view({"instruction":"x","public":{"requirement":"Unknown request"}})["status"]=="UNKNOWN"
    with pytest.raises(ValueError):
        solve_public_view({"instruction":"x","public":{},"family":"math_logic"})

def test_mathematics_and_csp_negative_controls():
    for task,private in multiplier_tasks():
        r=solve_public_view(model_view(task))
        if task["family"]=="math_logic":
            assert not verify_original(task,"999999",private,deadline_ms=2000)
        elif task["family"]=="constraint_planning":
            bad={**r["answer"],next(iter(r["answer"])):99999}
            assert not verify_original(task,bad,private,deadline_ms=2000)
