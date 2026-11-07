"""Q3 THIRD independent original cohort after source-frozen adaptive arity expansion.
Human-written universal k-bit truth-table VM and k<=3 search machinery.
Generated per-original AST and arity chosen from SOURCE examples only.
PRIOR runs PRE_100..147 never replaced; new PRE_148..171 not inspected.
"""
import hashlib
import itertools
import json
import pathlib
import time
import hard_original_unopened_method_gate as old

COHORT=[f'PRE_{i}_10' for i in range(148,172)]
LOCAL_UNIVERSAL_LEARNER_SHA='abf5256580d5483cba9b13e5110a79a04680f9a933d1ef448db99b4af047a441'
MAX_ARITY=3
INDEX_BOUND=2

def bit_eval(p,x):
 n=len(x);y=[]
 for i in range(n):
  key=0
  for d,fill in zip(p['offsets'],p['boundary_bits']):
   j=i+d
   key=(key<<1)|(x[j] if 0<=j<n else fill)
  y.append(p['truth_table'][key])
 return y

def valid(p,examples):
 return p is not None and all(bit_eval(p,x)==y for x,y in examples)

def sensitive(table,k):
 for j in range(k):
  d=1<<(k-j-1)
  if not any(table[i]!=table[i^d] for i in range(1<<k)):
   return False
 return True

def infer_at_k(pairs,k):
 if not pairs or len(pairs)<5 or any(not old.bits(x) or not old.bits(y) for x,y in pairs):
  return None,0
 ordered=sorted(range(-INDEX_BOUND,INDEX_BOUND+1),key=lambda x:(abs(x),x))
 checks=0
 for offsets in itertools.permutations(ordered,k):
  for fills in itertools.product((0,1),repeat=k):
   checks+=1
   table=[None]*(1<<k);conflict=False
   for x,y in pairs:
    n=len(x)
    for i,want in enumerate(y):
     cell=0
     for off,fill in zip(offsets,fills):
      j=i+off
      cell=(cell<<1)|(x[j] if 0<=j<n else fill)
     if table[cell] is None:table[cell]=want
     elif table[cell]!=want:conflict=True;break
    if conflict:break
   if conflict or any(z is None for z in table) or not sensitive(table,k):continue
   p={'kind':'LearnedIndexedTruthFunction','arity':k,'offsets':list(offsets),
      'boundary_bits':list(fills),'truth_table':table}
   if valid(p,pairs):return p,checks
 return None,checks

def self_expand(pairs):
 steps=[];total=0
 for k in range(1,MAX_ARITY+1):
  grammar={'production':'IndexedTruthTable','arity':k,
           'semantic_table_rows':1<<k,'index_bound':INDEX_BOUND}
  p,n=infer_at_k(pairs,k);total+=n
  steps.append({'new_grammar_production':grammar,'candidates_checked':n,
                'source_consistent':p is not None})
  if p is not None:return p,total,steps
 return None,total,steps

def run():
 start=time.perf_counter();rows=[]
 for tid in COHORT:
  z={'id':tid}
  try:
   data=old.fetch_original(tid)
   z['source_records']=len(data);z['source_sha256']=old.digest(data)
   train,heldout=old.split_original(data)
   z['train_n']=len(train);z['heldout_n']=len(heldout)
   known,n0=old.discover(train,old.learned_candidates(),500)
   cold,n1=old.discover(train,old.candidate_order(),500)
   fresh,total,steps=self_expand(train)
   z['methods']={
    'prior_learned':{'submitted':known is not None,'exact':old.exact(known,heldout),'checks':n0},
    'prior_strong_classical':{'submitted':cold is not None,'exact':old.exact(cold,heldout),'checks':n1},
    'self_expanding_arity':{'submitted':fresh is not None,'exact':valid(fresh,heldout),'checks':total,'program':fresh}
   }
   z['invention_transcript']=steps
  except Exception as e:z['error']=type(e).__name__+': '+str(e)[:180]
  rows.append(z)
 out={'schema':'neumann.q3.third-external-sygus-adaptive-arity-first.v1',
      'unseen_task_ids':COHORT,'source_universal_learner_sha256':LOCAL_UNIVERSAL_LEARNER_SHA,
      'upstream_commit':old.UPSTREAM_COMMIT,'max_arity':MAX_ARITY,
      'declared_interface':'64 input bits -> 64 output bits, 8 source pairs + 2 original heldout',
      'human_supplied':'arity 1..3, affine offsets [-2,2], truth table evaluator, search enumeration',
      'learned':'new grammar production arity, program offsets, branch boundaries, full truth table from source I/O',
      'rows':rows,
      'summary':{key:{'fully_exact':sum(int(r.get('methods',{}).get(key,{}).get('exact',False)) for r in rows),
                       'submitted':sum(int(r.get('methods',{}).get(key,{}).get('submitted',False)) for r in rows),
                       'checks':sum(r.get('methods',{}).get(key,{}).get('checks',0) for r in rows)}
                 for key in ('prior_learned','prior_strong_classical','self_expanding_arity')},
      'elapsed_s':round(time.perf_counter()-start,3)}
 pathlib.Path('Q3_ADAPTIVE_ARITY_EXTERNAL_FIRST.json').write_text(json.dumps(out,indent=2))
 print(json.dumps({'count':len(COHORT),'summary':out['summary'],'elapsed_s':out['elapsed_s']},indent=2))

if __name__=='__main__':run()
