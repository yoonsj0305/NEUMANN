"""Audit separately retained frontend and OCaml recovery records; no rejudgment."""
from pathlib import Path
from collections import Counter
import hashlib,json,zipfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from neumann1.functional_source import parse
from neumann1.functional_types import check

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def manifests(first):
    m=read(first/'manifest.json')
    for n,h in m.items():assert sha(first/n)==h,(first,n)
    return len(m)

def run(work):
    local=work/'Continuation/NATIVE_CONTINUATION_RECOVERY_FIRST';receipt=read(local/'export-receipt.json')
    assert sha(local/receipt['archive'])==receipt['sha256']
    assert (local/receipt['archive']).stat().st_size==receipt['bytes']
    for part in receipt['parts']:assert sha(local/part['file'])==part['sha256']
    with zipfile.ZipFile(local/receipt['archive'])as z:
        assert len(z.namelist())==len(set(z.namelist()))==receipt['members']
        for n in z.namelist():assert (local/n).read_bytes()==z.read(n)
    base=local/'neumann-resume';summary=[];rows=0
    prior=work/'Continuation/SUFU_NATIVE_FIRST/neumann-sufu/native-suite-first'
    for folder,prep,status in [('sufu-witness-roundtrip-replay','SUFU_WITNESS_ROUNDTRIP_PREPARATION','NATIVE_REPLAY_INCOMPLETE_PRESERVED'),
        ('sufu-witness-roundtrip-lf-replay','SUFU_WITNESS_ROUNDTRIP_LF_PREPARATION','NATIVE_REPLAY_COMPLETE')]:
        root=base/folder;first=root/'first';reg=read(root/'registration.json');r=read(first/'report.json')
        assert sha(root/'registration.json')==sha(work/'Continuation'/prep/'registration.json')
        assert read(first/'registration.json')==reg
        assert sha(root/'runner.py')==reg['runner_sha256']==sha(ROOT/'experiments/sufu_native_roundtrip.py')
        assert sha(ROOT/'experiments/sufu_source_witness_owned.cpp')==reg['adapter_source_sha256']
        assert sha(work/'Continuation/SUFU_NATIVE_REPLAYS_FIRST/neumann-resume/sufu-witness-build-owned-first/source-witness')==reg['binary_sha256']
        manifest_count=manifests(first);assert len(reg['cases'])==len(r['cases'])==4
        for c,observed in zip(reg['cases'],r['cases']):
            idx=c['index'];case=first/f'{idx:03}';assert observed==read(case/'record.json')
            assert observed['status']==status
            assert sha(root/c['inputs_file'])==c['inputs_sha256']
            assert sha(root/c['expected_file'])==c['expected_sha256']
            original=prior/f'{idx:03}'/'optimized.f';modified=root/f'{idx:03}.optimized.f'
            assert sha(original)==c['prior_optimized_sha256'];assert sha(modified)==c['optimized_sha256']
            before=parse(original.read_text());after=parse(modified.read_text());assert before==after
            assert check(before)==check(after)
            for arm,event in observed['workers'].items():
                assert sha(case/(arm+'.stdout'))==event['stdout_sha256']
                assert sha(case/(arm+'.stderr'))==event['stderr_sha256']
            if status!='NATIVE_REPLAY_COMPLETE':continue
            assert b'\r'not in modified.read_bytes()
            expected=read(root/c['expected_file']);a=read(case/'original.json');b=read(case/'optimized.json')
            assert len(a)==len(b)==len(expected)==c['rows']
            for x,y,e in zip(a,b,expected):assert x==e['original'] and y==e['optimized'] and x==y;rows+=1
            assert all(e['exit_code']==0 and e['status']=='NATIVE_VALUES_RETURNED'for e in observed['workers'].values())
        assert r['case_counts']=={status:4}
        summary.append({'folder':folder,'cases':4,'manifest_files':manifest_count,'status':status,'rows':r['returned_rows']})
    assert rows==276
    root=base/'ocaml-decoder-recovery';first=root/'first';reg=read(root/'registration.json')
    assert sha(root/'registration.json')==sha(work/'Continuation/SYMBOLIC_DECODER_OCAML_RECOVERY_PREPARATION/registration.json')
    assert sha(root/'runner.py')==reg['runner_sha256']==sha(ROOT/'experiments/symbolic_decoder_ocaml_recovery.py')
    manifest_count=manifests(first);original=work/'Continuation/SYMBOLIC_DECODER_FIRST'
    assert sha(root/'input.zip')==sha(original/'OCAML_SYMBOLIC_DECODER_REPLAY_INPUTS.zip')==reg['input_archive_sha256']
    with zipfile.ZipFile(root/'input.zip')as z:
        contract=json.loads(z.read('remote-contract.json'))
        assert contract==read(original/'remote-contract.json')
        for n,h in contract['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    assert read(first/'runtime.json')['compiler_version']=='4.14.1'
    events=read(first/'observations.json');cases=read(original/'cases.json');expected=read(original/'expected.json')
    assert len(events)==len(cases)==26;ocamlrows=0;sourcehashes=set();asts=set()
    for i,(c,e)in enumerate(zip(cases,events)):
        assert e['case_index']==i and e['source_original']==c['source']['path']and e['source_sha256']==c['source']['sha256']
        worker=first/e['label'];assert sha(worker/'main.ml')==c['ocaml_sha256']==sha(original/c['ocaml_path'])
        assert sha(worker/'run.bin')==e['binary_sha256'];assert e['status']=='ACTUAL_OCAML_FINITE_GOALS_MATCHED'
        assert e['compilation']['exit_code']==e['execution']['exit_code']==0
        assert not e['compilation']['timeout']and not e['execution']['timeout']
        lines=(worker/'run.stdout').read_text().splitlines();saved=read(worker/'parsed-rows.json');wanted=expected[c['label']]
        assert len(lines)==len(saved)==len(wanted)==e['rows']==c['specification']['rows']
        for line,s,w in zip(lines,saved,wanted):
            key,a,b=line.split('|');n,code,shape=map(int,key.split(','));a=list(map(int,a.split(',')));b=list(map(int,b.split(',')))
            assert (n,code,shape)==(s['length'],s['code'],s['shape'])==(w['length'],w['code'],w['shape'])
            assert a==b==s['original']==s['native']==w['expected'];ocamlrows+=1
        sourcehashes.add(c['source']['sha256']);asts.add(c['public_AST_sha256'])
    assert ocamlrows==7818 and len(sourcehashes)==20 and len(asts)==11
    report=read(first/'report.json');assert report['original_and_native_output_rows']==ocamlrows
    assert report['status_counts']=={'ACTUAL_OCAML_FINITE_GOALS_MATCHED':26}
    out=work/'Continuation/NATIVE_CONTINUATION_RECOVERY_AUDIT';out.mkdir()
    result={'status':'PASS_ARCHIVE_AND_EXACT_FROZEN_INPUT_RECOVERY','archive_members':receipt['members'],'frontend_phases':summary,
        'frontend_AST_and_type_identity_cases':8,'LF_native_original_optimized_expected_rows':rows,
        'OCaml_manifest_files':manifest_count,'OCaml_source_views':26,'OCaml_distinct_source_bytes':20,'OCaml_distinct_public_ASTs':11,
        'OCaml_actual_original_native_expected_rows':ocamlrows,'old_OCaml5_archive_loss_preserved':True,'old_native179_of183_first_preserved':True,
        'compiler_recovery_not_performance_comparison':True,'all_machine_integer_equivalence':False,'whole_original_OCaml_protocol':False,
        'universal_functional_equivalence':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False,'learning_performed':False}
    save(out/'report.json',result);save(out/'manifest.json',{p.name:sha(p)for p in out.iterdir()if p.is_file()})
    print(json.dumps(result,indent=2))

if __name__=='__main__':run(ROOT.parents[1])
