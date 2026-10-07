"""Build own input-only witness adapter against preserved upstream static libraries."""
from pathlib import Path
import hashlib,json,shlex,subprocess,time
ROOT=Path('/kaggle/working/neumann-sufu')
OUT=Path('/kaggle/working/neumann-resume/sufu-witness-build-first')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    assert(ROOT/'native-suite-first/report.json').exists(),'Do not run upstream frontend concurrently'
    OUT.mkdir()
    source=Path('/kaggle/working/neumann-resume/sufu_source_witness.cpp')
    make=ROOT/'build-jsoncpp/executor/CMakeFiles/run.dir'
    flags={line.split('=',1)[0].strip():shlex.split(line.split('=',1)[1])for line in(make/'flags.make').read_text().splitlines()if line.startswith('CXX_')}
    argv=shlex.split((make/'link.txt').read_text());command=[argv[0],*flags['CXX_DEFINES'],*flags['CXX_INCLUDES']]
    for token in argv[1:]:
        if token.startswith('-Wl,--dependency-file='):continue
        if token=='CMakeFiles/run.dir/run_incre_label.cpp.o':command.append(str(source))
        elif token=='run':command.append(str(OUT/'source-witness'))
        else:command.append(token)
    assert str(source)in command and str(OUT/'source-witness')in command
    before=time.perf_counter();child=subprocess.run(command,cwd=ROOT/'build-jsoncpp/executor',capture_output=True)
    elapsed=time.perf_counter()-before
    (OUT/'stdout').write_bytes(child.stdout);(OUT/'stderr').write_bytes(child.stderr)
    receipt={'status':'BUILT_OWN_NATIVE_WITNESS_ADAPTER'if child.returncode==0 else'BUILD_FAILED_PRESERVED',
             'command':command,'exit_code':child.returncode,'seconds':elapsed,'source_sha256':sha(source),
             'stdout_sha256':sha(OUT/'stdout'),'stderr_sha256':sha(OUT/'stderr'),
             'binary_sha256':sha(OUT/'source-witness')if(OUT/'source-witness').exists()else None,
             'upstream_algorithm_changes':0,'synthesis_run':False,'universal_equivalence_proven':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2));print(child.stderr.decode(errors='replace')[-5000:])


if __name__=='__main__':run()
