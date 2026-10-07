"""Static erased-type check for the declared pure functional source subset.

Compress/label annotations are erased. This does not prove termination,
equivalence, overflow safety, preconditions, or completeness of matches.
"""
from neumann1.functional_source import SourceError, WorkLimit

INT=('name','Int');BOOL=('name','Bool');UNIT=('name','Unit')


class TypeChecker:
    def __init__(self, commands):
        self.adts={c[1]:c[2] for c in commands if c[0]=='inductive'}
        self.aliases={c[1]:c[2] for c in commands if c[0]=='alias'}
        if self.adts.keys() & self.aliases.keys():
            raise SourceError('Type names cannot have conflicting declarations')
        self.constructors={}
        for owner,fields in self.adts.items():
            for name,declared in fields:
                if name in self.constructors:
                    raise SourceError('Ambiguous constructor across datatype declarations')
                self.constructors[name]=(owner,declared)
        self.remaining=100_000

    def normalize(self, declared, seen=frozenset()):
        if len(seen)>100:
            raise WorkLimit('Type alias budget')
        kind=declared[0]
        if kind=='compress':return self.normalize(declared[1],seen)
        if kind=='name':
            name=declared[1]
            if name in self.aliases:
                if name in seen:raise SourceError('Recursive type alias')
                return self.normalize(self.aliases[name],seen|{name})
            if name not in {'Int','Bool','Unit'} and name not in self.adts:
                raise SourceError(f'Unknown type {name!r}')
            return declared
        if kind in {'tuple','arrow'}:
            return (kind,*(self.normalize(t,seen) for t in declared[1:]))
        raise SourceError('Unknown type constructor')

    def require(self, actual, expected):
        a,b=self.normalize(actual),self.normalize(expected)
        if a!=b:raise SourceError(f'Type mismatch: {a!r} vs {b!r}')

    def pattern(self, node, declared):
        declared=self.normalize(declared);kind=node[0]
        if kind=='wildcard':return {}
        if kind=='variable':return {node[1]:declared}
        if kind=='constructor':
            if node[1] not in self.constructors:raise SourceError('Unknown pattern constructor')
            owner,payload=self.constructors[node[1]]
            self.require(declared,('name',owner))
            return self.pattern(node[2],payload)
        if kind=='tuple':
            if declared[0]!='tuple' or len(node)!=len(declared):raise SourceError('Pattern tuple type mismatch')
            result={}
            for field,t in zip(node[1:],declared[1:]):
                bindings=self.pattern(field,t)
                if result.keys() & bindings.keys():raise SourceError('Duplicate pattern variables')
                result.update(bindings)
            return result
        raise SourceError('Unknown pattern type')

    def infer(self, node, env):
        self.remaining-=1
        if self.remaining<0:raise WorkLimit('Static checking work budget')
        kind=node[0]
        if kind=='constant':
            if type(node[1])is bool:return BOOL
            if type(node[1])is int:return INT
            if node[1]is None:return UNIT
            raise SourceError('Unsupported constant type')
        if kind=='variable':
            if node[1]not in env:raise SourceError(f'Unbound static variable {node[1]!r}')
            return env[node[1]]
        if kind=='lambda':
            declared=self.normalize(node[2])
            return ('arrow',declared,self.infer(node[3],{**env,node[1]:declared}))
        if kind=='apply':
            function=self.normalize(self.infer(node[1],env));argument=self.infer(node[2],env)
            if function[0]!='arrow':raise SourceError('Static application of non-function')
            self.require(argument,function[1]);return function[2]
        if kind=='tuple':return ('tuple',*(self.infer(n,env) for n in node[1:]))
        if kind=='project':
            value=self.normalize(self.infer(node[1],env))
            if value[0]!='tuple' or node[2]>=len(value):raise SourceError('Static tuple projection out of range')
            return value[node[2]]
        if kind=='if':
            self.require(self.infer(node[1],env),BOOL)
            yes,no=self.infer(node[2],env),self.infer(node[3],env)
            self.require(yes,no);return yes
        if kind in {'label','unlabel','align'}:return self.infer(node[1],env)
        if kind=='not':self.require(self.infer(node[1],env),BOOL);return BOOL
        if kind=='sequence':
            self.require(self.infer(node[1],env),UNIT)
            return self.infer(node[2],env)
        if kind=='let':
            value=self.infer(node[2],env)
            return self.infer(node[3],{**env,node[1]:value})
        if kind=='letrec':
            if node[2][0]!='lambda':raise SourceError('Functional recursive binding required')
            raise SourceError('letrec requires retained result annotation; not in registered subset')
        if kind=='fix':
            function=self.normalize(self.infer(node[1],env))
            if function[0]!='arrow':raise SourceError('Fixpoint requires a function')
            self.require(function[1],function[2]);return function[1]
        if kind=='match':
            subject=self.infer(node[1],env);result=None
            for pattern,body in node[2]:
                value=self.infer(body,{**env,**self.pattern(pattern,subject)})
                if result is None:result=value
                else:self.require(result,value)
            if result is None:raise SourceError('Empty match')
            return result
        if kind=='op':
            expected=BOOL if node[1]in {'and','or'} else INT
            self.require(self.infer(node[2],env),expected);self.require(self.infer(node[3],env),expected)
            return BOOL if node[1]in {'and','or','==','<','<=','>','>='} else INT
        raise SourceError(f'Unsupported static expression {kind!r}')

    def check(self,commands):
        env={}
        for command in commands:
            if command[0]=='inductive':
                for name,declared in command[2]:
                    env[name]=('arrow',self.normalize(declared),('name',command[1]))
            elif command[0]=='input':env[command[1]]=self.normalize(command[2])
            elif command[0]=='bind':env[command[1]]=self.normalize(self.infer(command[2],env))
        return env


def check(commands):
    try:return TypeChecker(commands).check(commands)
    except RecursionError as error:raise WorkLimit('Static checker recursion budget') from error


def compatible(left,right,left_checker,right_checker,seen=frozenset()):
    """Check public constructor structure as well as erased type names."""
    left=left_checker.normalize(left);right=right_checker.normalize(right)
    key=(left,right)
    if key in seen:return True
    if left[0]!=right[0]:return False
    if left[0]=='name':
        l,r=left[1],right[1]
        if l in {'Int','Bool','Unit'} or r in {'Int','Bool','Unit'}:return l==r
        lc=dict(left_checker.adts[l]);rc=dict(right_checker.adts[r])
        return lc.keys()==rc.keys() and all(compatible(lc[n],rc[n],left_checker,right_checker,seen|{key}) for n in lc)
    return len(left)==len(right) and all(compatible(l,r,left_checker,right_checker,seen|{key}) for l,r in zip(left[1:],right[1:]))
