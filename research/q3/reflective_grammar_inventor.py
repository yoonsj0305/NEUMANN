"""Q3 scoped experiment: grammar productions and callable programs learned from examples.
No ARC-specific types or spatial primitives. Python stdlib only.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import itertools
import json


def pack(o):
    return json.dumps(o, sort_keys=True, separators=(',',':'))


def ident(o):
    return hashlib.sha256(pack(o).encode()).hexdigest()[:14]


def typ(v):
    if type(v) is bool: return 'Bool'
    if type(v) is int: return 'Int'
    if type(v) is list:
        if not v: return 'List[Empty]'
        children=[typ(a) for a in v]
        return 'List['+(children[0] if len(set(children))==1 else 'Mixed')+']'
    return 'Unknown'


def is_list_type(t):return t.startswith('List[') and t.endswith(']')
def element_type(t):return t[5:-1]

class Runtime:
    def __init__(self,defs=None):
        self.defs=dict(defs or {})
        self.calls=0
    def evaluate(self,ast,x,depth=0):
        self.calls+=1
        if depth>30 or self.calls>500000:raise ValueError('EVAL_LIMIT')
        tag=ast[0]
        if tag=='arg':return x
        if tag=='lit':return ast[1]
        if tag=='op':
            a=self.evaluate(ast[2],x,depth+1);b=self.evaluate(ast[3],x,depth+1)
            if type(a) is not int or type(b) is not int:raise ValueError('BAD_INT_TYPE')
            op=ast[1]
            if op=='add':v=a+b
            elif op=='mul':v=a*b
            elif op=='sub':v=a-b
            elif op=='mod':
                if b==0:raise ValueError('DIV_ZERO')
                v=a%b
            elif op=='eq':return a==b
            elif op=='lt':return a<b
            else:raise ValueError('BAD_OP')
            if abs(v)>1000000:raise ValueError('VALUE_LIMIT')
            return v
        if tag=='call':
            sym=ast[1];arg=self.evaluate(ast[2],x,depth+1)
            definition=self.defs.get(sym)
            if definition is None:raise ValueError('UNKNOWN_SYMBOL')
            return self.evaluate(definition['body'],arg,depth+1)
        if tag in ('map','filter'):
            sym=ast[1];arg=self.evaluate(ast[2],x,depth+1)
            if type(arg) is not list or len(arg)>100:raise ValueError('BAD_SEQUENCE')
            if sym not in self.defs:raise ValueError('UNKNOWN_SYMBOL')
            out=[]
            for v in arg:
                result=self.evaluate(['call',sym,['arg']],v,depth+1)
                if tag=='map':out.append(result)
                else:
                    if type(result) is not bool:raise ValueError('BAD_PREDICATE')
                    if result:out.append(v)
            return out
        raise ValueError('UNKNOWN_AST_TAG')


def exec_safe(ast,x,defs):
    try:return True,Runtime(defs).evaluate(ast,x)
    except (ValueError,TypeError,IndexError,RecursionError,KeyError):return False,None


def match(ast,examples,defs):
    for x,y in examples:
        ok,pred=exec_safe(ast,x,defs)
        if not ok or type(pred) is not type(y) or pred!=y:return False
    return True


def constants(examples):
    pool=set(range(0,6))
    for x,y in examples:
        for val in (x,y):
            if type(val) is int and -1<=val<=9:pool.add(val)
    return sorted(pool)

OPS=('mul','add','sub','mod','eq','lt')

def normalize(op,a,b):
    if op in ('mul','add','eq') and pack(a)>pack(b):a,b=b,a
    return ['op',op,a,b]


def synth_scalar(examples,max_depth=2):
    if not examples or any(type(x) is not int for x,y in examples):return None,0
    outputs=[y for x,y in examples]
    pool=constants(examples)
    atoms=[['arg']]+[['lit',x] for x in pool]
    found={}
    levels=[[]]
    candidates=0
    def observe(ast,level):
        nonlocal candidates
        candidates+=1
        vals=[]
        for x,y in examples:
            ok,v=exec_safe(ast,x,{})
            if not ok:return False
            vals.append((typ(v),pack(v)))
        sig=tuple(vals)
        if sig not in found:
            found[sig]=ast
            levels[level].append(ast)
        return all(v[0]==typ(y) and v[1]==pack(y) for v,y in zip(vals,outputs))
    for a in atoms:
        if observe(a,0):return a,candidates
    if max_depth==0:return None,candidates
    for level in range(1,max_depth+1):
        levels.append([])
        # Incremental observational search, bounded by one prior-level expression.
        prior=list(levels[level-1])
        for left in prior:
            for right in atoms:
                for op in OPS:
                    for a,b in ((left,right),(right,left)):
                        ast=normalize(op,a,b)
                        if observe(ast,level):return ast,candidates
    return None,candidates


def antiunify(a,b,state):
    if a==b:return a
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b) and a[0]==b[0]:
        if a[0]=='op' and a[1]!=b[1]:
            raise ValueError('BUILTIN_OPCODE_INCOMPATIBLE')
        if a[0]=='lit' and len(a)==2 and a[1]!=b[1]:
            pair=(pack(a),pack(b))
            if pair not in state:state[pair]='h'+str(len(state))
            return ['hole',state[pair]]
        return [antiunify(v,w,state) for v,w in zip(a,b)]
    if type(a) is str and type(b) is str:
        pair=('symbol',a,b)
        if pair not in state:state[pair]='h'+str(len(state))
        return ['symhole',state[pair]]
    raise ValueError('GRAMMAR_SOURCE_SHAPE_INCOMPATIBLE')


def count_fixed(template):
    if not isinstance(template,list):return 1
    if template and template[0] in ('hole','symhole'):return 0
    return sum(count_fixed(v) for v in template)


def fill(template,values):
    if isinstance(template,list):
        if template and template[0]=='hole':return ['lit',values[template[1]]]
        if template and template[0]=='symhole':return values[template[1]]
        return [fill(v,values) for v in template]
    return template


def collect_holes(node):
    if isinstance(node,list):
        if node and node[0] in ('hole','symhole'):
            return [(node[1], 'int' if node[0]=='hole' else 'symbol')]
        return [s for v in node for s in collect_holes(v)]
    return []

@dataclass
class MetaLanguage:
    defs:dict
    productions:list
    history:list

    @classmethod
    def empty(cls):return cls({},[],[])

    def define(self,body,examples,reason):
        if not match(body,examples,self.defs):raise ValueError('UNVERIFIED_DEFINITION')
        t_in=typ(examples[0][0]);t_out=typ(examples[0][1])
        symbol='invented_'+ident([body,t_in,t_out])
        self.defs[symbol]={'body':body,'input':t_in,'output':t_out,
                           'origin':reason,'proof_train_examples':len(examples)}
        self.history.append({'action':'define','symbol':symbol,'reason':reason})
        return symbol

    def invent_production(self,first,second):
        a=self.defs[first];b=self.defs[second]
        if (a['input'],a['output'])!=(b['input'],b['output']):return None
        state={}
        try:template=antiunify(a['body'],b['body'],state)
        except ValueError:return None
        holes=sorted(set(collect_holes(template)))
        if not holes or count_fixed(template)<2 or not ('arg' in pack(template)):
            return None
        definition={'symbol':'production_'+ident([template,a['input'],a['output']]),
                    'template':template,'holes':holes,'input':a['input'],
                    'output':a['output'],'sources':[first,second]}
        if definition['symbol'] not in [p['symbol'] for p in self.productions]:
            self.productions.append(definition)
            self.history.append({'action':'invent_grammar_rule',
                                 'symbol':definition['symbol'],
                                 'sources':[first,second],
                                 'holes':holes})
        return definition

    def source_only_json(self):
        return {'schema':'neumann.reflective-self-extending-language.v1',
                'defs':self.defs,'productions':self.productions,
                'history':self.history}

    @classmethod
    def load(cls,obj):
        if obj.get('schema')!='neumann.reflective-self-extending-language.v1':
            raise ValueError('UNTRUSTED_LANGUAGE')
        return cls(dict(obj['defs']),list(obj['productions']),list(obj['history']))

    def grammar_candidates(self,examples):
        t_in=typ(examples[0][0]);t_out=typ(examples[0][1])
        for prod in self.productions:
            if prod['input']!=t_in or prod['output']!=t_out:continue
            choices=[]
            for name,kind in prod['holes']:
                if kind=='int':choices.append(constants(examples))
                elif kind=='symbol':choices.append(sorted(self.defs))
                else:raise ValueError('BAD_GRAMMAR_HOLE')
            for combination in itertools.product(*choices):
                values=dict(zip([name for name,kind in prod['holes']],combination))
                candidate=fill(prod['template'],values)
                if match(candidate,examples,self.defs):
                    yield candidate,prod['symbol']

    def solve(self,examples,budget=1,allow_core_lifting=True):
        """Generic search -> self-invented production -> bounded generic core."""
        if not examples:return None
        t_in=typ(examples[0][0]);t_out=typ(examples[0][1])
        iterations=0
        if t_in=='Int':
            direct,iterations=synth_scalar(examples,max_depth=budget)
            if direct is not None:
                symbol=self.define(direct,examples,'base_search')
                return {'symbol':symbol,'mechanism':'base_search','attempts':iterations}
        # The grammar productions are learned from prior programs, not
        # manually specified for the target domain.
        for program,producer in self.grammar_candidates(examples):
            sym=self.define(program,examples,'self_invented_grammar:'+producer)
            return {'symbol':sym,'mechanism':'self_invented_grammar',
                    'production':producer,'attempts':iterations}
        # Seed language has generic map/filter, not domain-specific
        # predicates, coordinate operators or invented target functions.
        if allow_core_lifting and is_list_type(t_in) and is_list_type(t_out):
            for sym,definition in sorted(self.defs.items()):
                if element_type(t_in)==definition['input'] and \
                   element_type(t_out)==definition['output']:
                    program=['map',sym,['arg']]
                    if match(program,examples,self.defs):
                        derived=self.define(program,examples,'generic_core_map:'+sym)
                        return {'symbol':derived,'mechanism':'generic_core_map',
                                'source':sym}
                if t_in==t_out and element_type(t_in)==definition['input'] \
                   and definition['output']=='Bool':
                    program=['filter',sym,['arg']]
                    if match(program,examples,self.defs):
                        derived=self.define(program,examples,'generic_core_filter:'+sym)
                        return {'symbol':derived,'mechanism':'generic_core_filter',
                                'source':sym}
        return None
