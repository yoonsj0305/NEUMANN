"""Frozen v0.0.94 replay: does graph refinement add information over point-only?"""
from neumann1.lp_input_archive_v094 import load_archive
from experiments import lp_input_probe_v094 as prior

SEEDS=(87001,87002)
PROBE_MANIFEST='docs/experiments/results/v094_first_probe.manifest.json'


def protocol():
    return {
        'schema':'neumann.lp-graph-incremental-v095.v1',
        'source':'v094_first_probe',
        'cases':48,
        'seeds':list(SEEDS),
        'minimum_certificate_gain':4,
        'minimum_mean_recall_gain':0.05,
        'minimum_hit_wins':12,
        'maximum_hit_losses':6,
        'require_identical_retained_sets':48,
        'new_fitting':False,
        'new_inference':False,
        'new_solver_calls':False,
        'timing':False,
        'final_evaluation':False,
        'global_q3':'OPEN',
        'global_q4':'OPEN',
    }


def summarize(probe, sources):
    records={(r['case_id'],r['route']):r for r in probe['records']}
    labels={s['id']:set(s['label']['indices']) for s in sources}
    if len(labels)!=48:
        raise ValueError('source coverage drift')
    tests=[]
    for seed in SEEDS:
        point_cert=compact_cert=0
        point_recall=[]
        compact_recall=[]
        wins=losses=ties=0
        identical=0
        rows=[]
        for case_id,label in labels.items():
            point=records[(case_id,f'point_s{seed}')]
            compact=records[(case_id,f'compact_s{seed}')]
            if set(point['selected'])==set(compact['selected'])==set(point['shortlist'])==set(compact['shortlist']):
                identical+=1
            m=len(label)
            if m<=0:
                raise ValueError('empty label')
            ph=len(label.intersection(point['basis']))
            ch=len(label.intersection(compact['basis']))
            pr=ph/m
            cr=ch/m
            point_recall.append(pr)
            compact_recall.append(cr)
            point_cert+=int(point['candidate']['accepted'])
            compact_cert+=int(compact['candidate']['accepted'])
            if ch>ph:wins+=1
            elif ch<ph:losses+=1
            else:ties+=1
            rows.append({'case_id':case_id,'point_hits':ph,'compact_hits':ch,'delta_hits':ch-ph,
                         'point_certificate':bool(point['candidate']['accepted']),
                         'compact_certificate':bool(compact['candidate']['accepted'])})
        mean_point=sum(point_recall)/len(point_recall)
        mean_compact=sum(compact_recall)/len(compact_recall)
        cert_gain=compact_cert-point_cert
        recall_gain=mean_compact-mean_point
        passed=(cert_gain>=protocol()['minimum_certificate_gain']
            and recall_gain>=protocol()['minimum_mean_recall_gain']
            and wins>=protocol()['minimum_hit_wins']
            and losses<=protocol()['maximum_hit_losses']
            and identical==protocol()['require_identical_retained_sets'])
        tests.append({
            'seed':seed,
            'point_certificates':point_cert,
            'compact_certificates':compact_cert,
            'certificate_gain':cert_gain,
            'point_mean_label_recall':mean_point,
            'compact_mean_label_recall':mean_compact,
            'mean_label_recall_gain':recall_gain,
            'hit_wins':wins,
            'hit_losses':losses,
            'hit_ties':ties,
            'identical_retained_sets':identical,
            'passed':passed,
            'rows':rows,
        })
    return {
        'protocol':protocol(),
        'decision':('ADMIT_CLEAN_GRAPH_REFINEMENT_COST_PROTOCOL_NOT_Q3_Q4'
                    if all(t['passed'] for t in tests)
                    else 'STOP_GRAPH_REFINEMENT_INFORMATION_CANDIDATE'),
        'tests':tests,
        'cost_claim':False,
        'generalization_claim':False,
        'global_q3':'OPEN',
        'global_q4':'OPEN',
    }


def analyze():
    probe=load_archive(PROBE_MANIFEST)
    prior.validate(probe)
    original,_=prior.parents()
    return summarize(probe,original['train_sources'])
