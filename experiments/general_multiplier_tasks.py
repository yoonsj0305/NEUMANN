"""Small opened development set for the Architecture Multiplier gate.

Twelve author-constructed tasks only: 4 math, 4 coding, 4 finite planning.
This is not a sealed benchmark and cannot establish generalization.
"""
from __future__ import annotations

from neumann1.general_runtime_v106 import canonical, sha


def multiplier_tasks():
    return [
        (
            {
                "id": "am_math_01",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(a*b-c)/(d+e)",
                    "bindings": {"a": 17, "b": 13, "c": 5, "d": 4, "e": 8, "unused": 999},
                    "background": "A blue notebook is on the desk.",
                },
            },
            {"exact": "18"},
        ),
        (
            {
                "id": "am_math_02",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(p*q-r)/(s+t)",
                    "bindings": {"p": 29, "q": 11, "r": 7, "s": 3, "t": 9, "unused": 123},
                    "background": "The receipt is printed on green paper.",
                },
            },
            {"exact": "26"},
        ),
        (
            {
                "id": "am_math_03",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(x+y*z)/(u-v)",
                    "bindings": {"x": 14, "y": 3, "z": 8, "u": 19, "v": 7, "spare": 404},
                    "background": "A train leaves at noon.",
                },
            },
            {"exact": "19/6"},
        ),
        (
            {
                "id": "am_math_04",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(m*n+p)/(q-r)",
                    "bindings": {"m": 12, "n": 7, "p": 5, "q": 15, "r": 4, "unused": -77},
                    "background": "The folder label says ORBIT.",
                },
            },
            {"exact": "89/11"},
        ),
        (
            {
                "id": "am_code_01",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the number of distinct negative integers in items, a list of integers.",
                    "examples": [{"input": [-2, -2, 0, 3, -5], "output": 2}],
                    "background": "The caller likes music.",
                },
            },
            {
                "tests": [
                    {"input": [], "output": 0},
                    {"input": [-2, -2, 0, 3, -5], "output": 2},
                    {"input": [0, 1, 3], "output": 0},
                    {"input": [-1, -3, -1, -7], "output": 3},
                ]
            },
        ),
        (
            {
                "id": "am_code_02",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the sum of distinct even integers in items, a list of integers.",
                    "examples": [{"input": [2, 2, 3, 4, -2], "output": 4}],
                    "background": "The caller likes astronomy.",
                },
            },
            {
                "tests": [
                    {"input": [], "output": 0},
                    {"input": [2, 2, 3, 4, -2], "output": 4},
                    {"input": [1, 3, 5], "output": 0},
                    {"input": [0, 6, 6, 8], "output": 14},
                ]
            },
        ),
        (
            {
                "id": "am_code_03",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the number of distinct positive odd integers in items, a list of integers.",
                    "examples": [{"input": [1, 1, 2, 3, 5, -1], "output": 3}],
                    "background": "A poster on the wall is orange.",
                },
            },
            {
                "tests": [
                    {"input": [], "output": 0},
                    {"input": [1, 1, 2, 3, 5, -1], "output": 3},
                    {"input": [2, 4, 6], "output": 0},
                    {"input": [7, 9, 7, 0], "output": 2},
                ]
            },
        ),
        (
            {
                "id": "am_code_04",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the sum of absolute values of distinct nonzero integers in items, a list of integers.",
                    "examples": [{"input": [-2, -2, 3, 0], "output": 5}],
                    "background": "The request arrived on Tuesday.",
                },
            },
            {
                "tests": [
                    {"input": [], "output": 0},
                    {"input": [-2, -2, 3, 0], "output": 5},
                    {"input": [1, -1, 1], "output": 2},
                    {"input": [0, 4, -5, 4], "output": 9},
                ]
            },
        ),
        (
            {
                "id": "am_plan_01",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {"A": [0, 1, 2, 3], "B": [0, 1, 2, 3], "C": [0, 1, 2, 3], "D": [0, 1, 2, 3]},
                    "constraints": [["lt", "A", "B"], ["lt", "B", "C"], ["eq", "C", "D"]],
                    "background": "A train has six carriages.",
                },
            },
            {},
        ),
        (
            {
                "id": "am_plan_02",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {"W": [0, 1, 2, 3, 4], "X": [0, 1, 2, 3, 4], "Y": [0, 1, 2, 3, 4], "Z": [0, 1, 2, 3, 4]},
                    "constraints": [["lt", "W", "X"], ["le", "X", "Y"], ["lt", "Y", "Z"]],
                    "background": "Four empty boxes are stacked nearby.",
                },
            },
            {},
        ),
        (
            {
                "id": "am_plan_03",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {"P": [0, 1, 2, 3], "Q": [0, 1, 2, 3], "R": [0, 1, 2, 3], "S": [0, 1, 2, 3]},
                    "constraints": [["ne", "P", "Q"], ["lt", "Q", "R"], ["lt", "P", "R"], ["eq", "R", "S"]],
                    "background": "The room has a round clock.",
                },
            },
            {},
        ),
        (
            {
                "id": "am_plan_04",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {"A": [0, 1, 2, 3, 4], "B": [0, 1, 2, 3, 4], "C": [0, 1, 2, 3, 4], "D": [0, 1, 2, 3, 4], "E": [0, 1, 2, 3, 4]},
                    "constraints": [["eq", "A", "B"], ["lt", "B", "C"], ["lt", "C", "D"], ["eq", "D", "E"]],
                    "background": "A spare cable lies under the table.",
                },
            },
            {},
        ),
    ]


def model_view(task):
    """Remove runtime-only family/id labels from the model-visible problem."""
    return {"instruction": task["instruction"], "public": task["public"]}


TASK_SHA256 = sha(multiplier_tasks())
MODEL_VIEW_SHA256 = sha([model_view(task) for task, _private in multiplier_tasks()])


def manifest():
    tasks = multiplier_tasks()
    assert len(tasks) == 12
    assert len({task["id"] for task, _ in tasks}) == 12
    assert {task["family"] for task, _ in tasks} == {"math_logic", "coding", "constraint_planning"}
    return {
        "schema": "neumann.architecture-multiplier-opened-tasks.v1",
        "count": len(tasks),
        "task_sha256": TASK_SHA256,
        "model_view_sha256": MODEL_VIEW_SHA256,
        "families": {
            family: sum(task["family"] == family for task, _ in tasks)
            for family in ("math_logic", "coding", "constraint_planning")
        },
        "split": "opened_author_constructed_development",
        "sealed": False,
        "training_allowed": False,
    }
