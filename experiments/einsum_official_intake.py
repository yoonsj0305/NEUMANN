"""Read-only primary-source metadata intake. Never unpickle benchmark data."""
from pathlib import Path
import csv,hashlib,io,json,time,urllib.request


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'NEUMANN-research-metadata/1.0'}),timeout=45) as response:
        return response.read()


def main():
    work=Path(__file__).resolve().parents[3]
    target=work/'Continuation/EINSUM_OFFICIAL_METADATA_FIRST';target.mkdir()
    logs=[]
    def fetch(name,url):
        start=time.perf_counter()
        try:
            raw=get(url);(target/name).write_bytes(raw)
            logs.append({'url':url,'file':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'seconds':time.perf_counter()-start,'status':'FETCHED'})
            return raw
        except Exception as error:
            logs.append({'url':url,'status':'FAILED','seconds':time.perf_counter()-start,'reason':str(error)})
            return None
        finally:(target/'requests.json').write_text(json.dumps(logs,indent=2)+'\n')
    head=fetch('commit.json','https://api.github.com/repos/ti2-group/einsum_benchmark/commits/main')
    assert head is not None
    commit=json.loads(head)['sha'];prefix=f'https://raw.githubusercontent.com/ti2-group/einsum_benchmark/{commit}/'
    metadata=fetch('metadata.csv',prefix+'metadata.csv')
    fetch('LICENSE',prefix+'LICENSE');fetch('instances.py',prefix+'src/einsum_benchmark/instances.py');fetch('util.py',prefix+'src/einsum_benchmark/util.py')
    doi=fetch('zenodo-record.json','https://zenodo.org/api/records/11477304')
    rows=list(csv.DictReader(io.StringIO(metadata.decode())))
    summary={'repository':'https://github.com/ti2-group/einsum_benchmark','commit':commit,'metadata_rows':len(rows),
             'metadata_total_uncompressed_file_mb':sum(float(r['file_size_in_mb']) for r in rows),
             'dataset_files':[] if doi is None else [{'key':f['key'],'size':f['size'],'checksum':f['checksum'],'links':f['links']} for f in json.loads(doi)['files']],
             'actual_tensor_instances_downloaded':False,'pickle_executed':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False}
    (target/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
