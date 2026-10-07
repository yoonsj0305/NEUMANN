"""Opened parser intake only; no synthesized-program performance evaluation."""
from pathlib import Path
from collections import Counter
import hashlib,json,time
from neumann1.functional_source import parse,SourceError


def main():
    work=Path(__file__).resolve().parents[3]
    intake=work/'Continuation/SUFU_SOURCE_FIRST'
    records=[];start=time.perf_counter()
    manifest=json.loads((intake/'manifest.json').read_text())
    for item in manifest['files']:
        if not item['path'].startswith('benchmark/') or not item['path'].endswith('.f'):
            continue
        data=(intake/'upstream'/item['local_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==item['sha256']
        try:
            commands=parse(data.decode())
            result={'status':'PARSED_NOT_EXECUTED','commands':len(commands),
                    'inputs':[c[1] for c in commands if c[0]=='input']}
        except SourceError as error:
            result={'status':'UNSUPPORTED','error':str(error)}
        records.append({'path':item['path'],'sha256':item['sha256'],**result})
    target=work/'Continuation/FUNCTIONAL_SOURCE_PREFLIGHT'
    target.mkdir()
    report={'counts':dict(Counter(r['status'] for r in records)),'records':records,
            'seconds':time.perf_counter()-start,'capability_evidence':False,
            'fresh_eligible':0,'G0_passed':False,'G1_admitted':False}
    (target/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
    print(json.dumps([r for r in records if r['status']=='UNSUPPORTED'],indent=2))


if __name__=='__main__':main()
