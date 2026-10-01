"""Untimed opened-training diagnosis. No optimizer, fitting or final inputs."""
import math
import numpy as np
import torch
from threadpoolctl import threadpool_limits
from experiments import lp_cheap_screen_v091 as prior
from experiments.lp_late_models_v092 import restore_models as restore_late
from experiments.lp_feature_probe_v093 import POLICIES,indices,approximate_features
from experiments.lp_state_models_v087 import tensor_input
from neumann1.lp_model_study_archive_v088 import load_study
from neumann1.lp_cheap_archive_v091 import load_screen as load_cheap
from neumann1.lp_late_archive_v092 import load_screen as load_late
from neumann1.lp_certificate_v081 import verify_standard_form_certificate

PREFIXES=('v088_exact_','v088_cg3_','v091_cheap_','v092_late_')
ROUTES=POLICIES+tuple(prefix+r for prefix in PREFIXES for r in prior.old.LEARNERS)


def protocol():
    return {'schema':'neumann.lp-selector-probe.v1','runtime':prior.protocol()['runtime'],
        'parents':{'v088':'9fa7e160a0264cb22475c98eae9ce8b43d8de4c31146ee1c2004476efe349661',
            'v091':'6a47bd6c37ef492f50bc41d77ae0b4eb853694f5d74170003c4e88140a128534',
            'v092':'c5ee2b178207d83e6772a5848c5ca149f16f06abe1b65a43603df2e3feeb4cff'},
        'sources':'all48 opened v088 train only','cases':48,'routes':list(ROUTES),
        'cg_steps':[3,5],'trim_keeps':'n,n/2,n/4,n/8, floor m+1',
        'new_fitting':False,'timing':False,'final_evaluation':False,'lp_optimizer':False,
        'near_saturation':46,'minimum_cg_point_shortlist':36,'maximum_parity_loss':1,
        'global_q3':'OPEN','global_q4':'OPEN'}


def summarize(records):
    expected={(f'train{i}',r) for i in range(48) for r in ROUTES}
    keys=[(r['case_id'],r['route']) for r in records]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:raise ValueError('probe coverage drift')
    result={route:{'basis_certified':sum(r['candidate']['accepted'] for r in records if r['route']==route),
        'basis_covers':sum(r['basis_covers'] for r in records if r['route']==route),
        'shortlist_covers':sum(r['shortlist_covers'] for r in records if r['route']==route),
        'coarse_covers':sum(bool(r['coarse_covers']) for r in records if r['route']==route)} for route in ROUTES}
    saturated=max(result[r]['basis_certified'] for r in POLICIES)>=46
    shortlist=max(result[r]['shortlist_covers'] for r in POLICIES)>=46
    parity=[]
    for seed in prior.old.SEEDS:
        exact=result[f'v088_exact_point16_s{seed}'];cg3=result[f'v088_cg3_point16_s{seed}']
        parity.append({'seed':seed,'passed':cg3['shortlist_covers']>=36 and
            cg3['shortlist_covers']>=exact['shortlist_covers']-1 and
            cg3['basis_certified']>=exact['basis_certified']-1})
    decision=('CHEAP_CERTIFICATE_NEAR_SATURATION_DIAGNOSTIC_ONLY' if saturated else
        'CHEAP_SHORTLIST_NEAR_SATURATION_DIAGNOSTIC_ONLY' if shortlist else
        'ADMIT_PREREGISTERED_CG3_POINT_COST_SCREEN_NOT_Q3_Q4' if all(p['passed'] for p in parity) else
        'SELECTOR_GAP_UNRESOLVED_NO_NEW_FIT')
    return {'decision':decision,'routes':result,'point_parity':parity,
        'cost_claim':False,'global_q3':'OPEN','global_q4':'OPEN'}


