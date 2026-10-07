"""Public-only reuse of known ordered monoids. A strong native control, not LPS.

Matches a bounded catalogue modulo associative/commutative arithmetic, state
permutations and pointwise input maps. It may add known sufficient auxiliary
states and compose independent state blocks. Every proposal still needs the
same universal checker; recognition never authorizes execution.
"""
from copy import deepcopy
from itertools import permutations
import json

from neumann1.recursive_summary import SummaryError, program, validate_problem, validate_proposal

W = '$weight'
UNBOUND = object()


def normal(term):
    if not isinstance(term,list):
        return term
    op = term[0]
    args = [normal(t) for t in term[1:]]
    if op in {'add','min','max'}:
        flat = []
        for arg in args:
            if isinstance(arg,list) and arg[0] == op:
                flat.extend(arg[1:])
            else:
                flat.append(arg)
        ints = [t for t in flat if type(t) is int]
        flat = [t for t in flat if type(t) is not int]
        if ints:
            value = sum(ints) if op == 'add' else (min(ints) if op == 'min' else max(ints))
            if op != 'add' or value or not flat:
                flat.append(value)
        if op != 'add':
            flat = list({json.dumps(t,sort_keys=True):t for t in flat}.values())
        flat.sort(key=lambda t:json.dumps(t,sort_keys=True))
        return flat[0] if len(flat)==1 else [op,*flat]
    if op == 'sub' and args[1] == 0:
        return args[0]
    return [op,*args]


def binary(term):
    if not isinstance(term,list):return term
    op = term[0]
    args = [binary(t) for t in term[1:]]
    if op in {'add','max','min'} and len(args)>2:
        value=args[0]
        for arg in args[1:]:value=[op,value,arg]
        return value
    return [op,*args]


def replace(term, mapping):
    if isinstance(term,str):return deepcopy(mapping.get(term,term))
    return [replace(t,mapping) for t in term] if isinstance(term,list) else term


def refs(term):
    if isinstance(term,str):return {term} if term.startswith('r') and term[1:].isdigit() else set()
    return set().union(*(refs(t) for t in term)) if isinstance(term,list) else set()


def _match(pattern, actual, weight=UNBOUND, budget=None):
    if budget is None:budget=[2000]
    budget[0]-=1
    if budget[0]<0:raise SummaryError('Native catalogue matching budget exceeded')
    if pattern == W:
        if refs(actual):return None
        return actual if weight is UNBOUND else (weight if normal(weight)==normal(actual) else None)
    if not isinstance(pattern,list):return weight if type(pattern) is type(actual) and pattern == actual else None
    if not isinstance(actual,list) or pattern[0]!=actual[0]:return None
    if pattern[0] in {'add','max','min'}:
        pp,aa=pattern[1:],actual[1:]
        if len(aa)>7:return None
        # A pointwise map can contain several flattened input-only summands.
        if W in pp and len(aa)>=len(pp):
            fixed=[p for p in pp if p!=W]
            for chosen in permutations(range(len(aa)),len(fixed)):
                current=weight
                good=True
                for p,index in zip(fixed,chosen):
                    result=_match(p,aa[index],current,budget)
                    if result is None:good=False;break
                    current=result
                if not good:continue
                remaining=[a for index,a in enumerate(aa) if index not in chosen]
                joined=remaining[0] if len(remaining)==1 else [pattern[0],*remaining]
                result=_match(W,joined,current,budget)
                if result is not None:return result
            return None
        if len(pp)!=len(aa):return None
        for order in permutations(aa):
            current=weight
            good=True
            for p,a in zip(pp,order):
                result=_match(p,a,current,budget)
                if result is None:good=False;break
                current=result
            if good:return current
        return None
    if len(pattern)!=len(actual):return None
    current=weight
    for p,a in zip(pattern[1:],actual[1:]):
        result=_match(p,a,current,budget)
        if result is None:return None
        current=result
    return current


def conjunction(terms):
    value=True
    for term in terms:value=term if value is True else ['and',value,term]
    return value


