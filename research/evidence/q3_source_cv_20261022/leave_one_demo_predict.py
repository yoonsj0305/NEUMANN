#!/usr/bin/env python3
"""Leave-one-whole-demonstration-out: no withheld demo labels given to rule inducer.

Real original public task test outputs always stripped. Predict each left-out demo
before separate grader reads its original output.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'q3_relational_edit_masks_20261022'))
from infer_edit_rule import discover,apply

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--masked-root',required=True);p.add_argument('--concept-pregrade',required=True)
 p.add_argument('--arc-pregrade',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 cohorts=[
   ('conceptarc160',a.concept_pregrade,'bec1fb20c1a65fcf52fc724555de5057417a9edd78fb1bb0991b4ab66b6737c2',6),
   ('arc2train200',a.arc_pregrade,'995cae3eca85918312d370ca4105842d0124af29108405faf6357c9409e47538',5)]
 begin=time.perf_counter();rows={}
 for cohort,file,sha_expected,n_cases in cohorts:
    p=pathlib.Path(file);assert hashlib.sha256(p.read_bytes()).hexdigest()==sha_expected
    original=json.loads(p.read_text())['rows']
    cases={uid:r for uid,r in original.items() if r['status']=='INFERRED_RELATIONAL_EDIT_RULE'}
    assert len(cases)==n_cases
    out={}
    for uid,row in sorted(cases.items()):
        task=json.loads((pathlib.Path(a.masked_root)/cohort/(uid+'.json')).read_text())
        assert all('output' not in q for q in task['test'])
        demos=task['train']
        folds=[]
        for ix in range(len(demos)):
            others=[d for j,d in enumerate(demos) if j!=ix]
            # Only source input survives on the held-out side of this fold.
            test_source={'input':demos[ix]['input']}
            ast,stats=discover(others)
            if ast is None:
                folds.append({'fold':ix,'eligible':len(others)>=2,'status':'ABSTAIN',
                              'reason':stats['reason'],'prediction':None})
            else:
                try:
                    got=apply(test_source['input'],ast)
                    prediction=got.tolist() if got is not None else None
                except Exception:prediction=None
                folds.append({'fold':ix,'eligible':len(others)>=2,
                              'status':'PREDICTED' if prediction is not None else 'INAPPLICABLE',
                              'prediction':prediction,'ast':ast})
        out[uid]={'source_demos':len(demos),'folds':folds}
        print('SOURCE_ONLY_LOODO',cohort,uid,'n',len(demos),
              'predictions',sum(f['prediction'] is not None for f in folds),flush=True)
    rows[cohort]=out
 result={'schema':'NEUMANN_Q3_LEAVE_ONE_WHOLE_ORIGINAL_DEMO_OUT_PRE_GRADE.v1',
     'source_target_test_outputs_seen':False,'leftout_original_demo_outputs_given_to_trainer':False,
     'counts':{'conceptarc160':6,'arc2train200':5},'rows':rows,
     'source_only_wall_s':time.perf_counter()-begin,
     'global_unique_neural_Q3':'OPEN'}
 target=pathlib.Path(a.out);target.parent.mkdir(exist_ok=True,parents=True)
 target.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
 print('ALL11_FROZEN_DEMO_HOLDOUTS_SHA256',hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
