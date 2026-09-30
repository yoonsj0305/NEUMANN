from __future__ import annotations

from functools import lru_cache
from statistics import mean, median
from time import perf_counter_ns

from .family_registry import builtin_family_registry
from .paired_linear_dataset import (
    PairedLinearExample,
    direct_frontier_final_examples,
    direct_frontier_training_pool,
    direct_frontier_validation_examples,
    generate_solution_covered_linear_examples,
    make_near_negative,
    paired_linear_final_examples,
    paired_linear_training_examples,
    paired_linear_validation_examples,
    sequence_challenger_final_examples,
    sequence_challenger_training_pool,
    sequence_challenger_validation_examples,
)
from .types import CostLedger, IRKind, Problem


AUDIT_COUNT = 243
AUDIT_SEED = 7602
ADMISSIBILITY_THRESHOLD = 0.99


@lru_cache(maxsize=1)
def prior_linear_texts() -> frozenset[str]:
    datasets = (
        paired_linear_training_examples(),
        paired_linear_validation_examples(),
        paired_linear_final_examples(),
        direct_frontier_training_pool(),
        direct_frontier_validation_examples(),
        direct_frontier_final_examples(),
        sequence_challenger_training_pool(),
        sequence_challenger_validation_examples(),
        sequence_challenger_final_examples(),
    )
    return frozenset(example.text for dataset in datasets for example in dataset)


@lru_cache(maxsize=1)
def q4_admissibility_audit_examples() -> tuple[PairedLinearExample, ...]:
    examples = generate_solution_covered_linear_examples(
        AUDIT_COUNT,
        seed=AUDIT_SEED,
        forbidden_texts=prior_linear_texts(),
    )
    texts = {example.text for example in examples}
    if len(texts) != AUDIT_COUNT:
        raise RuntimeError("v0.0.76 audit corpus contains duplicate text")
    if texts.intersection(prior_linear_texts()):
        raise RuntimeError("v0.0.76 audit corpus overlaps an earlier linear corpus")
    return examples


def _semantic_solution_equivalent(
    example: PairedLinearExample,
    answer: object,
    *,
    tolerance: float = 1e-7,
) -> bool:
    if not isinstance(answer, dict):
        return False
    expected = dict(zip(example.variables, example.solution))
    if set(answer) != set(expected):
        return False
    return all(
        abs(float(answer[name]) - float(value)) <= tolerance
        for name, value in expected.items()
    )


def observe_positive(
    example: PairedLinearExample,
    *,
    compiler: object,
    solver: object,
    verifier: object,
) -> dict:
    ledger = CostLedger()
    start = perf_counter_ns()
    representation = compiler.form(Problem(example.text), ledger)
    compiled = representation.kind == IRKind.LINEAR_SYSTEM
    solved = False
    verified = False
    semantic_equivalent = False
    error = None
    answer = None

    if compiled:
        try:
            answer = solver.solve(representation, ledger)
            solved = True
            verification = verifier.verify(
                Problem(example.text),
                representation,
                answer,
                ledger,
            )
            verified = bool(verification.ok)
            semantic_equivalent = _semantic_solution_equivalent(example, answer)
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            error = f"{type(exc).__name__}: {exc}"

    elapsed_ms = (perf_counter_ns() - start) / 1e6
    return {
        "compiled": compiled,
        "solved": solved,
        "verified": verified,
        "semantic_equivalent": semantic_equivalent,
        "accepted_exact": compiled and solved and verified and semantic_equivalent,
        "total_ms": elapsed_ms,
        "representation_steps": ledger.representation_steps,
        "solver_steps": ledger.solver_steps,
        "verification_steps": ledger.verification_steps,
        "error": error,
    }


def observe_negative(
    text: str,
    *,
    compiler: object,
) -> dict:
    ledger = CostLedger()
    start = perf_counter_ns()
    representation = compiler.form(Problem(text), ledger)
    elapsed_ms = (perf_counter_ns() - start) / 1e6
    return {
        "fail_closed": representation.kind == IRKind.UNKNOWN,
        "total_ms": elapsed_ms,
        "representation_steps": ledger.representation_steps,
        "kind": (
            representation.kind.value
            if isinstance(representation.kind, IRKind)
            else str(representation.kind)
        ),
    }


