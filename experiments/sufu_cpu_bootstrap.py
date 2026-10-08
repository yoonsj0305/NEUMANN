"""Pinned SuFu artifact build on authorized Kaggle CPU, without licensed features.

Only the install-script's build paths are substituted. No core algorithm is
changed. Published caches stay historical, not newly executed measurements.
"""
from pathlib import Path
import hashlib,json,os,platform,signal,subprocess,sys,tarfile,time,urllib.request,zipfile

COMMIT='c2b3ff0637460c568b0533f992007278f88d0f55'
ARCHIVE_PIN='0eb8edd69373761be3052a5ab0e838335d75df21f807604907436492bf20878b'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def build(root):
    assert not root.exists();root.mkdir(parents=True);logs=root/'setup';logs.mkdir();events=[]
    save(root/'request.json',{'repository':'https://github.com/jiry17/SuFu','commit':COMMIT,'source_archive_sha256':ARCHIVE_PIN,
         'kind':'native baseline build only','Gurobi_licensed_features_requested':False,'GPU_requested':False,'G1_admitted':False,
         'python':sys.version,'platform':platform.platform(),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    def command(args,cwd,timeout=1200,extra_env=None):
        index=len(events);started=time.perf_counter();env=dict(os.environ)
        if extra_env:env.update(extra_env)
        child=subprocess.Popen(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        exceeded=False
        try:out,err=child.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            exceeded=True;os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
        (logs/f'{index:02}.stdout').write_bytes(out);(logs/f'{index:02}.stderr').write_bytes(err)
        event={'command':args,'cwd':str(cwd),'seconds':time.perf_counter()-started,'exit_code':child.returncode,'timeout':exceeded,
               'stdout_sha256':sha(logs/f'{index:02}.stdout'),'stderr_sha256':sha(logs/f'{index:02}.stderr')}
        events.append(event);save(logs/'events.json',events);print(json.dumps(event),flush=True)
        if child.returncode or exceeded:raise RuntimeError('Setup command failed; keep first logs, no silent retry')
        return out
    archive=root/'upstream.zip'
    with urllib.request.urlopen('https://codeload.github.com/jiry17/SuFu/zip/'+COMMIT,timeout=120) as response:data=response.read(64*1024*1024+1)
    assert len(data)<64*1024*1024;archive.write_bytes(data);assert sha(archive)==ARCHIVE_PIN
    source=root/'source';source.mkdir();manifest={}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and sum(i.file_size for i in z.infolist())<128*1024*1024
        prefix='SuFu-'+COMMIT+'/'
        for member in z.infolist():
            assert member.filename.startswith(prefix)
            rel=member.filename[len(prefix):]
            if not rel or member.is_dir():continue
            dest=(source/rel).resolve();assert dest.is_relative_to(source.resolve())
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(member))
            dest.chmod(0o755 if (member.external_attr>>16)&0o111 else 0o644);manifest[rel]=sha(dest)
    assert len(manifest)==1953;save(root/'original-source-manifest.json',manifest)
    command(['apt-get','update'],root,900)
    command(['apt-get','install','-y','ocaml','ocaml-findlib','libyojson-ocaml-dev','libjsoncpp-dev',
             'libgoogle-glog-dev','libgflags-dev','pkg-config'],root,1200,{'DEBIAN_FRONTEND':'noninteractive'})
    deps=root/'dependencies';deps.mkdir();wheels=deps/'wheels';wheels.mkdir()
    command([sys.executable,'-m','pip','download','--no-deps','--dest',str(wheels),'z3-solver==4.13.0.0'],root,300)
    wheel=list(wheels.glob('*.whl'));assert len(wheel)==1;z3_target=deps/'z3-wheel'
    command([sys.executable,'-m','pip','install','--no-deps','--target',str(z3_target),str(wheel[0])],root,300)
    z3_root=deps/'z3-layout';(z3_root/'src'/'api').mkdir(parents=True)
    (z3_root/'src'/'api'/'c++').symlink_to(z3_target/'z3'/'include',target_is_directory=True)
    (z3_root/'src'/'api'/'c').symlink_to(z3_target/'z3'/'include',target_is_directory=True)
    (z3_root/'build').symlink_to(z3_target/'z3'/'lib',target_is_directory=True)
    # The author-supported --use_gurobi=false mode still links vendor libraries.
    # No license acquisition, registration, terms UI or licensed solver is used.
    gurobi_archive=deps/'gurobi9.1.2_linux64.tar.gz'
    with urllib.request.urlopen('https://packages.gurobi.com/9.1/gurobi9.1.2_linux64.tar.gz',timeout=120) as response:data=response.read(256*1024*1024+1)
    assert len(data)<256*1024*1024;gurobi_archive.write_bytes(data)
    with tarfile.open(gurobi_archive,'r:gz') as archive_handle:
        members=archive_handle.getmembers();assert sum(m.size for m in members)<1024*1024*1024
        for member in members:
            dest=(deps/member.name).resolve();assert dest.is_relative_to(deps.resolve())
            if member.issym() or member.islnk():
                link=(dest.parent/member.linkname).resolve() if member.issym() else (deps/member.linkname).resolve()
                assert link.is_relative_to(deps.resolve())
        archive_handle.extractall(deps,filter='data')
    gurobi=deps/'gurobi912'/'linux64'
    replacements={'src/CMakeLists.txt':{'Z3PATH':str(z3_root),'GUROBIPATH':str(gurobi)},
      'src/basic/config.cpp':{'SOURCEPATH':json.dumps(str(source/'src'))},
      'exp/python/config.py':{'SUFUPATH':json.dumps(str(source))}}
    patches=[]
    for name,mapping in replacements.items():
        path=source/name;before=path.read_text();after=before
        for old,new in mapping.items():assert old in after;after=after.replace(old,new)
        path.write_text(after);patches.append({'path':name,'before_sha256':manifest[name],'after_sha256':sha(path),'substitutions':mapping,'kind':'author install build-path substitutions only'})
    save(root/'build-path-patches.json',patches)
    save(root/'dependency-archives.json',{'z3_version':'4.13.0.0','wheel':wheel[0].name,'wheel_sha256':sha(wheel[0]),
      'gurobi_version':'9.1.2','gurobi_archive_sha256':sha(gurobi_archive),'Gurobi_licensed_solver_used':False})
    command(['make','-j','2'],source/'src'/'surface',600)
    build_dir=root/'build';build_dir.mkdir();command(['cmake',str(source/'src')],build_dir,300)
    command(['cmake','--build','.', '--parallel','2'],build_dir,3000)
    executable=build_dir/'executor'/'run';assert executable.is_file()
    versions={}
    for name,args in [('ocaml',['ocamlopt','-version']),('gcc',['g++','--version']),('cmake',['cmake','--version'])]:
        versions[name]=command(args,root,30).decode().splitlines()[0]
    source_changes={n:sha(source/n) for n,pin in manifest.items() if sha(source/n)!=pin}
    assert set(source_changes)==set(replacements)
    receipt={'status':'BUILT_PINNED_SUFU_SUPPORTED_NON_GUROBI_MODE','executable_sha256':sha(executable),
      'frontend_sha256':sha(source/'src'/'surface'/'f'),'versions':versions,'recorded_setup_command_seconds':sum(e['seconds'] for e in events),
      'source_algorithm_changes':0,'build_path_files_modified':source_changes,'benchmarks_executed':False,
      'G0_passed':False,'G1_admitted':False,'fresh_eligible':0,'learning_performed':False}
    save(root/'build-receipt.json',receipt);print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':build(Path(sys.argv[1]))
