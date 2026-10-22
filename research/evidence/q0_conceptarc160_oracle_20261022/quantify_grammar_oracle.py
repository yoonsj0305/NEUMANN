#!/usr/bin/env python3
"""Postgrade only: decompose fixed ConceptARC source DSL into representation/selection bottlenecks."""
import argparse,collections,hashlib,json,pathlib,sys,time

def canonical(a): return json.dumps(a,sort_keys=True,separators=(',',':'))

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--mode',choices=['propose','grade'],required=True)
 p.add_argument('--masked');p.add_argument('--original');p.add_argument('--pred');p.add_argument('--out',required=True)
 a=p.parse_args();out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 if a.mode=='propose':
  assert a.masked and not a.pred and not a.original
  sys.path.insert(0,str(pathlib.Path('research/evidence/q0_arc2_typed_intermediate_20261022').resolve()))
  from relational_pipeline_selector_memo_v2 import task_rules,predict,complexity
  files=sorted(pathlib.Path(a.masked).glob('*.json'));assert len(files)==160
  rows=[];start=time.perf_counter()
  for fn in files:
   t=json.loads(fn.read_text());assert len(t['test'])==3 and all('output' not in r for r in t['test'])
   rules=task_rules(t);unique={}
   for rule in rules:
    pred=predict(t,rule)
    if pred is None:continue
    key=canonical(pred);rec=unique.setdefault(key,{'output':pred,'ast_count':0,'mdl':None,'ast':None})
    rec['ast_count']+=1;cost=list(complexity(rule))
    if rec['mdl'] is None or tuple(cost)<tuple(rec['mdl']):rec['mdl']=cost;rec['ast']=rule
   classes=sorted(unique.values(),key=lambda r:tuple(r['mdl']))
   vote=sorted(unique.values(),key=lambda r:(-r['ast_count'],tuple(r['mdl'])))
   rows.append({'id':fn.stem,'ast_count':len(rules),'behavior_count':len(classes),
                'classes':classes,'mdlpred':classes[0]['output'] if classes else None,
                'votepred':vote[0]['output'] if vote else None})
   if len(rows)%40==0:print('PREGRADE',len(rows),flush=True)
  res={'schema':'NEUMANN_Q0_CONCEPTARC160_CANDIDATES_FROZEN_V1','n':160,'rows':rows,
       'labels_seen':False,'neural_training':False,
       'grammar_sha':'a46dc5480f0819895effc48df1e0600a23640bdf',
       'wall_s':time.perf_counter()-start}
  out.write_text(json.dumps(res,sort_keys=True,separators=(',',':'))+'\n')
  print('IMMUTABLE_PREGRADE_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
 else:
  assert a.original and a.pred and not a.masked
  raw=pathlib.Path(a.pred).read_bytes();src=json.loads(raw)
  assert src['n']==160 and not src['labels_seen'] and not src['neural_training']
  counts=collections.Counter();categories=collections.defaultdict(collections.Counter);rows=[]
  for rec in src['rows']:
   group,name=rec['id'].split('__',1)
   d=json.loads((pathlib.Path(a.original)/group/(name+'.json')).read_text())
   truth=[x['output'] for x in d['test']];assert len(truth)==3
   hits=[i for i,v in enumerate(rec['classes']) if v['output']==truth]
   covered=rec['ast_count']>0;oracle=bool(hits);mdl=rec['mdlpred']==truth;vote=rec['votepred']==truth
   assert not mdl or oracle
   fields={'total':1,'covered':int(covered),'uncovered':int(not covered),
           'exact_oracle':int(oracle),'mdl_correct':int(mdl),'vote_correct':int(vote),
           'ambiguous_behavior':int(rec['behavior_count']>1),
           'singleton_behavior_wrong':int(rec['behavior_count']==1 and not mdl),
           'oracle_correct_but_mdl_wrong':int(oracle and not mdl)}
   counts.update(fields);categories[group].update(fields)
   rows.append({'id':rec['id'],'category':group,'ast_count':rec['ast_count'],
                'behavior_classes':rec['behavior_count'],'oracle_exact':oracle,
                'oracle_correct_programs':len(hits),'mdl_correct':mdl,'vote_correct':vote})
  assert counts['total']==160 and len(categories)==16 and counts['covered']+counts['uncovered']==160
  result={'schema':'NEUMANN_Q0_CONCEPTARC160_POSTGRADE_GRAMMAR_ORACLE_V1',
          'source_prediction_sha256':hashlib.sha256(raw).hexdigest(),
          'scope':'Previously evaluated ConceptARC160; fixed demo-consistent AST only; not frontier or learned-exclusive',
          'counts':dict(counts),'group_counts':{k:dict(v) for k,v in categories.items()},'rows':rows,
          'source_corpus_new_to_prior_corpus_campaign':True,'firstblind_after_grading':False}
  out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  print('ORIGINAL160_POSTGRADE_ORACLE',json.dumps(result['counts'],sort_keys=True),flush=True)

if __name__=='__main__': main()
