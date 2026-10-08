"""Opened v102 shortlist attribution from retained rankings and witnesses.

No fitting, model restoration, new forward, optimizer or timing. A cheap
deterministic residual control is computed only for support coverage; no new
solver utility or cost is inferred from that coverage.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from threadpoolctl import threadpool_limits
from neumann1 import lp_portfolio_v084 as storage
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from research.audit.analyze_retained_lp import decode, write_csv
from research.audit.analyze_feature_transfer import original_feature_function
from research.audit.analyze_certificate_geometry import geometry

PINS = {
    'v102_fresh_sources': ('9420b10a44ca3101374a79d638cc209f1301d2b867cec8de3ebecb0f270c4202',
                          '00dcdcb4b3ebaed4607685951a61b36d5fb5f3fc046720b39c2c8babcef4c0a5'),
    'v102_first_evaluation': ('a73c21e149852013b7db19c0380ddaa36d5c2d6582051008a22942e7309cf47a',
                             'd748f70433360ed76ed226f0608a34418af19e0aa9ec3d6aabe9233751995195')}


def load_opened(name):
    if name not in PINS:
        raise ValueError('Only explicitly opened v102 archives permitted')
    path = ROOT / 'docs/experiments/results' / (name + '.json.gz')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PINS[name][0]:
        raise ValueError('Original compressed archive drift')
    raw = gzip.decompress(data)
    if len(raw) > 128 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != PINS[name][1]:
        raise ValueError('Original decoded archive drift')
    return json.loads(raw)


def coverage(ranking, support, m):
    positions = {j:i+1 for i,j in enumerate(ranking)}
    if len(positions) != len(ranking) or any(j not in positions for j in support):
        raise ValueError('Invalid retained ranking')
    return {'missing_top2m': len(set(support) - set(ranking[:2*m])),
            'missing_top4m': len(set(support) - set(ranking[:4*m])),
            'worst_positive_support_rank': max(positions[j] for j in support)}


def analyze():
    sources = load_opened('v102_fresh_sources')['sources']
    report = load_opened('v102_first_evaluation')
    if report['summary']['decision'] != 'Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5':
        raise ValueError('First frozen verdict drift')
    first = {(r['case_id'],r['route']):r for r in report['records'] if r['repeat']==0}
    feature, feature_hash = original_feature_function()
    rows = []; ranks = []; witness_checks = 0
    with threadpool_limits(1), \
         patch('scipy.optimize.linprog', side_effect=AssertionError('No new optimizer')), \
         patch('scipy.optimize.milp', side_effect=AssertionError('No new optimizer')):
        for source in sources:
            raw = {k:decode(v) for k,v in source['arrays'].items()}
            if storage.input_digest(raw) != source['sha256']:
                raise ValueError('Original source array drift')
            case_id, m = source['id'], source['rows']
            g = geometry('v102_opened_historical_confirmation', case_id, raw,
                         source['label']['witness'], source['sha256'])
            ranks.append(g)
            support = source['label']['indices']
            if set(support) != set(np.flatnonzero(np.abs(source['label']['witness']['x'])>1e-8)):
                raise ValueError('Retained positive basis label mismatch')
            # First four quotient channels equal original CG5 channels. The
            # v097 A_DETERMINISTIC uses ascending stable channel1, without labels.
            _, columns = feature(raw)
            cheap = np.argsort(columns[:,1], kind='stable').tolist()
            for route in ('DIRECT','ORACLE','EXPAND4_s100001','EXPAND4_s100002'):
                retained = first[case_id,route]
                if not verify_standard_form_certificate(**raw,**retained['witness'])['accepted']:
                    raise ValueError('Original first-timed witness rejected')
                witness_checks += 1
            for route, ranking in [('CHEAP_RESIDUAL_COVERAGE_ONLY',cheap)] + [
                    (route,first[case_id,route]['ranking']) for route in ('EXPAND4_s100001','EXPAND4_s100002')]:
                row = {'case_id':case_id,'pair_id':source['pair_id'],'group':source['group'],
                       'rows':m,'columns':raw['A'].shape[1],'surface':source['surface'],
                       'route':route,**coverage(ranking,support,m)}
                if route.startswith('EXPAND4'):
                    retained = first[case_id,route]
                    if retained['top2'] != ranking[:2*m]:
                        raise ValueError('Original shortlist/ranking drift')
                    row.update(expanded=retained['expanded'],
                               subset_accepted=retained['subset_accepted'],
                               original_accepted=retained['accepted'],
                               fallback_used=retained['fallback_used'])
                else:
                    row.update(expanded=None,subset_accepted=None,original_accepted=None,fallback_used=None)
                rows.append(row)
    groups = {}
    for route in sorted({r['route'] for r in rows}):
        rr = [r for r in rows if r['route']==route]
        groups[route] = {'views':len(rr),'top2m_covers_entire_positive_basis':sum(r['missing_top2m']==0 for r in rr),
                         'top4m_covers_entire_positive_basis':sum(r['missing_top4m']==0 for r in rr),
                         'max_missing_top2m':max(r['missing_top2m'] for r in rr),
                         'max_worst_positive_support_rank_over_m':max(r['worst_positive_support_rank']/r['rows'] for r in rr),
                         'new_final_capability_or_cost':None}
        if route.startswith('EXPAND4'):
            groups[route]['expansion_matches_missing_top2m'] = all(r['expanded']==(r['missing_top2m']>0) for r in rr)
    out = ROOT / 'research/audit'
    write_csv(out/'Q34_SHORTLIST_ATTRIBUTION.csv', rows)
    write_csv(out/'Q34_CERTIFICATE_GEOMETRY.csv', ranks)
    result = {'kind':'OPENED_POSTHOC_Q34_COMPONENT_ANALYSIS','originals':len({s['pair_id'] for s in sources}),
              'equivalent_views':len(sources),'first_timed_original_witnesses_rechecked':witness_checks,
              'groups':groups,'all_v102_support_dual_nullities':sorted({r['active_equality_dual_nullity'] for r in ranks}),
              'learned_missing_top2m_original_ids':{route:sorted({r['pair_id'] for r in rows if r['route']==route and r['missing_top2m']>0})
                                                   for route in ('EXPAND4_s100001','EXPAND4_s100002')},
              'source_archive_pins':PINS,'feature_source_sha256':feature_hash,
              'new_model_forwards':0,'new_solver_calls':0,'new_problems':0,'new_performance_measurements':0,
              'cheap_control_scope':'Existing v097 residual rule, recomputed on already opened v102 arrays only. Coverage is not a timed solver/capability ablation; no new PASS/FAIL or threshold selection.',
              'verdict_unchanged':report['summary']['decision'],'decision':'HOLD_LEARNING'}
    (out/'Q34_SHORTLIST_ATTRIBUTION.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(analyze(),indent=2))
