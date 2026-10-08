"""Frozen native input-only replay of all eligible stress rows, no resampling."""
from pathlib import Path
from collections import Counter
import hashlib,json,os,signal,subprocess,time


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def run(root):
    reg=json.loads((root/'registration.json').read_text());assert sha(Path(__file__))==reg['runner_sha256']
    binary=Path(reg['binary']);assert sha(binary)==reg['binary_sha256']
    assert sha(Path(reg['adapter_source']))==reg['adapter_source_sha256']
    source=Path('/kaggle/working/neumann-sufu/source');native=Path('/kaggle/working/neumann-sufu/native-suite-first')
    assert(native/'report.json').exists();assert sha(native/'report.json')==reg['native_first_report_sha256']
    out=root/'first';assert not out.exists();out.mkdir();save(out/'registration.json',reg)
    cases=[];start=time.perf_counter()
    for c in reg['cases']:
        index=c['index'];folder=out/f'{index:03}';folder.mkdir()
        inputs=root/c['inputs_file'];assert sha(inputs)==c['inputs_sha256']
        expected=root/c['expected_file'];assert sha(expected)==c['expected_sha256'];expect=json.loads(expected.read_text())
        sources={'original':source/c['original_path'],'optimized':native/f'{index:03}'/'optimized.f'}
        result={'index':index,'original_path':c['original_path'],'rows':len(expect),'workers':{},'row_results':[]}
        for arm,p in sources.items():
            assert sha(p)==c[arm+'_sha256']
            outputs=folder/(arm+'.json');cmd=[str(binary),str(p),str(inputs),str(outputs)];begin=time.perf_counter();timeout=False
            with(folder/(arm+'.stdout')).open('xb')as stdout,(folder/(arm+'.stderr')).open('xb')as stderr:
                worker=subprocess.Popen(cmd,cwd=source,stdout=stdout,stderr=stderr,start_new_session=True)
                try:worker.wait(timeout=reg['per_program_seconds'])
                except subprocess.TimeoutExpired:timeout=True;os.killpg(worker.pid,signal.SIGKILL);worker.wait()
            status='TIMEOUT'if timeout else'NATIVE_VALUES_RETURNED'if worker.returncode==0 and outputs.exists()else'PROCESS_ERROR'
            event={'status':status,'exit_code':worker.returncode,'seconds':time.perf_counter()-begin,'stdout_sha256':sha(folder/(arm+'.stdout')),'stderr_sha256':sha(folder/(arm+'.stderr'))}
            if outputs.exists():event['outputs_sha256']=sha(outputs)
            result['workers'][arm]=event
        if all(v['status']=='NATIVE_VALUES_RETURNED'for v in result['workers'].values()):
            left=json.loads((folder/'original.json').read_text());right=json.loads((folder/'optimized.json').read_text())
            assert len(left)==len(right)==len(expect)
            canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'))
            for e,l,r in zip(expect,left,right):
                result['row_results'].append({'row_id':e['row_id'],'python_status':e['python_status'],
                    'original_native_matches_python':canon(l)==canon(e['original']),
                    'optimized_native_matches_python':canon(r)==canon(e['optimized']),
                    'native_pair_matches':not (type(l)is dict and l.get('native_semantics_error')) and not(type(r)is dict and r.get('native_semantics_error'))and canon(l)==canon(r),
                    'native_semantics_error':bool(type(l)is dict and l.get('native_semantics_error')or type(r)is dict and r.get('native_semantics_error'))})
            result['counts']={k:sum(r[k]for r in result['row_results'])for k in ['original_native_matches_python','optimized_native_matches_python','native_pair_matches']}
            result['status']='NATIVE_REPLAY_COMPLETE'
        else:result['status']='NATIVE_REPLAY_INCOMPLETE_PRESERVED'
        save(folder/'record.json',result);cases.append(result)
        with(out/'progress.jsonl').open('a')as f:f.write(json.dumps({'completed':len(cases),'total':len(reg['cases']),'last':index,'status':result['status']})+'\n');f.flush();os.fsync(f.fileno())
    rows=[r for c in cases for r in c['row_results']]
    report={'study':reg['study'],'case_counts':dict(Counter(c['status']for c in cases)),'cases':cases,'returned_rows':len(rows),
            'original_native_python_matches':sum(r['original_native_matches_python']for r in rows),
            'optimized_native_python_matches':sum(r['optimized_native_matches_python']for r in rows),
            'native_pair_differences':sum(not r['native_pair_matches']and not r['native_semantics_error']for r in rows),
            'native_semantics_error_rows':sum(r['native_semantics_error']for r in rows),'seconds':time.perf_counter()-start,
            'counterexamples_outside_upstream_sample_domain_possible':True,'official_score':False,'universal_equivalence_proven':False,
            'cost_advantage_established':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(out/'report.json',report);save(out/'manifest.json',{p.relative_to(out).as_posix():sha(p)for p in sorted(out.rglob('*'))if p.is_file()})
    print(json.dumps({k:v for k,v in report.items()if k!='cases'},indent=2))


if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]))
