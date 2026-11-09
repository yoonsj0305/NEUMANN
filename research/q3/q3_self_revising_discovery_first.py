"""Q3 FIRST: learn, falsify, then REWRITE a discovery method itself.

1. Meta-learn on 24 source-only numeric ANF functions. Freeze policy.
2. Independently disprove it on a graph source; move this one problem
   into the meta-training set and synthesize a new policy. Freeze its AST hash.
3. Test the FROZEN revised method on 300 previously unseen source tasks:
   130 numeric, 85 permuted graph, 85 permuted symbol-sequence functions.
4. Compare source queries AND CPU with exact classical degree-3 GF2 fitting.

The meta learner receives no domain-name labels or evaluation target outputs.
Grading inputs are forbidden in source oracle calls. All oracles are
researcher-generated GF2 tasks, NOT untouched independent ARC originals.
"""
from __future__ import annotations
from collections import Counter
from itertools import combinations
from random import Random
from pathlib import Path
from time import perf_counter_ns
import argparse
import json

from neumann1.discovery_policy_core import (
    MetaTask, DiscoveryMethodLearner, DiscoveryProcedureExecutor,
    DiscoveryStage, InferredDiscoveryMethod, revise_discovery_method,
)


def bits(i, n):
    return tuple((i >> j) & 1 for j in range(n))


def random_anfs(seed, n, degree):
    """Independent scoring law; never put its source into the meta search."""
    rng = Random(seed)
    terms = set()
    while len(terms) < 6:
        terms.add(tuple(sorted(rng.sample(range(n), degree))))
    linear = tuple(sorted(rng.sample(range(n), 3)))

    def oracle(x):
        v = 0
        for term in terms:
            p = 1
            for i in term:
                p &= x[i]
            v ^= p
        for i in linear:
            v ^= x[i]
        return v

    return oracle


def graph_triangles_permuted(seed):
    edges = list(combinations(range(5), 2))
    ids = {edge: i for i, edge in enumerate(edges)}
    terms = [
        (ids[a, b], ids[a, c], ids[b, c])
        for a, b, c in combinations(range(5), 3)
    ]
    perm = list(range(10))
    Random(seed).shuffle(perm)

    def oracle(x):
        result = 0
        for term in terms:
            v = 1
            for i in term:
                v &= x[perm[i]]
            result ^= v
        return result

    return oracle


def symbolic_101_pattern_permuted(seed):
    permutation = list(range(12))
    Random(seed).shuffle(permutation)

    def oracle(x):
        return sum(
            x[permutation[i]]
            & (1 ^ x[permutation[i + 1]])
            & x[permutation[i + 2]]
            for i in range(10)
        ) & 1

    return oracle


def hidden_grade_inputs(width, seed, count=128):
    # Inputs of Hamming weight >3 cannot be among rank-complete SOURCE
    # probes for an at-most-degree-3 program. Also exclude them from
    # independently chosen source-verification challenges explicitly.
    pool = [bits(i, width) for i in range(1 << width)
            if i.bit_count() > 3]
    return tuple(Random(seed).sample(pool, count))


def training_tasks():
    tasks = []
    for j in range(24):
        width = 10 if j % 3 == 0 else 12
        degree = 1 + j % 3
        seed = 300001 + j * 13
        tasks.append(MetaTask(
            random_anfs(seed, width, degree),
            width, hidden_grade_inputs(width, seed + 88, 32),
            seed + 951,
        ))
    return tuple(tasks)


def counterexample_feedback():
    seed = 50019
    return MetaTask(
        graph_triangles_permuted(10000 + 18 * 19),
        10, hidden_grade_inputs(10, seed + 4444, 128), seed,
    )


def fresh_transfer_cases():
    tasks = []
    for j in range(130):
        width = 12 if j % 2 else 10
        degree = 1 if j % 3 else 2
        tasks.append((
            "numeric", width,
            random_anfs(900001 + j * 13, width, degree),
            130001 + j,
        ))
    for j in range(85):
        tasks.append((
            "graph", 10,
            graph_triangles_permuted(200000 + j * 17),
            230001 + j,
        ))
    for j in range(85):
        tasks.append((
            "symbolic", 12,
            symbolic_101_pattern_permuted(300000 + j * 19),
            330001 + j,
        ))
    return tuple(tasks)


