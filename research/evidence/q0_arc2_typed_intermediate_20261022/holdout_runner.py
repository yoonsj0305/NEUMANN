#!/usr/bin/env python3
"""Source input and demonstrations ONLY. Former ARC2 code is exact original source frozen baseline."""
import argparse,hashlib,json,pathlib,time,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT.parent/'neumann_q0_frontier_gate_20261022'))
from relational_pipeline import task_rules,complexity,predict
from arc_compositional_grammar import find_programs,choose_program,predict as original_predict

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--frozen',required=True);p.add_argument('--out',required=True);p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=0);args=p.parse_args()
 r=json.loads(pathlib.Path(args.frozen).read_text());files=list(pathlib.Path(args.source).glob('*.json'));files.sort(key=lambda x:hashlib.sha256(x.stem.encode()).hexdigest())
 # Original source file list must contain exactly all 1000 filenames even if TEST fields masked
 assert len(files)==1000
 sha=lambda a:hashlib.sha256(('\n'.join(x.stem for x in a)+'\n').encode()).hexdigest()
 assert sha(files[:800])==r['dev_id_sha256'] and sha(files[800:])==r['val_id_sha256']
 hold=files[800:];hold=hold[args.offset:args.offset+args.limit] if args.limit else hold[args.offset:]
 start=time.perf_counter();rows=[]
 for q in hold:
  task=json.loads(q.read_text())
  assert all('output' not in d for d in task['test']), 'FAIL: TEST LABEL FOUND IN INFERENCE'
  source={'train':task['train'],'test':[{'input':z['input']} for z in task['test']]}
  old=find_programs(source);b=choose_program(old)
  old_pred=original_predict(source,b) if b else None
  t0=time.perf_counter();new=task_rules(source)
  chosen=min(new,key=complexity) if new else None
  new_pred=predict(source,chosen) if chosen else None
  pred=old_pred if old_pred is not None else new_pred
  rows.append({'id':q.stem,'n_legacy':len(old),'n_typed':len(new),'baseline_pred':old_pred,'typed_pred':new_pred,'hybrid_pred':pred,'selected':('legacy' if old_pred is not None else 'typed' if new_pred is not None else 'abstain'), 'selected_typed_AST':chosen if new_pred is not None else None,'typed_wall_s':time.perf_counter()-t0})
  if len(rows)%50==0:print('ANSWER_FREE_PROGRESS',len(rows),'typed_admit',sum(v['n_typed']>0 for v in rows),'baseline_admit',sum(v['n_legacy']>0 for v in rows),'wall',round(time.perf_counter()-start,3),flush=True)
 result={'schema':'NEUMANN_TYPED_RELATIONAL_INTERMEDIATE_ARC2_200_FIRST.v1','label_free':True,'frozen_source':r,'n':len(rows),'total_wall_s':time.perf_counter()-start,'baseline_coverage':sum(x['n_legacy']>0 for x in rows),'typed_coverage':sum(x['n_typed']>0 for x in rows),'hybrid_coverage':sum(x['hybrid_pred'] is not None for x in rows),'records':rows}
 dst=pathlib.Path(args.out);dst.parent.mkdir(parents=True,exist_ok=True);data=json.dumps(result,sort_keys=True,separators=(',',':')).encode();dst.write_bytes(data)
 print('PREGRADE_SHA256',hashlib.sha256(data).hexdigest(),'N',len(rows),'WALL',result['total_wall_s'],flush=True)
if __name__=='__main__':main()