def run(checkpoint):
    import os,sys,scipy,highspy
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    env={'python':list(sys.version_info[:2]),'numpy':np.__version__,'scipy':scipy.__version__,
        'torch':torch.__version__,'highspy':highspy.Highs().version()}
    if env!=protocol()['runtime'] or os.environ.get('OPENBLAS_CORETYPE')!='HASWELL':raise RuntimeError('probe runtime drift')
    old=load_study('docs/experiments/results/v088_completed.manifest.json')
    cheap=load_cheap('docs/experiments/results/v091_first_screen.manifest.json')
    late=load_late('docs/experiments/results/v092_first_screen.manifest.json')
    sources=old['train_sources'];models={'v088':prior.restore_models(old['training']),
        'v091':prior.restore_models(cheap['training']),'v092':restore_late(late['training'])}
    report={'protocol':protocol(),'environment':env,'sources':[{'id':s['id'],'sha256':s['sha256'],
        'rows':s['rows'],'cols':s['cols']} for s in sources],
        'weights_sha256':{version:{k:v['weights_sha256'] for k,v in parent['training'].items()}
            for version,parent in (('v088',old),('v091',cheap),('v092',late))},
        'records':[],'feature_errors':[],'stage':'loaded_opened_train'}
    checkpoint(report)
    with threadpool_limits(1):
        for source in sources:
            raw=prior.raw_source(source);m,n=raw['A'].shape
            exact=prior.previous.admission.features(**raw);approx=approximate_features(raw);cheap_features=prior.features(**raw)
            report['feature_errors'].append({'case_id':source['id'],
                'residual_relative_l2':float(np.linalg.norm(approx[2][:,1]-exact[2][:,1])/max(1e-12,np.linalg.norm(exact[2][:,1]))),
                'primal_relative_l2':float(np.linalg.norm(approx[2][:,2]-exact[2][:,2])/max(1e-12,np.linalg.norm(exact[2][:,2])))})
            proposals={}
            for policy in POLICIES:
                try:
                    basis,short=indices(raw,policy);proposals[policy]=(basis,short,None,None)
                except (ValueError,np.linalg.LinAlgError) as error:proposals[policy]=([],[],None,f'{type(error).__name__}: {error}')
            with torch.inference_mode():
                for prefix,version,features in (('v088_exact_','v088',exact),('v088_cg3_','v088',approx),
                    ('v091_cheap_','v091',cheap_features),('v092_late_','v092',cheap_features)):
                    tensors=tensor_input(*features)
                    for key,model in models[version].items():
                        out=model(*tensors);score=out['scores'];coarse=out['coarse']
                        if torch.isfinite(score).all() and torch.isfinite(coarse).all():
                            order=torch.argsort(score,descending=True,stable=True).tolist()
                            chosen=torch.argsort(coarse,descending=True,stable=True)[:2*m].tolist()
                            proposals[prefix+key]=(order[:m],order[:2*m],chosen,None)
                        else:proposals[prefix+key]=([],[],[], 'nonfinite model proposal')
            # Labels are inspected only after ALL target-free proposals are fixed.
            label=set(source['label']['indices'])
            for route,(basis,short,coarse,error) in proposals.items():
                candidate=prior.previous.storage.candidate_once(raw,basis,'diagnostic_basis')
                record={'case_id':source['id'],'route':route,'basis':basis,'shortlist':short,'coarse':coarse,
                    'basis_covers':label.issubset(basis),'shortlist_covers':label.issubset(short),
                    'coarse_covers':label.issubset(coarse) if coarse is not None else None,
                    'proposal_error':error,'candidate':candidate}
                report['records'].append(record);checkpoint({'stage':'observation','record':record})
            print('case',source['id'],'records',len(report['records']),flush=True)
        report['summary']=summarize(report['records']);report['stage']='completed';checkpoint(report)
    return report


def validate(report):
    if report['protocol']!=protocol() or report['environment']!=protocol()['runtime'] or report['stage']!='completed':
        raise ValueError('probe protocol drift')
    old=load_study('docs/experiments/results/v088_completed.manifest.json')
    sources={s['id']:s for s in old['train_sources']}
    if report['sources']!=[{'id':s['id'],'sha256':s['sha256'],'rows':s['rows'],'cols':s['cols']} for s in old['train_sources']]:
        raise ValueError('probe source drift')
    for version,parent in (('v088',old),('v091',load_cheap('docs/experiments/results/v091_first_screen.manifest.json')),
        ('v092',load_late('docs/experiments/results/v092_first_screen.manifest.json'))):
        if report['weights_sha256'][version]!={k:v['weights_sha256'] for k,v in parent['training'].items()}:
            raise ValueError('probe checkpoint identity drift')
    errors=report['feature_errors']
    if len(errors)!=48 or {e['case_id'] for e in errors}!=set(sources) or any(
        not math.isfinite(e[k]) or e[k]<0 for e in errors for k in ('residual_relative_l2','primal_relative_l2')):
        raise ValueError('probe feature-error drift')
    raws={case:prior.raw_source(s) for case,s in sources.items()}
    for row in report['records']:
        source=sources[row['case_id']];raw=raws[row['case_id']];m,n=raw['A'].shape
        label=set(source['label']['indices'])
        for key,size in (('basis',m),('shortlist',2*m),('coarse',2*m)):
            ix=row[key]
            if ix is None:
                if key!='coarse' or row['route'] not in POLICIES:raise ValueError('invalid absent coarse')
                continue
            if (len(ix)!=len(set(ix)) or any(type(i) is not int or not 0<=i<n for i in ix)
                or (not row['proposal_error'] and len(ix)!=min(n,size))):raise ValueError('probe indices drift')
        if (row['basis_covers']!=label.issubset(row['basis']) or row['shortlist_covers']!=label.issubset(row['shortlist'])
            or row['coarse_covers']!=(label.issubset(row['coarse']) if row['coarse'] is not None else None)):
            raise ValueError('probe offline coverage drift')
        candidate=row['candidate'];w=candidate['witness'];cert=candidate['certificate']
        if candidate['indices']!=row['basis']:raise ValueError('candidate basis drift')
        if cert:
            if w is None or verify_standard_form_certificate(**raw,**w)['accepted']!=cert['accepted']:
                raise ValueError('probe witness drift')
            if candidate['accepted']!=cert['accepted']:raise ValueError('probe acceptance drift')
        elif candidate['accepted']:raise ValueError('missing diagnostic certificate')
    if report['summary']!=summarize(report['records']):raise ValueError('probe summary drift')
