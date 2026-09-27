import pytest

from neumann1 import (
    IRKind,
    Problem,
    Representation,
    builtin_family_registry,
    canonical_representation_bytes,
    measure_repeated_structural_reuse,
)


@pytest.mark.parametrize(
    ("kind", "text"),
    [
        (
            IRKind.BIPARTITE_MATCHING,
            "S1 can use A or B; S2 can use B or C; S3 can use A or C",
        ),
        (
            IRKind.LINEAR_SYSTEM,
            "x + y = 5; x - y = 1",
        ),
    ],
)
def test_structural_reuse_preserves_answers_and_amortizes_compilation(kind, text):
    registry = builtin_family_registry()
    adapter = registry.get(kind)
    assert adapter is not None

    observation = measure_repeated_structural_reuse(
        Problem(text),
        adapter,
        repeats=6,
    )

    assert observation.compile_every_time.verified_rate == 1.0
    assert observation.compile_once_reuse.verified_rate == 1.0
    assert observation.answer_equivalence_rate == 1.0
    assert observation.representation_identity_stable

    assert observation.compile_every_time.representation_steps == 6
    assert observation.compile_once_reuse.representation_steps == 1
    assert observation.representation_step_reduction_factor == 6.0

    # Solver and verification work is not deleted by representation reuse.
    assert (
        observation.compile_every_time.solver_steps
        == observation.compile_once_reuse.solver_steps
    )
    assert (
        observation.compile_every_time.verification_steps
        == observation.compile_once_reuse.verification_steps
    )


def test_representation_byte_accounting_is_semantic_not_narrative():
    a = Representation(
        kind=IRKind.LINEAR_SYSTEM,
        payload={"variables": ["x"], "A": [[1.0]], "b": [2.0]},
        confidence=0.51,
        rationale="first explanation",
    )
    b = Representation(
        kind=IRKind.LINEAR_SYSTEM,
        payload={"variables": ["x"], "A": [[1.0]], "b": [2.0]},
        confidence=0.99,
        rationale="different explanation",
    )
    assert canonical_representation_bytes(a) == canonical_representation_bytes(b)


def test_structural_efficiency_does_not_require_representation_to_be_smaller():
    adapter = builtin_family_registry().get(IRKind.LINEAR_SYSTEM)
    assert adapter is not None
    observation = measure_repeated_structural_reuse(
        Problem("x + y = 5; x - y = 1"),
        adapter,
        repeats=3,
    )
    assert observation.raw_text_bytes > 0
    assert observation.representation_bytes > 0
    assert observation.representation_to_raw_byte_ratio > 0


def test_structural_efficiency_requires_repeat_workload():
    adapter = builtin_family_registry().get(IRKind.LINEAR_SYSTEM)
    assert adapter is not None
    with pytest.raises(ValueError, match="repeats must be >= 2"):
        measure_repeated_structural_reuse(
            Problem("x + y = 5; x - y = 1"),
            adapter,
            repeats=1,
        )
