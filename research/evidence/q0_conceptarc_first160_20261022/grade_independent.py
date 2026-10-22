#!/usr/bin/env python3
"""After prior prediction-artifact upload: exact full 160-task and 480-grid test evaluation."""
import argparse,json,pathlib,hashlib,collections,math

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pred',required=True);ap.add_argument('--corpus',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args()
    pred_path=pathlib.Path(a.pred);raw=pred_path.read_bytes();d=json.loads(raw)
    assert not d['labels_seen'] and d['n']==160 and d['test_grids']==480
    rows=[];cum=collections.defaultdict(lambda:collections.Counter());correct={'old':0,'typed':0,'fallback':0};grid={x:0 for x in correct};wins=[]
    for x in d['rows']:
        group,name=x['id'].split('__',1)
        data=json.loads((pathlib.Path(a.corpus)/group/(name+'.json')).read_text())
        gt=[q['output'] for q in data['test']]
        assert len(gt)==3
        result={k:x[k] is not None and x[k]==gt for k in correct}
        for k in correct:
            correct[k]+=result[k]
            if x[k] is not None:grid[k]+=sum(y==z for y,z in zip(x[k],gt))
            cum[group][k]+=result[k]
        assert sum([bool(v) for v in result.values()])>=0
        if result['fallback'] and not result['old']:wins.append(x['id'])
        rows.append({'id':x['id'],'group':group,'actual':result,'old_covered':x['n_old']>0,'typed_covered':x['n_typed']>0})
    assert len(rows)==160 and len(set(x['id'] for x in rows))==160 and len(cum)==16
    oldonly=sum(x['actual']['old'] and not x['actual']['typed'] for x in rows)
    newonly=sum(x['actual']['typed'] and not x['actual']['old'] for x in rows)
    discordant=oldonly+newonly
    pval=min(1.0,2*sum(math.comb(discordant,i) for i in range(min(oldonly,newonly)+1))/(2**discordant)) if discordant else 1.0
    result={'n':160,'test_grids':480,'frozen_prediction_sha256':hashlib.sha256(raw).hexdigest(),
            'counts':correct,'grid_counts':grid,'n_covered':{'old':sum(z['old_covered'] for z in rows),'typed':sum(z['typed_covered'] for z in rows)},
            'grouped':{g:dict(c) for g,c in sorted(cum.items())},'new_only':newonly,'old_only':oldonly,
            'exact_mcnemar_p':pval,'fallback_extra_correct':wins,'rows':rows,
            'scope':'ConceptARC original 160/480 first source-body-unopened campaign, nonlearned exact DSL; not independent ARC frontier baseline'}
    p=pathlib.Path(a.out);p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('CONCEPTARC_160_FIRST_INDEPENDENT_GRADE',json.dumps({k:result[k] for k in ['counts','grid_counts','n_covered','new_only','old_only','exact_mcnemar_p','fallback_extra_correct']},sort_keys=True),flush=True)
if __name__=='__main__':main()
