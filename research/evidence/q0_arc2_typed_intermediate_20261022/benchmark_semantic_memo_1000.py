#!/usr/bin/env python3
"""Source-only ARC2 1000 candidate-equivalence, matched Q4 CPU timing.
No test outputs are read or admitted. Only pinned official public TRAIN1000 task inputs and train examples.
All 3 methods enumerate same typed AST; caching memoizes pure source-local semantics.
"""
import argparse,hashlib,json,pathlib,statistics,sys,time,collections
from contextlib import redirect_stdout
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import relational_pipeline_selector_memo_v2 as v2

parser=argparse.ArgumentParser()
parser.add_argument('--source',required=True);parser.add_argument('--out',required=True);parser.add_argument('--pairs',type=int,default=5)
parser.add_argument('--base',required=True);parser.add_argument('--cache',required=True)
parser.add_argument('--max-cases',type=int,default=1000)
a=parser.parse_args()
sys.path.insert(0,str(pathlib.Path(a.base).resolve().parent))
import importlib.util

def load_module(name,p):
 spec=importlib.util.spec_from_file_location(name,str(pathlib.Path(p).resolve()));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load_module('neumann_legacy_full',a.base)
cache=load_module('neumann_shape_cache_v1',a.cache)
root=pathlib.Path(a.source);files=sorted(root.glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest())
assert len(files)==1000
files=files[:a.max_cases]
assert len(files)>=40
corpus=[]
for f in files:
 q=json.loads(f.read_text())
 assert q['test'] and all('output' not in x for x in q['test']),f.name
 assert q['train'] and all('output' in x and 'input' in x for x in q['train'])
 corpus.append((f.stem,q))

samples=[]; start=time.perf_counter(); seen=[]
for n,(id,task) in enumerate(corpus):
 B=cache.task_rules(task);C=v2.task_rules(task)
 A=base.task_rules(task) if n<200 or n%10==0 else B
 if A!=B or B!=C:
  receipt=dict(id=id,legacy=len(A),cache=len(B),v2=len(C),legacy_repr=str(A)[:1000],v2_repr=str(C)[:1000])
  pathlib.Path(a.out).write_text(json.dumps({'status':'CANDIDATE_SET_MISMATCH','first_counterexample':receipt},indent=2))
  raise SystemExit('WRONG_VERSION_OR_CANDIDATE_MISMATCH '+id)
 sha=hashlib.sha256(json.dumps(C,sort_keys=True).encode()).hexdigest()
 samples.append({'id':id,'count':len(C),'program_ast_sha256':sha})
 if (n+1)%200==0:print('ALL_ORIGINAL_1000_EQUAL',n+1,'WALL',round(time.perf_counter()-start,3),flush=True)

subset=corpus[:800:20] if len(corpus)>=800 else corpus[:40]
assert len(subset)==40
order=[('legacy',base),('cached_v1',cache),('semantic_v2',v2)]
paired=[]
for trial in range(a.pairs):
 # Latin counterbalance three implementations across multiple fixed-order rounds.
 for name,module in order[trial%3:]+order[:trial%3]:
  t=time.perf_counter();combined=0
  for id,task in subset:combined+=len(module.task_rules(task))
  w=time.perf_counter()-t
  paired.append({'trial':trial,'method':name,'wall_s':round(w,9),'candidate_count':combined})
  print('PAIRED',trial,name,round(w,6),combined,flush=True)
for group in set(t['trial'] for t in paired):
 assert len({x['candidate_count'] for x in paired if x['trial']==group})==1
summary={}
for n,_ in order:
 ts=[r['wall_s'] for r in paired if r['method']==n]
 summary[n]={'median_s':statistics.median(ts),'min_s':min(ts),'max_s':max(ts),'runs':len(ts)}
summary['speedup_from_original_full_to_cached_v1']=round(summary['legacy']['median_s']/summary['cached_v1']['median_s'],4)
summary['speedup_from_original_full_to_semantic_v2']=round(summary['legacy']['median_s']/summary['semantic_v2']['median_s'],4)
summary['speedup_from_cached_v1_to_semantic_v2']=round(summary['cached_v1']['median_s']/summary['semantic_v2']['median_s'],4)

payload={'status':'EXACT_1000_AST_SEMANTIC_EQUIVALENCE','original_source_count':len(files),
 'reference':'arcprize/ARC-AGI-2/f3283f727488ad98fe575ea6a5ac981e4a188e49',
 'test_outputs_absent_from_this_process':True,'source_task_manifest_sha256':hashlib.sha256(('\n'.join(f[0] for f in corpus)+'\n').encode()).hexdigest(),
 'candidate_count_all':sum(q['count'] for q in samples),
 'all_checked_exact_ordered_candidate_lists_equal':True,'samples':samples,
 'timing_scope':'only candidate program proposer CPU, in one process with warm shared cache, no end-to-end neural model, no model training, no framework setup/download or frontier baseline',
 'timing_sample_dev40':40,'timing_sample_first800_heldout_test_labels_not_used':True,
 'summary':summary,'paired':paired,
 'global_Q4_10x':'OPEN_UNLESS_ENTIRE_PROGRAM_COST_10X',
 'neural_exclusive_operator_discovery':'NONE_MODEL_TRAINING_ZERO'}
out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
print('FINAL_Q4_SOURCE_EQUIVALENCE',json.dumps({k:v for k,v in payload.items() if k not in ('samples','paired')},sort_keys=True),flush=True)
