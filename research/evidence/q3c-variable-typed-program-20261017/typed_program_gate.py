"""Q3C model-output boundary: typed AST -> exact original Horn verification.

NO TRAINED SEMANTIC MODEL. Source graph examples are already opened.
Constant true/false are deliberate negative controls, never model outputs.
"""
import argparse,hashlib,json,re,urllib.request
from pathlib import Path
TARGETS={
'inc-max-2-base3-safe.smt2':'bed91ed9ddcac635626f150b683c23329e87e7ff8ccb1b39110745d5814cf889',
'lists-3-inc-some-safe.smt2':'caca97e89ef8cd7a089d107d7b74971a50b5135deab68d268dc7f01b0a87786d'}
REV='e5a86a1ad252fe1df75e06814769ec1d14540032'
DECL=re.compile(r'^\(declare-fun\s+([^\s()]+)\s+\(([^()]*)\)\s+Bool\)$')
class Reject(ValueError):pass

def forms(text):
    out=[];depth=0;start=None;comment=False;quote=False;string=False;i=0
    while i<len(text):
        c=text[i]
        if comment:
            if c=='\n':comment=False
        elif string:
            if c=='"':
                if i+1<len(text) and text[i+1]=='"':i+=1
                else:string=False
        elif quote:
            if c=='|':quote=False
        elif c==';':comment=True
        elif c=='"':string=True
        elif c=='|':quote=True
        elif c=='(':
            if depth==0:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth<0:raise Reject('UNBALANCED')
            if depth==0:out.append(text[start:i+1])
        i+=1
    if depth or quote or string:raise Reject('INCOMPLETE_SOURCE')
    return out

def read_source(raw):
    declarations={};adt=[];rules=[]
    for form in forms(raw.decode('utf-8')):
        if form.startswith('(declare-datatypes'):adt.append(form)
        elif form.startswith('(declare-fun'):
            m=DECL.match(form)
            if not m or m.group(1) in declarations:raise Reject('INVALID_RELATION_DECL')
            declarations[m.group(1)]=m.group(2).split()
        elif form.startswith('(assert '):rules.append(form)
        elif form.startswith('(set-logic ') or form=='(check-sat)':continue
        else:raise Reject('UNRECOGNIZED_ORIGINAL_COMMAND')
    if not rules or not declarations:raise Reject('NO_RELATIONS_OR_RULES')
    return adt,declarations,rules

def compile_ast(node,sorts,counter):
    if not isinstance(node,dict) or type(node.get('op')) is not str:raise Reject('INVALID_AST')
    counter[0]+=1
    if counter[0]>256:raise Reject('AST_LIMIT')
    op=node['op']
    if op=='arg':
        i=node.get('index')
        if set(node)!={'op','index'} or type(i)!=int or not 0<=i<len(sorts):raise Reject('ARG_TYPE')
        return f'p{i}',sorts[i]
    if op=='bool':
        if set(node)!={'op','value'} or type(node['value'])!=bool:raise Reject('BOOL_TYPE')
        return ('true' if node['value'] else 'false'),'Bool'
    if op=='int':
        v=node.get('value')
        if set(node)!={'op','value'} or type(v)!=int or abs(v)>1000000:raise Reject('INT_TYPE')
        return (str(v) if v>=0 else f'(- {-v})'),'Int'
    if op=='selector':
        typemap={'~cur<Int>':('~Mut<Int>','Int'),'~ret<Int>':('~Mut<Int>','Int'),
                 '~cur<%List>':('~Mut<%List>','%List'),'~ret<%List>':('~Mut<%List>','%List')}
        name=node.get('name')
        if set(node)!={'op','name','arg'} or name not in typemap:raise Reject('SELECTOR_SCHEMA')
        val,got=compile_ast(node['arg'],sorts,counter)
        if got!=typemap[name][0]:raise Reject('SELECTOR_SORT')
        return f'({name} {val})',typemap[name][1]
    bounds={'not':(1,1),'and':(2,12),'or':(2,12),'eq':(2,2),'le':(2,2),
            'lt':(2,2),'add':(2,6),'sub':(2,2),'ite':(3,3)}
    if op not in bounds or set(node)!={'op','args'} or type(node['args'])!=list:
        raise Reject('UNSUPPORTED_OPERATION')
    lo,hi=bounds[op]
    if not lo<=len(node['args'])<=hi:raise Reject('BAD_ARITY')
    children=[compile_ast(c,sorts,counter) for c in node['args']]
    kinds=[s for _,s in children]
    if op in ('and','or','not'):
        if any(s!='Bool' for s in kinds):raise Reject('BOOLEAN_SORT')
        result='Bool'
    elif op=='eq':
        if kinds[0]!=kinds[1]:raise Reject('EQUALITY_SORT')
        result='Bool'
    elif op in ('lt','le','add','sub'):
        if any(s!='Int' for s in kinds):raise Reject('ARITHMETIC_SORT')
        result='Bool' if op in ('lt','le') else 'Int'
    elif op=='ite':
        if kinds[0]!='Bool' or kinds[1]!=kinds[2]:raise Reject('ITE_SORT')
        result=kinds[1]
    names={'eq':'=','le':'<=','lt':'<','add':'+','sub':'-'}
    return '('+names.get(op,op)+' '+' '.join(s for s,_ in children)+')',result

