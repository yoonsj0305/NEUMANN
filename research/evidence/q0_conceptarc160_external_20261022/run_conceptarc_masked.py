#!/usr/bin/env python3
"""FROZEN masked inference: ConceptARC160 3 tests per task. No labels accessible.
Old ARC2 symbolic composer vs dynamic geometry/repetition primitive synthesizer.
"""
import argparse,hashlib,json,pathlib,sys,time
from source_structural_v2 import synthesize_demos,predict as predict_new
from arc_compositional_grammar import find_programs,choose_program,predict as predict_old

def go():
  p=argparse.ArgumentParser();p.add_argument('--masked-dir',required=True);p.add_argument('--out',required=True);p.add_argument('--frozen',required=True);a=p.parse_args()
  reg=json.loads(pathlib.Path(a.frozen).read_text());assert reg['corpus_git_sha']=='a9e933c021388297f21fa1cded180105479addc0'
  root=pathlib.Path(a.masked_dir);files=sorted(root.glob('*/*.json'))
  assert len(files)==160
  groups={f.parent.name for f in files};assert len(groups)==16 and all(sum(f.parent.name==g for f in files)==10 for g in groups)
  started=time.perf_counter();out=[]
  for i,f in enumerate(files):
    task=json.loads(f.read_text());assert all('output' not in t for t in task['test'])
    old=find_programs(task);choice=choose_program(old);prior=predict_old(task,choice) if choice is not None else None
    dynamic,stats=synthesize_demos(task['train']);best=dynamic[0] if dynamic else None
    new=predict_new(task['test'],best)
    # Conservative triage: protect all old successes, run new rules only when old has no viable candidate.
    hybrid=prior if prior is not None else new
    out.append({'id':f.parent.name+'/'+f.stem,'group':f.parent.name,'n_tests':len(task['test']),
                'old':prior,'new':new,'hybrid':hybrid,
                'old_demo_candidates':len(old),'new_demo_candidates':len(dynamic),
                'new_operator':best[1] if best is not None else None})
    if (i+1)%40==0:print('MASKED_SOURCE_TASKS',i+1,flush=True)
  res={'schema':'NEUMANN_Q0_CONCEPTARC160_FROZEN_EXTERNAL_OOD.v1','source_git_sha':reg['source_git_sha'],
       'labels_accessible':False,'neural_training_calls':0,'total_tasks':160,'total_tests':sum(x['n_tests'] for x in out),
       'wall_s':time.perf_counter()-started,'rows':out}
  b=json.dumps(res,sort_keys=True,separators=(',',':')).encode();p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  print('BEFORE_GRADE_SHA256',hashlib.sha256(b).hexdigest(),'NEW_GRAMMAR_PREDICTED',sum(x['new'] is not None for x in out),
        'OLD_PREDICTED',sum(x['old'] is not None for x in out),'WALL_S',res['wall_s'],flush=True)
if __name__=='__main__':go()
