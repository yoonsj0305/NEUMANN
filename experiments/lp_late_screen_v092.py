"""First bounded late-pruning screen, with prior strong learned controls."""
import math,random
from statistics import median,geometric_mean
from time import perf_counter_ns
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from experiments import lp_cheap_screen_v091 as prior
from experiments.lp_late_models_v092 import roster,restore_models
from experiments.lp_shortlist_screen_v089 import raw_source
from experiments.lp_state_models_v087 import tensor_input
from neumann1.lp_cheap_archive_v091 import load_screen

OLD_LEARNERS=tuple('v091_'+r for r in prior.old.LEARNERS)
ROUTES=prior.ROUTES+OLD_LEARNERS


def protocol():
    return {'schema':'neumann.lp-late-pruning-screen.v1','runtime':prior.protocol()['runtime'],
        'prior_json_sha256':'6a47bd6c37ef492f50bc41d77ae0b4eb853694f5d74170003c4e88140a128534',
        'train_split':'all48 opened v088 train retained in v091','screen_split':'same train first16',
        'graph_change':'coarse head and compact2m selection after update1, not update0',
        'models':list(prior.old.NAMES),'seeds':list(prior.old.SEEDS),'epochs':12,
        'optimizer':'Adam','lr':.001,'loss':prior.old.protocol()['loss'],
        'fit_seconds_cap':240.,'checkpoint':'last epoch only','parameter_cap':400000,
        'features':'unchanged v091 cheap observables; no least squares',
        'executor':prior.protocol()['executor'],'routes':list(ROUTES),
        'cases':16,'warmups':1,'repeats':3,'order_seed':92991,'budget_s':5.,
        'ratio_max':.8,'minimum_wins':12,'minimum_no_full_rescue':12,
        'amortization_queries':10000,'training_ledger':'new fit-phase wall incl all8 fits/checkpoint I/O',
        'final_evaluation':False,'global_q3':'OPEN','global_q4':'OPEN'}


def summarize(records,sources,training_phase_ms):
    ids=[s['id'] for s in sources];keys=[(r['case_id'],r['route'],r['repeat']) for r in records]
    if (len(ids)!=16 or len(set(ids))!=16 or len(keys)!=len(set(keys)) or
        set(keys)!={(case,route,i) for case in ids for route in ROUTES for i in (-1,0,1,2)}):
        raise ValueError('late coverage drift')
    if not math.isfinite(training_phase_ms) or training_phase_ms<=0:raise ValueError('training wall drift')
    if any(type(r['accepted']) is not bool or not math.isfinite(r['total_ms']) or r['total_ms']<=0 for r in records):
        raise ValueError('late cost drift')
    if not all(r['accepted'] for r in records):
        return {'decision':'CAPABILITY_UNREACHED','global_q3':'OPEN','global_q4':'OPEN'}
    costs={(case,route):median(r['total_ms'] for r in records if r['case_id']==case and r['route']==route
        and r['repeat']>=0) for case in ids for route in ROUTES}
    direct=[r for r in prior.old.LEARNERS+OLD_LEARNERS if 'compact16' not in r]
    tests=[]
    for seed in prior.old.SEEDS:
        compact=f'compact16_s{seed}';full=f'full16_s{seed}'
        values=[[],[],[],[]];no_rescue=0
        for case in ids:
            c=costs[case,compact];classic=min(costs[case,r] for r in prior.CLASSICS)
            for v,x in zip(values,(c/classic,c/min(costs[case,r] for r in direct),
                c/costs[case,full],(c+training_phase_ms/10000.)/classic)):v.append(x)
            no_rescue+=int(all((r.get('execution') or {}).get('subset_accepted',False)
                for r in records if r['case_id']==case and r['route']==compact))
        ratios=[geometric_mean(v) for v in values];wins=[sum(x<=.8 for x in v) for v in values[:3]]
        tests.append({'seed':seed,'classical_ratio':ratios[0],'direct_ratio':ratios[1],
            'own_full_ratio':ratios[2],'amortized_classical_ratio':ratios[3],
            'wins':wins,'no_full_rescue_cases':no_rescue,
            'passed':max(ratios)<=.8 and min(wins)>=12 and no_rescue>=12})
    return {'decision':'ADMIT_NEW_HOLDOUT_NOT_Q3_Q4' if all(t['passed'] for t in tests)
        else 'STOP_LATE_PRUNING_CANDIDATE','tests':tests,'global_q3':'OPEN','global_q4':'OPEN'}


