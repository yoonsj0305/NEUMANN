"""POSTGRADE ONLY CellARC validation source inferred structure vs original hidden metadata."""
import argparse,collections,hashlib,json,pathlib,urllib.request
def read(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'NEUMANN-independent-val1000-postgrade'}),timeout=120) as r:return r.read()
def main():
    p=argparse.ArgumentParser();p.add_argument('--sealed',required=True);p.add_argument('--original',required=True);p.add_argument('--out',required=True)
    a=p.parse_args()
    frozen=pathlib.Path(a.sealed);state=json.loads(frozen.read_text())
    assert state['n']==1000 and not state['hidden_meta_accessed']
    actual={q['id']:q for q in map(json.loads,pathlib.Path(a.original).read_text().splitlines())}
    assert len(actual)==1000
    repo='mireklzicar/cellarc_100k_meta'
    revision=json.loads(read(f'https://huggingface.co/api/datasets/{repo}'))['sha']
    raw=read(f'https://huggingface.co/datasets/{repo}/resolve/{revision}/data/val.jsonl')
    meta=[json.loads(q) for q in raw.decode().splitlines()]
    assert len(meta)==1000 and {q['id'] for q in meta}==set(actual)
    counts=collections.Counter()
    problems=[]
    for z in meta:
        uid=z['id'];truth=actual[uid];pred=state['rows'][uid];m=z['meta']
        for key in ('train','query','solution'):assert z[key]==truth[key]
        expected=m['construction']=='cycle'
        has_struct=pred['status'] in ('SOURCE_INDUCED_CYCLE_PREDICTION','NO_UNIQUE_PREDICTION')
        attempted=pred['prediction'] is not None
        correct=attempted and pred['prediction']==truth['solution']
        counts['total']+=1
        counts['true_cycle']+=int(expected)
        counts['predicted_cycle']+=int(has_struct)
        counts['true_positive_cycle']+=int(expected and has_struct)
        counts['false_positive_cycle']+=int(has_struct and not expected)
        counts['false_negative_cycle']+=int(expected and not has_struct)
        counts['attempted']+=int(attempted)
        counts['correct']+=int(correct)
        counts['wrong']+=int(attempted and not correct)
        if has_struct:
            info=pred['structural_model']
            counts['true_W_identified']+=int(info['W']==m['window'])
            counts['true_k_identified']+=int(info['k']==m['alphabet_size'])
            counts['true_effective_radius_identified']+=int(info['effective_radius']==m['radius']*m['steps'])
        if has_struct and not expected or attempted and not correct:
            problems.append({'id':uid,'false_cycle':has_struct and not expected,
                'wrong_pred':attempted and not correct,'construction':m['construction'],
                'true_W':m['window'],'true_k':m['alphabet_size'],
                'true_steps':m['steps'],'inferred':pred.get('structural_model')})
    d={'schema':'NEUMANN_FIRST_VAL1000_TRUE_META_AFTER_GRADE_ONLY.v1','n':1000,
       'source_sha':hashlib.sha256(frozen.read_bytes()).hexdigest(),
       'original_meta_revision':revision,'original_meta_file_sha256':hashlib.sha256(raw).hexdigest(),
       'metadata_not_exposed_to_inference':True,'counts':dict(counts),'counterexample_records':problems}
    print('FIRST_VAL1000_TRUE_STRUCTURE_AFTER_GRADE',json.dumps(dict(counts),sort_keys=True),flush=True)
    print('FIRST_VAL1000_TRUE_STRUCTURE_COUNTEREXAMPLES',json.dumps(problems,sort_keys=True),flush=True)
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(d,sort_keys=True)+'\n')
    print('VAL1000_TRUE_STRUCTURE_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
