"""Complete operational native/free cost on all certified opened references.

Free valid summaries are not globally optimal Oracles or learned discoveries.
Huge expanded list sizes are semantic lengths, never reported speedup ratios.
"""
from time import perf_counter
BOOT=perf_counter()
from pathlib import Path
import argparse,hashlib,json,math,platform,random,statistics,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from neumann1.recursive_summary import identity
from neumann1.recursive_dag import CertifiedDagSummary,validate_dag
from neumann1.recursive_library_baseline import propose as library
from neumann1.finite_response_baseline import propose as finite_response
from neumann1.recursive_summary_data import problem_view
from neumann1.structural_data_rights import load_json_view

ROUTES=['PUBLIC_GENERATIVE_NATIVE','FREE_VALID_REFERENCE']
SOURCES=['experiments/compressed_recursive_cost.py','neumann1/recursive_dag.py',
         'neumann1/recursive_summary.py','neumann1/recursive_library_baseline.py',
         'neumann1/finite_response_baseline.py','neumann1/recursive_summary_data.py',
         'neumann1/structural_data_rights.py','experiments/recursive_summary_replay.py']


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def make_query(seed,index):
    rng=random.Random(seed);values=[rng.randint(-9,9) for _ in range(5)]
    nodes=[['nil']]+[['single',h] for h in values]
    pool=list(range(1,6))
    while len(pool)>1:
        a,b=pool.pop(0),pool.pop(0);nodes.append(['concat',a,b]);pool.append(len(nodes)-1)
    block=pool[0];root=block
    exponent=[60,8,14,22,30,46,60][index%7]
    for _ in range(exponent):nodes.append(['concat',root,root]);root=len(nodes)-1
    # Distinct ordered tails and shared subgraphs across actual requests.
    nodes.append(['concat',root,block] if index%2 else ['concat',block,root])
    return {'semantics':'ordered_integer_list_dag','nodes':nodes,'roots':[len(nodes)-1]}


def independent_query(proposal,query):
    from experiments.recursive_summary_replay import eval_program
    validate_dag(query);states=[]
    for node in query['nodes']:
        if node[0]=='nil':state=list(proposal['empty'])
        elif node[0]=='single':state=eval_program(proposal['step'],[node[1]]+proposal['empty'])
        else:state=eval_program(proposal['merge'],states[node[1]]+states[node[2]])
        states.append(state)
    return [eval_program(proposal['decode'],states[r]) for r in query['roots']]


def freeze(portfolio,preparation):
    assert not preparation.exists();preparation.mkdir(parents=True)
    assert sha(portfolio/'report.json')=='804b51bc3c09b89087a4384c194b59aeb22d604044a0304d2998551a6c8af097'
    assert sha(portfolio/'manifest.json')=='855b0ff97e0e45c32801b06644a4ebb1d8c4dbe02b64de66167af3e0afaf2654'
    assert all(sha(portfolio/p)==h for p,h in read(portfolio/'manifest.json').items())
    registry=read(portfolio/'registry.json')
    keys=sorted({k.split('/')[0] for k in registry['offline']})
    assert len(keys)==20
    contract={'experiment_id':'COMPRESSED_RECURSIVE_COMPLETE_COST_V1','cases':keys,
              'routes':ROUTES,'repetitions':3,'reuse_counts':[1,16],
              'worker_timeout_seconds':15,'seed_base':91340000,
              'source_portfolio_report_sha256':sha(portfolio/'report.json'),
              'source_portfolio_manifest_sha256':sha(portfolio/'manifest.json'),
              'selection':'all20 previously certified opened ASTs;7 unsupported ASTs remain outside this restricted cost scope,not globally rejected',
              'primary_cost':'parent process launch through exit,reading outputs and full exact goal comparison; includes imports,reads,generation,proof,actual query execution,writes',
              'native_rights':'public recurrence only;known monoid/map/permutation/direct-product and generated finite response;same common verifier/DAG compiler/query reuse',
              'free_rights':'offline valid proposal supplied;same verifier/DAG compiler/query reuse;only discovery omitted,not globally optimal',
              'query_scope':'compact shared ordered DAGs,actual differing heads/edges;1 or16 actual queries;unfolded lengths are not speedup denominators',
              'proof_reuse':'certify same original program once per worker,then execute actual differing DAG inputs for both routes',
              'qualification':'all3 workers and allactual queries correct percase/regime;native+free both mustqualify;failures charged and retained',
              'rule':{'geometric_mean_at_least':10,'individual_wins_at_least':16,'case_count':20,'both_regimes_required':True,'all_cases_evaluable':True},
              'positive':'ONE_DOMAIN_VALID_REFERENCE_HEADROOM_ONLY_NOT_G1_ADMISSION',
              'negative':'NO_10X_IN_REGISTERED_COMPRESSED_REFERENCES','incomplete':'INCOMPLETE_NO_ADMISSION',
              'original_goal_check':'universal adapted-fold certificate plus independently interpreted reference;large DAGs not physically unfolded',
              'prior_exposure':'all source/projections/native proposals and small unit DAG fixtures opened before freeze',
              'offline_investment':'source intake/build/library/proposal inventory priorcost preserved,query/expected construction separately timed;research labour and upstream algorithm creation UNKNOWN,never zero',
              'resources':'operational CPU wall seconds only;FLOPs/energy/money/peak memory UNKNOWN',
              'fresh_eligible':0,'independent_domains':1,'G1_admitted':False,'G2_admitted':False,'learning_performed':False,
              'sources':{p:sha(ROOT/p) for p in SOURCES},'prepared_assets':{}}
    start=perf_counter();assets={};expected={}
    for index,key in enumerate(keys):
        public=problem_view(portfolio,registry['public'][key]);save(preparation/'public'/(key+'.json'),public)
        choices=[(name,asset) for name,asset in registry['offline'].items() if name.startswith(key+'/')]
        name,asset=sorted(choices,key=lambda item:item[0])[0]
        found=load_json_view(portfolio,asset,'offline_oracle')
        save(preparation/'offline'/(key+'.json'),{'proposal':found['proposal'],'source_native_route':name})
        queries=[make_query(contract['seed_base']+index*100+i,i) for i in range(16)]
        assert len({identity(q) for q in queries})==16
        expected[key]=[independent_query(found['proposal'],q) for q in queries]
        for count in contract['reuse_counts']:save(preparation/'queries'/key/(str(count)+'.json'),queries[:count])
        assets[key]={'public':{**registry['public'][key],'path':'public/'+key+'.json','sha256':sha(preparation/'public'/(key+'.json'))},
                     'offline':{**asset,'path':'offline/'+key+'.json','sha256':sha(preparation/'offline'/(key+'.json'))}}
    save(preparation/'assets.json',assets);save(preparation/'expected.json',expected)
    contract['offline_query_and_expected_construction_seconds']=perf_counter()-start
    contract['prepared_assets']={str(p.relative_to(preparation)):sha(p) for p in preparation.rglob('*') if p.is_file()}
    save(preparation/'preregister.json',contract)
    for name in SOURCES:
        dest=preparation/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    save(preparation/'freeze.json',{'registration_sha256':sha(preparation/'preregister.json'),'performance_started':False})
    print(sha(preparation/'preregister.json'),flush=True)


