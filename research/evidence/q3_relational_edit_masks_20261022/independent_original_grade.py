#!/usr/bin/env python3
"""Immutable grader for true original labels, callable only after sealed pregrade."""
import argparse,collections,hashlib,json,pathlib

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--source',required=True);p.add_argument('--corpus',choices=['conceptarc160','arc2eval120'],required=True)
 p.add_argument('--sealed',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();predfile=pathlib.Path(a.sealed);d=json.loads(predfile.read_text())
 n=160 if a.corpus=='conceptarc160' else 120
 assert d['n']==n and not d['test_labels_seen']
 root=pathlib.Path(a.source);original={}
 if a.corpus=='conceptarc160':
    folders=sorted(x for x in root.iterdir() if x.is_dir());assert len(folders)==16
    for folder in folders:
        fs=sorted(folder.glob('*.json'));assert len(fs)==10
        for f in fs:original[folder.name+'__'+f.stem]=json.loads(f.read_text())
 else:
    fs=sorted(root.glob('*.json'));assert len(fs)==120
    original={f.stem:json.loads(f.read_text()) for f in fs}
 assert set(original)==set(d['rows'])
 counts=collections.Counter();rows={}
 encode=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
 for id in sorted(original):
    r=d['rows'][id];t=[x['output'] for x in original[id]['test']];out=r.get('prediction')
    correct=bool(out is not None and len(out)==len(t) and all(x==y for x,y in zip(out,t)))
    counts[r['status']]+=1;counts['attempted']+=int(out is not None);counts['correct']+=int(correct)
    if r['status']=='INFERRED_RELATIONAL_EDIT_RULE':
        counts['learned_mask_attempted']+=1;counts['learned_mask_correct']+=int(correct)
        if correct:
            print('NEW_EXACT_SOURCE_DERIVED_RELATIONAL_EDIT',json.dumps({
                'id':id,'ast':r['ast'],'demonstrations':len(original[id]['train']),
                'test_grids':len(t),'predicted_sha256':hashlib.sha256(encode(out)).hexdigest(),
                'independent_truth_sha256':hashlib.sha256(encode(t)).hexdigest()},sort_keys=True),flush=True)
    else:counts['baseline_correct']+=int(correct)
    rows[id]={'status':r['status'],'correct':correct,'prediction_emitted':out is not None}
 assert counts['baseline_correct']+counts['learned_mask_correct']==counts['correct']
 result={'schema':'NEUMANN_RELATIONAL_EDIT_SOURCE_INDEPENDENT_ORIGINAL_GRADE.v1',
   'n':n,'corpus':a.corpus,'pregrade_sha256':hashlib.sha256(predfile.read_bytes()).hexdigest(),
   'counts':dict(counts),'rows':rows,'global_Q3_learned_exclusive':'OPEN',
   'global_Q4_total10x':'OPEN','fresh_blind_status':'REUSED_PUBLIC_CORPUS'}
 out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(result,sort_keys=True)+'\n')
 print('RELATIONAL_EDIT_INDEPENDENT_ORIGINAL',a.corpus,json.dumps(result['counts'],sort_keys=True),
       'sha256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
