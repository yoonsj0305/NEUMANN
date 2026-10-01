"""Opened-training-only shortlist diagnostic, never a final accuracy/cost audit.

Restore every v088 checkpoint without fitting. Do not load/use final_sources or
records for selection. Labels are used only to score already produced indices.
"""
import argparse
import base64
import json
from pathlib import Path

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from experiments.lp_state_models_v087 import roster, tensor_input
from experiments.lp_model_study_v088 import pack_weights, SEEDS
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage


def restore_models(training):
    models = {}
    for seed in SEEDS:
        for name, model in roster(seed).items():
            key = f'{name}_s{seed}'
            state = {k: torch.tensor(np.frombuffer(base64.b64decode(v['base64'], validate=True),
                     dtype='<f4').reshape(v['shape']).copy())
                     for k, v in training[key]['weights'].items()}
            model.load_state_dict(state, strict=True)
            if pack_weights(model)[1] != training[key]['weights_sha256']:
                raise ValueError('restored checkpoint identity drift')
            models[key] = model.eval()
    return models


def raw_source(source):
    m, n = source['rows'], source['cols']
    raw = {k: storage.decode_array(source['arrays'][k], shape)
           for k, shape in (('A', (m, n)), ('b', (m,)), ('c', (n,)))}
    if storage.input_digest(raw) != source['sha256']:
        raise ValueError('retained input identity drift')
    return raw


def selections(raw, models):
    """Advisory selection sees only A,b,c; never accepts a label argument."""
    m = raw['A'].shape[0]
    D, rows, cols = admission.features(**raw)
    result = {
        'centred_residual': np.argsort(cols[:, 1], kind='stable')[:2*m].tolist(),
        'absolute_residual': np.argsort(np.abs(cols[:, 1]), kind='stable')[:2*m].tolist(),
        'minimum_norm_primal': np.argsort(-cols[:, 2], kind='stable')[:2*m].tolist(),
    }
    tensors = tensor_input(D, rows, cols)
    with torch.inference_mode():
        for key, model in models.items():
            scores = model(*tensors)['scores']
            result[key] = torch.argsort(scores, descending=True, stable=True)[:2*m].tolist()
    return result


def screen(train_sources, training):
    models = restore_models(training)
    records = []
    for source in train_sources:
        raw = raw_source(source)
        proposals = selections(raw, models)
        # Offline development scoring only, after target-free inference.
        basis = set(source['label']['indices'])
        for route, indices in proposals.items():
            missing = sorted(basis - set(indices))
            records.append({'case_id': source['id'], 'source_sha256': source['sha256'],
                            'route': route, 'indices': indices, 'missing': missing,
                            'covers_basis': not missing})
    summary = {route: {'covers': sum(r['covers_basis'] for r in records if r['route']==route),
                      'cases': len(train_sources)} for route in sorted({r['route'] for r in records})}
    return {'schema': 'neumann.lp-shortlist-development.v1', 'split': 'v088_opened_train_only',
            'new_fitting': False, 'final_evaluation': False, 'cost_claim': False,
            'shortlist_columns': 'min(n,2m)', 'records': records, 'summary': summary,
            'global_q3': 'OPEN', 'global_q4': 'OPEN'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    # Reserve output before any work; accidental reruns cannot replace first data.
    with Path(args.output).open('x') as output:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        with threadpool_limits(1):
            retained = load_study('docs/experiments/results/v088_completed.manifest.json')
            result = screen(retained['train_sources'], retained['training'])
        json.dump(result, output, sort_keys=True, separators=(',', ':'))
        output.write('\n')
    print(json.dumps(result['summary'], indent=2), flush=True)


if __name__ == '__main__':
    main()
