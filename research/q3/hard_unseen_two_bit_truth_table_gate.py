"""Q3 independent second unopened SyGuS cohort: two-bit truth-table representation.
The table and coordinates are DISCOVERED from I/O; the two-bit universe,
enumerator and safe interpreter are human-authored, not discovered primitives.
Created post-first cohort and frozen before downloading PRE_124..147 originals.
"""
import hashlib
import itertools
import json
from pathlib import Path
import time
import hard_original_unopened_method_gate as old

IDS=[f'PRE_{i}_10' for i in range(124,148)]
SOURCE_PRIOR_BLOB='9e514ec24ab92ad74d95dcf25d9aaa41cbdd2b68'
NEW_HUMAN_METHOD_SHA='b122e7ff722418808cd2c355018713dd6e48a8f71e9bc47a51055bb15b142702'
BINARY_BUDGET=1000
UNARY_BUDGET=500

def execute(p,x):
 n=len(x);d1=p['offset_a'];d2=p['offset_b'];v=[]
 for i in range(n):
  j=i+d1;k=i+d2
  a=x[j] if 0<=j<n else p['boundary_a']
  b=x[k] if 0<=k<n else p['boundary_b']
  v.append(p['table'][2*a+b])
 return v

def nontrivial(t):
 return (t[0]!=t[2] or t[1]!=t[3]) and (t[0]!=t[1] or t[2]!=t[3])

def derive(examples,budget=BINARY_BUDGET):
 if not examples or len(examples)<3 or any(not old.bits(x) or not old.bits(y) for x,y in examples):
  return None,0
 n=len(examples[0][0]);attempts=0
 offsets=sorted(range(-4,5),key=lambda z:(abs(z),z))
 for oa,ob in itertools.product(offsets,repeat=2):
  if oa==ob:continue
  for ba,bb in itertools.product((0,1),repeat=2):
   if attempts>=budget:return None,attempts
   attempts+=1
   table=[None]*4;conflict=False
   for x,y in examples:
    for i,want in enumerate(y):
     j=i+oa;k=i+ob
     a=x[j] if 0<=j<n else ba
     b=x[k] if 0<=k<n else bb
     z=2*a+b
     if table[z] is None:table[z]=want
     elif table[z]!=want:conflict=True;break
    if conflict:break
   if conflict or any(t is None for t in table) or not nontrivial(table):continue
   candidate={'kind':'SynthesizedBinaryBitTable','offset_a':oa,'offset_b':ob,
              'boundary_a':ba,'boundary_b':bb,'table':table}
   if all(execute(candidate,x)==y for x,y in examples):
    return candidate,attempts
 return None,attempts

def exact2(p,examples):
 return p is not None and all(execute(p,x)==y for x,y in examples)

def run():
 st=time.perf_counter()
 rows=[]
 for ident in IDS:
  rec={'id':ident}
  try:
   data=old.fetch_original(ident)
   rec['original_sha256']=old.digest(data);rec['published_records']=len(data)
   train,test=old.split_original(data)
   rec['train_count']=len(train);rec['heldout_count']=len(test)
   old_learned,n1=old.discover(train,old.learned_candidates(),UNARY_BUDGET)
   old_cold,n2=old.discover(train,old.candidate_order(),UNARY_BUDGET)
   expanded,n3=derive(train)
   # Shared budget for hybrid: 20 learned + up to 1000 novel +
   # remaining cold candidate budget. Scope: explicit switch overhead.
   picked=None
   if old_learned is not None:picked=('learned_prior',old_learned)
   elif expanded is not None:picked=('generated_two_bit',expanded)
   elif old_cold is not None:picked=('cold_fallback',old_cold)
   rec['arms']={
    'learned_old':{'correct':old.exact(old_learned,test),'submitted':old_learned is not None,'checks':n1},
    'strong_cold_unary':{'correct':old.exact(old_cold,test),'submitted':old_cold is not None,'checks':n2},
    'new_generated_boolean':{'correct':exact2(expanded,test),'submitted':expanded is not None,'checks':n3},
    'hybrid':{'correct': (old.exact(picked[1],test) if picked[0]!='generated_two_bit' else exact2(picked[1],test)) if picked else False,
              'submitted':picked is not None,'picked':picked[0] if picked else None,
              'checks':n1+(0 if old_learned is not None else n3)+(0 if old_learned is not None or expanded is not None else n2)}}
   rec['generated_boolean_ast']=expanded
   rec['learned_old_ast']=old_learned
   rec['cold_unary_ast']=old_cold
  except Exception as e:rec['error']=type(e).__name__+': '+str(e)[:160]
  rows.append(rec)
 out={'schema':'neumann.q3.two-bit-meta-representation-independent-original.v1',
      'source_git_blob':SOURCE_PRIOR_BLOB,'local_method_sha256':NEW_HUMAN_METHOD_SHA,
      'upstream':old.UPSTREAM_COMMIT,'task_ids':IDS,'rows':rows,
      'truth_table_precondition':'All four 2-input cells observed; both input roles causally relevant',
      'summary':{name:{'exact':sum(int(r.get('arms',{}).get(name,{}).get('correct',False)) for r in rows),
                       'submitted':sum(int(r.get('arms',{}).get(name,{}).get('submitted',False)) for r in rows),
                       'candidate_checks':sum(r.get('arms',{}).get(name,{}).get('checks',0) for r in rows)}
                 for name in ('learned_old','strong_cold_unary','new_generated_boolean','hybrid')},
      'wall_s':round(time.perf_counter()-st,3)}
 Path('Q3_BINARY_NEW_ORIGINAL_FIRST.json').write_text(json.dumps(out,indent=2))
 print(json.dumps({'task_count':len(IDS),'summary':out['summary'],'wall_s':out['wall_s']},indent=2))
 return out

if __name__=='__main__':run()
