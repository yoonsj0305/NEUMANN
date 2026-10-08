"""Bounded public symbolic decoder/projection/product synthesis.

Known summary algebras are reused, including weighted runs and arg-extrema.
Small traces only propose decoders. Universal checks alone authorize them.
No learned NEUMANN mechanism, task-name lookup or Oracle input is involved.
"""
from copy import deepcopy
from itertools import combinations,permutations,product
import json
from neumann1.recursive_summary import (SummaryError,program,validate_problem,validate_proposal,
                                      check_summary,reference,interpret,identity)
from neumann1.recursive_library_baseline import catalogue,replace,refs,propose as legacy


def binary(term):
    """Return the exact binary IR after associative matching normalization."""
    if not isinstance(term,list):return term
    op=term[0];args=[binary(t) for t in term[1:]]
    if op in {'add','max','min','and','or'} and len(args)>2:
        value=args[0]
        for arg in args[1:]:value=[op,value,arg]
        return value
    return [op,*args]


def neg(term):
    if type(term)is int:return -term
    if isinstance(term,list):
        if term[0]=='sub' and term[1]==0:return term[2]
        if term[0]=='add':return ['add',*[neg(t) for t in term[1:]]]
        if term[0]=='sub':return ['add',neg(term[1]),term[2]]
        if term[0] in {'max','min'}:return ['min' if term[0]=='max' else 'max',*[neg(t) for t in term[1:]]]
        if term[0]=='ite':return ['ite',term[1],neg(term[2]),neg(term[3])]
    return ['sub',0,term]


def normal(term):
    if not isinstance(term,list):return term
    op=term[0];args=[normal(t) for t in term[1:]]
    if op=='sub':
        if args[1]==0:return args[0]
        if args[0]==0:
            n=neg(args[1])
            return [op,*args] if n==[op,*args] else normal(n)
        return normal(['add',args[0],neg(args[1])])
    if op in {'add','max','min','and','or'}:
        flat=[]
        for a in args:flat.extend(a[1:] if isinstance(a,list) and a[0]==op else [a])
        if op in {'and','or'}:
            zero=op=='or';unit=not zero
            if any(type(a)is bool and a==zero for a in flat):return zero
            flat=[a for a in flat if type(a)is not bool]
            if not flat:return unit
        else:
            numbers=[a for a in flat if type(a)is int];flat=[a for a in flat if type(a)is not int]
            if numbers:
                v=sum(numbers) if op=='add' else max(numbers) if op=='max' else min(numbers)
                if op!='add' or v or not flat:flat.append(v)
        if op!='add':flat=list({json.dumps(a,sort_keys=True):a for a in flat}.values())
        flat.sort(key=lambda a:json.dumps(a,sort_keys=True))
        return flat[0] if len(flat)==1 else [op,*flat]
    if op=='ite':
        if type(args[0])is bool:return args[1] if args[0] else args[2]
        if args[1]==args[2]:return args[1]
        a=args[1][1:] if isinstance(args[1],list) and args[1][0]=='add' else [args[1]]
        b=args[2][1:] if isinstance(args[2],list) and args[2][0]=='add' else [args[2]]
        remaining=list(b);common=[];left=[]
        for t in a:
            if t in remaining:common.append(t);remaining.remove(t)
            else:left.append(t)
        if common:
            fold=lambda xs:0 if not xs else xs[0] if len(xs)==1 else ['add',*xs]
            return normal(['add',*common,['ite',args[0],fold(left),fold(remaining)]])
    if op=='not' and isinstance(args[0],list) and args[0][0]=='not':return args[0][1]
    return [op,*args]


def match(pattern,actual,slots,budget):
    budget[0]-=1
    if budget[0]<0:raise SummaryError('Bounded symbolic matcher work exhausted')
    if isinstance(pattern,str) and pattern.startswith('$'):
        if refs(actual):return None
        if pattern in slots:return slots if normal(slots[pattern])==normal(actual) else None
        return {**slots,pattern:deepcopy(actual)}
    if not isinstance(pattern,list):return slots if type(pattern)is type(actual) and pattern==actual else None
    if not isinstance(actual,list) or pattern[0]!=actual[0]:return None
    if pattern[0] in {'add','max','min','and','or'}:
        pp,aa=pattern[1:],actual[1:]
        if len(aa)>7:return None
        wild=[p for p in pp if isinstance(p,str) and p.startswith('$')]
        if len(wild)==1 and len(aa)>=len(pp):
            fixed=[p for p in pp if p not in wild]
            for indices in permutations(range(len(aa)),len(fixed)):
                current=slots
                for p,i in zip(fixed,indices):
                    current=match(p,aa[i],current,budget)
                    if current is None:break
                if current is None:continue
                extra=[a for i,a in enumerate(aa) if i not in indices]
                if not extra:continue
                joined=extra[0] if len(extra)==1 else [pattern[0],*extra]
                found=match(wild[0],joined,current,budget)
                if found is not None:return found
            return None
        if len(pp)!=len(aa):return None
        for order in permutations(aa):
            current=slots
            for p,a in zip(pp,order):
                current=match(p,a,current,budget)
                if current is None:break
            if current is not None:return current
        return None
    if len(pattern)!=len(actual):return None
    current=slots
    for p,a in zip(pattern[1:],actual[1:]):
        current=match(p,a,current,budget)
        if current is None:return None
    return current


