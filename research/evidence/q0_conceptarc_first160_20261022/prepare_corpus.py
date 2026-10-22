#!/usr/bin/env python3
"""Canonical ConceptARC 160 task materialization without evaluation outputs."""
import argparse, pathlib, json, hashlib, shutil

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True)
    ap.add_argument('--masked',required=True)
    ap.add_argument('--metadata',required=True)
    a=ap.parse_args()
    source=pathlib.Path(a.source);output=pathlib.Path(a.masked)
    assert not output.exists()
    output.mkdir(parents=True)
    groups=sorted(x for x in source.iterdir() if x.is_dir())
    assert len(groups)==16
    records=[];grids=0
    for group in groups:
        originals=sorted(group.glob('*.json'))
        assert len(originals)==10,(group,len(originals))
        for path in originals:
            original=json.loads(path.read_text())
            assert isinstance(original['train'],list) and 1<=len(original['train'])<=4
            assert len(original['test'])==3
            assert all('input' in r and 'output' in r for r in original['train'])
            assert all('input' in r and 'output' in r for r in original['test'])
            uid=group.name+'__'+path.stem
            masked={'train':original['train'],'test':[{'input':x['input']} for x in original['test']]}
            assert all('output' not in x for x in masked['test'])
            (output/(uid+'.json')).write_text(json.dumps(masked,separators=(',',':'))+'\n')
            records.append({'id':uid,'group':group.name,'path':str(path.relative_to(source))})
            grids+=len(original['test'])
    assert len(records)==160 and grids==480
    assert len(set(r['id'] for r in records))==160
    meta={'n':160,'test_grids':480,'groups':sorted(set(r['group'] for r in records)),'rows':records,
          'source_corpus_tree':'a9e933c021388297f21fa1cded180105479addc0','labels_masked':True}
    p=pathlib.Path(a.metadata);p.parent.mkdir(exist_ok=True,parents=True)
    p.write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print('MASKED_FIRST_CONCEPTARC',len(records),grids,hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__': main()
