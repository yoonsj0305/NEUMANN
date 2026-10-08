"""Local integrity replay of all frozen native outcomes, including failed workers."""
from pathlib import Path,PurePosixPath
from collections import Counter
import hashlib,json,zipfile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(work):
    out=work/'Continuation/SUFU_NATIVE_FIRST';receipt=json.loads((out/'export-receipt.json').read_text())
    archive=out/'SUFU_NATIVE_FIRST.zip';assert sha(archive)==receipt['sha256'];assert archive.stat().st_size==receipt['bytes']
    for p in receipt['parts']:assert sha(out/p['file'])==p['sha256'] and(out/p['file']).stat().st_size==p['bytes']
    with zipfile.ZipFile(archive)as z:
        assert len(z.infolist())==receipt['members'];assert len(z.namelist())==len(set(z.namelist()))
        for item in z.infolist():
            rel=PurePosixPath(item.filename)
            assert not rel.is_absolute()and'..'not in rel.parts and'\\'not in item.filename
            destination=out.joinpath(*rel.parts)
            assert out.resolve()in destination.resolve().parents
            destination.parent.mkdir(parents=True,exist_ok=True)
            raw=z.read(item)
            if destination.exists():assert destination.read_bytes()==raw,'Extracted bytes changed'
            else:
                with destination.open('xb')as f:f.write(raw)
    native=out/'neumann-sufu/native-suite-first'
    report=json.loads((native/'report.json').read_text());reg=json.loads((native/'registration.json').read_text())
    assert sha(native/'report.json')==receipt['native_first_report_sha256'];assert sha(native/'manifest.json')==receipt['native_first_manifest_sha256']
    files=json.loads((native/'manifest.json').read_text())
    for n,h in files.items():assert sha(native/n)==h
    prep=work/'Continuation/SUFU_NATIVE_PREPARATION'
    assert sha(native/'registration.json')==sha(prep/'registration.json')
    repo=work/'GitHub/NEUMANN'
    assert sha(repo/'experiments/sufu_native_suite.py')==reg['runner_sha256']
    assert sha(out/'neumann-sufu/build-jsoncpp/executor/run')==receipt['binary_sha256']==reg['executable_sha256']
    build_receipt=json.loads((out/'neumann-sufu/build-repair-receipt.json').read_text())
    assert sha(out/'neumann-sufu/source/src/surface/f')==build_receipt['frontend_sha256']
    assert'NDEBUG'not in(out/'neumann-sufu/build-jsoncpp/executor/CMakeFiles/run.dir/flags.make').read_text()
    intake=work/'Continuation/SUFU_SOURCE_FIRST';m=json.loads((intake/'manifest.json').read_text())
    originals={r['path']:r for r in m['files']};native_counts=Counter();checked=[]
    assert len(report['outcomes'])==290==len(reg['benchmarks'])
    for index,r in enumerate(report['outcomes']):
        assert r['index']==index;assert r['benchmark']==reg['benchmarks'][index]
        original=intake/'upstream'/originals[r['benchmark']['path']]['local_path'];assert sha(original)==r['benchmark']['sha256']
        p=native/f'{index:03}';assert json.loads((p/'record.json').read_text())==r
        assert sha(p/'stdout')==r['stdout_sha256'];assert sha(p/'stderr')==r['stderr_sha256']
        target=p/'optimized.f';assert(sha(target)if target.exists()else None)==r['optimized_sha256']
        text=(p/'stdout').read_text(errors='replace');lines=text.strip().splitlines()
        success=bool(not r['timeout']and r['exit_code']==0 and lines and lines[-1]=='Success'and'\nincorrect\n'not in'\n'+text+'\n'and target.exists()and target.stat().st_size>0)
        status='UPSTREAM_BOUNDED_SUCCESS'if success else'TIMEOUT'if r['timeout']else'PROCESS_ERROR'if r['exit_code']!=0 else'NOT_VERIFIED'
        assert status==r['status'];native_counts[status]+=1;checked.append({'index':index,'status':status})
    assert dict(native_counts)==report['counts']==receipt['counts']
    assert abs(sum(r['launch_to_exit_seconds']for r in report['outcomes'])-report['recorded_worker_seconds'])<1e-6
    audit=work/'Continuation/SUFU_NATIVE_AUDIT';audit.mkdir()
    result={'status':'PASS_NATIVE_FIRST_INTEGRITY_REPLAY','archive_members':receipt['members'],'native_manifest_files':len(files),
            'benchmarks_checked':290,'counts':dict(native_counts),'binary_and_frontend_hash_verified':True,
            'registration_and_public_source_hashes_verified':True,'stdout_status_recomputed':True,
            'whole_native_seconds':report['sequential_suite_seconds'],'complete_dependency_closure':False,
            'functional_equivalence_proven':False,'cost_advantage_established':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False}
    (audit/'report.json').write_text(json.dumps(result,indent=2)+'\n');(audit/'checked.json').write_text(json.dumps(checked,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main(Path(__file__).resolve().parents[3])
