#!/usr/bin/env python3
"""CellARC: infer per-task CA rule abstractions solely from five original demonstrations.
Independent 2000 out-of-project episodes, no task metadata/rule table/solution at inference.
Exact finite table identity checks, not a neural model and not a new mathematical theorem.
"""
import argparse,collections,hashlib,json,pathlib,time

def win(xs,i,r):
    n=len(xs)
    return tuple(xs[(i+d)%n] for d in range(-r,r+1))

KINDS=('total','center_outer','center_total','center_counts','center','full')
def feature(w,kind):
    r=len(w)//2;c=w[r]
    if kind=='total':return (sum(w),)
    if kind=='center_outer':return (c,sum(w)-c)
    if kind=='center_total':return (c,sum(w))
    if kind=='center_counts':return (c,tuple(sorted(collections.Counter(w[:r]+w[r+1:]).items())))
    if kind=='center':return (c,)
    if kind=='full':return w
    raise ValueError(kind)

def attempt(d):
    begin=time.perf_counter();pairs=d['train'];query=d['query']
    if len(pairs)!=5 or not query or not all(isinstance(x,int) for x in query):
        return {'status':'UNSUPPORTED','prediction':None,'s':time.perf_counter()-begin}
    if any(len(p['input'])!=len(p['output']) or len(p['input'])!=len(query) or
       any(not isinstance(x,int) for x in p['input']+p['output']) for p in pairs):
        return {'status':'UNSUPPORTED','prediction':None,'s':time.perf_counter()-begin}
    valid=[];contradicted=0;unknown=0
    for r in (1,2,3):
        for kind in KINDS:
            table={};consistent=True
            for p in pairs:
                a=p['input'];b=p['output']
                for j,target in enumerate(b):
                    v=feature(win(a,j,r),kind)
                    if v in table and table[v]!=target:
                        consistent=False;break
                    table[v]=target
                if not consistent:break
            if not consistent:
                contradicted+=1;continue
            xs=[feature(win(query,j,r),kind) for j in range(len(query))]
            if any(k not in table for k in xs):
                unknown+=1;continue
            pred=[table[k] for k in xs]
            valid.append({'radius':r,'kind':kind,'predict':pred,'distinct_observations':len(table)})
    if not valid:return {'status':'ABSTAIN_NO_CERTIFIED_SOURCE_RULE','prediction':None,
                        'contradicted_hypotheses':contradicted,'unseen_hypotheses':unknown,
                        's':time.perf_counter()-begin}
    groups={}
    for x in valid:
        key=tuple(x['predict'])
        groups.setdefault(key,[]).append(x)
    if len(groups)!=1:
        return {'status':'ABSTAIN_CANDIDATES_DISAGREE','prediction':None,
                'hypotheses':len(valid),'semantic_classes':len(groups),
                's':time.perf_counter()-begin}
    chosen=min(valid,key=lambda x:(KINDS.index(x['kind']),x['radius']))
    return {'status':'SOURCE_CONSENSUS','prediction':chosen['predict'],'radius':chosen['radius'],
            'kind':chosen['kind'],'hypotheses':len(valid),'tested_source_rules':18,
            's':time.perf_counter()-begin}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['predict','grade'],required=True)
    p.add_argument('--input-dir');p.add_argument('--prediction-dir');p.add_argument('--source-dir');p.add_argument('--out',required=True)
    a=p.parse_args();begin=time.perf_counter()
    if a.mode=='predict':
        allrows={};summary={}
        for split in ('test_interpolation','test_extrapolation'):
            source=pathlib.Path(a.input_dir)/(split+'.jsonl')
            assert source.exists(),source
            rows={};start=time.perf_counter()
            with source.open() as stream:
                for index,line in enumerate(stream):
                    d=json.loads(line)
                    assert 'solution' not in d and 'meta' not in d and 'program' not in d
                    assert len(d['train'])==5 and 'query' in d
                    key=d['id'];assert key not in rows
                    rows[key]=attempt(d)
            assert len(rows)==1000,(split,len(rows))
            allrows[split]=rows
            summary[split]={'n':1000,'s':time.perf_counter()-start,
                            'status':dict(collections.Counter(v['status'] for v in rows.values()))}
            print('SEALED_CELLARC_SOURCE_ONLY',split,json.dumps(summary[split],sort_keys=True),flush=True)
        data={'schema':'NEUMANN_CELLARC2000_RULE_INFORMATION_CERTIFICATE.v1',
              'n':2000,'public_source_test_solutions_read':False,'meta_accessed':False,
              'no_neural_training':True,'known_math':'finite local CA windows information identifiability',
              'overall_s':time.perf_counter()-begin,'summary':summary,'rows':allrows}
    else:
        beforefile=pathlib.Path(a.prediction_dir);before=json.loads(beforefile.read_text())
        assert before['n']==2000 and not before['public_source_test_solutions_read']
        totals={};detail={}
        for split in ('test_interpolation','test_extrapolation'):
            original=pathlib.Path(a.source_dir)/(split+'.jsonl')
            correct=0;attempted=0;wrong=0;bykind=collections.Counter()
            with original.open() as stream:
                for line in stream:
                    d=json.loads(line)
                    assert 'solution' in d
                    r=before['rows'][split][d['id']]
                    has=r['prediction'] is not None
                    ok=bool(has and r['prediction']==d['solution'])
                    attempted+=int(has);correct+=int(ok);wrong+=int(has and not ok)
                    if has:bykind[r['kind']+(':OK' if ok else ':WRONG')]+=1
                    detail[d['id']]={'split':split,'status':r['status'],'correct':ok}
            assert len([v for v in detail.values() if v['split']==split])==1000
            totals[split]={'n':1000,'correct':correct,'attempted':attempted,'wrong':wrong,
                           'status_by_kind':dict(bykind)}
            print('INDEPENDENT_ORIGINAL_CELLARC2000',split,json.dumps(totals[split],sort_keys=True),flush=True)
        data={'schema':'NEUMANN_CELLARC2000_SEALED_INDEPENDENT_EXACT_SCORE.v1','n':2000,
              'independent_original_scores':totals,'rows':detail,
              'pregrade_sha256':hashlib.sha256(beforefile.read_bytes()).hexdigest(),
              'global_Q3_learned_exclusive':'OPEN','global_Q4_10x':'OPEN',
              'accuracy_condition':'original exact CA query states only, abstentions count as wrong'}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,separators=(',',':'),sort_keys=True)+'\n')
    print('INDEPENDENT_EVIDENCE_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