def execute_first():
    t0 = perf_counter_ns()
    meta_training = training_tasks()
    learner = DiscoveryMethodLearner(
        max_degree=3, verifier_counts=(8, 16, 32))
    first = learner.learn(meta_training)
    assert first.training_task_count == 24
    assert len(first.policy.steps) > 1
    feedback = counterexample_feedback()
    revised = revise_discovery_method(
        learner, first, meta_training, feedback)
    assert revised.original_feedback_errors > 0
    assert revised.repaired_feedback_errors == 0
    assert revised.revised_digest != revised.previous_digest
    method = revised.revised.policy
    frozen_hash = method.digest

    # A genuine strong classical baseline for THIS exact bounded algebraic
    # class. It is NOT a globally optimal solver for arbitrary problems.
    classical = InferredDiscoveryMethod((DiscoveryStage(3, 16),))
    executor = DiscoveryProcedureExecutor(max_queries=1024)
    tally = Counter()
    errors = []
    samples = []

    for family, width, oracle, seed in fresh_transfer_cases():
        hidden = hidden_grade_inputs(width, seed + 98765, 128)
        learned_run = executor.run(
            method, oracle, width=width, seed=seed,
            forbidden_inputs=hidden)
        classical_run = executor.run(
            classical, oracle, width=width, seed=seed,
            forbidden_inputs=hidden)
        # Target labels are now evaluated by a SEPARATE scorer, after both
        # frozen methods have returned. Both were forbidden from asking them.
        targets = tuple(oracle(x) for x in hidden)
        actual = (
            learned_run.program is not None and
            all(learned_run.apply(x) == y
                for x, y in zip(hidden, targets))
        )
        reference = (
            classical_run.program is not None and
            all(classical_run.apply(x) == y
                for x, y in zip(hidden, targets))
        )
        tally["meta_solved"] += bool(actual)
        tally["classical_solved"] += bool(reference)
        tally["meta_source_queries"] += learned_run.source_queries
        tally["classical_source_queries"] += classical_run.source_queries
        tally["meta_cpu_ms"] += learned_run.elapsed_ms
        tally["classical_cpu_ms"] += classical_run.elapsed_ms
        tally[family + "_meta_solved"] += bool(actual)
        tally[family + "_classical_solved"] += bool(reference)
        tally[family + "_meta_queries"] += learned_run.source_queries
        tally[family + "_classical_queries"] += classical_run.source_queries
        tally["source_refutations"] += learned_run.counterexample_count
        tally["last_stage"] += learned_run.stages_reached == 3
        if len(samples) < 12:
            samples.append({
                "family": family, "seed": seed,
                "source_status": learned_run.status,
                "source_trace": learned_run.trace,
                "source_queries": learned_run.source_queries,
                "correct_on_reserved_target": bool(actual),
            })
        if not actual or not reference:
            errors.append({
                "family": family, "seed": seed,
                "learned": bool(actual), "classical": bool(reference),
                "source_trace": learned_run.trace,
            })
    if method.digest != frozen_hash:
        raise AssertionError("meta policy was changed after target evaluation")

    total_learned = (
        revised.visible_meta_source_cost + tally["meta_source_queries"])
    total_classical = tally["classical_source_queries"]
    summary = {
        "task_count": 300,
        "meta_accuracy": tally["meta_solved"],
        "classical_accuracy": tally["classical_solved"],
        "initial_policy_ast": first.policy.ast,
        "initial_policy_sha256": first.digest,
        "revised_policy_ast": method.ast,
        "revised_policy_sha256": frozen_hash,
        "initial_feedback_errors": revised.original_feedback_errors,
        "repaired_feedback_errors": revised.repaired_feedback_errors,
        "meta_training_tasks": 25,
        "initial_meta_source_queries": first.meta_training_queries,
        "revised_meta_source_queries": revised.revised.meta_training_queries,
        "revision_feedback_source_query_charge":
            revised.feedback_source_query_charge,
        "revision_feedback_grading_query_charge":
            revised.feedback_grading_query_charge,
        "meta_training_cpu_ms":
            round(revised.revised.meta_training_elapsed_ms, 4),
        "heldout_meta_source_queries": tally["meta_source_queries"],
        "heldout_classical_source_queries":
            tally["classical_source_queries"],
        "meta_total_training_and_heldout_source_queries": total_learned,
        "classical_total_heldout_source_queries": total_classical,
        "independent_target_evaluation_labels": 300 * 128,
        "meta_total_including_target_scoring": total_learned + 300 * 128,
        "classical_total_including_target_scoring":
            total_classical + 300 * 128,
        "meta_heldout_cpu_ms": round(tally["meta_cpu_ms"], 4),
        "classical_heldout_cpu_ms": round(tally["classical_cpu_ms"], 4),
        "meta_cpu_including_training_ms": round(
            revised.revised.meta_training_elapsed_ms +
            tally["meta_cpu_ms"], 4),
        "classical_cpu_for_heldout_ms": round(
            tally["classical_cpu_ms"], 4),
        "counterexample_branches_in_new_tasks":
            tally["source_refutations"],
        "cases_reaching_last_degree": tally["last_stage"],
        "per_family": {
            fam: {
                "meta_correct": tally[fam + "_meta_solved"],
                "classical_correct": tally[fam + "_classical_solved"],
                "meta_source_queries": tally[fam + "_meta_queries"],
                "classical_source_queries": tally[fam + "_classical_queries"],
            } for fam in ("numeric", "graph", "symbolic")
        },
        "family_labels_provided_to_policy": False,
        "target_inputs_forbidden_during_source_discovery": True,
        "uses_synthetic_mathematical_oracles": True,
        "global_Q3_Q4_Q6_pass": False,
        "degraded_mode": "ABSTAIN when source evidence insufficient",
    }
    return {
        "schema": "NEUMANN.Q3.self-revising.discovery-method.v1",
        "summary": summary,
        "candidate_procedures": [
            {"sha256": s.digest,
             "stage_degrees": [q.degree for q in s.policy.steps],
             "checks_per_stage": [q.fresh_checks
                                  for q in s.policy.steps],
             "source_training_solved": s.solved,
             "training_errors": s.errors,
             "training_abstentions": s.abstentions,
             "gross_candidate_queries": s.source_queries}
            for s in revised.revised.trace
        ],
        "samples": samples,
        "errors": errors,
        "limits": [
            "Researcher-authored synthetic source tasks; not independent ARC.",
            "All primitive discovery operations and GF2 language are predesigned.",
            "Graph, numeric and symbolic semantics share GF2 polynomial class.",
            "Fixed-degree classical baseline is not global optimality.",
            "Earlier 240-case diagnostic research cost is additional.",
            "Source query savings do not imply wall-clock total compute savings.",
            "Finite source verification cannot certify arbitrary unknown laws.",
        ],
        "elapsed_wall_ms": round((perf_counter_ns()-t0)/1e6, 4),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", default="q3_meta_method_first_evidence.json")
    args = parser.parse_args()
    result = execute_first()
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    s = result["summary"]
    print(json.dumps({
        "meta_accuracy": s["meta_accuracy"],
        "classical_accuracy": s["classical_accuracy"],
        "meta_total_source_queries":
            s["meta_total_training_and_heldout_source_queries"],
        "classical_source_queries":
            s["classical_total_heldout_source_queries"],
        "initial_policy_sha256": s["initial_policy_sha256"],
        "revised_policy_sha256": s["revised_policy_sha256"],
        "meta_cpu_including_training_ms":
            s["meta_cpu_including_training_ms"],
        "classical_cpu_for_heldout_ms":
            s["classical_cpu_for_heldout_ms"],
        "errors": len(result["errors"]),
    }, indent=2))
