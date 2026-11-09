"""Q3 source-frozen external SyGuS-SGI-1 64-bit cohort, ALL preselected IDs.

External task names are metadata-selected, not chosen by source outcomes. No .sl,
reference solution or output read before method is frozen. Published I/O first
N-2 examples for fitting, last 2 hash-sorted for heldout. Model class is
limited to single affine input-bit coordinate + XOR polarity + boundary bit.
"""
import hashlib
import itertools
import json
import pathlib
import time
import urllib.request

SOURCE_SHA='8cab168dcbb901fa21c75cdff382420a08aaac45f874dc6c2e3b0c9ee029efa3'
METHOD_SHA='b46954f23503d4ed992cf9998bb9cefe80838affa2fc2e6fe9cd4f3b27415c55'
UPSTREAM_COMMIT='e7ae840e5546e9243ff94afb1a29064fc050011c'
TASK_NAMES=[f'PRE_{i}_10' for i in range(100,124)]
BUDGET=500

METHOD={'kind': 'ExecutableLearnedBitMethod', 'template': {'boundary': {'hole': 1}, 'coefficients': [1, 0, {'hole': 2}], 'invert': {'hole': 3}, 'kind': 'GeneratedBitRelation'}, 'hole_options': [[1, [0, 1]], [2, [0, -1, -2, 1, 2]], [3, [0, 1]]], 'source_program_digests': ['99e5474a4db950209b32b441612d9b22044712b0a728994d8c5a8961944c5a4e', '4c568bd9ab9072ebec7d85a7288fb9c4566b2d43c02af4c2de076efcad394975', 'ff214f27f959651c5c9bb349c5c9d3dea6ed3c5820cfac3470859a648545d83c']}

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def bits(x):return type(x) is list and len(x)==64 and all(type(y) is int and y in (0,1) for y in x)

def evaluate(p,x):
 a,b,c=p['coefficients']; invert=p['invert'];boundary=p['boundary'];n=len(x)
 return [(x[a*i+b*n+c]^invert) if 0<=a*i+b*n+c<n else boundary for i in range(n)]

def exact(p,examples):
 return p is not None and all(evaluate(p,x)==y for x,y in examples)

def candidate_order():
 coords=list(itertools.product(range(-2,3),repeat=3))
 coords.sort(key=lambda t:(sum(map(abs,t)),t!=(1,0,0),t))
 for a,b,c in coords:
  for invert in (0,1):
   for boundary in (0,1):
    yield {'kind':'GeneratedBitRelation','coefficients':[a,b,c],
           'invert':invert,'boundary':boundary}

def fill(node,d):
 if isinstance(node,dict):
  if set(node)=={'hole'}:return d[node['hole']]
  return {k:fill(x,d) for k,x in node.items()}
 if isinstance(node,list):return [fill(x,d) for x in node]
 return node

def learned_candidates():
 meth=METHOD
 for vs in itertools.product(*(v for _,v in meth['hole_options'])):
  d={name:val for (name,_),val in zip(meth['hole_options'],vs)}
  yield fill(meth['template'],d)

def discover(examples,candidates,budget):
 count=0
 for p in candidates:
  if count>=budget:break
  count+=1
  if exact(p,examples):return p,count
 return None,count

def fetch_original(ident):
 u=(f'https://raw.githubusercontent.com/Barnard-PL-Labs/sygus-sgi-1/{UPSTREAM_COMMIT}'
    f'/data/benchmarks/hard/{ident}/examples.json')
 with urllib.request.urlopen(u,timeout=25) as h:
  raw=h.read(1000001)
 if len(raw)>1000000:raise ValueError('DOWNLOAD_LIMIT')
 return json.loads(raw)

def split_original(blob):
 if not isinstance(blob,list):raise ValueError('NOT_LIST')
 records=[];seen=set()
 for item in blob:
  if not isinstance(item,dict):raise ValueError('BAD_RECORD')
  x,y=item.get('input'),item.get('output')
  if not bits(x) or not bits(y):raise ValueError('BAD_BIT_SHAPE')
  k=tuple(x)
  if k in seen:continue
  seen.add(k);records.append((x,y))
 records.sort(key=lambda t:hashlib.sha256(canon(t[0]).encode()).hexdigest())
 if len(records)<6:raise ValueError('FEW_DISTINCT_PAIRS')
 return records[:-2],records[-2:]

def run():
 start=time.perf_counter()
 out={'schema':'neumann.q3.source-frozen-sygus-sgi-1-hard-2026-11-07.v1',
      'source_method_sha256':METHOD_SHA,'source_learner_sha256':SOURCE_SHA,
      'upstream_commit':UPSTREAM_COMMIT,'policy':'first 24 lexicographic _10 tasks from PRE_100 through PRE_123',
      'task_count':len(TASK_NAMES),'candidate_budget':BUDGET,'rows':[]}
 for ident in TASK_NAMES:
  t=time.perf_counter();r={'id':ident}
  try:
   data=fetch_original(ident);r['published_count']=len(data);r['source_data_sha256']=digest(data)
   train,test=split_original(data)
   r['train_count']=len(train);r['heldout_count']=len(test)
   preds={}
   for name,gen in [('learned_method',learned_candidates()),
                    ('strong_cold',candidate_order())]:
    t0=time.perf_counter()
    prog,tries=discover(train,gen,BUDGET)
    preds[name]={'submitted':prog is not None,'train_exact':exact(prog,train),
                 'original_heldout_exact':exact(prog,test),'candidate_checks':tries,
                 'discover_ms':round((time.perf_counter()-t0)*1000,5),
                 'program':prog}
   r['predictions']=preds
  except Exception as e:
   r['error']=type(e).__name__+': '+str(e)[:160]
  r['elapsed_s']=round(time.perf_counter()-t,5)
  out['rows'].append(r)
 out['summary']={name:{'exact_tasks':sum(bool(r.get('predictions',{}).get(name,{}).get('original_heldout_exact')) for r in out['rows']),
                       'submitted_tasks':sum(bool(r.get('predictions',{}).get(name,{}).get('submitted')) for r in out['rows']),
                       'candidate_checks':sum(r.get('predictions',{}).get(name,{}).get('candidate_checks',0) for r in out['rows'])}
                 for name in ('learned_method','strong_cold')}
 out['elapsed_s']=round(time.perf_counter()-start,3)
 return out

if __name__=='__main__':
 result=run()
 pathlib.Path('Q3_HARD_EXTERNAL_FIRST.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k in ('task_count','summary','elapsed_s')},indent=2))
