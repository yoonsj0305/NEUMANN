"""Preserve first D0 index, repair only execution IDs in a separate asset version."""
from pathlib import Path
from collections import Counter
import hashlib,json
from neumann1.functional_experience_store import ExperienceStore


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def run(work):
    first=work/'Continuation/FUNCTIONAL_EXPERIENCES_FIRST';index=json.loads((first/'index.json').read_text())
    original_manifest=json.loads((first/'manifest.json').read_text())
    for n,h in original_manifest.items():assert sha(first/n)==h
    out=work/'Continuation/FUNCTIONAL_EXPERIENCES_IDENTITY_REPAIR'
    assert not(out/'manifest.json').exists(),'Completed repair must not be overwritten'
    out.mkdir(exist_ok=True)
    old_index_sha=sha(first/'index.json');old_counts=Counter(r['record_id']for r in index['records'])
    assert len(old_counts)==285 and len(index['records'])==290
    for i,r in enumerate(index['records']):
        r['prior_record_id']=r['record_id'];r['record_id']+=':case:'+str(i).zfill(3)
        for asset in r['assets'].values():
            source=first/asset['path'];assert sha(source)==asset['sha256']
            target=out/asset['path'];target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==source.read_bytes()
            else:target.write_bytes(source.read_bytes())
            assert sha(target)==asset['sha256']
    index['study']='D0_FUNCTIONAL_STRUCTURAL_EXPERIENCE_IDENTITY_REPAIR_V1'
    index['prior_index_sha256']=old_index_sha;index['repair']='Exact source byte hash remains lineage; unique benchmark execution index becomes record identity'
    save(out/'index.json',index)
    store=ExperienceStore(out,sha(out/'index.json'));denials=0
    for r in index['records']:
        assert store.view(r['record_id'],'original','development_problem')['source']
        for field,asset in r['assets'].items():
            assert store.view(r['record_id'],field,'audit') is not None
            for purpose in ['train','fresh_evaluation','runtime_oracle']:
                try:store.view(r['record_id'],field,purpose)
                except ValueError:denials+=1
                else:raise AssertionError('Denied role activated')
    report={'status':'PASS_D0_DISTINCT_EXECUTION_IDS_AND_UNCHANGED_PAYLOADS','records':290,'distinct_record_ids':len(store.records),
            'distinct_source_byte_groups':285,'duplicate_source_group_count':sum(n>1 for n in old_counts.values()),
            'original_first_index_preserved':True,'original_payloads_all_unchanged':True,'index_sha256':sha(out/'index.json'),
            'loader_denials':denials,'counterexample_rows':373,'fresh_eligible':0,'training':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(out/'report.json',report);save(out/'manifest.json',{p.relative_to(out).as_posix():sha(p)for p in sorted(out.rglob('*'))if p.is_file()})
    print(json.dumps(report,indent=2))


if __name__=='__main__':run(Path(__file__).resolve().parents[3])
