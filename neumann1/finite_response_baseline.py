"""Known finite transformation-monoid lifting from a public fold, no labels.

Finite exploration proposes a state table. It never proves closure or authorizes
execution; all nine universal conditions still belong to the common verifier.
This is a strong symbolic comparator, not learned NEUMANN or a new principle.
"""
from collections import deque
from copy import deepcopy
from neumann1.recursive_summary import (SummaryError, program, validate_problem,
                                       validate_proposal, interpret)
from neumann1.recursive_library_baseline import replace


def conjunction(items):
    result=True
    for item in items:result=item if result is True else ['and',result,item]
    return result


def simplify(term):
    """Local constant folding only; universal certification remains mandatory."""
    if not isinstance(term,list):return term
    op=term[0];args=[simplify(t) for t in term[1:]]
    if op=='ite':
        if type(args[0]) is bool:return args[1] if args[0] else args[2]
        if args[1]==args[2]:return args[1]
    if op=='not' and type(args[0]) is bool:return not args[0]
    if op in {'and','or'}:
        identity_value=op=='and'
        if any(type(a)is bool and a!=identity_value for a in args):return not identity_value
        args=[a for a in args if type(a)is not bool]
        if not args:return identity_value
        if len(args)==1:return args[0]
    if len(args)==2 and all(type(a)is int for a in args):
        return interpret(program([],[[op,*args]]),[])[0]
    return [op,*args]


def lookup(entries,index):
    result=deepcopy(entries[-1])
    for i in reversed(range(len(entries)-1)):
        result=['ite',['eq',deepcopy(index),i],deepcopy(entries[i]),result]
    return result


def propose(public, *, max_states=8, max_responses=32, exploration_heads=(-1,0,1)):
    width=validate_problem(public)
    if type(max_states) is not int or not 1<=max_states<=8:
        raise SummaryError('Bounded finite-state exploration required')
    if type(max_responses)is not int or not 1<=max_responses<=64:
        raise SummaryError('Bounded response closure required')
    if (not isinstance(exploration_heads,(tuple,list)) or not 1<=len(exploration_heads)<=8
        or any(type(h)is not int or abs(h)>2**63-1 for h in exploration_heads)):
        raise SummaryError('Bounded integer exploration heads required')
    states=[list(public['empty'])];keys={tuple(states[0])};pending=deque(states)
    while pending:
        state=pending.popleft()
        for head in exploration_heads:
            after=interpret(public['step'],[head]+state)
            key=tuple(after)
            if key not in keys:
                if len(states)==max_states:return None
                keys.add(key);states.append(after);pending.append(after)
    n=len(states)
    code={tuple(state):i for i,state in enumerate(states)}
    generators=[]
    for head in exploration_heads:
        table=[code[tuple(interpret(public['step'],[head]+state))] for state in states]
        if table not in generators:generators.append(table)
    responses=[list(range(n))];seen={tuple(responses[0])};pending=deque(responses)
    while pending:
        old=pending.popleft()
        for generator in generators:
            new=[generator[i] for i in old]
            if tuple(new) not in seen:
                if len(responses)==max_responses:return None
                seen.add(tuple(new));responses.append(new);pending.append(new)
    singleton=[]
    # Exact symbolic response on each explored state. The default code does
    # not establish that unknown heads remain in the explored state set.
    for state in states:
        after=[simplify(replace(expr,{f'r{i}':state[i] for i in range(width)})) for expr in public['step']['outputs']]
        encoded=0
        for i in reversed(range(n)):
            equals=conjunction([['eq',term,value] for term,value in zip(after,states[i])])
            encoded=['ite',equals,i,encoded]
        singleton.append(simplify(encoded))
    z=[f'z{i}' for i in range(n)]
    l=[f'l{i}' for i in range(n)];r=[f'r{i}' for i in range(n)]
    # A finite closed response subset narrows proof search. Only a universal
    # certificate can establish that unsampled integer heads preserve it.
    response_invariant=False
    for response in responses:
        equalities=conjunction([['eq',index,value] for index,value in zip(z,response)])
        response_invariant=equalities if response_invariant is False else ['or',response_invariant,equalities]
    proposal={'empty':list(range(n)),
              'step':program(['head']+z,[lookup(singleton,index) for index in z]),
              'merge':program(l+r,[lookup(l,index) for index in r]),
              'decode':program(z,[lookup([state[j] for state in states],z[0]) for j in range(width)]),
              'invariant':program(z,[response_invariant])}
    try:validate_proposal(public,proposal)
    except SummaryError:return None
    return {'proposal':proposal,'mechanism':'KNOWN_FINITE_TRANSFORMATION_MONOID_NOT_LEARNING',
            'reachable_state_candidates':states,'exploration_heads':list(exploration_heads),
            'response_candidates':responses,
            'universal_closure_not_established_by_exploration':True,
            'training_performed':False,'source':'public recurrence only; no candidate/goal/Oracle labels'}
