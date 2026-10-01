"""First paid screen, conditional on the retained architecture probe."""
import math,random
from time import perf_counter_ns
from statistics import median,geometric_mean
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from experiments import lp_input_probe_v094 as probe
from experiments import lp_cheap_screen_v091 as old
from experiments.lp_state_models_v087 import tensor_input
from neumann1.lp_shortlist_v089 import solve_shortlist_checked
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

NEW=tuple(f'cg5_{name}_s{s}' for s in probe.SEEDS for name in ('point','full','fullsolo','compact'))
ROUTES=old.CLASSICS+old.old.LEARNERS+NEW+('cg5_residual',)


def protocol():
    return {'schema':'neumann.lp-input-cost.v1','runtime':probe.protocol()['runtime'],
        'source_sha256':probe.protocol()['source_parent_sha256'],'cases':16,'routes':list(ROUTES),
        'warmups':1,'repeats':3,'order_seed':94991,'budget_s':5.,'ratio_max':.8,
        'minimum_wins':12,'minimum_no_rescue':12,'amortization_queries':10000,
        'new_fitting':False,'final_evaluation':False,'global_q3':'OPEN','global_q4':'OPEN'}


def observe(raw,route,models):
    start=perf_counter_ns();D,rows,cols=probe.features(raw);m,n=D.shape
    if route=='cg5_residual':
        order=np.argsort(cols[:,1],kind='stable');basis=order[:m].tolist();short=order[:2*m].tolist();out=None
    else:
        name,seed=route.removeprefix('cg5_').split('_s');point=models[f'point16_s{seed}'];full=models[f'full16_s{seed}']
        with torch.inference_mode():
            tensors=tensor_input(D,rows,cols)
            if name=='fullsolo':
                out=full(*tensors);order=torch.argsort(out['scores'],descending=True,stable=True)
                out={**out,'basis':order[:m].tolist(),'shortlist':order[:2*m].tolist()}
            else:out=probe.propose(*tensors,point,None if name=='point' else full,name=='compact')
        basis,short=out['basis'],out['shortlist']
    proposal_ms=(perf_counter_ns()-start)/1e6
    candidate=probe.prior.prior.previous.storage.candidate_once(raw,basis,'paid_input_basis')
    execution=None;w=candidate['witness'] if candidate['accepted'] else None
    remaining=5.-(perf_counter_ns()-start)/1e9
    if not candidate['accepted'] and remaining>0:
        execution=solve_shortlist_checked(**raw,indices=short,budget_s=remaining);w=execution['witness']
    elapsed=(perf_counter_ns()-start)/1e6
    return {'accepted':bool((candidate['accepted'] or (execution and execution['accepted'])) and elapsed<=5000),
        'total_ms':elapsed,'proposal_ms':proposal_ms,'basis':basis,'indices':short,'candidate':candidate,
        'execution':execution,'witness':w,'state_columns':out['state_columns'] if out else 0,
        'edge_multiply_terms':out['edge_multiply_terms'] if out else 0}


def summarize(records,sources,investment_ms):
    ids=[s['id'] for s in sources];keys=[(r['case_id'],r['route'],r['repeat']) for r in records]
    if len(ids)!=16 or len(set(keys))!=len(keys) or set(keys)!={(case,route,i) for case in ids for route in ROUTES for i in (-1,0,1,2)}:raise ValueError('cost coverage drift')
    if any(type(r['accepted']) is not bool or not math.isfinite(r['total_ms']) or r['total_ms']<=0 for r in records):raise ValueError('invalid costs')
    if not all(r['accepted'] for r in records):return {'decision':'CAPABILITY_UNREACHED','global_q3':'OPEN','global_q4':'OPEN'}
    c={(case,route):median(r['total_ms'] for r in records if r['case_id']==case and r['route']==route and r['repeat']>=0) for case in ids for route in ROUTES}
    direct=[r for r in old.old.LEARNERS if not r.startswith('compact')]+[r for r in NEW if 'compact' not in r]
    tests=[]
    for seed in probe.SEEDS:
        route=f'cg5_compact_s{seed}';ratios=[[],[],[],[],[]];rescue=0
        for case in ids:
            value=c[case,route];classic=min(c[case,r] for r in old.CLASSICS+('cg5_residual',))
            denominators=[classic,min(c[case,r] for r in direct),c[case,f'cg5_full_s{seed}'],c[case,f'cg5_point_s{seed}']]
            for a,d in zip(ratios[:4],denominators):a.append(value/d)
            ratios[4].append((value+investment_ms/10000)/classic)
            rescue+=int(all(r['candidate']['accepted'] or (r['execution'] and r['execution']['subset_accepted']) for r in records if r['case_id']==case and r['route']==route))
        geos=[geometric_mean(a) for a in ratios];wins=[sum(x<=.8 for x in a) for a in ratios[:4]]
        tests.append({'seed':seed,'ratios':geos,'wins':wins,'no_full_rescue_cases':rescue,
            'passed':max(geos)<=.8 and min(wins)>=12 and rescue>=12})
    return {'decision':'ADMIT_SEPARATELY_REGISTERED_HOLDOUT_NOT_Q3_Q4' if all(t['passed'] for t in tests) else 'STOP_FROZEN_INPUT_COMPACTION_COST_CANDIDATE',
        'ratio_order':['classical','best_learned_direct','own_full_with_selector','point_only','amortized_classical'],
        'tests':tests,'global_q3':'OPEN','global_q4':'OPEN'}


