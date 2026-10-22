#!/usr/bin/env python3
"""Train on demos only; freeze all test predictions before independent real scoring.
Uses PREDEFINED classical geometric features, not newly invented neural primitives.
"""
import argparse, collections, hashlib, json, pathlib, sys, time
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from capacity_probe import features, appended, certify

VARIANTS=((),('rowcol',),('components',),('rowcol','components'))
def make_features(grid,variant):
    x=features(grid)
    if not variant:return x
    r,c=appended(grid)
    return np.column_stack([x]+([r] if 'rowcol' in variant else [])+([c] if 'components' in variant else []))

def infer_one(d):
    demos=d['train']; tests=d['test']
    if not demos or any(np.shape(t['input'])!=np.shape(t['output']) for t in demos):
        return {'status':'ABSTAIN_SHAPE_CHANGE'}
    if sum(len(t['input'])*len(t['input'][0]) for t in demos)>3500:
        return {'status':'ABSTAIN_PIXEL_CAP'}
    y=np.concatenate([np.asarray(x['output'],dtype=np.int32).ravel() for x in demos])
    attempt=[]
    for vi,variant in enumerate(VARIANTS):
        xs=[make_features(x['input'],variant) for x in demos]
        x=np.concatenate(xs)
        proof=certify(x,y)
        if proof['conflicting_groups']:
            attempt.append({'variant':list(variant),'status':'UNFIT_INFORMATION_PROOF',
                            'collision_count':proof['conflicting_groups']})
            continue
        for depth in (1,2,3,4,5,6,8):
            m=DecisionTreeClassifier(max_depth=depth,min_samples_leaf=1,criterion='entropy',random_state=182)
            m.fit(x,y)
            if not np.array_equal(m.predict(x),y):continue
            passes=[]
            for k,demo in enumerate(demos):
                others=[z for j,z in enumerate(demos) if j!=k]
                if not others:passes.append(False);continue
                xx=np.concatenate([make_features(a['input'],variant) for a in others])
                yy=np.concatenate([np.asarray(a['output'],np.int32).ravel() for a in others])
                test=DecisionTreeClassifier(max_depth=depth,min_samples_leaf=1,criterion='entropy',random_state=182)
                test.fit(xx,yy)
                pred=test.predict(xs[k]).reshape(np.asarray(demo['output']).shape)
                passes.append(bool(np.array_equal(pred,np.asarray(demo['output']))))
            if not all(passes):
                attempt.append({'variant':list(variant),'status':'FAILED_LEAVE_DEMO_OUT',
                                'depth':depth,'cv_pass':sum(passes),'cv_n':len(passes)})
                break
            prediction=[m.predict(make_features(t['input'],variant))
                        .reshape(np.asarray(t['input']).shape).astype(int).tolist()
                        for t in tests]
            return {'status':'CV_ACCEPTED','variant':list(variant),'tree_depth':depth,
                    'crossdemo_n':len(demos),'prediction':prediction,'attempts':attempt}
    return {'status':'ABSTAIN_NO_CV_PROOF','attempts':attempt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['infer','grade'],required=True)
    p.add_argument('--masked-dir');p.add_argument('--pred');p.add_argument('--official-dir');p.add_argument('--out',required=True)
    a=p.parse_args();t0=time.perf_counter()
    if a.mode=='infer':
        files=sorted(pathlib.Path(a.masked_dir).glob('*.json'));assert len(files)==120
        results={}
        for f in files:
            task=json.loads(f.read_text())
            assert all('output' not in z for z in task['test']),f
            results[f.stem]=infer_one(task)
        d={'schema':'NEUMANN_Q3_Q4_PREDEFINED_RELATIONAL_SOURCE120.v1',
           'n':120,'official_test_labels_seen':False,
           'original_model_changed':False,'source_freeze':'f3283f727488ad98fe575ea6a5ac981e4a188e49',
           'status_counts':dict(collections.Counter(z['status'] for z in results.values())),
           'source_only_elapsed_s':time.perf_counter()-t0,'rows':results}
    else:
        d0=json.loads(pathlib.Path(a.pred).read_text())
        assert d0['n']==120 and not d0['official_test_labels_seen']
        files=sorted(pathlib.Path(a.official_dir).glob('*.json'));assert len(files)==120
        exact=[];attempted=[];per={}
        for f in files:
            t=json.loads(f.read_text());r=d0['rows'][f.stem]
            truth=[x['output'] for x in t['test']]
            if r['status']=='CV_ACCEPTED':
                attempted.append(f.stem)
                valid=len(truth)==len(r['prediction']) and all(p==q for p,q in zip(r['prediction'],truth))
                if valid:exact.append(f.stem)
                per[f.stem]={'status':'MATCH' if valid else 'WRONG','variant':r['variant']}
            else:per[f.stem]={'status':r['status']}
        d={'schema':'NEUMANN_Q3_Q4_ACTUAL_OFFICIAL120_EXACT_GRADE.v1',
           'n':120,'correct':len(exact),'attempted':len(attempted),
           'correct_ids':exact,'official_prior_frozen_learner_correct':0,
           'prior_source':'GitHub Actions 39761109427 official120 exact score',
           'claim':'scoped known public-evaluation source; NEVER globally pristine blind',
           'global_Q3_neural_novelty':'OPEN','global_Q4_10x':'OPEN',
           'pregrade_sha256':hashlib.sha256(pathlib.Path(a.pred).read_bytes()).hexdigest(),
           'rows':per}
    out=pathlib.Path(a.out);out.write_text(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n')
    print('SOURCE_ONLY_RESULT' if a.mode=='infer' else 'INDEPENDENT_120_REAL_SCORE',
          json.dumps(d.get('status_counts',{'correct':d.get('correct'),'attempted':d.get('attempted')}),sort_keys=True),
          'sha256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
