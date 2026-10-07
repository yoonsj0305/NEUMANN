"""Read a bounded integer-only emitted homomorphism, never execute source text.

Only a CNil/Single/Concat skeleton and pure integer scalar/flat-tuple helpers
are accepted. The common universal verifier is still required. This adapter
does not establish equivalence of arbitrary upstream repr/target functions.
"""
from copy import deepcopy
import re

from neumann1.recursive_summary import (SummaryError, program, validate_program,
    validate_problem, check_summary, cvc_program, identity, interpret)
from neumann1.typed_fold_projection import Parser, Value
from neumann1.recursive_library_baseline import replace


def outputs(value):
    items=value.expression if value.kind=='Tuple' else [value]
    if not items or len(items)>8 or any(item.kind!='Int' for item in items):
        raise SummaryError('Only bounded integer helper outputs supported')
    return [item.expression for item in items]


def parse_solution(source):
    if not isinstance(source,str) or len(source)>100000:
        raise SummaryError('Bounded emitted solution required')
    # The recursive skeleton is parsed separately, not run as an expression.
    declarations=list(re.finditer(r'^let\s+(rec\s+)?(\w+)\s*([^=]*?)=\s*',source,re.M))
    if not declarations:raise SummaryError('No emitted definitions')
    functions={}
    constants={}
    recursive=[]
    for index,match in enumerate(declarations):
        body=source[match.end():declarations[index+1].start() if index+1<len(declarations) else len(source)].strip()
        is_recursive,name,parameters=match.groups()
        if is_recursive:
            recursive.append((name,parameters,body))
            continue
        parser=Parser(parameters+' =',{})
        patterns=[]
        while parser.peek()!='=':patterns.append(parser.pattern())
        parser.take('=')
        names=[name for pattern in patterns for name in pattern]
        if len(set(names))!=len(names) or len(names)>16:
            raise SummaryError('Bounded unique helper parameters required')
        environment=dict(constants)
        environment.update({name:Value('Int',name) for name in names})
        parsed=Parser(body,environment).complete()
        result=outputs(parsed)
        validate_program(program(names,result),['Int']*len(result))
        functions[name]={'patterns':patterns,'names':names,'outputs':result}
        if not patterns:constants[name]=parsed
    if len(recursive)!=1:raise SummaryError('Exactly one supported emitted recursive skeleton required')
    name,parameters,body=recursive[0]
    if parameters.strip():raise SummaryError('Parameterized skeleton unsupported')
    # Preserve the actual left/right calls. Reversing them changes the program.
    compact=re.sub(r'\s+',' ',body)
    pattern=(r'function (?:\| )?CNil -> (\w+) \| Single\s*\(?(\w+)\)? -> (\w+) (\w+) '
             r'\| Concat\s*\(\s*(\w+)\s*,\s*(\w+)\s*\) -> (\w+) '
             r'\(('+re.escape(name)+r') (\w+)\) \(('+re.escape(name)+r') (\w+)\)')
    match=re.fullmatch(pattern,compact)
    if not match:raise SummaryError('Emitted skeleton is outside CNil/Single/ordered Concat subset')
    base,leaf,single,argument,left,right,merge,_,call_left,_,call_right=match.groups()
    if argument!=leaf or (call_left,call_right)!=(left,right):
        raise SummaryError('Emitted constructor argument/order mismatch')
    if any(key not in functions for key in [base,single,merge]):
        raise SummaryError('Unresolved emitted helper')
    b,f,m=[functions[key] for key in [base,single,merge]]
    if b['patterns'] or len(f['names'])!=1 or len(m['patterns'])!=2:
        raise SummaryError('Unsupported emitted constructor helper arity')
    empty=b['outputs']
    d=len(empty)
    if any(type(v)is not int for v in empty) or len(f['outputs'])!=d or len(m['outputs'])!=d:
        raise SummaryError('Constant equally sized constructor summaries required')
    if len(m['patterns'][0])!=d or len(m['patterns'][1])!=d:
        raise SummaryError('Emitted merge tuple width mismatch')
    single_outputs=[replace(t,{f['names'][0]:'head'}) for t in f['outputs']]
    mapping={key:f'{side}{i}' for side,names in zip(['l','r'],m['patterns']) for i,key in enumerate(names)}
    merge_outputs=[replace(t,mapping) for t in m['outputs']]
    validate_program(program(['head'],single_outputs),['Int']*d)
    validate_program(program([f'l{i}' for i in range(d)]+[f'r{i}' for i in range(d)],merge_outputs),['Int']*d)
    # Cons(h,z) is the emitted singleton merged with z. Certification must also
    # check that this operation at E equals the actual emitted singleton.
    mapping={**{f'l{i}':single_outputs[i] for i in range(d)},**{f'r{i}':f'z{i}' for i in range(d)}}
    step_outputs=[replace(t,mapping) for t in merge_outputs]
    return {'empty':deepcopy(empty),
            'singleton':program(['head'],single_outputs),
            'merge':program([f'l{i}' for i in range(d)]+[f'r{i}' for i in range(d)],merge_outputs),
            'step':program(['head']+[f'z{i}' for i in range(d)],step_outputs),
            'scope':'emitted constructor kernel only, original repr/target not adapted by this reader'}