def compile_program(candidate,relations):
    if not isinstance(candidate,dict) or set(candidate)!={'relations'} or not isinstance(candidate['relations'],dict):
        raise Reject('PROGRAM_SCHEMA')
    if set(candidate['relations'])!=set(relations):raise Reject('RELATION_COVERAGE')
    definitions=[]
    for name,sorts in relations.items():
        body,typ=compile_ast(candidate['relations'][name],sorts,[0])
        if typ!='Bool':raise Reject('PREDICATE_RETURN_TYPE')
        params=' '.join(f'(p{i} {sort})' for i,sort in enumerate(sorts))
        definitions.append(f'(define-fun {name} ({params}) Bool {body})')
    return definitions

def verify_original(raw,candidate):
    import z3
    adt,relations,rules=read_source(raw)
    definitions=compile_program(candidate,relations)
    prefix='(set-logic ALL)\n'+'\n'.join(adt+definitions)+'\n'
    verdicts=[]
    for assertion in rules:
        formula=assertion[len('(assert '):-1]
        check=z3.parse_smt2_string(prefix+'(assert (not '+formula+'))')
        if len(check)!=1:raise Reject('ORIGINAL_REPARSE')
        solver=z3.Solver();solver.set(timeout=2500);solver.add(check[0])
        answer=str(solver.check());verdicts.append(answer)
        if answer!='unsat':break
    return {'accepted':len(verdicts)==len(rules) and all(x=='unsat' for x in verdicts),
            'first_nonproof':next((i for i,x in enumerate(verdicts) if x!='unsat'),None),
            'verdicts':verdicts,'original_rule_count':len(rules),
            'relation_count':len(relations),
            'relation_arities':[len(x) for x in relations.values()]}

def audit():
    out=[]
    for name,sha in TARGETS.items():
        url=f'https://raw.githubusercontent.com/chc-comp/rust-horn/{REV}/{name}'
        with urllib.request.urlopen(url,timeout=30) as result:raw=result.read()
        if hashlib.sha256(raw).hexdigest()!=sha:raise Reject('SOURCE_SHA256_CHANGED')
        _,relations,clauses=read_source(raw)
        row={'name':name,'sha256':sha,'clauses':len(clauses),'relations':len(relations),'learned_calls':0}
        for literal,label in ((True,'all_true'),(False,'all_false')):
            proposal={'relations':{n:{'op':'bool','value':literal} for n in relations}}
            row[label]=verify_original(raw,proposal)
            if row[label]['accepted'] is True:raise AssertionError('INVALID_TRIVIAL_PROOF_ACCEPTED')
        missing={'relations':{n:{'op':'bool','value':True} for n in list(relations)[1:]}}
        try:compile_program(missing,relations)
        except Reject:row['missing_relation_rejected']=True
        else:raise AssertionError('MISSING_RELATION_NOT_REJECTED')
        bad={'relations':{n:{'op':'bool','value':True} for n in relations}}
        first=next(iter(relations))
        bad['relations'][first]={'op':'eq','args':[{'op':'arg','index':0},{'op':'int','value':0}]}
        try:compile_program(bad,relations)
        except Reject:row['ill_typed_rejected']=True
        else:raise AssertionError('ILL_TYPED_NOT_REJECTED')
        out.append(row)
    return {'study':'Q3C_VARIABLE_TYPED_RELATION_AST_INTERFACE',
            'status':'GATE_READY_NO_TRAINED_MODEL',
            'source_status':'PREVIOUSLY_OPENED_DEVELOPMENT_ONLY',
            'original_rules_seen':sum(x['clauses'] for x in out),
            'trained_model_used':False,'global_q1_q7':'OPEN','records':out}

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=audit();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+'\n')
    print('Q3C',r['status'],[(x['name'],x['relations'],x['clauses'],x['all_true']['verdicts'],x['all_false']['verdicts']) for x in r['records']])
if __name__=='__main__':main()
