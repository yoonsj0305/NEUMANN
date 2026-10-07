"""Separate Ubuntu Jsoncpp discovery repair; original first setup stays intact."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def repair(root):
    logs=root/'setup-jsoncpp-repair';assert not logs.exists();logs.mkdir()
    source=root/'source';manifest=json.loads((root/'original-source-manifest.json').read_text())
    patches=json.loads((root/'build-path-patches.json').read_text())
    allowed={p['path']:p['after_sha256'] for p in patches}
    assert {n:sha(source/n) for n,h in manifest.items() if sha(source/n)!=h}==allowed
    old=json.loads((root/'setup'/'events.json').read_text());assert old[-1]['exit_code']==1
    error=(root/'setup'/'05.stderr').read_text();assert 'Jsoncpp_INCLUDE_DIR-NOTFOUND' in error
    include=Path('/usr/include/jsoncpp');library=Path('/usr/lib/x86_64-linux-gnu/libjsoncpp.so')
    assert (include/'json'/'json.h').exists() and library.exists()
    events=[]
    def command(args,cwd,limit):
        index=len(events);start=time.perf_counter()
        child=subprocess.Popen(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        timeout=False
        try:out,err=child.communicate(timeout=limit)
        except subprocess.TimeoutExpired:timeout=True;os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
        (logs/f'{index:02}.stdout').write_bytes(out);(logs/f'{index:02}.stderr').write_bytes(err)
        event={'command':args,'cwd':str(cwd),'seconds':time.perf_counter()-start,'exit_code':child.returncode,'timeout':timeout,
               'stdout_sha256':sha(logs/f'{index:02}.stdout'),'stderr_sha256':sha(logs/f'{index:02}.stderr')}
        events.append(event);save(logs/'events.json',events);print(json.dumps(event),flush=True)
        assert child.returncode==0 and not timeout,'Retain repair failure; do not tune experiments'
        return out
    build=root/'build-jsoncpp';assert not build.exists();build.mkdir()
    command(['cmake',str(source/'src'),'-DJsoncpp_INCLUDE_DIR='+str(include),'-DJsoncpp_LIBRARY='+str(library)],build,300)
    command(['cmake','--build','.', '--parallel','2'],build,3000)
    executable=build/'executor'/'run';assert executable.exists()
    versions={name:command(args,root,30).decode().splitlines()[0] for name,args in [
       ('ocaml',['ocamlopt','-version']),('gcc',['g++','--version']),('cmake',['cmake','--version'])]}
    changes={n:sha(source/n) for n,h in manifest.items() if sha(source/n)!=h};assert changes==allowed
    report={'status':'BUILT_PINNED_SUFU_NON_GUROBI_ENVIRONMENT_REPAIR','executable':str(executable),'executable_sha256':sha(executable),
       'frontend_sha256':sha(source/'src'/'surface'/'f'),'versions':versions,
       'first_setup_failure_preserved':True,'repair':'CMake command receives installed Jsoncpp include/library paths;no source algorithm edits',
       'recorded_first_setup_seconds':sum(e['seconds'] for e in old),'recorded_repair_seconds':sum(e['seconds'] for e in events),
       'source_algorithm_changes':0,'build_path_files_modified':changes,'benchmarks_executed':False,
       'Gurobi_licensed_features_requested':False,'G0_passed':False,'G1_admitted':False,'fresh_eligible':0,'learning_performed':False}
    save(root/'build-repair-receipt.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':repair(Path(sys.argv[1]))
