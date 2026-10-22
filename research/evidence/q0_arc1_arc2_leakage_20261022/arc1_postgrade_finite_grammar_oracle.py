#!/usr/bin/env python3
"""POSTGRADE only. Enumerate ALL demo-consistent candidates from immutable frozen DSL.
This computes the real ceiling of candidate selection, NOT an inference score.
"""
import argparse,collections,hashlib,json,pathlib,time
from structural_object_language import all_candidates,predict_with

def main():
 ap=argparse.ArgumentParser()
 for n in ['evaluation_dir','score','audit','out']:ap.add_argument('--'+n.replace('_','-'),required=True)
 a=ap.parse_args()
 files=sorted(pathlib.Path(a.evaluation_dir).glob('*.json'))
 assert len(files)==400
 compact=json.loads(pathlib.Path(a.score).read_text());assert compact['n']==400
 s={x[0]:x for x in compact['score']}
 audit=json.loads(pathlib.Path(a.audit).read_text());m={x['id']:x for x in audit['rows']}
 assert len(m)==len(s)==400
 cc=collections.Counter();rows=[];st=time.perf_counter()
 for i,file in enumerate(files):
  id=file.stem;task=json.loads(file.read_text());safe={'train':task['train'],'test':[{'input':x['input']} for x in task['test']]};truth=[x['output'] for x in task['test']]
  old,new=all_candidates(safe)
  win_old=[str(x[0]) for x in old if predict_with(safe,x)==truth]
  win_new=[str(x[0]) for x in new if predict_with(safe,x)==truth]
  oracleold=bool(win_old);oraclenew=bool(win_old or win_new)
  cc['baseline_oracle']+=oracleold;cc['extended_oracle']+=oraclenew
  cc['new_only_oracle']+=oraclenew and not oracleold
  cc['candidate_coverage']+=bool(old or new)
  if m[id]['id_disjoint']:
    cc['id_disjoint_18_oracle']+=oraclenew
    cc['id_disjoint_18_covered']+=bool(old or new)
  cc['candidate_count_total']+=len(old)+len(new)
  score=s[id]
  assert not bool(score[1]) or oracleold
  assert not bool(score[2]) or oraclenew
  rows.append({'id':id,'old_oracle':oracleold,'new_oracle':oraclenew,'id_disjoint':m[id]['id_disjoint'],'n_old':len(old),'n_extension':len(new),'winners_old':win_old,'winners_new':win_new})
  if (i+1)%100==0:print('COMPLETE_POSTGRADE_ORACLE',i+1,flush=True)
 result={'schema':'NEUMANN_Q0_ARC1_PUBLIC400_FIXED_ALL_CANDIDATES_POSTGRADE_CEILING','first_score_sha256':hashlib.sha256(pathlib.Path(a.score).read_bytes()).hexdigest(),'first_pregade_sha256':compact['pregade_artifact_sha256'],'full_400_problems':400,'oracle':dict(cc),'wall_s':time.perf_counter()-st,'source_content_audit_sha256':hashlib.sha256(pathlib.Path(a.audit).read_bytes()).hexdigest(),'interpretation':'Exact ceiling for frozen finite source-conditioned candidate grammar only; arbitrary program synthesis or frontier model not bounded by this oracle','rows':rows}
 target=pathlib.Path(a.out);target.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print('FINITE_GRAMMAR_FIRST_COMPLETE_POSTGRADE_ORACLE',dict(cc),flush=True)
 print('ORACLE_PROOF_SHA256',hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)

if __name__=='__main__':main()
