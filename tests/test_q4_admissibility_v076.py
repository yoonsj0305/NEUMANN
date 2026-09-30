from neumann1.family_registry import builtin_family_registry
from neumann1.paired_linear_dataset import (
    generate_paired_linear_examples,
    make_near_negative,
)
from neumann1.q4_admissibility_v076 import (
    ADMISSIBILITY_THRESHOLD,
    AUDIT_COUNT,
    observe_negative,
    observe_positive,
    prior_linear_texts,
    q4_admissibility_audit_examples,
    summarize,
)
from neumann1.types import IRKind


def test_v076_nonfinal_positive_and_negative_contract():
    adapter = builtin_family_registry().get(IRKind.LINEAR_SYSTEM)
    assert adapter is not None

    examples = generate_paired_linear_examples(12, seed=7699)
    for index, example in enumerate(examples):
        positive = observe_positive(
            example,
            compiler=adapter.compiler,
            solver=adapter.solver,
            verifier=adapter.answer_verifier,
        )
        assert positive["accepted_exact"]
        assert positive["representation_steps"] > 0
        assert positive["solver_steps"] > 0
        assert positive["verification_steps"] > 0

        negative = observe_negative(
            make_near_negative(example, index),
            compiler=adapter.compiler,
        )
        assert negative["fail_closed"]
        assert negative["representation_steps"] > 0


def test_v076_fresh_audit_corpus_contract():
    examples = q4_admissibility_audit_examples()
    assert len(examples) == AUDIT_COUNT
    texts = {example.text for example in examples}
    assert len(texts) == AUDIT_COUNT
    assert not texts.intersection(prior_linear_texts())
    assert len({example.solution for example in examples}) == 81


def _rows(*, positive_failures=0, negative_failures=0):
    rows = []
    for index in range(AUDIT_COUNT):
        positive_ok = index >= positive_failures
        rows.append(
            {
                "index": index,
                "polarity": "positive",
                "compiled": positive_ok,
                "verified": positive_ok,
                "semantic_equivalent": positive_ok,
                "accepted_exact": positive_ok,
                "total_ms": 1.0,
                "representation_steps": 1,
                "solver_steps": 1,
                "verification_steps": 1,
            }
        )
        negative_ok = index >= negative_failures
        rows.append(
            {
                "index": index,
                "polarity": "negative",
                "fail_closed": negative_ok,
                "total_ms": 1.0,
                "representation_steps": 1,
            }
        )
    return rows


def test_v076_threshold_is_frozen_and_not_all_or_nothing():
    assert ADMISSIBILITY_THRESHOLD == 0.99
    perfect = summarize(_rows())
    assert perfect["decision"] == "REJECT_EXISTING_LINEAR_TASK_FOR_Q4"

    # 2/243 failures still leave the frozen >= .99 criterion satisfied.
    near = summarize(_rows(positive_failures=2, negative_failures=2))
    assert near["positive_exact_verified_rate"] >= ADMISSIBILITY_THRESHOLD
    assert near["negative_fail_closed_rate"] >= ADMISSIBILITY_THRESHOLD
    assert near["decision"] == "REJECT_EXISTING_LINEAR_TASK_FOR_Q4"

    # 3/243 failures cross below .99 and must preserve the candidate.
    below = summarize(_rows(positive_failures=3))
    assert below["positive_exact_verified_rate"] < ADMISSIBILITY_THRESHOLD
    assert below["decision"] == "LINEAR_TASK_REMAINS_Q4_CANDIDATE"
