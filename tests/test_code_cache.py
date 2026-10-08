import pytest

from neumann1.code_cache import ExactCodeCache


def task(prompt="def arbitrary_function(x):\n    \"\"\"Return x + 1.\"\"\"", task_id="a"):
    return {"prompt": prompt, "entry_point": "arbitrary_function", "task_id": task_id}


SOURCE = "def arbitrary_function(x):\n    return x + 1\n"


def test_full_specification_not_task_id():
    cache = ExactCodeCache()
    cache.put(task(), SOURCE)
    assert cache.get(task(task_id="changed")) == SOURCE
    assert cache.get(task(prompt=task()["prompt"].replace("+ 1", "+ 2"))) is None


def test_no_gold_or_test_feedback_in_key():
    cache = ExactCodeCache()
    cache.put(task(), SOURCE)
    assert cache.get({**task(), "canonical_solution": "private", "plus_input": [999]}) == SOURCE


def test_conflicting_population_rejected():
    cache = ExactCodeCache()
    cache.put(task(), SOURCE)
    with pytest.raises(ValueError, match="conflicting"):
        cache.put(task(), SOURCE.replace("+ 1", "+ 2"))


def test_unsafe_program_rejected_before_cache_use():
    cache = ExactCodeCache()
    with pytest.raises(ValueError):
        cache.put(task(), "def arbitrary_function(x):\n    return eval(x)\n")


def test_empty_unknown_cache_abstains():
    assert ExactCodeCache().get(task()) is None
