"""First bounded learned-model study. Explicit runner only, never CI fitting.

All models see A,b,c-derived observables only. Final generation is downstream
of completed frozen fitting; targets cannot enter any inference adapter.
"""
from __future__ import annotations

import base64
import hashlib
import math
import random
from statistics import geometric_mean, median
from time import perf_counter_ns

import numpy as np
import torch
from torch.nn import functional as F
from threadpoolctl import threadpool_info, threadpool_limits

from experiments.lp_state_models_v087 import roster, tensor_input
from neumann1 import lp_model_admission_v087 as admission
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

NAMES = ('compact16', 'full16', 'point16', 'full128')
SEEDS = (87001, 87002)
CLASSICS = admission.ROUTES[:7] + ('scale_portfolio',)
LEARNERS = tuple(f'{name}_s{seed}' for seed in SEEDS for name in NAMES)
ROUTES = CLASSICS + LEARNERS


def protocol():
    return {'schema': 'neumann.lp-first-model-study.v1', 'runtime': admission.RUNTIME,
        'threads': 1, 'openblas_coretype': 'HASWELL',
        'admission_json_sha256': '92654a458e1c8f6e3856737a37a9a40b959423cae544220236a5292caee5638a',
        'train_examples': 48, 'train_seed_base': 88100, 'train_rows': [32, 64],
        'final_seed_base': 88900, 'final_examples': 12,
        'final_groups': {'iid': [64], 'size_surface_shift': [128]},
        'conditions': [1, 1000], 'width_factor': 16,
        'epochs': 12, 'fit_seconds_cap': 240., 'seeds': list(SEEDS),
        'optimizer': 'Adam', 'lr': .001, 'weight_decay': 0.,
        'loss': 'coarse balanced BCE + selected balanced BCE + 0.1*(scaled primal MSE + scaled dual MSE)',
        'checkpoint': 'last epoch only, no validation selection',
        'parameter_cap': 400000, 'models': list(NAMES), 'routes': list(ROUTES),
        'order_seed': 88991, 'warmups': 1, 'repeats': 3, 'budget_s': 5.,
        'ratio_max': .8, 'minimum_wins_per_group': 4,
        'minimum_exact_basis_per_group': 4, 'amortization_queries': 10000,
        'global_q3': 'OPEN', 'global_q4': 'OPEN', 'scope': 'constructed LP candidate roster only'}


