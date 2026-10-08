"""Inspect retained opened primal/dual geometry, without a new LP or model call.

Numerical ranks are diagnostics, not exact proofs. The ideal full-rank basis
argument is stated separately in CERTIFICATE_GEOMETRY_CAUSAL_REVIEW.md.
"""
import hashlib
import json
from pathlib import Path
import statistics
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from threadpoolctl import threadpool_limits
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1.lp_model_study_archive_v088 import load_study
from research.audit.analyze_retained_lp import decode, verify_source, write_csv


def geometry(designation, case_id, raw, witness, source_hash):
    cert = verify_standard_form_certificate(**raw, **witness)
    if not cert['accepted']:
        raise ValueError('Retained original certificate not accepted')
    A, c = raw['A'], raw['c']
    x, y = np.asarray(witness['x']), np.asarray(witness['y'])
    support = np.flatnonzero(np.abs(x) > 1e-8)
    S = A[:, support]
    singular = np.linalg.svd(S, compute_uv=False)
    tolerance = max(S.shape) * np.finfo(float).eps * singular[0]
    rank = int(np.count_nonzero(singular > tolerance))
    slack = c - A.T @ y
    outside = np.ones(len(c), dtype=bool); outside[support] = False
    tight = np.flatnonzero(np.abs(slack) <= cert['dual_feasibility_tol'])
    tight_singular = np.linalg.svd(A[:, tight], compute_uv=False)
    tight_tolerance = max(A[:, tight].shape) * np.finfo(float).eps * tight_singular[0]
    tight_rank = int(np.count_nonzero(tight_singular > tight_tolerance))
    return {'case_id': case_id, 'designation': designation,
            'source_array_sha256': source_hash,
            'rows': A.shape[0], 'columns': A.shape[1],
            'positive_support_size': len(support),
            'support_matrix_numerical_rank': rank,
            'active_equality_dual_nullity': A.shape[0] - rank,
            'positive_support_fraction': len(support) / len(c),
            'dual_tight_column_count': len(tight),
            'zero_primal_dual_tight_columns': len(set(tight)-set(support)),
            'dual_tight_columns_numerical_rank': tight_rank,
            'tightness_diagnostic_tolerance': cert['dual_feasibility_tol'],
            'support_rank_tolerance': float(tolerance),
            'support_min_singular_value': float(singular[-1]),
            'support_max_singular_value': float(singular[0]),
            'min_positive_primal': float(x[support].min()),
            'active_stationarity_max_error': float(np.abs(slack[support]).max()),
            'inactive_min_reduced_slack': float(slack[outside].min()),
            'inactive_max_reduced_slack': float(slack[outside].max()),
            'original_certificate_accepted': cert['accepted']}


def summarize(rows):
    return {'originals': len(rows),
            'support_sizes': sorted({r['positive_support_size'] for r in rows}),
            'dual_nullities': sorted({r['active_equality_dual_nullity'] for r in rows}),
            'positive_support_fractions': sorted({r['positive_support_fraction'] for r in rows}),
            'dual_tight_column_counts': sorted({r['dual_tight_column_count'] for r in rows}),
            'zero_primal_dual_tight_counts': sorted({r['zero_primal_dual_tight_columns'] for r in rows}),
            'dual_tight_ranks': sorted({r['dual_tight_columns_numerical_rank'] for r in rows}),
            'all_active_support_full_rank': all(r['support_matrix_numerical_rank'] == r['positive_support_size'] for r in rows),
            'active_stationarity_max_error': max(r['active_stationarity_max_error'] for r in rows),
            'inactive_min_reduced_slack': min(r['inactive_min_reduced_slack'] for r in rows),
            'median_positive_primal': statistics.median(r['min_positive_primal'] for r in rows)}


def analyze():
    train_path = ROOT / 'docs/experiments/results/v088_completed.manifest.json'
    train = load_study(train_path)['train_sources']
    folder = ROOT / 'docs/experiments/results/m106_bp_transfer_first'
    source_path, report_path = folder / 'sources.json', folder / 'report.json'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != '61b3b5cea713c7265379c039f97cb5eb1c656031f14aba0ee70176da776fc7e8':
        raise ValueError('M106 first source manifest hash drift')
    if hashlib.sha256(report_path.read_bytes()).hexdigest() != 'fd0f069bb43c8f4f471578de35a6f70af2c418b46b701260f12cd1d27bebd6b8':
        raise ValueError('M106 first report hash drift')
    report = json.loads(report_path.read_bytes())
    manifest = json.loads(source_path.read_bytes())
    native = {r['case_id']: r['witness'] for r in report['records']
              if r['route'] == 'NATIVE' and r['phase'] == 'timed' and r['repeat'] == 0}
    rows = []
    with threadpool_limits(1), \
         patch('scipy.optimize.linprog', side_effect=AssertionError('No new optimizer')), \
         patch('scipy.optimize.milp', side_effect=AssertionError('No new optimizer')):
        for s in train:
            raw = {k: decode(v) for k, v in s['arrays'].items()}
            digest = storage.input_digest(raw)
            if digest != s['sha256']:
                raise ValueError('Training source hash drift')
            rows.append(geometry('v088_opened_training', s['id'], raw, s['label']['witness'], digest))
        for entry in manifest['cases']:
            s = verify_source(folder / entry['identity']['file'], entry['identity'])
            raw = {k: decode(v) for k, v in s['arrays'].items()}
            case_id = s['metadata']['id']
            rows.append(geometry('M106_opened_transfer', case_id, raw, native[case_id], storage.input_digest(raw)))
    out = ROOT / 'research/audit'
    write_csv(out / 'CERTIFICATE_GEOMETRY_DIAGNOSTICS.csv', rows)
    result = {'kind': 'RETAINED_OPENED_CERTIFICATE_GEOMETRY_ANALYSIS',
              'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (train_path, source_path, report_path,
                                    ROOT / 'neumann1/lp_basis_headroom_v082.py',
                                    ROOT / 'experiments/lp_quotient_refit_v100.py')},
              'groups': {name: summarize([r for r in rows if r['designation'] == name])
                         for name in ('v088_opened_training', 'M106_opened_transfer')},
              'new_solver_calls': 0, 'new_model_forwards': 0, 'new_problems': 0,
              'rank_scope': 'Numerical SVD default epsilon-scaled threshold; no exact rank or uniqueness claim for arbitrary floating input.',
              'causal_boundary': 'Full-rank positive basis fixes the dual through stationarity in the ideal original generator. Sparse BP active equalities leave dual freedom. This explains loss of an automatic certificate property, but not every ranking or cost failure.',
              'decision': 'HOLD_LEARNING'}
    (out / 'CERTIFICATE_GEOMETRY_DIAGNOSTICS.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2))
