"""Hash replay of first full-tool run; independent proof of adapted subset only."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.recursive_summary_replay import (independent_obligations,
    z3_expression, eval_program, mathematical_reference)
from neumann1.typed_fold_projection import project
from neumann1.synduce_solution import certify_solution


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path, value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def independently_execute(kernel, node):
    if node[0]=='nil':return list(kernel['empty'])
    if node[0]=='single':return eval_program(kernel['singleton'],[node[1]])
    assert node[0]=='concat' and len(node)==3
    return eval_program(kernel['merge'],independently_execute(kernel,node[1])+independently_execute(kernel,node[2]))


def independent_fold(public, values):
    state=list(public['empty'])
    for h in reversed(values):state=eval_program(public['step'],[h]+state)
    return state


def shaped(values, shape):
    if not values:return ['nil']
    if len(values)==1:return ['single',values[0]]
    cut=1 if shape=='RIGHT' else len(values)-1 if shape=='LEFT' else len(values)//2
    return ['concat',shaped(values[:cut],shape),shaped(values[cut:],shape)]


def audit(first, intake, output):
    import z3
    assert not output.exists()
    output.mkdir(parents=True)
    p=first/'extracted/baseline-first'
    archive=first/'NEUMANN_FULL_SYNDUCE_FIRST_RECORDS.zip'
    assert sha(archive)=='3aaa0dd4340a4d93180ad9814ffd4c9c5f3a254d2908385073c10a3b11c62276'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():assert (first/'extracted'/name).read_bytes()==z.read(name)
        archive_files=len(z.namelist())
    manifest=read(p/'manifest.json')
    assert all(sha(p/name)==digest for name,digest in manifest.items())
    contract=read(p/'preregister.json')
    assert sha(p/'preregister.json')=='3192a320a6b0758aabf729bcb7e67a209f13e37049b907d85f35d09392620921'
    assert sha(first/'extracted/frozen-baseline-code/synduce_full_baseline.py')=='e4a413744a995f91036e11436d3f645c63287d7c5faa2649c75908e1871fe908'
    assert sha(ROOT/'experiments/synduce_full_baseline.py')=='e4a413744a995f91036e11436d3f645c63287d7c5faa2649c75908e1871fe908'
    source_manifest=read(intake/'manifest.json')
    sources={row['path']:row for row in source_manifest['files']}
    assert contract['source_commit']==source_manifest['commit']
    report=read(p/'report.json');rows=read(p/'observations.json')
    assert len(rows)==87 and report['workers']==87 and report['cases']==29
    expected=[(i,r) for i in range(29) for r in range(3)]
    assert [(row['case_index'],row['repeat']) for row in rows]==expected
    counts=Counter();certified=[];proofs=0;serialized=0;numeric=0;unsupported=[]
    for row in rows:
        i,r=row['case_index'],row['repeat'];case=contract['cases'][i]
        assert row['label']==f'{i:02}-{r}' and row['path']==case['path']
        source_row=sources['benchmarks/'+row['path']]
        source_path=intake/'upstream'/source_row['local_path']
        assert sha(source_path)==case['source_sha256']==source_row['sha256']
        assert row['seconds']>=0
        stdout,stderr=p/(row['label']+'.stdout'),p/(row['label']+'.stderr')
        assert sha(stdout)==row['stdout_sha256'] and sha(stderr)==row['stderr_sha256']
        try:decoded=json.loads(stdout.read_bytes())
        except (ValueError,UnicodeDecodeError):decoded=None
        assert decoded==row['upstream_result']
        if row['timeout']:
            status='NOT_SOLVED_EXTERNAL_TIMEOUT';assert row['seconds']>=60 and row['exit_code']==-9
        elif row['exit_code']:
            status='EXECUTION_ERROR_NOT_EVALUATED'
        elif not isinstance(decoded,dict):status='NO_VALID_UPSTREAM_RESULT'
        elif decoded.get('failure'):status='UPSTREAM_REPORTED_FAILURE'
        elif decoded.get('unrealizable') is True:status='UPSTREAM_REPORTED_UNREALIZABLE'
        elif isinstance(decoded.get('solution'),str):status='UPSTREAM_REPORTED_REALIZABLE'
        else:status='UNCLASSIFIED_UPSTREAM_JSON'
        assert status==row['status']
        counts[status]+=1
        if status!='UPSTREAM_REPORTED_REALIZABLE':continue
        try:
            projection=project(source_path.read_text(encoding='utf-8'))
            result=certify_solution(projection['public'],decoded['solution'])
        except ValueError as error:
            unsupported.append({'label':row['label'],'path':row['path'],'status':'UNSUPPORTED_ADAPTER_NO_CLAIM','reason':str(error)})
            continue
        save(output/(row['label']+'.certificate.json'),{'projection':projection,'result':result})
        if not result['accepted']:
            unsupported.append({'label':row['label'],'path':row['path'],'status':result['status']})
            continue
        public,proposal,kernel=projection['public'],result['proposal'],result['kernel']
        own=independent_obligations(public,proposal)
        h=z3.Int('head')
        raw=eval_z3(kernel['singleton'],[h])
        step=eval_z3(kernel['step'],[h]+[z3.IntVal(e) for e in kernel['empty']])
        own['EMITTED_SINGLETON_BINDING']=z3.And(*[a==b for a,b in zip(raw,step)])
        for name,theorem in own.items():
            solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem))
            assert solver.check()==z3.unsat,(row['label'],name)
            proofs+=1
        queries=result['attempts'][-1]['certificate']['obligations']+[result['singleton_binding']]
        for query in queries:
            solver=z3.Solver();solver.set(timeout=2000);solver.from_string(query['smt2'])
            assert solver.check()==z3.unsat
            serialized+=1
        sequences=[list(xs) for n in range(5) for xs in itertools.product([-2,0,3],repeat=n)]
        sequences += [[10**80,-10**80,3],[-10**90,5,10**90]]
        for xs in sequences:
            reference=independent_fold(public,xs)
            if row['path'] in ['list/sum.ml','list/mps.ml','list/mts.ml']:
                assert reference==mathematical_reference(Path(row['path']).stem,xs)
            for shape in ['LEFT','RIGHT','BALANCED']:
                latent=independently_execute(kernel,shaped(xs,shape))
                assert eval_program(proposal['decode'],latent)==reference
                numeric+=1
        certified.append({'label':row['label'],'path':row['path'],'latent_width':len(kernel['empty'])})
    assert dict(counts)==report['status_counts']
    assert report['whole_seconds']>=sum(row['seconds'] for row in rows)
    events=read(first/'extracted/build-evidence/events.json')
    repairs=read(first/'extracted/build-evidence/compatibility-events.json')
    for prefix,records in [('step',events),('compat',repairs)]:
        for event in records:
            assert sha(first/f'extracted/build-evidence/{prefix}-{event["index"]:02}.log')==event['log_sha256']
    result={'status':'PASS_FIRST_HASH_AND_ADAPTED_KERNEL_AUDIT',
            'archive_files_checked':archive_files,'manifest_files_checked':len(manifest),
            'original_workers':len(rows),'original_status_counts':dict(counts),
            'original_whole_seconds':report['whole_seconds'],
            'original_worker_seconds_sum':sum(row['seconds'] for row in rows),
            'recorded_setup_command_seconds':sum(e['seconds'] for e in events+repairs),
            'certified_adapted_emitted_kernels':certified,'unsupported_or_uncertified':unsupported,
            'independent_Z3_AST_conditions':proofs,'serialized_CVC5_queries_replayed_Z3':serialized,
            'independent_numeric_constructor_checks':numeric,
            'original_task_protocol_independently_certified':False,
            'scope':'adapted mathematical fold only; source attributes, repr, target and machine overflow not replayed',
            'first_report_sha256':sha(p/'report.json'),'first_manifest_sha256':sha(p/'manifest.json'),
            'learning_performed':False,'headroom_claim':False,'G1_admitted':False,'fresh_eligible':0}
    save(output/'report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['certified_adapted_emitted_kernels','unsupported_or_uncertified']},indent=2))


def eval_z3(program,args):
    return [z3_expression(t,dict(zip(program['inputs'],args))) for t in program['outputs']]


if __name__=='__main__':audit(*(Path(a) for a in sys.argv[1:]))