def conjunction(items):
    result=True
    for item in items:result=item if result is True else ['and',result,item]
    return result


def templates():
    result=deepcopy(catalogue())
    run=deepcopy(next(t for t in result if t['name']=='boolean_run_lengths'))
    def weighted(t):
        if t==['gt','$weight',0]:return '$predicate'
        if isinstance(t,list) and t[0]=='add' and len(t)==3 and t[2]==1:return ['add',weighted(t[1]),'$increment']
        return [weighted(a) for a in t] if isinstance(t,list) else t
    run['name']='weighted_segment_monoid'
    run['step']=[weighted(t) for t in run['step']]
    run['reference']['outputs']=[weighted(t) for t in run['reference']['outputs']]
    result.append(run)
    a=lambda x,y:['add',x,y]
    ge=lambda x,y:['ge',x,y]
    eq=lambda x,y:['eq',x,y]
    def add(name,empty,step,merge,inv):
        result.append({'name':name,'empty':empty,'step':step,'merge':merge,'invariant':inv,
                       'reference':{'empty':empty,'outputs':[replace(t,{f'z{i}':f'r{i}' for i in range(len(empty))}) for t in step]}})
    flag=['and','$predicate',eq('z2',1)]
    add('length_suffix_predicate',[0,0,1],
        [a('z0',1),['ite',flag,a('z0',1),'z1'],['ite',flag,1,0]],
        [a('l0','r0'),['ite',eq('r2',1),a('l1','r0'),'r1'],['ite',['and',eq('l2',1),eq('r2',1)],1,0]],
        conjunction([ge('z0',0),ge('z1',0),['le','z1','z0'],['or',eq('z2',0),eq('z2',1)],
                     ['or',eq('z2',0),eq('z1','z0')]]))
    candidate=a('z1','$weight');better=['gt',candidate,'z0']
    best=a('l0','r1');choose=['gt',best,'r0']
    add('suffix_argmax_shortest_tie',[0,0,0,0],
        [['max','z0',candidate],candidate,['ite',better,a('z3',1),'z2'],a('z3',1)],
        [['max','r0',best],a('l1','r1'),['ite',choose,a('l2','r3'),'r2'],a('l3','r3')],
        conjunction([ge('z0',0),ge('z0','z1'),ge('z3',0),ge('z2',0),['le','z2','z3'],
                     ['or',['gt','z0',0],eq('z2',0)],['or',['gt','z2',0],eq('z0',0)]]))
    return sorted(result,key=lambda t:(len(t['empty']),t['name']))


def closed_subsets(outputs):
    width=len(outputs)
    for n in range(1,min(width,4)+1):
        for indices in combinations(range(width),n):
            if all(refs(outputs[i]) <= {f'r{j}' for j in indices} for i in indices):yield indices


def variants():
    result=[]
    for t in templates():
        for indices in closed_subsets(t['reference']['outputs']):
            mapping={f'r{i}':f'r{j}' for j,i in enumerate(indices)}
            result.append((t,indices,[normal(replace(t['reference']['outputs'][i],mapping)) for i in indices]))
    return result


def features(width):
    z=[f'z{i}' for i in range(width)]
    expressions=[*z,*[['sub',0,v] for v in z],0,1]
    expressions += [[op,a,b] for a in z for b in z for op in ['add','sub','max','min'] if a!=b]
    expressions += [['ite',[op,a,b],1,0] for a in z for b in [0,1,*z] for op in ['eq','ge','le','gt','lt'] if a!=b]
    return list({identity(t):t for t in expressions}.values())


def latent_traces(proposal,sequences):
    traces=[]
    for values in sequences:
        state=list(proposal['empty'])
        for h in reversed(values):state=interpret(proposal['step'],[h]+state)
        traces.append(state)
    return traces


def decode_from_traces(proposal,traces,answers):
    names=[f'z{i}' for i in range(len(proposal['empty']))]
    wanted=list(zip(*answers));choices=[None]*len(wanted)
    for term in features(len(names)):
        values=tuple(interpret(program(names,[term]),z)[0] for z in traces)
        for i,target in enumerate(wanted):
            if choices[i] is None and values==target:choices[i]=term
        if all(t is not None for t in choices):return program(names,choices)
    return None


def compose(a,b):
    da,db=len(a['empty']),len(b['empty']);d=da+db
    def part(prop,offset,key):
        mapping={f'{prefix}{i}':f'{prefix}{i+offset}' for prefix in ['z','l','r'] for i in range(len(prop['empty']))}
        return [replace(t,mapping) for t in prop[key]['outputs']]
    return {'empty':a['empty']+b['empty'],
            'step':program(['head']+[f'z{i}' for i in range(d)],part(a,0,'step')+part(b,da,'step')),
            'merge':program([f'l{i}' for i in range(d)]+[f'r{i}' for i in range(d)],part(a,0,'merge')+part(b,da,'merge')),
            'invariant':program([f'z{i}' for i in range(d)],[conjunction(part(a,0,'invariant')+part(b,da,'invariant'))])}


