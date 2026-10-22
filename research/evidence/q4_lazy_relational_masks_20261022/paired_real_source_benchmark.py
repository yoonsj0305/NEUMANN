#!/usr/bin/env python3
"""Paired real original-input inference benchmark of unchanged eager vs exact lazy program."""
import argparse,hashlib,json,pathlib,statistics,time,sys,collections
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'q3_relational_edit_masks_20261022'),str(HERE)]
from infer_edit_rule import apply,geometries
from lazy_masks import run_lazy,audit_semantics,lazy_predicate

def main():
 p=argparse.ArgumentParser()
 for k in ('concept-inputs','arc-inputs','concept-pregrade','arc-pregrade','out'):p.add_argument('--'+k,required=True)
 p.add_argument('--trials',type=int,default=7);p.add_argument('--repetitions',type=int,default=20)
 a=p.parse_args()
 proofs=audit_semantics();source={}
 for name,pred_path,root,expected_sha in [
  ('conceptarc160',a.concept_pregrade,a.concept_inputs,'bec1fb20c1a65fcf52fc724555de5057417a9edd78fb1bb0991b4ab66b6737c2'),
  ('arc2train200',a.arc_pregrade,a.arc_inputs,'995cae3eca85918312d370ca4105842d0124af29108405faf6357c9409e47538')]:
    pre=pathlib.Path(pred_path);assert hashlib.sha256(pre.read_bytes()).hexdigest()==expected_sha
    rows=json.loads(pre.read_text())['rows']
    programs={uid:r for uid,r in rows.items() if r['status']=='INFERRED_RELATIONAL_EDIT_RULE'}
    assert len(programs)==(6 if name=='conceptarc160' else 5),name
    cases=[]
    for uid,r in sorted(programs.items()):
        f=pathlib.Path(root)/(uid+'.json')
        task=json.loads(f.read_text())
        assert all('output' not in q for q in task['test'])
        for demo in task['train']:
            original=apply(demo['input'],r['ast'])
            lazy=run_lazy(demo['input'],r['ast'])
            assert original is not None and np.array_equal(original,lazy)
            assert np.array_equal(original,np.asarray(demo['output']))
            cases.append((uid,'demo',demo['input'],r['ast']))
        for t in task['test']:
            eager=apply(t['input'],r['ast'])
            lazy=run_lazy(t['input'],r['ast'])
            assert eager is not None and np.array_equal(eager,lazy)
            cases.append((uid,'test',t['input'],r['ast']))
    source[name]={'programs':len(programs),'actual_masked_original_inputs':len(cases),'cases':cases}
 data=[]
 for kind,rec in source.items():
    cases=rec.pop('cases')
    observations=[]
    def run_mode(mode):
        total=0;t0=time.perf_counter_ns()
        for repeat in range(a.repetitions):
            for _,_,g,rule in cases:
                output=apply(g,rule) if mode=='eager' else run_lazy(g,rule)
                total+=int(output.ravel()[0])
        return (time.perf_counter_ns()-t0)/1e9,total
    run_mode('eager');run_mode('lazy')
    for trial in range(a.trials):
        order=['eager','lazy'] if trial%2==0 else ['lazy','eager']
        timed={}
        for mode in order:timed[mode]=run_mode(mode)
        assert timed['eager'][1]==timed['lazy'][1]
        observations.append({'trial':trial,'order':order,'eager_s':timed['eager'][0],
                             'lazy_s':timed['lazy'][0],
                             'exact_identical_checksum':timed['eager'][1]})
    e=statistics.median(v['eager_s'] for v in observations)
    l=statistics.median(v['lazy_s'] for v in observations)
    source[kind].update({'eager_median_s':e,'lazy_median_s':l,
           'median_paired_speedup':e/l,'trials':observations,
           'per_trial_repetitions':a.repetitions})
    print('EXACT_REAL_INPUT_LAZY_SPEED',kind,'programs',rec['programs'],
          'real_input_grids',len(cases),'repetitions',a.repetitions,
          'eager_median_s',round(e,6),'lazy_median_s',round(l,6),
          'ratio',round(e/l,4),flush=True)
 result={'schema':'NEUMANN_Q4_EXACT_MASK_AST_LAZY_EXECUTION_SCOPED.v1',
         'environment':'single dedicated GitHub Actions CPU runner per paired mode',
         'static_grammar_equivalence':proofs,'real_source_benchmarks':source,
         'statement':'same AST and source test predictions; only unnecessary boolean feature computation removed',
         'total_system_Q4_10x':'OPEN','training_optimization':'NOT_MEASURED',
         'physical_joules':'NOT_MEASURED','novel_learned_primitive':'NOT_ESTABLISHED'}
 path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('LAZY_EXECUTION_FINAL_RECEIPT_SHA256',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
