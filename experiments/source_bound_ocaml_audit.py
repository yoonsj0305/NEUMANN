"""Independent local replay of frozen actual OCaml finite engineering."""
from pathlib import Path
import hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.recursive_summary_replay import independent_obligations


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def audit(preparation,local,remote,output):
    import z3
    assert not output.exists();output.mkdir(parents=True)
    contract=read(preparation/'preregister.json')
    assert sha(preparation/'preregister.json')=='44d423a623b4beb04a30c0b1cf25d500346c4caebe5f0515b7c57f5d7eb60b20'
    assert sha(preparation/'preregister.json')==read(preparation/'freeze.json')['registration_sha256']
    assert sha(local/'report.json')=='5ac54a33a61a5406f5312d22abe7bf4c37fdd5b35ed6173f2b3198f7b14209c4'
    assert sha(local/'manifest.json')=='a768622790023280b4679d35e886eb190ffc9fff041d32c3adff2033e3756ac3'
    assert all(sha(ROOT/n)==sha(preparation/'source'/n)==pin for n,pin in contract['sources'].items())
    local_manifest=read(local/'manifest.json');assert all(sha(local/n)==pin for n,pin in local_manifest.items())
    archive=remote/'NEUMANN_SOURCE_BOUND_OCAML_FIRST.zip'
    assert sha(archive)=='a437d24cad4655319c98f82c4e41444728cdff0bc021885d4b1ce66293b73201'
    extracted=remote/'extracted';assert not extracted.exists();extracted.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        for member in z.infolist():
            destination=(extracted/member.filename).resolve()
            assert destination.is_relative_to(extracted.resolve()) and not member.is_dir()
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(z.read(member))
        archive_members=len(z.namelist())
    first=extracted/'source-bound-ocaml-first';transport=extracted/'source-bound-ocaml-transport';preflight=extracted/'source-bound-preflight'
    manifest=read(first/'manifest.json');assert all(sha(first/n)==pin for n,pin in manifest.items())
    freeze=read(transport/'freeze.json')
    assert sha(transport/'inputs.zip')==freeze['input_archive_sha256']==sha(local/'OCAML_SOURCE_BOUND_REPLAY_INPUTS.zip')
    assert sha(transport/'source_bound_ocaml_remote.py')==freeze['runner_sha256']=='2984a911f758bdf128a1f510118bc99c84212e3c35e132b120ec12f6608eb3f9'
    assert read(first/'runtime.json')['compiler_version']=='5.0.0'
    cases,expected,events=read(local/'cases.json'),read(local/'expected.json'),read(first/'observations.json')
    assert len(cases)==len(events)==15
    programs=set();originals=set();proofs=serialized=rows=0
    for index,(case,event) in enumerate(zip(cases,events)):
        assert event['case_index']==index and event['source_original']==case['source']['path']
        assert event['source_sha256']==case['source']['sha256']
        worker=first/event['label'];assert sha(worker/'main.ml')==case['ocaml_sha256']==sha(local/case['ocaml_path'])
        assert event['status']=='ACTUAL_OCAML_FINITE_GOALS_MATCHED' and not event['compilation']['timeout'] and event['compilation']['exit_code']==0
        assert not event['execution']['timeout'] and event['execution']['exit_code']==0
        assert sha(worker/'run.bin')==event['binary_sha256']
        assert event['original_hole_skeleton_implementable']==case['original_hole_skeleton_implementable']
        result=read(local/'certificates'/(case['label']+'.json'))
        assert result['accepted'] and result['certificate']['accepted']
        key=(case['public_AST_sha256'],result['proposal_sha256'])
        if key not in programs:
            programs.add(key)
            public=result['binding']['projection']['public'];proposal=case['proposal']['proposal']
            for name,theorem in independent_obligations(public,proposal).items():
                solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem));assert solver.check()==z3.unsat
                proofs+=1
            for lemma in result['certificate']['obligations']:
                solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['smt2']);assert solver.check()==z3.unsat
                serialized+=1
        saved=read(worker/'parsed-rows.json');wanted=expected[case['label']]
        lines=(worker/'run.stdout').read_text().splitlines()
        assert len(lines)==len(saved)==len(wanted)==event['rows']==case['specification']['rows']
        for line,parsed,want in zip(lines,saved,wanted):
            label,a,b=line.split('|');n,code,shape=map(int,label.split(','))
            original=[int(x) for x in a.split(',')];native=[int(x) for x in b.split(',')]
            assert (n,code,shape)==(want['length'],want['code'],want['shape'])==(parsed['length'],parsed['code'],parsed['shape'])
            assert original==native==parsed['original']==parsed['native']==want['expected'];rows+=1
        originals.add(case['source']['sha256'])
    termination=0
    inventory=read(local/'inventory.json')
    for item in inventory:
        if item['status']=='UNSUPPORTED_SOURCE_PROTOCOL_NO_CLAIM':continue
        binding=read(local/item['binding'])
        assert binding['source_sha256']==item['source']['sha256']
        assert binding['projection']['reference_function']==binding['assertion']['reference']
        assert all(c['word_actual']==c['word_expected'] for c in binding['flatten_proof']['clause_records'])
        for lemma in binding['flatten_proof']['proof_records']:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(lemma['termination_smt2']);assert solver.check()==z3.unsat
            termination+=1
    report=read(first/'report.json')
    assert report['source_views']==len(cases) and report['original_and_native_output_rows']==rows==5445
    assert read(preflight/'receipt.json')['compile_exit']==2
    repair=read(preflight/'repair-receipt.json');assert repair['compile_exit']==0 and repair['rows']==363
    assert sha(preflight/'mss.ml')==repair['source_sha256']==read(preflight/'receipt.json')['source_sha256']
    result={'status':'PASS_SOURCE_BOUND_ACTUAL_OCAML_AND_INDEPENDENT_PROOF_AUDIT','archive_members_checked':archive_members,
            'remote_manifest_files_checked':len(manifest),'local_manifest_files_checked':len(local_manifest),
            'original_source_views':len(cases),'distinct_original_source_bytes':len(originals),'distinct_certified_programs':len(programs),
            'independent_Z3_summary_conditions':proofs,'serialized_CVC5_summary_conditions_in_Z3':serialized,
            'serialized_termination_conditions_in_Z3':termination,'actual_OCaml_original_native_expected_rows':rows,
            'preflight_environment_failure_retained':True,'duplicate_source_views_not_independent_tasks':True,
            'remote_first_report_sha256':sha(first/'report.json'),'remote_first_manifest_sha256':sha(first/'manifest.json'),
            'original_entire_OCaml_protocol_certified':False,'all_machine_integer_equivalence':False,'G1_admitted':False,'fresh_eligible':0}
    save(output/'audit.json',result);save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps(result,indent=2))


if __name__=='__main__':audit(*(Path(p) for p in sys.argv[1:]))
