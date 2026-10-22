#!/usr/bin/env python3
"""Independent exact multicase ARC grid scorer, run only after separate pregrade receipt."""
import argparse,json,pathlib,hashlib,math

def equals(pred,truth):return pred is not None and pred==[t['output'] for t in truth['test']]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pred',required=True);p.add_argument('--real',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 b=pathlib.Path(a.pred).read_bytes();payload=json.loads(b);r=payload['records'];assert payload['label_free'] and len(r)==payload['n']==200
 scores=[]
 for x in r:
  truth=json.load(open(pathlib.Path(a.real)/(x['id']+'.json')))
  old=equals(x['baseline_pred'],truth);new=equals(x['typed_pred'],truth);hyb=equals(x['hybrid_pred'],truth)
  scores.append({'id':x['id'],'baseline':old,'typed':new,'hybrid':hyb,'baseline_admit':x['n_legacy']>0,'typed_admit':x['n_typed']>0})
 assert len({x['id'] for x in scores})==200
 s={k:sum(x[k] for x in scores) for k in ('baseline','typed','hybrid','baseline_admit','typed_admit')}
 s['hybrid_additional']=sum(x['hybrid'] and not x['baseline'] for x in scores)
 s['hybrid_regressions']=sum(x['baseline'] and not x['hybrid'] for x in scores)
 s['typed_additional']=sum(x['typed'] and not x['baseline'] for x in scores)
 s['typed_regressions']=sum(x['baseline'] and not x['typed'] for x in scores)
 n=s['hybrid_additional']+s['hybrid_regressions'];k=min(s['hybrid_additional'],s['hybrid_regressions']);s['mcnemar_two_sided_p']=min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else 1
 verdict={'pregrade_sha256':hashlib.sha256(b).hexdigest(),'official_train200_not_official_eval':True,'not_firstblind_to_any_past_use_of_holdout':True,'n':200,'scored':s,'rows':scores}
 out=pathlib.Path(a.out);out.write_text(json.dumps(verdict,indent=2,sort_keys=True))
 print('SCOPED_REAL_NEW_RELATIONAL_COMPOSER_RESULT',s,'SOURCE',verdict['pregrade_sha256'],flush=True)
if __name__=='__main__':main()
