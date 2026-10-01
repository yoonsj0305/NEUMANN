"""Single frozen opened-input pass; portable replay never proposes again."""
import math
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from experiments import lp_selector_probe_v093 as prior
from experiments.lp_input_compaction_v094 import features,propose
from experiments.lp_state_models_v087 import tensor_input
from neumann1.lp_selector_archive_v093 import load_probe
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

SEEDS=(87001,87002)
ROUTES=tuple(f'{name}_s{s}' for s in SEEDS for name in ('point','full','compact'))


def protocol():
    return {'schema':'neumann.lp-input-probe.v1','runtime':prior.protocol()['runtime'],
        'source_parent_sha256':prior.protocol()['parents']['v088'],
        'reference_sha256':'0530cd6fe39630ee6428174240c87f640f24eca8699c5e2cb2dffa2b94e30077',
        'cases':48,'routes':list(ROUTES),'cg_steps':5,'new_fitting':False,'timing':False,
        'final_evaluation':False,'minimum_coverage':36,'maximum_loss':1,'graph_ratio_max':.125,
        'global_q3':'OPEN','global_q4':'OPEN'}


def summarize(records,reference):
    expected={(f'train{i}',route) for i in range(48) for route in ROUTES}
    keys=[(r['case_id'],r['route']) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:raise ValueError('coverage drift')
    stats={route:{'shortlist_covers':sum(r['shortlist_covers'] for r in records if r['route']==route),
        'basis_certified':sum(r['candidate']['accepted'] for r in records if r['route']==route)} for route in ROUTES}
    tests=[]
    by={(r['case_id'],r['route']):r for r in records}
    for seed in SEEDS:
        point,full,compact=(stats[f'{name}_s{seed}'] for name in ('point','full','compact'))
        exact=reference['summary']['routes'][f'v088_exact_point16_s{seed}']
        point_ok=(point['shortlist_covers']>=36 and point['shortlist_covers']>=exact['shortlist_covers']-1
            and point['basis_certified']>=exact['basis_certified']-1)
        transfer_ok=(compact['shortlist_covers']>=36 and compact['shortlist_covers']>=full['shortlist_covers']-1
            and compact['basis_certified']>=full['basis_certified']-1)
        state_ok=all(by[(f'train{i}',f'compact_s{seed}')]['edge_multiply_terms']<=
            .125*by[(f'train{i}',f'full_s{seed}')]['edge_multiply_terms'] for i in range(48))
        tests.append({'seed':seed,'point_parity':point_ok,'transfer_parity':transfer_ok,
            'state_removal':state_ok,'passed':point_ok and transfer_ok and state_ok})
    return {'decision':'ADMIT_SEPARATELY_REGISTERED_COMPLETE_COST_SCREEN_NOT_Q3_Q4' if all(t['passed'] for t in tests)
        else 'STOP_FROZEN_INPUT_COMPACTION_NO_NEW_FIT','routes':stats,'tests':tests,
        'cost_claim':False,'global_q3':'OPEN','global_q4':'OPEN'}


def parents():
    original=prior.load_study('docs/experiments/results/v088_completed.manifest.json')
    reference=load_probe('docs/experiments/results/v093_first_probe.manifest.json')
    return original,reference


def run(checkpoint):
    import os,sys,scipy,highspy
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    env={'python':list(sys.version_info[:2]),'numpy':np.__version__,'scipy':scipy.__version__,
        'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if env!=protocol()['runtime'] or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':raise RuntimeError('runtime drift')
    original,reference=parents();models=prior.prior.restore_models(original['training'])
    report={'protocol':protocol(),'environment':env,'sources':reference['sources'],
        'weights_sha256':reference['weights_sha256']['v088'],'records':[],'stage':'loaded'}
    checkpoint(report)
    with threadpool_limits(1),torch.inference_mode():
        for source in original['train_sources']:
            raw=prior.prior.raw_source(source);tensors=tensor_input(*features(raw))
            proposals={}
            for seed in SEEDS:
                for name in ('point','full','compact'):
                    route=f'{name}_s{seed}'
                    out=propose(*tensors,models[f'point16_s{seed}'],
                        None if name=='point' else models[f'full16_s{seed}'],name=='compact')
                    proposals[route]=out
            label=set(source['label']['indices'])
            for route,out in proposals.items():
                candidate=prior.prior.previous.storage.candidate_once(raw,out['basis'],'input_probe')
                row={'case_id':source['id'],'route':route,**out,
                    'shortlist_covers':label.issubset(out['shortlist']),'candidate':candidate}
                report['records'].append(row)
            checkpoint({'stage':'case_completed','case_id':source['id'],'records':report['records'][-6:]})
            print(source['id'],len(report['records']),flush=True)
    report['summary']=summarize(report['records'],reference);report['stage']='completed';checkpoint(report)
    return report


def validate(report):
    original,reference=parents()
    if report['protocol']!=protocol() or report['environment']!=protocol()['runtime'] or report['stage']!='completed':raise ValueError('protocol drift')
    if report['sources']!=reference['sources'] or report['weights_sha256']!=reference['weights_sha256']['v088']:raise ValueError('identity drift')
    sources={s['id']:s for s in original['train_sources']}
    for row in report['records']:
        source=sources[row['case_id']];raw=prior.prior.raw_source(source);m,n=raw['A'].shape
        name=row['route'].split('_s')[0]
        for key,size in (('basis',m),('shortlist',2*m),('selected',n if name=='full' else 2*m)):
            ix=row[key]
            if len(ix)!=min(n,size) or len(set(ix))!=len(ix) or any(type(i) is not int or not 0<=i<n for i in ix):raise ValueError('indices drift')
        columns=0 if name=='point' else n if name=='full' else 2*m
        terms=0 if name=='point' else m*columns*16*6
        if row['state_columns']!=columns or row['edge_multiply_terms']!=terms:raise ValueError('state ledger drift')
        if not set(row['basis']).issubset(row['selected']) or not set(row['shortlist']).issubset(row['selected']):raise ValueError('selection drift')
        if row['shortlist_covers']!=set(source['label']['indices']).issubset(row['shortlist']):raise ValueError('offline coverage drift')
        c=row['candidate'];cert=c['certificate'];w=c['witness']
        if c['indices']!=row['basis']:raise ValueError('basis drift')
        if cert:
            if w is None or verify_standard_form_certificate(**raw,**w)['accepted']!=cert['accepted'] or c['accepted']!=cert['accepted']:raise ValueError('witness drift')
        elif c['accepted']:raise ValueError('missing certificate')
    if report['summary']!=summarize(report['records'],reference):raise ValueError('verdict drift')
