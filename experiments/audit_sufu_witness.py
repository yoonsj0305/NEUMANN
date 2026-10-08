"""Verify all native replay artifacts and exact native/Python differences locally."""
from pathlib import Path,PurePosixPath
from collections import Counter
import hashlib,json,zipfile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def error(v):return type(v)is dict and v.get('native_semantics_error')is True
def run(work):
    root=work/'Continuation/SUFU_NATIVE_REPLAYS_FIRST';receipt=json.loads((root/'export-receipt.json').read_text())
    archive=root/'SUFU_NATIVE_REPLAYS_FIRST.zip';assert sha(archive)==receipt['sha256']and archive.stat().st_size==receipt['bytes']
    for p in receipt['parts']:assert sha(root/p['file'])==p['sha256']
    with zipfile.ZipFile(archive)as z:
        assert len(z.namelist())==len(set(z.namelist()))==receipt['members']
        for name in z.namelist():
            rel=PurePosixPath(name);assert not rel.is_absolute()and'..'not in rel.parts and'\\'not in name
            p=root.joinpath(*rel.parts);assert root.resolve()in p.resolve().parents;p.parent.mkdir(parents=True,exist_ok=True)
            raw=z.read(name)
            if p.exists():assert p.read_bytes()==raw
            else:
                with p.open('xb')as f:f.write(raw)
    base=root/'neumann-resume';phases=[('sufu-witness-replay','SUFU_WITNESS_PREPARATION','sufu_source_witness.cpp'),
        ('sufu-witness-initialized-replay','SUFU_WITNESS_INITIALIZED_PREPARATION','sufu_source_witness_initialized.cpp'),
        ('sufu-witness-owned-replay','SUFU_WITNESS_OWNED_PREPARATION','sufu_source_witness_owned.cpp')]
    phase_summaries=[];native_differences=[];verified_rows=0;semantic_errors=0;missing=[]
    stress=json.loads((work/'Continuation/FUNCTIONAL_STRESS_FIRST/report.json').read_text());stress_by={c['index']:c for c in stress['cases_detail']}
    original_counts=Counter();optimized_counts=Counter()
    for folder,preparation,source_name in phases:
        p=base/folder;first=p/'first';reg=json.loads((p/'registration.json').read_text());report=json.loads((first/'report.json').read_text())
        assert sha(p/'registration.json')==sha(work/'Continuation'/preparation/'registration.json')
        assert json.loads((first/'registration.json').read_text())==reg
        assert sha(p/'runner.py')==reg['runner_sha256'];assert sha(base/source_name)==reg['adapter_source_sha256']
        manifest=json.loads((first/'manifest.json').read_text())
        for n,h in manifest.items():assert sha(first/n)==h
        assert len(report['cases'])==183==len(reg['cases']);counts=Counter()
        for c,expected_case in zip(report['cases'],reg['cases']):
            assert c['index']==expected_case['index'];idx=c['index'];case_folder=first/f'{idx:03}'
            assert json.loads((case_folder/'record.json').read_text())==c;counts[c['status']]+=1
            for arm,event in c['workers'].items():
                assert sha(case_folder/(arm+'.stdout'))==event['stdout_sha256'];assert sha(case_folder/(arm+'.stderr'))==event['stderr_sha256']
                if event.get('outputs_sha256'):assert sha(case_folder/(arm+'.json'))==event['outputs_sha256']
            inp=p/expected_case['inputs_file'];exp=p/expected_case['expected_file']
            assert sha(inp)==expected_case['inputs_sha256'];assert sha(exp)==expected_case['expected_sha256']
            assert all(set(r)=={'entrypoint','inputs','arguments'}for r in json.loads(inp.read_text()))
            if folder!='sufu-witness-owned-replay':continue
            if c['status']!='NATIVE_REPLAY_COMPLETE':
                missing.append({'index':idx,'original_path':c['original_path'],'rows':c['rows'],'workers':c['workers']});continue
            assert all(e['exit_code']==0 and e['status']=='NATIVE_VALUES_RETURNED'for e in c['workers'].values())
            left=json.loads((case_folder/'original.json').read_text());right=json.loads((case_folder/'optimized.json').read_text());expected=json.loads(exp.read_text())
            assert len(left)==len(right)==len(expected)==len(c['row_results'])
            for e,l,r,observed in zip(expected,left,right,c['row_results']):
                sr=stress_by[idx]['rows'][e['row_id']]
                assert canon(sr['original_output'])==canon(e['original']);assert canon(sr['transformed_output'])==canon(e['optimized'])
                has_error=error(l)or error(r);semantic_errors+=has_error
                original_counts['error'if error(l)else'match'if canon(l)==canon(e['original'])else'disagreement']+=1
                optimized_counts['error'if error(r)else'match'if canon(r)==canon(e['optimized'])else'disagreement']+=1
                if not error(l):assert canon(l)==canon(e['original'])
                if not error(r):assert canon(r)==canon(e['optimized'])
                reconstructed={'row_id':e['row_id'],'python_status':e['python_status'],
                    'original_native_matches_python':canon(l)==canon(e['original']),
                    'optimized_native_matches_python':canon(r)==canon(e['optimized']),
                    'native_pair_matches':not has_error and canon(l)==canon(r),'native_semantics_error':has_error}
                assert reconstructed==observed
                if not has_error and canon(l)!=canon(r):
                    assert sr['status']=='CONCRETE_COUNTEREXAMPLE';native_differences.append({'index':idx,'original_path':c['original_path'],'row_id':e['row_id'],'phase':sr['phase'],'original':l,'optimized':r})
                verified_rows+=1
        assert dict(counts)==report['case_counts'];phase_summaries.append({'folder':folder,'case_counts':dict(counts),'manifest_files':len(manifest),'registration_sha256':sha(p/'registration.json')})
    assert sha(base/'sufu-witness-build-owned-first/source-witness')==receipt['corrected_binary_sha256']
    native_report=json.loads((base/'sufu-witness-owned-replay/first/report.json').read_text());assert native_report==receipt['report']|{'cases':native_report['cases']}
    assert len(native_differences)==native_report['native_pair_differences']==373
    assert verified_rows==native_report['returned_rows'];assert semantic_errors==native_report['native_semantics_error_rows']
    audit=work/'Continuation/SUFU_NATIVE_REPLAYS_AUDIT';audit.mkdir()
    result={'status':'PASS_ALL_NATIVE_REPLAY_ARTIFACTS_AND_NONERROR_VALUES','archive_members':receipt['members'],'phases':phase_summaries,
            'native_rows':verified_rows,'native_semantic_error_rows':semantic_errors,'original_counts':dict(original_counts),'optimized_counts':dict(optimized_counts),
            'native_confirmed_pair_differences':len(native_differences),'programs_with_differences':len(set(c['index']for c in native_differences)),
            'failed_program_pairs':missing,'official_score_changed':False,'universal_equivalence_proven':False,'cost_advantage_established':False,
            'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    (audit/'report.json').write_text(json.dumps(result,indent=2)+'\n');(audit/'native-differences.json').write_text(json.dumps(native_differences,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='failed_program_pairs'},indent=2));print('INCOMPLETE_PAIRS',[(c['index'],c['original_path'])for c in missing])


if __name__=='__main__':run(Path(__file__).resolve().parents[3])
