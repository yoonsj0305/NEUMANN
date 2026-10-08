"""Conservative Nil/Cons reference projection with exact Boolean bit encoding.

Never executes OCaml or imports arbitrary functions. Boolean inputs are encoded
as integers with truth map h>0; Boolean states/outputs use 0/1. Original machine
overflow, attributes, target skeleton and representation functions are outside
this adaptation. Nonlinear multiplication, division and general recursion reject.
"""
from dataclasses import dataclass
import re

from neumann1.recursive_summary import SummaryError, program, validate_problem
from neumann1.synduce_reference import uncomment


@dataclass
class Value:
    kind: str
    expression: object


def encode(value):
    if value.kind=='Int':return value.expression
    if value.kind=='Bool':
        if type(value.expression)is bool:return int(value.expression)
        return ['ite',value.expression,1,0]
    raise SummaryError('Scalar output expected')


class Parser:
    def __init__(self,text,environment,recursive_name=None,recursive_value=None):
        self.tokens=[]
        while text.strip():
            match=re.match(r'\s*(>=|<=|<>|&&|\|\||\d+|[A-Za-z_]\w*|[(),+\-=<>])',text)
            if not match:raise SummaryError('Unsupported typed expression syntax')
            self.tokens.append(match[1]);text=text[match.end():]
        if len(self.tokens)>16000:raise SummaryError('Projection token budget exceeded')
        self.index=0
        self.environment=dict(environment)
        self.recursive_name=recursive_name
        self.recursive_value=recursive_value
        self.head_kind=None
        self.depth=0

    def peek(self):return self.tokens[self.index] if self.index<len(self.tokens) else None

    def take(self,expected=None):
        value=self.peek()
        if value is None or expected is not None and value!=expected:
            raise SummaryError('Unexpected typed expression token')
        self.index+=1
        return value

    def require(self,value,kind):
        if value.kind=='Head':
            if self.head_kind not in (None,kind):raise SummaryError('Mixed Boolean/integer input use')
            self.head_kind=kind
            return Value(kind,'head' if kind=='Int' else ['gt','head',0])
        if value.kind!=kind:raise SummaryError('Typed expression mismatch')
        return value

    def pattern(self):
        if self.peek()=='(':
            self.take('(')
            names=self.pattern()
            self.take(')')
            return names
        names=[self.take()]
        while self.peek()==',':self.take(',');names.append(self.take())
        if any(not name.isidentifier() or name in {'let','in','if','then','else'} for name in names):
            raise SummaryError('Identifier binding required')
        return names

    def values(self):
        first=self.expression()
        if self.peek()!=',':return first
        items=[first]
        while self.peek()==',':self.take(',');items.append(self.expression())
        if any(item.kind=='Tuple' for item in items):raise SummaryError('Nested tuple unsupported')
        return Value('Tuple',items)

    def atom(self):
        token=self.take()
        if token.isdigit():return Value('Int',int(token))
        if token in {'true','false'}:return Value('Bool',token=='true')
        if token=='-':
            value=self.require(self.atom(),'Int')
            return Value('Int',['sub',0,value.expression])
        if token=='(':
            value=self.values();self.take(')');return value
        if token in {'max','min'}:
            left=self.require(self.atom(),'Int');right=self.require(self.atom(),'Int')
            return Value('Int',[token,left.expression,right.expression])
        if token=='not':return Value('Bool',['not',self.require(self.atom(),'Bool').expression])
        if token=='abs':
            value=self.require(self.atom(),'Int').expression
            return Value('Int',['max',value,['sub',0,value]])
        if token==self.recursive_name:
            self.take('tl')
            if self.recursive_value is None:raise SummaryError('Recursive reference unavailable')
            return self.recursive_value
        if token not in self.environment:raise SummaryError('Unknown variable or unsupported call')
        return self.environment[token]

    def expression(self,minimum=0):
        self.depth+=1
        if self.depth>64:raise SummaryError('Projection expression depth exceeded')
        try:
            if self.peek()=='let':
                self.take('let');names=self.pattern();self.take('=')
                value=self.values();self.take('in')
                items=value.expression if value.kind=='Tuple' else [value]
                if len(items)!=len(names):raise SummaryError('Binding width mismatch')
                prior=dict(self.environment)
                self.environment.update(zip(names,items))
                left=self.values()
                self.environment=prior
            elif self.peek()=='if':
                self.take('if');condition=self.require(self.expression(),'Bool').expression
                self.take('then');yes=self.expression()
                self.take('else');no=self.expression()
                if yes.kind=='Head':yes=self.require(yes,no.kind)
                if no.kind=='Head':no=self.require(no,yes.kind)
                if yes.kind!=no.kind or yes.kind not in {'Int','Bool'}:
                    raise SummaryError('Scalar equally typed conditional arms required')
                if yes.kind=='Int':left=Value('Int',['ite',condition,yes.expression,no.expression])
                else:left=Value('Bool',['or',['and',condition,yes.expression],['and',['not',condition],no.expression]])
            else:left=self.atom()
            precedence={'||':1,'&&':2,'=':3,'<>':3,'>':3,'<':3,'>=':3,'<=':3,'+':4,'-':4}
            operators={'||':'or','&&':'and','=':'eq','>':'gt','<':'lt','>=':'ge','<=':'le','+':'add','-':'sub'}
            while self.peek() in precedence and precedence[self.peek()]>=minimum:
                operator=self.take();right=self.expression(precedence[operator]+1)
                if operator in {'&&','||'}:
                    a=self.require(left,'Bool');b=self.require(right,'Bool')
                    left=Value('Bool',[operators[operator],a.expression,b.expression])
                elif operator in {'+','-'}:
                    a=self.require(left,'Int');b=self.require(right,'Int')
                    left=Value('Int',[operators[operator],a.expression,b.expression])
                else:
                    if left.kind=='Head':left=self.require(left,right.kind)
                    if right.kind=='Head':right=self.require(right,left.kind)
                    if left.kind!=right.kind or left.kind not in {'Int','Bool'}:
                        raise SummaryError('Equally typed scalar comparison required')
                    if left.kind=='Bool' and operator not in {'=','<>'}:
                        raise SummaryError('Boolean ordering unsupported')
                    a=encode(left) if left.kind=='Bool' else left.expression
                    b=encode(right) if right.kind=='Bool' else right.expression
                    comparison=['eq' if operator=='<>' else operators[operator],a,b]
                    left=Value('Bool',['not',comparison] if operator=='<>' else comparison)
            return left
        finally:self.depth-=1

    def complete(self):
        result=self.values()
        if self.index!=len(self.tokens):raise SummaryError('Unconsumed typed expression syntax')
        return result


