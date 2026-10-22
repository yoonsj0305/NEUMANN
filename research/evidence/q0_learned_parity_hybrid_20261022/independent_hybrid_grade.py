#!/usr/bin/env python3
"""Original source exact grade ONLY AFTER immutable pred artifact written.
No admission of oracle top1. ARC2 public TRAIN 200 repeated previously scored cohort.
"""
import json,hashlib,zipfile,collections,argparse,pathlib
PREVIOUS_CLASSICAL=set('3c9b0459 1cf80156 68b16354 6150a2bd 7468f01a 6d0aefbc 833dafe3 9172f3a0 ed36ccf7 5582e5ca'.split())

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prediction',required=True);ap.add_argument('--fullzip',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 source=pathlib.Path(a.prediction);d=json.loads(source.read_bytes());assert d['denominator']==200 and not d['test_ground_truth_seen']
 ids=sorted(d['rows'],key=lambda x:hashlib.sha256(x.encode()).hexdigest());assert len(ids)==200
 assert hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
 passed=[];by_route=collections.Counter();num=collections.Counter();ledger={}
 with zipfile.ZipFile(a.fullzip) as z:
  for id in ids:
   entry=d['rows'][id];truth=json.loads(z.read('training/'+id+'.json'))['test'];pred=entry['prediction'];correct=pred is not None and pred==[t['output'] for t in truth]
   if correct:passed.append(id)
   num[entry['route']]+=1;by_route[entry['route']]+=int(correct)
   ledger[id]={'route':entry['route'],'correct':bool(correct),'prior_classical_correct':id in PREVIOUS_CLASSICAL}
 assert len(PREVIOUS_CLASSICAL)==10
 result={'schema':'NEUMANN_Q0_HYBRID_NO_TEST_LABEL_INFERENCE_POSTHOC_INDEPENDENT_SCORE.v1',
         'study':'ARC2 official public TRAIN heldout200 cohort REUSED: not official evaluation or pristine corpus',
         'prior_classical_correct':10,'hybrid_exact':len(passed),'hybrid_new_correct_ids':sorted(set(passed)-PREVIOUS_CLASSICAL),
         'hybrid_lost_classical_ids':sorted(PREVIOUS_CLASSICAL-set(passed)),
         'hybrid_exact_ids':sorted(passed),'num_assigned':dict(num),'correct_by_assigned_route':dict(by_route),
         'paired_accuracy_improvement_if_all_predictions_were_inference_locked':len(passed)-10,
         'hybrid_pred_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'estimated_inference_cost_s_from_earlier_cpu_runs':d['estimated_sequential_model_cpu_wall_s'],
         'global_frontier_accuracy':'NOT_PROVEN','global_Q3_learned_exclusive_operator':'NOT_PROVEN',
         'global_Q4_10x':'NOT_PROVEN','verification':'exact original test grid equality independent grader, all200 denominator',
         'all200_ledger':ledger}
 pathlib.Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print('REAL_SELECTED_HYBRID',len(passed),'OF_200; classical',10,'new',result['hybrid_new_correct_ids'],'lost',result['hybrid_lost_classical_ids'], 'extra_cost',d['learned_cpu_fit_inference_wall_s'],flush=True)
if __name__=='__main__':main()
