#!/usr/bin/env python3
"""Independent labels-only postgrade, strict ALL 3 tests correctness and paired outcomes."""
import argparse,collections,hashlib,json,pathlib

def go():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--predictions',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 predfile=pathlib.Path(a.predictions);pr=json.loads(predfile.read_text());assert pr['total_tasks']==160 and pr['total_tests']==480 and not pr['labels_accessible']
 score=collections.Counter();groups=collections.defaultdict(lambda:collections.Counter());rows=[];scores={}
 for rec in pr['rows']:
  f=pathlib.Path(a.source)/(rec['id']+'.json');raw=json.loads(f.read_text());truth=[z['output'] for z in raw['test']]
  assert len(truth)==len(rec['old'] or truth)==len(rec['new'] or truth)==len(rec['hybrid'] or truth)==3
  row={'id':rec['id'],'group':rec['group'],'old_demo_candidates':rec['old_demo_candidates'],'new_demo_candidates':rec['new_demo_candidates'],'new_operator':rec['new_operator']}
  for arm in ['old','new','hybrid']:
   candidate=rec[arm];hits=[int(x==y) for x,y in zip(candidate or [None]*3,truth)]
   ok=all(hits);row[arm+'_correct']=ok;row[arm+'_tests']=sum(hits)
   score[arm+'_all3']+=int(ok);score[arm+'_individual']+=sum(hits);score[arm+'_coverage']+=int(candidate is not None)
   groups[rec['group']][arm+'_all3']+=int(ok)
  if row['new_correct'] and not row['old_correct']:score['new_only']+=1
  if row['old_correct'] and not row['new_correct']:score['old_only']+=1
  if row['hybrid_correct'] and not row['old_correct']:score['hybrid_new_only']+=1
  rows.append(row)
 assert len(rows)==160
 all_info={'schema':'NEUMANN_Q0_CONCEPTARC160_FIRST_OOD_POSTGRADE.v1','original_test_count':480,
  'original_task_count':160,'pregrade_sha256':hashlib.sha256(predfile.read_bytes()).hexdigest(),
  'scores':dict(score),'concept_groups':{g:dict(v) for g,v in sorted(groups.items())},'rows':rows,
  'scientific_attribution':'Zero-training symbolic operator composition, not neural new-operator invention. Original task sources were not opened until after fixed freeze. Source may share concepts with ARC2, no guaranteed independent problem family.'}
 path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(all_info,indent=2,sort_keys=True)+'\n');print('FIRST_ALL_160_RESULTS',dict(score),flush=True)
if __name__=='__main__':go()
