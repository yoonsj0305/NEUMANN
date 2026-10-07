"""Frozen metadata extraction from the complete verified DOI archive."""
from pathlib import Path
from collections import Counter
import hashlib,json,time,zipfile
import numpy as np
from neumann1.pickle_metadata import read,array,MetadataError,Call


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar(value):
    if isinstance(value,Call):
        data=array(value)
        if data.shape!=():raise MetadataError('Reference sum is not scalar')
        value=np.frombuffer(data.raw,dtype=data.dtype)[0].item()
    if type(value)is complex:return {'real':value.real,'imag':value.imag}
    if type(value)not in {bool,int,float}:raise MetadataError('Unsupported reference sum')
    return value


def extract(work):
    repo=Path(__file__).resolve().parents[1]
    prep=work/'Continuation/EINSUM_METADATA_RECOVERY_PREPARATION'
    registration=json.loads((prep/'registration.json').read_text())
    for name,h in registration['source_pins'].items():assert sha(repo/name)==h
    archive=work/'Continuation/EINSUM_OFFICIAL_ARCHIVE_FIRST/instances.zip'
    assert sha(archive)==registration['archive_sha256']
    target=work/'Continuation/EINSUM_METADATA_RECOVERY_FIRST';target.mkdir()
    start=time.perf_counter();records=[]
    with zipfile.ZipFile(archive)as z:
        files=[i for i in z.infolist() if i.filename in registration['members']];assert len(files)==5
        for item in files:
            folder=target/f'{len(records):03}';folder.mkdir()
            result={'member':item.filename,'bytes':item.file_size,'fresh_eligible':False,
                    'provided_paths_role':'O_OFFLINE_HEADROOM_OR_EXPLICIT_PRIOR_ASSET_NOT_POLICY_INPUT',
                    'provided_answer_role':'O_VERIFICATION_ONLY','arrays_role':'D_OPENED_PUBLIC_INPUT'}
            try:
                if item.file_size>registration['max_pickle_bytes']:raise MetadataError('Registered byte budget')
                raw=z.read(item);result['source_sha256']=hashlib.sha256(raw).hexdigest()
                root,symbols=read(raw,max_bytes=registration['max_pickle_bytes'],max_ops=registration['max_pickle_ops'],max_memo=registration['max_pickle_memo'])
                if type(root)is not tuple or len(root)!=4:raise MetadataError('Benchmark root must be four plain fields')
                equation,tensors,paths,answer=root
                if type(equation)is not str or type(tensors)is not list or type(paths)is not tuple or len(paths)!=2:raise MetadataError('Invalid benchmark root schema')
                decoded=[array(v)for v in tensors]
                if len(equation.split('->')[0].split(','))!=len(decoded):raise MetadataError('Equation/tensor arity differs')
                path_records=[]
                for p in paths:
                    if type(p)is not tuple or len(p)!=5 or type(p[0])is not list:raise MetadataError('Invalid path metadata')
                    if any(type(step)is not tuple or any(type(v)is not int for v in step)for step in p[0]):raise MetadataError('Invalid path steps')
                    path_records.append({'path':p[0],'author_max_intermediate_log2':p[1],
                                         'author_work_log10':p[2],'min_density':p[3],'avg_density':p[4],
                                         'global_optimality_assumed':False})
                result.update({'status':'NON_EXECUTING_METADATA_EXTRACTED','name':Path(item.filename).stem,
                    'equation':equation,'shapes':[list(v.shape)for v in decoded],
                    'arrays':[v.metadata()for v in decoded],
                    'provided_paths':{'opt_size':path_records[0],'opt_flops':path_records[1]},
                    'provided_result_sum':scalar(answer),'inert_globals_seen':symbols,
                    'pickle_callable_invoked':False,'numerical_task_executed':False})
            except Exception as error:
                result['status']='NOT_EXTRACTED';result['reason']=type(error).__name__+': '+str(error)
            (folder/'record.json').write_text(json.dumps(result,indent=2)+'\n')
            records.append(result)
            if len(records)%16==0:print(json.dumps({'completed':len(records),'counts':dict(Counter(r['status']for r in records))}),flush=True)
    report={'study':registration['study'],'records':records,'counts':dict(Counter(r['status']for r in records)),
            'seconds':time.perf_counter()-start,'pickle_executed':False,'numerical_tasks_executed':False,
            'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    (target/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (target/'manifest.json').write_text(json.dumps({p.relative_to(target).as_posix():sha(p)for p in sorted(target.rglob('*'))if p.is_file()},indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='records'},indent=2))
    print(json.dumps([{'member':r['member'],'reason':r['reason']}for r in records if r['status']=='NOT_EXTRACTED'],indent=2))


def prepare(work):
    repo=Path(__file__).resolve().parents[1];target=work/'Continuation/EINSUM_METADATA_RECOVERY_PREPARATION';target.mkdir()
    names=['neumann1/pickle_metadata.py','experiments/extract_einsum_metadata.py','experiments/recover_einsum_metadata.py']
    registration={'study':'OFFICIAL_EINSUM_NON_EXECUTING_BUDGET_RECOVERY_V1',
                  'source_pins':{n:sha(repo/n)for n in names},
                  'archive_sha256':'b65e9f8f80d27346442479311dbc295f29834481c3a07cb8cc7a438b8adbb82a',
                  'max_pickle_bytes':128*1024*1024,'max_pickle_ops':8_000_000,'max_pickle_memo':2_000_000,
                  'selection':'All five original Memo budget refusals; original 163/5 first record unchanged','members':[r['member'] for r in json.loads((work/'Continuation/EINSUM_METADATA_FIRST/report.json').read_text())['records'] if r['status']=='NOT_EXTRACTED'], 'original_first_report_sha256':sha(work/'Continuation/EINSUM_METADATA_FIRST/report.json'), 'old_first_refusals_replaced':False,
                  'numpy_reconstruction':'Explicit byte views with numeric dtype whitelist; no data callable invocation',
                  'fresh_eligible':0,'G0_passed':False,'G1_admitted':False}
    raw=(json.dumps(registration,indent=2)+'\n').encode();(target/'registration.json').write_bytes(raw)
    for n in names:
        p=target/'pinned'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((repo/n).read_bytes())
    (target/'freeze.json').write_text(json.dumps({'registration_sha256':hashlib.sha256(raw).hexdigest(),
             'source_pins':registration['source_pins'],'execution_started':False},indent=2)+'\n')
    print('FROZEN',hashlib.sha256(raw).hexdigest())


if __name__=='__main__':
    import sys
    work=Path(__file__).resolve().parents[3]
    prepare(work)if sys.argv[1:]==['prepare']else extract(work)
