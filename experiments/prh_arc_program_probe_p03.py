"""P0.3: bounded ARC-AGI-1 *opened development* executable-program synthesis.

Tests a verifiable program-synthesis interface rather than a JEPAs/PRH claim.
The mini-DSL and dataset choices were influenced by known opened ARC tasks;
this is neither blind evaluation nor evidence of a newly invented operator.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
import numpy as np

SCHEMA = 'neumann.prh.arc.program-probe.p03.v1'
CONTRACT = {
    'schema': SCHEMA,
    'stage': 'OPENED_DEVELOPMENT_NOT_HOLDOUT',
    'task_ids': ['007bbfb7', '08ed6ac7', '0d3d703e', '05f2a901'],
    'fixture_source': 'fchollet/ARC-AGI data/training, Apache-2.0',
    'test_outputs_for_training': False,
    'test_outputs_for_selection': False,
    'claims': {
       'jepa_run': False, 'new_operator_invented': False,
       'frontier_gap': False, 'global_q1_to_q7': 'OPEN',
    },
    'fallback': 'ABSTAIN_ON_NO_PROGRAM_OR_AMBIGUOUS_TEST_PREDICTIONS',
}


def palette_program(training: list[dict]):
    """Infer per-color map from pairs; never from test output."""
    mapping = {}
    for pair in training:
        x, y = np.asarray(pair['input']), np.asarray(pair['output'])
        if x.shape != y.shape:
            return None
        for source in np.unique(x):
            produced = np.unique(y[x == source])
            if len(produced) != 1:
                return None
            previous = mapping.setdefault(int(source), int(produced[0]))
            if previous != int(produced[0]):
                return None
    if len(mapping) == 0:
        return None
    return mapping


def apply_palette(x, mapping):
    out = np.empty_like(x)
    for value in np.unique(x):
        if int(value) not in mapping:
            raise ValueError('unseen-color-no-map')
        out[x == value] = mapping[int(value)]
    return out


def column_rank(x):
    """Recolor monochrome vertical bars by descending height, zero stays zero."""
    x = np.asarray(x, dtype=np.int64)
    active = np.where(np.any(x != 0, axis=0))[0]
    if len(active) < 2 or len(active) > 9:
        raise ValueError('not-2-to-9-bars')
    counts = [(int(np.count_nonzero(x[:, c])), int(c)) for c in active]
    if len({n for n, _ in counts}) != len(counts):
        raise ValueError('ambiguous-column-height-tie')
    # Unique color allowed per bar, any input palette; no color label read.
    if any(len(set(x[:, c]) - {0}) != 1 for c in active):
        raise ValueError('multicolor-bar')
    out = np.zeros_like(x)
    for rank, (_, col) in enumerate(sorted(counts, reverse=True), start=1):
        out[x[:, col] != 0, col] = rank
    return out


def candidate_functions(training):
    """Fixed, interpretable candidate grammar, no task ID conditionals."""
    mp = palette_program(training)
    fns = [
        ('identity', lambda x: x),
        ('flip_lr', np.fliplr),
        ('flip_ud', np.flipud),
        ('rot90', lambda x: np.rot90(x, 1)),
        ('rot180', lambda x: np.rot90(x, 2)),
        ('rot270', lambda x: np.rot90(x, 3)),
        ('transpose', lambda x: x.T),
        ('tile_2x2', lambda x: np.tile(x, (2, 2))),
        ('tile_3x3', lambda x: np.tile(x, (3, 3))),
        ('kron_nonzero_first', lambda x: np.kron(x != 0, x)),
        ('kron_nonzero_second', lambda x: np.kron(x, x != 0)),
        ('column_rank_by_height', column_rank),
    ]
    if mp is not None:
        fns.append(('inferred_color_map', lambda x: apply_palette(x, mp)))
    return fns


def synthesize(training: list[dict]):
    """Every program is executed against every example without an oracle."""
    winners = []
    eval_count = 0
    errors = []
    if not training:
        return {'status': 'ABSTAIN_EMPTY_TRAIN', 'program_names': [], 'eval_count': 0}, []
    candidates = candidate_functions(training)
    for name, fn in candidates:
        ok = True
        for pair in training:
            x, expected = np.asarray(pair['input'], dtype=np.int64), np.asarray(pair['output'], dtype=np.int64)
            eval_count += 1
            try:
                actual = fn(x)
                if not np.array_equal(actual, expected):
                    ok = False
                    break
            except (ValueError, IndexError, TypeError):
                ok = False
                break
        if ok:
            winners.append((name, fn))
    return {
        'status': 'CANDIDATES_FOUND' if winners else 'ABSTAIN_NO_PROGRAM',
        'program_names': [name for name, _ in winners],
        'eval_count': eval_count,
        'candidate_count': len(candidates),
        'errors': errors,
    }, winners


def predict_with_consensus(winners, test_input):
    """Only release output when all training-consistent programs agree."""
    if not winners:
        return None, 'ABSTAIN_NO_PROGRAM'
    predictions = []
    for _, fn in winners:
        try:
            predictions.append(np.asarray(fn(np.asarray(test_input, dtype=np.int64))))
        except (ValueError, IndexError, TypeError):
            return None, 'ABSTAIN_TEST_EXECUTION'
    if any(not np.array_equal(predictions[0], p) for p in predictions[1:]):
        return None, 'ABSTAIN_DISAGREEMENT'
    return predictions[0].tolist(), 'PREDICT_UNANIMOUS'


def score_opened_task(task: dict, task_id: str):
    started = time.perf_counter_ns()
    # Mechanism sees only TRAIN list; ARC test outputs used only in scoring below.
    record, winners = synthesize(task['train'])
    predictions = [predict_with_consensus(winners, row['input']) for row in task['test']]
    search_and_run_ns = time.perf_counter_ns() - started
    exact = [pred is not None and pred == row['output'] for (pred, _), row in zip(predictions, task['test'])]
    return {
        'task_id': task_id,
        'synthetic': False,
        'source': 'official public ARC-AGI-1 training/opened development',
        'train_count': len(task['train']),
        'test_count': len(task['test']),
        'programs': record['program_names'],
        'search_status': record['status'],
        'prediction_status': [status for _, status in predictions],
        'test_exact': exact,
        'task_solved': bool(all(exact)),
        'program_evaluations': record['eval_count'],
        'candidate_count': record['candidate_count'],
        'search_plus_prediction_wall_ns': search_and_run_ns,
    }


def run(fixtures: Path):
    rows = []
    missing = []
    for task_id in CONTRACT['task_ids']:
        path = fixtures / f'{task_id}.json'
        if not path.exists():
            missing.append(task_id)
            continue
        rows.append(score_opened_task(json.loads(path.read_text()), task_id))
    return {
        'contract': CONTRACT,
        'rows': rows,
        'unavailable_task_ids': missing,
        'opened_dev_solved': sum(row['task_solved'] for row in rows),
        'opened_dev_total': len(rows),
        'global_q1_to_q7': 'OPEN',
        'new_program_invention': 'NOT_DEMONSTRATED',
        'jepa_training': 'NOT_RUN',
        'complete_iso_capability': 'NOT_MEASURED',
        'energy_joule': None,
        'flops': None,
        'peak_memory_bytes': None,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path, default=Path(__file__).parent / 'fixtures' / 'arc_agi1_opened')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.fixtures)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write('\n')
    print(json.dumps({'solved': result['opened_dev_solved'], 'total': result['opened_dev_total'], 'rows': result['rows']}, indent=2))


if __name__ == '__main__':
    main()
