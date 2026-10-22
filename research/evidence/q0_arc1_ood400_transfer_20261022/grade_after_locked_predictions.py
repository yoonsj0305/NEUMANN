#!/usr/bin/env python3
"""Independent scorer. Read precommitted SHA and full official TRAIN labels only now."""
import argparse,json,hashlib,pathlib,math,collections
p=argparse.ArgumentParser();p.add_argument('--receipt',required=True);p.add_argument('--expected-sha',required=True);p.add_argument('--training',required=True);p.add_argument('--out',required=True);p.add_argument('--expected-denominator',type=int,default=200);a=p.parse_args()
b=pathlib.Path(a.receipt).read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha==a.expected_sha, (sha,a.expected_sha)
d=json.loads(b);assert len(d['rows'])==d['n']==a.expected_denominator;assert d['outputs_provided_to_solver']==0
ids=[r['id'] for r in d['rows']];assert len(set(ids))==len(ids)
metrics=collections.Counter();deltas=[];row_out=[]
for r in d['rows']:
 t=json.loads((pathlib.Path(a.training)/(r['id']+'.json')).read_text());targets=[z['output'] for z in t['test']]
 old=r['old_guess']==targets;new=r['new_guess']==targets
 metrics['old_correct']+=old;metrics['new_correct']+=new
 metrics['old_covered']+=r['old_coverage']>0
 metrics['new_covered']+=r['old_coverage']+r['new_coverage']>0
 metrics['old_only']+=old and not new;metrics['new_only']+=new and not old
 metrics['shared']+=old and new
 if old!=new: deltas.append({'id':r['id'],'old_correct':old,'new_correct':new,'chosen':r['chosen']})
 row_out.append({'id':r['id'],'old_exact':old,'new_exact':new,'family':r['selected_family']})
n=metrics['old_only']+metrics['new_only']
from math import comb
pval=min(1.0,2*sum(comb(n,i) for i in range(min(metrics['old_only'],metrics['new_only'])+1))/2**n) if n else 1
out={'study':'POSTHOC_ARC_AGI_2_TRAIN_ONLY_800_200_SOURCE_RELATIONAL_EXTENSION_FIRST_REPLAY', 'input_pregrade_sha256':sha,'n':d['n'],'scope':'published training set split, NOT official public evaluation 120, previous 200 already evaluated before grammar extension','results':dict(metrics),'paired_mcnemar_exact_two_sided_p':pval,'delta':deltas,'rows':row_out,'pregrade_wall_seconds':d['wall_s'],'gradients':0,'neural_training':False,'learned_unique_operator':False}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:out[k] for k in ['n','input_pregrade_sha256','results','paired_mcnemar_exact_two_sided_p','delta']},indent=2,ensure_ascii=False))
