#!/usr/bin/env python3
"""POSTGRADE provenance: source-independent exact semantic ARC1,ARC2,ConceptARC duplicates.
Never participates in inference or selector tuning; no semantic-concept-family guarantee.
"""
import argparse,collections,hashlib,json,pathlib

def canonical(task):
    def row(x):return json.dumps(x,separators=(',',':'),sort_keys=True)
    demos=sorted(row(x) for x in task['train'])
    tests=sorted(row(x) for x in task['test'])
    a=hashlib.sha256(('\n'.join(demos)+'\n').encode()).hexdigest()
    b=hashlib.sha256(('\n'.join(demos)+'\n---TESTS---\n'+'\n'.join(tests)+'\n').encode()).hexdigest()
    return a,b

def main():
    p=argparse.ArgumentParser();p.add_argument('--conceptarc',required=True);p.add_argument('--arc1',required=True);p.add_argument('--arc2',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    src={}
    for group,paths in {
       'arc1_training':list(pathlib.Path(a.arc1).glob('training/*.json')),
       'arc1_evaluation':list(pathlib.Path(a.arc1).glob('evaluation/*.json')),
       'arc2_training':list(pathlib.Path(a.arc2).glob('training/*.json')),
       'arc2_evaluation':list(pathlib.Path(a.arc2).glob('evaluation/*.json')),
       'conceptarc':list(pathlib.Path(a.conceptarc).glob('*/*.json')),
    }.items():
        exp={'arc1_training':400,'arc1_evaluation':400,'arc2_training':1000,'arc2_evaluation':120,'conceptarc':160}[group]
        assert len(paths)==exp,(group,len(paths),exp)
        src[group]=[(str(path.relative_to(pathlib.Path(a.conceptarc) if group=='conceptarc' else pathlib.Path(a.arc2 if group.startswith('arc2') else a.arc1))),*canonical(json.loads(path.read_text()))) for path in sorted(paths)]
    other=[(group,*row) for group,rows in src.items() if group!='conceptarc' for row in rows]
    trainidx=collections.defaultdict(list);fullidx=collections.defaultdict(list)
    for group,path,train,full in other:
        trainidx[train].append(group+'/'+path);fullidx[full].append(group+'/'+path)
    receipts=[]
    for path,train,full in src['conceptarc']:
        receipts.append({'conceptarc_path':path,'canonical_train_sha':train,'canonical_full_sha':full,
                        'other_corpora_same_train':trainidx.get(train,[]),'other_corpora_same_full':fullidx.get(full,[])})
    result={'schema':'NEUMANN_Q0_POSTGRADE_EXACT_CORPUS_DUPLICATE_AUDIT.v1',
       'corpus_counts':{k:len(v) for k,v in src.items()},
       'other_originals':len(other),'conceptarc_originals':len(receipts),
       'identical_demo_multiset_count':sum(bool(x['other_corpora_same_train']) for x in receipts),
       'identical_full_original_count':sum(bool(x['other_corpora_same_full']) for x in receipts),
       'matching_cases':[x for x in receipts if x['other_corpora_same_train'] or x['other_corpora_same_full']],
       'receipts':receipts,
       'limit':'Identical test/demonstration content check only, NOT abstract concept/rule novelty, author independence of concepts, data contamination from neural pretraining, or out-of-domain theorem.',
       'graded_after_first_external_source_inference':True}
    q=pathlib.Path(a.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('CONCEPTARC160_CANONICAL_DUPLICATION_AUDIT',result['identical_demo_multiset_count'],result['identical_full_original_count'],flush=True)
if __name__=='__main__':main()
