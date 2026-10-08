from pathlib import Path
from collections import Counter
import hashlib,json,time
from neumann1.functional_source import parse,SourceError
from neumann1.functional_types import check


def main():
    work=Path(__file__).resolve().parents[3];intake=work/'Continuation/SUFU_SOURCE_FIRST'
    manifest=json.loads((intake/'manifest.json').read_text());records=[];start=time.perf_counter()
    for item in manifest['files']:
        if not item['path'].startswith('benchmark/') or not item['path'].endswith('.f'):continue
        raw=(intake/'upstream'/item['local_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==item['sha256']
        try:
            types=check(parse(raw.decode()));result={'status':'ERASED_TYPE_CHECKED','term_bindings':len(types)}
        except SourceError as error:result={'status':'NOT_TYPE_CHECKED','reason':str(error)}
        records.append({'path':item['path'],'source_sha256':item['sha256'],**result})
    report={'counts':dict(Counter(r['status'] for r in records)),'records':records,
            'seconds':time.perf_counter()-start,'universal_equivalence_proven':False,
            'termination_proven':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False}
    target=work/'Continuation/FUNCTIONAL_TYPE_PREFLIGHT';target.mkdir()
    (target/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
    print(json.dumps([r for r in records if r['status']!='ERASED_TYPE_CHECKED'],indent=2))


if __name__=='__main__':main()
