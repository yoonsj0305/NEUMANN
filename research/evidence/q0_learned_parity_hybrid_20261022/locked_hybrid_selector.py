#!/usr/bin/env python3
"""Frozen answer-free hybrid of two PREVIOUSLY IMMUTABLE GitHub prediction artifacts.
No official test labels, no learned test-output side channels. Scientific cohort: ARC2 TRAIN200.
Priority is classical demo-certified program, then CV-certified local learned rule, else abstain.
"""
import zipfile,json,hashlib,argparse,pathlib,collections
CLASSICAL_SHA='9293322611df92093ddf55c694c5e85b58f1efc8ad0b7fea877d6d99c417b229'
LEARNED_SHA='166601d58786f856be24b09d832300cdf5023abbb06acd6fffd7ad24c38896f9'
VALIDATION_SHA='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'

def archive_member(zipname,entry,expected):
 with zipfile.ZipFile(zipname) as z: raw=z.read(entry)
 sha=hashlib.sha256(raw).hexdigest()
 if sha!=expected:raise ValueError('Immutable prediction artifact SHA changed '+sha)
 return json.loads(raw)

def combine(old,new):
 assert old['n']==new['count']==200 and new['id_sha256']==VALIDATION_SHA
 assert old['eval_labels_provided_to_solver'] is False and new['test_label_access'] is False
 classical={x['id']:x for x in old['decisions']}; learned=new['rows']
 assert len(classical)==len(learned)==200 and set(classical)==set(learned)
 rows={};cnt=collections.Counter()
 for id in sorted(classical):
  c=classical[id];m=learned[id];cc=c.get('attempt')
  if cc is not None:
   label='EXACT_CLASSICAL_PROGRAM';prediction=cc
  elif m.get('status')=='fit' and m.get('cv_all') is True:
   label='ACTUALLY_LEARNED_CROSSDEMO_VALIDATED_RULE';prediction=m['prediction']
  else:
   label='ABSTAIN_NO_PROVED_CANDIDATE';prediction=None
  cnt[label]+=1;rows[id]={'route':label,'prediction':prediction}
 assert sum(cnt.values())==200
 return {'schema':'NEUMANN_Q0_FROZEN_CLASSICAL_FIRST_CV_LEARNED_SECOND_HYBRID.v1',
         'denominator':200,'original_prior_classical_prediction_sha256':CLASSICAL_SHA,
         'original_frozen_learned_prediction_sha256':LEARNED_SHA,
         'test_ground_truth_seen':False,'selection_uses_grader_output':False,
         'decision':'original source demo-valid classical first; else learned decision tree if and ONLY IF fully leave-one-demonstration-out consistent; else abstain',
         'routed_count':dict(cnt),'prior_symbolic_inference_wall_s':old['wall_s'],'learned_cpu_fit_inference_wall_s':new['wall_s'],
         'estimated_sequential_model_cpu_wall_s':old['wall_s']+new['wall_s'],'rows':rows}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--classical',required=True);ap.add_argument('--learned',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 c=archive_member(a.classical,'ARC2_TRAIN200_PREDICTIONS_PRE_GRADE.json',CLASSICAL_SHA)
 m=archive_member(a.learned,'FROZEN_NEURAL_FREE_DECISION_TREE_200_PREGRADE.json',LEARNED_SHA)
 result=combine(c,m);pathlib.Path(a.out).write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
 print('NO_ANSWER_HYBRID_LOCKED',result['routed_count'],'PREDICTION_SHA',hashlib.sha256(pathlib.Path(a.out).read_bytes()).hexdigest(),flush=True)
