import pytest

from neumann1.code_contract import admit, messages, public_view


def test_generation_receives_spec_only_not_private_authority():
    task = {"task_id": "fixture", "prompt": "def solve(x): ...", "entry_point": "solve",
            "canonical_solution": "SECRET GOLD", "plus_input": ["SECRET TEST"],
            "base_input": ["SECRET BASE"], "contract": "SECRET CONTRACT"}
    visible = public_view(task)
    assert set(visible) == {"task_id", "prompt", "entry_point"}
    assert "SECRET" not in str(messages(visible))
    assert task["canonical_solution"] == "SECRET GOLD"


def test_general_entry_names_and_standard_algorithms_are_allowed():
    source = "from collections import Counter\ndef count_letters(text: str):\n    return Counter(text)\n"
    assert admit(source, "count_letters") == source


@pytest.mark.parametrize("body", ["return open('secret').read()", "return getattr(x,'__class__')",
                                      "return x.__class__", "return eval(x)"])
def test_system_and_dynamic_operations_are_not_execution_authority(body):
    with pytest.raises(ValueError):
        admit("def solve(x):\n    " + body, "solve")


def test_imports_are_limited_to_declared_standard_library():
    with pytest.raises(ValueError):
        admit("import os\ndef solve(x): return os.environ", "solve")


def test_missing_entry_is_a_recorded_admission_failure():
    with pytest.raises(ValueError):
        admit("def other(x): return x", "solve")
