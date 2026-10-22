#!/usr/bin/env python3
"""ConceptARC 160 authentic independently-authored tasks; frozen solver no eval targets."""
import argparse,collections,hashlib,json,pathlib,sys,time
SRC=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parent/'q3_object_synthesis_transfer_20261022'))
from object_relational_proposer import solve

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['predict','grade'],required=True)
 p.add_argument('--masked');p.add_argument('--source');p.add_argument('--sealed');p.add_argument('--out',required=True)
 a=p.parse_args();t=time.perf_counter()
 if a.mode=='predict':
    paths=sorted(pathlib.Path(a.masked).glob('*.json'))
    assert len(paths)==160
    rows={}
    for f in paths:
        d=json.loads(f.read_text());assert len(d['test'])==3 and all('output' not in x for x in d['test'])
        try:r=solve(d)
        except Exception as e:r={'status':'ERROR','prediction':None,'error':type(e).__name__+': '+str(e)[:200]}
        rows[f.stem]=r
    d={'schema':'NEUMANN_CONCEPTARC160_OBJECT_PROGRAM_PRE_GRADE.v1','n':160,
       'test_truth_seen':False,'rows':rows,
       'counts':dict(collections.Counter(x['status'] for x in rows.values())),
       'elapsed_s':time.perf_counter()-t}
    print('SOURCE_ONLY_CONCEPTARC_160',json.dumps(d['counts'],sort_keys=True),flush=True)
 else:
    s=pathlib.Path(a.sealed);before=json.loads(s.read_text())
    assert before['n']==160 and before['test_truth_seen'] is False
    groups=sorted(x for x in pathlib.Path(a.source).iterdir() if x.is_dir());assert len(groups)==16
    count=collections.Counter();rows={}
    for group in groups:
        paths=sorted(group.glob('*.json'));assert len(paths)==10
        for f in paths:
            uid=group.name+'__'+f.stem;d=json.loads(f.read_text());row=before['rows'][uid]
            output=[x['output'] for x in d['test']];pred=row['prediction']
            exact=bool(pred is not None and len(pred)==len(output) and all(a==b for a,b in zip(pred,output)))
            count['correct']+=int(exact);count['attempted']+=int(pred is not None)
            count[row['status']]+=1
            if row['status']=='NEW_RELATIONAL_PROGRAM':
                count['new_program_correct']+=int(exact)
                if exact:
                    enc=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
                    print('NEW_EXTERNAL_AUTHOR_EXACT',json.dumps({'uid':uid,'ast':row.get('ast'),
                          'predicted_sha256':hashlib.sha256(enc(pred)).hexdigest(),
                          'independent_truth_sha256':hashlib.sha256(enc(output)).hexdigest()},sort_keys=True),flush=True)
            rows[uid]={'correct':exact,'status':row['status']}
    d={'schema':'NEUMANN_CONCEPTARC160_OBJECT_PROGRAM_EXACT_INDEPENDENT_GRADE.v1',
       'n':160,'test_grids':480,'counts':dict(count),'rows':rows,
       'pregrade_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),
       'historical_prior_baseline_correct':6,'historical_prior_evidence':'GitHub PR468',
       'pristine_new_blind':False,'global_neural_exclusive_Q3':'OPEN','global_Q4_10x':'OPEN'}
    print('ORIGINAL_CONCEPTARC160_INDEPENDENT_EXACT',json.dumps(d['counts'],sort_keys=True),flush=True)
 out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
 out.write_text(json.dumps(d,sort_keys=True)+'\n')
 print('CONCEPTARC160_EVIDENCE_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
