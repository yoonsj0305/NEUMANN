#!/usr/bin/env python3
"""Independent grader only after prediction artifact from separate job was uploaded.
All 400 published ARC1 evaluation test outputs read ONLY in this process.
"""
import argparse,collections,hashlib,json,pathlib,math

def main():
 p=argparse.ArgumentParser();p.add_argument('--predictions',required=True);p.add_argument('--evaluation-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 data=pathlib.Path(a.predictions).read_bytes();sha=hashlib.sha256(data).hexdigest();receipt=json.loads(data)
 assert receipt['n']==len(receipt['rows'])==400 and receipt['eval_labels_seen'] is False
 folders=pathlib.Path(a.evaluation_dir);filenames=sorted(folders.glob('*.json'))
 assert len(filenames)==400
 assert [f.stem for f in filenames]==[x['id'] for x in receipt['rows']]
 n=collections.Counter();deltas=[];strict_rows=[]
 for r,f in zip(receipt['rows'],filenames):
  t=json.loads(f.read_text());answer=[y['output'] for y in t['test']]
  old=r['old_guess']==answer;new=r['new_guess']==answer
  n['baseline_correct']+=old;n['new_correct']+=new
  n['baseline_demo_fit']+=r['old_coverage']>0;n['new_demo_fit']+=r['old_coverage']+r['new_coverage']>0
  n['new_only']+=new and not old;n['baseline_only']+=old and not new
  if new!=old:deltas.append({'id':r['id'],'baseline_correct':old,'new_correct':new,'chosen':r['chosen']})
  strict_rows.append({'id':r['id'],'baseline_correct':old,'new_correct':new,'model_selected_family':r['selected_family']})
 k=n['new_only']+n['baseline_only']
 from math import comb
 prob=min(1.,2*sum(comb(k,j) for j in range(min(n['baseline_only'],n['new_only'])+1))/2**k) if k else 1.
 verdict={'schema':'NEUMANN_ARC1_OOD400_POSTGRADE_FIRST.v1','source_pin':receipt['source_commit'],'n':400,'pregade_artifact_sha256':sha,'results':dict(n),'paired_mcnemar_exact_two_sided_p':prob,'deltas':deltas,'rows':strict_rows,'inference_seconds':receipt['wall_s'],'neural_specific_structure':'UNPROVEN','frontier_parity':'UNPROVEN','claims':'Cross-corpus transfer of fixed *classical* grammar only. Public test labels; not hidden leaderboard or first-ever ARC1 exposure proof.'}
 out=pathlib.Path(a.out);out.write_text(json.dumps(verdict,indent=2,sort_keys=True)+'\n')
 print('STRICT_POSTGRADE_400',json.dumps({'results':dict(n),'p_value':prob,'pred_sha256':sha,'deltas':deltas}),flush=True)

if __name__=='__main__':main()