def catalogue():
    a=lambda x,y:['add',x,y]
    mx=lambda x,y:['max',x,y]
    mn=lambda x,y:['min',x,y]
    ge=lambda x,y:['ge',x,y]
    templates=[]
    def add(name,empty,step,merge,invariant=True,reference_step=None,decode=None,reference_empty=None):
        d=len(empty)
        decode=list(range(d)) if decode is None else decode
        rs=step if reference_step is None else reference_step
        rs=[replace(t,{f'z{i}':f'r{i}' for i in range(d)}) for t in rs]
        reference={'empty':empty if reference_empty is None else reference_empty,'outputs':rs}
        templates.append({'name':name,'reference':reference,'empty':empty,'step':step,
                          'merge':merge,'decode':decode,'invariant':invariant})
    add('sum',[0],[a(W,'z0')],[a('l0','r0')])
    add('length',[0],[a(1,'z0')],[a('l0','r0')],ge('z0',0))
    for op in ['max','min']:
        inv=ge('z0',0) if op=='max' else ['le','z0',0]
        add(op+'_zero',[0],[[op,W,'z0']],[[op,'l0','r0']],inv)
        pairinv=conjunction([ge('z0','z1'),ge('z1',0)]) if op=='max' else conjunction([['le','z0','z1'],['le','z1',0]])
        other='min' if op=='max' else 'max'
        add('top2_'+op,[0,0],[[op,W,'z0'],[op,'z1',[other,W,'z0']]],
            [[op,'l0','r0'],[op,[op,'l1','r1'],[other,'l0','r0']]],pairinv)
    add('positive_sum',[0],[mx(a('z0',W),'z0')],[a('l0','r0')],ge('z0',0))
    pinv=conjunction([ge('z0',0),ge('z0','z1')])
    prefixstep=[mx(a(W,'z0'),0),a(W,'z1')]
    prefixmerge=[mx('l0',a('l1','r0')),a('l1','r1')]
    add('prefix_with_sum',[0,0],prefixstep,prefixmerge,pinv)
    add('prefix_lift',[0,0],prefixstep,prefixmerge,pinv,
        reference_step=[mx(a(W,'r0'),0)],decode=[0],reference_empty=[0])
    add('suffix_with_sum',[0,0],[mx('z0',a('z1',W)),a('z1',W)],
        [mx('r0',a('l0','r1')),a('l1','r1')],pinv)
    triple=[a('z0',W),mx('z1',a('z0',W)),mx(a('z2',W),0)]
    tmerge=[a('l0','r0'),mx('r1',a('l1','r0')),mx('l2',a('l0','r2'))]
    tinv=conjunction([ge('z1',0),ge('z2',0),ge('z1','z0'),ge('z2','z0')])
    add('sum_suffix_prefix',[0,0,0],triple,tmerge,tinv)
    full=[*triple,mx('z3',mx(a('z2',W),0))]
    fullmerge=[*tmerge,mx(mx('l3','r3'),a('l1','r2'))]
    finv=conjunction([ge('z1',0),ge('z2',0),ge('z1','z0'),ge('z2','z0'),
                      ge('z3','z1'),ge('z3','z2'),ge('z3',0)])
    add('sum_suffix_prefix_subarray',[0,0,0,0],full,fullmerge,finv)
    add('prefix_subarray_lift',[0,0,0,0],full,fullmerge,finv,
        reference_step=[mx(a('r0',W),0),mx('r1',mx(a('r0',W),0))],
        decode=[2,3],reference_empty=[0,0])
    # Goal is first two values with the reference's exact empty/single defaults.
    inv=conjunction([ge('z0',0),['le','z0',2],
                     ['or',['gt','z0',0],['and',['eq','z1',0],['eq','z2',0]]],
                     ['or',['not',['eq','z0',1]],['eq','z2',0]]])
    step=[mn(2,a('z0',1)),W,['ite',['eq','z0',0],0,'z1']]
    merge=[mn(2,a('l0','r0')),['ite',['gt','l0',0],'l1','r1'],
           ['ite',ge('l0',2),'l2',['ite',['eq','l0',1],['ite',['gt','r0',0],'r1',0],'r2']]]
    add('first_two_lift',[0,0,0],step,merge,inv,
        reference_step=[W,'r0'],reference_empty=[0,1],decode=[
            ['ite',['eq','z0',0],0,'z1'],['ite',['eq','z0',0],1,'z2']])
    # Known run-length monoid, with Boolean all-true encoded as 0/1.
    flag=['gt',W,0]
    prefix=['ite',flag,a('z0',1),0]
    alltrue=['and',['eq','z3',1],flag]
    runstep=[prefix,mx('z1',prefix),['ite',alltrue,a('z2',1),'z2'],['ite',alltrue,1,0]]
    runmerge=[['ite',['eq','l3',1],a('l0','r0'),'l0'],
              mx(mx('l1','r1'),a('l2','r0')),
              ['ite',['eq','r3',1],a('l2','r2'),'r2'],
              ['ite',['and',['eq','l3',1],['eq','r3',1]],1,0]]
    runinv=conjunction([ge('z0',0),ge('z2',0),ge('z1','z0'),ge('z1','z2'),
                        ['or',['eq','z3',0],['eq','z3',1]],
                        ['or',['eq','z3',0],['and',['eq','z0','z1'],['eq','z0','z2']]]])
    add('boolean_run_lengths',[0,0,0,1],runstep,runmerge,runinv)
    return templates


