"""Opened original-array CPU calibration, not full investment or G0 evidence."""
from pathlib import Path
import hashlib,json,math,random,time,zipfile
import numpy as np
from neumann1.pickle_metadata import read,array
from neumann1.contraction_structure import certify_path,public_plan,is_matrix_chain


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def agreement(a,b):
    a,b=np.asarray(a),np.asarray(b)
    return bool(a.shape==b.shape and np.isfinite(a).all()and np.isfinite(b).all()and np.allclose(a,b,rtol=1e-8,atol=0))
def original(raw):
    root,_=read(raw)
    if type(root)is not tuple or len(root)!=4 or type(root[0])is not str or type(root[1])is not list:raise ValueError('Original public data schema')
    numeric=[array(v)for v in root[1]]
    values=[np.frombuffer(v.raw,dtype=v.dtype).reshape(v.shape,order=v.order)for v in numeric]
    return root[0],values,[v.metadata()for v in numeric]


def prepare(work):
    from experiments.representation_headroom import package_identity
    repo=Path(__file__).resolve().parents[1];prep=work/'Continuation/EINSUM_ORIGINAL_KERNEL_PREPARATION';prep.mkdir()
    screen=work/'Continuation/EINSUM_FULL_SCREEN_FIRST';r=json.loads((screen/'report.json').read_text());meta=work/'Continuation/EINSUM_METADATA_FIRST/report.json'
    m={c.get('name'):c for c in json.loads(meta.read_text())['records']};archive=work/'Continuation/EINSUM_OFFICIAL_ARCHIVE_FIRST/instances.zip'
    assert sha(archive)=='b65e9f8f80d27346442479311dbc295f29834481c3a07cb8cc7a438b8adbb82a'
    selected=[];decisions=[]
    with zipfile.ZipFile(archive)as z:
        for c in r['cases']:
            eligible=bool(c['complete_native_comparison']and max(c[a]['certificate']['dense_arithmetic_work_model']for a in ['best_native','best_provided'])<=2_000_000_000 and max(c[a]['certificate']['largest_intermediate_elements']for a in ['best_native','best_provided'])<=8_000_000)
            decisions.append({'name':c['name'],'eligible':eligible,'selection':'complete model comparison AND both cheapest-work paths <=2G modeled work and <=8M peak elements'})
            if not eligible:continue
            n=len(selected);raw=z.read(m[c['name']]['member']);assert hashlib.sha256(raw).hexdigest()==m[c['name']]['source_sha256']
            p=prep/f'{n:03}.original.pkl';p.write_bytes(raw)
            value={'name':c['name'],'public':c['public'],'original_file':p.name,'original_sha256':sha(p),'metadata':m[c['name']]['arrays'],
                   'checksum':m[c['name']]['provided_result_sum'],'cached_native':c['best_native']['path'],
                   'provided_paths':{k:v['path']for k,v in m[c['name']]['provided_paths'].items()},
                   'previous_model_search_seconds':sum(e.get('launch_to_exit_seconds',0)for e in c['events']),
                   'prior_public_search_counted_separately':True,'provided_research_investment':'UNKNOWN_NOT_ZERO'}
            q=prep/f'{n:03}.json';save(q,value);selected.append({'file':q.name,'sha256':sha(q),'name':c['name']})
    names=['experiments/einsum_original_kernel.py','neumann1/pickle_metadata.py','neumann1/contraction_structure.py']
    reg={'study':'OFFICIAL_OPENED_ORIGINAL_TENSOR_CPU_CALIBRATION_V1','cases':selected,'all30_selection_decisions':decisions,
         'source_pins':{n:sha(repo/n)for n in names},'source_screen_sha256':sha(screen/'report.json'),
         'package_pins':{n:package_identity(n)for n in ['numpy','opt_einsum','threadpoolctl']},
         'repetitions':3,'query_factors':[1.0,1.01,0.99],'query_lineage':'q0 exact official arrays; q1/q2 derived by scaling first operand, not independent tasks',
         'routes':['CACHED_NATIVE','PUBLIC_GREEDY','PUBLIC_AUTO_HQ','PUBLIC_DP','FREE_OPT_FLOPS','FREE_OPT_SIZE'],
         'bounds':{'work':2_000_000_000,'peak_elements':8_000_000},'BLAS_threads':1,
         'reference':'full outputs from two independently index-certified provided paths; q0 sum against original author checksum; finite values and rtol1e-8, atol0',
         'timed_calibration':'route artifact access/discovery, certificate, compilation, scans, kernels, full output comparisons; within-process component only',
         'separate_costs':['original pickle decoding','derived query creation','reference execution','package imports/cold process','previous native discovery','provided-path research investment unknown'],
         'total_compute_advantage_claim':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False,'learning':False,'fresh_eligible':0}
    save(prep/'registration.json',reg);save(prep/'freeze.json',{'registration_sha256':sha(prep/'registration.json')})
    for n in names:
        p=prep/'pinned'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((repo/n).read_bytes())
    print('FROZEN',sha(prep/'registration.json'),'cases',len(selected))


