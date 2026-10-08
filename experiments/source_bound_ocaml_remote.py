"""Frozen CPU OCaml replay runner. No new learning/cost-headroom verdict."""
from collections import Counter
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time,zipfile


INPUT_PIN='4adef6a9e8bb535dd99258be903dde2a0e8f2c6f560d5619d6fbb273ea592ffa'


def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(path.read_bytes())
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def command(args,cwd,seconds):
    start=time.perf_counter();child=subprocess.Popen(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timeout=False
    try:stdout,stderr=child.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        timeout=True;os.killpg(child.pid,signal.SIGKILL);stdout,stderr=child.communicate()
    return {'command':args,'exit_code':child.returncode,'timeout':timeout,'seconds':time.perf_counter()-start},stdout,stderr


def parse_rows(stdout,spec):
    rows=[];seen=set();base=len(spec['alphabet'])
    for line in stdout.decode('utf-8').splitlines():
        key,original,native=line.split('|')
        length,code,shape=[int(i) for i in key.split(',')]
        assert 0<=length<=spec['max_length'] and 0<=code<base**length and shape in spec['shapes']
        assert (length,code,shape) not in seen;seen.add((length,code,shape))
        original=[int(i) for i in original.split(',')];native=[int(i) for i in native.split(',')]
        assert original==native
        rows.append({'length':length,'code':code,'shape':shape,'original':original,'native':native})
    assert len(rows)==spec['rows']
    return rows


def run(archive,output):
    assert sha(archive)==INPUT_PIN and not output.exists();output.mkdir(parents=True)
    entries={};duplicates=[]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for member in z.infolist():
            assert not member.is_dir() and '..' not in Path(member.filename).parts and not member.filename.startswith(('/','\\'))
            data=z.read(member)
            if member.filename in entries:
                assert data==entries[member.filename],'Duplicate member has inconsistent bytes'
                duplicates.append(member.filename)
            entries[member.filename]=data
    contract=json.loads(entries['remote-contract.json'])
    assert set(entries)=={'remote-contract.json',*contract['files']}
    assert all(digest(entries[path])==pin for path,pin in contract['files'].items())
    assert len(contract['cases'])==15
    start=time.perf_counter();events=[]
    save(output/'input-receipt.json',{'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,
         'duplicate_members':duplicates,'all_duplicate_member_bytes_equal':True,
         'handling':'all15 original source views retained;each worker gets separate index directory;no overwrite of first preparation',
         'unique_OCaml_program_files':len(contract['files'])})
    version,stdout,stderr=command(['opam','exec','--root=/kaggle/working/neumann-synduce/opam','--switch=neumann','--','ocamlopt','-version'],output,30)
    (output/'compiler-version.stdout').write_bytes(stdout);(output/'compiler-version.stderr').write_bytes(stderr)
    assert version['exit_code']==0 and stdout.decode().strip()=='5.0.0'
    save(output/'runtime.json',{'compiler_version':stdout.decode().strip(),'compiler_query':version,'gpu_requested':False,'platform':sys.platform,'python':sys.version})
    for index,case in enumerate(contract['cases']):
        label=f'{index:02}-{case["label"]}';worker=output/label;worker.mkdir()
        source=entries[case['ocaml_path']];assert digest(source)==case['ocaml_sha256']
        (worker/'main.ml').write_bytes(source)
        compile_args=['opam','exec','--root=/kaggle/working/neumann-synduce/opam','--switch=neumann','--','ocamlopt','-w','-a','main.ml','-o','run.bin']
        compilation,out,err=command(compile_args,worker,contract['compile_timeout_seconds'])
        (worker/'compile.stdout').write_bytes(out);(worker/'compile.stderr').write_bytes(err)
        event={'case_index':index,'label':label,'source_original':case['source']['path'],'source_sha256':case['source']['sha256'],
               'ocaml_sha256':case['ocaml_sha256'],'compilation':compilation,'status':'COMPILE_NOT_COMPLETED','rows':0,
               'original_hole_skeleton_implementable':case['original_hole_skeleton_implementable']}
        if compilation['exit_code']==0 and not compilation['timeout']:
            execution,out,err=command([str(worker/'run.bin')],worker,contract['run_timeout_seconds'])
            (worker/'run.stdout').write_bytes(out);(worker/'run.stderr').write_bytes(err)
            event['execution']=execution;event['binary_sha256']=sha(worker/'run.bin')
            try:
                assert execution['exit_code']==0 and not execution['timeout']
                rows=parse_rows(out,case['specification']);save(worker/'parsed-rows.json',rows)
                event['rows']=len(rows);event['status']='ACTUAL_OCAML_FINITE_GOALS_MATCHED'
            except (AssertionError,ValueError,UnicodeDecodeError) as error:
                event['status']='RUNTIME_OR_OUTPUT_NOT_VERIFIED';event['error']=str(error)
        events.append(event);save(output/'observations.json',events)
        print(json.dumps({k:event[k] for k in ['case_index','source_original','status','rows']}),flush=True)
    report={'experiment_id':contract['experiment_id'],'kind':'opened actual compiled OCaml finite fragment integration',
            'source_views':len(events),'distinct_source_byte_hashes':len({c['source']['sha256'] for c in contract['cases']}),
            'distinct_public_ASTs':len({c['public_AST_sha256'] for c in contract['cases']}),
            'status_counts':dict(Counter(e['status'] for e in events)),'original_and_native_output_rows':sum(e['rows'] for e in events),
            'whole_seconds':time.perf_counter()-start,'first_input_archive_sha256':INPUT_PIN,
            'all_machine_integers_proved':False,'original_entire_OCaml_protocol':False,'performance_headroom_claim':False,
            'G1_admitted':False,'G2_admitted':False,'fresh_eligible':0,'learning_performed':False}
    save(output/'report.json',report);save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':run(*(Path(p) for p in sys.argv[1:]))
