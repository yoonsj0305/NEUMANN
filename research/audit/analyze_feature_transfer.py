"""Inspect original opened feature arrays; no model, optimizer or new problem.

Use the original quotient_columns function body verbatim without importing its
Torch/model restoration dependencies. This is posthoc representation diagnosis,
not a counterfactual training experiment or replacement for M106's first result.
"""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from experiments import lp_feature_probe_v093 as f
from neumann1.lp_model_study_archive_v088 import load_study
from research.audit.analyze_retained_lp import decode, verify_source


def original_feature_function():
    path = ROOT / 'experiments/lp_equivalence_quotient_v099.py'
    body = path.read_text(encoding='utf-8')
    tree = ast.parse(body)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'quotient_columns')
    namespace = {'f': f, 'math': math, 'np': np}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['quotient_columns'], hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows):
    return {'originals': len(rows),
            'channel_std_median': [statistics.median(r[f'channel_{i}_std'] for r in rows) for i in range(8)],
            'channel_std_max': [max(r[f'channel_{i}_std'] for r in rows) for i in range(8)],
            'channel_under_1e_8_originals': [sum(r[f'channel_{i}_std'] < 1e-8 for r in rows) for i in range(8)],
            'channels_under_1e_8_per_original': sorted({r['channels_under_1e_8'] for r in rows})}


def analyze():
    feature, feature_hash = original_feature_function()
    manifest_path = ROOT / 'docs/experiments/results/v088_completed.manifest.json'
    train = load_study(manifest_path)['train_sources']
    folder = ROOT / 'docs/experiments/results/m106_bp_transfer_first'
    sources_path = folder / 'sources.json'
    manifest = json.loads(sources_path.read_bytes())
    groups = [('v088_opened_training', [(s['id'], {k: decode(v) for k,v in s['arrays'].items()}) for s in train])]
    transfer = []
    for entry in manifest['cases']:
        source = verify_source(folder / entry['identity']['file'], entry['identity'])
        transfer.append((source['metadata']['id'], {k: decode(v) for k,v in source['arrays'].items()}))
    groups.append(('M106_opened_transfer', transfer))
    rows = []
    # All supported scientific solver entry points fail closed in this analysis.
    with patch('scipy.optimize.linprog', side_effect=AssertionError('analysis must not solve')), \
         patch('scipy.optimize.milp', side_effect=AssertionError('analysis must not solve')):
        for designation, originals in groups:
            for case_id, raw in originals:
                D, cols = feature(raw)
                _, _, q = f.normalized(**raw)
                std = cols.std(axis=0)
                row = {'case_id': case_id, 'designation': designation,
                       'rows': D.shape[0], 'columns': D.shape[1],
                       'normalized_cost_std': float(q.std()),
                       'channels_under_1e_8': int(np.count_nonzero(std < 1e-8))}
                row.update({f'channel_{i}_std': float(std[i]) for i in range(8)})
                if designation == 'M106_opened_transfer':
                    half = D.shape[1] // 2
                    row['signed_pair_matrix_max_error'] = float(np.max(np.abs(D[:,:half] + D[:,half:])))
                    row['signed_pair_even_channels_max_error'] = float(np.max(np.abs(cols[:half,[0,1,4,5,6,7]] - cols[half:,[0,1,4,5,6,7]])))
                    row['signed_pair_odd_channels_max_error'] = float(np.max(np.abs(cols[:half,[2,3]] + cols[half:,[2,3]])))
                rows.append(row)
    out = ROOT / 'research/audit'
    fields = list(rows[-1])
    with (out/'FEATURE_TRANSFER_DIAGNOSTICS.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    result = {'kind': 'OPENED_POSTHOC_FEATURE_ANALYSIS',
              'original_function_sha256': feature_hash,
              'training_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              'M106_source_manifest_sha256': hashlib.sha256(sources_path.read_bytes()).hexdigest(),
              'groups': {name: summarize([r for r in rows if r['designation'] == name]) for name,_ in groups},
              'M106_max_pair_errors': {key: max(r[key] for r in rows if r['designation'] == 'M106_opened_transfer') for key in ('signed_pair_matrix_max_error','signed_pair_even_channels_max_error','signed_pair_odd_channels_max_error')},
              'new_model_forwards': 0, 'new_solver_calls': 0, 'new_training': 0, 'new_problems': 0,
              'boundary': 'Feature degeneration is observed, but does not prove missing-information impossibility, causality of ranking failure, or sufficiency of retraining. Scalar channels2/3 retain original correlations; original verifier and paid-certificate economics remain separate.',
              'decision': 'HOLD_LEARNING'}
    (out/'FEATURE_TRANSFER_DIAGNOSTICS.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2))
