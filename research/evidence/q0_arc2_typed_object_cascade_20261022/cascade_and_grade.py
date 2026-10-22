#!/usr/bin/env python3
"""NEUMANN Q0 exact-candidate-first routing; no correctness labels in routing.

First old fixed source-only program selection. If any exact demo-consistent
candidate exists, retain its answer. Otherwise use new typed-object pipeline.
Posthoc experiment on previously evaluated ARC2 training 200, not firstblind.
"""
import json,argparse,hashlib,pathlib,math

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--old-locked',required=True);ap.add_argument('--new-locked',required=True)
 ap.add_argument('--out',required=True);a=ap.parse_args()
 oldfile=pathlib.Path(a.old_locked);newfile=pathlib.Path(a.new_locked)
 old=json.loads(oldfile.read_text());new=json.loads(newfile.read_text())
 assert old['n']==new['num']==200
 om={z['id']:z for z in old['rows']};assert len(om)==200
 records=[]
 for n in new['records']:
  p=om[n['id']]
  # Source-only decision; never inspect unseen test answer
  original_fit=p['old_coverage']+p['new_coverage']>0
  chosen='prior_first' if original_fit else ('new_typed_object' if n['pred'] is not None else 'ABSTAIN')
  y=p['new_guess'] if original_fit else n['pred']
  records.append({'id':n['id'],'choice':chosen,'prediction':y,'old_coverage':p['old_coverage']+p['new_coverage'],'typed_coverage':n['num_candidates']})
 out={'n':200,'status':'POSTHOC_COMPOSED_ON_ALREADY_EVALUATED_TRAIN_HOLDOUT200_NOT_NEW_FIRSTBLIND','source_only_routing':True,'old_pregrade_sha256':hashlib.sha256(oldfile.read_bytes()).hexdigest(),'typed_new_pregrade_sha256':hashlib.sha256(newfile.read_bytes()).hexdigest(),'records':records,'route_counts':{k:sum(x['choice']==k for x in records) for k in ('prior_first','new_typed_object','ABSTAIN')}}
 p=pathlib.Path(a.out);p.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
 print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'route_counts':out['route_counts']}))
if __name__=='__main__':main()