def worker(preparation,key,route,count,output):
    output.mkdir(parents=True,exist_ok=False)
    asset=read(preparation/'assets.json')[key]
    public=problem_view(preparation,asset['public'])
    queries=read(preparation/'queries'/key/(str(count)+'.json'))
    assert len(queries)==count
    progress={'phase':'inputs_loaded','oracle_used':route=='FREE_VALID_REFERENCE','route':route,'case':key}
    save(output/'progress.json',progress);before=perf_counter()
    if route=='FREE_VALID_REFERENCE':proposal=load_json_view(preparation,asset['offline'],'offline_oracle')['proposal']
    else:
        assert route=='PUBLIC_GENERATIVE_NATIVE'
        found=library(public)
        if found is None:found=finite_response(public)
        assert found is not None,'Native bounded generator abstained'
        proposal=found['proposal']
        progress['native_mechanism']=found['mechanism']
    generation_seconds=perf_counter()-before
    save(output/'proposal.json',proposal);progress['phase']='proposal_generated';save(output/'progress.json',progress)
    before=perf_counter();engine=CertifiedDagSummary(public,proposal);build_seconds=perf_counter()-before
    save(output/'certificate.json',engine.certificate)
    rows=[]
    for i,query in enumerate(queries):
        before=perf_counter();result=engine.run_dag(query)
        rows.append({'index':i,'query_sha256':identity(query),'seconds':perf_counter()-before,'result':result})
    save(output/'result.json',{'route':route,'case':key,'count':count,'generation_seconds':generation_seconds,
                            'certificate_and_engine_seconds':build_seconds,'queries':rows,
                            'entry_through_saved_queries_seconds':perf_counter()-BOOT,
                            'neural_forward_calls':0,'learning_performed':False,'oracle_used':route=='FREE_VALID_REFERENCE'})


