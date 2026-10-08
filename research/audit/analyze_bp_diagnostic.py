"""Optimizer-free causal accounting of the first opened BP diagnostic."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT.parents[1] / 'Continuation/BP_CERTIFICATE_DIAGNOSTIC_2026-10-08'
OUT = ROOT / 'research/audit'


def analyze():
    sys.path.insert(0, str(FOLDER / 'deps'))
    import highspy
    from threadpoolctl import threadpool_limits
    from experiments import bp_certificate_diagnostic as d
    from experiments.q5_register import evidence_module
    ev = evidence_module(); d.science()
    with patch('scipy.optimize.linprog', side_effect=AssertionError('no solve analysis')), \
         patch('highspy.Highs.run', side_effect=AssertionError('no native analysis')), \
         patch('spgl1.spg_bp', side_effect=AssertionError('no discovery analysis')):
        replay = d.replay(FOLDER / 'first')
    events, terminal = ev.read_events(FOLDER / 'first')
    records = [ev.unpack_case(FOLDER / 'first', e['payload']['identity']) for e in events if e['kind'] == 'observation']
    report = json.loads((FOLDER / 'first/report.json').read_bytes())
    per_route = {}
    with threadpool_limits(1):
        for r in records:
            raw = d.decode(ev.unpack_case(d.SOURCE, r['source_identity']))
            ex = r['execution']
            if ex and ex['accepted'] and not d.checker(**raw, **ex['witness'])['accepted']:
                raise ValueError('false primary path authorization')
            if r['route'] == 'D_ORACLE_SPARSE' and ex['free_dual_used']:
                raise ValueError('Oracle dual leaked into D')
    for route in d.ROUTES:
        rows = [r for r in records if r['route'] == route]
        timed = [r for r in rows if r['repeat'] >= 0]
        fallback = lambda r: bool(r['fallback']) or bool(r['execution'] and r['execution'].get('fallback_used'))
        row = {'requests': len(rows), 'independent_originals': len({r['case_id'] for r in rows}),
               'final_verified': sum(r['accepted'] for r in rows),
               'fallback_requests': sum(fallback(r) for r in rows),
               'fallback_originals': sorted({r['case_id'] for r in rows if fallback(r)}),
               'timed_query_ms_median': statistics.median(r['query_ms'] for r in timed),
               'timed_decode_ms_median': statistics.median(r['decode_ms'] for r in timed),
               'candidate_errors': dict(Counter(r['candidate_error'] for r in rows if r['candidate_error']))}
        if route.startswith(('D_', 'E_')):
            row['first_dual_accepted_requests'] = sum(r['execution']['attempts'][0]['certificate']['accepted'] for r in rows)
            row['first_dual_accepted_originals'] = sorted({r['case_id'] for r in rows if r['execution']['attempts'][0]['certificate']['accepted']})
            row['dual_method_counts'] = dict(Counter(a['method'] for r in rows for a in r['execution']['attempts']))
            row['stage_medians_ms_not_additive'] = {stage: statistics.median(sum(a['ms'] for a in r['execution']['stages'] if a['stage'] == stage) for r in timed)
                for stage in sorted({a['stage'] for r in rows for a in r['execution']['stages']})}
        per_route[route] = row
    cells = []
    for c in report['summary']['cells']:
        best = min((v['amortized_operational_q10000_ms'], r) for r, v in c['costs'].items() if r.startswith('A_') and v['all_verified'])
        row = {'case_id': c['case_id'], 'level': int(c['case_id'].split('_k')[1].split('_')[0]),
               'strongest_declared_native': best[1], 'native_q10000_ms': best[0]}
        for r in d.ROUTES[4:]:
            row[r + '_q10000_ms'] = c['costs'][r]['amortized_operational_q10000_ms']
            row[r + '_speedup'] = c['strong_native_over_candidate'][r]
        cells.append(row)
    summary = {'kind': 'OPENED_POSTHOC_CAUSAL_ANALYSIS_NOT_FIRST_VERDICT_REPLACEMENT',
               'original_report_sha256': hashlib.sha256((FOLDER / 'first/report.json').read_bytes()).hexdigest(),
               'contract_sha256': report['contract_sha256'], 'replay': replay,
               'independent_originals': 16, 'observations': len(records),
               'per_route': per_route, 'first_screening': report['summary']['screening'],
               'strongest_native_counts': dict(Counter(c['strongest_declared_native'] for c in cells)),
               'new_model_forwards': 0, 'new_solver_calls_in_analysis': 0,
               'decision': 'HOLD_LEARNING',
               'causal_boundary': 'Certificate acquisition is expensive for this minimum-norm/HiGHS feasibility adapter; not an intrinsic impossibility of cheap certification. Oracle E is not a learned engine.',
               'cost_boundary': 'Windows matched operational Q10000, includes source read/decode/check/response plus common diagnostic startup and dependency setup. Full investment/energy/FLOPs/peak memory UNKNOWN.'}
    with (OUT / 'BP_CERTIFICATE_DIAGNOSTIC_ANALYSIS.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(cells[0])); w.writeheader(); w.writerows(cells)
    (OUT / 'BP_CERTIFICATE_DIAGNOSTIC_ANALYSIS.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    result = analyze()
    print(json.dumps({'replay': result['replay'], 'screening': result['first_screening'],
                      'decision': result['decision']}, indent=2))
