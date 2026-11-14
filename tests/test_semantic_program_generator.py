"""Mechanism/interface tests; these do not certify original task capability."""
import inspect

import numpy as np

from neumann1 import invention_core as ic, semantic_program_generator as g


def task(ast, xs, tid):
    examples = [((x,), ic.run_program(ast, g.LIB, (x,))) for x in xs]
    return {"id": tid, "in_types": ["L"], "out_type": "L", "ast": ast,
            "train": examples, "test": []}


def test_typed_prefix_changes_program_structure_and_roundtrips():
    ast = ("map", ("add", ("v", 1), ("k", 1)), ("v", 0))
    tokens = g.tokenize(ast)
    stack, prefix = [("L", ("L",))], []
    for token in tokens:
        assert g.allowed(stack[-1])[token]
        assert g.context(prefix, stack).shape == (g.CTX_DIM,)
        stack = g.advance(stack, token)
        prefix.append(token)
    assert stack == [] and g.tree(tokens) == ast
    # A function body gains a bound input and can combine it with other nodes.
    assert g.allowed(("I", ("L", "I")))[g.INDEX["$1"]]
    assert not g.allowed(("I", ("L",)))[g.INDEX["$1"]]


def test_observations_are_task_id_free_and_order_invariant():
    a = [(((1, 2),), (2, 3)), (((4, 5),), (5, 6))]
    assert np.allclose(g.observations(a), g.observations(a[::-1]))
    assert g.observations(a).shape == (g.OBS_DIM,)
    assert "test" not in inspect.signature(g.SemanticProgramGenerator.invent).parameters


def test_real_gradient_update_and_checkpoint_replay(tmp_path):
    xs = [(1, 2, 3), (4, 5), (6, 0, 8)]
    ts = [task(("map", ("add", ("v", 1), ("k", 1)), ("v", 0)), xs, "a"),
          task(("cons", ("k", 2), ("v", 0)), xs, "b")]
    model = g.SemanticProgramGenerator(hidden=16)
    r = model.fit(ts, epochs=8, batch=16)
    assert r["parameter_l2_delta"] > 0 and r["loss"][-1] < r["loss"][0]
    path = tmp_path / "checkpoint.npz"
    model.save(path)
    copied = g.SemanticProgramGenerator.load(path)
    assert all(np.array_equal(x, y) for x, y in zip(model.parameters(), copied.parameters()))


def test_rejects_empty_or_nonunary_observations():
    for examples in ([], [((1, 2), 3)]):
        try:
            g.observations(examples)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid observation accepted")
