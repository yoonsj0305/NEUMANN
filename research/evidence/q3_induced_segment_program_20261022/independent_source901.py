#!/usr/bin/env python3
"""Original external 1D-ARC901: source-only induced programs vs previous frozen model.
Separate grader cannot run in source inference; no evaluation targets read in inference.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'q3_object_synthesis_transfer_20261022'))
sys.path.insert(0,str(P.parent/'q3_external_1d900_20261022'))
from object_relational_proposer import solve as frozen_old
from external_1d900 import adapt_task,original_files
from induced_rewrite import run as induced

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--mode',choices=['infer','grade'],required=True)
    a.add_argument('--masked');a.add_argument('--original');a.add_argument('--sealed');a.add_argument('--out',required=True)
    args=a.parse_args();start=time.perf_counter()
    if args.mode=='infer':
        files=sorted(pathlib.Path(args.masked).glob('*.json'))
        assert len(files)==901
        rows={};trials=collections.Counter()
        for idx,f in enumerate(files):
            task=json.loads(f.read_text())
            assert all('output' not in item for item in task['test']),f.stem
            prior=frozen_old(task);trials[prior['status']]+=1
            if prior.get('prediction') is not None:
                extra={'status':'SKIPPED_EXISTING_PREDICTION','prediction':None,'total_s':0}
            else:
                extra=induced(task)
            trials[extra['status']]+=1
            rows[f.stem]={'prior':prior,'induced':extra,
                          'fallback_prediction':prior.get('prediction') if prior.get('prediction') is not None else extra.get('prediction'),
                          'fallback_route':'FROZEN_CLASSICAL_FIRST' if prior.get('prediction') is not None else extra['status']}
            if (idx+1)%150==0:print('RUN_1D',idx+1,dict(trials),flush=True)
        d={'schema':'NEUMANN_Q3_INDUCED_SEQUENCE_RULES_FIRST_FIXED_901.v1','n':901,
           'source_git_pin':'1e74dc4cb4c58d8160e1fbd0ba638eb745f37147',
           'test_truth_seen':False,'rows':rows,'status_counts':dict(trials),'source_only_wall_s':time.perf_counter()-start,
           'neural_forward_count':0,'training_method':'task-local symbolic rule and parameter induction from demos',
           'model_generated_primitive_claim':False}
        print('SOURCE_ONLY_901_INDUCED',json.dumps(d['status_counts'],sort_keys=True),'wall_s',d['source_only_wall_s'],flush=True)
    else:
        before_file=pathlib.Path(args.sealed);p=json.loads(before_file.read_text())
        assert p['n']==901 and p['test_truth_seen'] is False and len(p['rows'])==901
        records=original_files(pathlib.Path(args.original));assert len(records)==901
        totals=collections.Counter();groups={};rows={}
        for uid,file in records:
            r=p['rows'][uid];task=adapt_task(json.loads(file.read_text()),True)
            target=[x['output'] for x in task['test']]
            def exact(q):return q is not None and len(q)==len(target) and all(x==y for x,y in zip(q,target))
            old=bool(exact(r['prior'].get('prediction')))
            new=bool(exact(r['induced'].get('prediction')))
            fallback=bool(exact(r['fallback_prediction']))
            totals['old_correct']+=int(old)
            totals['old_attempted']+=int(r['prior'].get('prediction') is not None)
            totals['new_correct']+=int(new)
            totals['new_attempted']+=int(r['induced'].get('prediction') is not None)
            totals['fallback_correct']+=int(fallback)
            totals['fallback_attempted']+=int(r['fallback_prediction'] is not None)
            totals['new_unique_correct']+=int(new and not old)
            totals['wrong_fallback']+=int(r['fallback_prediction'] is not None and not fallback)
            group=file.parent.name
            e=groups.setdefault(group,{'n':0,'old_correct':0,'new_correct':0,'fallback_correct':0})
            e['n']+=1;e['old_correct']+=int(old);e['new_correct']+=int(new);e['fallback_correct']+=int(fallback)
            if new and not old:
                print('FIRST_REAL_NEW_INDUCED',json.dumps({'original_id':uid,
                     'kind':r['induced'].get('induced_kind'),'parameter':r['induced'].get('induced_parameter')},sort_keys=True),flush=True)
            rows[uid]={'old_exact':old,'induced_exact':new,'fallback_exact':fallback,
                       'prior_status':r['prior']['status'],'new_status':r['induced']['status']}
        d={'schema':'NEUMANN_Q3_ORIGINAL901_INDUCED_RULES_INDEPENDENT_TRUTH.v1',
           'n':901,'totals':dict(totals),'per_category':groups,'rows':rows,
           'source_only_receipt_sha256':hashlib.sha256(before_file.read_bytes()).hexdigest(),
           'preexisting_original_1d901_first_score':99,
           'prior_direct_same_source_recomputed':True,
           'neural_exclusive_operator_discovery':'NOT_PROVED','global_q4_total10x':'OPEN',
           'original_family_previously_publicly_tested_in_project':True}
        print('INDEPENDENT_901_REAL_INDUCED_SCORE',json.dumps(d['totals'],sort_keys=True),flush=True)
        print('SOURCE_901_INDUCED_BY_FAMILY',json.dumps(groups,sort_keys=True),flush=True)
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(d,separators=(',',':'),sort_keys=True)+'\n')
    print('RECEIPT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
