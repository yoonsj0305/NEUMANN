"""Registered alternative published solver backend; preserves the CVC5 first."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
from synduce_full_baseline import registration as base_registration, PIN, sha


def registration(source):
    c=base_registration(source)
    c.update(experiment_id='FULL_SYNDuce_CVC4_BASELINE_INTEGRATION_V1',solver='cvc4',
             solver_version='record_actual_apt_version_before_execution',
             prior_exposure='All sources, public previous solution texts and CVC5 first outputs opened; no fresh evaluation',
             previous_CVC5_first_report_sha256='9fcd9c14fd0584c3368410dca69137e7bba51806112a382e5cb58441749c3daa',
             rationale='Published implementation originally tested CVC4 1.8; alternative backend is a strong native control, never a replacement first result')
    return c


def run(source,output,contract_path):
    data=contract_path.read_bytes();contract=json.loads(data)
    assert contract==registration(source)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==PIN
    assert not output.exists()
    output.mkdir(parents=True);(output/'preregister.json').write_bytes(data)
    binary=source/'_build/default/bin/Synduce.exe'
    runtime={'source_commit':PIN,'binary_sha256':sha(binary),
             'cpu':Path('/proc/cpuinfo').read_text(),
             'cvc4':subprocess.check_output(['cvc4','--version'],text=True),
             'z3':subprocess.check_output(['z3','--version'],text=True),
             'kernel':subprocess.check_output(['uname','-a'],text=True),
             'gpu_requested':False}
    (output/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    start=time.perf_counter();rows=[]
    for i,case in enumerate(contract['cases']):
        for repeat in range(3):
            label=f'{i:02}-{repeat}'
            command=[str(binary),'--cvc4','--compact','-j',*case['options'],str(source/'benchmarks'/case['path'])]
            before=time.perf_counter()
            child=subprocess.Popen(command,cwd=source,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            timed_out=False
            try:out,err=child.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
            seconds=time.perf_counter()-before
            (output/(label+'.stdout')).write_bytes(out);(output/(label+'.stderr')).write_bytes(err)
            try:decoded=json.loads(out)
            except (ValueError,UnicodeDecodeError):decoded=None
            if timed_out:status='NOT_SOLVED_EXTERNAL_TIMEOUT'
            elif child.returncode:status='EXECUTION_ERROR_NOT_EVALUATED'
            elif not isinstance(decoded,dict):status='NO_VALID_UPSTREAM_RESULT'
            elif decoded.get('failure'):status='UPSTREAM_REPORTED_FAILURE'
            elif decoded.get('unrealizable') is True:status='UPSTREAM_REPORTED_UNREALIZABLE'
            elif isinstance(decoded.get('solution'),str):status='UPSTREAM_REPORTED_REALIZABLE'
            else:status='UNCLASSIFIED_UPSTREAM_JSON'
            row={'label':label,'case_index':i,'path':case['path'],'repeat':repeat,
                 'command':command,'seconds':seconds,'timeout':timed_out,'exit_code':child.returncode,
                 'status':status,'upstream_result':decoded,
                 'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest(),
                 'independently_certified_original_task':False}
            rows.append(row)
            (output/'observations.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(json.dumps({k:row[k] for k in ['label','path','seconds','status']}),flush=True)
    report={'experiment_id':contract['experiment_id'],'status':'COMPLETE_UPSTREAM_INTEGRATION_ONLY',
            'workers':len(rows),'cases':len(contract['cases']),
            'status_counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
            'whole_seconds':time.perf_counter()-start,'registration_sha256':hashlib.sha256(data).hexdigest(),
            'runtime':runtime,'G0_passed':False,'G1_admitted':False,'learning_performed':False,'fresh_eligible':0}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({p.name:sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='runtime'}),flush=True)
