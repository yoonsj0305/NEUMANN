"""Development original-source witness check, retaining every unsupported call."""
from pathlib import Path
from collections import Counter
import hashlib,json,time
from neumann1.functional_source import parse,SourceError
from neumann1.functional_examples import Sampler,concrete_call


def main():
    work=Path(__file__).resolve().parents[3]
    intake=work/'Continuation/SUFU_SOURCE_FIRST'
    target=work/'Continuation/FUNCTIONAL_RUNTIME_PREFLIGHT_ENTRYPOINTS'
    target.mkdir()
    start=time.perf_counter();records=[]
    manifest=json.loads((intake/'manifest.json').read_text())
    for item in manifest['files']:
        if not item['path'].startswith('benchmark/') or not item['path'].endswith('.f') or item['path'].endswith('autolifter-base.f'):
            continue
        raw=(intake/'upstream'/item['local_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==item['sha256']
        commands=parse(raw.decode());sampler=Sampler(commands,int(item['sha256'][:16],16))
        rows=[]
        for index in range(8):
            try:
                row={'status':'ORIGINAL_CONCRETE_VALUE_ONLY',**concrete_call(commands,sampler,index%5)}
            except (SourceError,RecursionError) as error:
                row={'status':'NOT_EVALUATED','reason':type(error).__name__+': '+str(error)}
            rows.append({'index':index,**row})
        record={'path':item['path'],'source_sha256':item['sha256'],'rows':rows,
                'counts':dict(Counter(r['status'] for r in rows)),
                'optimized_source_compared':False,'universal_equivalence_proven':False,
                'capability_score':False,'fresh_eligible':False}
        folder=target/f'{len(records):03}';folder.mkdir()
        (folder/'record.json').write_text(json.dumps(record,indent=2)+'\n')
        records.append(record)
    report={'study':'FUNCTIONAL_ORIGINAL_SOURCE_DEVELOPMENT_PREFLIGHT',
            'sources':len(records),'calls':sum(len(r['rows']) for r in records),
            'counts':dict(Counter(row['status'] for r in records for row in r['rows'])),
            'seconds':time.perf_counter()-start,'G0_passed':False,'G1_admitted':False,
            'fresh_eligible':0,'records':records}
    (target/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
    print(json.dumps(dict(Counter(row['reason'] for r in records for row in r['rows'] if row['status']=='NOT_EVALUATED')),indent=2))


if __name__=='__main__':main()