def singleton_binding(kernel, timeout_ms=2000):
    """The raw emitted Single must equal the certified Cons(h,E) summary.

    This additional condition is essential: common list-summary obligations
    alone do not constrain the emitted leaf implementation.
    """
    import cvc5
    from cvc5 import Kind
    if type(timeout_ms) is not int or not 1 <= timeout_ms <= 10000:
        raise SummaryError('Bounded singleton checker required')
    d = len(kernel['empty'])
    validate_program(kernel['singleton'], ['Int'] * d)
    if kernel['singleton']['inputs'] != ['head']:
        raise SummaryError('Singleton interface mismatch')
    tm = cvc5.TermManager()
    h = tm.mkConst(tm.getIntegerSort(), 'head')
    actual = cvc_program(tm, kernel['singleton'], [h])
    expected = cvc_program(tm, kernel['step'], [h] + [tm.mkInteger(e) for e in kernel['empty']])
    equalities = [tm.mkTerm(Kind.EQUAL, a, b) for a, b in zip(actual, expected)]
    theorem = equalities[0] if d == 1 else tm.mkTerm(Kind.AND, *equalities)
    solver = cvc5.Solver(tm)
    solver.setLogic('QF_LIA')
    solver.setOption('produce-models', 'true')
    solver.setOption('tlimit-per', str(timeout_ms))
    solver.setOption('rlimit-per', '200000')
    negation = tm.mkTerm(Kind.NOT, theorem)
    solver.assertFormula(negation)
    result = solver.checkSat()
    return {'obligation': 'EMITTED_SINGLETON_BINDING', 'accepted': result.isUnsat(),
            'status': str(result),
            'smt2': '(set-logic QF_LIA)\n(declare-fun head () Int)\n(assert ' + str(negation) + ')\n',
            'counterexample': int(solver.getValue(h).getIntegerValue()) if result.isSat() else None}


def certify_solution(problem, source, *, max_decoders=64, timeout_ms=2000):
    """Certify an emitted kernel against an explicitly adapted public fold.

    Invariants are public-step Houdini proposals, decoded state is a bounded
    ordered projection. Source attributes and repr/target are outside this
    adapter; rejection means unsupported or insufficient, not upstream wrong.
    """
    from itertools import permutations
    from time import perf_counter
    from neumann1.recursive_symbolic_baseline import infer_invariant
    if type(max_decoders) is not int or not 1 <= max_decoders <= 256:
        raise SummaryError('Bounded decoder search required')
    start = perf_counter()
    width = validate_problem(problem)
    kernel = parse_solution(source)
    binding = singleton_binding(kernel, timeout_ms)
    common = {'source_sha256': __import__('hashlib').sha256(source.encode()).hexdigest(),
              'kernel_sha256': identity(kernel), 'problem_sha256': identity(problem),
              'kernel': kernel, 'singleton_binding': binding,
              'scope': 'all finite mathematical integer lists, adapted reference only; not original OCaml protocol',
              'learning_performed': False, 'fresh_eligible': 0}
    if not binding['accepted']:
        return {**common, 'accepted': False, 'status': 'EMITTED_SINGLETON_NOT_BOUND',
                'attempts': [], 'seconds': perf_counter() - start}
    d = len(kernel['empty'])
    if width > d:
        return {**common, 'accepted': False, 'status': 'UNSUPPORTED_DECODER_WIDTH',
                'attempts': [], 'seconds': perf_counter() - start}
    z = [f'z{i}' for i in range(d)]
    proxy = {'semantics': 'integer_list_right_fold', 'empty': kernel['empty'],
             'step': program(['head'] + [f'r{i}' for i in range(d)],
                             [replace(t, {f'z{i}': f'r{i}' for i in range(d)}) for t in kernel['step']['outputs']])}
    invariant, inference = infer_invariant(proxy)
    attempts = []
    for indices in permutations(range(d), width):
        if len(attempts) >= max_decoders:
            break
        # Empty mismatch prunes a proposal, never establishes correctness.
        if [kernel['empty'][i] for i in indices] != problem['empty']:
            continue
        proposal = {'empty': deepcopy(kernel['empty']), 'step': deepcopy(kernel['step']),
                    'merge': deepcopy(kernel['merge']), 'decode': program(z, [z[i] for i in indices]),
                    'invariant': deepcopy(invariant)}
        certificate = check_summary(problem, proposal, timeout_ms=timeout_ms)
        attempts.append({'decode_indices': list(indices), 'certificate': certificate})
        if certificate['accepted']:
            return {**common, 'accepted': True, 'status': 'CERTIFIED_ADAPTED_EMITTED_KERNEL',
                    'proposal': proposal, 'invariant_inference': inference, 'attempts': attempts,
                    'seconds': perf_counter() - start}
    return {**common, 'accepted': False, 'status': 'NO_CERTIFIED_BOUNDED_DECODER',
            'invariant_inference': inference, 'attempts': attempts, 'seconds': perf_counter() - start}


def run_raw_kernel(kernel, tree, max_nodes=100000):
    """Diagnostic execution of parsed emitted constructors, not authorization."""
    stack = [(tree, False)]
    values = []
    visited = 0
    while stack:
        node, expanded = stack.pop()
        if expanded:
            right, left = values.pop(), values.pop()
            values.append(interpret(kernel['merge'], left + right))
            continue
        visited += 1
        if visited > max_nodes or not isinstance(node, list) or not node:
            raise SummaryError('Malformed or over-budget diagnostic tree')
        if node == ['nil']:
            values.append(list(kernel['empty']))
        elif len(node) == 2 and node[0] == 'single' and type(node[1]) is int:
            values.append(interpret(kernel['singleton'], [node[1]]))
        elif len(node) == 3 and node[0] == 'concat':
            stack.extend([(node, True), (node[2], False), (node[1], False)])
        else:
            raise SummaryError('Malformed diagnostic constructor')
    if len(values) != 1:
        raise SummaryError('Malformed tree result')
    return values[0]
