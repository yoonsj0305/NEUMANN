"""Stream the immutable DOI archive; read bytes only, never load pickle."""
from pathlib import Path
import hashlib,json,time,urllib.request


def main():
    work=Path(__file__).resolve().parents[3]
    intake=work/'Continuation/EINSUM_OFFICIAL_METADATA_FIRST'
    metadata=json.loads((intake/'summary.json').read_text())
    artifact=next(f for f in metadata['dataset_files'] if f['key']=='instances.zip')
    assert artifact['size']==551789940 and artifact['checksum']=='md5:b476f37d39a5b8a978e8230375326eb3'
    target=work/'Continuation/EINSUM_OFFICIAL_ARCHIVE_FIRST';target.mkdir()
    url=artifact['links']['self'];assert url=='https://zenodo.org/api/records/11477304/files/instances.zip/content'
    (target/'request.json').write_text(json.dumps({'url':url,'expected_bytes':artifact['size'],'expected_md5':artifact['checksum'],
            'license_metadata':json.loads((intake/'zenodo-record.json').read_text())['metadata'].get('license'),
            'pickle_execution_allowed':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False},indent=2)+'\n')
    start=time.perf_counter();md5=hashlib.md5();digest=hashlib.sha256();total=0
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'NEUMANN-readonly-archive/1.0'}),timeout=45) as response,(target/'instances.zip').open('xb') as output:
        while True:
            chunk=response.read(1024*1024)
            if not chunk:break
            output.write(chunk);md5.update(chunk);digest.update(chunk);total+=len(chunk)
            if total%(16*1024*1024)==0:
                progress={'bytes':total,'expected_bytes':artifact['size'],'seconds':time.perf_counter()-start}
                with (target/'progress.jsonl').open('a') as log:log.write(json.dumps(progress)+'\n')
                print(json.dumps(progress),flush=True)
    assert total==artifact['size'] and md5.hexdigest()==artifact['checksum'][4:]
    receipt={'status':'ORIGINAL_ARCHIVE_BYTES_VERIFIED_NOT_EXECUTED','bytes':total,'md5':md5.hexdigest(),
             'sha256':digest.hexdigest(),'seconds':time.perf_counter()-start,'pickle_executed':False,
             'fresh_eligible':0,'G0_passed':False,'G1_admitted':False}
    (target/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
