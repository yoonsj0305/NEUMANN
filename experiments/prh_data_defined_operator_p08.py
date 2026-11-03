"""P0.8 | Synthesize an executable semantic rule table from observations.

The system is given a *fixed local-stencil interface*, not a rule ID. It infers
all eight bits of the operator from train pairs. Neither the hidden rule ID nor
held-out outputs enter `induce`. Synthetic closed-family mechanism only;
not JEPA, unbounded opcode invention, general Q3 closure or frontier evidence.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

SCHEMA = 'neumann.prh.data-defined-local-op.p08.v1'
CONTRACT = {
    'schema': SCHEMA,
    'base_seed': 20261103,
    'task_count': 16,
    'train_lengths': [19, 23, 29, 31, 37],
    'test_1d_lengths': [41, 53, 67],
    'test_2d_shapes': [[4, 43], [7, 59]],
    'stencil': 'binary-radius-1-periodic',
    'draw_rule_ids': 'default_rng(base_seed).choice(256, size=16, replace=False)',
    'no_conditional_resampling': True,
    'negative_controls': [
        'undercoverage', 'contradictory_label', 'wrong_output_shape',
        'unsupported_alphabet', 'nonlocal_dependence',
    ],
    'frozen_gate': {
        'unique_complete_operator_tables': 16,
        'independent_rule_certificate_passes': 16,
        'heldout_1d_exact': 48,
        'heldout_2d_exact': 32,
        'negative_controls_rejected': 5,
    },
    'global_q1_to_q7': 'OPEN',
    'jepa_or_neural_training': 'NOT_RUN',
    'novelty_scope': 'novel_semantic_table_within_predeclared_local_stencil',
}


@dataclass(frozen=True)
class Rule8:
    """Typed dynamically created, fully determined 8-entry local operator."""
    table: tuple[int, ...]
    radius: int = 1
    boundary: str = 'periodic'
    op: str = 'LOCAL_RULE8'

    def __post_init__(self) -> None:
        if (len(self.table) != 8 or any(type(x) is not int or x not in (0, 1) for x in self.table)
            or self.radius != 1 or self.boundary != 'periodic' or self.op != 'LOCAL_RULE8'):
            raise ValueError('illtyped_local_operator')

    @property
    def rule_id(self) -> int:
        return sum(bit << pos for pos, bit in enumerate(self.table))

    def as_json(self) -> dict:
        return {'op': self.op, 'radius': self.radius, 'boundary': self.boundary,
                'table': list(self.table)}


class Reject(ValueError):
    pass


def _input_bits(raw: list[int]) -> list[int]:
    if (not isinstance(raw, list) or len(raw) < 3
        or any(type(x) is not int or x not in (0, 1) for x in raw)):
        raise Reject('ABSTAIN_ALPHABET_OR_LENGTH')
    return raw


def _observations(train: list[dict]) -> tuple[list[int | None], list[int]]:
    if not isinstance(train, list) or not train:
        raise Reject('ABSTAIN_NO_TRAINING_PAIRS')
    table: list[int | None] = [None] * 8
    coverage = [0] * 8
    for ex in train:
        if not isinstance(ex, dict) or set(ex) != {'input', 'output'}:
            raise Reject('ABSTAIN_INVALID_EXAMPLE')
        src = _input_bits(ex['input'])
        dst = ex['output']
        if (not isinstance(dst, list) or len(src) != len(dst)
            or any(type(v) is not int or v not in (0, 1) for v in dst)):
            raise Reject('ABSTAIN_OUTPUT_SHAPE_OR_ALPHABET')
        n = len(src)
        for i in range(n):
            k = (src[(i - 1) % n] << 2) | (src[i] << 1) | src[(i + 1) % n]
            v = dst[i]
            coverage[k] += 1
            if table[k] is None:
                table[k] = v
            elif table[k] != v:
                raise Reject('ABSTAIN_CONTRADICTORY_LOCAL_RULE')
    return table, coverage


def induce(train: list[dict]) -> dict:
    """No rule byte or test output argument exists: local semantic inference."""
    start = time.perf_counter_ns()
    try:
        values, coverage = _observations(train)
        if any(v is None for v in values):
            raise Reject('ABSTAIN_INCOMPLETE_CONTEXT')
        candidate = Rule8(tuple(values))
        # Compiler-side replay checks the complete original examples.
        if any(execute_1d(candidate, ex['input']) != ex['output'] for ex in train):
            raise Reject('ABSTAIN_REPLAY_MISMATCH')
        return {'status': 'INDUCED_COMPLETE_LOCAL_OPERATOR',
                'ast': candidate.as_json(), 'rule_id': candidate.rule_id,
                'coverage': coverage, 'train_cells_observed': sum(coverage),
                'compile_and_replay_ns': time.perf_counter_ns() - start}
    except Reject as exc:
        return {'status': str(exc), 'ast': None,
                'compile_and_replay_ns': time.perf_counter_ns() - start}


def _ast(raw: dict) -> Rule8:
    if not isinstance(raw, dict) or set(raw) != {'op', 'radius', 'boundary', 'table'}:
        raise Reject('ABSTAIN_ILLTYPED_AST')
    if not isinstance(raw['table'], list):
        raise Reject('ABSTAIN_ILLTYPED_AST')
    try:
        return Rule8(tuple(raw['table']), raw['radius'], raw['boundary'], raw['op'])
    except ValueError:
        raise Reject('ABSTAIN_ILLTYPED_AST') from None


def execute_1d(program: Rule8, raw: list[int]) -> list[int]:
    """Vectorized independent compiled interpreter (not the reference loop)."""
    src = _input_bits(raw)
    x = np.asarray(src, dtype=np.int64)
    neighborhood = (np.roll(x, 1) << 2) | (x << 1) | np.roll(x, -1)
    return np.asarray(program.table, dtype=np.int64)[neighborhood].tolist()


def execute_2d(program: Rule8, raw: list[list[int]]) -> list[list[int]]:
    if not isinstance(raw, list) or not raw or any(not isinstance(row, list) for row in raw):
        raise Reject('ABSTAIN_INVALID_ROW_VIEW')
    length = len(raw[0])
    if length < 3 or any(len(row) != length for row in raw):
        raise Reject('ABSTAIN_INVALID_ROW_VIEW')
    return [execute_1d(program, row) for row in raw]


def execute_typed(raw_ast: dict, input_data: list, *, rowwise: bool = False) -> list:
    op = _ast(raw_ast)
    return execute_2d(op, input_data) if rowwise else execute_1d(op, input_data)


def reference_1d(src: list[int], reference_rule_byte: int) -> list[int]:
    """Independent bitwise reference: not synthesized from `Rule8`."""
    if type(reference_rule_byte) is not int or not (0 <= reference_rule_byte <= 255):
        raise ValueError('invalid_reference_byte')
    n = len(src)
    return [((reference_rule_byte >> ((4 * src[(i-1) % n])
                                       + (2 * src[i]) + src[(i+1) % n])) & 1)
            for i in range(n)]


def reference_2d(src: list[list[int]], rule_byte: int) -> list[list[int]]:
    return [reference_1d(row, rule_byte) for row in src]


def enumerative_direct(train: list[dict]) -> dict:
    """Bounded catalog baseline, same train pairs, no supplied rule ID."""
    start = time.perf_counter_ns()
    hits = []
    checked = 0
    for byte in range(256):
        ok = True
        for ex in train:
            checked += 1
            if reference_1d(ex['input'], byte) != ex['output']:
                ok = False
                break
        if ok:
            hits.append(byte)
    return {'candidates_scanned': 256, 'train_replays': checked,
            'unique_rule_id': hits[0] if len(hits) == 1 else None,
            'consistent_candidate_count': len(hits),
            'enumeration_ns': time.perf_counter_ns() - start}


def generate_task(i: int, rule_byte: int) -> dict:
    base = CONTRACT['base_seed'] + i * 1009
    train_rng = np.random.default_rng(base + 11)
    test_rng = np.random.default_rng(base + 911)
    def random_row(rng: np.random.Generator, n: int) -> list[int]:
        return rng.integers(0, 2, size=n).astype(int).tolist()
    train = []
    for n in CONTRACT['train_lengths']:
        src = random_row(train_rng, n)
        train.append({'input': src, 'output': reference_1d(src, rule_byte)})
    test_1d = []
    for n in CONTRACT['test_1d_lengths']:
        src = random_row(test_rng, n)
        test_1d.append({'input': src, 'output': reference_1d(src, rule_byte)})
    test_2d = []
    for rows, columns in CONTRACT['test_2d_shapes']:
        src = [random_row(test_rng, columns) for _ in range(rows)]
        test_2d.append({'input': src, 'output': reference_2d(src, rule_byte)})
    return {'train': train, 'test_1d': test_1d, 'test_2d': test_2d}


def negative_controls(source_task: dict) -> dict:
    src = source_task['train']
    results = {}
    incomplete = [{'input':[0] * n, 'output':[0] * n}
                  for n in CONTRACT['train_lengths']]
    results['undercoverage'] = induce(incomplete)['status']
    corrupt = deepcopy(src)
    # One flipped output of a context repeated throughout training is necessarily
    # inconsistent (if the underlying function really is local).
    corrupt[0]['output'][0] ^= 1
    results['contradictory_label'] = induce(corrupt)['status']
    bad_shape = deepcopy(src)
    bad_shape[0]['output'].pop()
    results['wrong_output_shape'] = induce(bad_shape)['status']
    bad_alphabet = deepcopy(src)
    bad_alphabet[0]['input'][0] = 2
    results['unsupported_alphabet'] = induce(bad_alphabet)['status']
    nonlocal_train = [
        {'input':[0] * 19, 'output':[0] * 19},
        {'input':[1] + [0] * 18, 'output':[0,0,1] + [0] * 16},
    ]
    results['nonlocal_dependence'] = induce(nonlocal_train)['status']
    return results


def task_evaluation(i: int, rule_byte: int) -> dict:
    task = generate_task(i, rule_byte)
    # Only train enters induction; source rule and all test targets are scorer-only.
    program_receipt = induce(task['train'])
    baseline_receipt = enumerative_direct(task['train'])
    t0 = time.perf_counter_ns()
    if program_receipt['ast'] is None:
        exact_1d = [False] * len(task['test_1d'])
        exact_2d = [False] * len(task['test_2d'])
        local_cert = {'complete':False, 'verified_entries':0}
    else:
        program = _ast(program_receipt['ast'])
        exact_1d = [execute_1d(program, ex['input']) == ex['output'] for ex in task['test_1d']]
        exact_2d = [execute_2d(program, ex['input']) == ex['output'] for ex in task['test_2d']]
        local_cert = {
            'complete':True,
            'verified_entries': sum(program.table[idx] == ((rule_byte >> idx) & 1) for idx in range(8)),
            'train_replay_exact': all(execute_1d(program, ex['input']) == ex['output'] for ex in task['train']),
        }
    verify_and_execute_ns = time.perf_counter_ns() - t0
    t1 = time.perf_counter_ns()
    baseline_identical = baseline_receipt['unique_rule_id'] == rule_byte
    if baseline_receipt['unique_rule_id'] is not None:
        baseline_program = Rule8(tuple((baseline_receipt['unique_rule_id'] >> j)&1 for j in range(8)))
        baseline_success = all(execute_1d(baseline_program, ex['input']) == ex['output'] for ex in task['test_1d']) and all(execute_2d(baseline_program, ex['input']) == ex['output'] for ex in task['test_2d'])
    else:
        baseline_success = False
    baseline_verify_execute_ns = time.perf_counter_ns() - t1
    return {
        'task_index': i,
        'reference_rule_for_independent_scorer_only': rule_byte,
        'train_sha256': sha256(json.dumps(task['train'], sort_keys=True).encode()).hexdigest(),
        'induction': program_receipt,
        'baseline_catalog': baseline_receipt,
        'independent_truth_certificate': local_cert,
        'heldout_1d_exact': exact_1d,
        'heldout_2d_exact': exact_2d,
        'baseline_rule_correct': baseline_identical,
        'baseline_heldout_all_correct': baseline_success,
        'induced_rule_correct': program_receipt.get('rule_id') == rule_byte,
        'original_verification_and_test_ns': verify_and_execute_ns,
        'catalog_original_verification_and_test_ns': baseline_verify_execute_ns,
    }


def run() -> dict:
    started = time.perf_counter_ns()
    ids = np.random.default_rng(CONTRACT['base_seed']).choice(256, size=CONTRACT['task_count'], replace=False).tolist()
    rows = [task_evaluation(i, int(byte)) for i, byte in enumerate(ids)]
    negatives = negative_controls(generate_task(0, int(ids[0])))
    negative_ok = {
        'undercoverage': negatives['undercoverage'] == 'ABSTAIN_INCOMPLETE_CONTEXT',
        'contradictory_label': negatives['contradictory_label'] == 'ABSTAIN_CONTRADICTORY_LOCAL_RULE',
        'wrong_output_shape': negatives['wrong_output_shape'] == 'ABSTAIN_OUTPUT_SHAPE_OR_ALPHABET',
        'unsupported_alphabet': negatives['unsupported_alphabet'] == 'ABSTAIN_ALPHABET_OR_LENGTH',
        'nonlocal_dependence': negatives['nonlocal_dependence'] == 'ABSTAIN_CONTRADICTORY_LOCAL_RULE',
    }
    metrics = {
        'unique_complete_tables': sum(r['induction']['status'] == 'INDUCED_COMPLETE_LOCAL_OPERATOR' for r in rows),
        'independent_certificates_passed': sum(r['independent_truth_certificate'].get('verified_entries') == 8 and r['independent_truth_certificate'].get('train_replay_exact', False) for r in rows),
        'induced_rule_ids_exact': sum(r['induced_rule_correct'] for r in rows),
        'heldout_1d_exact': sum(sum(r['heldout_1d_exact']) for r in rows),
        'heldout_2d_exact': sum(sum(r['heldout_2d_exact']) for r in rows),
        'negative_rejections': sum(negative_ok.values()),
        'baseline_catalog_tasks_exact': sum(r['baseline_rule_correct'] and r['baseline_heldout_all_correct'] for r in rows),
        'induction_plus_certificate_and_test_ns': sum(r['induction']['compile_and_replay_ns'] + r['original_verification_and_test_ns'] for r in rows),
        'enumeration_plus_certificate_and_test_ns': sum(r['baseline_catalog']['enumeration_ns'] + r['catalog_original_verification_and_test_ns'] for r in rows),
        'catalog_candidate_programs_tested': sum(r['baseline_catalog']['candidates_scanned'] for r in rows),
        'catalog_train_replays': sum(r['baseline_catalog']['train_replays'] for r in rows),
        'induction_train_cells_observed': sum(r['induction'].get('train_cells_observed', 0) for r in rows),
    }
    g = CONTRACT['frozen_gate']
    passed = (
        metrics['unique_complete_tables'] == g['unique_complete_operator_tables']
        and metrics['independent_certificates_passed'] == g['independent_rule_certificate_passes']
        and metrics['induced_rule_ids_exact'] == g['unique_complete_operator_tables']
        and metrics['heldout_1d_exact'] == g['heldout_1d_exact']
        and metrics['heldout_2d_exact'] == g['heldout_2d_exact']
        and metrics['negative_rejections'] == g['negative_controls_rejected']
    )
    return {
        'contract': CONTRACT,
        'first_local_gate': 'P08_CLOSED_STENCIL_OPERATOR_INDUCTION_PASS' if passed else 'P08_CLOSED_STENCIL_OPERATOR_INDUCTION_FAIL',
        'metrics': metrics, 'rows': rows,
        'negative_controls': negatives, 'negative_control_expected_rejected': negative_ok,
        'total_study_wall_ns_including_synthetic_source_generation': time.perf_counter_ns() - started,
        'total_cost_scope': 'CPU-region timers; do not infer hardware energy/FLOPs/VRAM or direct-model cost',
        'flops': None, 'energy_joules': None, 'peak_ram_bytes': None, 'total_cost_usd': None,
        'global_Q1_to_Q7': 'OPEN',
        'JEPA_train_or_inference': 'NOT_RUN',
        'open_ended_opcode_invention': 'NOT_DEMONSTRATED',
        'source_family': 'synthetic_binary_radius1_periodic_CA',
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'machine': platform.machine()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    r = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf8') as f:
        json.dump(r, f, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps({'verdict':r['first_local_gate'],'metrics':r['metrics'],
                      'negative':r['negative_controls']}, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
