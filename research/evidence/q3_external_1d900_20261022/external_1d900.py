#!/usr/bin/env python3
"""Original public 1D-ARC, 18 categories x 50 tasks. Algorithm completely frozen.
One-time external-author transfer: source-only inference; grade isolated only AFTER sealed prediction.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'q3_object_synthesis_transfer_20261022'))
from object_relational_proposer import solve

def as_grid(x):
    if not isinstance(x,list) or not x:raise ValueError('bad grid')
    if all(isinstance(v,int) for v in x):return [x]
    if all(isinstance(v,list) and len(v)>0 and all(isinstance(q,int) for q in v) for v in x):
        return x
    raise ValueError('unsupported grid')

def adapt_task(d,truth_allowed):
    train=[{'input':as_grid(z['input']),'output':as_grid(z['output'])} for z in d['train']]
    test=[{'input':as_grid(z['input']),**({'output':as_grid(z['output'])} if truth_allowed else {})} for z in d['test']]
    assert train and test
    return {'train':train,'test':test}

def original_files(root):
    folders=sorted(x for x in root.iterdir() if x.is_dir())
    assert len(folders)==18,('original category count',len(folders))
    records=[]
    for folder in folders:
        files=sorted(folder.glob('*.json'))
        assert len(files)==(51 if folder.name=='1d_scale_dp' else 50),(folder,len(files))
        for f in files: records.append((folder.name+'__'+f.stem,f))
    assert len(records)==901 and len({id for id,_ in records})==901
    return records

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['prepare','infer','grade'],required=True)
    p.add_argument('--source');p.add_argument('--masked');p.add_argument('--sealed');p.add_argument('--metadata')
    p.add_argument('--out',required=True);a=p.parse_args();start=time.perf_counter()
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    if a.mode=='prepare':
        fs=original_files(pathlib.Path(a.source))
        masked=pathlib.Path(a.masked);assert not masked.exists();masked.mkdir(parents=True)
        metadata={'schema':'SOURCE_1D_ARC_901_ORIGINAL_PINNED.v1','n':901,'groups':sorted({f.parent.name for _,f in fs}),'rows':[]}
        for uid,f in fs:
            d=adapt_task(json.loads(f.read_text()),False)
            assert all('output' not in x for x in d['test'])
            (masked/(uid+'.json')).write_text(json.dumps(d,separators=(',',':'))+'\n')
            metadata['rows'].append({'uid':uid,'relative_source':str(f.relative_to(a.source))})
        out.write_text(json.dumps(metadata,sort_keys=True)+'\n')
        print('SOURCE_901_TEST_LABELS_REMOVED',len(metadata['rows']),flush=True)
    elif a.mode=='infer':
        fs=sorted(pathlib.Path(a.masked).glob('*.json'));assert len(fs)==901
        rows={}
        for i,f in enumerate(fs):
            d=json.loads(f.read_text());assert all('output' not in z for z in d['test'])
            try:r=solve(d)
            except Exception as err:r={'status':'ERROR','prediction':None,'error':type(err).__name__+': '+str(err)[:200]}
            rows[f.stem]=r
            if (i+1)%150==0:print('SOURCE_ONLY_1D_PROGRESS',i+1,dict(collections.Counter(x['status'] for x in rows.values())),flush=True)
        payload={'schema':'NEUMANN_UNCHANGED_1D_ARC901_PRE_GRADE.v1','n':901,'test_truth_seen':False,
                 'source_repo':'khalil-research/1D-ARC','git_commit':'1e74dc4cb4c58d8160e1fbd0ba638eb745f37147',
                 'status_counts':dict(collections.Counter(x['status'] for x in rows.values())),'rows':rows,
                 'elapsed_s':time.perf_counter()-start}
        out.write_text(json.dumps(payload,sort_keys=True)+'\n')
        print('SOURCE_1D_900_PRE_GRADE',json.dumps(payload['status_counts'],sort_keys=True),flush=True)
    else:
        sealed=pathlib.Path(a.sealed);before=json.loads(sealed.read_text())
        assert before['n']==901 and before['test_truth_seen'] is False
        fs=original_files(pathlib.Path(a.source));assert len(fs)==901
        results={};totals=collections.Counter();group_counts={}
        for uid,f in fs:
            original=adapt_task(json.loads(f.read_text()),True)
            expectation=[z['output'] for z in original['test']]
            r=before['rows'][uid];pred=r['prediction']
            correct=bool(pred is not None and len(pred)==len(expectation) and all(x==y for x,y in zip(pred,expectation)))
            totals['correct']+=int(correct);totals['attempted']+=int(pred is not None)
            totals[r['status']]+=1;totals['new_relational_correct']+=int(correct and r['status']=='NEW_RELATIONAL_PROGRAM')
            g=f.parent.name;group_counts.setdefault(g,{'n':0,'correct':0,'attempted':0})
            group_counts[g]['n']+=1;group_counts[g]['correct']+=int(correct);group_counts[g]['attempted']+=int(pred is not None)
            results[uid]={'status':r['status'],'exact_correct':correct}
        report={'schema':'NEUMANN_FRESH_1D_ARC901_INDEPENDENT_EXACT_ORIGINAL.v1',
          'n':901,'totals':dict(totals),'groups':group_counts,'rows':results,
          'sealed_pregrade_sha256':hashlib.sha256(sealed.read_bytes()).hexdigest(),
          'first_run_code_frozen_before_dataset_task_body_exposure':True,
          'not_comparable_to_2d_arc2_frontier_accuracy':True,'global_neural_operator_novelty':'OPEN',
          'global_cost_10x':'OPEN'}
        out.write_text(json.dumps(report,sort_keys=True)+'\n')
        print('REAL_1D_ARC900_INDEPENDENT_SCORE',json.dumps(report['totals'],sort_keys=True),flush=True)
        print('REAL_1D_ARC900_GROUPS',json.dumps(group_counts,sort_keys=True),flush=True)
    print('OUTPUT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