def project(source):
    clean=uncomment(source)
    declarations=list(re.finditer(r'let\s+rec\s+(\w+)\s*=\s*function\s*\|\s*Nil\s*->\s*([\s\S]*?)\|\s*Cons\s*\(hd,\s*tl\)\s*->\s*([\s\S]*?)(?=\[@@|;;)',clean))
    if not declarations:raise SummaryError('Supported Nil/Cons reference declaration required')
    names=re.findall(r'assert\s*\([^)]*@@\s*(\w+)\s*\)',clean)
    selected=next((item for item in declarations if names and item[1]==names[-1]),declarations[0])
    name,base,body=selected.groups()
    initial=Parser(base,{}).complete()
    items=initial.expression if initial.kind=='Tuple' else [initial]
    if not 1<=len(items)<=8:raise SummaryError('Bounded reference tuple required')
    empty=[]
    for item in items:
        encoded=encode(item)
        if type(encoded)is not int:raise SummaryError('Constant reference base required')
        empty.append(encoded)
    state=[Value(item.kind,['eq',f'r{i}',1] if item.kind=='Bool' else f'r{i}') for i,item in enumerate(items)]
    recursive=Value('Tuple',state) if len(state)>1 else state[0]
    parser=Parser(body,{'hd':Value('Head','head')},name,recursive)
    result=parser.complete()
    outputs=result.expression if result.kind=='Tuple' else [result]
    if len(outputs)!=len(items):raise SummaryError('Reference result width mismatch')
    outputs=[parser.require(value,initial.kind) for value,initial in zip(outputs,items)]
    public={'semantics':'integer_list_right_fold','empty':empty,
            'step':program(['head']+[f'r{i}' for i in range(len(items))],[encode(value) for value in outputs])}
    validate_problem(public)
    return {'public':public,'reference_function':name,'goal_types':[item.kind for item in items],
            'input_type':parser.head_kind or 'Int','Boolean_input_encoding':'positive->true, nonpositive->false' if parser.head_kind=='Bool' else None,
            'Boolean_goal_encoding':'false=0,true=1','scope':'adapted first chosen Nil/Cons reference, not original target/repr/attributes/machine overflow',
            'fresh_eligible':False}