def run(checkpoint):
    import os,sys,scipy,highspy
    torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True)
    env={'python':list(sys.version_info[:2]),'numpy':np.__version__,'scipy':scipy.__version__,
        'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if env!=protocol()['runtime'] or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':
        raise RuntimeError('late runtime drift')
    phase=perf_counter_ns()
    original=load_screen('docs/experiments/results/v091_first_screen.manifest.json')
    report={'protocol':protocol(),'environment':env,'train_sources':original['train_sources'],
        'sources':original['sources'],'training':{},'records':[],'stage':'opened_train'}
    with threadpool_limits(1):
        data=[]
        for source in report['train_sources']:
            raw=raw_source(source);x,y=prior.old.scaled_targets(raw,source['label'])
            data.append((tensor_input(*prior.features(**raw)),torch.tensor(source['label']['indices']),
                torch.tensor(x,dtype=torch.float32),torch.tensor(y,dtype=torch.float32)))
        report['training_setup_ms']=(perf_counter_ns()-phase)/1e6
        for seed in prior.old.SEEDS:
            for name,model in roster(seed).items():
                key=f'{name}_s{seed}';report['training'][key]=prior.old.fit_one(model,data,seed,name)
                report['stage']='fit_'+key;checkpoint(report)
                print(report['stage'],report['training'][key]['fit_ms'],flush=True)
                if not report['training'][key]['completed']:raise RuntimeError('late first fit failed; no retry')
        report['training_phase_ms']=(perf_counter_ns()-phase)/1e6
        models=restore_models(report['training']);old_models=prior.restore_models(original['training'])
        raws={s['id']:raw_source(s) for s in report['sources']}
        report['stage']='weights_frozen';checkpoint(report)
        for repeat in (-1,0,1,2):
            order=[(case,route) for case in raws for route in ROUTES];random.Random(92991+repeat).shuffle(order)
            for case,route in order:
                raw=raws[case]
                if route.startswith('v091_'):row=prior.observe(raw,route[5:],old_models[route[5:]])
                elif route in prior.old.LEARNERS or route in prior.CHEAP_CLASSICS:row=prior.observe(raw,route,models.get(route))
                elif route=='scale_portfolio':row=prior.previous.storage.discovery_once(**raw)
                elif route in prior.old.CLASSICS:row=prior.previous.admission.observe(raw,route,None,{})
                else:row=prior.previous.observe(raw,route)
                record={'case_id':case,'route':route,'repeat':repeat,**row};report['records'].append(record)
                checkpoint({'stage':'observation','record':record})
            print('repeat',repeat,'records',len(report['records']),flush=True)
        report['summary']=summarize(report['records'],report['sources'],report['training_phase_ms'])
        report['stage']='completed';checkpoint(report)
    return report


def validate(report):
    if report['protocol']!=protocol() or report['environment']!=protocol()['runtime'] or report['stage']!='completed':
        raise ValueError('late protocol drift')
    original=load_screen('docs/experiments/results/v091_first_screen.manifest.json')
    if report['train_sources']!=original['train_sources'] or report['sources']!=original['sources']:
        raise ValueError('late source drift')
    models=restore_models(report['training'])
    for key,model in models.items():
        t=report['training'][key]
        if (not t['completed'] or key!=f"{t['name']}_s{t['seed']}" or not 0<t['fit_ms']<=240000.
            or t['parameters']!=sum(p.numel() for p in model.parameters()) or t['parameters']>400000
            or [e['epoch'] for e in t['epochs']]!=list(range(1,13))
            or any(not math.isfinite(e['mean_loss']) for e in t['epochs'])):raise ValueError('late fit drift')
    if (not math.isfinite(report['training_setup_ms']) or report['training_setup_ms']<=0 or
        report['training_phase_ms']<report['training_setup_ms']+sum(t['fit_ms'] for t in report['training'].values())):
        raise ValueError('fit-phase ledger drift')
    # Reuse portable certificate/ledger replay with a schema adapter only.
    # v091 expects its own source/training and edge metadata; only validation
    # metadata is adapted in a separate view, never first bytes or measured costs.
    rows=[]
    for row in report['records']:
        r=dict(row)
        if r['route'].startswith('v091_'):continue
        if r['route'] in prior.old.LEARNERS:
            source=next(s for s in report['sources'] if s['id']==r['case_id']);m,n=source['rows'],source['cols']
            width=128 if r['route'].startswith('full128') else 16
            expected=0 if r['route'].startswith('point16') else m*n*width*4+m*r['state_columns']*width*2
            if r['edge_multiply_terms']!=expected:raise ValueError('late edge ledger drift')
            r['edge_multiply_terms']=0 if r['route'].startswith('point16') else m*n*width*2+m*r['state_columns']*width*4
        rows.append(r)
    view={'protocol':prior.protocol(),'environment':report['environment'],'stage':'completed',
        'train_sources':report['train_sources'],'sources':report['sources'],'training':report['training'],
        'training_setup_ms':report['training_setup_ms'],'records':rows}
    view['summary']=prior.summarize(rows,view['sources'],view['training'],view['training_setup_ms'])
    prior.validate(view)
    old_rows=[dict(row,route=row['route'][5:]) for row in report['records'] if row['route'].startswith('v091_')]
    # Native/classical rows reused here are byte-identical observations, not runs.
    old_rows += [row for row in report['records'] if row['route'] in prior.CLASSICS]
    view.update(training=original['training'],training_setup_ms=original['training_setup_ms'],records=old_rows)
    view['summary']=prior.summarize(old_rows,view['sources'],view['training'],view['training_setup_ms'])
    prior.validate(view)
    if report['summary']!=summarize(report['records'],report['sources'],report['training_phase_ms']):
        raise ValueError('late summary drift')
