"""Prospective opened official-array shape screen, not a runtime/capability claim."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,os,random,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from neumann1.contraction_structure import validate_public,certify_path,public_plan,is_matrix_chain
from neumann1.cotengra_baseline import plan
from experiments.representation_headroom import package_identity


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def select(records):
    selected=[];decisions=[]
    for r in records:
        d={'member':r['member'],'status':'NOT_SELECTED','fresh_eligible':False}
        if r['status']!='NON_EXECUTING_METADATA_EXTRACTED':d['reason']='Original extraction refusal preserved'
        else:
            public={'equation':r['equation'],'shapes':r['shapes']}
            try:
                inputs,output,sizes=validate_public(public)
                total=sum(math.prod(s)for s in public['shapes']);volume=math.prod(sizes[k]for k in output)
                d.update(name=r['name'],operand_count=len(inputs),input_elements=total,output_elements=volume)
                if len(inputs)<=128 and total<=16_000_000 and volume<=1_000_000:
                    d['status']='PUBLIC_SHAPE_SELECTED';selected.append(r)
                else:d['reason']='Predeclared public shape budget'
            except ValueError as error:d['reason']='Public language refusal: '+str(error)
        decisions.append(d)
    return sorted(selected,key=lambda r:r['name']),decisions


def prepare(work):
    prep=work/'Continuation/EINSUM_FULL_SCREEN_PREPARATION';prep.mkdir()
    intake=work/'Continuation/EINSUM_METADATA_FIRST';report=json.loads((intake/'report.json').read_text())
    for n,h in json.loads((intake/'manifest.json').read_text()).items():assert sha(intake/n)==h
    selected,decisions=select(report['records'])
    old=work/'Continuation/STRUCTURAL_SCREEN_FIRST/cases'
    oldpaths=work/'Continuation/CONTRACTION_CHALLENGE_FIRST'
    cases=[]
    for i,r in enumerate(selected):
        public={'equation':r['equation'],'shapes':r['shapes']};prior=[]
        for f in old.glob('tensor_*.json'):
            source=json.loads(f.read_text())
            if source.get('public')!=public:continue
            for p in oldpaths.glob(f.stem+'_*.json'):
                v=json.loads(p.read_text())
                if v.get('status')=='CERTIFIED_MODEL_ONLY':
                    prior.append({'path':v['path'],'source':str(p),'sha256':sha(p),'role':'B_REUSABLE_PREVIOUS_PUBLIC_ONLY_PLAN'})
        value={'name':r['name'],'public':public,'provided_paths':r['provided_paths'],'prior_public_paths':prior,
               'source_sha256':r['source_sha256'],'source_member':r['member'],'fresh_eligible':False}
        p=prep/f'{i:03}.json';save(p,value)
        q=prep/f'{i:03}.public.json';save(q,public)
        cases.append({'file':p.name,'sha256':sha(p),'public_file':q.name,'public_sha256':sha(q),'name':r['name']})
    names=['experiments/einsum_full_model_screen.py','neumann1/contraction_structure.py','neumann1/cotengra_baseline.py','experiments/representation_headroom.py']
    reg={'study':'OFFICIAL_EINSUM_OPENED_STRONG_MODEL_SCREEN_V1','cases':cases,'selection_decisions':decisions,
         'selection':'All decoded original inputs with <=128 operands, <=16M input elements, <=1M output elements; public data only',
         'source_intake_report_sha256':sha(intake/'report.json'),'source_pins':{n:sha(ROOT/n)for n in names},
         'package_pins':{n:package_identity(n)for n in ['numpy','opt_einsum','cotengra','autoray']},
         'routes':['greedy','auto-hq','dynamic-programming','GREEDY128','RECONF32'],'seeds':[19,23,47],
         'timeout_seconds':20,'DP_eligibility':'<=16 operands or matrix chain; other cases marked ineligible before discovery',
         'execution':'Sequential fresh workers; model screening only; failed costs retained',
         'shortlist':'all eligible native workers complete, lowest modeled native work / lowest valid provided-path work >=10; provided peak no greater than native peak',
         'optimality':'Provided plans valid when certified, not globally optimal or free research investment',
         'fresh_eligible':0,'actual_tensor_execution':False,'G0_passed':False,'G1_admitted':False,'GPU':False}
    save(prep/'registration.json',reg);save(prep/'freeze.json',{'registration_sha256':sha(prep/'registration.json')})
    for n in names:
        p=prep/'pinned'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    print('FROZEN',sha(prep/'registration.json'),'CASES',len(cases),flush=True)


def worker(case,route,seed,target):
    public=json.loads(case.read_text());validate_public(public);begin=time.perf_counter();random.seed(seed)
    try:
        result=plan(public,route,seed)if route in {'GREEDY128','RECONF32'}else public_plan(public,route)
        result.update(status='CERTIFIED_DENSE_MODEL_ONLY',route=route,seed=seed)
    except Exception as e:result={'status':'FAILED','reason':type(e).__name__+': '+str(e),'route':route,'seed':seed}
    result['inside_worker_seconds']=time.perf_counter()-begin;save(target,result)


def run(work):
    prep=work/'Continuation/EINSUM_FULL_SCREEN_PREPARATION';reg=json.loads((prep/'registration.json').read_text())
    assert sha(prep/'registration.json')==json.loads((prep/'freeze.json').read_text())['registration_sha256']
    for n,h in reg['source_pins'].items():assert sha(ROOT/n)==h
    for n,h in reg['package_pins'].items():assert package_identity(n)==h
    target=work/'Continuation/EINSUM_FULL_SCREEN_FIRST';target.mkdir();save(target/'registration.json',reg)
    summaries=[];begin=time.perf_counter()
    for i,c in enumerate(reg['cases']):
        source=prep/c['file'];assert sha(source)==c['sha256'];value=json.loads(source.read_text());public=value['public']
        folder=target/f'{i:03}';folder.mkdir();native=[];supplied=[];events=[]
        for name,p in value['provided_paths'].items():
            try:supplied.append({'route':name,'path':p['path'],'certificate':certify_path(public,p['path']),'status':'CERTIFIED_DENSE_MODEL_ONLY','oracle':True})
            except Exception as e:events.append({'route':name,'status':'SUPPLIED_PATH_REFUSED','reason':str(e)})
        for p in value['prior_public_paths']:
            assert sha(Path(p['source']))==p['sha256']
            native.append({'route':'PRIOR_PUBLIC_PLAN','path':p['path'],'certificate':certify_path(public,p['path']),'status':'CERTIFIED_DENSE_MODEL_ONLY','prior_investment_counted_here':False})
        for route in reg['routes']:
            if route=='dynamic-programming'and len(public['shapes'])>16 and not is_matrix_chain(public):
                events.append({'route':route,'status':'PREDECLARED_INELIGIBLE'});continue
            for seed in reg['seeds']if route in {'GREEDY128','RECONF32'}else [19]:
                public_file=prep/c['public_file'];assert sha(public_file)==c['public_sha256']
                out=folder/f'{route}_{seed}.json';start=time.perf_counter();command=[sys.executable,'-X','utf8',str(Path(__file__).resolve()),'worker',str(public_file),route,str(seed),str(out)]
                try:
                    child=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=reg['timeout_seconds'],env={**os.environ,'PYTHONHASHSEED':'0','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
                    (folder/f'{route}_{seed}.stdout').write_bytes(child.stdout);(folder/f'{route}_{seed}.stderr').write_bytes(child.stderr)
                    event={'route':route,'seed':seed,'exit_code':child.returncode,'status':'FINISHED'if child.returncode==0 and out.exists()else'PROCESS_ERROR'}
                except subprocess.TimeoutExpired as e:
                    (folder/f'{route}_{seed}.stdout').write_bytes(e.stdout or b'');(folder/f'{route}_{seed}.stderr').write_bytes(e.stderr or b'');event={'route':route,'seed':seed,'status':'TIMEOUT'}
                event['launch_to_exit_seconds']=time.perf_counter()-start;events.append(event)
                if out.exists():
                    observation=json.loads(out.read_text());event['observation_status']=observation['status']
                    if event['status']=='FINISHED'and observation['status']=='CERTIFIED_DENSE_MODEL_ONLY':
                        assert certify_path(public,observation['path'])==observation['certificate'];native.append(observation)
                save(folder/'events.json',events)
        complete=all(e['status']=='PREDECLARED_INELIGIBLE'or(e['status']=='FINISHED'and e.get('observation_status')=='CERTIFIED_DENSE_MODEL_ONLY')for e in events)
        best=min(native,key=lambda v:v['certificate']['dense_arithmetic_work_model'])if native else None
        oracle=min(supplied,key=lambda v:v['certificate']['dense_arithmetic_work_model'])if supplied else None
        ratio=best['certificate']['dense_arithmetic_work_model']/oracle['certificate']['dense_arithmetic_work_model']if best and oracle else None
        result={'name':c['name'],'public':public,'complete_native_comparison':complete,'ratio_dense_model_only':ratio,
                'best_native':best,'best_provided':oracle,'native_plans':native,'provided_plans':supplied,'events':events,
                'remaining_model_shortlist':bool(complete and ratio is not None and ratio>=10 and oracle['certificate']['largest_intermediate_elements']<=best['certificate']['largest_intermediate_elements']),
                'measured_cost_advantage':False,'fresh_eligible':False}
        save(folder/'record.json',result);summaries.append(result)
        progress={'completed':len(summaries),'total':len(reg['cases']),'last':c['name'],'ratio_model_only':ratio,'complete':complete,'shortlist':result['remaining_model_shortlist']}
        with(target/'progress.jsonl').open('a')as f:f.write(json.dumps(progress)+'\n');f.flush();os.fsync(f.fileno())
        print(json.dumps(progress),flush=True)
    report={'study':reg['study'],'cases':summaries,'cases_count':len(summaries),'whole_screen_seconds':time.perf_counter()-begin,
            'model_shortlist':[x['name']for x in summaries if x['remaining_model_shortlist']],
            'all_original_intake_decisions':reg['selection_decisions'],'actual_tensor_execution':False,'dense_model_is_runtime':False,
            'cost_advantage_established':False,'learning_performed':False,'G0_passed':False,'G1_admitted':False,'G2_admitted':False,'fresh_eligible':0}
    save(target/'report.json',report);save(target/'manifest.json',{p.relative_to(target).as_posix():sha(p)for p in sorted(target.rglob('*'))if p.is_file()})
    print(json.dumps({k:v for k,v in report.items()if k not in {'cases','all_original_intake_decisions'}},indent=2),flush=True)


if __name__=='__main__':
    work=ROOT.parents[1]
    if sys.argv[1]=='prepare':prepare(work)
    elif sys.argv[1]=='run':run(work)
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),sys.argv[3],int(sys.argv[4]),Path(sys.argv[5]))
    else:raise ValueError('Explicit mode required')
