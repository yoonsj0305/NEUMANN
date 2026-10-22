#!/usr/bin/env python3
"""True source-only cascade: compute expensive structural candidates iff old program has no demo-fit.
The old receipt contains FIRST pregrade predictions ONLY, no validation labels.
"""
import json,argparse,pathlib,hashlib,time,sys
from relational_pipeline import task_rules,complexity,predict

def main():
 ap=argparse.ArgumentParser()
 for f in ('masked-data','freeze','old-pregrade','out'):ap.add_argument('--'+f,required=True)
 a=ap.parse_args()
 root=pathlib.Path(a.masked_data);oldpath=pathlib.Path(a.old_pregrade)
 reg=json.loads(pathlib.Path(a.freeze).read_text());fs=sorted(root.glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest())
 assert len(fs)==1000 and reg['dev_n']==800 and reg['validation_n']==200
 dh=lambda docs:hashlib.sha256(('\n'.join(f.stem for f in docs)+'\n').encode()).hexdigest()
 assert dh(fs[:800])==reg['dev_id_sha256'] and dh(fs[800:])==reg['val_id_sha256']
 old=json.loads(oldpath.read_text());assert old['n']==200 and len(old['rows'])==200
 idx={r['id']:r for r in old['rows']};assert len(idx)==200
 result=[];calls=0;started=time.perf_counter();seconds_spent=0
 for f in fs[800:]:
  rec=idx[f.stem];oldfit=bool(rec['old_coverage']+rec['new_coverage'])
  if oldfit:
   result.append({'id':f.stem,'choice':'prior_first','prediction':rec['new_guess'],'old_coverage':rec['old_coverage']+rec['new_coverage'],'typed_coverage':None})
   continue
  task=json.loads(f.read_text());assert all('output' not in t for t in task['test'])
  t0=time.perf_counter();candidates=task_rules(task);seconds_spent+=time.perf_counter()-t0;calls+=1
  c=min(candidates,key=complexity) if candidates else None
  p=predict(task,c) if c else None
  result.append({'id':f.stem,'choice':'new_typed_object' if p is not None else 'ABSTAIN','prediction':p,'old_coverage':0,'typed_coverage':len(candidates)})
 assert len(result)==200
 counts={k:sum(r['choice']==k for r in result) for k in ('prior_first','new_typed_object','ABSTAIN')}
 d={'n':200,'status':'POSTHOC_FROZEN_SOURCE_ONLY_CASCADE_ALREADY_EVALUATED_HOLDOUT','old_pregrade_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest(),'no_test_outputs_in_program_search':True,'calls_to_expensive_new_synthesizer':calls,'wall_s':time.perf_counter()-started,'typed_search_wall_s':seconds_spent,'records':result,'route_counts':counts}
 dest=pathlib.Path(a.out);dest.write_text(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n')
 print(json.dumps({'first_pregrade_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_only_calls':calls,'wall_seconds':d['wall_s'],'routes':counts},sort_keys=True),flush=True)
if __name__=='__main__':main()
