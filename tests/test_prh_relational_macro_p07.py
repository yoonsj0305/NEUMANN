"""Contract tests for the advisory PRH relational macro, no neural/JEPA claims."""
import json
from pathlib import Path

import numpy as np

from neumann1.prh_relational_macro_p07 import SCHEMA, Abstain, fit, predict, execute

FIXTURE = Path(__file__).resolve().parents[1] / "experiments" / "fixtures" / "arc_agi1_opened" / "05f2a901.json"


def example(direction, gap, clearance, moving_color=2, anchor_color=8):
    """Independent reference geometry; no synthesizer used to make labels."""
    grid = np.zeros((25, 25), dtype=np.int64)
    target = grid.copy()
    grid[11:13, 11:13] = anchor_color
    target[11:13, 11:13] = anchor_color
    if direction == "down":
        r, c = 11 - gap - 3, 10
        dr, dc = gap - clearance, 0
    elif direction == "up":
        r, c = 13 + gap, 10
        dr, dc = -(gap - clearance), 0
    elif direction == "right":
        r, c = 10, 11 - gap - 3
        dr, dc = 0, gap - clearance
    else:
        r, c = 10, 13 + gap
        dr, dc = 0, -(gap - clearance)
    # The moving shape has more pixels and a 3x3 occupied bounding box.
    pixels = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    for rr, cc in pixels:
        grid[r+rr, c+cc] = moving_color
        target[r+rr+dr, c+cc+dc] = moving_color
    return {"input": grid.tolist(), "output": target.tolist()}


def test_public_opened_arc_dev_only():
    task = json.loads(FIXTURE.read_text(encoding="utf-8"))
    inferred = fit(task["train"])
    assert inferred["candidates"] == [{"schema": SCHEMA, "role": "max_area", "clearance": 0}]
    assert predict(task["test"][0]["input"], inferred)["output"] == task["test"][0]["output"]


def test_induced_gap_and_left_unseen_direction():
    for clearance in range(4):
        training = [example(d, clearance+3, clearance) for d in ("down", "right", "up")]
        guess = fit(training)
        assert guess["status"] == "CONSISTENT_AST"
        assert guess["candidates"] == [{"schema": SCHEMA, "role": "max_area", "clearance": clearance}]
        held = example("left", clearance+4, clearance, moving_color=9, anchor_color=3)
        assert predict(held["input"], guess)["output"] == held["output"]


def test_output_label_mutation_does_not_affect_inference():
    task = json.loads(FIXTURE.read_text(encoding="utf-8"))
    before = fit(task["train"])
    task["test"][0]["output"] = [[-99]]
    assert before == fit(task["train"])


def test_contradictory_train_refuses_to_guess():
    training = [example(d, 4, 1) for d in ("down", "right", "up")]
    training[1]["output"][0][0] = 7
    assert fit(training)["candidates"] == []


def test_unsupported_and_unsafe_ast_abstain():
    inferred = fit([example(d, 4, 1) for d in ("down", "right", "up")])
    grid = np.zeros((10, 10), dtype=np.int64)
    grid[1:3, 1:3] = 2
    grid[6:8, 6:8] = 8
    assert predict(grid.tolist(), inferred)["status"] == "ABSTAIN_INVALID_SCENE"
    for clearance in (True, -1, 5, "1"):
        try:
            execute(example("left", 4, 1)["input"],
                    {"schema": SCHEMA, "role": "max_area", "clearance": clearance})
        except Abstain:
            pass
        else:
            raise AssertionError("invalid AST accepted")