def summarize(rows,contract):
    regimes={}
    for count in contract['reuse_counts']:
        cases=[]
        for key in contract['cases']:
            times={}
            for route in contract['routes']:
                selected=[r for r in rows if r['case']==key and r['route']==route and r['count']==count and r['accepted']]
                if len(selected)==3:times[route]=statistics.median(r['complete_operational_seconds'] for r in selected)
            qualified=all(r in times for r in ROUTES)
            ratio=times[ROUTES[0]]/times[ROUTES[1]] if qualified else None
            cases.append({'case':key,'qualified':qualified,'median_seconds':times,'native_over_free':ratio})
        complete=all(c['qualified'] for c in cases)
        mean=math.exp(statistics.mean(math.log(c['native_over_free']) for c in cases)) if complete else None
        wins=sum(c['native_over_free']>=10 for c in cases if c['qualified'])
        passed=complete and mean>=10 and wins>=16
        regimes[str(count)]={'cases':cases,'all_evaluable':complete,'geometric_mean_native_over_free':mean,'10x_wins':wins,'passed':passed}
    complete=all(r['all_evaluable'] for r in regimes.values())
    decision=contract['incomplete'] if not complete else contract['positive'] if all(r['passed'] for r in regimes.values()) else contract['negative']
    return {'decision':decision,'regimes':regimes,'G1_admitted':False,'fresh_eligible':0,'learning_performed':False}


def run(preparation,output):
    contract=read(preparation/'preregister.json')
    assert sha(preparation/'preregister.json')==read(preparation/'freeze.json')['registration_sha256']
    assert all(sha(ROOT/p)==h==sha(preparation/'source'/p) for p,h in contract['sources'].items())
    assert all(sha(preparation/p)==h for p,h in contract['prepared_assets'].items())
    assert not output.exists();output.mkdir(parents=True)
    (output/'preregister.json').write_bytes((preparation/'preregister.json').read_bytes())
    save(output/'runtime.json',{'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),'executable':sys.executable,'gpu_requested':False})
    expected=read(preparation/'expected.json');events=[];start=perf_counter();rng=random.Random(119310)
    for key in contract['cases']:
        for count in contract['reuse_counts']:
            for repeat in range(3):
                routes=list(ROUTES);rng.shuffle(routes)
                for route in routes:
                    label=f'{key[:12]}-{count}-{repeat}-{route}'
                    dest=output/'workers'/label
                    command=[sys.executable,'-X','utf8',str(ROOT/'experiments/compressed_recursive_cost.py'),'worker',str(preparation),key,route,str(count),str(dest)]
                    before=perf_counter();timeout=False
                    try:
                        child=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=contract['worker_timeout_seconds'])
                        stdout,stderr=child.stdout,child.stderr;code=child.returncode
                    except subprocess.TimeoutExpired as error:
                        timeout=True;stdout=error.stdout or b'';stderr=error.stderr or b'';code=None
                    accepted=False;error=None;result=None
                    try:
                        assert not timeout and code==0,'worker did not complete'
                        result=read(dest/'result.json')
                        assert len(result['queries'])==count
                        for i,q in enumerate(result['queries']):
                            assert q['index']==i and q['result']['outputs']==expected[key][i],'original goal comparison failed'
                        accepted=True
                    except (AssertionError,OSError,ValueError) as exc:error=str(exc)
                    seconds=perf_counter()-before
                    (output/(label+'.stdout')).write_bytes(stdout);(output/(label+'.stderr')).write_bytes(stderr)
                    row={'case':key,'route':route,'count':count,'repeat':repeat,'worker':str(dest.relative_to(output)),
                         'complete_operational_seconds':seconds,'accepted':accepted,'timeout':timeout,'exit_code':code,'error':error,
                         'all_goal_outputs_checked':count if accepted else 0}
                    events.append(row);save(output/'observations.json',events)
                    print(json.dumps({k:row[k] for k in ['case','route','count','repeat','complete_operational_seconds','accepted','error']}),flush=True)
    analysis=summarize(events,contract)
    report={'experiment_id':contract['experiment_id'],'status':'COMPLETE_OPERATIONAL_COST_SCREEN',
            'workers':len(events),'accepted_workers':sum(e['accepted'] for e in events),
            'actual_queries_checked':sum(e['all_goal_outputs_checked'] for e in events),'distinct_requests':20*16,
            'whole_seconds':perf_counter()-start,'registration_sha256':sha(preparation/'preregister.json'),
            'analysis':analysis,'source_scope':'20 opened adapted ASTs,one domain;7 unqualified source projections remain unresolved',
            'free_reference_is_globally_optimal':False,'expanded_lengths_are_speedup_ratios':False,
            'total_R_and_D_cost_known':False,'FLOPs_energy_money_peak_memory':'UNKNOWN',
            'G1_admitted':False,'G2_admitted':False,'fresh_eligible':0,'learning_performed':False}
    save(output/'report.json',report)
    save(output/'manifest.json',{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()})
    print(json.dumps({k:v for k,v in report.items() if k!='analysis'},indent=2),flush=True)
    print(json.dumps({count:{k:v for k,v in row.items() if k!='cases'} for count,row in analysis['regimes'].items()},indent=2),flush=True)


if __name__=='__main__':
    mode,*args=sys.argv[1:]
    if mode=='freeze':freeze(*(Path(a) for a in args))
    elif mode=='run':run(*(Path(a) for a in args))
    elif mode=='worker':worker(Path(args[0]),args[1],args[2],int(args[3]),Path(args[4]))
    else:raise ValueError('Unknown mode')
