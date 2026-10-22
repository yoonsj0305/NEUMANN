#!/usr/bin/env python3
"""Frozen unadapted ARC2 grammar to all official ARC1 public EVAL examples.
Inference sees only each task's train examples and test inputs, never test outputs.
No training or test-specific selection. Difference from ARC2 benchmark is input corpus only.
"""
import argparse,hashlib,json,pathlib,time
from structural_object_language import run_task

def main():
 p=argparse.ArgumentParser();p.add_argument('--masked-evaluation-dir',required=True);p.add_argument('--registry',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 register=json.loads(pathlib.Path(a.registry).read_text())
 assert register['source_commit']=='399030444e0ab0cc8b4e199870fb20b863846f34'
 root=pathlib.Path(a.masked_evaluation_dir)
 files=sorted(root.glob('*.json'))
 assert len(files)==register['evaluation_n']==400
 records=[];start=time.perf_counter()
 for i,f in enumerate(files):
  task=json.loads(f.read_text())
  assert 'train' in task and 'test' in task
  assert all('output' not in x for x in task['test']),f.name
  result=run_task(task);result['id']=f.stem
  records.append(result)
  if (i+1)%50==0:print('FROZEN_UNCHANGED_ARC1_OOD',i+1,'old',sum(bool(x['old_coverage']) for x in records),'new',sum(bool(x['new_coverage']+x['old_coverage']) for x in records),flush=True)
 data={'schema':'NEUMANN_ARC1_OOD400_SOURCE_ONLY_FIRST_PREGRADE.v1','source_repo':register['source_repo'],'source_commit':register['source_commit'],'n':len(records),'eval_labels_seen':False,'neural_training':False,'model_change_from_arc2_dev800':False,'old_demo_fits':sum(x['old_coverage']>0 for x in records),'new_demo_fits':sum(x['old_coverage']+x['new_coverage']>0 for x in records),'wall_s':time.perf_counter()-start,'rows':records}
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);s=json.dumps(data,sort_keys=True,separators=(',',':')).encode();out.write_bytes(s)
 print('ARC1_FIRST_400_PREGRADE_SHA256',hashlib.sha256(s).hexdigest(),'time_s',data['wall_s'],'old',data['old_demo_fits'],'new',data['new_demo_fits'],flush=True)

if __name__=='__main__':main()
