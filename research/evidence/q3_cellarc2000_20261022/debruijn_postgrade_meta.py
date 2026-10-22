"""Postscore ONLY hidden generator metadata classifier, never imported by source solver."""
import argparse,collections,hashlib,json,pathlib,urllib.request

def download(url):
    req=urllib.request.Request(url,headers={'User-Agent':'NEUMANN-postgrade-source-audit/1.0'})
    with urllib.request.urlopen(req,timeout=120) as x:return x.read()
def main():
    p=argparse.ArgumentParser();p.add_argument('--pregrade',required=True)
    p.add_argument('--original-dir',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();pre=pathlib.Path(a.pregrade);d=json.loads(pre.read_text())
    assert d['n']==2000 and not d['hidden_metadata_seen']
    repo='mireklzicar/cellarc_100k_meta'
    revision=json.loads(download('https://huggingface.co/api/datasets/'+repo))['sha']
    results={};total=collections.Counter()
    for split in ('test_interpolation','test_extrapolation'):
        true={v['id']:v for v in map(json.loads,(pathlib.Path(a.original_dir)/(split+'.jsonl')).read_text().splitlines())}
        raw=download(f'https://huggingface.co/datasets/{repo}/resolve/{revision}/data/{split}.jsonl')
        metadata=[json.loads(x) for x in raw.decode().splitlines()]
        assert len(metadata)==1000 and set(z['id'] for z in metadata)==set(true)
        ct=collections.Counter()
        for z in metadata:
            i=z['id']
            for key in ('train','query','solution'):assert z[key]==true[i][key]
            m=z['meta'];out=d['models'][split][i]
            actualcycle=(m['construction']=='cycle')
            unique=out['status'] in ('SOURCE_INDUCED_CYCLE_PREDICTION','NO_UNIQUE_PREDICTION')
            ct['all']+=1;ct['true_cycle']+=int(actualcycle);ct['claimed_cycle_structure']+=int(unique)
            ct['true_positive_cycle']+=int(unique and actualcycle)
            ct['false_positive_cycle']+=int(unique and not actualcycle)
            ct['false_negative_cycle']+=int(actualcycle and not unique)
            if unique:
                guess=out['structural_model']
                ct['true_W_identified']+=int(int(guess['W'])==int(m['window']))
                ct['true_k_identified']+=int(int(guess['k'])==int(m['alphabet_size']))
                ct['true_effective_radius_identified']+=int(int(guess['effective_radius'])==int(m['radius'])*int(m['steps']))
                ct['true_construction_cycle']+=int(actualcycle)
            if out.get('prediction') is not None and out['prediction']!=z['solution']:
                print('POSTGRADE_WRONG_ID_NOT_INFERENCE',json.dumps({'split':split,'id':i,
                    'actual_construction':m['construction'],'true_k':m['alphabet_size'],
                    'true_W':m['window'],'true_r':m['radius'],'true_steps':m['steps'],
                    'inferred_parameters':out.get('structural_model'),
                    'model_families':out.get('compatible_model_families')},sort_keys=True),flush=True)
            group=m['construction']+'/'+str(m['window'])
            ct['group:'+group]+=1
        results[split]={'counts':dict(ct),'original_sha256':hashlib.sha256(raw).hexdigest()}
        total.update(ct)
        print('POSTGRADE_GENERATOR_IDENTITY',split,json.dumps(dict(ct),sort_keys=True),flush=True)
    r={'schema':'NEUMANN_CELLARC_SOURCE_GENERATOR_POSTGRADE_META_AUDIT.v1',
       'n':2000,'meta_revision':revision,'pregrade_sha256':hashlib.sha256(pre.read_bytes()).hexdigest(),
       'meta_never_passed_to_inference':True,'splits':results,'total':dict(total)}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,sort_keys=True)+'\n')
    print('POSTGRADE_GENERATOR_META_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