def run(checkpoint):
    import os,sys,scipy,highspy,gzip,json
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    env={'python':list(sys.version_info[:2]),'numpy':np.__version__,'scipy':scipy.__version__,'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if env!=protocol()['runtime'] or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':raise RuntimeError('runtime drift')
    p=json.load(gzip.open('docs/experiments/results/v094_first_probe.json.gz'));probe.validate(p)
    if not all(t['passed'] for t in p['summary']['tests']):raise ValueError('probe did not admit cost screen')
    loading=perf_counter_ns();parent,_=probe.parents();models=old.restore_models(parent['training']);load_ms=(perf_counter_ns()-loading)/1e6
    # Conservatively charge the full original eight-model fit, setup and restoration.
    investment=parent['training_setup_ms']+sum(t['fit_ms'] for t in parent['training'].values())+load_ms
    report={'protocol':protocol(),'environment':env,'sources':parent['train_sources'][:16],
        'weights_sha256':p['weights_sha256'],'investment_ms':investment,'loading_ms':load_ms,'records':[],'stage':'loaded'}
    checkpoint(report);raws={s['id']:old.raw_source(s) for s in report['sources']}
    with threadpool_limits(1):
        for repeat in (-1,0,1,2):
            order=[(case,route) for case in raws for route in ROUTES];random.Random(94991+repeat).shuffle(order)
            for case,route in order:
                raw=raws[case]
                if route.startswith('cg5_'):row=observe(raw,route,models)
                elif route in old.old.LEARNERS:row=old.previous.observe(raw,route,models[route])
                elif route in old.CHEAP_CLASSICS:row=old.observe(raw,route)
                elif route=='scale_portfolio':row=old.previous.storage.discovery_once(**raw)
                elif route in old.old.CLASSICS:row=old.previous.admission.observe(raw,route,None,{})
                else:row=old.previous.observe(raw,route)
                record={'case_id':case,'route':route,'repeat':repeat,**row};report['records'].append(record)
                checkpoint({'stage':'observation','record':record})
            print('repeat',repeat,len(report['records']),flush=True)
    report['summary']=summarize(report['records'],report['sources'],investment);report['stage']='completed';checkpoint(report)
    return report


def validate(report):
    parent,reference=probe.parents()
    if report['protocol']!=protocol() or report['environment']!=protocol()['runtime'] or report['stage']!='completed':raise ValueError('protocol drift')
    if report['sources']!=parent['train_sources'][:16] or report['weights_sha256']!=reference['weights_sha256']['v088']:raise ValueError('source/checkpoint drift')
    if not math.isfinite(report['loading_ms']) or report['loading_ms']<0 or report['investment_ms']!=parent['training_setup_ms']+sum(t['fit_ms'] for t in parent['training'].values())+report['loading_ms']:raise ValueError('investment drift')
    raws={s['id']:old.raw_source(s) for s in report['sources']}
    for r in report['records']:
        raw=raws[r['case_id']]
        if r['accepted'] and (r['total_ms']>5000 or r['witness'] is None or not verify_standard_form_certificate(**raw,**r['witness'])['accepted']):raise ValueError('original witness drift')
        if r['route'].startswith('cg5_'):
            m,n=raw['A'].shape;name=r['route'].removeprefix('cg5_').split('_s')[0]
            for ix,size in ((r['basis'],m),(r['indices'],2*m)):
                if len(ix)!=size or len(set(ix))!=size or any(type(i) is not int or not 0<=i<n for i in ix):raise ValueError('proposal drift')
            columns=0 if name in ('point','residual') else 2*m if name=='compact' else n
            terms=0 if columns==0 else m*columns*16*6
            if r['state_columns']!=columns or r['edge_multiply_terms']!=terms:raise ValueError('state ledger drift')
            c=r['candidate'];cert=c['certificate']
            if c['indices']!=r['basis']:raise ValueError('basis drift')
            if cert and (c['witness'] is None or verify_standard_form_certificate(**raw,**c['witness'])['accepted']!=cert['accepted'] or c['accepted']!=cert['accepted']):raise ValueError('rejected basis drift')
        e=r.get('execution')
        if e and r['total_ms']+1e-6<r['proposal_ms']+e['total_ms']:raise ValueError('paid ledger drift')
        if e and 'subset_accepted' in e:
            if e['indices']!=r['indices']:raise ValueError('executor indices drift')
            for native,small in ((e['restricted'],True),(e['fallback'],False)):
                if not native:continue
                ix=e['indices'];target={'A':raw['A'][:,ix],'b':raw['b'],'c':raw['c'][ix]} if small else raw
                for a in native['attempts']:
                    if a['certificate'] and (a['witness'] is None or verify_standard_form_certificate(**target,**a['witness'])['accepted']!=a['certificate']['accepted']):raise ValueError('native witness drift')
            if e['original_certificate']:
                w=e['restricted']['attempts'][-1]['witness'];x=np.zeros(raw['A'].shape[1]);x[e['indices']]=w['x']
                accepted=verify_standard_form_certificate(**raw,x=x,y=w['y'])['accepted']
                if accepted!=e['subset_accepted'] or accepted!=e['original_certificate']['accepted']:raise ValueError('omitted-column drift')
    if report['summary']!=summarize(report['records'],report['sources'],report['investment_ms']):raise ValueError('summary drift')
