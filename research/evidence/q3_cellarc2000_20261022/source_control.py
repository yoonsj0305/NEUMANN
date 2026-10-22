#!/usr/bin/env python3
"""Freeze independent CellARC source revision and physically redact original query labels."""
import argparse,hashlib,json,pathlib,urllib.request

BASE='https://huggingface.co'
ID='mireklzicar/cellarc_100k'
SPLITS=('test_interpolation','test_extrapolation')
def download(url):
    req=urllib.request.Request(url,headers={'User-Agent':'NEUMANN-Independent-Scientific-Gate/1.0'})
    with urllib.request.urlopen(req,timeout=120) as obj:return obj.read()

def main():
    a=argparse.ArgumentParser();a.add_argument('--mode',choices=('mask','restore'),required=True)
    a.add_argument('--dir',required=True);a.add_argument('--manifest',required=True);x=a.parse_args()
    out=pathlib.Path(x.dir);out.mkdir(parents=True,exist_ok=True)
    mf=pathlib.Path(x.manifest)
    if x.mode=='mask':
        data=json.loads(download(BASE+'/api/datasets/'+ID))
        sha=data['sha']
        assert len(sha)==40 and all(c in '0123456789abcdef' for c in sha)
        d={'repo':ID,'sha':sha,'splits':{}}
        for split in SPLITS:
            raw=download(BASE+'/datasets/'+ID+'/resolve/'+sha+'/data/'+split+'.jsonl')
            lines=raw.decode().splitlines()
            assert len(lines)==1000,(split,len(lines))
            p=out/(split+'.jsonl')
            with p.open('w') as o:
                for line in lines:
                    rec=json.loads(line)
                    assert all(k in rec for k in ('id','train','query','solution')) and len(rec['train'])==5
                    no_answers={'id':rec['id'],'train':rec['train'],'query':rec['query']}
                    assert 'solution' not in no_answers and 'meta' not in no_answers
                    o.write(json.dumps(no_answers,sort_keys=True,separators=(',',':'))+'\n')
            d['splits'][split]={'raw_sha256':hashlib.sha256(raw).hexdigest(),
                                'masked_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                                'n':len(lines)}
        mf.parent.mkdir(parents=True,exist_ok=True)
        mf.write_text(json.dumps(d,sort_keys=True)+'\n')
        print('CELLARC_FIRST_REAL_EXTERNAL_REVISION',sha,flush=True)
        print('CELLARC_2000_ALL_SOURCE_TARGETS_PHYSICALLY_ABSENT',flush=True)
    else:
        d=json.loads(mf.read_text());assert d['repo']==ID and len(d['sha'])==40
        for split in SPLITS:
            raw=download(BASE+'/datasets/'+ID+'/resolve/'+d['sha']+'/data/'+split+'.jsonl')
            assert hashlib.sha256(raw).hexdigest()==d['splits'][split]['raw_sha256']
            p=out/(split+'.jsonl');p.write_bytes(raw)
        print('CELLARC_INDEPENDENT_RESTORED_ORIGINAL_SHA_IDENTICAL',d['sha'],flush=True)
if __name__=='__main__':main()
