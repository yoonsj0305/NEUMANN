#!/usr/bin/env python3
"""Out-of-process scoring, only now opens original 200 test outputs.
Model phase sees ONLY masked val. This is train-only reused cohort, NOT ARC2 official eval.
"""
import argparse,json,hashlib,zipfile,collections,statistics,math,time
from math import comb
PREVIOUS_CLASSICAL=set('3c9b0459 1cf80156 68b16354 6150a2bd 7468f01a 6d0aefbc 833dafe3 9172f3a0 ed36ccf7 5582e5ca'.split())

def exact_mcnemar(new,old):
 onlynew=len(new-old);onlyold=len(old-new); n=onlynew+onlyold
 p=min(1,2*sum(comb(n,i) for i in range(min(onlynew,onlyold)+1))/2**n) if n else 1
 return {'learned_only':onlynew,'classical_only':onlyold,'discordant_n':n,'exact_twosided_p':p}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prediction',required=True);ap.add_argument('--fullzip',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 d=json.load(open(a.prediction)); assert d['subset']=='valid' and d['count']==200 and d['test_label_access'] is False
 keys=sorted(d['rows']);assert len(keys)==200
 ordered=sorted(keys,key=lambda v:hashlib.sha256(v.encode()).hexdigest());assert hashlib.sha256(('\n'.join(ordered)+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
 allok=set(); cvok=set(); mappingok=set();nn=collections.Counter();notes={}; t=time.perf_counter()
 with zipfile.ZipFile(a.fullzip) as z:
  for id in keys:
   r=d['rows'][id];nn[r['status']]+=1
   orig=json.loads(z.read('training/'+id+'.json'))
   truth=[t['output'] for t in orig['test']]
   match=r['status']=='fit' and r['prediction']==truth
   if match:allok.add(id)
   if match and r.get('cv_all',False):cvok.add(id)
   mapmatch=bool(r.get('mapping_fit',False)) and r.get('baseline_color_lookup')==truth
   if mapmatch:mappingok.add(id)
   notes[id]={'fitted':r['status']=='fit','cv_pass':r.get('cv_all',False),'learned_exact':match,'cv_gated_exact':match and r.get('cv_all',False),'classical_color_mapping_exact':mapmatch,'prior_classical_composition_exact':id in PREVIOUS_CLASSICAL}
 assert len(PREVIOUS_CLASSICAL)==10
 verdict={'schema':'NEUMANN_Q0_TASK_CONDITIONED_LEARNED_RULE_HELDOUT200_INDEPENDENT_GRADE.v1',
 'scope':'ARC-AGI-2 published training corpus reserved previously scored 200; not untouched official ARC2 evaluation',
 'test_input_output_separation':'masked 200 test outputs unavailable to predictor job; second independent grade job reads original labels',
 'original_git_commit':'f3283f727488ad98fe575ea6a5ac981e4a188e49',
 'prediction_sha256':hashlib.sha256(open(a.prediction,'rb').read()).hexdigest(),
 'validation_n':200,'previous_classical_exact':len(PREVIOUS_CLASSICAL),
 'learned_tree_exact':len(allok),'learned_tree_cv_gated_exact':len(cvok),
 'no_learning_color_lookup_exact':len(mappingok),'model_fit_status':dict(nn),
 'paired_unrestricted_vs_classical':exact_mcnemar(allok,PREVIOUS_CLASSICAL),
 'paired_cv_gated_vs_classical':exact_mcnemar(cvok,PREVIOUS_CLASSICAL),
 'paired_cv_gated_vs_no_learning_color_lookup':exact_mcnemar(cvok,mappingok),
 'new_ids_vs_prior_classical':sorted(allok-PREVIOUS_CLASSICAL),
 'cv_gated_new_ids_vs_prior_classical':sorted(cvok-PREVIOUS_CLASSICAL),
 'prior_classical_ids':sorted(PREVIOUS_CLASSICAL),'tree_correct_ids':sorted(allok),'tree_cv_gated_ids':sorted(cvok),'mapping_correct_ids':sorted(mappingok),
 'all200_case_ledger':notes,
 'learned_invented_operators':False,'is_frontier_level':False,'global_Q3':'OPEN','global_Q4_10x':'OPEN','global_Q6':'OPEN'}
 with open(a.out,'w') as out:json.dump(verdict,out,sort_keys=True,indent=2)
 print(json.dumps({k:v for k,v in verdict.items() if k in ('validation_n','learned_tree_exact','learned_tree_cv_gated_exact','no_learning_color_lookup_exact','previous_classical_exact','new_ids_vs_prior_classical','cv_gated_new_ids_vs_prior_classical','paired_cv_gated_vs_classical')},sort_keys=True),flush=True)
if __name__=='__main__':main()