def summarize(rows: list[dict]) -> dict:
    positives = [row for row in rows if row["polarity"] == "positive"]
    negatives = [row for row in rows if row["polarity"] == "negative"]
    if len(positives) != AUDIT_COUNT or len(negatives) != AUDIT_COUNT:
        raise ValueError("v0.0.76 requires all 243 positive and negative rows")

    positive_compile_rate = mean(float(row["compiled"]) for row in positives)
    positive_verifier_rate = mean(float(row["verified"]) for row in positives)
    positive_semantic_rate = mean(
        float(row["semantic_equivalent"]) for row in positives
    )
    positive_exact_verified_rate = mean(
        float(row["accepted_exact"]) for row in positives
    )
    negative_fail_closed_rate = mean(
        float(row["fail_closed"]) for row in negatives
    )

    learned_parameter_count = 0
    reject = (
        positive_exact_verified_rate >= ADMISSIBILITY_THRESHOLD
        and negative_fail_closed_rate >= ADMISSIBILITY_THRESHOLD
        and learned_parameter_count == 0
    )
    decision = (
        "REJECT_EXISTING_LINEAR_TASK_FOR_Q4"
        if reject
        else "LINEAR_TASK_REMAINS_Q4_CANDIDATE"
    )

    return {
        "decision": decision,
        "learned_parameter_count": learned_parameter_count,
        "positive_rows": len(positives),
        "negative_rows": len(negatives),
        "positive_compile_rate": positive_compile_rate,
        "positive_verifier_rate": positive_verifier_rate,
        "positive_hidden_solution_equivalence_rate": positive_semantic_rate,
        "positive_exact_verified_rate": positive_exact_verified_rate,
        "negative_fail_closed_rate": negative_fail_closed_rate,
        "median_positive_total_ms": median(row["total_ms"] for row in positives),
        "median_negative_rejection_ms": median(row["total_ms"] for row in negatives),
        "mean_positive_representation_steps": mean(
            row["representation_steps"] for row in positives
        ),
        "mean_positive_solver_steps": mean(row["solver_steps"] for row in positives),
        "mean_positive_verification_steps": mean(
            row["verification_steps"] for row in positives
        ),
        "mean_negative_representation_steps": mean(
            row["representation_steps"] for row in negatives
        ),
        "threshold": ADMISSIBILITY_THRESHOLD,
    }


def run_audit(
    examples: tuple[PairedLinearExample, ...] | None = None,
) -> dict:
    if examples is None:
        examples = q4_admissibility_audit_examples()
    if len(examples) != AUDIT_COUNT:
        raise ValueError(f"expected exactly {AUDIT_COUNT} audit examples")

    registry = builtin_family_registry()
    adapter = registry.get(IRKind.LINEAR_SYSTEM)
    if adapter is None:
        raise RuntimeError("linear-system family is not registered")

    rows: list[dict] = []
    for index, example in enumerate(examples):
        positive = observe_positive(
            example,
            compiler=adapter.compiler,
            solver=adapter.solver,
            verifier=adapter.answer_verifier,
        )
        rows.append(
            {
                "index": index,
                "polarity": "positive",
                "text": example.text,
                **positive,
            }
        )

        negative_text = make_near_negative(example, index)
        negative = observe_negative(
            negative_text,
            compiler=adapter.compiler,
        )
        rows.append(
            {
                "index": index,
                "polarity": "negative",
                "text": negative_text,
                "negative_mode": index % 3,
                **negative,
            }
        )

    summary = summarize(rows)
    return {
        "experiment": "v0.0.76 Q4 task-admissibility gate",
        "audit_count": AUDIT_COUNT,
        "audit_seed": AUDIT_SEED,
        "prior_text_count": len(prior_linear_texts()),
        "summary": summary,
        "rows": rows,
    }
