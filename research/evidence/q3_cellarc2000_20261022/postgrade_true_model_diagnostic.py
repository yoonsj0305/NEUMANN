#!/usr/bin/env python3
"""Strict POSTGRADE-only causal/identifiability diagnosis using hidden TRUE metadata.
Never feed metadata, solutions, families or labels back into source-inference.
"""
import argparse,collections,hashlib,json,pathlib,urllib.request
from halo_boundary_probe import fit
from exact_local_rule_probe import feature,win
SPLITS=('test_interpolation','test_extrapolation')
def fetch(u):
    req=urllib.request.Request(u,headers={'User-Agent':'NEUMANN-POSTGRADE-ONLY-ORACLE/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:return r.read()
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pregrade',required=True)
    p.add_argument('--original-dir',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    beforefile=pathlib.Path(a.pregrade);before=json.loads(beforefile.read_text())
    assert before['n']==2000 and not before['sees_original_truth'] and not before['sees_metadata']
    metadata_repo='mireklzicar/cellarc_100k_meta'
    md_revision=json.loads(fetch('https://huggingface.co/api/datasets/'+metadata_repo))['sha']
    assert len(md_revision)==40
    strata=collections.defaultdict(collections.Counter);numbers=collections.Counter()
    witness=[];by_split={}
    for split in SPLITS:
        origin={}
        for line in (pathlib.Path(a.original_dir)/(split+'.jsonl')).read_text().splitlines():
            d=json.loads(line);origin[d['id']]=d
        assert len(origin)==1000
        base=f'https://huggingface.co/datasets/{metadata_repo}/resolve/{md_revision}/data/{split}.jsonl'
        raw=fetch(base);meta_rows=[json.loads(s) for s in raw.decode().splitlines()]
        assert len(meta_rows)==1000
        assert {s['id'] for s in meta_rows}==set(origin)
        counter=collections.Counter()
        for d in meta_rows:
            root=origin[d['id']]
            for key in ('train','query','solution'):
                assert d[key]==root[key],(split,d['id'],key)
            meta=d['meta']
            steps=int(meta['steps']);W=int(meta['window']);construction=str(meta.get('construction','UNKNOWN'))
            family=str(meta.get('family','UNKNOWN'));radius=(W-1)//2
            assert 2*radius+1==W and 1<=radius<=3 and 1<=steps<=5,(split,d['id'],radius,steps)
            row=before['rows'][split][d['id']]
            legacy=row['legacy'].get('prediction')==root['solution']
            newer=row['halo'].get('prediction')==root['solution']
            cv=row['halo'].get('cv',{}).get('prediction')==root['solution']
            stepkey='one_step' if steps==1 else 'multi_step'
            for group in (f'{stepkey}/{construction}',f'{family}/{stepkey}',f'r{radius}/t{steps}',f'{split}/{construction}'):
                t=strata[group]
                t['n']+=1
                t['legacy_correct']+=int(legacy)
                t['halo_correct']+=int(newer)
                t['cv_correct']+=int(cv)
                t['halo_wrong']+=int(row['halo'].get('prediction') is not None and not newer)
            counter[stepkey]+=1;counter[construction]+=1
            # Exact oracle-conditional structural proof: only true ONE-STEP source process.
            if steps==1:
                table=fit(d['train'],radius,'full')
                numbers['one_step_episodes']+=1
                if not table:
                    numbers['true_radius_demo_inconsistency']+=1
                    continue
                q=d['query'];ground=root['solution']
                # Boundary-agnostic interior cells of query have real local context.
                matched=0;covered=0;miss=0
                for i in range(radius,len(q)-radius):
                    key=tuple(q[i-radius:i+radius+1])
                    if key in table:
                        covered+=1
                        ok=int(table[key]==ground[i]);matched+=ok;miss+=int(not ok)
                numbers['true_radius_query_interior_supported_cells']+=covered
                numbers['true_radius_query_interior_exact_cells']+=matched
                numbers['true_radius_query_interior_wrong_cells']+=miss
                if miss and len(witness)<10:witness.append({'id':d['id'],'split':split,'issue':'unexpected_correct_class_interior_counterexample','wrong_interior':miss})
                # For cycle, circular query neighborhoods reflect actual process.
                if construction=='cycle':
                    numbers['one_step_cycle_episodes']+=1
                    windows=[tuple(win(q,j,radius)) for j in range(len(q))]
                    if all(k in table for k in windows):
                        p=[table[k] for k in windows]
                        numbers['one_step_cycle_full_input_covered']+=1
                        numbers['one_step_cycle_full_exact']+=int(p==ground)
                        numbers['one_step_cycle_full_wrong']+=int(p!=ground)
                    else:
                        numbers['one_step_cycle_query_unknown_windows']+=1
        by_split[split]={'n':1000,'original_meta_jsonl_sha256':hashlib.sha256(raw).hexdigest(),
                         'construction_and_step_groups':dict(counter)}
        print('POSTGRADE_TRUE_CA_SOURCE_STRATA',split,json.dumps(by_split[split],sort_keys=True),flush=True)
    output={'schema':'NEUMANN_CELLARC2000_POSTGRADE_TRUE_MODEL_MEMBERSHIP_AUDIT.v1',
            'metadata_repository':metadata_repo,'metadata_sha':md_revision,
            'metadata_never_available_to_inference':True,
            'meta_original_train_query_solution_exactly_identical':True,
            'pregrade_sha256':hashlib.sha256(beforefile.read_bytes()).hexdigest(),
            'n':2000,'strata':{k:dict(v) for k,v in sorted(strata.items())},
            'oracle_certification':dict(numbers),'counterexamples':witness,
            'oracle_not_deployable':True,'global_Q3_autonomous_trueclass_inference':'OPEN',
            'global_Q4_total10x':'OPEN'}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,sort_keys=True,separators=(',',':'))+'\n')
    print('ORACLE_TRUE_MODEL_SCOPE_BOUNDS',json.dumps(output['oracle_certification'],sort_keys=True),flush=True)
    print('ORACLE_TRUE_MODEL_STRATA',json.dumps(output['strata'],sort_keys=True),flush=True)
    print('POSTGRADE_AUDIT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
