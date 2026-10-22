#!/usr/bin/env python3
"""Read-only exact semantic overlap audit for pinned ARC-AGI-1 vs ARC-AGI-2.

Strict inference registry is frozen and first 400 prediction artifact already published.
This tool consumes evaluation answers only AFTER scoring; never changes predictions.
Canonical test preserves test order; training examples are an UNORDERED multiset.
Source semantic hashes are hashes of complete grid content, not Git blobs.
"""
import argparse, collections, hashlib, json, pathlib, math

ARC1='399030444e0ab0cc8b4e199870fb20b863846f34'
ARC2='f3283f727488ad98fe575ea6a5ac981e4a188e49'
PRE_GRADE='98dba8c5432f437d296df95d0db2860f6354575313bfc18d5fb2bf713dd2ea47'
OFFICIAL_GRADE='0f72e52b1ccc504a35717135d556090f34205a635e8f4dba050a47ce5aab035f'
COMPACT_GRADE='11ea8eb3438914e2ab7e9b5b83d80a8f3c3bea28d2f77e7b8d135544287d5878'

def sha(data): return hashlib.sha256(data).hexdigest()
def enc(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def canonical(task):
    # The unordered multiset of COMPLETE example inputs/outputs; test order meaningful.
    return sha(enc({'train':sorted(enc(x) for x in task['train']),
                    'test':[enc(x) for x in task['test']]}).encode())
def canonical_train(task): return sha(enc(sorted(enc(x) for x in task['train'])).encode())
def canonical_test(task): return sha(enc([enc(x) for x in task['test']]).encode())
def canon_case(directory):
    files=sorted(pathlib.Path(directory).glob('*.json'))
    return {f.stem:(canonical(json.loads(f.read_text())),canonical_train(json.loads(f.read_text())),canonical_test(json.loads(f.read_text()))) for f in files}

def main():
    ap=argparse.ArgumentParser()
    for n in ('arc1_eval','arc2_train','arc2_eval','score','out'):
        ap.add_argument('--'+n.replace('_','-'),required=True)
    x=ap.parse_args()
    src=pathlib.Path(x.arc1_eval); train=pathlib.Path(x.arc2_train); ev=pathlib.Path(x.arc2_eval)
    one=canon_case(src);two=canon_case(train);three=canon_case(ev)
    assert (len(one),len(two),len(three))==(400,1000,120)
    scorepath=pathlib.Path(x.score)
    assert sha(scorepath.read_bytes())==COMPACT_GRADE, 'frozen first-grade summary changed'
    grades=json.loads(scorepath.read_text())
    assert grades['n']==400 and len(grades['score'])==400
    assert grades['pregade_artifact_sha256']==PRE_GRADE
    assert grades['source_full_original_score_sha256']==OFFICIAL_GRADE
    assert grades['results']['baseline_correct']==5==grades['results']['new_correct']
    scores={t[0]:(bool(t[1]),bool(t[2])) for t in grades['score']}
    assert len(scores)==400 and set(scores)==set(one)
    # Cross-ID identical content (rare but scientifically necessary to examine).
    old_by_hash=collections.defaultdict(list)
    for tag,data in [('arc2_train',two),('arc2_eval',three)]:
        for ident,triple in data.items():old_by_hash[triple[0]].append((tag,ident))
    grouped=collections.Counter();rows=[]
    for name,(canon_sha,train_sha,test_sha) in one.items():
        known_train=name in two;known_eval=name in three
        hashes=old_by_hash.get(canon_sha,[])
        same_id_train_sem=known_train and two[name][0]==canon_sha
        same_id_eval_sem=known_eval and three[name][0]==canon_sha
        semantic_leak=bool(hashes)
        id_leak=known_train or known_eval
        id_clean=not id_leak; semantic_clean=not semantic_leak
        fully_clean=id_clean and semantic_clean
        b,n=scores[name]
        if known_train:
            grouped['arc1_ids_in_arc2_train']+=1
            grouped['arc1_train_semantic_equal']+=same_id_train_sem
            grouped['arc1_train_demo_equal']+=two[name][1]==train_sha
            grouped['arc1_train_test_equal']+=two[name][2]==test_sha
        if known_eval:
            grouped['arc1_ids_in_arc2_eval']+=1
            grouped['arc1_eval_semantic_equal']+=same_id_eval_sem
        if id_leak:grouped['any_id_overlap']+=1
        if semantic_leak:grouped['any_semantic_overlap']+=1
        if id_clean:grouped['strict_id_disjoint']+=1
        if semantic_clean:grouped['semantic_disjoint']+=1
        if fully_clean:grouped['conservatively_clean']+=1
        if b:grouped['baseline_correct_all']+=1
        if n:grouped['new_correct_all']+=1
        for label,condition in [('id_disjoint',id_clean),('semantic_disjoint',semantic_clean),('conservative_clean',fully_clean),('overlap',id_leak or semantic_leak)]:
            if condition:
                grouped[label+'_n']+=1
                grouped[label+'_baseline_correct']+=b
                grouped[label+'_new_correct']+=n
        rows.append({'id':name,'semantic_sha256':canon_sha,'train_sha256':train_sha,'test_sha256':test_sha,
                     'arc2_train_same_id':known_train,'arc2_eval_same_id':known_eval,
                     'arc2_train_full_semantic_equal':bool(same_id_train_sem),
                     'arc2_train_demo_equal':bool(known_train and two[name][1]==train_sha),
                     'arc2_train_test_equal':bool(known_train and two[name][2]==test_sha),
                     'semantic_duplicate_targets':[{'split':z,'id':j} for z,j in hashes],
                     'id_disjoint':id_clean,'semantic_disjoint':semantic_clean,'strict_clean':fully_clean,
                     'baseline_correct':b,'new_correct':n})
    assert grouped['baseline_correct_all']==grouped['new_correct_all']==5
    assert grouped['any_id_overlap']+grouped['strict_id_disjoint']==400
    assert grouped['conservatively_clean']<=grouped['strict_id_disjoint']
    # No task is declared globally independent merely because ID and canonical content differ.
    n_clean=grouped['conservative_clean_n']; n_success=grouped['conservative_clean_new_correct']
    report={'schema':'NEUMANN_Q0_ARC1_ARC2_CROSS_CORPUS_SEMANTIC_LEAKAGE_v2',
            'source_pins':{'arc1_commit':ARC1,'arc1_eval_tree':'4a19f8327d45dda5e1809ee47be08bf1484b493b',
                           'arc2_commit':ARC2,'arc2_train_tree':'dac7259367cc5099ef6a7b604a50a93affbbee33',
                           'arc2_eval_tree':'8d04288aac3146b7c47d0b799c18bc9c0217d838'},
            'frozen_first_pregrade_sha256':PRE_GRADE,'frozen_first_full_postgrade_sha256':OFFICIAL_GRADE,
            'frozen_compact_grades_sha256':COMPACT_GRADE,
            'canonicalization':'Train list unordered multiset of complete input-output grids; test list ordered and fully exact; no color/permutation/geometric augmentation used',
            'counts':dict(grouped),'strict_clean_ids':sorted(r['id'] for r in rows if r['strict_clean']),
            'conservative_clean_rate':None if not n_clean else round(n_success/n_clean,8),
            'global_OOD_independence_proven':False,
            'interpretation':'Only task-ID and exact-content disjointness on two public corpora audited. Same-family concepts, historical public exposure and near-duplicates NOT excluded; this is not a certified frontier generalization.',
            'rows':rows}
    p=pathlib.Path(x.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('ARC1_ARC2_SEMANTIC_OVERLAP_AUDIT',json.dumps(dict(grouped),sort_keys=True),flush=True)
    print('CLEAN_ID_N',n_clean,'CLEAN_NEW_CORRECT',n_success,'FIRST_RESULT_UNCHANGED',flush=True)
    print('REPRODUCIBLE_AUDIT_SHA256',sha(p.read_bytes()),flush=True)
if __name__=='__main__':main()