def run(work):
    import opt_einsum as oe
    from threadpoolctl import threadpool_limits,threadpool_info
    from experiments.representation_headroom import package_identity
    repo=Path(__file__).resolve().parents[1];prep=work/'Continuation/EINSUM_ORIGINAL_KERNEL_PREPARATION';reg=json.loads((prep/'registration.json').read_text())
    assert sha(prep/'registration.json')==json.loads((prep/'freeze.json').read_text())['registration_sha256']
    for n,h in reg['source_pins'].items():assert sha(repo/n)==h
    for n,h in reg['package_pins'].items():assert package_identity(n)==h
    target=work/'Continuation/EINSUM_ORIGINAL_KERNEL_FIRST';target.mkdir();start=time.perf_counter();cases=[]
    with threadpool_limits(limits=1):
        pools=threadpool_info()
        for i,c in enumerate(reg['cases']):
            p=prep/c['file'];assert sha(p)==c['sha256'];v=json.loads(p.read_text());folder=target/f'{i:03}';folder.mkdir();t=time.perf_counter()
            source=prep/v['original_file'];assert sha(source)==v['original_sha256'];equation,base,metadata=original(source.read_bytes())
            assert metadata==v['metadata']and equation==v['public']['equation'];decode_seconds=time.perf_counter()-t;t=time.perf_counter()
            batches=[[base[0]*factor,*base[1:]]for factor in reg['query_factors']];derived_seconds=time.perf_counter()-t
            result={'name':c['name'],'decode_and_identity_seconds':decode_seconds,'derived_seconds':derived_seconds,
                    'previous_search_seconds':v['previous_model_search_seconds'],'provided_research_investment':'UNKNOWN','observations':[],'references':[]}
            refs=[];t=time.perf_counter();reference_ok=True
            for q,arrays in enumerate(batches):
                values=[]
                for label,path in v['provided_paths'].items():
                    cert=certify_path(v['public'],path)
                    if cert['dense_arithmetic_work_model']>reg['bounds']['work']or cert['largest_intermediate_elements']>reg['bounds']['peak_elements']:
                        reference_ok=False;result['references'].append({'query':q,'label':label,'status':'PREDECLARED_RESOURCE_EXCLUSION','certificate':cert});continue
                    y=np.asarray(oe.contract(equation,*arrays,optimize=[tuple(s)for s in path],backend='numpy'));np.save(folder/f'reference-{q}-{label}.npy',y,allow_pickle=False);values.append(y)
                valid=len(values)==2 and agreement(values[0],values[1]);reference_ok&=valid
                if q==0 and values:
                    checksum=v['checksum'];expected=complex(checksum['real'],checksum['imag'])if type(checksum)is dict else checksum
                    checksum_ok=agreement(np.asarray(values[0].sum()),np.asarray(expected));reference_ok&=checksum_ok
                else:checksum_ok=None
                result['references'].append({'query':q,'two_provided_full_outputs_agree':valid,'official_checksum_checked':q==0,'official_checksum_agrees':checksum_ok,
                                             'actual_first_operand_sha256':hashlib.sha256(np.ascontiguousarray(arrays[0]).tobytes()).hexdigest()})
                refs.append(values[0]if values else None)
            result['reference_seconds']=time.perf_counter()-t;result['reference_verified']=bool(reference_ok)
            if not reference_ok:
                result['status']='REFERENCE_NOT_VERIFIED_PRESERVED';save(folder/'record.json',result);cases.append(result);continue
            for repeat in range(reg['repetitions']):
                routes=list(reg['routes']);random.Random(6101100+repeat).shuffle(routes)
                for route in routes:
                    observation={'route':route,'repeat':repeat,'queries':[]};t=time.perf_counter()
                    if route=='PUBLIC_DP'and len(base)>16 and not is_matrix_chain(v['public']):
                        observation['status']='PREDECLARED_TOPOLOGY_EXCLUSION';result['observations'].append(observation);continue
                    try:
                        if route=='CACHED_NATIVE':
                            assert sha(p)==c['sha256'];path=v['cached_native']
                        elif route.startswith('FREE_'):path=v['provided_paths']['opt_flops'if route=='FREE_OPT_FLOPS'else'opt_size']
                        else:path=public_plan(v['public'],{'PUBLIC_GREEDY':'greedy','PUBLIC_AUTO_HQ':'auto-hq','PUBLIC_DP':'dynamic-programming'}[route])['path']
                        cert=certify_path(v['public'],path);observation.update(path=path,certificate=cert)
                        if cert['dense_arithmetic_work_model']>reg['bounds']['work']or cert['largest_intermediate_elements']>reg['bounds']['peak_elements']:
                            observation.update(status='PREDECLARED_RESOURCE_EXCLUSION',failed_seconds=time.perf_counter()-t);result['observations'].append(observation);continue
                        expression=oe.contract_expression(equation,*map(tuple,v['public']['shapes']),optimize=[tuple(s)for s in path]);observation['setup_seconds']=time.perf_counter()-t
                        for q,arrays in enumerate(batches):
                            t=time.perf_counter();finite=all(np.isfinite(a).all()for a in arrays);after_scan=time.perf_counter();y=np.asarray(expression(*arrays,backend='numpy'));after_kernel=time.perf_counter();valid=finite and agreement(y,refs[q]);after_check=time.perf_counter()
                            np.save(folder/f'{route}-{repeat}-{q}.npy',y,allow_pickle=False)
                            observation['queries'].append({'query':q,'scan_seconds':after_scan-t,'kernel_seconds':after_kernel-after_scan,'comparison_seconds':after_check-after_kernel,'full_output_agrees':bool(valid)})
                        observation['status']='VERIFIED_CALIBRATION_ONLY'if all(x['full_output_agrees']for x in observation['queries'])else'NUMERIC_DISAGREEMENT_PRESERVED'
                        observation['first_component_seconds']=observation['setup_seconds']+sum(observation['queries'][0][k]for k in ['scan_seconds','kernel_seconds','comparison_seconds'])
                        observation['three_components_seconds']=observation['setup_seconds']+sum(x[k]for x in observation['queries']for k in ['scan_seconds','kernel_seconds','comparison_seconds'])
                    except Exception as e:observation.update(status='ERROR_PRESERVED',reason=type(e).__name__+': '+str(e),failed_seconds=time.perf_counter()-t)
                    result['observations'].append(observation);save(folder/'record.json',result)
            result['status']='CALIBRATION_COMPLETED_WITH_ALL_EXCLUSIONS_PRESERVED';save(folder/'record.json',result);cases.append(result)
            print(json.dumps({'completed':len(cases),'name':c['name'],'reference_verified':reference_ok,'observations':len(result['observations'])}),flush=True)
    report={'study':reg['study'],'cases':cases,'case_count':len(cases),'whole_study_seconds':time.perf_counter()-start,'threadpools':pools,
            'official_original_array_checksums_checked':True,'two_provided_reference_paths_not_global_optimum':True,
            'measurements_are_within_process_components':True,'complete_investment_cost_measured':False,'cost_advantage_established':False,
            'learning_performed':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(target/'report.json',report);save(target/'manifest.json',{p.relative_to(target).as_posix():sha(p)for p in sorted(target.rglob('*'))if p.is_file()})
    print(json.dumps({k:v for k,v in report.items()if k not in {'cases','threadpools'}},indent=2),flush=True)


if __name__=='__main__':
    import sys
    work=Path(__file__).resolve().parents[3]
    prepare(work)if sys.argv[1]=='prepare'else run(work)
