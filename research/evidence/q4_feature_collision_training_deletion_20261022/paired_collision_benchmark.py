#!/usr/bin/env python3
"""Independent source-only paired CPU experiment. Validation test targets must be stripped in input ZIP.
Shows mathematical impossibility (feature collisions) and strong exact original fit equivalence.
No GPU, no gradient, no frontier claim. Includes repeated actual wall, all 1000 source tasks.
"""
import argparse,subprocess,sys,json,hashlib,zipfile,time,pathlib,statistics,collections
import numpy as np

def audit_witnesses(z, ids, old_module, optimized, split):
 result=[]
 for id in sorted(ids):
  d=json.loads(z.read('training/'+id+'.json'))
  # Original frozen feature algorithm, independently regenerating every source witness.
  examples=d['train'];seen={};witness=None
  for ex_num,ex in enumerate(examples):
   X=old_module.features(ex['input']);Y=np.asarray(ex['output']).ravel()
   for index,(row,y) in enumerate(zip(X,Y)):
    key=row.tobytes();tuple_hit=(ex_num,index,int(y))
    if key in seen and seen[key][2]!=int(y):
     witness={'original_task':id,'split':split,'identical_feature_hash':hashlib.sha256(key).hexdigest(),
       'observed_prior_position':list(seen[key]),'conflicting_position':list(tuple_hit),
       'distinct_labels':[seen[key][2],int(y)],
       'argument':'identical full fixed features cannot map to two labels in any deterministic model'}
     break
    seen[key]=tuple_hit
   if witness:break
  assert witness and witness['distinct_labels'][0]!=witness['distinct_labels'][1],id
  result.append(witness)
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--masked-data',required=True);p.add_argument('--baseline',required=True);p.add_argument('--optimized',required=True);p.add_argument('--out-dir',required=True);p.add_argument('--pairs',type=int,default=5);a=p.parse_args()
 out=pathlib.Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
 import importlib.util
 sp=importlib.util.spec_from_file_location('genuine_old_src',a.baseline)
 src=importlib.util.module_from_spec(sp);sp.loader.exec_module(src)
 times={};proofs={};summary={};data={}
 with zipfile.ZipFile(a.masked_data) as z:
  ids=sorted((n.rsplit('/',1)[-1][:-5] for n in z.namelist()),key=lambda x:hashlib.sha256(x.encode()).hexdigest())
  assert len(ids)==1000
  for split,cohort in [('dev',ids[:800]),('valid',ids[800:])]:
   assert len(cohort)==(800 if split=='dev' else 200)
   if split=='valid':
    assert hashlib.sha256(('\n'.join(cohort)+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
    for id in cohort:
     d=json.loads(z.read('training/'+id+'.json'))
     assert all('output' not in t for t in d['test']),id
   results=[]
   for i in range(a.pairs):
    group=['baseline','optimized'] if i%2==0 else ['optimized','baseline'];r={}
    for mode in group:
     script=a.baseline if mode=='baseline' else a.optimized
     path=out/f'{split}_{i}_{mode}.json'
     cmd=[sys.executable,script,'--zip',a.masked_data,'--subset',split,'--out',str(path)]
     start=time.perf_counter()
     q=subprocess.run(cmd,capture_output=True,text=True,timeout=150)
     elapsed=time.perf_counter()-start
     if q.returncode!=0:raise RuntimeError(str(cmd)+'\n'+q.stdout[-1200:]+'\n'+q.stderr[-1200:])
     receipt=json.loads(path.read_text());assert receipt['count']==len(cohort)
     r[mode]={'s':elapsed,'receipt':receipt}
     # Preserve raw model receipts for 1st trial only, avoiding duplicated massive records.
     if i>0:path.unlink()
    base,fast=r['baseline']['receipt'],r['optimized']['receipt']
    assert set(base['rows'])==set(fast['rows'])==set(cohort)
    preserved=[];skipped=[]
    for id,b in base['rows'].items():
     c=fast['rows'][id]
     if b['status']=='fit':
      assert c['status']=='fit' and c['prediction']==b['prediction'] and c['cv_all']==b['cv_all'],id
      preserved.append(id)
     if c['status']=='feature_collision':
      assert b['status']=='no_exact_fit',id
      skipped.append(id)
    assert len(preserved)==(43 if split=='dev' else 9)
    assert len(skipped)==(218 if split=='dev' else 54)
    if i==0:
      proofs[split]=audit_witnesses(z,skipped,src,fast,split)
      assert len(proofs[split])==len(skipped)
    results.append({'rep':i,'order':group,'baseline_process_wall_s':r['baseline']['s'],
      'optimized_process_wall_s':r['optimized']['s'],'baseline_reported_internal_wall_s':base['wall_s'],
      'optimized_reported_internal_wall_s':fast['wall_s'],'identical_accepted_predictions':len(preserved),
      'feature_collision_unsatisfiable_tasks':len(skipped)})
   mb=statistics.median(x['baseline_process_wall_s'] for x in results)
   mo=statistics.median(x['optimized_process_wall_s'] for x in results)
   summary[split]={'task_count':len(cohort),'paired_trials':a.pairs,'model_fit_predictions_unchanged':len(preserved),
        'mathematically_impossible_candidate_models_skipped':len(skipped),
        'baseline_median_wall_s':mb,'optimized_median_wall_s':mo,'speedup':mb/mo,'individual_runs':results}
   print('SOURCE_ORIGINAL_PAIRED',split,'n',len(cohort),'collision',len(skipped),
         'true_learned_solutions_preserved',len(preserved),'medians',round(mb,3),round(mo,3),'speedup',round(mb/mo,3),flush=True)
 # Each of 272 source-origins includes independent feature hash and opposite training labels.
 assert sum(len(v) for v in proofs.values())==272
 verdict={'schema':'NEUMANN_Q4_EXACT_NO_UNNECESSARY_MODEL_TRAINING_FEATURE_COLLISION_GATE.v1',
   'study':'public ARC2 TRAIN 800 development plus previously-scored reserved TRAIN 200, no official-eval generalization claim',
   'source_pin':'f3283f727488ad98fe575ea6a5ac981e4a188e49',
   'model_changed_only_impossibility_prefilter':True,
   'mathematical_statement':'if F(x1)=F(x2) and training targets differ, NO deterministic output f(F(x)) can fit both, therefore training any fixed-feature decision tree is unnecessary',
   'train_sources_1000':1000,'witnesses_total':272,'both_split_learned_accepted_models_identical':True,
   'paired':summary,'global_Q3_novel_operator':'OPEN','global_Q4_10x':'OPEN','frontier_performance':'OPEN'}
 (out/'PAIRED_SOURCE1000_COST_EVIDENCE.json').write_text(json.dumps(verdict,indent=2,sort_keys=True)+'\n')
 (out/'ALL272_EXACT_FEATURE_COLLISION_WITNESSES.json').write_text(json.dumps(proofs,indent=2,sort_keys=True)+'\n')
 print('COMPLETE_PROOF_CONDITIONED_COMPUTE_DELETION',hashlib.sha256((out/'PAIRED_SOURCE1000_COST_EVIDENCE.json').read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