def propose(public,*,max_unifications=20000,max_pool=24,max_checks=24,checkpoint=None):
    width=validate_problem(public)
    if any(type(n)is not int or not 1<=n<=100000 for n in [max_unifications,max_pool,max_checks]) or max_pool>32 or max_checks>64:
        raise SummaryError('Bounded symbolic portfolio required')
    record={'mechanism':'KNOWN_SYMBOLIC_PROJECTION_DECODER_PRODUCT_NOT_LEARNING','unifications':0,'decoder_candidates':0,
            'checks':[],'pool_programs':0,'invalid_candidate_count':0,'sample_sequences':40,'Oracle_used':False,'learning_performed':False}
    def emit_record():
        if checkpoint:checkpoint(deepcopy(record))
    existing=legacy(public)
    if existing is not None:
        cert=check_summary(public,existing['proposal']);record['checks'].append({'source':'existing_native','certificate':cert})
        if cert['accepted']:return {**record,'status':'CERTIFIED','accepted':True,'proposal':existing['proposal'],'certificate':cert,'origin':existing}
    if width>4:return {**record,'status':'ABSTAINED_PUBLIC_WIDTH','accepted':False,'proposal':None}
    sequences=[list(xs) for n in range(4) for xs in product([-2,0,3],repeat=n)]
    answers=[reference(public,xs) for xs in sequences];pool=[];seen=set();by_width={n:[] for n in range(1,5)}
    for item in variants():by_width[len(item[1])].append(item)
    def consider(proposal,origin):
        fingerprint=identity(proposal)
        if fingerprint in seen:return None
        seen.add(fingerprint)
        try:validate_proposal(public,{**proposal,'decode':program([f'z{i}' for i in range(len(proposal['empty']))],[0]*width)})
        except SummaryError:record['invalid_candidate_count']+=1;return None
        traces=latent_traces(proposal,sequences)
        decoder=decode_from_traces(proposal,traces,answers);record['decoder_candidates']+=1
        if decoder is not None and len(record['checks'])<max_checks:
            full={**proposal,'decode':decoder};cert=check_summary(public,full)
            record['checks'].append({'source':origin,'proposal':full,'certificate':cert});emit_record()
            if cert['accepted']:return {**record,'status':'CERTIFIED','accepted':True,'proposal':full,'certificate':cert,'origin':origin}
        if len(pool)<max_pool:pool.append((proposal,origin));record['pool_programs']=len(pool)
        return None
    exhausted=False
    for indices in closed_subsets(public['step']['outputs']):
        n=len(indices)
        for order in permutations(indices):
            for signs in product([1,-1],repeat=n):
                mapping={f'r{i}':f'r{j}' if signs[j]==1 else ['sub',0,f'r{j}'] for j,i in enumerate(order)}
                outputs=[normal(replace(public['step']['outputs'][i],mapping) if signs[j]==1 else neg(replace(public['step']['outputs'][i],mapping))) for j,i in enumerate(order)]
                empty=[signs[j]*public['empty'][i] for j,i in enumerate(order)]
                for template,chosen,patterns in by_width[n]:
                    if [template['reference']['empty'][i] for i in chosen]!=empty:continue
                    record['unifications']+=1
                    if record['unifications']>max_unifications:exhausted=True;break
                    slots={};budget=[2000]
                    try:
                        for p,a in zip(patterns,outputs):
                            slots=match(p,a,slots,budget)
                            if slots is None:break
                    except SummaryError:slots=None
                    if slots is None:continue
                    slots={'$weight':'head','$predicate':['gt','head',0],'$increment':1,**slots}
                    def instantiate(t):return binary(normal(replace(t,slots)))
                    d=len(template['empty']);z=[f'z{i}' for i in range(d)]
                    proposal={'empty':deepcopy(template['empty']),
                        'step':program(['head']+z,[instantiate(t) for t in template['step']]),
                        'merge':program([f'l{i}' for i in range(d)]+[f'r{i}' for i in range(d)],[instantiate(t) for t in template['merge']]),
                        'invariant':program(z,[instantiate(template['invariant'])])}
                    found=consider(proposal,{'template':template['name'],'core':list(order),'signs':list(signs),'reference_projection':list(chosen),'public_input_maps':slots})
                    if found:return found
                if exhausted:break
            if exhausted:break
        if exhausted:break
    # Shared input and independently certified product algebras; same rights
    # must be available to any later neural proposer.
    initial_pool=list(pool)
    for (a,oa),(b,ob) in combinations(initial_pool,2):
        if len(a['empty'])+len(b['empty'])>8:continue
        candidate=compose(a,b)
        found=consider(candidate,{'direct_product':[oa,ob]})
        if found:return found
        if len(record['checks'])>=max_checks:break
    emit_record()
    return {**record,'status':'ABSTAINED_BOUNDED_SYMBOLIC_GRAMMAR','accepted':False,'proposal':None,'unification_budget_exhausted':exhausted}
