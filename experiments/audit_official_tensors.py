"""Independent index/cost reconstruction and retained original-array checks."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,statistics,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from neumann1.pickle_metadata import read as inert_read,array

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def manifest(root):
    m=load(root/'manifest.json')
    for n,h in m.items():assert sha(root/n)==h,(root,n)
    return len(m)
def registration(prep):
    r=load(prep/'registration.json');assert sha(prep/'registration.json')==load(prep/'freeze.json')['registration_sha256']
    for n,h in r['source_pins'].items():assert sha(ROOT/n)==h==sha(prep/'pinned'/n)
    from experiments.representation_headroom import package_identity
    for n,pin in r['package_pins'].items():assert package_identity(n)==pin
    return r

def independent_path(public,path,cert):
    """Recompute surviving indices from unselected operands, without shared certifier."""
    inputs,out=public['equation'].split('->');terms=inputs.split(',');sizes={}
    for term,shape in zip(terms,public['shapes']):
        assert len(term)==len(shape)
        for k,v in zip(term,shape):assert k not in sizes or sizes[k]==v;sizes[k]=v
    active=list(map(frozenset,terms));goal=frozenset(out);work=0;peak=0;witness=[]
    for step in path:
        assert len(step)==len(set(step))and all(type(i)is int and 0<=i<len(active)for i in step)
        chosen=[active[i]for i in step];remaining=[v for i,v in enumerate(active)if i not in step]
        allchosen=frozenset().union(*chosen);needed=goal.union(*remaining)
        keep=allchosen&needed;removed=allchosen-keep
        operations=math.prod(sizes[k]for k in allchosen)*(max(1,len(step)-1)+bool(removed))
        volume=math.prod(sizes[k]for k in keep);work+=operations;peak=max(peak,volume)
        witness.append({'consumed':step,'kept':sorted(keep),'summed':sorted(removed),'dense_work':operations,'intermediate_elements':volume})
        active=remaining+[keep]
    assert active==[goal] and work==cert['dense_arithmetic_work_model']and peak==cert['largest_intermediate_elements']
    assert witness==cert['witness'] and cert['ordered_output']==out and cert['accepted']
    return work,peak

def agree(a,b):
    return bool(a.shape==b.shape and np.isfinite(a).all()and np.isfinite(b).all()and np.all(np.abs(a-b)<=1e-8*np.abs(b)))

def run(work):
    prep=work/'Continuation/EINSUM_FULL_SCREEN_PREPARATION';reg=registration(prep)
    first=work/'Continuation/EINSUM_FULL_SCREEN_FIRST';screen=load(first/'report.json');screenfiles=manifest(first)
    intake=work/'Continuation/EINSUM_METADATA_FIRST';assert sha(intake/'report.json')==reg['source_intake_report_sha256']
    decisions=[]
    for r in load(intake/'report.json')['records']:
        if r['status']!='NON_EXECUTING_METADATA_EXTRACTED':continue
        terms,out=r['equation'].split('->');dims={k:d for t,s in zip(terms.split(','),r['shapes'])for k,d in zip(t,s)}
        eligible=len(r['shapes'])<=128 and sum(math.prod(s)for s in r['shapes'])<=16_000_000 and math.prod(dims[k]for k in out)<=1_000_000
        if eligible:decisions.append(r['name'])
    assert sorted(decisions)==[c['name']for c in reg['cases']]
    events=Counter();checked_paths=0;shortlist=[];modelsummary=[]
    for i,(c,r)in enumerate(zip(reg['cases'],screen['cases'])):
        assert sha(prep/c['file'])==c['sha256'];assert sha(prep/c['public_file'])==c['public_sha256']
        public=load(prep/c['public_file']);assert set(public)=={'equation','shapes'}and public==r['public']
        assert r==load(first/f'{i:03}/record.json');assert r['events']==load(first/f'{i:03}/events.json')
        for plan in r['native_plans']+r['provided_plans']:independent_path(public,plan['path'],plan['certificate']);checked_paths+=1
        for e in r['events']:
            events[e['status']]+=1
            if e['status']=='FINISHED':
                p=first/f'{i:03}'/(e['route']+'_'+str(e['seed'])+'.json');a=load(p)
                assert a['status']==e['observation_status']=='CERTIFIED_DENSE_MODEL_ONLY'
                independent_path(public,a['path'],a['certificate']);checked_paths+=1
        complete=all(e['status']=='PREDECLARED_INELIGIBLE'or(e['status']=='FINISHED'and e.get('observation_status')=='CERTIFIED_DENSE_MODEL_ONLY')for e in r['events'])
        assert complete==r['complete_native_comparison']
        native=min(r['native_plans'],key=lambda p:p['certificate']['dense_arithmetic_work_model'])
        oracle=min(r['provided_plans'],key=lambda p:p['certificate']['dense_arithmetic_work_model'])
        assert native==r['best_native']and oracle==r['best_provided']
        ratio=native['certificate']['dense_arithmetic_work_model']/oracle['certificate']['dense_arithmetic_work_model']
        assert ratio==r['ratio_dense_model_only']
        keep=complete and ratio>=10 and oracle['certificate']['largest_intermediate_elements']<=native['certificate']['largest_intermediate_elements']
        assert keep==r['remaining_model_shortlist']
        if keep:shortlist.append(c['name'])
        modelsummary.append({'name':c['name'],'complete':complete,'dense_model_ratio':ratio})
    assert shortlist==screen['model_shortlist']==[]
    kp=work/'Continuation/EINSUM_ORIGINAL_KERNEL_PREPARATION';kr=registration(kp)
    assert sha(first/'report.json')==kr['source_screen_sha256']
    kf=work/'Continuation/EINSUM_ORIGINAL_KERNEL_FIRST';kernel=load(kf/'report.json');kernelfiles=manifest(kf)
    counts=Counter();numeric=0;references=0;matrixchecks=0;ratios=[]
    assert len(kr['cases'])==len(kernel['cases'])==4
    assert not agree(np.zeros(1),np.array([1e-200]))
    assert not agree(np.zeros(1),np.zeros((1,1)))and not agree(np.array([np.inf]),np.array([np.inf]))
    for i,(c,r)in enumerate(zip(kr['cases'],kernel['cases'])):
        p=kp/c['file'];assert sha(p)==c['sha256'];v=load(p);folder=kf/f'{i:03}';assert r==load(folder/'record.json')
        assert sha(kp/v['original_file'])==v['original_sha256']
        raw,_=inert_read((kp/v['original_file']).read_bytes());assert raw[0]==v['public']['equation']
        decoded=[array(a)for a in raw[1]];assert [a.metadata()for a in decoded]==v['metadata']
        base=[np.frombuffer(a.raw,dtype=a.dtype).reshape(a.shape,order=a.order)for a in decoded]
        for q,factor in enumerate(kr['query_factors']):
            arrays=[base[0]*factor,*base[1:]]
            a=np.load(folder/f'reference-{q}-opt_size.npy',allow_pickle=False);b=np.load(folder/f'reference-{q}-opt_flops.npy',allow_pickle=False)
            assert agree(a,b);references+=2
            if q==0:
                expected=v['checksum'];expected=complex(expected['real'],expected['imag'])if type(expected)is dict else expected
                assert agree(np.asarray(a.sum()),np.asarray(expected))
            observed=r['references'][q];assert observed['actual_first_operand_sha256']==hashlib.sha256(np.ascontiguousarray(arrays[0]).tobytes()).hexdigest()
            if c['name']=='str_matrix_chain_multiplication_100':
                from threadpoolctl import threadpool_limits
                terms,output=v['public']['equation'].split('->');pending=list(zip(terms.split(','),arrays));ordered=[];endpoint=output[0]
                while pending:
                    matches=[j for j,(labels,_)in enumerate(pending)if endpoint in labels];assert len(matches)==1
                    labels,value=pending.pop(matches[0]);assert len(labels)==2
                    ordered.append(value if labels[0]==endpoint else value.T)
                    endpoint=labels[1]if labels[0]==endpoint else labels[0]
                assert endpoint==output[1]
                with threadpool_limits(limits=1):independent=np.linalg.multi_dot(ordered)
                assert agree(independent,a);matrixchecks+=1
            for e in r['observations']:
                if e['status']!='VERIFIED_CALIBRATION_ONLY':continue
                y=np.load(folder/f'{e["route"]}-{e["repeat"]}-{q}.npy',allow_pickle=False)
                assert agree(y,a)and agree(y,b);numeric+=1
        for e in r['observations']:
            counts[e['status']]+=1
            if 'certificate'in e:
                workcost,peak=independent_path(v['public'],e['path'],e['certificate']);checked_paths+=1
                if e['status']=='PREDECLARED_RESOURCE_EXCLUSION':assert workcost>kr['bounds']['work']or peak>kr['bounds']['peak_elements']
            if e['status']!='VERIFIED_CALIBRATION_ONLY':continue
            assert len(e['queries'])==3 and all(q['full_output_agrees']for q in e['queries'])
            one=e['setup_seconds']+sum(e['queries'][0][k]for k in ['scan_seconds','kernel_seconds','comparison_seconds'])
            three=e['setup_seconds']+sum(q[k]for q in e['queries']for k in ['scan_seconds','kernel_seconds','comparison_seconds'])
            assert one==e['first_component_seconds']and three==e['three_components_seconds']
        routevalues={}
        for metric in ['first_component_seconds','three_components_seconds']:
            medians={route:statistics.median(e[metric]for e in r['observations']if e['route']==route and e['status']=='VERIFIED_CALIBRATION_ONLY')for route in kr['routes']if any(e['route']==route and e['status']=='VERIFIED_CALIBRATION_ONLY'for e in r['observations'])}
            native=min(value for route,value in medians.items()if not route.startswith('FREE_'))
            free=min(value for route,value in medians.items()if route.startswith('FREE_'))
            routevalues[metric]={'native_envelope_seconds':native,'provided_envelope_seconds':free,'ratio_component_only':native/free,'route_medians':medians}
        ratios.append({'name':c['name'],'component_ratios':routevalues})
    assert counts=={'VERIFIED_CALIBRATION_ONLY':45,'PREDECLARED_RESOURCE_EXCLUSION':18,'PREDECLARED_TOPOLOGY_EXCLUSION':9}
    assert numeric==135 and references==24 and matrixchecks==3
    out=work/'Continuation/OFFICIAL_TENSOR_AUDIT';out.mkdir()
    result={'status':'PASS_INDEPENDENT_INDEX_MODEL_AND_RETAINED_NUMERIC_OUTPUT_AUDIT','model_manifest_files':screenfiles,'kernel_manifest_files':kernelfiles,
        'original_shape_selected_cases':len(decisions),'model_event_counts':dict(events),'independent_path_certificates_checked':checked_paths,
        'remaining10x_model_shortlist':shortlist,'kernel_observation_counts':dict(counts),'retained_full_outputs_against_two_references':numeric,
        'reference_outputs_checked':references,'independent_numpy_multi_dot_original_chain_queries':matrixchecks,
        'original_author_checksums':4,'component_calibration':ratios,'complete_investment_cost_measured':False,'IEEE_bit_identity':False,
        'universal_runtime_or_compute_impossibility':False,'learning_performed':False,'fresh_eligible':0,'G0_passed':False,'G1_admitted':False,'G2_admitted':False}
    save(out/'report.json',result);save(out/'model-cases.json',modelsummary);save(out/'manifest.json',{p.name:sha(p)for p in out.iterdir()if p.is_file()})
    print(json.dumps({k:v for k,v in result.items()if k!='component_calibration'},indent=2))
    print(json.dumps([{ 'name':r['name'],'ratios':{k:v['ratio_component_only']for k,v in r['component_ratios'].items()}}for r in ratios],indent=2))

if __name__=='__main__':run(ROOT.parents[1])
