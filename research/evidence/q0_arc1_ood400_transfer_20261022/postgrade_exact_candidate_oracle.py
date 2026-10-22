#!/usr/bin/env python3
"""POST-GRADE ONLY. Never use this result to represent first-blind performance."""
import hashlib,json,pathlib,collections,time
from structural_object_language import all_candidates,predict_with
from arc_compositional_grammar import candidates_from_grammar
root=pathlib.Path('/mnt/data/neumann_arc_q0_new_20261022');pre=root/'holdout200_preg_FIRST.json'
raw=pre.read_bytes();assert hashlib.sha256(raw).hexdigest()=='9761c2e6080021e16f5db34db12e1ad8a448b1ad5bd413cee9bdc8c48f9e6a94'
d=json.loads(raw);counts=collections.Counter();reasons=[];start=time.perf_counter()
for i,row in enumerate(d['rows']):
 task=json.load(open(root/'train'/(row['id']+'.json')));safe={'train':task['train'],'test':[{'input':x['input']} for x in task['test']]};truth=[x['output'] for x in task['test']]
 a,b=all_candidates(safe)
 oldany=any(predict_with(safe,c)==truth for c in a)
 newany=any(predict_with(safe,c)==truth for c in b)
 counts['old_oracle']+=oldany;counts['added_oracle']+=newany and not oldany
 counts['new_oracle']+=oldany or newany
 if b and not a:
  reasons.append({'id':row['id'],'none_selected_correct':row['new_guess']!=truth,'any_exact_new_candidate':newany,'candidates':len(b),'examples':len(task['train'])})
 if (i+1)%50==0:print('ORACLE_POSTGRADE',i+1,flush=True)
res={'correctness_scope':'POSTGRADE_AFTER_IMMUTABLE_200_PREGRADE','receipt_sha256':hashlib.sha256(raw).hexdigest(),'counts':dict(counts),'new_only_covered':reasons,'postgrade_wall_s':time.perf_counter()-start,'gradient_calls':0,'candidate_language_ceiling_only':True}
(root/'holdout200_postgrade_oracle.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
print(json.dumps(res,indent=2))
