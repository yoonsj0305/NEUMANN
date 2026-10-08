"""Derive causal diagnostics from opened first evidence. Never solve or infer.

All new numerical checks use the existing optimizer-free original LP verifier.
Missing one retained optimum's support does not exclude alternate optima.
Break-even assumes stationary same-case requests and the historical cost scope.
"""
from __future__ import annotations
import base64, csv, gzip, hashlib, json, math, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from experiments.q5_register import evidence_module
from experiments.q5_first_archive import source_pin, result_pin

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p):
    p=Path(p); b=p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def decode(a):
    return np.frombuffer(base64.b64decode(a['data']),dtype=a['dtype']).reshape(a['shape']).copy()
def verify_source(p,identity):
    b=p.read_bytes(); raw=gzip.decompress(b)
    assert sha(b)==identity['gzip_sha256'] and sha(raw)==identity['json_sha256'],str(p)
    return json.loads(raw)
def break_even(i_direct,i_candidate,op_direct,op_candidate):
    saving=op_direct-op_candidate
    if saving<=0: return None
    return max(1,math.floor((i_candidate-i_direct)/saving)+1)
def dump(p,value):
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def write_csv(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader();w.writerows(rows)

def m106():
    folder=ROOT/'docs/experiments/results/m106_bp_transfer_first'
    report=read(folder/'report.json'); manifest=read(folder/'sources.json')
    assert sha((folder/'report.json').read_bytes())=='fd0f069bb43c8f4f471578de35a6f70af2c418b46b701260f12cd1d27bebd6b8'
    ev=evidence_module(); chain,terminal=ev.read_events(folder)
    assert terminal['report_sha256']==ev.digest(ev.canonical(report))
    assert report['sources_sha256']==ev.digest(ev.canonical(manifest))
    archived_records=[row['payload'] for row in chain if row['kind']=='observation']
    assert archived_records==report['records']
    sources={}
    for row in manifest['cases']:
        source=verify_source(folder/row['identity']['file'],row['identity'])
        sources[source['metadata']['id']]={k:decode(v) for k,v in source['arrays'].items()}
    records=report['records']; native={}
    for r in records:
        if r['route']=='NATIVE' and r['phase']=='timed' and r['repeat']==0: native[r['case_id']]=r['witness']
    checks=Counter(); events=Counter(); failures=Counter(); rows=[]; factor_counts=defaultdict(Counter)
    for r in records:
        a=sources[r['case_id']]
        if r.get('witness'):
            cert=verify_standard_form_certificate(a['A'],a['b'],a['c'],**r['witness'])
            checks['final_checked']+=1; checks['final_accepted']+=int(cert['accepted'])
            assert cert['accepted']==r['accepted']
        if not r['route'].startswith('EXPAND'): continue
        ex=r['execution']
        for k in ['expanded','expanded_accepted','subset_accepted','fallback_used']:
            events[k]+=int(ex[k])
        n=len(a['c']); m=len(a['b'])
        nx=np.array(native[r['case_id']]['x'])
        support=set(np.flatnonzero(np.abs(nx)>1e-8).tolist())
        nobj=float(a['c']@nx)
        for attempt in ex['attempts']:
            ar=attempt['result']; indices=ar['indices']; witness=ar.get('witness')
            if witness is None:
                failures['no_restricted_witness']+=1;continue
            cert=verify_standard_form_certificate(a['A'],a['b'],a['c'],**witness)
            assert cert['accepted']==bool(ar['original_certificate']['accepted'])
            checks['restricted_original_checked']+=1;checks['restricted_original_accepted']+=int(cert['accepted'])
            gap=abs(cert['primal_objective']-nobj)
            # Comparison is a posthoc diagnostic; original numerical certificate is authority.
            equal=gap<=1e-8+1e-8*max(1,abs(nobj),abs(cert['primal_objective']))
            failed=[k for k in ['equality','nonnegative','dual_feasibility','objective_gap'] if cert[k+'_ratio']>1]
            failures['+'.join(failed) if failed else 'accepted']+=1
            checks['objective_matches_native']+=int(equal)
            checks['objective_matches_native_but_original_rejected']+=int(equal and not cert['accepted'])
            if r['phase']=='timed' and r['repeat']==0:
                fc=factor_counts[str(attempt.get('support_factor'))]
                fc['attempts']+=1;fc['original_accepted']+=int(cert['accepted'])
                fc['native_primal_objective_equal']+=int(equal)
                fc['optimal_primal_but_dual_rejected']+=int(equal and not cert['accepted'])
                fc['retained_optimum_support_covered']+=int(support<=set(indices))
                if equal and not cert['accepted']:
                    cross=verify_standard_form_certificate(a['A'],a['b'],a['c'],witness['x'],native[r['case_id']]['y'])
                    checks['offline_existing_native_dual_pair_checks']+=1
                    checks['offline_existing_native_dual_pair_accepted']+=int(cross['accepted'])
                rows.append({'case_id':r['case_id'],'route':r['route'],'rows':m,'columns':n,
                             'optimal_nonzero_support_size':len(support),'selected_size':len(indices),
                             'support_factor':attempt.get('support_factor'),
                             'retained_native_optimum_support_covered':support<=set(indices),
                             'support_overlap':len(support&set(indices)),
                             'restricted_native_accepted':ar['native']['accepted'],
                             'original_accepted':cert['accepted'],
                             'primal_objective_matches_native':equal,'primal_objective_gap':gap,
                             'original_dual_violation_ratio':cert['dual_feasibility_ratio'],
                             'original_objective_gap_ratio':cert['objective_gap_ratio'],
                             'rejected_axes':'+'.join(failed),
                             'attempt_ms_historical':ar['total_ms'],
                             'fallback_used':ex['fallback_used'],
                             'proposal_ms_historical':r['proposal_ms'],
                             'total_ms_historical':r['total_ms']})
    write_csv(ROOT/'research/audit/M106_RETAINED_DIAGNOSTICS.csv',rows)
    first_optimal_rejected=[r for r in rows if r['primal_objective_matches_native'] and not r['original_accepted']]
    summary={'source_hash':sha((folder/'report.json').read_bytes()),
             'independent_problems':len(sources),'observations':len(records),
             'checks':dict(checks),'candidate_events_all_repeats':dict(events),
             'rejection_axes_all_repeats':dict(failures),
             'first_timed_repeat_factor_counts':dict(factor_counts),
             'independent_candidate_problem_paths':len({(x['case_id'],x['route']) for x in rows}),
             'first_timed_optimal_primal_rejected_attempts':len(first_optimal_rejected),
             'first_timed_optimal_primal_rejected_paths':len({(x['case_id'],x['route']) for x in first_optimal_rejected}),
             'first_timed_optimal_primal_rejected_originals':len({x['case_id'] for x in first_optimal_rejected}),
             'native_optimal_support_sizes':{k:int(np.count_nonzero(np.abs(v['x'])>1e-8)) for k,v in native.items()},
             'native_support_not_unique_authority':True,
             'new_solver_calls':0,'new_model_forwards':0,'new_data_generated':0,
             'original_decisions':report['summary']['decisions']}
    dump(ROOT/'research/audit/M106_RETAINED_DIAGNOSTICS.json',summary)
    return summary

def q5():
    folder=ROOT/'docs/experiments/results/q5_first_evaluation'
    sources=source_pin(ROOT/'docs/experiments/results/q5_first_sources')
    report,chain=result_pin(folder)
    meta={r['metadata']['id']:r['metadata'] for r in sources['cases']}
    costs={(r['case_id'],r['route']):r for r in report['summary']['case_costs']}
    expansion=defaultdict(Counter); observed_totals=defaultdict(list)
    ev=evidence_module()
    for entry in chain:
        if entry['kind']!='observation':continue
        r=ev.unpack_case(folder,entry['payload']['identity'])
        if r['repeat']<0: continue
        e=r['execution']; key=(r['case_id'],r['route'])
        observed_totals[key].append(r['total_ms'])
        for k in ['expanded','expanded_accepted','subset_accepted','fallback_used']:
            expansion[key][k]+=int(e.get(k,False))
    rows=[]
    for (case_id,route),c in sorted(costs.items()):
        if not route.startswith('EXPAND'): continue
        d=costs[case_id,'DIRECT']; md=meta[case_id]
        # Historical q5_evidence.py: cold_q1 = startup + setup + median(total_ms).
        # post_ms excludes proposal, and therefore cannot be used for investment subtraction.
        cp=statistics.median(observed_totals[case_id,route])
        dp=statistics.median(observed_totals[case_id,'DIRECT'])
        ci=c['cold_q1_ms']-cp; di=d['cold_q1_ms']-dp
        comparable=c['capable'] and d['capable'] and c['accounted'] and d['accounted']
        rows.append({'case_id':case_id,'pair_id':md['pair_id'],'seed':md['seed'],
                     'm':md['rows'],'width_factor':md['width_factor'],'conditioning':md['condition'],
                     'surface':md['surface'],'route':route,'direct_capable':d['capable'],
                     'candidate_capable':c['capable'],'direct_observed_operational_ms':dp,
                     'candidate_observed_operational_ms':cp,
                     'direct_cold_plus_investment_ms':di,'candidate_cold_plus_investment_ms':ci,
                     'direct_registered_complete_ms':d['complete_ms'],
                     'candidate_registered_complete_ms':c['complete_ms'],
                     'S_registered_ms':d['complete_ms']-c['complete_ms'] if comparable else None,
                     'registered_candidate_direct_ratio':c['complete_ms']/d['complete_ms'] if comparable else None,
                     'S_stationary_operational_ms':dp-cp if comparable else None,
                     'N_break_even_same_case':break_even(di,ci,dp,cp) if comparable else None,
                     'status':'COMPARABLE' if comparable else 'CAPABILITY_OR_ACCOUNTING_UNREACHED',
                     'expanded_timed_observations':expansion[case_id,route]['expanded'],
                     'expanded_accepted_timed_observations':expansion[case_id,route]['expanded_accepted'],
                     'fallback_timed_observations':expansion[case_id,route]['fallback_used']})
    write_csv(ROOT/'research/audit/LP_SUCCESS_ENVELOPE.csv',rows)
    summary={'report_sha256':sha((folder/'report.json').read_bytes()),
             'source_manifest_sha256':sha((ROOT/'docs/experiments/results/q5_first_sources/manifest.json').read_bytes()),
             'independent_problems':len({r['pair_id'] for r in meta.values()}),'equivalent_views':len(meta),
             'observations':report['summary']['observations'],
             'derived_candidate_view_rows':len(rows),'comparable_rows':sum(r['status']=='COMPARABLE' for r in rows),
             'registered_cost_advantage_rows':sum(r['S_registered_ms'] is not None and r['S_registered_ms']>0 for r in rows),
             'finite_stationary_break_even_rows':sum(r['N_break_even_same_case'] is not None for r in rows),
             'original_decision':report['summary']['decision'],'original_cells':report['summary']['cells'],
             'break_even_scope':'Same historical process/runtime and identical stationary workload; excludes unmeasured investment. No new performance execution.',
             'new_solver_calls':0,'new_model_forwards':0}
    dump(ROOT/'research/audit/LP_SUCCESS_ENVELOPE.json',summary)
    return {k:v for k,v in summary.items() if k!='original_cells'}

if __name__=='__main__':
    print(json.dumps({'m106':m106(),'q5':q5()},ensure_ascii=False,indent=2))
