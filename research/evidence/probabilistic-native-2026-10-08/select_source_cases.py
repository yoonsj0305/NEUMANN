"""Cost-blind source selection from the frozen public catalogue."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import sys
from urllib.request import Request, urlopen
sys.set_int_max_str_digits(100_000)
root=Path(__file__).resolve().parent
catalog=json.loads((root/'public-catalog-first.json').read_text())
bins=[('small',100,5000),('large',5001,100000)]
allowed=['prob-reach','exp-reward','exp-steps']
cases=[]
exclusions=[]
for row in catalog['rows']:
    m=row['metadata']; eligible=[]
    for file in m['files']:
        for params in file.get('open-parameter-values',[]):
            counts=[s['number'] for s in params.get('states',[]) if isinstance(s.get('number'),int)]
            if not counts: continue
            size=min(counts)
            for goal in params.get('results',[]):
                value=goal.get('value'); kind=next((p['type'] for p in m['properties'] if p['name']==goal['property']),None)
                if isinstance(value,int): exact=Fraction(value)
                elif isinstance(value,dict) and {'num','den'}<=value.keys(): exact=Fraction(value['num'],value['den'])
                else: continue
                if kind not in allowed or kind=='prob-reach' and exact in [0,1]: continue
                eligible.append({'family':row['family'],'file':file['file'],'goal':goal['property'],'goal_type':kind,
                                 'expected_exact':str(exact),'parameters':params.get('values',[]),
                                 'file_parameters':file.get('file-parameter-values',[]),'metadata_states':size,
                                 'metadata_source_sha256':row['sha256'],'source_commit':row['commit']})
    for name,lo,hi in bins:
        options=[x for x in eligible if lo<=x['metadata_states']<=hi]
        if not options:
            exclusions.append({'family':row['family'],'bin':name,'reason':'No public exact nontrivial supported goal in predeclared size range'})
            continue
        options.sort(key=lambda x:(x['metadata_states'],allowed.index(x['goal_type']),x['file'],x['goal'],json.dumps(x['parameters'],sort_keys=True)))
        chosen=dict(options[0]); chosen['complexity_bin']=name
        chosen['problem_lineage_id']=chosen['family']+'/'+chosen['file']+'/'+json.dumps(chosen['parameters'],sort_keys=True)
        chosen['case_id']=f"{chosen['family']}-{name}-{chosen['goal']}"
        rel=f"benchmarks/dtmc/{chosen['family']}/{chosen['file']}"
        chosen['source_url']=f"https://raw.githubusercontent.com/ahartmanns/qcomp/{row['commit']}/{rel}"
        target=root/'inputs'/chosen['family']/chosen['file']; target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            data=target.read_bytes()
            try:
                json.loads(data)
            except json.JSONDecodeError:
                # Preserve the initial bounded/truncated source retrieval attempt.
                assert target.resolve().is_relative_to(root.resolve())
                target.rename(target.with_suffix(target.suffix+'.partial-read-attempt-1'))
                data=None
        else: data=None
        if data is None:
            with urlopen(Request(chosen['source_url'],headers={'User-Agent':'NEUMANN-local-evidence-audit'}),timeout=20) as response: data=response.read(8_000_001)
            assert len(data)<=8_000_000, 'Source exceeds predeclared retrieval cap; do not treat partial bytes as a model'
            with target.open('xb') as out: out.write(data)
        parsed=json.loads(data)
        chosen['file_sha256']=hashlib.sha256(data).hexdigest(); chosen['file_bytes']=len(data)
        chosen['goal_expression']=next(p['expression'] for p in parsed['properties'] if p['name']==chosen['goal'])
        cases.append(chosen)
result={'scope':'Source selection only, before native scientific measurements',
        'selection_rule':'All 10 registered DTMC families; minimum metadata state count per fixed size bin, nontrivial exact reachability then expected reward/steps; deterministic tie breaks',
        'size_bins':bins,'cases':cases,'exclusions':exclusions}
with (root/'source-cases-first.json').open('x') as out: json.dump(result,out,indent=2)
for c in cases: print(json.dumps({k:v for k,v in c.items() if k in ['case_id','metadata_states','parameters','goal_type','goal_expression','file_bytes']}))
print('SELECTED',len(cases),'EXCLUDED_BINS',len(exclusions))