def specs(split):
    """Prospective specs only; neither generate nor open a final case here."""
    if split == 'train':
        return [dict(id=f'train{i}', group='train', rows=(32, 64)[i % 2],
                     condition=(1, 1000)[(i // 2) % 2], seed=88100+i, surface=False)
                for i in range(48)]
    if split == 'final':
        return [dict(id=f'final{i}', group='iid' if i < 6 else 'size_surface_shift',
                     rows=64 if i < 6 else 128, condition=(1, 1000)[i % 2],
                     seed=88900+i, surface=i >= 6) for i in range(12)]
    raise ValueError('unregistered split')


def generate(spec):
    from neumann1.lp_basis_headroom_v082 import generate_case
    m = spec['rows']
    case = generate_case({'id': spec['id'], 'pair_id': spec['id'], 'rows': m,
        'width_factor': 16, 'cols': 16*m, 'condition_number': spec['condition'],
        'replicate': 0, 'seed': spec['seed']})
    A, b, c = storage.normalized(case['A'], case['b'], case['c'])
    if spec['surface']:
        # Equivalent row transformation, permutation and positive column scaling.
        # Labels are recomputed in the transformed original problem, never passed
        # to the model or used for selection.
        rng = np.random.default_rng(spec['seed'] + 100000)
        order = rng.permutation(m)
        sign = rng.choice([-1., 1.], size=m)
        A, b = A[order] * sign[:, None], b[order] * sign
        scaling = np.exp(rng.uniform(-1.5, 1.5, size=A.shape[1]))
        A, c = A * scaling, c * scaling
    raw = {'A': A, 'b': b, 'c': c}
    label = storage.candidate_once(raw, case['oracle_basis'], 'dataset_label_setup')
    if not label['accepted']:
        raise ValueError('constructed label rejected by original certificate')
    return raw, label


def packed_source(spec, raw, label):
    return {**spec, 'cols': raw['A'].shape[1], 'sha256': storage.input_digest(raw),
            'arrays': {k: storage.encode_array(v) for k, v in raw.items()}, 'label': label}


def scaled_targets(raw, label):
    lengths = np.linalg.norm(raw['A'], axis=0)
    bscale = max(1., float(np.linalg.norm(raw['b'])))
    cscale = max(1., float(np.sqrt(np.mean((raw['c']/lengths)**2))))
    # x is in column-normalized coordinates; y in original row coordinates.
    return (np.asarray(label['witness']['x']) * lengths / bscale,
            np.asarray(label['witness']['y']) / cscale)


def loss(output, basis, x, y):
    target = torch.zeros_like(output['coarse'])
    target[basis] = 1.
    selected = output['selected']
    weight = torch.tensor(15., dtype=target.dtype)
    coarse = F.binary_cross_entropy_with_logits(output['coarse'], target, pos_weight=weight)
    refined = F.binary_cross_entropy_with_logits(output['scores'][selected], target[selected],
                                                pos_weight=weight)
    return coarse + refined + .1*(F.mse_loss(output['x'], x) + F.mse_loss(output['y'], y))


def pack_weights(model):
    result = {}
    for k, value in model.state_dict().items():
        a = value.detach().cpu().numpy().astype('<f4')
        result[k] = {'shape': list(a.shape), 'base64': base64.b64encode(a.tobytes()).decode()}
    digest = hashlib.sha256()
    for k, v in result.items():
        digest.update(k.encode()); digest.update(base64.b64decode(v['base64']))
    return result, digest.hexdigest()


def fit_one(model, data, seed, name):
    """Frozen last-epoch fitting, no access to final data or tuning callbacks."""
    started = perf_counter_ns()
    torch.manual_seed(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    epochs = []
    model.train()
    for epoch in range(12):
        order = list(range(len(data)))
        random.Random(88191 + epoch).shuffle(order)
        losses = []
        for i in order:
            tensors, basis, x, y = data[i]
            optimizer.zero_grad(set_to_none=True)
            objective = loss(model(*tensors), basis, x, y)
            if not torch.isfinite(objective): raise ValueError('nonfinite first-fit loss')
            objective.backward(); optimizer.step()
            losses.append(float(objective.detach()))
            if (perf_counter_ns()-started)/1e9 > 240.:
                return {'completed': False, 'reason': 'fit deadline', 'epochs': epochs,
                        'fit_ms': (perf_counter_ns()-started)/1e6, 'name': name, 'seed': seed}
        epochs.append({'epoch': epoch+1, 'mean_loss': sum(losses)/len(losses)})
    model.eval()
    weights, sha = pack_weights(model)
    elapsed = (perf_counter_ns()-started)/1e6
    return {'completed': elapsed <= 240000., 'epochs': epochs, 'fit_ms': elapsed,
            'name': name, 'seed': seed, 'parameters': sum(p.numel() for p in model.parameters()),
            'weights': weights, 'weights_sha256': sha}


def learned_observe(A, b, c, model):
    """Same paid answer/basis/repair authority for every learner. No target argument."""
    started = perf_counter_ns()
    raw = dict(A=A, b=b, c=c)
    D, rows, cols = admission.features(A, b, c)
    tensors = tensor_input(D, rows, cols)
    with torch.inference_mode(): output = model(*tensors)
    indices = torch.argsort(output['scores'], descending=True, stable=True)[:A.shape[0]].tolist()
    # Both x/y answer and executable basis are allowed for all models.
    bscale = max(1., float(np.linalg.norm(b)))
    cscale = max(1., float(np.sqrt(np.mean((c/np.linalg.norm(A, axis=0))**2))))
    witness = {'x': (output['x'].numpy()*bscale/np.linalg.norm(A, axis=0)).tolist(),
               'y': (output['y'].numpy()*cscale).tolist()}
    answer = verify_standard_form_certificate(**raw, **witness)
    proposal_ms = (perf_counter_ns()-started)/1e6
    remaining = 5. - proposal_ms/1000.
    execution = None
    if not answer['accepted'] and remaining > 0:
        execution = admission.checked_head(raw, indices, remaining)
        accepted = execution['accepted']
        winner = execution['witness']
    else:
        accepted, winner = answer['accepted'], witness
    elapsed = (perf_counter_ns()-started)/1e6
    return {'accepted': bool(accepted and elapsed <= 5000.), 'witness': winner,
            'total_ms': elapsed, 'proposal_ms': proposal_ms,
            'answer': {'certificate': answer, 'witness': witness}, 'execution': execution,
            'indices': indices, 'state_columns': output['state_columns'],
            'edge_multiply_terms': output['edge_multiply_terms']}


def summarize(records, sources, training, setup_ms):
    expected = {(s['id'], r, i) for s in sources for r in ROUTES for i in (-1,0,1,2)}
    keys = [(r['case_id'],r['route'],r['repeat']) for r in records]
    if len(sources) != 12 or len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('final coverage drift')
    if any(type(r['accepted']) is not bool or not math.isfinite(r['total_ms']) or r['total_ms'] <= 0 for r in records):
        raise ValueError('invalid cost/capability evidence')
    if not all(r['accepted'] for r in records):
        return {'decision': 'CAPABILITY_UNREACHED', 'global_q3': 'OPEN', 'global_q4': 'OPEN'}
    timings = {(s['id'],route):median(r['total_ms'] for r in records if r['case_id']==s['id']
               and r['route']==route and r['repeat']>=0) for s in sources for route in ROUTES}
    tests = []
    for seed in SEEDS:
        compact, full = f'compact16_s{seed}', f'full16_s{seed}'
        fit_ms = setup_ms + training[compact]['fit_ms']
        for group in ('iid','size_surface_shift'):
            ids = [s['id'] for s in sources if s['group']==group]
            if len(ids)!=6: raise ValueError('final group drift')
            cr, lr, ar, amortized, savings = [],[],[],[],[]
            exact = 0
            for case in ids:
                cost = timings[case,compact]
                classical = min(timings[case,r] for r in CLASSICS)
                learned = min(timings[case,r] for r in LEARNERS if not r.startswith('compact16'))
                cr.append(cost/classical); lr.append(cost/learned); ar.append(cost/timings[case,full])
                amortized.append((cost+fit_ms/10000.)/classical)
                savings.append(classical-cost)
                exact += int(all(r['execution'] is not None and r['execution']['candidate']['accepted']
                    for r in records if r['case_id']==case and r['route']==compact))
            passed = (max(geometric_mean(cr),geometric_mean(lr),geometric_mean(ar),geometric_mean(amortized))<=.8
                      and min(sum(x<=.8 for x in cr),sum(x<=.8 for x in lr),sum(x<=.8 for x in ar))>=4
                      and exact>=4)
            avg_saving = sum(savings)/len(savings)
            tests.append({'seed':seed,'group':group,'classical_ratio':geometric_mean(cr),
                'best_learned_direct_ratio':geometric_mean(lr),'own_no_compression_ratio':geometric_mean(ar),
                'training_amortized_classical_ratio_at_10000':geometric_mean(amortized),
                'exact_basis_cases':exact,'break_even_queries':math.ceil(fit_ms/avg_saving) if avg_saving>0 else None,
                'passed':passed})
    return {'decision':'BOUNDED_CANDIDATE_ROSTER_PASS_NOT_GLOBAL_Q3_Q4' if all(t['passed'] for t in tests)
            else 'FIRST_LEARNED_CANDIDATE_GATE_FAILED', 'tests':tests,'global_q3':'OPEN','global_q4':'OPEN'}


def run_study(checkpoint):
    """Checkpoint callback durably saves stages; no held-out access before fit."""
    import highspy, scipy, sys, os
    torch.set_num_threads(1); torch.set_num_interop_threads(1); torch.use_deterministic_algorithms(True)
    environment = {'python':list(sys.version_info[:2]), 'numpy':np.__version__,
                   'scipy':scipy.__version__,'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if any(environment[k]!=v for k,v in admission.RUNTIME.items()) or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':
        raise RuntimeError('first study runtime drift')
    report = {'protocol':protocol(),'environment':environment,'train_sources':[],
              'training':{},'final_sources':[],'records':[],'stage':'preflight'}
    with threadpool_limits(1):
        environment['threadpools']=threadpool_info()
        if not environment['threadpools'] or any(p['num_threads']!=1 for p in environment['threadpools']):
            raise RuntimeError('first study thread drift')
        setup = perf_counter_ns(); data=[]
        for spec in specs('train'):
            raw,label=generate(spec)
            D,rows,cols=admission.features(**raw)
            x,y=scaled_targets(raw,label)
            data.append((tensor_input(D,rows,cols),torch.tensor(label['indices']),
                         torch.tensor(x,dtype=torch.float32),torch.tensor(y,dtype=torch.float32)))
            report['train_sources'].append(packed_source(spec,raw,label))
        report['training_setup_ms']=(perf_counter_ns()-setup)/1e6
        report['stage']='training_data_frozen'; checkpoint(report)
        models={}
        for seed in SEEDS:
            for name,model in roster(seed).items():
                key=f'{name}_s{seed}'; models[key]=model
                fit=fit_one(model,data,seed,name); report['training'][key]=fit
                report['stage']=f'fit_{key}'; checkpoint(report)
                print(key,fit['completed'],round(fit['fit_ms'],2),flush=True)
                if not fit['completed']:
                    report['summary']={'decision':'FIRST_FIT_BUDGET_FAILED','global_q3':'OPEN','global_q4':'OPEN'}
                    return report
        # No final input generated until EVERY registered checkpoint is settled.
        report['stage']='all_fits_frozen_final_still_unopened'; checkpoint(report)
        inputs={}
        for spec in specs('final'):
            raw,label=generate(spec); inputs[spec['id']]=raw
            report['final_sources'].append(packed_source(spec,raw,label))
        report['stage']='final_inputs_frozen'; checkpoint(report)
        for repeat in (-1,0,1,2):
            order=[(case,route) for case in inputs for route in ROUTES]
            random.Random(88991+repeat).shuffle(order)
            for case,route in order:
                raw=inputs[case]
                if route=='scale_portfolio':
                    row=storage.discovery_once(**raw)
                    row['accepted']=bool(row['accepted'] and row['total_ms']<=5000.)
                else:
                    row=(admission.observe(raw,route,None,{}) if route in CLASSICS
                         else learned_observe(**raw,model=models[route]))
                report['records'].append({'case_id':case,'route':route,'repeat':repeat,
                    'weights_sha256':report['training'][route]['weights_sha256'] if route in LEARNERS else None,**row})
                checkpoint({'stage':'observation','record':report['records'][-1]})
            report['stage']=f'final_repeat_{repeat}'; checkpoint(report)
            print(report['stage'],len(report['records']),flush=True)
        report['summary']=summarize(report['records'],report['final_sources'],report['training'],report['training_setup_ms'])
        report['stage']='completed'; checkpoint(report)
    return report


def validate_report(report):
    """Only decode retained inputs/weights and check original equations; no solve/forward."""
    if report['protocol']!=protocol() or report['stage']!='completed':
        raise ValueError('completed frozen protocol required')
    if any(report['environment'].get(k)!=v for k,v in admission.RUNTIME.items()):
        raise ValueError('runtime evidence drift')
    if not report['environment']['threadpools'] or any(x['num_threads']!=1 for x in report['environment']['threadpools']):
        raise ValueError('thread evidence drift')
    if set(report['training'])!=set(LEARNERS): raise ValueError('missing fitted comparator')
    for route,fit in report['training'].items():
        if not fit['completed'] or not 0<fit['fit_ms']<=240000. or len(fit['epochs'])!=12:
            raise ValueError('fit budget/checkpoint drift')
        if [e['epoch'] for e in fit['epochs']]!=list(range(1,13)) or any(
                not math.isfinite(e['mean_loss']) for e in fit['epochs']):
            raise ValueError('training loss ledger drift')
        digest=hashlib.sha256(); count=0
        for k,v in fit['weights'].items():
            raw_bytes=base64.b64decode(v['base64'],validate=True)
            count+=math.prod(v['shape'])
            a=np.frombuffer(raw_bytes,dtype='<f4')
            if a.size!=math.prod(v['shape']) or not np.isfinite(a).all():
                raise ValueError('weight bytes drift')
            digest.update(k.encode()); digest.update(raw_bytes)
        expected=299268 if route.startswith('full128') else 611 if route.startswith('point16') else 5156
        if count!=expected or count!=fit['parameters'] or digest.hexdigest()!=fit['weights_sha256']:
            raise ValueError('checkpoint identity drift')
    inputs={}
    for split in ('train','final'):
        source=report[f'{split}_sources']; expected=specs(split)
        if len(source)!=len(expected) or [s['id'] for s in source]!=[s['id'] for s in expected]:
            raise ValueError('source coverage drift')
        for s,original_spec in zip(source,expected):
            if any(s[k]!=v for k,v in original_spec.items()) or s['cols']!=16*s['rows']:
                raise ValueError('split metadata drift')
            m,n=s['rows'],s['cols']
            raw={k:storage.decode_array(s['arrays'][k],shape) for k,shape in
                 (('A',(m,n)),('b',(m,)),('c',(n,)))}
            if storage.input_digest(raw)!=s['sha256'] or not verify_standard_form_certificate(
                    **raw,**s['label']['witness'])['accepted']:
                raise ValueError('original source/label evidence drift')
            if split=='final': inputs[s['id']]=raw
    for r in report['records']:
        raw=inputs[r['case_id']]
        if r['accepted'] and (r['total_ms']>5000. or r['witness'] is None or not
                verify_standard_form_certificate(**raw,**r['witness'])['accepted']):
            raise ValueError('original acceptance witness drift')
        if r['route'] not in LEARNERS: continue
        if r['weights_sha256']!=report['training'][r['route']]['weights_sha256']:
            raise ValueError('inference checkpoint reference drift')
        answer=r['answer']; execution=r['execution']
        if verify_standard_form_certificate(**raw,**answer['witness'])['accepted']!=answer['certificate']['accepted']:
            raise ValueError('answer certificate drift')
        if not 0<=r['proposal_ms']<=r['total_ms']: raise ValueError('proposal ledger drift')
        if execution:
            candidate=execution['candidate']; native=execution['native']
            if r['witness']!=execution['witness'] or r['accepted']!=(execution['accepted'] and r['total_ms']<=5000.):
                raise ValueError('execution capability drift')
            if r['total_ms']+1e-9<r['proposal_ms']+execution['total_ms'] or not (
                    0<execution['budget_s']<=5.-r['proposal_ms']/1000.+1e-9):
                raise ValueError('omitted upstream cost/deadline')
            if candidate['indices']!=r['indices'] or execution['fallback_used']!=(native is not None):
                raise ValueError('basis/fallback ledger drift')
            if candidate['accepted'] and candidate['witness'] is None:
                raise ValueError('missing basis witness')
            if candidate['witness'] is not None and verify_standard_form_certificate(
                    **raw,**candidate['witness'])['accepted']!=candidate['accepted']:
                raise ValueError('basis certificate drift')
            if native and execution['total_ms']+1e-9<candidate['total_ms']+native['total_ms']:
                raise ValueError('omitted repair cost')
        elif r['accepted']!=(answer['certificate']['accepted'] and r['total_ms']<=5000.):
            raise ValueError('answer-only capability drift')
        m,n=raw['A'].shape
        width=128 if r['route'].startswith('full128') else 16
        columns=min(n,2*m) if r['route'].startswith('compact16') else n
        terms=0 if r['route'].startswith('point16') else 2*m*n*width+4*m*columns*width
        if r['state_columns']!=columns or r['edge_multiply_terms']!=terms:
            raise ValueError('model architecture trace drift')
    if not math.isfinite(report['training_setup_ms']) or report['training_setup_ms']<0:
        raise ValueError('training setup cost drift')
    if report['summary']!=summarize(report['records'],report['final_sources'],report['training'],report['training_setup_ms']):
        raise ValueError('derived final gate drift')