def _one_block(problem):
    width=validate_problem(problem)
    if width>4:return None
    actual=[normal(t) for t in problem['step']['outputs']]
    for template in catalogue():
        reference=template['reference']
        if len(reference['empty'])!=width:continue
        for order in permutations(range(width)):
            if [problem['empty'][i] for i in order]!=reference['empty']:continue
            mapping={f'r{i}':f'r{order[i]}' for i in range(width)}
            weight=0 if template['name']=='length' else UNBOUND
            budget=[2000]
            good=True
            for index,term in enumerate(reference['outputs']):
                result=_match(normal(replace(term,mapping)),actual[order[index]],weight,budget)
                if result is None:good=False;break
                weight=result
            if not good:continue
            d=len(template['empty'])
            decoded=[f'z{i}' if type(i)is int else i for i in template['decode']]
            ordered=[None]*width
            for index,target in enumerate(order):ordered[target]=decoded[index]
            def concrete(t):return binary(normal(replace(t,{W:weight})))
            proposal={'empty':deepcopy(template['empty']),
                      'step':program(['head']+[f'z{i}' for i in range(d)],[concrete(t) for t in template['step']]),
                      'merge':program([f'l{i}' for i in range(d)]+[f'r{i}' for i in range(d)],template['merge']),
                      'decode':program([f'z{i}' for i in range(d)],ordered),
                      'invariant':program([f'z{i}' for i in range(d)],[template['invariant']])}
            validate_proposal(problem,proposal)
            return {'proposal':proposal,'mechanism':'KNOWN_MONOID_REUSE_NOT_LEARNING',
                    'template':template['name'],'state_order':list(order),'input_map':binary(weight)}
    return None


def propose(problem):
    width=validate_problem(problem)
    result=_one_block(problem)
    if result:return result
    # Undirected state-dependency components permit known direct-product reuse.
    components=[{i} for i in range(width)]
    for index,term in enumerate(problem['step']['outputs']):
        linked={index,*[int(v[1:]) for v in refs(term)]}
        hits=[c for c in components if c & linked]
        if len(hits)>1:
            combined=set().union(*hits)
            components=[c for c in components if c not in hits]+[combined]
    components=sorted(components,key=min)
    if len(components)<=1:return None
    blocks=[]
    latent=0
    for component in components:
        indices=sorted(component)
        mapping={f'r{original}':f'r{local}' for local,original in enumerate(indices)}
        subproblem={'semantics':'integer_list_right_fold','empty':[problem['empty'][i] for i in indices],
                    'step':program(['head']+[f'r{i}' for i in range(len(indices))],
                                   [replace(problem['step']['outputs'][i],mapping) for i in indices])}
        block=_one_block(subproblem)
        if block is None:return None
        d=len(block['proposal']['empty'])
        if latent+d>8:return None
        blocks.append((indices,latent,block))
        latent+=d
    empty=[];steps=[];merges=[];decodes=[None]*width;invariants=[]
    for indices,offset,block in blocks:
        p=block['proposal'];d=len(p['empty'])
        mapping={f'{prefix}{i}':f'{prefix}{offset+i}' for prefix in ['z','l','r'] for i in range(d)}
        empty.extend(p['empty'])
        steps.extend(replace(t,mapping) for t in p['step']['outputs'])
        merges.extend(replace(t,mapping) for t in p['merge']['outputs'])
        invariants.extend(replace(t,mapping) for t in p['invariant']['outputs'])
        for original,term in zip(indices,p['decode']['outputs']):decodes[original]=replace(term,mapping)
    proposal={'empty':empty,'step':program(['head']+[f'z{i}' for i in range(latent)],steps),
              'merge':program([f'l{i}' for i in range(latent)]+[f'r{i}' for i in range(latent)],merges),
              'decode':program([f'z{i}' for i in range(latent)],decodes),
              'invariant':program([f'z{i}' for i in range(latent)],[conjunction(invariants)])}
    validate_proposal(problem,proposal)
    return {'proposal':proposal,'mechanism':'KNOWN_DIRECT_PRODUCT_REUSE_NOT_LEARNING',
            'blocks':[{'reference_indices':i,'latent_offset':o,'template':b['template'],'input_map':b['input_map']}
                      for i,o,b in blocks]}
