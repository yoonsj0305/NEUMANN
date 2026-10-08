"""Inspect retained historical records only; no inference, optimization or timing."""
import gzip, json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
def load(p):
    b=(root/p).read_bytes()
    return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
for p in ['docs/experiments/results/q5_first_evaluation/report.json',
          'docs/experiments/results/m106_bp_transfer_first/report.json']:
    o=load(p)
    print(p, 'ROOT',list(o), 'SUMMARY',list(o['summary']))
    for k in ['case_costs','cells','decisions','decision']:
        v=o['summary'].get(k)
        print(k, json.dumps(v[:2] if isinstance(v,list) else v)[:7000])
    if 'records' in o:
        from collections import Counter
        print('ROUTES',Counter(r['route'] for r in o['records']))
        r=next(r for r in o['records'] if r['route'].startswith('EXPAND'))
        print('RECORD KEYS',list(r),'EXEC',list(r['execution']))
        print('ATTEMPT',json.dumps(r['execution']['attempts'][0])[:2500])
        print('FINAL WITNESS', str(r.get('witness'))[:80],str(r['execution'].get('witness'))[:80])
for p in ['docs/experiments/results/q5_first_sources/manifest.json',
          'docs/experiments/results/m106_bp_transfer_first/sources.json',
          'docs/experiments/results/m106_bp_transfer_first/m106_bp_k8_r0.json.gz']:
    o=load(p); print(p, 'ROOT',list(o)); print(json.dumps(o)[:900])
